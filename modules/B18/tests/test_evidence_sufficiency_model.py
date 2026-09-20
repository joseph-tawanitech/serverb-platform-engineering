import pytest

from engine.evidence_sufficiency_model import (
    EvidenceSufficiency,
    SufficiencyStatus,
)


def test_valid_sufficiency_assessment():
    assessment = EvidenceSufficiency(
        hypothesis_id="HYP-001",
        status=SufficiencyStatus.SUFFICIENT,
        evidence_ids=["E-001", "E-002"],
        supporting_evidence_count=2,
        contradicting_evidence_count=0,
        reliable_evidence_count=2,
        confidence=0.90,
        reasoning="Multiple reliable evidence items support the hypothesis.",
    )

    assessment.validate()

    assert assessment.hypothesis_id == "HYP-001"
    assert assessment.status == SufficiencyStatus.SUFFICIENT
    assert assessment.reliable_evidence_count == 2
    assert assessment.confidence == 0.90


def test_insufficient_status_is_supported():
    assessment = EvidenceSufficiency(
        hypothesis_id="HYP-002",
        status=SufficiencyStatus.INSUFFICIENT,
    )

    assessment.validate()

    assert assessment.status == SufficiencyStatus.INSUFFICIENT


def test_partial_status_is_supported():
    assessment = EvidenceSufficiency(
        hypothesis_id="HYP-003",
        status=SufficiencyStatus.PARTIAL,
        missing_sources=["logs", "traces"],
    )

    assessment.validate()

    assert assessment.status == SufficiencyStatus.PARTIAL
    assert assessment.missing_sources == ["logs", "traces"]


def test_confidence_must_be_between_zero_and_one():
    assessment = EvidenceSufficiency(
        hypothesis_id="HYP-004",
        status=SufficiencyStatus.PARTIAL,
        confidence=1.2,
    )

    with pytest.raises(ValueError, match="confidence"):
        assessment.validate()


def test_evidence_ids_must_be_unique():
    assessment = EvidenceSufficiency(
        hypothesis_id="HYP-005",
        status=SufficiencyStatus.PARTIAL,
        evidence_ids=["E-001", "E-001"],
    )

    with pytest.raises(ValueError, match="evidence_ids"):
        assessment.validate()


def test_missing_sources_must_be_unique():
    assessment = EvidenceSufficiency(
        hypothesis_id="HYP-006",
        status=SufficiencyStatus.INSUFFICIENT,
        missing_sources=["logs", "logs"],
    )

    with pytest.raises(ValueError, match="missing_sources"):
        assessment.validate()


def test_evidence_counts_cannot_be_negative():
    assessment = EvidenceSufficiency(
        hypothesis_id="HYP-007",
        status=SufficiencyStatus.PARTIAL,
        supporting_evidence_count=-1,
    )

    with pytest.raises(
        ValueError,
        match="supporting_evidence_count",
    ):
        assessment.validate()


def test_reliable_evidence_count_cannot_be_negative():
    assessment = EvidenceSufficiency(
        hypothesis_id="HYP-008",
        status=SufficiencyStatus.PARTIAL,
        reliable_evidence_count=-1,
    )

    with pytest.raises(
        ValueError,
        match="reliable_evidence_count",
    ):
        assessment.validate()


def test_invalid_status_is_rejected():
    assessment = EvidenceSufficiency(
        hypothesis_id="HYP-009",
        status="sufficient",
    )

    with pytest.raises(ValueError, match="SufficiencyStatus"):
        assessment.validate()
