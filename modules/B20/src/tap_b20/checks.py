"""Deterministic security controls for TAP B20."""

from .models import (
    SecurityCheck,
    SecurityDecision,
    SecurityRequest,
    SecurityResult,
    SecuritySeverity,
)


def check_request_scope(
    request: SecurityRequest,
    check: SecurityCheck,
) -> SecurityResult:
    """Verify that the request identifies an environment and asset."""

    if not check.enabled:
        return SecurityResult(
            request_id=request.request_id,
            check_id=check.check_id,
            decision=SecurityDecision.REVIEW,
            severity=SecuritySeverity.MEDIUM,
            message="Security check is disabled and requires review.",
        )

    if not request.environment.strip() or not request.asset.strip():
        return SecurityResult(
            request_id=request.request_id,
            check_id=check.check_id,
            decision=SecurityDecision.BLOCK,
            severity=SecuritySeverity.HIGH,
            message="Security request has no defined environment or asset.",
        )

    return SecurityResult(
        request_id=request.request_id,
        check_id=check.check_id,
        decision=SecurityDecision.ALLOW,
        severity=SecuritySeverity.INFO,
        message="Security request has a defined environment and asset.",
        evidence={
            "environment": request.environment,
            "asset": request.asset,
        },
    )


def check_request_identity(
    request: SecurityRequest,
    check: SecurityCheck,
) -> SecurityResult:
    """Verify that the request identifies its requester."""

    if not check.enabled:
        return SecurityResult(
            request_id=request.request_id,
            check_id=check.check_id,
            decision=SecurityDecision.REVIEW,
            severity=SecuritySeverity.MEDIUM,
            message="Security check is disabled and requires review.",
        )

    if not request.requester.strip():
        return SecurityResult(
            request_id=request.request_id,
            check_id=check.check_id,
            decision=SecurityDecision.BLOCK,
            severity=SecuritySeverity.HIGH,
            message="Security request has no identified requester.",
        )

    return SecurityResult(
        request_id=request.request_id,
        check_id=check.check_id,
        decision=SecurityDecision.ALLOW,
        severity=SecuritySeverity.INFO,
        message="Security request has an identified requester.",
        evidence={"requester": request.requester},
    )


def check_request_purpose(
    request: SecurityRequest,
    check: SecurityCheck,
) -> SecurityResult:
    """Verify that the request states an operational purpose."""

    if not check.enabled:
        return SecurityResult(
            request_id=request.request_id,
            check_id=check.check_id,
            decision=SecurityDecision.REVIEW,
            severity=SecuritySeverity.MEDIUM,
            message="Security check is disabled and requires review.",
        )

    if not request.purpose.strip():
        return SecurityResult(
            request_id=request.request_id,
            check_id=check.check_id,
            decision=SecurityDecision.BLOCK,
            severity=SecuritySeverity.MEDIUM,
            message="Security request has no stated purpose.",
        )

    return SecurityResult(
        request_id=request.request_id,
        check_id=check.check_id,
        decision=SecurityDecision.ALLOW,
        severity=SecuritySeverity.INFO,
        message="Security request has a stated operational purpose.",
        evidence={"purpose": request.purpose},
    )


def run_foundation_checks(
    request: SecurityRequest,
    checks: list[SecurityCheck],
) -> list[SecurityResult]:
    """Run the B20.1 deterministic foundation checks."""

    results: list[SecurityResult] = []

    for check in checks:
        if check.check_id == "B20-SCOPE":
            results.append(check_request_scope(request, check))
        elif check.check_id == "B20-IDENTITY":
            results.append(check_request_identity(request, check))
        elif check.check_id == "B20-PURPOSE":
            results.append(check_request_purpose(request, check))
        else:
            results.append(
                SecurityResult(
                    request_id=request.request_id,
                    check_id=check.check_id,
                    decision=SecurityDecision.REVIEW,
                    severity=SecuritySeverity.MEDIUM,
                    message="Unknown security check requires review.",
                )
            )

    return results
