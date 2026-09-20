from datetime import datetime, timezone

import pytest

from engine.correlation_model import CorrelationGroup
from engine.evidence_model import Evidence, EvidenceReliability, EvidenceStatus, EvidenceType
from engine.evidence_sufficiency_model import EvidenceSufficiency, SufficiencyStatus
from engine.hypothesis_model import Hypothesis
from engine.incident_model import Incident, IncidentSeverity, IncidentStatus
from engine.investigation_model import InvestigationResult
from engine.rca_model import RCAStatus, RootCauseAnalysis
from engine.timeline_model import TimelineEvent


def make_incident() -> Incident:
    return Incident(
        incident_id="INC-B18-0001",
        title="Test incident",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.INVESTIGATING,
        detected_at=datetime.now(timezone.utc),
        source="test",
    )


def make_evidence(evidence_id: str) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source="prometheus",
        evidence_type=EvidenceType.METRIC,
        collected_at=datetime.now(timezone.utc),
        resource="server-b-tap",
        reliability=EvidenceReliability.HIGH,
        status=EvidenceStatus.COLLECTED,
    )


def make_hypothesis(hypothesis_id: str) -> Hypothesis:
    return Hypothesis(
        hypothesis_id=hypothesis_id,
        statement="A common condition affected the resource.",
        supporting_evidence_ids=["E-001"],
        affected_resources=["server-b-tap"],
    )


def make_sufficiency(hypothesis_id: str) -> EvidenceSufficiency:
    return EvidenceSufficiency(
        hypothesis_id=hypothesis_id,
        status=SufficiencyStatus.PARTIAL,
        evidence_ids=["E-001"],
        supporting_evidence_count=1,
        contradicting_evidence_count=0,
        reliable_evidence_count=1,
        confidence=0.5,
        reasoning="Evidence is partially sufficient.",
    )


def make_rca(hypothesis_id: str) -> RootCauseAnalysis:
    return RootCauseAnalysis(
        incident_id="INC-B18-0001",
        status=RCAStatus.PROVISIONAL,
        root_cause="A common condition affected the resource.",
        hypothesis_id=hypothesis_id,
        supporting_evidence_ids=["E-001"],
        affected_resources=["server-b-tap"],
        confidence=0.5,
        reasoning="The evidence supports the hypothesis, but evidence gaps remain.",
    )


def test_valid_investigation_result():
    incident = make_incident()
    evidence = [make_evidence("E-001")]

    result = InvestigationResult(
        incident=incident,
        evidence=evidence,
        hypotheses=[make_hypothesis("HYP-001")],
        sufficiency=[make_sufficiency("HYP-001")],
        rca=[make_rca("HYP-001")],
    )

    result.validate()


def test_evidence_ids_must_be_unique():
    evidence = make_evidence("E-001")

    result = InvestigationResult(
        incident=make_incident(),
        evidence=[evidence, evidence],
    )

    with pytest.raises(ValueError, match="evidence IDs must be unique"):
        result.validate()


def test_hypothesis_ids_must_be_unique():
    hypothesis = make_hypothesis("HYP-001")

    result = InvestigationResult(
        incident=make_incident(),
        hypotheses=[hypothesis, hypothesis],
    )

    with pytest.raises(ValueError, match="hypothesis IDs must be unique"):
        result.validate()


def test_sufficiency_hypothesis_ids_must_be_unique():
    assessment = make_sufficiency("HYP-001")

    result = InvestigationResult(
        incident=make_incident(),
        sufficiency=[assessment, assessment],
    )

    with pytest.raises(
        ValueError,
        match="sufficiency hypothesis IDs must be unique",
    ):
        result.validate()


def test_rca_hypothesis_ids_must_be_unique():
    rca = make_rca("HYP-001")

    result = InvestigationResult(
        incident=make_incident(),
        rca=[rca, rca],
    )

    with pytest.raises(
        ValueError,
        match="RCA hypothesis IDs must be unique",
    ):
        result.validate()


def test_rca_incident_id_must_match():
    rca = make_rca("HYP-001")
    rca.incident_id = "INC-DIFFERENT"

    result = InvestigationResult(
        incident=make_incident(),
        rca=[rca],
    )

    with pytest.raises(
        ValueError,
        match="RCA incident_id must match investigation incident_id",
    ):
        result.validate()


def test_nested_artifacts_are_validated():
    incident = make_incident()
    evidence = make_evidence("E-001")

    timeline = TimelineEvent(
        event_id="EVT-001",
        timestamp=datetime.now(timezone.utc),
        evidence_id="E-001",
        source="prometheus",
        event_type="metric",
        description="CPU increased",
        resource="server-b-tap",
    )

    correlation = CorrelationGroup(
        correlation_id="CORR-B18-0001",
        evidence_ids=["E-001"],
    )

    result = InvestigationResult(
        incident=incident,
        evidence=[evidence],
        timeline=[timeline],
        correlations=[correlation],
    )

    result.validate()


def test_empty_investigation_artifacts_are_allowed():
    result = InvestigationResult(
        incident=make_incident(),
    )

    result.validate()
