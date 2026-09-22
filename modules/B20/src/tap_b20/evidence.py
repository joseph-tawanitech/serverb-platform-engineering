"""Security evidence contracts for TAP B20."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .models import SecuritySeverity


@dataclass(frozen=True)
class SecurityEvidence:
    """Normalized security evidence collected by TAP."""

    evidence_id: str
    source: str
    environment: str
    asset: str
    observation: str
    category: str
    severity: SecuritySeverity
    evidence: dict[str, Any] = field(default_factory=dict)
    policy_reference: str | None = None
    risk: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def is_utc(self) -> bool:
        """Return True when the evidence timestamp is timezone-aware UTC."""
        return (
            self.timestamp.tzinfo is not None
            and self.timestamp.utcoffset() is not None
            and self.timestamp.utcoffset().total_seconds() == 0
        )
