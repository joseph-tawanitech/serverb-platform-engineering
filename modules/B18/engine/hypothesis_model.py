from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HypothesisStatus(str, Enum):
    """Current investigation state of a hypothesis."""

    PROPOSED = "proposed"
    TESTING = "testing"
    SUPPORTED = "supported"
    WEAKENED = "weakened"
    REJECTED = "rejected"


@dataclass
class Hypothesis:
    """A possible explanation for correlated incident evidence."""

    hypothesis_id: str
    statement: str
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    supporting_evidence_ids: list[str] = field(default_factory=list)
    contradicting_evidence_ids: list[str] = field(default_factory=list)
    confidence: float | None = None
    affected_resources: list[str] = field(default_factory=list)
    reasoning: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.hypothesis_id.strip():
            raise ValueError("hypothesis_id must not be empty")

        if not self.statement.strip():
            raise ValueError("statement must not be empty")

        if not isinstance(self.status, HypothesisStatus):
            raise ValueError("status must be a HypothesisStatus")

        if len(set(self.supporting_evidence_ids)) != len(
            self.supporting_evidence_ids
        ):
            raise ValueError("supporting_evidence_ids must be unique")

        if len(set(self.contradicting_evidence_ids)) != len(
            self.contradicting_evidence_ids
        ):
            raise ValueError("contradicting_evidence_ids must be unique")

        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        overlap = set(self.supporting_evidence_ids) & set(
            self.contradicting_evidence_ids
        )

        if overlap:
            raise ValueError(
                "evidence cannot simultaneously support and contradict "
                "the same hypothesis"
            )

        if len(set(self.affected_resources)) != len(self.affected_resources):
            raise ValueError("affected_resources must be unique")
