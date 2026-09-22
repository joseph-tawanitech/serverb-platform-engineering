"""Verification contracts for TAP B20.8."""

from dataclasses import dataclass, field
from typing import Any

from .models import SecurityDecision, SecuritySeverity


@dataclass(frozen=True)
class SecurityExecutionResult:
    """Observed result returned after a governed security action executes."""

    action_id: str
    request_id: str
    operation: str
    environment: str
    asset: str
    success: bool
    message: str
    evidence_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityVerificationResult:
    """Verification result for a completed security action."""

    action_id: str
    request_id: str
    verification_status: str
    decision: SecurityDecision
    severity: SecuritySeverity
    expected: str
    observed: str
    evidence_ids: tuple[str, ...] = ()
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
