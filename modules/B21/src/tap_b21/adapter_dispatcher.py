
"""Dispatcher contracts for TAP B21.

These contracts describe dispatch attempts and their outcomes.
They do not perform adapter selection, authorization or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .adapter_contracts import (
    AdapterExecutionResult,
    ExecutionStatus,
)
from .contracts import SUPPORTED_CHANNELS


class ActionExecutionStatus(str, Enum):
    """Lifecycle status of an individual dispatcher action attempt."""

    NOT_STARTED = "NOT_STARTED"
    PREPARED = "PREPARED"
    BLOCKED = "BLOCKED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    UNKNOWN = "UNKNOWN"


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_optional_text(
    value: str | None,
    field_name: str,
) -> None:
    if value is not None:
        _require_text(value, field_name)


def _require_aware_datetime(
    value: datetime | None,
    field_name: str,
) -> None:
    if value is None:
        return

    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _validate_adapter_result(
    result: AdapterExecutionResult,
    *,
    task_id: str,
    plan_id: str,
    action_id: str,
    adapter_id: str | None,
    selected_channel: str,
    status: ActionExecutionStatus,
) -> None:
    if not isinstance(result, AdapterExecutionResult):
        raise ValueError(
            "adapter_result must be an AdapterExecutionResult"
        )

    result.validate()

    expected_statuses = {
        ActionExecutionStatus.SUCCEEDED: ExecutionStatus.SUCCEEDED,
        ActionExecutionStatus.FAILED: ExecutionStatus.FAILED,
        ActionExecutionStatus.TIMED_OUT: ExecutionStatus.TIMED_OUT,
        ActionExecutionStatus.UNKNOWN: ExecutionStatus.UNKNOWN,
    }

    expected_adapter_status = expected_statuses.get(status)

    if expected_adapter_status is None:
        raise ValueError(
            "adapter_result is not valid for this dispatcher status"
        )

    if result.status != expected_adapter_status:
        raise ValueError(
            "adapter result status does not match dispatcher status"
        )

    if result.task_id != task_id:
        raise ValueError("adapter result task ID mismatch")

    if result.plan_id != plan_id:
        raise ValueError("adapter result plan ID mismatch")

    if result.action_id != action_id:
        raise ValueError("adapter result action ID mismatch")

    if adapter_id is not None and result.adapter_id != adapter_id:
        raise ValueError("adapter result adapter ID mismatch")

    if result.selected_channel != selected_channel:
        raise ValueError("adapter result channel mismatch")


@dataclass(frozen=True)
class ActionExecutionRecord:
    """Immutable record of one individual action attempt."""

    dispatch_id: str
    attempt_id: str
    attempt_number: int
    task_id: str
    plan_id: str
    action_id: str
    adapter_id: str | None
    selected_channel: str
    grant_id: str
    status: ActionExecutionStatus
    prepared_at: datetime
    resource_checked_at: datetime | None = None
    authorization_confirmed_at: datetime | None = None
    adapter_result: AdapterExecutionResult | None = None
    failure_code: str | None = None
    failure_message: str | None = None

    def validate(self) -> None:
        for field_name in (
            "dispatch_id",
            "attempt_id",
            "task_id",
            "plan_id",
            "action_id",
            "selected_channel",
            "grant_id",
        ):
            _require_text(getattr(self, field_name), field_name)

        _require_optional_text(self.adapter_id, "adapter_id")
        _require_optional_text(self.failure_code, "failure_code")
        _require_optional_text(self.failure_message, "failure_message")

        if (
            isinstance(self.attempt_number, bool)
            or not isinstance(self.attempt_number, int)
            or self.attempt_number < 1
        ):
            raise ValueError("attempt_number must be a positive integer")

        if not isinstance(self.status, ActionExecutionStatus):
            raise ValueError("status must be an ActionExecutionStatus")

        if self.selected_channel not in SUPPORTED_CHANNELS:
            raise ValueError("unsupported selected_channel")

        if self.prepared_at is None:
            raise ValueError("prepared_at is required")

        _require_aware_datetime(self.prepared_at, "prepared_at")
        _require_aware_datetime(
            self.resource_checked_at,
            "resource_checked_at",
        )
        _require_aware_datetime(
            self.authorization_confirmed_at,
            "authorization_confirmed_at",
        )

        if self.resource_checked_at is not None:
            if self.resource_checked_at < self.prepared_at:
                raise ValueError(
                    "resource_checked_at cannot precede prepared_at"
                )

        if self.authorization_confirmed_at is not None:
            if self.authorization_confirmed_at < self.prepared_at:
                raise ValueError(
                    "authorization_confirmed_at cannot precede prepared_at"
                )

        if self.adapter_result is not None:
            _validate_adapter_result(
                self.adapter_result,
                task_id=self.task_id,
                plan_id=self.plan_id,
                action_id=self.action_id,
                adapter_id=self.adapter_id,
                selected_channel=self.selected_channel,
                status=self.status,
            )

        if (
            self.status
            in {
                ActionExecutionStatus.NOT_STARTED,
                ActionExecutionStatus.PREPARED,
                ActionExecutionStatus.BLOCKED,
                ActionExecutionStatus.EXECUTING,
            }
            and self.adapter_result is not None
        ):
            raise ValueError(
                "adapter_result is not valid before a terminal outcome"
            )

        if (
            self.status == ActionExecutionStatus.SUCCEEDED
            and self.adapter_result is None
        ):
            raise ValueError(
                "SUCCEEDED requires an adapter execution result"
            )


@dataclass(frozen=True)
class DispatchResult:
    """Immutable summary of one plan dispatch operation."""

    dispatch_id: str
    task_id: str
    plan_id: str
    grant_id: str
    action_records: tuple[ActionExecutionRecord, ...]
    overall_status: ActionExecutionStatus
    started_at: datetime
    completed_at: datetime | None
    message: str

    def validate(self) -> None:
        for field_name in (
            "dispatch_id",
            "task_id",
            "plan_id",
            "grant_id",
            "message",
        ):
            _require_text(getattr(self, field_name), field_name)

        if not isinstance(self.action_records, tuple):
            raise ValueError("action_records must be a tuple")

        if not self.action_records:
            raise ValueError("action_records must not be empty")

        if not isinstance(self.overall_status, ActionExecutionStatus):
            raise ValueError(
                "overall_status must be an ActionExecutionStatus"
            )

        if self.started_at is None:
            raise ValueError("started_at is required")

        _require_aware_datetime(self.started_at, "started_at")
        _require_aware_datetime(self.completed_at, "completed_at")

        if (
            self.completed_at is not None
            and self.completed_at < self.started_at
        ):
            raise ValueError(
                "completed_at cannot precede started_at"
            )

        attempt_ids: set[str] = set()
        action_attempts: set[tuple[str, int]] = set()

        for record in self.action_records:
            if not isinstance(record, ActionExecutionRecord):
                raise ValueError(
                    "every action record must be an ActionExecutionRecord"
                )

            record.validate()

            if record.dispatch_id != self.dispatch_id:
                raise ValueError("action record dispatch ID mismatch")

            if record.task_id != self.task_id:
                raise ValueError("action record task ID mismatch")

            if record.plan_id != self.plan_id:
                raise ValueError("action record plan ID mismatch")

            if record.grant_id != self.grant_id:
                raise ValueError("action record grant ID mismatch")

            if record.attempt_id in attempt_ids:
                raise ValueError("attempt IDs must be unique")

            attempt_ids.add(record.attempt_id)

            action_attempt = (record.action_id, record.attempt_number)
            if action_attempt in action_attempts:
                raise ValueError(
                    "attempt numbers must be unique per action"
                )

            action_attempts.add(action_attempt)
