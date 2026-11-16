from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from tap_b21.adapter_contracts import (
    AdapterExecutionResult,
    ExecutionStatus,
)
from tap_b21.adapter_dispatcher import (
    ActionExecutionRecord,
    ActionExecutionStatus,
)
from tap_b22.kubernetes_adapter import KubernetesDeploymentTarget

from tap_b23.contracts import VerificationStatus
from tap_b23.kubernetes_verifier import KubernetesDeploymentVerifier


def make_record(
    execution_status=ActionExecutionStatus.SUCCEEDED,
):
    now = datetime.now(timezone.utc)
    adapter_result = None

    if execution_status in {
        ActionExecutionStatus.SUCCEEDED,
        ActionExecutionStatus.UNKNOWN,
    }:
        adapter_status = (
            ExecutionStatus.SUCCEEDED
            if execution_status == ActionExecutionStatus.SUCCEEDED
            else ExecutionStatus.UNKNOWN
        )

        adapter_result = AdapterExecutionResult(
            task_id="task-001",
            plan_id="plan-001",
            action_id="action-001",
            adapter_id="tap-b22-kubernetes",
            selected_channel="kubernetes",
            operation="restart_deployment",
            target="test-web",
            environment="test",
            status=adapter_status,
            started_at=now,
            completed_at=(
                now + timedelta(seconds=1)
                if adapter_status == ExecutionStatus.SUCCEEDED
                else None
            ),
            message="Deployment restart requested.",
        )

    record = ActionExecutionRecord(
        dispatch_id="dispatch-001",
        attempt_id="attempt-001",
        attempt_number=1,
        task_id="task-001",
        plan_id="plan-001",
        action_id="action-001",
        adapter_id="tap-b22-kubernetes",
        selected_channel="kubernetes",
        grant_id="grant-001",
        status=execution_status,
        prepared_at=now - timedelta(seconds=2),
        resource_checked_at=now - timedelta(seconds=1),
        authorization_confirmed_at=now - timedelta(seconds=1),
        adapter_result=adapter_result,
    )
    record.validate()
    return record


def make_deployment(record, *, complete=True):
    restart_timestamp = record.adapter_result.started_at.isoformat()

    return SimpleNamespace(
        metadata=SimpleNamespace(generation=5),
        spec=SimpleNamespace(
            replicas=2,
            template=SimpleNamespace(
                metadata=SimpleNamespace(
                    annotations={
                        "kubectl.kubernetes.io/restartedAt":
                            restart_timestamp
                    }
                )
            ),
        ),
        status=SimpleNamespace(
            observed_generation=5,
            updated_replicas=2 if complete else 1,
            available_replicas=2 if complete else 1,
            unavailable_replicas=0 if complete else 1,
        ),
    )


class FakeAppsAPI:
    def __init__(self, deployment=None, error=None):
        self.deployment = deployment
        self.error = error
        self.calls = []

    def read_namespaced_deployment(
        self, *, name, namespace, _request_timeout
    ):
        self.calls.append((name, namespace))

        if self.error:
            raise self.error

        return self.deployment


def make_verifier(api, timeout=0.01):
    return KubernetesDeploymentVerifier(
        apps_api=api,
        targets={
            "test-web": KubernetesDeploymentTarget(
                namespace="default",
                deployment="web",
            )
        },
        timeout_seconds=timeout,
        poll_interval_seconds=0.001,
        request_timeout_seconds=1.0,
    )


def test_completed_restart_is_verified():
    record = make_record()
    api = FakeAppsAPI(make_deployment(record))
    verifier = make_verifier(api)

    result = verifier.verify(record)

    assert result.status == VerificationStatus.VERIFIED
    assert result.dispatch_id == record.dispatch_id
    assert result.attempt_id == record.attempt_id
    assert result.execution_status == ActionExecutionStatus.SUCCEEDED
    assert any("Rollout complete: True" in item for item in result.evidence)
    assert len(api.calls) == 1


def test_incomplete_rollout_is_not_verified():
    record = make_record()
    api = FakeAppsAPI(make_deployment(record, complete=False))
    verifier = make_verifier(api, timeout=0.003)

    result = verifier.verify(record)

    assert result.status == VerificationStatus.UNVERIFIED
    assert result.status != VerificationStatus.VERIFIED
    assert "deadline" in result.message.lower()


def test_missing_deployment_is_failed():
    class NotFoundError(Exception):
        status = 404

    record = make_record()
    api = FakeAppsAPI(error=NotFoundError())
    verifier = make_verifier(api)

    result = verifier.verify(record)

    assert result.status == VerificationStatus.FAILED
    assert "does not exist" in result.message


def test_blocked_execution_is_skipped():
    record = make_record(ActionExecutionStatus.BLOCKED)
    api = FakeAppsAPI()
    verifier = make_verifier(api)

    result = verifier.verify(record)

    assert result.status == VerificationStatus.SKIPPED
    assert api.calls == []
    assert result.execution_status == ActionExecutionStatus.BLOCKED
