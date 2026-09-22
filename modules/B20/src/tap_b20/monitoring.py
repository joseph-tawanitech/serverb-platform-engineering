"""Security monitoring contracts for TAP B20."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .models import SecuritySeverity


@dataclass(frozen=True)
class SecurityObservation:
    """A normalized observation produced by a security monitoring source."""

    observation_id: str
    source: str
    environment: str
    asset: str
    observation: str
    category: str
    severity: SecuritySeverity
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def is_utc(self) -> bool:
        """Return True when the observation timestamp is UTC."""
        return (
            self.timestamp.tzinfo is not None
            and self.timestamp.utcoffset() is not None
            and self.timestamp.utcoffset().total_seconds() == 0
        )
