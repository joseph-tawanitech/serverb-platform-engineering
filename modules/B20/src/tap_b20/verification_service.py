"""Verification and audit service for TAP B20.8."""

from .models import SecurityAudit, SecurityDecision, SecuritySeverity
from .verification import (
    SecurityExecutionResult,
    SecurityVerificationResult,
)


def verify_security_action(
    execution: SecurityExecutionResult,
    *,
    actor: str,
    expected: str,
) -> tuple[SecurityVerificationResult, SecurityAudit]:
    """Verify an execution result and create the corresponding audit record."""

    if not actor.strip():
        raise ValueError("actor must not be empty")

    if not expected.strip():
        raise ValueError("expected must not be empty")

    status = "PASS" if execution.success else "FAIL"
    decision = (
        SecurityDecision.ALLOW
        if execution.success
        else SecurityDecision.REVIEW
    )
    severity = (
        SecuritySeverity.INFO
        if execution.success
        else SecuritySeverity.HIGH
    )

    verification = SecurityVerificationResult(
        action_id=execution.action_id,
        request_id=execution.request_id,
        verification_status=status,
        decision=decision,
        severity=severity,
        expected=expected,
        observed=execution.message,
        evidence_ids=execution.evidence_ids,
        message=(
            "Security action verification passed."
            if execution.success
            else "Security action verification failed."
        ),
        metadata=dict(execution.metadata),
    )

    audit = SecurityAudit(
        request_id=execution.request_id,
        decision=decision,
        actor=actor,
        operation=execution.operation,
        environment=execution.environment,
        asset=execution.asset,
        message=verification.message,
    )

    return verification, audit
