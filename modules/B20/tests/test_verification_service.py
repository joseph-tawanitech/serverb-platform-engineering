import pytest

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
        message=(
            "Service restarted successfully."
            if success
            else "Service restart failed."
        ),
        evidence_ids=("EVID-001", "EVID-002"),
    )


def test_matching_observation_passes_and_creates_audit():
    verification, audit = verify_security_action(
        make_execution(success=True),
        actor="tap-authority",
        expected="Service is running",
        observed="Service is running",
    )

    assert verification.verification_status == "PASS"
    assert verification.decision == SecurityDecision.ALLOW
    assert verification.severity == SecuritySeverity.INFO
    assert verification.expected == "Service is running"
    assert verification.observed == "Service is running"
    assert verification.evidence_ids == ("EVID-001", "EVID-002")

    assert audit.request_id == "REQ-001"
    assert audit.decision == SecurityDecision.ALLOW
    assert audit.actor == "tap-authority"
    assert audit.operation == "restart_service"
    assert audit.environment == "server-b"
    assert audit.asset == "web-01"
    assert audit.is_utc()


def test_failed_execution_fails_even_if_observation_matches():
    verification, audit = verify_security_action(
        make_execution(success=False),
        actor="tap-authority",
        expected="Service is running",
        observed="Service is running",
    )

    assert verification.verification_status == "FAIL"
    assert verification.decision == SecurityDecision.REVIEW
    assert verification.severity == SecuritySeverity.HIGH
    assert audit.decision == SecurityDecision.REVIEW


def test_mismatched_observation_fails():
    verification, audit = verify_security_action(
        make_execution(success=True),
        actor="tap-authority",
        expected="Service is running",
        observed="Service is stopped",
    )

    assert verification.verification_status == "FAIL"
    assert verification.decision == SecurityDecision.REVIEW
    assert verification.severity == SecuritySeverity.HIGH
    assert verification.observed == "Service is stopped"
    assert audit.decision == SecurityDecision.REVIEW


@pytest.mark.parametrize("observed", [None, "", "   "])
def test_missing_observation_is_unverified(observed):
    verification, audit = verify_security_action(
        make_execution(success=True),
        actor="tap-authority",
        expected="Service is running",
        observed=observed,
    )

    assert verification.verification_status == "UNVERIFIED"
    assert verification.decision == SecurityDecision.REVIEW
    assert verification.severity == SecuritySeverity.MEDIUM
    assert "No independent state observation" in verification.observed
    assert audit.decision == SecurityDecision.REVIEW


def test_empty_actor_is_rejected():
    with pytest.raises(ValueError, match="actor"):
        verify_security_action(
            make_execution(success=True),
            actor="",
            expected="Service is running",
        )


def test_empty_expected_result_is_rejected():
    with pytest.raises(ValueError, match="expected"):
        verify_security_action(
            make_execution(success=True),
            actor="tap-authority",
            expected="",
        )
