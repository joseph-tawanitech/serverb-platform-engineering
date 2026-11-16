"""Controlled plan execution dispatcher for TAP B22.

Uses B21's prepared-action and immutable execution-record contracts.
Resource safety must ALLOW before adapter authorization and execution.

This dispatcher is sequential: after the first non-successful action,
remaining actions are recorded as NOT_STARTED.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from uuid import uuid4

from tap_b21.adapter_contracts import (
    AdapterExecutionResult,
    ExecutionStatus,
)
from tap_b21.adapter_dispatcher import (
    ActionExecutionRecord,
    ActionExecutionStatus,
    DispatchResult,
    PreparedAction,
)
from tap_b21.resource_safety import (
    ResourceImpact,
    ResourceSafetyAssessment,
    ResourceSafetyDecision,
    ResourceSafetyGate,
    ResourceSnapshot,
)


class ExecutionDispatchError(ValueError):
    """Raised when a dispatch request is structurally invalid."""


class AdapterExecutionDispatcher:
    """Execute a prepared plan through independently authorized adapters."""

    def __init__(self, resource_safety_gate: ResourceSafetyGate) -> None:
        if not callable(getattr(resource_safety_gate, "assess", None)):
            raise TypeError(
                "resource_safety_gate must implement assess()"
            )

        self._resource_safety_gate = resource_safety_gate

    def dispatch(
        self,
        prepared_actions: tuple[PreparedAction, ...],
        resource_inputs: Mapping[
            str, tuple[ResourceSnapshot, ResourceImpact]
        ],
        *,
        attempt_number: int = 1,
    ) -> DispatchResult:
        """Dispatch every action in a prepared plan in plan order.

        resource_inputs maps each action ID to its current resource
        snapshot and estimated resource impact.

        NEEDS_HUMAN and BLOCK both stop autonomous execution.
        Human approval cannot override a hard resource BLOCK.
        """

        if not isinstance(prepared_actions, tuple) or not prepared_actions:
            raise ExecutionDispatchError(
                "prepared_actions must be a non-empty tuple"
            )

        if not isinstance(resource_inputs, Mapping):
            raise ExecutionDispatchError(
                "resource_inputs must be a mapping"
            )

        if (
            isinstance(attempt_number, bool)
            or not isinstance(attempt_number, int)
            or attempt_number < 1
        ):
            raise ExecutionDispatchError(
                "attempt_number must be a positive integer"
            )

        for prepared in prepared_actions:
            if not isinstance(prepared, PreparedAction):
                raise ExecutionDispatchError(
                    "every item must be a PreparedAction"
                )
            prepared.validate()

        first_request = prepared_actions[0].request
        task = first_request.task
        plan = first_request.plan
        grant = first_request.authorization_grant

        # All prepared actions must belong to the same task, plan and grant.
        prepared_by_id = {}

        for prepared in prepared_actions:
            request = prepared.request

            if request.task != task:
                raise ExecutionDispatchError(
                    "prepared actions do not belong to the same task"
                )

            if request.plan != plan:
                raise ExecutionDispatchError(
                    "prepared actions do not belong to the same plan"
                )

            if request.authorization_grant != grant:
                raise ExecutionDispatchError(
                    "prepared actions do not share the same authorization grant"
                )

            action_id = request.action.action_id

            if action_id in prepared_by_id:
                raise ExecutionDispatchError(
                    f"duplicate prepared action: {action_id}"
                )

            prepared_by_id[action_id] = prepared

        expected_ids = {action.action_id for action in plan.actions}

        if set(prepared_by_id) != expected_ids:
            raise ExecutionDispatchError(
                "prepared actions must cover every plan action exactly once"
            )

        if set(resource_inputs.keys()) != expected_ids:
            raise ExecutionDispatchError(
                "resource inputs must cover every plan action exactly"
            )

        for action_id, values in resource_inputs.items():
            if not isinstance(values, tuple) or len(values) != 2:
                raise ExecutionDispatchError(
                    f"resource inputs for {action_id} must be "
                    "(ResourceSnapshot, ResourceImpact)"
                )

            snapshot, impact = values

            if not isinstance(snapshot, ResourceSnapshot):
                raise ExecutionDispatchError(
                    f"invalid resource snapshot for {action_id}"
                )

            if not isinstance(impact, ResourceImpact):
                raise ExecutionDispatchError(
                    f"invalid resource impact for {action_id}"
                )

        dispatch_id = uuid4().hex
        started_at = datetime.now(timezone.utc)
        records: list[ActionExecutionRecord] = []

        halted = False
        halt_message = ""

        # Preserve the exact action order from the approved plan.
        for action in plan.actions:
            prepared = prepared_by_id[action.action_id]
            request = prepared.request

            if halted:
                record = self._make_record(
                    dispatch_id=dispatch_id,
                    attempt_number=attempt_number,
                    prepared=prepared,
                    status=ActionExecutionStatus.NOT_STARTED,
                    failure_code="PREVIOUS_ACTION_NOT_SUCCESSFUL",
                    failure_message=(
                        "Action was not started because an earlier "
                        "action did not complete successfully."
                    ),
                )
                records.append(record)
                continue

            snapshot, impact = resource_inputs[action.action_id]

            record = self._execute_one(
                dispatch_id=dispatch_id,
                attempt_number=attempt_number,
                prepared=prepared,
                snapshot=snapshot,
                impact=impact,
            )
            records.append(record)

            if record.status is not ActionExecutionStatus.SUCCEEDED:
                halted = True
                halt_message = (
                    f"Dispatch stopped after action {record.action_id} "
                    f"ended with {record.status.value}."
                )

        if all(
            record.status is ActionExecutionStatus.SUCCEEDED
            for record in records
        ):
            overall_status = ActionExecutionStatus.SUCCEEDED
            message = (
                "All actions were accepted as successful by their adapters. "
                "Independent verification is still required."
            )
        else:
            overall_status = next(
                record.status
                for record in records
                if record.status is not ActionExecutionStatus.SUCCEEDED
                and record.status is not ActionExecutionStatus.NOT_STARTED
            )
            message = (
                halt_message
                + " Remaining actions were not started."
            )

        completed_at = datetime.now(timezone.utc)

        result = DispatchResult(
            dispatch_id=dispatch_id,
            task_id=task.task_id,
            plan_id=plan.plan_id,
            grant_id=grant.grant_id,
            action_records=tuple(records),
            overall_status=overall_status,
            started_at=started_at,
            completed_at=completed_at,
            message=message,
        )
        result.validate()
        return result

    def _execute_one(
        self,
        *,
        dispatch_id: str,
        attempt_number: int,
        prepared: PreparedAction,
        snapshot: ResourceSnapshot,
        impact: ResourceImpact,
    ) -> ActionExecutionRecord:
        request = prepared.request
        action = request.action
        resource_checked_at = None
        authorization_confirmed_at = None

        # Resource assessment is fail-closed.
        try:
            assessment = self._resource_safety_gate.assess(
                snapshot,
                impact,
            )
            if not isinstance(assessment, ResourceSafetyAssessment):
                raise TypeError(
                    "resource safety gate returned an invalid assessment type"
                )
            assessment.validate()
            resource_checked_at = assessment.assessed_at

        except Exception as exc:
            return self._make_record(
                dispatch_id=dispatch_id,
                attempt_number=attempt_number,
                prepared=prepared,
                status=ActionExecutionStatus.BLOCKED,
                resource_checked_at=datetime.now(timezone.utc),
                failure_code="RESOURCE_ASSESSMENT_FAILED",
                failure_message=(
                    "Resource safety assessment failed; execution "
                    f"was blocked ({type(exc).__name__})."
                ),
            )

        if assessment.decision is ResourceSafetyDecision.BLOCK:
            return self._make_record(
                dispatch_id=dispatch_id,
                attempt_number=attempt_number,
                prepared=prepared,
                status=ActionExecutionStatus.BLOCKED,
                resource_checked_at=resource_checked_at,
                failure_code="RESOURCE_HARD_LIMIT",
                failure_message="; ".join(assessment.reasons),
            )

        if assessment.decision is ResourceSafetyDecision.NEEDS_HUMAN:
            return self._make_record(
                dispatch_id=dispatch_id,
                attempt_number=attempt_number,
                prepared=prepared,
                status=ActionExecutionStatus.BLOCKED,
                resource_checked_at=resource_checked_at,
                failure_code="RESOURCE_REVIEW_REQUIRED",
                failure_message="; ".join(assessment.reasons),
            )

        if assessment.decision is not ResourceSafetyDecision.ALLOW:
            return self._make_record(
                dispatch_id=dispatch_id,
                attempt_number=attempt_number,
                prepared=prepared,
                status=ActionExecutionStatus.BLOCKED,
                resource_checked_at=resource_checked_at,
                failure_code="INVALID_RESOURCE_DECISION",
                failure_message=(
                    "Resource gate returned an unsupported decision."
                ),
            )

        # The adapter independently verifies the signed authorization.
        try:
            prepared.adapter.validate_execution_request(request)
            authorization_confirmed_at = datetime.now(timezone.utc)

        except Exception as exc:
            return self._make_record(
                dispatch_id=dispatch_id,
                attempt_number=attempt_number,
                prepared=prepared,
                status=ActionExecutionStatus.BLOCKED,
                resource_checked_at=resource_checked_at,
                failure_code="ADAPTER_VALIDATION_REJECTED",
                failure_message=(
                    "Adapter validation or authorization was rejected "
                    f"({type(exc).__name__})."
                ),
            )

        # Once execution is invoked, an unexpected exception is UNKNOWN:
        # a remote system might have applied the operation before failing.
        try:
            adapter_result = prepared.adapter.execute_approved_request(
                request
            )
        except Exception as exc:
            return self._make_record(
                dispatch_id=dispatch_id,
                attempt_number=attempt_number,
                prepared=prepared,
                status=ActionExecutionStatus.UNKNOWN,
                resource_checked_at=resource_checked_at,
                authorization_confirmed_at=authorization_confirmed_at,
                failure_code="ADAPTER_EXECUTION_OUTCOME_UNKNOWN",
                failure_message=(
                    "Adapter raised an exception; execution may have "
                    f"partially occurred ({type(exc).__name__}). "
                    "Independent reconciliation is required."
                ),
            )

        # Never trust a malformed or mismatched adapter result as success.
        try:
            if not isinstance(adapter_result, AdapterExecutionResult):
                raise ValueError("adapter returned an invalid result type")

            adapter_result.validate()

            expected = {
                "task_id": request.task.task_id,
                "plan_id": request.plan.plan_id,
                "action_id": action.action_id,
                "adapter_id": prepared.adapter_id,
                "selected_channel": request.routed_action.selected_channel,
                "operation": action.operation,
                "target": action.target,
                "environment": request.task.environment,
            }

            for field_name, expected_value in expected.items():
                if getattr(adapter_result, field_name) != expected_value:
                    raise ValueError(
                        f"adapter result {field_name} mismatch"
                    )

        except (TypeError, ValueError):
            return self._make_record(
                dispatch_id=dispatch_id,
                attempt_number=attempt_number,
                prepared=prepared,
                status=ActionExecutionStatus.UNKNOWN,
                resource_checked_at=resource_checked_at,
                authorization_confirmed_at=authorization_confirmed_at,
                failure_code="INVALID_ADAPTER_RESULT",
                failure_message=(
                    "Adapter returned an invalid or mismatched result. "
                    "The execution outcome cannot be trusted."
                ),
            )

        status_map = {
            ExecutionStatus.SUCCEEDED: ActionExecutionStatus.SUCCEEDED,
            ExecutionStatus.FAILED: ActionExecutionStatus.FAILED,
            ExecutionStatus.TIMED_OUT: ActionExecutionStatus.TIMED_OUT,
            ExecutionStatus.UNKNOWN: ActionExecutionStatus.UNKNOWN,
        }
        status = status_map[adapter_result.status]

        failure_code = None
        failure_message = None

        if status is not ActionExecutionStatus.SUCCEEDED:
            failure_code = f"ADAPTER_{adapter_result.status.value}"
            failure_message = adapter_result.message

        return self._make_record(
            dispatch_id=dispatch_id,
            attempt_number=attempt_number,
            prepared=prepared,
            status=status,
            resource_checked_at=resource_checked_at,
            authorization_confirmed_at=authorization_confirmed_at,
            adapter_result=adapter_result,
            failure_code=failure_code,
            failure_message=failure_message,
        )

    @staticmethod
    def _make_record(
        *,
        dispatch_id: str,
        attempt_number: int,
        prepared: PreparedAction,
        status: ActionExecutionStatus,
        resource_checked_at=None,
        authorization_confirmed_at=None,
        adapter_result=None,
        failure_code=None,
        failure_message=None,
    ) -> ActionExecutionRecord:
        request = prepared.request

        record = ActionExecutionRecord(
            dispatch_id=dispatch_id,
            attempt_id=uuid4().hex,
            attempt_number=attempt_number,
            task_id=request.task.task_id,
            plan_id=request.plan.plan_id,
            action_id=request.action.action_id,
            adapter_id=prepared.adapter_id,
            selected_channel=request.routed_action.selected_channel,
            grant_id=request.authorization_grant.grant_id,
            status=status,
            prepared_at=prepared.prepared_at,
            resource_checked_at=resource_checked_at,
            authorization_confirmed_at=authorization_confirmed_at,
            adapter_result=adapter_result,
            failure_code=failure_code,
            failure_message=failure_message,
        )
        record.validate()
        return record
