"""Tests for the B20.5 AI Security Operator service."""

from tap_b20.models import SecuritySeverity
from tap_b20.operator import SecurityInvestigationRequest
from tap_b20.operator_service import investigate


def test_investigation_returns_structured_result() -> None:
    request = SecurityInvestigationRequest(
        request_id="INV-002",
        environment="server-b",
        asset="node/server-b-tap",
        question="Investigate unusual network activity.",
        evidence_ids=("OBS-001",),
    )

    result = investigate(request)

    assert result.request_id == "INV-002"
    assert result.summary == "Security investigation request accepted."
    assert len(result.findings) == 1

    finding = result.findings[0]
    assert finding.finding_id == "INV-002-F001"
    assert finding.severity == SecuritySeverity.INFO
    assert finding.evidence_ids == ("OBS-001",)
    assert finding.confidence == 1.0


def test_operator_service_does_not_select_an_ai_provider() -> None:
    request = SecurityInvestigationRequest(
        request_id="INV-003",
        environment="server-b",
        asset="node/server-b-tap",
        question="Investigate authentication activity.",
    )

    result = investigate(request)

    assert result.provider is None
    assert result.model is None
