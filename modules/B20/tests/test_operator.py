"""Tests for B20.5 AI Security Operator contracts."""

from tap_b20.models import SecuritySeverity
from tap_b20.operator import (
    SecurityFinding,
    SecurityInvestigationRequest,
    SecurityOperatorResult,
)


def test_investigation_request_contract() -> None:
    request = SecurityInvestigationRequest(
        request_id="INV-001",
        environment="server-b",
        asset="node/server-b-tap",
        question="Investigate unusual network activity.",
        prompt="Investigate the supplied security evidence and return structured findings.",
        evidence_ids=("OBS-001", "OBS-002"),
        knowledge_context={"source": "B19-RAG", "documents": ["runbook-001"]},
    )

    assert request.request_id == "INV-001"
    assert request.environment == "server-b"
    assert request.asset == "node/server-b-tap"
    assert request.evidence_ids == ("OBS-001", "OBS-002")
    assert request.prompt.startswith("Investigate the supplied")
    assert request.knowledge_context["source"] == "B19-RAG"


def test_security_finding_contract() -> None:
    finding = SecurityFinding(
        finding_id="FIND-001",
        request_id="INV-001",
        severity=SecuritySeverity.MEDIUM,
        title="Unusual network activity",
        explanation="Observed traffic exceeds the expected baseline.",
        evidence_ids=("OBS-001",),
        confidence=0.85,
        recommendation="Review the source of the traffic.",
    )

    assert finding.finding_id == "FIND-001"
    assert finding.severity == SecuritySeverity.MEDIUM
    assert finding.confidence == 0.85
    assert finding.evidence_ids == ("OBS-001",)


def test_operator_result_is_provider_neutral() -> None:
    result = SecurityOperatorResult(
        request_id="INV-001",
        summary="Investigation completed.",
        findings=(),
    )

    assert result.request_id == "INV-001"
    assert result.summary == "Investigation completed."
    assert result.provider is None
    assert result.model is None
