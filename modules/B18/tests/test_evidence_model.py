from datetime import datetime, timezone

import pytest

from engine.evidence_model import (
    Evidence,
    EvidenceReliability,
    EvidenceStatus,
    EvidenceType,
)


def build_valid_evidence() -> Evidence:
    return Evidence(
        evidence_id="EV-B18-0001",
        source="prometheus",
        evidence_type=EvidenceType.METRIC,
        collected_at=datetime.now(timezone.utc),
        observation_time=datetime.now(timezone.utc),
        resource="deployment/api",
        content={
            "metric": "http_requests_total",
            "value": 1250,
        },
        reliability=EvidenceReliability.HIGH,
        status=EvidenceStatus.COLLECTED,
    )


def test_valid_evidence():
    evidence = build_valid_evidence()

    evidence.validate()

    assert evidence.evidence_id == "EV-B18-0001"
    assert evidence.source == "prometheus"
    assert evidence.evidence_type is EvidenceType.METRIC
    assert evidence.reliability is EvidenceReliability.HIGH
    assert evidence.status is EvidenceStatus.COLLECTED


def test_empty_evidence_id_rejected():
    evidence = build_valid_evidence()
    evidence.evidence_id = "   "

    with pytest.raises(ValueError, match="evidence_id must not be empty"):
        evidence.validate()


def test_empty_source_rejected():
    evidence = build_valid_evidence()
    evidence.source = ""

    with pytest.raises(ValueError, match="source must not be empty"):
        evidence.validate()


def test_invalid_evidence_type_rejected():
    evidence = build_valid_evidence()
    evidence.evidence_type = "metric"

    with pytest.raises(
        ValueError,
        match="evidence_type must be a valid EvidenceType",
    ):
        evidence.validate()


def test_invalid_reliability_rejected():
    evidence = build_valid_evidence()
    evidence.reliability = "high"

    with pytest.raises(
        ValueError,
        match="reliability must be a valid EvidenceReliability",
    ):
        evidence.validate()


def test_invalid_status_rejected():
    evidence = build_valid_evidence()
    evidence.status = "collected"

    with pytest.raises(
        ValueError,
        match="status must be a valid EvidenceStatus",
    ):
        evidence.validate()
