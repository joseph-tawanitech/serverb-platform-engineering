from datetime import datetime, timezone

from engine.evidence_model import (
    Evidence,
    EvidenceReliability,
    EvidenceStatus,
    EvidenceType,
)
from engine.evidence_sufficiency_evaluator import (
    EvidenceSufficiencyEvaluator,
)
from engine.evidence_sufficiency_model import SufficiencyStatus
from engine.hypothesis_model import Hypothesis


def make_evidence(
    evidence_id: str,
    source: str,
    reliability: EvidenceReliability,
) -> Evidence:
    timestamp = datetime(
        2026,
        9,
        21,
        10,
        0,
        tzinfo=timezone.utc,
    )

    return Evidence(
        evidence_id=evidence_id,
        source=source,
        evidence_type=EvidenceType.LOG,
        collected_at=timestamp,
        observation_time=timestamp,
        resource="deployment/api",
        content={"description": f"Evidence from {source}"},
        reliability=reliability,
        status=EvidenceStatus.COLLECTED,
    )


def make_hypothesis(
    supporting: list[str],
    contradicting: list[str] | None = None,
) -> Hypothesis:
    return Hypothesis(
        hypothesis_id="HYP-001",
        statement="A common condition may have affected the API.",
        supporting_evidence_ids=supporting,
        contradicting_evidence_ids=contradicting or [],
    )


def test_sufficient_when_two_reliable_supporting_items_exist():
    evidence = [
        make_evidence("E-001", "logs", EvidenceReliability.HIGH),
        make_evidence("E-002", "prometheus", EvidenceReliability.HIGH),
    ]

    hypothesis = make_hypothesis(["E-001", "E-002"])

    result = EvidenceSufficiencyEvaluator.evaluate(
        hypothesis,
        evidence,
        required_sources=["logs", "prometheus"],
    )

    assert result.status == SufficiencyStatus.SUFFICIENT
    assert result.supporting_evidence_count == 2
    assert result.reliable_evidence_count == 2
    assert result.contradicting_evidence_count == 0
    assert result.missing_sources == []
    assert result.confidence == 0.9


def test_insufficient_when_no_supporting_evidence_exists():
    evidence = []

    hypothesis = make_hypothesis([])

    result = EvidenceSufficiencyEvaluator.evaluate(
        hypothesis,
        evidence,
    )

    assert result.status == SufficiencyStatus.INSUFFICIENT
    assert result.supporting_evidence_count == 0
    assert result.confidence == 0.0


def test_insufficient_when_supporting_evidence_is_unreliable():
    evidence = [
        make_evidence("E-001", "logs", EvidenceReliability.UNKNOWN),
        make_evidence("E-002", "prometheus", EvidenceReliability.LOW),
    ]

    hypothesis = make_hypothesis(["E-001", "E-002"])

    result = EvidenceSufficiencyEvaluator.evaluate(
        hypothesis,
        evidence,
    )

    assert result.status == SufficiencyStatus.INSUFFICIENT
    assert result.reliable_evidence_count == 0


def test_partial_when_only_one_reliable_supporting_item_exists():
    evidence = [
        make_evidence("E-001", "logs", EvidenceReliability.HIGH),
    ]

    hypothesis = make_hypothesis(["E-001"])

    result = EvidenceSufficiencyEvaluator.evaluate(
        hypothesis,
        evidence,
    )

    assert result.status == SufficiencyStatus.PARTIAL
    assert result.supporting_evidence_count == 1
    assert result.reliable_evidence_count == 1
    assert result.confidence == 0.5


def test_partial_when_contradicting_evidence_exists():
    evidence = [
        make_evidence("E-001", "logs", EvidenceReliability.HIGH),
        make_evidence("E-002", "prometheus", EvidenceReliability.HIGH),
        make_evidence("E-003", "events", EvidenceReliability.HIGH),
    ]

    hypothesis = make_hypothesis(
        ["E-001", "E-002"],
        ["E-003"],
    )

    result = EvidenceSufficiencyEvaluator.evaluate(
        hypothesis,
        evidence,
    )

    assert result.status == SufficiencyStatus.PARTIAL
    assert result.contradicting_evidence_count == 1


def test_partial_when_required_source_is_missing():
    evidence = [
        make_evidence("E-001", "logs", EvidenceReliability.HIGH),
        make_evidence("E-002", "logs", EvidenceReliability.HIGH),
    ]

    hypothesis = make_hypothesis(["E-001", "E-002"])

    result = EvidenceSufficiencyEvaluator.evaluate(
        hypothesis,
        evidence,
        required_sources=["logs", "prometheus"],
    )

    assert result.status == SufficiencyStatus.PARTIAL
    assert result.missing_sources == ["prometheus"]


def test_missing_referenced_evidence_is_recorded():
    evidence = [
        make_evidence("E-001", "logs", EvidenceReliability.HIGH),
    ]

    hypothesis = make_hypothesis(["E-001", "E-999"])

    result = EvidenceSufficiencyEvaluator.evaluate(
        hypothesis,
        evidence,
    )

    assert result.status == SufficiencyStatus.PARTIAL
    assert result.metadata["missing_evidence_ids"] == ["E-999"]


def test_evidence_ids_are_preserved_for_traceability():
    evidence = [
        make_evidence("E-001", "logs", EvidenceReliability.HIGH),
        make_evidence("E-002", "prometheus", EvidenceReliability.MEDIUM),
    ]

    hypothesis = make_hypothesis(["E-001", "E-002"])

    result = EvidenceSufficiencyEvaluator.evaluate(
        hypothesis,
        evidence,
    )

    assert result.evidence_ids == ["E-001", "E-002"]


def test_required_sources_are_normalized():
    evidence = [
        make_evidence("E-001", "Logs", EvidenceReliability.HIGH),
        make_evidence("E-002", "PROMETHEUS", EvidenceReliability.HIGH),
    ]

    hypothesis = make_hypothesis(["E-001", "E-002"])

    result = EvidenceSufficiencyEvaluator.evaluate(
        hypothesis,
        evidence,
        required_sources=["logs", "prometheus"],
    )

    assert result.status == SufficiencyStatus.SUFFICIENT
    assert result.missing_sources == []
