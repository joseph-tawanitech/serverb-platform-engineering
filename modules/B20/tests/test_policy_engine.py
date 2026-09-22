"""Tests for TAP B20.2 operational security policy evaluation."""

from tap_b20.models import SecurityDecision, SecurityRequest
from tap_b20.policy import SecurityPolicy, SecurityRisk
from tap_b20.policy_engine import evaluate_policy


def make_request(**overrides) -> SecurityRequest:
    """Create a valid baseline security request."""
    values = {
        "request_id": "REQ-B20-002",
        "operation": "security_check",
        "environment": "server-b-tap",
        "asset": "server-b-tap",
        "requester": "cloudman",
        "purpose": "Validate security posture",
    }
    values.update(overrides)
    return SecurityRequest(**values)


def make_policy(**overrides) -> SecurityPolicy:
    """Create a valid baseline operational security policy."""
    values = {
        "policy_id": "POL-B20-001",
        "name": "Server B Security Policy",
        "version": "1.0",
        "environment": "server-b-tap",
        "authorized_assets": ("server-b-tap",),
        "allowed_operations": ("security_check",),
        "review_operations": ("configuration_change",),
        "blocked_operations": ("disable_security_control",),
        "max_risk": SecurityRisk.LOW,
        "enabled": True,
    }
    values.update(overrides)
    return SecurityPolicy(**values)


def test_allowed_operation_returns_allow():
    result = evaluate_policy(
        make_request(),
        make_policy(),
    )

    assert result.decision == SecurityDecision.ALLOW
    assert result.policy_id == "POL-B20-001"
    assert result.policy_version == "1.0"


def test_wrong_environment_returns_block():
    result = evaluate_policy(
        make_request(environment="unknown-environment"),
        make_policy(),
    )

    assert result.decision == SecurityDecision.BLOCK
    assert result.risk == SecurityRisk.CRITICAL


def test_unauthorized_asset_returns_block():
    result = evaluate_policy(
        make_request(asset="unauthorized-asset"),
        make_policy(),
    )

    assert result.decision == SecurityDecision.BLOCK
    assert result.risk == SecurityRisk.HIGH


def test_blocked_operation_returns_block():
    result = evaluate_policy(
        make_request(operation="disable_security_control"),
        make_policy(),
    )

    assert result.decision == SecurityDecision.BLOCK


def test_review_operation_returns_review():
    result = evaluate_policy(
        make_request(operation="configuration_change"),
        make_policy(),
    )

    assert result.decision == SecurityDecision.REVIEW


def test_unknown_operation_returns_review():
    result = evaluate_policy(
        make_request(operation="unknown_operation"),
        make_policy(),
    )

    assert result.decision == SecurityDecision.REVIEW


def test_disabled_policy_returns_review():
    result = evaluate_policy(
        make_request(),
        make_policy(enabled=False),
    )

    assert result.decision == SecurityDecision.REVIEW


def test_policy_max_risk_is_preserved():
    result = evaluate_policy(
        make_request(operation="configuration_change"),
        make_policy(max_risk=SecurityRisk.HIGH),
    )

    assert result.risk == SecurityRisk.HIGH
    assert result.decision == SecurityDecision.REVIEW
