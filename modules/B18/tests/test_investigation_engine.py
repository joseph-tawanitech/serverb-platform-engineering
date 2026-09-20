from datetime import datetime, timedelta, timezone

from engine.evidence_model import (
    Evidence,
    EvidenceReliability,
    EvidenceStatus,
    EvidenceType,
)
from engine.incident_model import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
)
from engine.investigation_engine import InvestigationEngine


def make_incident() -> Incident:
    return Incident(
        incident_id="INC-B18-ENGINE-0001",
        title="Server CPU incident",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.INVESTIGATING,
        detected_at=datetime.now(timezone.utc),
        source="test",
        affected_resources=["server-b-tap"],
        symptoms=["CPU usage increased"],
    )


def make_evidence(
    evidence_id: str,
    source: str,
    evidence_type: EvidenceType,
    timestamp: datetime,
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source=source,
        evidence_type=evidence_type,
        collected_at=timestamp,
        observation_time=timestamp,
        resource="server-b-tap",
        content={"value": 95},
        reliability=EvidenceReliability.HIGH,
        status=EvidenceStatus.COLLECTED,
    )


def make_evidence_set() -> list[Evidence]:
    base_time = datetime.now(timezone.utc)

    return [
        make_evidence(
            "E-001",
            "prometheus",
            EvidenceType.METRIC,
            base_time,
        ),
        make_evidence(
            "E-002",
            "kubernetes",
            EvidenceType.KUBERNETES_STATE,
            base_time + timedelta(seconds=30),
        ),
    ]


def test_investigation_engine_produces_complete_result():
    incident = make_incident()
    evidence = make_evidence_set()

    engine = InvestigationEngine()

    result = engine.investigate(
        incident=incident,
        evidence_items=evidence,
    )

    result.validate()

    assert result.incident.incident_id == incident.incident_id
    assert len(result.evidence) == 2
    assert len(result.timeline) == 2
    assert len(result.correlations) >= 1
    assert len(result.hypotheses) >= 1
    assert len(result.sufficiency) == len(result.hypotheses)
    assert len(result.rca) == len(result.hypotheses)


def test_investigation_engine_preserves_evidence_ids():
    incident = make_incident()
    evidence = make_evidence_set()

    engine = InvestigationEngine()

    result = engine.investigate(
        incident=incident,
        evidence_items=evidence,
    )

    result_ids = [item.evidence_id for item in result.evidence]

    assert result_ids == ["E-001", "E-002"]


def test_investigation_engine_creates_matching_hypothesis_and_sufficiency():
    incident = make_incident()
    evidence = make_evidence_set()

    engine = InvestigationEngine()

    result = engine.investigate(
        incident=incident,
        evidence_items=evidence,
    )

    hypothesis_ids = {
        hypothesis.hypothesis_id
        for hypothesis in result.hypotheses
    }

    sufficiency_ids = {
        assessment.hypothesis_id
        for assessment in result.sufficiency
    }

    assert hypothesis_ids == sufficiency_ids


def test_investigation_engine_creates_matching_rca():
    incident = make_incident()
    evidence = make_evidence_set()

    engine = InvestigationEngine()

    result = engine.investigate(
        incident=incident,
        evidence_items=evidence,
    )

    hypothesis_ids = {
        hypothesis.hypothesis_id
        for hypothesis in result.hypotheses
    }

    rca_ids = {
        analysis.hypothesis_id
        for analysis in result.rca
    }

    assert hypothesis_ids == rca_ids


def test_investigation_engine_passes_required_sources():
    incident = make_incident()
    evidence = make_evidence_set()

    engine = InvestigationEngine(
        required_sources=["prometheus", "kubernetes"],
    )

    result = engine.investigate(
        incident=incident,
        evidence_items=evidence,
    )

    assert result.metadata["required_sources"] == [
        "prometheus",
        "kubernetes",
    ]


def test_investigation_engine_accepts_empty_evidence():
    incident = make_incident()

    engine = InvestigationEngine()

    result = engine.investigate(
        incident=incident,
        evidence_items=[],
    )

    result.validate()

    assert result.evidence == []
    assert result.timeline == []
    assert result.correlations == []
    assert result.hypotheses == []
    assert result.sufficiency == []
    assert result.rca == []


def test_investigation_engine_rejects_invalid_incident():
    incident = make_incident()
    incident.incident_id = ""

    engine = InvestigationEngine()

    try:
        engine.investigate(
            incident=incident,
            evidence_items=[],
        )
    except ValueError as exc:
        assert str(exc) == "incident_id must not be empty"
    else:
        raise AssertionError("Expected ValueError")


def test_investigation_engine_rejects_invalid_evidence():
    incident = make_incident()
    evidence = make_evidence_set()
    evidence[0].evidence_id = ""

    engine = InvestigationEngine()

    try:
        engine.investigate(
            incident=incident,
            evidence_items=evidence,
        )
    except ValueError as exc:
        assert str(exc) == "evidence_id must not be empty"
    else:
        raise AssertionError("Expected ValueError")
