"""Append-only in-memory recording for TAP B23."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

from tap_b21.adapter_dispatcher import DispatchResult

from .contracts import VerificationReport


class RecorderError(ValueError):
    """Raised when a recording operation is rejected."""


@dataclass(frozen=True)
class RecordedDispatch:
    """Immutable execution and verification history for one dispatch."""

    dispatch: DispatchResult
    verification: VerificationReport

    def validate(self) -> None:
        if not isinstance(self.dispatch, DispatchResult):
            raise RecorderError("dispatch must be a DispatchResult")

        if not isinstance(self.verification, VerificationReport):
            raise RecorderError(
                "verification must be a VerificationReport"
            )

        self.dispatch.validate()
        self.verification.validate()

        if self.dispatch.dispatch_id != self.verification.dispatch_id:
            raise RecorderError("dispatch ID mismatch")

        execution_by_attempt = {
            record.attempt_id: record
            for record in self.dispatch.action_records
        }

        verification_by_attempt = {
            result.attempt_id: result
            for result in self.verification.results
        }

        if set(execution_by_attempt) != set(verification_by_attempt):
            raise RecorderError(
                "execution and verification attempts do not match"
            )

        for attempt_id, execution in execution_by_attempt.items():
            result = verification_by_attempt[attempt_id]

            expected_identity = (
                execution.dispatch_id,
                execution.task_id,
                execution.plan_id,
                execution.action_id,
                execution.selected_channel,
                execution.status,
            )

            actual_identity = (
                result.dispatch_id,
                result.task_id,
                result.plan_id,
                result.action_id,
                result.selected_channel,
                result.execution_status,
            )

            if actual_identity != expected_identity:
                raise RecorderError(
                    f"verification identity mismatch for attempt {attempt_id}"
                )


class AppendOnlyRecorder:
    """Thread-safe, process-local append-only dispatch recorder.

    This implementation is for development and testing.
    It does not provide durable storage across process restarts.
    """

    def __init__(self) -> None:
        self._records: dict[str, RecordedDispatch] = {}
        self._lock = RLock()

    def record(
        self,
        dispatch: DispatchResult,
        verification: VerificationReport,
    ) -> RecordedDispatch:
        entry = RecordedDispatch(
            dispatch=dispatch,
            verification=verification,
        )
        entry.validate()

        with self._lock:
            dispatch_id = dispatch.dispatch_id

            if dispatch_id in self._records:
                raise RecorderError(
                    "dispatch has already been recorded"
                )

            self._records[dispatch_id] = entry

        return entry

    def get(self, dispatch_id: str) -> RecordedDispatch:
        if not isinstance(dispatch_id, str) or not dispatch_id.strip():
            raise RecorderError("dispatch_id must be non-empty text")

        with self._lock:
            entry = self._records.get(dispatch_id)

            if entry is None:
                raise RecorderError("dispatch has not been recorded")

            return entry

    def list_records(self) -> tuple[RecordedDispatch, ...]:
        with self._lock:
            return tuple(self._records.values())

    def __len__(self) -> int:
        with self._lock:
            return len(self._records)
