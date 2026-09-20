from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RCAStatus(str, Enum):
    """Current state of a root cause analysis."""

    NOT_ESTABLISHED = "not_established"
    PROVISIONAL = "provisional"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


@dataclass
class RootCauseAnalysis:
    """Structured root-cause conclusion derived from incident evidence."""

    incident_id: str
    status: RCAStatus
    root_cause: str | None = None
    hypothesis_id: str | None = None
    supporting_evidence_ids: list[str] = field(default_factory=list)
    contradicting_evidence_ids: list[str] = field(default_factory=list)
    affected_resources: list[str] = field(default_factory=list)
    root_cause_location: str | None = None
    contributing_factors: list[str] = field(default_factory=list)
    confidence: float | None = None
    reasoning: str | None = None
    limitations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.incident_id.strip():
            raise ValueError("incident_id must not be empty")

        if not isinstance(self.status, RCAStatus):
            raise ValueError("status must be an RCAStatus")

        if self.status in {
            RCAStatus.PROVISIONAL,
            RCAStatus.CONFIRMED,
        } and not self.root_cause:
            raise ValueError(
                "root_cause is required for provisional or confirmed RCA"
            )

        if self.hypothesis_id is not None and not self.hypothesis_id.strip():
            raise ValueError("hypothesis_id must not be empty when provided")

        if len(set(self.supporting_evidence_ids)) != len(
            self.supporting_evidence_ids
        ):
            raise ValueError("supporting_evidence_ids must be unique")

        if len(set(self.contradicting_evidence_ids)) != len(
            self.contradicting_evidence_ids
        ):
            raise ValueError("contradicting_evidence_ids must be unique")

        overlap = set(self.supporting_evidence_ids) & set(
            self.contradicting_evidence_ids
        )

        if overlap:
            raise ValueError(
                "evidence cannot simultaneously support and contradict RCA"
            )

        if len(set(self.affected_resources)) != len(self.affected_resources):
            raise ValueError("affected_resources must be unique")

        if len(set(self.contributing_factors)) != len(
            self.contributing_factors
        ):
            raise ValueError("contributing_factors must be unique")

        if len(set(self.limitations)) != len(self.limitations):
            raise ValueError("limitations must be unique")

        if self.root_cause_location is not None:
            if not self.root_cause_location.strip():
                raise ValueError(
                    "root_cause_location must not be empty when provided"
                )

        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        if self.status == RCAStatus.NOT_ESTABLISHED and self.root_cause:
            raise ValueError(
                "root_cause must be empty when RCA is not established"
            )
