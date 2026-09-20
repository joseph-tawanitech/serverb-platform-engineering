from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TimelineEvent:
    """A chronological event derived from incident evidence."""

    event_id: str
    timestamp: datetime
    evidence_id: str
    source: str
    event_type: str
    description: str
    resource: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty")

        if not self.evidence_id.strip():
            raise ValueError("evidence_id must not be empty")

        if not self.source.strip():
            raise ValueError("source must not be empty")

        if not self.event_type.strip():
            raise ValueError("event_type must not be empty")

        if not self.description.strip():
            raise ValueError("description must not be empty")

        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
