from __future__ import annotations

from typing import Iterable

from engine.evidence_model import Evidence
from engine.timeline_model import TimelineEvent


class TimelineBuilder:
    """Build chronological timeline events from normalized evidence."""

    @staticmethod
    def from_evidence(evidence: Evidence) -> TimelineEvent:
        """Convert one evidence record into a timeline event."""
        evidence.validate()

        timestamp = evidence.observation_time or evidence.collected_at

        description = TimelineBuilder._build_description(evidence)

        event = TimelineEvent(
            event_id=f"TL-{evidence.evidence_id}",
            timestamp=timestamp,
            evidence_id=evidence.evidence_id,
            source=evidence.source,
            event_type=evidence.evidence_type.value,
            description=description,
            resource=evidence.resource,
            metadata={
                **evidence.metadata,
                "evidence_status": evidence.status.value,
                "evidence_reliability": evidence.reliability.value,
            },
        )

        event.validate()
        return event

    @staticmethod
    def build(evidence_items: Iterable[Evidence]) -> list[TimelineEvent]:
        """Build and chronologically sort timeline events."""
        events = [
            TimelineBuilder.from_evidence(evidence)
            for evidence in evidence_items
        ]

        return sorted(events, key=lambda event: event.timestamp)

    @staticmethod
    def _build_description(evidence: Evidence) -> str:
        """Create a concise timeline description without replacing raw evidence."""
        if isinstance(evidence.content, dict):
            description = evidence.content.get("description")

            if isinstance(description, str) and description.strip():
                return description.strip()

        resource = evidence.resource or "unknown-resource"

        return (
            f"{evidence.evidence_type.value} evidence from "
            f"{evidence.source} for {resource}"
        )
