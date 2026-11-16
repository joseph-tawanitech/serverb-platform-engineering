"""Resource safety contracts and simulated assessment for TAP B21.

The Resource Safety Gate evaluates current and projected resource usage
before controlled infrastructure execution.

This module does not authorize or execute infrastructure changes.
Live monitoring integration is intentionally deferred.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol


class ResourceSafetyDecision(str, Enum):
    """Outcome of a resource safety assessment."""

    ALLOW = "ALLOW"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    BLOCK = "BLOCK"


RESOURCE_METRICS = ("ram", "cpu", "disk")


def _require_percentage(
    value: float | None,
    field_name: str,
    *,
    optional: bool = False,
) -> None:
    """Validate a percentage value between 0 and 100."""

    if value is None:
        if optional:
            return
        raise ValueError(f"{field_name} is required")

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")

    if not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")

    if not 0 <= value <= 100:
        raise ValueError(f"{field_name} must be between 0 and 100")


def _require_nonnegative_finite(
    value: float | None,
    field_name: str,
    *,
    optional: bool = False,
) -> None:
    """Validate a finite, non-negative numeric value."""

    if value is None:
        if optional:
            return
        raise ValueError(f"{field_name} is required")

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")

    if not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")

    if value < 0:
        raise ValueError(f"{field_name} must not be negative")


def _require_aware_datetime(value: datetime, field_name: str) -> None:
    """Require a timezone-aware datetime."""

    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


@dataclass(frozen=True)
class ResourceSnapshot:
    """Current resource usage, expressed as percentages.

    A missing reading is represented by None. Missing readings prevent
    an ALLOW decision.
    """

    ram_used_percent: float | None
    cpu_used_percent: float | None
    disk_used_percent: float | None

    def validate(self) -> None:
        for metric in RESOURCE_METRICS:
            _require_percentage(
                getattr(self, f"{metric}_used_percent"),
                f"{metric}_used_percent",
                optional=True,
            )


@dataclass(frozen=True)
class ResourceImpact:
    """Estimated additional resource usage caused by an action.

    Values are percentage-point increases, not relative percentages.
    For example, a RAM impact of 5 means usage may increase by 5
    percentage points.
    """

    ram_increase_percent: float | None
    cpu_increase_percent: float | None
    disk_increase_percent: float | None

    def validate(self) -> None:
        for metric in RESOURCE_METRICS:
            value = getattr(self, f"{metric}_increase_percent")

            if value is None:
                continue

            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(
                    f"{metric}_increase_percent must be a number"
                )

            if not math.isfinite(value):
                raise ValueError(
                    f"{metric}_increase_percent must be finite"
                )

            if value < 0:
                raise ValueError(
                    f"{metric}_increase_percent cannot be negative"
                )


@dataclass(frozen=True)
class ResourceSafetyLimits:
    """Review thresholds and non-overridable hard resource limits.

    Values represent maximum permitted resource usage percentages.
    """

    ram_review_percent: float = 80.0
    cpu_review_percent: float = 85.0
    disk_review_percent: float = 80.0

    ram_hard_limit_percent: float = 90.0
    cpu_hard_limit_percent: float = 95.0
    disk_hard_limit_percent: float = 90.0

    def validate(self) -> None:
        for metric in RESOURCE_METRICS:
            review = getattr(self, f"{metric}_review_percent")
            hard_limit = getattr(
                self,
                f"{metric}_hard_limit_percent",
            )

            _require_percentage(review, f"{metric}_review_percent")
            _require_percentage(
                hard_limit,
                f"{metric}_hard_limit_percent",
            )

            if review >= hard_limit:
                raise ValueError(
                    f"{metric} review threshold must be below "
                    "its hard limit"
                )


@dataclass(frozen=True)
class ResourceSafetyAssessment:
    """Immutable result of a resource safety assessment."""

    decision: ResourceSafetyDecision
    assessed_at: datetime
    reasons: tuple[str, ...]
    projected_usage: tuple[
        tuple[str, float | None],
        ...,
    ]

    def validate(self) -> None:
        if not isinstance(self.decision, ResourceSafetyDecision):
            raise ValueError(
                "decision must be a ResourceSafetyDecision"
            )

        _require_aware_datetime(self.assessed_at, "assessed_at")

        if not isinstance(self.reasons, tuple):
            raise ValueError("reasons must be a tuple")

        if not self.reasons:
            raise ValueError("reasons must not be empty")

        for reason in self.reasons:
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError(
                    "every assessment reason must be non-empty text"
                )

        if not isinstance(self.projected_usage, tuple):
            raise ValueError("projected_usage must be a tuple")

        metric_names = set()

        for item in self.projected_usage:
            if not isinstance(item, tuple) or len(item) != 2:
                raise ValueError(
                    "each projected usage entry must be a pair"
                )

            metric, value = item

            if metric not in RESOURCE_METRICS:
                raise ValueError(
                    f"unsupported resource metric: {metric}"
                )

            if metric in metric_names:
                raise ValueError(
                    f"duplicate projected usage metric: {metric}"
                )

            metric_names.add(metric)

            _require_nonnegative_finite(
                value,
                f"{metric} projected usage",
                optional=True,
            )

        if metric_names != set(RESOURCE_METRICS):
            raise ValueError(
                "projected_usage must contain RAM, CPU and disk"
            )


class ResourceSafetyGate(Protocol):
    """Interface for a resource safety assessment provider."""

    def assess(
        self,
        snapshot: ResourceSnapshot,
        impact: ResourceImpact,
    ) -> ResourceSafetyAssessment:
        """Assess current and projected resource capacity."""
        ...


class SimulatedResourceSafetyGate:
    """Deterministic evaluator using supplied simulated readings.

    Decision rules:
    - BLOCK if current or projected usage reaches a hard limit.
    - NEEDS_HUMAN if readings or projected impact are missing.
    - NEEDS_HUMAN if projected usage reaches a review threshold.
    - ALLOW only when all readings are present and within review limits.

    A BLOCK decision cannot be overridden by human approval.
    """

    def __init__(
        self,
        limits: ResourceSafetyLimits | None = None,
    ) -> None:
        self._limits = limits or ResourceSafetyLimits()
        self._limits.validate()

    def assess(
        self,
        snapshot: ResourceSnapshot,
        impact: ResourceImpact,
    ) -> ResourceSafetyAssessment:
        if not isinstance(snapshot, ResourceSnapshot):
            raise ValueError("snapshot must be a ResourceSnapshot")

        if not isinstance(impact, ResourceImpact):
            raise ValueError("impact must be a ResourceImpact")

        snapshot.validate()
        impact.validate()

        reasons: list[str] = []
        projected_usage: list[tuple[str, float | None]] = []

        hard_limit_violations: list[str] = []
        review_warnings: list[str] = []
        missing_evidence: list[str] = []

        for metric in RESOURCE_METRICS:
            current = getattr(
                snapshot,
                f"{metric}_used_percent",
            )
            increase = getattr(
                impact,
                f"{metric}_increase_percent",
            )

            review_limit = getattr(
                self._limits,
                f"{metric}_review_percent",
            )
            hard_limit = getattr(
                self._limits,
                f"{metric}_hard_limit_percent",
            )

            if current is None:
                projected_usage.append((metric, None))
                missing_evidence.append(
                    f"Missing current {metric.upper()} reading"
                )
                continue

            if increase is None:
                projected_usage.append((metric, None))
                missing_evidence.append(
                    f"Missing projected {metric.upper()} impact"
                )

                if current >= hard_limit:
                    hard_limit_violations.append(
                        f"Current {metric.upper()} usage "
                        f"{current:.1f}% reaches hard limit "
                        f"{hard_limit:.1f}%"
                    )
                elif current >= review_limit:
                    review_warnings.append(
                        f"Current {metric.upper()} usage "
                        f"{current:.1f}% reaches review threshold "
                        f"{review_limit:.1f}%"
                    )

                continue

            projected = current + increase
            projected_usage.append((metric, projected))

            if current >= hard_limit:
                hard_limit_violations.append(
                    f"Current {metric.upper()} usage "
                    f"{current:.1f}% reaches hard limit "
                    f"{hard_limit:.1f}%"
                )

            if projected >= hard_limit:
                hard_limit_violations.append(
                    f"Projected {metric.upper()} usage "
                    f"{projected:.1f}% reaches hard limit "
                    f"{hard_limit:.1f}%"
                )
            elif projected >= review_limit:
                review_warnings.append(
                    f"Projected {metric.upper()} usage "
                    f"{projected:.1f}% reaches review threshold "
                    f"{review_limit:.1f}%"
                )

        if hard_limit_violations:
            decision = ResourceSafetyDecision.BLOCK
            reasons.extend(hard_limit_violations)
            reasons.append(
                "Hard resource limits cannot be overridden by approval"
            )

        elif missing_evidence:
            decision = ResourceSafetyDecision.NEEDS_HUMAN
            reasons.extend(missing_evidence)
            reasons.append(
                "Resource evidence is incomplete; autonomous execution "
                "is not permitted"
            )

        elif review_warnings:
            decision = ResourceSafetyDecision.NEEDS_HUMAN
            reasons.extend(review_warnings)
            reasons.append(
                "Resource usage requires human review before execution"
            )

        else:
            decision = ResourceSafetyDecision.ALLOW
            reasons.append(
                "Current and projected resource usage are within "
                "configured review thresholds and hard limits"
            )

        assessment = ResourceSafetyAssessment(
            decision=decision,
            assessed_at=datetime.now(timezone.utc),
            reasons=tuple(reasons),
            projected_usage=tuple(projected_usage),
        )

        assessment.validate()

        return assessment
