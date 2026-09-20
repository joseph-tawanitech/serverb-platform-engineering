from datetime import datetime, timezone, timedelta

import pytest

from engine.evidence_model import (
    Evidence,
    EvidenceReliability,
    EvidenceStatus,
    EvidenceType,
)
from engine.evidence_normalizer import EvidenceNormalizer


def build_evidence() -> Evidence:
    return Evidence(
        evidence_id="EV-B18-0002",
        source="  Prometheus  ",
        evidence_type=EvidenceType.METRIC,
        collected_at=datetime(
            2026,
            9,
            21,
            10,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        ),
        observation_time=datetime(
            2026,
            9,
            21,
            11,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        ),
        resource="  POD/API-7D8F  ",
        content={"metric": "cpu_usage", "value": 94},
        reliability=EvidenceReliability.HIGH,
        status=EvidenceStatus.COLLECTED,
    )


def test_normalize_source():
    evidence = build_evidence()

    normalized = EvidenceNormalizer.normalize(evidence)

    assert normalized.source == "prometheus"


def test_normalize_collected_time_to_utc():
    evidence = build_evidence()

    normalized = EvidenceNormalizer.normalize(evidence)

    assert normalized.collected_at == datetime(
        2026,
        9,
        21,
        8,
        0,
        tzinfo=timezone.utc,
    )


def test_normalize_observation_time_to_utc():
    evidence = build_evidence()

    normalized = EvidenceNormalizer.normalize(evidence)

    assert normalized.observation_time == datetime(
        2026,
        9,
        21,
        9,
        0,
        tzinfo=timezone.utc,
    )


def test_normalize_resource():
    evidence = build_evidence()

    normalized = EvidenceNormalizer.normalize(evidence)

    assert normalized.resource == "pod/API-7D8F"


def test_normalize_resource_without_type():
    evidence = build_evidence()
    evidence.resource = "  SERVER-B  "

    normalized = EvidenceNormalizer.normalize(evidence)

    assert normalized.resource == "server-b"


def test_timezone_naive_timestamp_rejected():
    evidence = build_evidence()
    evidence.collected_at = datetime(2026, 9, 21, 10, 0)

    with pytest.raises(
        ValueError,
        match="timestamp must be timezone-aware",
    ):
        EvidenceNormalizer.normalize(evidence)


def test_normalization_preserves_content():
    evidence = build_evidence()

    normalized = EvidenceNormalizer.normalize(evidence)

    assert normalized.content == {
        "metric": "cpu_usage",
        "value": 94,
    }
