import pytest

from engine.hypothesis_model import Hypothesis, HypothesisStatus


def test_valid_hypothesis():
    hypothesis = Hypothesis(
        hypothesis_id="HYP-001",
        statement="Database connection failure caused application errors.",
        supporting_evidence_ids=["E-001", "E-002"],
        affected_resources=["deployment/api"],
        confidence=0.75,
        reasoning="Application logs and connection metrics support the hypothesis.",
    )

    hypothesis.validate()

    assert hypothesis.hypothesis_id == "HYP-001"
    assert hypothesis.status == HypothesisStatus.PROPOSED
    assert hypothesis.confidence == 0.75


def test_default_status_is_proposed():
    hypothesis = Hypothesis(
        hypothesis_id="HYP-002",
        statement="The workload experienced resource pressure.",
    )

    hypothesis.validate()

    assert hypothesis.status == HypothesisStatus.PROPOSED
    assert hypothesis.confidence is None


def test_confidence_must_be_between_zero_and_one():
    hypothesis = Hypothesis(
        hypothesis_id="HYP-003",
        statement="Invalid confidence.",
        confidence=1.5,
    )

    with pytest.raises(ValueError, match="confidence"):
        hypothesis.validate()


def test_supporting_evidence_must_be_unique():
    hypothesis = Hypothesis(
        hypothesis_id="HYP-004",
        statement="Duplicate evidence test.",
        supporting_evidence_ids=["E-001", "E-001"],
    )

    with pytest.raises(ValueError, match="supporting_evidence_ids"):
        hypothesis.validate()


def test_contradicting_evidence_must_be_unique():
    hypothesis = Hypothesis(
        hypothesis_id="HYP-005",
        statement="Duplicate contradiction test.",
        contradicting_evidence_ids=["E-002", "E-002"],
    )

    with pytest.raises(ValueError, match="contradicting_evidence_ids"):
        hypothesis.validate()


def test_evidence_cannot_support_and_contradict_same_hypothesis():
    hypothesis = Hypothesis(
        hypothesis_id="HYP-006",
        statement="Conflicting evidence test.",
        supporting_evidence_ids=["E-001"],
        contradicting_evidence_ids=["E-001"],
    )

    with pytest.raises(ValueError, match="simultaneously support and contradict"):
        hypothesis.validate()


def test_invalid_status_is_rejected():
    hypothesis = Hypothesis(
        hypothesis_id="HYP-007",
        statement="Invalid status test.",
        status="supported",
    )

    with pytest.raises(ValueError, match="HypothesisStatus"):
        hypothesis.validate()


def test_affected_resources_must_be_unique():
    hypothesis = Hypothesis(
        hypothesis_id="HYP-008",
        statement="Duplicate resource test.",
        affected_resources=["pod/api-1", "pod/api-1"],
    )

    with pytest.raises(ValueError, match="affected_resources"):
        hypothesis.validate()
