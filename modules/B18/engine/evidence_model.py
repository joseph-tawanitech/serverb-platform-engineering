from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EvidenceType(str, Enum):
    METRIC = "metric"
    LOG = "log"
    TRACE = "trace"
    EVENT = "event"
    KUBERNETES_STATE = "kubernetes_state"
    COMMAND_OUTPUT = "command_output"
    CONFIGURATION = "configuration"
    ALERT = "alert"
    OTHER = "other"


class EvidenceReliability(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceStatus(str, Enum):
    COLLECTED = "collected"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class Evidence:
    evidence_id: str
    source: str
    evidence_type: EvidenceType
    collected_at: datetime

    observation_time: datetime | None = None
    resource: str | None = None
    content: Any = None
    location: str | None = None

    reliability: EvidenceReliability = EvidenceReliability.UNKNOWN
    status: EvidenceStatus = EvidenceStatus.COLLECTED

    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate the minimum structural requirements of evidence."""

        if not self.evidence_id.strip():
            raise ValueError("evidence_id must not be empty")

        if not self.source.strip():
            raise ValueError("source must not be empty")

        if not isinstance(self.evidence_type, EvidenceType):
            raise ValueError("evidence_type must be a valid EvidenceType")

        if not isinstance(self.reliability, EvidenceReliability):
            raise ValueError("reliability must be a valid EvidenceReliability")

        if not isinstance(self.status, EvidenceStatus):
            raise ValueError("status must be a valid EvidenceStatus")
