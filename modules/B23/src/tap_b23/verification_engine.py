"""Coordinate independent verification for complete TAP dispatches."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

from tap_b21.adapter_dispatcher import DispatchResult

from .contracts import (
    VerificationReport,
    VerificationResult,
    VerificationStatus,
    new_verification_id,
)


class VerificationEngine:
    """Run the configured independent verifier for each dispatched action."""

    def __init__(self, *, verifiers: Mapping[str, object]) -> None:
        if not isinstance(verifiers, Mapping):
            raise TypeError("verifiers must be a mapping")

        for channel, verifier in verifiers.items():
            if not isinstance(channel, str) or not channel.strip():
                raise ValueError("verifier channel must be non-empty text")

            if not callable(getattr(verifier, "verify", None)):
                raise TypeError(
                    f"verifier for {channel!r} must implement verify(record)"
                )

        self._verifiers = dict(verifiers)

    def verify_dispatch(self, dispatch: DispatchResult) -> VerificationReport:
        if not isinstance(dispatch, DispatchResult):
            raise TypeError("dispatch must be a DispatchResult")

        dispatch.validate()
        started_at = datetime.now(timezone.utc)
        results: list[VerificationResult] = []

        for record in dispatch.action_records:
            verifier = self._verifiers.get(record.selected_channel)

            if verifier is None:
                now = datetime.now(timezone.utc)
                result = VerificationResult(
                    verification_id=new_verification_id(),
                    dispatch_id=record.dispatch_id,
                    attempt_id=record.attempt_id,
                    task_id=record.task_id,
                    plan_id=record.plan_id,
                    action_id=record.action_id,
                    selected_channel=record.selected_channel,
                    execution_status=record.status,
                    status=VerificationStatus.SKIPPED,
                    started_at=now,
                    completed_at=now,
                    evidence=(),
                    message=(
                        "No independent verifier is configured for channel "
                        f"{record.selected_channel!r}."
                    ),
                )
                result.validate()
            else:
                result = verifier.verify(record)

                if not isinstance(result, VerificationResult):
                    raise TypeError(
                        "verifier must return a VerificationResult"
                    )

                result.validate()

                if result.dispatch_id != dispatch.dispatch_id:
                    raise ValueError("verifier returned a different dispatch ID")

                if result.attempt_id != record.attempt_id:
                    raise ValueError("verifier returned a different attempt ID")

                expected_identity = (
                    ("task_id", record.task_id),
                    ("plan_id", record.plan_id),
                    ("action_id", record.action_id),
                    ("selected_channel", record.selected_channel),
                    ("execution_status", record.status),
                )

                for field, expected in expected_identity:
                    if getattr(result, field) != expected:
                        raise ValueError(
                            f"verifier returned a different {field}"
                        )

            results.append(result)

        statuses = [result.status for result in results]

        if VerificationStatus.FAILED in statuses:
            overall = VerificationStatus.FAILED
            message = "At least one action failed independent verification."
        elif VerificationStatus.UNVERIFIED in statuses:
            overall = VerificationStatus.UNVERIFIED
            message = "At least one action remains unverified."
        elif all(status == VerificationStatus.SKIPPED for status in statuses):
            overall = VerificationStatus.SKIPPED
            message = "No action received independent verification."
        elif VerificationStatus.SKIPPED in statuses:
            overall = VerificationStatus.UNVERIFIED
            message = "Some actions were verified; others were skipped."
        else:
            overall = VerificationStatus.VERIFIED
            message = "All dispatched actions were independently verified."

        report = VerificationReport(
            dispatch_id=dispatch.dispatch_id,
            status=overall,
            results=tuple(results),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            message=message,
        )
        report.validate()
        return report
