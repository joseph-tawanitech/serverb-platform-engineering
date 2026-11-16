"""Independent verification contracts for TAP B23."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import uuid4

from tap_b21.adapter_dispatcher import ActionExecutionStatus


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    UNVERIFIED = "UNVERIFIED"
    SKIPPED = "SKIPPED"


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")


def _require_aware_datetime(value: datetime, field: str) -> None:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(f"{field} must be timezone-aware")


@dataclass(frozen=True)
class VerificationResult:
    """Immutable verification outcome for one execution attempt."""

    verification_id: str
    dispatch_id: str
    attempt_id: str
    task_id: str
    plan_id: str
    action_id: str
    selected_channel: str
    execution_status: ActionExecutionStatus
    status: VerificationStatus
    started_at: datetime
    completed_at: datetime
    evidence: tuple[str, ...]
    message: str

    def validate(self) -> None:
        for field in (
            "verification_id",
            "dispatch_id",
            "attempt_id",
            "task_id",
            "plan_id",
            "action_id",
            "selected_channel",
            "message",
        ):
            _require_text(getattr(self, field), field)

        if not isinstance(self.execution_status, ActionExecutionStatus):
            raise ValueError("invalid execution_status")

        if not isinstance(self.status, VerificationStatus):
            raise ValueError("invalid verification status")

        _require_aware_datetime(self.started_at, "started_at")
        _require_aware_datetime(self.completed_at, "completed_at")

        if self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at")

        if not isinstance(self.evidence, tuple):
            raise ValueError("evidence must be a tuple")

        for item in self.evidence:
            _require_text(item, "evidence item")

        if self.status == VerificationStatus.VERIFIED and not self.evidence:
            raise ValueError("VERIFIED requires evidence")


def new_verification_id() -> str:
    return uuid4().hex


@dataclass(frozen=True)
class VerificationReport:
    """Immutable verification summary for one complete dispatch."""

    dispatch_id: str
    status: VerificationStatus
    results: tuple[VerificationResult, ...]
    started_at: datetime
    completed_at: datetime
    message: str

    def validate(self) -> None:
        _require_text(self.dispatch_id, "dispatch_id")
        _require_text(self.message, "message")

        if not isinstance(self.status, VerificationStatus):
            raise ValueError("invalid report status")

        if not isinstance(self.results, tuple) or not self.results:
            raise ValueError("results must be a non-empty tuple")

        _require_aware_datetime(self.started_at, "started_at")
        _require_aware_datetime(self.completed_at, "completed_at")

        if self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at")

        attempt_ids: set[str] = set()

        for result in self.results:
            if not isinstance(result, VerificationResult):
                raise ValueError("results must contain VerificationResult")

            result.validate()

            if result.dispatch_id != self.dispatch_id:
                raise ValueError("verification dispatch ID mismatch")

            if result.attempt_id in attempt_ids:
                raise ValueError("duplicate verification attempt")

            attempt_ids.add(result.attempt_id)
