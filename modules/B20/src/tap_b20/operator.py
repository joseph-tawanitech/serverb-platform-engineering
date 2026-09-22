"""AI Security Operator contracts for TAP B20."""

from dataclasses import dataclass, field
from typing import Any

from .models import SecuritySeverity


@dataclass(frozen=True)
class SecurityInvestigationRequest:
    """Request for the AI Security Operator to investigate evidence."""

    request_id: str
    environment: str
    asset: str
    question: str
    prompt: str = ""
    evidence_ids: tuple[str, ...] = ()
    knowledge_context: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityFinding:
    """Finding produced by the AI Security Operator."""

    finding_id: str
    request_id: str
    severity: SecuritySeverity
    title: str
    explanation: str
    evidence_ids: tuple[str, ...] = ()
    confidence: float = 0.0
    recommendation: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityOperatorResult:
    """Provider-neutral result returned by the security operator."""

    request_id: str
    findings: tuple[SecurityFinding, ...] = ()
    summary: str = ""
    provider: str | None = None
    model: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
