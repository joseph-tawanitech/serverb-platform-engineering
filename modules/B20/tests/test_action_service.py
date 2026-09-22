"""Tests for TAP B20.7 governed security actions."""

from tap_b20.actions import SecurityActionRequest
from tap_b20.action_service import evaluate_security_action
from tap_b20.models import SecurityDecision
from tap_b20.policy import SecurityPolicy, SecurityRisk


def make_action(**overrides) -> SecurityActionRequest:
    values = {
        "action_id": "ACT-B20-001",
        "request_id": "REQ-B20-007",
        "operation": "security_check",
        "environment": "server-b-tap",
        "asset": "server-b-tap",
        "requester": "cloudman",
        "purpose": "Apply security remediation",
        "recommendation": "Run the approved security operation.",
        "risk": SecurityRisk.LOW,
    }
    values.update(overrides)
    return SecurityActionRequest(**values)


def make_policy(**overrides) -> SecurityPolicy:
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


def test_allowed_action_reuses_policy_and_requires_authority():
    result = evaluate_security_action(
        make_action(),
        make_policy(),
    )

    assert result.action_id == "ACT-B20-001"
    assert result.request_id == "REQ-B20-007"
    assert result.decision == SecurityDecision.ALLOW
    assert result.policy_id == "POL-B20-001"
    assert result.policy_version == "1.0"
    assert result.authorization_required is True


def test_review_action_requires_authority():
    result = evaluate_security_action(
        make_action(
            operation="configuration_change",
            recommendation="Apply configuration remediation.",
        ),
        make_policy(),
    )

    assert result.decision == SecurityDecision.REVIEW
    assert result.authorization_required is True


def test_blocked_action_cannot_proceed():
    result = evaluate_security_action(
        make_action(
            operation="disable_security_control",
            recommendation="Disable the security control.",
        ),
        make_policy(),
    )

    assert result.decision == SecurityDecision.BLOCK
    assert result.authorization_required is False


def test_unauthorized_asset_is_blocked():
    result = evaluate_security_action(
        make_action(asset="unauthorized-asset"),
        make_policy(),
    )

    assert result.decision == SecurityDecision.BLOCK
    assert result.risk == SecurityRisk.HIGH
    assert result.authorization_required is False
