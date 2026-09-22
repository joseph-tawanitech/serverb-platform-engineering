"""Tests for B20.4 monitoring-to-evidence integration."""

from tap_b20.evidence import SecurityEvidence
from tap_b20.models import SecuritySeverity
from tap_b20.monitoring import SecurityObservation
from tap_b20.monitoring_adapter import observation_to_evidence


def test_observation_to_evidence() -> None:
    observation = SecurityObservation(
        observation_id="OBS-001",
        source="prometheus",
        environment="server-b",
        asset="node/server-b-tap",
        observation="Unusual network traffic detected.",
        category="network",
        severity=SecuritySeverity.MEDIUM,
        data={"traffic_rate": 1250},
    )

    result = observation_to_evidence(
        observation,
        policy_reference="B20-POLICY-001",
        risk="MEDIUM",
    )

    assert isinstance(result, SecurityEvidence)
    assert result.evidence_id == "OBS-001"
    assert result.source == "prometheus"
    assert result.asset == "node/server-b-tap"
    assert result.category == "network"
    assert result.severity == SecuritySeverity.MEDIUM
    assert result.evidence["traffic_rate"] == 1250
    assert result.policy_reference == "B20-POLICY-001"
    assert result.risk == "MEDIUM"


def test_monitoring_provenance_is_preserved() -> None:
    observation = SecurityObservation(
        observation_id="OBS-002",
        source="kubernetes",
        environment="server-b",
        asset="pod/security-api",
        observation="Unexpected pod restart detected.",
        category="workload",
        severity=SecuritySeverity.HIGH,
    )

    result = observation_to_evidence(observation)

    assert result.provenance["monitoring_source"] == "kubernetes"
    assert result.provenance["observation_id"] == "OBS-002"
