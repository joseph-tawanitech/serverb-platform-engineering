"""Coordinate independent verification and durable audit recording."""

from __future__ import annotations

from typing import Protocol

from tap_b21.adapter_dispatcher import DispatchResult

from .contracts import VerificationReport
from .recorder import RecordedDispatch
from .verification_engine import VerificationEngine


class DispatchRecorder(Protocol):
    """Storage interface supported by B23 recorder implementations."""

    def record(
        self,
        dispatch: DispatchResult,
        verification: VerificationReport,
    ) -> RecordedDispatch:
        ...


class VerificationRecordingService:
    """Verify a dispatch and record its execution and verification history."""

    def __init__(
        self,
        *,
        verification_engine: VerificationEngine,
        recorder: DispatchRecorder,
    ) -> None:
        if not callable(
            getattr(verification_engine, "verify_dispatch", None)
        ):
            raise TypeError(
                "verification_engine must implement verify_dispatch"
            )

        if not callable(getattr(recorder, "record", None)):
            raise TypeError("recorder must implement record")

        self._verification_engine = verification_engine
        self._recorder = recorder

    def verify_and_record(
        self,
        dispatch: DispatchResult,
    ) -> RecordedDispatch:
        if not isinstance(dispatch, DispatchResult):
            raise TypeError("dispatch must be a DispatchResult")

        verification = self._verification_engine.verify_dispatch(dispatch)

        return self._recorder.record(dispatch, verification)
