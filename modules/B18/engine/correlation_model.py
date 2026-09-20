from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CorrelationLink:
    """A relationship between two pieces of incident evidence."""

    source_evidence_id: str
    related_evidence_id: str
    reason: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.source_evidence_id.strip():
            raise ValueError("source_evidence_id must not be empty")

        if not self.related_evidence_id.strip():
            raise ValueError("related_evidence_id must not be empty")

        if not self.reason.strip():
            raise ValueError("reason must not be empty")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        if self.source_evidence_id == self.related_evidence_id:
            raise ValueError("evidence items cannot correlate with themselves")


@dataclass
class CorrelationGroup:
    """A group of evidence items related to the same incident context."""

    correlation_id: str
    evidence_ids: list[str]
    links: list[CorrelationLink] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.correlation_id.strip():
            raise ValueError("correlation_id must not be empty")

        if not self.evidence_ids:
            raise ValueError("evidence_ids must not be empty")

        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids must be unique")

        for link in self.links:
            link.validate()
