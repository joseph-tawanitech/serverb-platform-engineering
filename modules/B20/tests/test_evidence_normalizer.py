"""Tests for TAP B20.3 security evidence normalization."""

from tap_b20.evidence_normalizer import normalize_security_observation
from tap_b20.models import SecuritySeverity


def test_normalizer_creates_security_evidence():
    result = normalize_security_observation(
        evidence_id="EVD-B20-002",
        source="kubernetes",
        environment="server-b-tap",
        asset="k3s",
        observation="A workload is running with a privileged security context.",
        category="configuration",
        severity=SecuritySeverity.HIGH,
        evidence={"namespace": "default", "privileged": True},
        policy_reference="POL-B20-001",
        risk="HIGH",
        provenance={"collector": "mcp", "method": "read_only"},
    )

    assert result.evidence_id == "EVD-B20-002"
    assert result.source == "kubernetes"
    assert result.environment == "server-b-tap"
    assert result.asset == "k3s"
    assert result.category == "configuration"
    assert result.severity == SecuritySeverity.HIGH
    assert result.evidence["privileged"] is True
    assert result.policy_reference == "POL-B20-001"
    assert result.risk == "HIGH"
    assert result.provenance["collector"] == "mcp"


def test_normalizer_defaults_optional_data_to_empty_values():
    result = normalize_security_observation(
        evidence_id="EVD-B20-003",
        source="linux",
        environment="server-b-tap",
        asset="server-b-tap",
        observation="Security configuration collected.",
        category="configuration",
        severity=SecuritySeverity.INFO,
    )

    assert result.evidence == {}
    assert result.policy_reference is None
    assert result.risk is None
    assert result.provenance == {}


def test_normalizer_preserves_nested_evidence():
    result = normalize_security_observation(
        evidence_id="EVD-B20-004",
        source="network",
        environment="server-b-tap",
        asset="server-b-tap",
        observation="Network service observed.",
        category="network",
        severity=SecuritySeverity.LOW,
        evidence={
            "service": {
                "protocol": "tcp",
                "port": 22,
            }
        },
    )

    assert result.evidence["service"]["protocol"] == "tcp"
    assert result.evidence["service"]["port"] == 22
