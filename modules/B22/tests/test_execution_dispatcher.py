"""Tests for the shared B22 execution dispatcher."""

import base64
from datetime import datetime, timedelta, timezone

import pytest

from tap_b21.adapter_contracts import (
    AdapterExecutionRequest,
    AdapterExecutionResult,
    ExecutionStatus,
)
from tap_b21.adapter_dispatcher import (
    ActionExecutionStatus,
    PreparedAction,
)
from tap_b21.authorization import (
    AuthorizationGrant,
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

from tap_b22.execution_dispatcher import (
    AdapterExecutionDispatcher,
    ExecutionDispatchError,
)


class FakeAdapter:
    adapter_id = "test-kubernetes-adapter"
    supported_channels = frozenset({"kubernetes"})
    supported_operations = frozenset({"restart_deployment"})

    def __init__(self):
        self.validation_calls = 0
        self.execution_calls = 0
        self.reject_validation = False
        self.execution_error = None
        self.result_status = ExecutionStatus.SUCCEEDED
        self.result_override = None

    def validate_execution_request(self, request):
        self.validation_calls += 1
        if self.reject_validation:
            raise PermissionError("authorization rejected")

    def execute_approved_request(self, request):
        self.execution_calls += 1

        if self.execution_error is not None:
            raise self.execution_error

        if self.result_override is not None:
            return self.result_override

        now = datetime.now(timezone.utc)
        completed = (
            None
            if self.result_status in {
                ExecutionStatus.TIMED_OUT,
                ExecutionStatus.UNKNOWN,
            }
            else now
        )

        return AdapterExecutionResult(
            task_id=request.task.task_id,
            plan_id=request.plan.plan_id,
            action_id=request.action.action_id,
            adapter_id=self.adapter_id,
            selected_channel="kubernetes",
            operation=request.action.operation,
            target=request.action.target,
            environment=request.task.environment,
            status=self.result_status,
            started_at=now,
            completed_at=completed,
            message=f"Simulated adapter outcome: {self.result_status.value}",
        )


def make_resource_input(
    *,
    ram=50.0,
    cpu=50.0,
    disk=50.0,
    ram_increase=5.0,
    cpu_increase=5.0,
    disk_increase=5.0,
):
    return (
        ResourceSnapshot(
            ram_used_percent=ram,
            cpu_used_percent=cpu,
            disk_used_percent=disk,
        ),
        ResourceImpact(
            ram_increase_percent=ram_increase,
            cpu_increase_percent=cpu_increase,
            disk_increase_percent=disk_increase,
        ),
    )


def make_prepared_plan(adapter, action_count=1):
    now = datetime.now(timezone.utc)

    task = TaskRequest(
        task_id="task-dispatch-001",
        incident_id="incident-dispatch-001",
        target="payments-api",
        environment="lab",
        requested_by="sre-user",
        objective="Restore payments service",
    )

    actions = tuple(
        RemediationAction(
            action_id=f"action-{index:03d}",
            channel="kubernetes",
            operation="restart_deployment",
            target="payments-api",
            purpose="Restart payments Deployment",
            expected_state="deployment_available",
            parameters={},
        )
        for index in range(1, action_count + 1)
    )

    plan = RemediationPlan(
        plan_id="plan-dispatch-001",
        task_id=task.task_id,
        summary="Restore payments service",
        actions=actions,
        verification_requirements=("deployment_available",),
    )

    routes = tuple(
        RoutedAction(
            action_id=action.action_id,
            operation=action.operation,
            target=action.target,
            environment=task.environment,
            selected_channel="kubernetes",
        )
        for action in actions
    )

    # The fake adapter performs its own validation in these tests.
    unsigned_grant = AuthorizationGrant(
        grant_id="grant-dispatch-001",
        task_id=task.task_id,
        plan_id=plan.plan_id,
        plan_digest=compute_plan_digest(task, plan, routes),
        environment=task.environment,
        approved_by="test-human-approver",
        issuer_id="test-authority",
        issued_at=(now - timedelta(minutes=1)).isoformat(),
        expires_at=(now + timedelta(hours=1)).isoformat(),
        signing_algorithm="Ed25519",
        signature=base64.b64encode(b"x" * 64).decode("ascii"),
    )

    prepared = []

    for action, route in zip(actions, routes):
        request = AdapterExecutionRequest(
            task=task,
            plan=plan,
            action=action,
            routed_action=route,
            routed_actions=routes,
            authorization_grant=unsigned_grant,
        )

        prepared.append(
            PreparedAction(
                adapter=adapter,
                adapter_id=adapter.adapter_id,
                request=request,
                prepared_at=now - timedelta(seconds=10),
            )
        )

    return tuple(prepared), actions


def make_dispatcher():
    return AdapterExecutionDispatcher(
        SimulatedResourceSafetyGate()
    )


def resource_map(actions, resource_input=None):
    value = resource_input or make_resource_input()
    return {action.action_id: value for action in actions}


def test_safe_action_executes_and_returns_success_record():
    adapter = FakeAdapter()
    prepared, actions = make_prepared_plan(adapter)

    result = make_dispatcher().dispatch(
        prepared,
        resource_map(actions),
    )

    assert result.overall_status is ActionExecutionStatus.SUCCEEDED
    assert len(result.action_records) == 1

    record = result.action_records[0]
    assert record.status is ActionExecutionStatus.SUCCEEDED
    assert record.resource_checked_at is not None
    assert record.authorization_confirmed_at is not None
    assert record.adapter_result.status is ExecutionStatus.SUCCEEDED
    assert adapter.validation_calls == 1
    assert adapter.execution_calls == 1
    result.validate()


def test_hard_resource_limit_blocks_without_adapter_calls():
    adapter = FakeAdapter()
    prepared, actions = make_prepared_plan(adapter)

    high_usage = make_resource_input(ram=90.0)

    result = make_dispatcher().dispatch(
        prepared,
        resource_map(actions, high_usage),
    )

    record = result.action_records[0]

    assert result.overall_status is ActionExecutionStatus.BLOCKED
    assert record.failure_code == "RESOURCE_HARD_LIMIT"
    assert record.status is ActionExecutionStatus.BLOCKED
    assert adapter.validation_calls == 0
    assert adapter.execution_calls == 0


def test_missing_resource_reading_requires_human_and_stops():
    adapter = FakeAdapter()
    prepared, actions = make_prepared_plan(adapter)

    missing_reading = make_resource_input(ram=None)

    result = make_dispatcher().dispatch(
        prepared,
        resource_map(actions, missing_reading),
    )

    record = result.action_records[0]

    assert record.status is ActionExecutionStatus.BLOCKED
    assert record.failure_code == "RESOURCE_REVIEW_REQUIRED"
    assert "Missing current RAM reading" in record.failure_message
    assert adapter.validation_calls == 0
    assert adapter.execution_calls == 0


def test_adapter_authorization_rejection_blocks_execution():
    adapter = FakeAdapter()
    adapter.reject_validation = True

    prepared, actions = make_prepared_plan(adapter)

    result = make_dispatcher().dispatch(
        prepared,
        resource_map(actions),
    )

    record = result.action_records[0]

    assert record.status is ActionExecutionStatus.BLOCKED
    assert record.failure_code == "ADAPTER_VALIDATION_REJECTED"
    assert adapter.validation_calls == 1
    assert adapter.execution_calls == 0


def test_adapter_exception_is_recorded_as_unknown():
    adapter = FakeAdapter()
    adapter.execution_error = TimeoutError("simulated timeout")

    prepared, actions = make_prepared_plan(adapter)

    result = make_dispatcher().dispatch(
        prepared,
        resource_map(actions),
    )

    record = result.action_records[0]

    assert record.status is ActionExecutionStatus.UNKNOWN
    assert record.failure_code == "ADAPTER_EXECUTION_OUTCOME_UNKNOWN"
    assert record.adapter_result is None
    assert adapter.execution_calls == 1


def test_adapter_reported_failure_is_preserved():
    adapter = FakeAdapter()
    adapter.result_status = ExecutionStatus.FAILED

    prepared, actions = make_prepared_plan(adapter)

    result = make_dispatcher().dispatch(
        prepared,
        resource_map(actions),
    )

    record = result.action_records[0]

    assert result.overall_status is ActionExecutionStatus.FAILED
    assert record.status is ActionExecutionStatus.FAILED
    assert record.adapter_result.status is ExecutionStatus.FAILED


def test_mismatched_adapter_result_becomes_unknown():
    adapter = FakeAdapter()
    prepared, actions = make_prepared_plan(adapter)

    adapter.result_override = None

    request = prepared[0].request
    wrong_result = AdapterExecutionResult(
        task_id=request.task.task_id,
        plan_id=request.plan.plan_id,
        action_id="different-action",
        adapter_id=adapter.adapter_id,
        selected_channel="kubernetes",
        operation=request.action.operation,
        target=request.action.target,
        environment=request.task.environment,
        status=ExecutionStatus.SUCCEEDED,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        message="Incorrect action result",
    )
    adapter.result_override = wrong_result

    result = make_dispatcher().dispatch(
        prepared,
        resource_map(actions),
    )

    record = result.action_records[0]

    assert record.status is ActionExecutionStatus.UNKNOWN
    assert record.failure_code == "INVALID_ADAPTER_RESULT"
    assert record.adapter_result is None


def test_plan_stops_after_first_failed_action():
    adapter = FakeAdapter()
    adapter.result_status = ExecutionStatus.FAILED

    prepared, actions = make_prepared_plan(
        adapter,
        action_count=2,
    )

    result = make_dispatcher().dispatch(
        prepared,
        resource_map(actions),
    )

    assert result.overall_status is ActionExecutionStatus.FAILED
    assert len(result.action_records) == 2
    assert result.action_records[0].status is ActionExecutionStatus.FAILED
    assert (
        result.action_records[1].status
        is ActionExecutionStatus.NOT_STARTED
    )
    assert adapter.execution_calls == 1


def test_every_action_requires_resource_input():
    adapter = FakeAdapter()
    prepared, _ = make_prepared_plan(adapter, action_count=2)

    with pytest.raises(ExecutionDispatchError):
        make_dispatcher().dispatch(
            prepared,
            {},
        )

    assert adapter.execution_calls == 0


def test_prepared_actions_must_cover_complete_plan():
    adapter = FakeAdapter()
    prepared, _ = make_prepared_plan(adapter, action_count=2)

    with pytest.raises(ExecutionDispatchError):
        make_dispatcher().dispatch(
            (prepared[0],),
            {
                prepared[0].request.action.action_id:
                    make_resource_input(),
            },
        )

    assert adapter.execution_calls == 0
