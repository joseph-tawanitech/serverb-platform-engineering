"""Core contracts for TAP B20 AI Security Operations."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class SecurityDecision(str, Enum):
    """Deterministic security control decision."""

    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class SecuritySeverity(str, Enum):
    """Security finding severity."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class SecurityRequest:
    """A request for a B20 security operation."""

    request_id: str
    operation: str
    environment: str
    asset: str
    requester: str
    purpose: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityCheck:
    """Definition of a deterministic security check."""

    check_id: str
    name: str
    description: str
    severity: SecuritySeverity
    enabled: bool = True


@dataclass(frozen=True)
class SecurityResult:
    """Result produced by a security check or security operation."""

    request_id: str
    check_id: str
    decision: SecurityDecision
    severity: SecuritySeverity
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityAudit:
    """Immutable record of a B20 security operation."""

    request_id: str
    decision: SecurityDecision
    actor: str
    operation: str
    environment: str
    asset: str
    message: str
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def is_utc(self) -> bool:
        """Return True when the audit timestamp is timezone-aware UTC."""
        return self.timestamp.tzinfo is not None and self.timestamp.utcoffset() is not None
