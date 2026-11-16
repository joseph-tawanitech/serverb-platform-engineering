"""Integration tests for B21 preparation and B22 Kubernetes dispatch."""

import base64
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from tap_b21.adapter_dispatcher import (
    ActionExecutionStatus,
    prepare_action,
)
from tap_b21.adapter_registry import AdapterRegistry
from tap_b21.authorization import (
    AuthorizationGrant,
    authorization_grant_signing_bytes,
    compute_plan_digest,
)
from tap_b21.contracts import (
    RemediationAction,
    RemediationPlan,
    TaskRequest,
)
from tap_b21.plan_router import RoutedAction
from tap_b21.resource_safety import (
    ResourceImpact,
    ResourceSnapshot,
    SimulatedResourceSafetyGate,
)

from tap_b22.execution_dispatcher import AdapterExecutionDispatcher
from tap_b22.kubernetes_adapter import (
    KubernetesAdapter,
    KubernetesDeploymentTarget,
)


class FakeAppsApi:
    def __init__(self):
        self.read_calls = []
        self.patch_calls = []

    def read_namespaced_deployment(
        self, *, name, namespace, _request_timeout
    ):
        self.read_calls.append((name, namespace))
        return SimpleNamespace(
            metadata=SimpleNamespace(resource_version="10")
        )

    def patch_namespaced_deployment(
        self, *, name, namespace, body, _request_timeout
    ):
        self.patch_calls.append((name, namespace, body))
        return SimpleNamespace(
            metadata=SimpleNamespace(resource_version="11")
        )


def build_integrated_execution(*, tamper_signature=False):
    now = datetime.now(timezone.utc)
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    task = TaskRequest(
        task_id="integration-task-001",
        incident_id="integration-incident-001",
        target="payments-api",
        environment="lab",
        requested_by="sre-user",
        objective="Restore payments service",
    )

    action = RemediationAction(
        action_id="integration-action-001",
        channel="kubernetes",
        operation="restart_deployment",
        target="payments-api",
        purpose="Restart payments Deployment",
        expected_state="deployment_available",
        parameters={},
    )

    plan = RemediationPlan(
        plan_id="integration-plan-001",
        task_id=task.task_id,
        summary="Restart payments Deployment",
        actions=(action,),
        verification_requirements=("deployment_available",),
    )

    route = RoutedAction(
        action_id=action.action_id,
        operation=action.operation,
        target=action.target,
        environment=task.environment,
        selected_channel="kubernetes",
    )
    routes = (route,)

    unsigned = AuthorizationGrant(
        grant_id="integration-grant-001",
        task_id=task.task_id,
        plan_id=plan.plan_id,
        plan_digest=compute_plan_digest(task, plan, routes),
        environment=task.environment,
        approved_by="integration-test-approver",
        issuer_id="integration-test-authority",
        issued_at=(now - timedelta(minutes=1)).isoformat(),
        expires_at=(now + timedelta(hours=1)).isoformat(),
        signing_algorithm="Ed25519",
        signature="temporary-placeholder",
    )

    signature = private_key.sign(
        authorization_grant_signing_bytes(unsigned)
    )
    grant = replace(
        unsigned,
        signature=base64.b64encode(signature).decode("ascii"),
    )

    if tamper_signature:
        grant = replace(
            grant,
            signature=base64.b64encode(b"x" * 64).decode("ascii"),
        )

    api = FakeAppsApi()

    adapter = KubernetesAdapter(
        apps_api=api,
        trusted_public_keys={
            "integration-test-authority": public_key,
        },
        targets={
            "payments-api": KubernetesDeploymentTarget(
                namespace="apps",
                deployment="payments-api",
            )
        },
        allowed_namespaces=frozenset({"apps"}),
        execution_enabled=True,
    )

    registry = AdapterRegistry()
    registry.register(adapter)

    prepared = prepare_action(
        registry=registry,
        task=task,
        plan=plan,
        action=action,
        routed_action=route,
        routed_actions=routes,
        authorization_grant=grant,
        prepared_at=now,
    )

    resources = {
        action.action_id: (
            ResourceSnapshot(
                ram_used_percent=50.0,
                cpu_used_percent=50.0,
                disk_used_percent=50.0,
            ),
            ResourceImpact(
                ram_increase_percent=5.0,
                cpu_increase_percent=5.0,
                disk_increase_percent=5.0,
            ),
        )
    }

    result = AdapterExecutionDispatcher(
        SimulatedResourceSafetyGate()
    ).dispatch(
        (prepared,),
        resources,
    )

    return result, api


def test_b21_preparation_to_b22_kubernetes_execution():
    result, api = build_integrated_execution()

    assert result.overall_status is ActionExecutionStatus.SUCCEEDED
    assert len(result.action_records) == 1
    assert (
        result.action_records[0].status
        is ActionExecutionStatus.SUCCEEDED
    )

    # The actual adapter was reached through the registry and dispatcher.
    assert len(api.read_calls) == 1
    assert len(api.patch_calls) == 1

    result.validate()


def test_invalid_grant_stops_before_kubernetes_api_calls():
    result, api = build_integrated_execution(tamper_signature=True)

    assert result.overall_status is ActionExecutionStatus.BLOCKED
    assert (
        result.action_records[0].status
        is ActionExecutionStatus.BLOCKED
    )
    assert (
        result.action_records[0].failure_code
        == "ADAPTER_VALIDATION_REJECTED"
    )

    assert api.read_calls == []
    assert api.patch_calls == []
