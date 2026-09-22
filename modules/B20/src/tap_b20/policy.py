"""Operational security policy contracts for TAP B20."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .models import SecurityDecision


class SecurityRisk(str, Enum):
    """Operational security risk classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class SecurityPolicy:
    """Policy defining what a B20 security operation may do."""

    policy_id: str
    name: str
    version: str
    environment: str
    authorized_assets: tuple[str, ...] = ()
    allowed_operations: tuple[str, ...] = ()
    review_operations: tuple[str, ...] = ()
    blocked_operations: tuple[str, ...] = ()
    max_risk: SecurityRisk = SecurityRisk.LOW
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyDecision:
    """Result of evaluating a security request against policy."""

    policy_id: str
    policy_version: str
    request_id: str
    decision: SecurityDecision
    risk: SecurityRisk
    message: str
