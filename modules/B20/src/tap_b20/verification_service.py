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
    observed: str | None = None,
) -> tuple[SecurityVerificationResult, SecurityAudit]:
    """Evaluate execution and an explicitly supplied state observation.

    The caller is responsible for obtaining `observed` from a suitable
    verification mechanism. This service does not query infrastructure itself.
    """

    if not actor.strip():
        raise ValueError("actor must not be empty")

    if not expected.strip():
        raise ValueError("expected must not be empty")

    expected_state = expected.strip()
    observed_state = observed.strip() if observed and observed.strip() else None

    if not execution.success:
        status = "FAIL"
        message = "Security action execution failed."
    elif observed_state is None:
        status = "UNVERIFIED"
        message = "No independent state observation was supplied."
    elif observed_state != expected_state:
        status = "FAIL"
        message = "Observed state does not match the expected state."
    else:
        status = "PASS"
        message = "Observed state matches the expected state."

    decision = (
        SecurityDecision.ALLOW
        if status == "PASS"
        else SecurityDecision.REVIEW
    )

    severity = {
        "PASS": SecuritySeverity.INFO,
        "FAIL": SecuritySeverity.HIGH,
        "UNVERIFIED": SecuritySeverity.MEDIUM,
    }[status]

    verification = SecurityVerificationResult(
        action_id=execution.action_id,
        request_id=execution.request_id,
        verification_status=status,
        decision=decision,
        severity=severity,
        expected=expected_state,
        observed=(
            observed_state
            if observed_state is not None
            else "No independent state observation available."
        ),
        evidence_ids=execution.evidence_ids,
        message=message,
        metadata=dict(execution.metadata),
    )

    audit = SecurityAudit(
        request_id=execution.request_id,
        decision=decision,
        actor=actor,
        operation=execution.operation,
        environment=execution.environment,
        asset=execution.asset,
        message=message,
    )

    return verification, audit
