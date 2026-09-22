from tap_b20.models import SecurityDecision, SecuritySeverity
from tap_b20.verification import SecurityExecutionResult
from tap_b20.verification_service import verify_security_action


def make_execution(*, success: bool) -> SecurityExecutionResult:
    return SecurityExecutionResult(
        action_id="ACT-001",
        request_id="REQ-001",
        operation="restart_service",
        environment="server-b",
        asset="web-01",
        success=success,
        message="Service restarted successfully."
        if success
        else "Service restart failed.",
        evidence_ids=("EVID-001", "EVID-002"),
    )


def test_successful_execution_verifies_and_creates_audit():
    verification, audit = verify_security_action(
        make_execution(success=True),
        actor="tap-authority",
        expected="Service is running",
    )

    assert verification.verification_status == "PASS"
    assert verification.decision == SecurityDecision.ALLOW
    assert verification.severity == SecuritySeverity.INFO
    assert verification.evidence_ids == ("EVID-001", "EVID-002")

    assert audit.request_id == "REQ-001"
    assert audit.decision == SecurityDecision.ALLOW
    assert audit.actor == "tap-authority"
    assert audit.operation == "restart_service"
    assert audit.asset == "web-01"
    assert audit.is_utc()


def test_failed_execution_produces_failed_verification_and_audit():
    execution = make_execution(success=False)

    verification, audit = verify_security_action(
        execution,
        actor="tap-authority",
        expected="Service is running",
    )

    assert verification.verification_status == "FAIL"
    assert verification.decision == SecurityDecision.REVIEW
    assert verification.severity == SecuritySeverity.HIGH
    assert verification.observed == "Service restart failed."

    assert audit.decision == SecurityDecision.REVIEW
    assert audit.actor == "tap-authority"


def test_empty_actor_is_rejected():
    try:
        verify_security_action(
            make_execution(success=True),
            actor="",
            expected="Service is running",
        )
    except ValueError as exc:
        assert "actor" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_empty_expected_result_is_rejected():
    try:
        verify_security_action(
            make_execution(success=True),
            actor="tap-authority",
            expected="",
        )
    except ValueError as exc:
        assert "expected" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
