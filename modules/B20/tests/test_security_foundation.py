"""Tests for TAP B20.1 security foundation controls."""

from datetime import timezone

from tap_b20.checks import run_foundation_checks
from tap_b20.models import (
    SecurityAudit,
    SecurityCheck,
    SecurityDecision,
    SecurityRequest,
    SecuritySeverity,
)


def make_request(**overrides) -> SecurityRequest:
    """Create a valid baseline security request."""
    values = {
        "request_id": "REQ-B20-001",
        "operation": "security_check",
        "environment": "server-b-tap",
        "asset": "server-b-tap",
        "requester": "cloudman",
        "purpose": "Validate security posture",
    }
    values.update(overrides)
    return SecurityRequest(**values)


def foundation_checks() -> list[SecurityCheck]:
    """Return the standard B20.1 foundation checks."""
    return [
        SecurityCheck(
            check_id="B20-SCOPE",
            name="Request Scope",
            description="Environment and asset must be defined.",
            severity=SecuritySeverity.HIGH,
        ),
        SecurityCheck(
            check_id="B20-IDENTITY",
            name="Requester Identity",
            description="Requester must be identified.",
            severity=SecuritySeverity.HIGH,
        ),
        SecurityCheck(
            check_id="B20-PURPOSE",
            name="Operational Purpose",
            description="Purpose must be stated.",
            severity=SecuritySeverity.MEDIUM,
        ),
    ]


def test_valid_request_allows_all_foundation_checks():
    results = run_foundation_checks(
        make_request(),
        foundation_checks(),
    )

    assert len(results) == 3
    assert all(result.decision == SecurityDecision.ALLOW for result in results)


def test_missing_environment_blocks_scope_check():
    results = run_foundation_checks(
        make_request(environment=""),
        foundation_checks(),
    )

    scope_result = next(
        result for result in results if result.check_id == "B20-SCOPE"
    )

    assert scope_result.decision == SecurityDecision.BLOCK
    assert scope_result.severity == SecuritySeverity.HIGH


def test_missing_asset_blocks_scope_check():
    results = run_foundation_checks(
        make_request(asset=""),
        foundation_checks(),
    )

    scope_result = next(
        result for result in results if result.check_id == "B20-SCOPE"
    )

    assert scope_result.decision == SecurityDecision.BLOCK


def test_missing_requester_blocks_identity_check():
    results = run_foundation_checks(
        make_request(requester=""),
        foundation_checks(),
    )

    identity_result = next(
        result for result in results if result.check_id == "B20-IDENTITY"
    )

    assert identity_result.decision == SecurityDecision.BLOCK
    assert identity_result.severity == SecuritySeverity.HIGH


def test_missing_purpose_blocks_purpose_check():
    results = run_foundation_checks(
        make_request(purpose=""),
        foundation_checks(),
    )

    purpose_result = next(
        result for result in results if result.check_id == "B20-PURPOSE"
    )

    assert purpose_result.decision == SecurityDecision.BLOCK
    assert purpose_result.severity == SecuritySeverity.MEDIUM


def test_disabled_check_requires_review():
    checks = foundation_checks()
    checks[0] = SecurityCheck(
        check_id="B20-SCOPE",
        name="Request Scope",
        description="Environment and asset must be defined.",
        severity=SecuritySeverity.HIGH,
        enabled=False,
    )

    results = run_foundation_checks(
        make_request(),
        checks,
    )

    scope_result = next(
        result for result in results if result.check_id == "B20-SCOPE"
    )

    assert scope_result.decision == SecurityDecision.REVIEW
    assert scope_result.severity == SecuritySeverity.MEDIUM


def test_unknown_check_requires_review():
    checks = [
        SecurityCheck(
            check_id="B20-UNKNOWN",
            name="Unknown Check",
            description="Intentional test of unknown control handling.",
            severity=SecuritySeverity.MEDIUM,
        )
    ]

    results = run_foundation_checks(
        make_request(),
        checks,
    )

    assert len(results) == 1
    assert results[0].decision == SecurityDecision.REVIEW
    assert results[0].severity == SecuritySeverity.MEDIUM


def test_security_audit_timestamp_is_utc():
    audit = SecurityAudit(
        request_id="REQ-B20-001",
        decision=SecurityDecision.ALLOW,
        actor="cloudman",
        operation="security_check",
        environment="server-b-tap",
        asset="server-b-tap",
        message="Foundation security check completed.",
    )

    assert audit.timestamp.tzinfo is not None
    assert audit.timestamp.utcoffset().total_seconds() == 0
    assert audit.is_utc()
    assert audit.timestamp.tzinfo == timezone.utc
