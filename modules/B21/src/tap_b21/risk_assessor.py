"""Deterministic, evidence-backed action risk assessment for TAP B21.

The assessor does not trust an AI-provided overall risk label.
It evaluates seven separately supplied factor classifications and
uses the highest factor as the overall action risk.

This component assesses risk. It does not authorize or execute actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tap_b20.policy import SecurityRisk


class RiskAssessmentError(ValueError):
    """Raised when risk evidence is missing or invalid."""


RISK_ORDER = {
    SecurityRisk.LOW: 1,
    SecurityRisk.MEDIUM: 2,
    SecurityRisk.HIGH: 3,
    SecurityRisk.CRITICAL: 4,
}

RISK_DIMENSIONS = (
    "impact",
    "scope",
    "availability",
    "reversibility",
    "security",
    "uncertainty",
    "resource_impact",
)


@dataclass(frozen=True)
class ActionRiskEvidence:
    """Factor classifications produced from trusted assessment evidence.

    Each dimension must be independently evaluated. The evidence
    references identify the records used to reach those classifications.
    """

    impact: SecurityRisk
    scope: SecurityRisk
    availability: SecurityRisk
    reversibility: SecurityRisk
    security: SecurityRisk
    uncertainty: SecurityRisk
    resource_impact: SecurityRisk
    evidence_refs: tuple[str, ...]
    assessor_id: str
    assessed_at: datetime

    def validate(self) -> None:
        for name in RISK_DIMENSIONS:
            value = getattr(self, name)
            if not isinstance(value, SecurityRisk):
                raise RiskAssessmentError(
                    f"{name} must be a valid SecurityRisk classification"
                )

        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise RiskAssessmentError(
                "at least one evidence reference is required"
            )

        for reference in self.evidence_refs:
            if not isinstance(reference, str) or not reference.strip():
                raise RiskAssessmentError(
                    "evidence references must be non-empty strings"
                )

        if not isinstance(self.assessor_id, str) or not self.assessor_id.strip():
            raise RiskAssessmentError("assessor_id must be non-empty text")

        if not isinstance(self.assessed_at, datetime):
            raise RiskAssessmentError("assessed_at must be a datetime")

        if (
            self.assessed_at.tzinfo is None
            or self.assessed_at.utcoffset() is None
        ):
            raise RiskAssessmentError(
                "assessed_at must be timezone-aware"
            )


@dataclass(frozen=True)
class ActionRiskAssessment:
    """Immutable, traceable risk assessment for one action."""

    action_id: str
    risk: SecurityRisk
    dimensions: tuple[tuple[str, SecurityRisk], ...]
    evidence_refs: tuple[str, ...]
    assessor_id: str
    assessed_at: datetime

    def validate(self) -> None:
        if not isinstance(self.action_id, str) or not self.action_id.strip():
            raise RiskAssessmentError("action_id must be non-empty text")

        if not isinstance(self.risk, SecurityRisk):
            raise RiskAssessmentError("risk must be a SecurityRisk")

        if not isinstance(self.dimensions, tuple):
            raise RiskAssessmentError("dimensions must be a tuple")

        names = tuple(name for name, _ in self.dimensions)
        if names != RISK_DIMENSIONS:
            raise RiskAssessmentError(
                "assessment must contain every risk dimension exactly once"
            )

        for name, value in self.dimensions:
            if not isinstance(value, SecurityRisk):
                raise RiskAssessmentError(
                    f"{name} must be a SecurityRisk classification"
                )

        expected_risk = max(
            (value for _, value in self.dimensions),
            key=RISK_ORDER.__getitem__,
        )
        if self.risk is not expected_risk:
            raise RiskAssessmentError(
                "overall risk does not match the highest factor risk"
            )

        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise RiskAssessmentError("evidence references are required")

        if not isinstance(self.assessor_id, str) or not self.assessor_id.strip():
            raise RiskAssessmentError("assessor_id must be non-empty text")

        if (
            not isinstance(self.assessed_at, datetime)
            or self.assessed_at.tzinfo is None
            or self.assessed_at.utcoffset() is None
        ):
            raise RiskAssessmentError(
                "assessed_at must be a timezone-aware datetime"
            )


class ActionRiskAssessor:
    """Calculate conservative action risk from explicit factor evidence."""

    def assess(
        self,
        action_id: str,
        evidence: ActionRiskEvidence,
    ) -> ActionRiskAssessment:
        if not isinstance(action_id, str) or not action_id.strip():
            raise RiskAssessmentError("action_id must be non-empty text")

        if not isinstance(evidence, ActionRiskEvidence):
            raise RiskAssessmentError(
                "evidence must be an ActionRiskEvidence instance"
            )

        evidence.validate()

        dimensions = tuple(
            (name, getattr(evidence, name))
            for name in RISK_DIMENSIONS
        )

        overall_risk = max(
            (value for _, value in dimensions),
            key=RISK_ORDER.__getitem__,
        )

        assessment = ActionRiskAssessment(
            action_id=action_id,
            risk=overall_risk,
            dimensions=dimensions,
            evidence_refs=evidence.evidence_refs,
            assessor_id=evidence.assessor_id,
            assessed_at=evidence.assessed_at,
        )
        assessment.validate()
        return assessment
