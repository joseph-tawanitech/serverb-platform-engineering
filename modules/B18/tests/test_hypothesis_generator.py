from datetime import datetime, timedelta, timezone

from engine.correlation_model import CorrelationGroup
from engine.evidence_model import (
    Evidence,
    EvidenceReliability,
    EvidenceStatus,
    EvidenceType,
)
from engine.hypothesis_generator import HypothesisGenerator


def make_evidence(
    evidence_id: str,
    resource: str,
    offset_seconds: int,
) -> Evidence:
    timestamp = datetime(
        2026,
        9,
        21,
        10,
        0,
        tzinfo=timezone.utc,
    ) + timedelta(seconds=offset_seconds)

    return Evidence(
        evidence_id=evidence_id,
        source="kubernetes",
        evidence_type=EvidenceType.KUBERNETES_STATE,
        collected_at=timestamp,
        observation_time=timestamp,
        resource=resource,
        content={
            "description": f"Observed condition for {resource}",
        },
        reliability=EvidenceReliability.HIGH,
        status=EvidenceStatus.COLLECTED,
    )


def test_generate_hypothesis_from_correlation_group():
    evidence = [
        make_evidence("E-001", "deployment/api", 0),
        make_evidence("E-002", "deployment/api", 30),
    ]

    group = CorrelationGroup(
        correlation_id="CORR-B18-0001",
        evidence_ids=["E-001", "E-002"],
    )

    hypotheses = HypothesisGenerator.generate(group, evidence)

    assert len(hypotheses) == 1

    hypothesis = hypotheses[0]

    assert hypothesis.hypothesis_id == "HYP-CORR-B18-0001"
    assert hypothesis.status.value == "proposed"
    assert hypothesis.supporting_evidence_ids == ["E-001", "E-002"]
    assert hypothesis.affected_resources == ["deployment/api"]
    assert hypothesis.confidence is None


def test_generator_preserves_evidence_traceability():
    evidence = [
        make_evidence("E-010", "pod/api-1", 0),
        make_evidence("E-011", "pod/api-1", 20),
    ]

    group = CorrelationGroup(
        correlation_id="CORR-B18-0002",
        evidence_ids=["E-010", "E-011"],
    )

    hypothesis = HypothesisGenerator.generate(group, evidence)[0]

    assert set(hypothesis.supporting_evidence_ids) == {
        "E-010",
        "E-011",
    }


def test_generator_records_affected_resources():
    evidence = [
        make_evidence("E-020", "pod/api-1", 0),
        make_evidence("E-021", "pod/api-2", 10),
    ]

    group = CorrelationGroup(
        correlation_id="CORR-B18-0003",
        evidence_ids=["E-020", "E-021"],
    )

    hypothesis = HypothesisGenerator.generate(group, evidence)[0]

    assert hypothesis.affected_resources == [
        "pod/api-1",
        "pod/api-2",
    ]


def test_generator_returns_empty_when_no_matching_evidence():
    evidence = [
        make_evidence("E-030", "pod/api-1", 0),
    ]

    group = CorrelationGroup(
        correlation_id="CORR-B18-0004",
        evidence_ids=["E-999"],
    )

    hypotheses = HypothesisGenerator.generate(group, evidence)

    assert hypotheses == []


def test_generator_explanation_does_not_claim_root_cause():
    evidence = [
        make_evidence("E-040", "deployment/api", 0),
        make_evidence("E-041", "deployment/api", 15),
    ]

    group = CorrelationGroup(
        correlation_id="CORR-B18-0005",
        evidence_ids=["E-040", "E-041"],
    )

    hypothesis = HypothesisGenerator.generate(group, evidence)[0]

    assert "possible relationship" in hypothesis.reasoning
    assert "not causation" in hypothesis.reasoning
