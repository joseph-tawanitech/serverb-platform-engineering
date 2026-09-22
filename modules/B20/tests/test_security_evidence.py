"""Tests for TAP B20.3 security evidence contracts."""

from datetime import datetime, timezone

from tap_b20.evidence import SecurityEvidence
from tap_b20.models import SecuritySeverity


def make_evidence(**overrides) -> SecurityEvidence:
    """Create a valid baseline security evidence record."""
    values = {
        "evidence_id": "EVD-B20-001",
        "source": "linux",
        "environment": "server-b-tap",
        "asset": "server-b-tap",
        "observation": "SSH service is listening on the expected port.",
        "category": "network",
        "severity": SecuritySeverity.INFO,
        "evidence": {"port": 22, "protocol": "tcp"},
        "policy_reference": "POL-B20-001",
        "risk": "LOW",
        "provenance": {
            "collector": "mcp",
            "method": "read_only",
        },
    }
    values.update(overrides)
    return SecurityEvidence(**values)


def test_security_evidence_contains_core_fields():
    result = make_evidence()

    assert result.evidence_id == "EVD-B20-001"
    assert result.source == "linux"
    assert result.environment == "server-b-tap"
    assert result.asset == "server-b-tap"
    assert result.category == "network"
    assert result.severity == SecuritySeverity.INFO


def test_security_evidence_preserves_evidence_payload():
    result = make_evidence()

    assert result.evidence["port"] == 22
    assert result.evidence["protocol"] == "tcp"


def test_security_evidence_preserves_provenance():
    result = make_evidence()

    assert result.provenance["collector"] == "mcp"
    assert result.provenance["method"] == "read_only"


def test_security_evidence_supports_policy_reference_and_risk():
    result = make_evidence(
        policy_reference="POL-B20-002",
        risk="MEDIUM",
    )

    assert result.policy_reference == "POL-B20-002"
    assert result.risk == "MEDIUM"


def test_security_evidence_timestamp_defaults_to_utc():
    result = make_evidence()

    assert result.is_utc()
    assert result.timestamp.tzinfo == timezone.utc


def test_security_evidence_accepts_explicit_utc_timestamp():
    timestamp = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc)

    result = make_evidence(timestamp=timestamp)

    assert result.timestamp == timestamp
    assert result.is_utc()
