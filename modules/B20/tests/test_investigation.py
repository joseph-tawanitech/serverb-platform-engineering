from datetime import datetime, timezone

import pytest

from tap_b20.evidence import SecurityEvidence
from tap_b20.investigation import (
    SecurityInvestigation,
    SecurityInvestigationBuilder,
)
from tap_b20.models import SecuritySeverity


def make_evidence(
    evidence_id: str,
    source: str,
    severity: SecuritySeverity,
) -> SecurityEvidence:
    return SecurityEvidence(
        evidence_id=evidence_id,
        source=source,
        environment="test",
        asset="server-01",
        observation="security observation",
        category="security",
        severity=severity,
        evidence={"value": "test"},
        provenance={"test": True},
        timestamp=datetime.now(timezone.utc),
    )


def test_build_investigation():
    evidence = [
        make_evidence(
            "E001",
            "prometheus",
            SecuritySeverity.MEDIUM,
        )
    ]

    result = SecurityInvestigationBuilder().build(
        investigation_id="INV-001",
        environment="test",
        asset="server-01",
        question="Investigate abnormal security condition.",
        evidence=evidence,
        missing_evidence=("firewall_state",),
    )

    assert result.investigation_id == "INV-001"
    assert len(result.evidence) == 1
    assert result.missing_evidence == ("firewall_state",)


def test_summarize_investigation():
    builder = SecurityInvestigationBuilder()

    evidence = [
        make_evidence(
            "E001",
            "prometheus",
            SecuritySeverity.MEDIUM,
        ),
        make_evidence(
            "E002",
            "logs",
            SecuritySeverity.HIGH,
        ),
    ]

    investigation = builder.build(
        investigation_id="INV-002",
        environment="test",
        asset="server-01",
        question="Investigate security condition.",
        evidence=evidence,
    )

    summary = builder.summarize(investigation)

    assert summary.evidence_count == 2
    assert summary.highest_severity == "HIGH"
    assert summary.evidence_sources == (
        "logs",
        "prometheus",
    )


def test_investigation_requires_valid_evidence():
    with pytest.raises(TypeError):
        SecurityInvestigationBuilder().build(
            investigation_id="INV-003",
            environment="test",
            asset="server-01",
            question="Investigate.",
            evidence=["not-evidence"],
        )


def test_investigation_rejects_non_utc_evidence():
    evidence = SecurityEvidence(
        evidence_id="E004",
        source="logs",
        environment="test",
        asset="server-01",
        observation="observation",
        category="security",
        severity=SecuritySeverity.LOW,
        timestamp=datetime(
            2026,
            1,
            1,
        ),
    )

    with pytest.raises(ValueError):
        SecurityInvestigationBuilder().build(
            investigation_id="INV-004",
            environment="test",
            asset="server-01",
            question="Investigate.",
            evidence=[evidence],
        )


def test_investigation_validates_required_fields():
    with pytest.raises(ValueError):
        SecurityInvestigation(
            investigation_id="",
            environment="test",
            asset="server-01",
            question="Investigate.",
        ).validate()
