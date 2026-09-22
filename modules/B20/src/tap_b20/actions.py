"""Governed security action contracts for TAP B20.7."""

from dataclasses import dataclass, field
from typing import Any

from .models import SecurityDecision
from .policy import SecurityRisk


@dataclass(frozen=True)
class SecurityActionRequest:
    """A proposed security action awaiting governed policy evaluation."""

    action_id: str
    request_id: str
    operation: str
    environment: str
    asset: str
    requester: str
    purpose: str
    recommendation: str
    risk: SecurityRisk = SecurityRisk.LOW
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityActionDecision:
    """Governed decision for a proposed security action."""

    action_id: str
    request_id: str
    decision: SecurityDecision
    risk: SecurityRisk
    policy_id: str
    policy_version: str
    authorization_required: bool
    message: str
