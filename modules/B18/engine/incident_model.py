from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    DETECTED = "detected"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    ROOT_CAUSE_IDENTIFIED = "root_cause_identified"
    RECOMMENDATION_READY = "recommendation_ready"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class EvidenceReference:
    evidence_id: str
    source: str
    description: str
    collected_at: datetime | None = None
    location: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Incident:
    incident_id: str
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    detected_at: datetime
    source: str

    affected_resources: list[str] = field(default_factory=list)
    symptoms: list[str] = field(default_factory=list)
    evidence: list[EvidenceReference] = field(default_factory=list)

    timeline: list[dict[str, Any]] = field(default_factory=list)
    impact: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)

    root_cause: str | None = None
    recommendations: list[str] = field(default_factory=list)
    confidence: float | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate the minimum structural requirements of an incident."""

        if not self.incident_id.strip():
            raise ValueError("incident_id must not be empty")

        if not self.title.strip():
            raise ValueError("title must not be empty")

        if not self.source.strip():
            raise ValueError("source must not be empty")

        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
