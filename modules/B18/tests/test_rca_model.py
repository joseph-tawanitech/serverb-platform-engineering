import pytest

from engine.rca_model import RCAStatus, RootCauseAnalysis


def test_valid_provisional_rca():
    rca = RootCauseAnalysis(
        incident_id="INC-001",
        status=RCAStatus.PROVISIONAL,
        root_cause="Database connectivity failure caused application errors.",
        hypothesis_id="HYP-001",
        supporting_evidence_ids=["E-001", "E-002"],
        affected_resources=["deployment/api"],
        root_cause_location="pod/api-1",
        contributing_factors=["Network dependency instability"],
        confidence=0.8,
        reasoning="Reliable evidence supports the database connectivity explanation.",
        limitations=["Trace data was unavailable."],
    )

    rca.validate()

    assert rca.incident_id == "INC-001"
    assert rca.status == RCAStatus.PROVISIONAL
    assert rca.root_cause == (
        "Database connectivity failure caused application errors."
    )
    assert rca.confidence == 0.8


def test_valid_confirmed_rca():
    rca = RootCauseAnalysis(
        incident_id="INC-002",
        status=RCAStatus.CONFIRMED,
        root_cause="Configuration error caused the service failure.",
        confidence=0.95,
    )

    rca.validate()

    assert rca.status == RCAStatus.CONFIRMED
    assert rca.root_cause is not None


def test_not_established_rca_has_no_root_cause():
    rca = RootCauseAnalysis(
        incident_id="INC-003",
        status=RCAStatus.NOT_ESTABLISHED,
    )

    rca.validate()

    assert rca.root_cause is None
    assert rca.confidence is None


def test_provisional_rca_requires_root_cause():
    rca = RootCauseAnalysis(
        incident_id="INC-004",
        status=RCAStatus.PROVISIONAL,
    )

    with pytest.raises(ValueError, match="root_cause is required"):
        rca.validate()


def test_confirmed_rca_requires_root_cause():
    rca = RootCauseAnalysis(
        incident_id="INC-005",
        status=RCAStatus.CONFIRMED,
    )

    with pytest.raises(ValueError, match="root_cause is required"):
        rca.validate()


def test_not_established_rca_cannot_contain_root_cause():
    rca = RootCauseAnalysis(
        incident_id="INC-006",
        status=RCAStatus.NOT_ESTABLISHED,
        root_cause="This should not be present.",
    )

    with pytest.raises(ValueError, match="root_cause must be empty"):
        rca.validate()


def test_supporting_and_contradicting_evidence_cannot_overlap():
    rca = RootCauseAnalysis(
        incident_id="INC-007",
        status=RCAStatus.PROVISIONAL,
        root_cause="Test root cause.",
        supporting_evidence_ids=["E-001"],
        contradicting_evidence_ids=["E-001"],
    )

    with pytest.raises(
        ValueError,
        match="simultaneously support and contradict",
    ):
        rca.validate()


def test_confidence_must_be_between_zero_and_one():
    rca = RootCauseAnalysis(
        incident_id="INC-008",
        status=RCAStatus.PROVISIONAL,
        root_cause="Test root cause.",
        confidence=1.1,
    )

    with pytest.raises(ValueError, match="confidence"):
        rca.validate()


def test_affected_resources_must_be_unique():
    rca = RootCauseAnalysis(
        incident_id="INC-009",
        status=RCAStatus.PROVISIONAL,
        root_cause="Test root cause.",
        affected_resources=["pod/api-1", "pod/api-1"],
    )

    with pytest.raises(ValueError, match="affected_resources"):
        rca.validate()


def test_contributing_factors_must_be_unique():
    rca = RootCauseAnalysis(
        incident_id="INC-010",
        status=RCAStatus.PROVISIONAL,
        root_cause="Test root cause.",
        contributing_factors=["network", "network"],
    )

    with pytest.raises(ValueError, match="contributing_factors"):
        rca.validate()


def test_limitations_must_be_unique():
    rca = RootCauseAnalysis(
        incident_id="INC-011",
        status=RCAStatus.PROVISIONAL,
        root_cause="Test root cause.",
        limitations=["missing logs", "missing logs"],
    )

    with pytest.raises(ValueError, match="limitations"):
        rca.validate()


def test_root_cause_location_cannot_be_empty():
    rca = RootCauseAnalysis(
        incident_id="INC-012",
        status=RCAStatus.PROVISIONAL,
        root_cause="Test root cause.",
        root_cause_location="   ",
    )

    with pytest.raises(ValueError, match="root_cause_location"):
        rca.validate()


def test_hypothesis_id_cannot_be_empty():
    rca = RootCauseAnalysis(
        incident_id="INC-013",
        status=RCAStatus.PROVISIONAL,
        root_cause="Test root cause.",
        hypothesis_id="   ",
    )

    with pytest.raises(ValueError, match="hypothesis_id"):
        rca.validate()


def test_invalid_status_is_rejected():
    rca = RootCauseAnalysis(
        incident_id="INC-014",
        status="confirmed",
        root_cause="Test root cause.",
    )

    with pytest.raises(ValueError, match="RCAStatus"):
        rca.validate()
