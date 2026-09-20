from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SufficiencyStatus(str, Enum):
    """Investigation assessment of available evidence."""

    INSUFFICIENT = "insufficient"
    PARTIAL = "partial"
    SUFFICIENT = "sufficient"


@dataclass
class EvidenceSufficiency:
    """Assessment of whether available evidence is sufficient for a hypothesis."""

    hypothesis_id: str
    status: SufficiencyStatus
    evidence_ids: list[str] = field(default_factory=list)
    supporting_evidence_count: int = 0
    contradicting_evidence_count: int = 0
    reliable_evidence_count: int = 0
    missing_sources: list[str] = field(default_factory=list)
    confidence: float | None = None
    reasoning: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.hypothesis_id.strip():
            raise ValueError("hypothesis_id must not be empty")

        if not isinstance(self.status, SufficiencyStatus):
            raise ValueError("status must be a SufficiencyStatus")

        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids must be unique")

        if self.supporting_evidence_count < 0:
            raise ValueError("supporting_evidence_count must not be negative")

        if self.contradicting_evidence_count < 0:
            raise ValueError("contradicting_evidence_count must not be negative")

        if self.reliable_evidence_count < 0:
            raise ValueError("reliable_evidence_count must not be negative")

        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        if len(set(self.missing_sources)) != len(self.missing_sources):
            raise ValueError("missing_sources must be unique")
