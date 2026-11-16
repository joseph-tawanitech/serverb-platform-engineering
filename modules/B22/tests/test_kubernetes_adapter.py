"""Tests for the TAP B22 Kubernetes adapter."""

import base64
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from tap_b21.adapter_contracts import (
    AdapterAuthorizationError,
    AdapterExecutionRequest,
    ExecutionStatus,
)
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

from tap_b22.kubernetes_adapter import (
    KubernetesAdapter,
    KubernetesDeploymentTarget,
    KubernetesExecutionDisabledError,
    KubernetesTargetError,
)


class FakeKubernetesApi:
    def __init__(self):
        self.read_calls = []
        self.patch_calls = []
        self.read_error = None
        self.patch_error = None

    def read_namespaced_deployment(
        self, *, name, namespace, _request_timeout
    ):
        self.read_calls.append((name, namespace, _request_timeout))
        if self.read_error:
            raise self.read_error
        return SimpleNamespace(metadata=SimpleNamespace(resource_version="10"))

    def patch_namespaced_deployment(
        self, *, name, namespace, body, _request_timeout
    ):
        self.patch_calls.append(
            (name, namespace, body, _request_timeout)
        )
        if self.patch_error:
            raise self.patch_error
        return SimpleNamespace(
            metadata=SimpleNamespace(resource_version="11")
        )


class FakeApiError(Exception):
    def __init__(self, status):
        super().__init__(f"HTTP {status}")
        self.status = status


class KubernetesAdapterTests(unittest.TestCase):
    def setUp(self):
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.now = datetime.now(timezone.utc)

        self.task = TaskRequest(
            task_id="task-k8s-001",
            incident_id="incident-k8s-001",
            target="payments-api",
            environment="lab",
            requested_by="sre-user",
            objective="Restart the payments Deployment",
        )

        self.action = RemediationAction(
            action_id="action-k8s-001",
            channel="kubernetes",
            operation="restart_deployment",
            target="payments-api",
            purpose="Restart the payments Deployment",
            expected_state="deployment_available",
            parameters={},
        )

        self.plan = RemediationPlan(
            plan_id="plan-k8s-001",
            task_id=self.task.task_id,
            summary="Restart payments Deployment",
            actions=(self.action,),
            verification_requirements=(
                "deployment_available",
                "new_replicas_ready",
            ),
        )

        self.route = RoutedAction(
            action_id=self.action.action_id,
            operation=self.action.operation,
            target=self.action.target,
            environment=self.task.environment,
            selected_channel="kubernetes",
        )
        self.routes = (self.route,)

        self.grant = self.make_grant()
        self.request = AdapterExecutionRequest(
            task=self.task,
            plan=self.plan,
            action=self.action,
            routed_action=self.route,
            routed_actions=self.routes,
            authorization_grant=self.grant,
        )

        self.api = FakeKubernetesApi()
        self.adapter = self.make_adapter(execution_enabled=True)

    def make_grant(self):
        digest = compute_plan_digest(
            self.task,
            self.plan,
            self.routes,
        )

        unsigned = AuthorizationGrant(
            grant_id="grant-k8s-001",
            task_id=self.task.task_id,
            plan_id=self.plan.plan_id,
            plan_digest=digest,
            environment=self.task.environment,
            approved_by="human-approver",
            issuer_id="trusted-authority",
            issued_at=(self.now - timedelta(minutes=1)).isoformat(),
            expires_at=(self.now + timedelta(hours=1)).isoformat(),
            signing_algorithm="Ed25519",
            signature="temporary-placeholder",
        )

        signature = self.private_key.sign(
            authorization_grant_signing_bytes(unsigned)
        )
        return replace(
            unsigned,
            signature=base64.b64encode(signature).decode("ascii"),
        )

    def make_adapter(
        self,
        *,
        execution_enabled=False,
        targets=None,
        allowed_namespaces=frozenset({"apps"}),
    ):
        if targets is None:
            targets = {
                "payments-api": KubernetesDeploymentTarget(
                    namespace="apps",
                    deployment="payments-api",
                )
            }

        return KubernetesAdapter(
            apps_api=self.api,
            trusted_public_keys={
                "trusted-authority": self.public_key,
            },
            targets=targets,
            allowed_namespaces=allowed_namespaces,
            execution_enabled=execution_enabled,
        )

    def test_adapter_exposes_expected_contract(self):
        self.assertEqual(
            self.adapter.adapter_id,
            "tap-b22-kubernetes",
        )
        self.assertEqual(
            self.adapter.supported_channels,
            frozenset({"kubernetes"}),
        )
        self.assertEqual(
            self.adapter.supported_operations,
            frozenset({"restart_deployment"}),
        )

    def test_valid_request_passes_authorization_and_scope_checks(self):
        self.adapter.validate_execution_request(self.request)
        self.assertEqual(self.api.read_calls, [])
        self.assertEqual(self.api.patch_calls, [])

    def test_unknown_target_is_rejected(self):
        adapter = self.make_adapter(
            targets={
                "another-target": KubernetesDeploymentTarget(
                    namespace="apps",
                    deployment="another-deployment",
                )
            }
        )

        with self.assertRaises(KubernetesTargetError):
            adapter.validate_execution_request(self.request)

    def test_ai_supplied_parameters_are_rejected(self):
        action = replace(
            self.action,
            parameters={"namespace": "kube-system"},
        )
        plan = replace(self.plan, actions=(action,))
        route = replace(self.route, operation=action.operation)
        routes = (route,)
        unsigned_request = AdapterExecutionRequest(
            task=self.task,
            plan=plan,
            action=action,
            routed_action=route,
            routed_actions=routes,
            authorization_grant=self.grant,
        )

        with self.assertRaises(Exception):
            self.adapter.validate_execution_request(unsigned_request)

    def test_invalid_signature_is_rejected_before_api_access(self):
        forged = replace(
            self.grant,
            signature=base64.b64encode(b"x" * 64).decode("ascii"),
        )
        request = replace(
            self.request,
            authorization_grant=forged,
        )

        with self.assertRaises(AdapterAuthorizationError):
            self.adapter.validate_execution_request(request)

        self.assertEqual(self.api.read_calls, [])
        self.assertEqual(self.api.patch_calls, [])

    def test_execution_is_disabled_by_default(self):
        adapter = self.make_adapter(execution_enabled=False)

        with self.assertRaises(KubernetesExecutionDisabledError):
            adapter.execute_approved_request(self.request)

        self.assertEqual(self.api.read_calls, [])
        self.assertEqual(self.api.patch_calls, [])

    def test_successful_restart_sends_only_restart_annotation(self):
        result = self.adapter.execute_approved_request(self.request)

        self.assertEqual(result.status, ExecutionStatus.SUCCEEDED)
        self.assertEqual(len(self.api.read_calls), 1)
        self.assertEqual(len(self.api.patch_calls), 1)

        name, namespace, body, timeout = self.api.patch_calls[0]
        self.assertEqual(name, "payments-api")
        self.assertEqual(namespace, "apps")
        self.assertGreater(timeout, 0)
        self.assertIn(
            "kubectl.kubernetes.io/restartedAt",
            body["spec"]["template"]["metadata"]["annotations"],
        )

        self.assertIn(
            "rollout completion requires independent verification",
            result.message,
        )

    def test_kubernetes_4xx_response_returns_failed(self):
        self.api.patch_error = FakeApiError(403)

        result = self.adapter.execute_approved_request(self.request)

        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertEqual(result.completed_at is not None, True)

    def test_transport_timeout_returns_unknown(self):
        self.api.patch_error = TimeoutError("simulated timeout")

        result = self.adapter.execute_approved_request(self.request)

        self.assertEqual(result.status, ExecutionStatus.UNKNOWN)
        self.assertIsNone(result.completed_at)
        self.assertIn("outcome is unknown", result.message)

    def test_namespace_outside_allowlist_is_rejected_at_configuration(self):
        with self.assertRaises(ValueError):
            self.make_adapter(
                allowed_namespaces=frozenset({"other"}),
            )


if __name__ == "__main__":
    unittest.main()
