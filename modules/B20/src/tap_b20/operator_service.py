"""Provider-neutral AI Security Operator service for TAP B20."""

from .operator import (
    SecurityFinding,
    SecurityInvestigationRequest,
    SecurityOperatorResult,
)
from .models import SecuritySeverity


def investigate(
    request: SecurityInvestigationRequest,
) -> SecurityOperatorResult:
    """Create a deterministic investigation result from an authorized request.

    This initial implementation establishes the B20.5 operator boundary.
    AI provider integration is intentionally handled outside this contract.
    """

    finding = SecurityFinding(
        finding_id=f"{request.request_id}-F001",
        request_id=request.request_id,
        severity=SecuritySeverity.INFO,
        title="Investigation request accepted",
        explanation=(
            "The security investigation request was accepted by the "
            "provider-neutral B20.5 operator boundary."
        ),
        evidence_ids=request.evidence_ids,
        confidence=1.0,
        recommendation=None,
    )

    return SecurityOperatorResult(
        request_id=request.request_id,
        findings=(finding,),
        summary="Security investigation request accepted.",
    )
