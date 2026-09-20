from __future__ import annotations

from datetime import datetime, timezone

from engine.evidence_model import Evidence


class EvidenceNormalizer:
    """Normalize collected evidence into a consistent B18 representation."""

    @staticmethod
    def normalize(evidence: Evidence) -> Evidence:
        """Normalize source, timestamps, and resource representation."""

        evidence.validate()

        evidence.source = evidence.source.strip().lower()

        evidence.collected_at = EvidenceNormalizer._to_utc(
            evidence.collected_at
        )

        if evidence.observation_time is not None:
            evidence.observation_time = EvidenceNormalizer._to_utc(
                evidence.observation_time
            )

        if evidence.resource is not None:
            evidence.resource = EvidenceNormalizer._normalize_resource(
                evidence.resource
            )

        return evidence

    @staticmethod
    def _to_utc(value: datetime) -> datetime:
        """Convert an aware datetime to UTC."""

        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")

        return value.astimezone(timezone.utc)

    @staticmethod
    def _normalize_resource(resource: str) -> str:
        """Normalize basic resource formatting."""

        normalized = resource.strip()

        if not normalized:
            return normalized

        if "/" in normalized:
            resource_type, resource_name = normalized.split("/", 1)
            return f"{resource_type.strip().lower()}/{resource_name.strip()}"

        return normalized.strip().lower()
