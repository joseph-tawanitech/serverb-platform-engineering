from datetime import datetime, timezone

from engine.correlation_engine import CorrelationEngine
from engine.evidence_model import (
    Evidence,
    EvidenceReliability,
    EvidenceStatus,
    EvidenceType,
)


def build_evidence(
    evidence_id: str,
    timestamp: datetime,
    resource: str | None = "pod/api-7d8f",
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source="kubernetes",
        evidence_type=EvidenceType.EVENT,
        collected_at=timestamp,
        observation_time=timestamp,
        resource=resource,
        content={"description": f"Event for {evidence_id}"},
        location="cluster/server-b-tap",
        reliability=EvidenceReliability.HIGH,
        status=EvidenceStatus.COLLECTED,
    )


def test_same_resource_and_time_window_are_correlated():
    first = build_evidence(
        "EV-B18-0001",
        datetime(2026, 9, 21, 10, 1, 0, tzinfo=timezone.utc),
    )

    second = build_evidence(
        "EV-B18-0002",
        datetime(2026, 9, 21, 10, 2, 0, tzinfo=timezone.utc),
    )

    groups = CorrelationEngine(time_window_seconds=300).correlate(
        [first, second]
    )

    assert len(groups) == 1
    assert groups[0].evidence_ids == [
        "EV-B18-0001",
        "EV-B18-0002",
    ]
    assert len(groups[0].links) == 1
    assert groups[0].links[0].confidence == 0.95


def test_same_resource_outside_time_window_still_correlates():
    first = build_evidence(
        "EV-B18-0003",
        datetime(2026, 9, 21, 10, 0, 0, tzinfo=timezone.utc),
    )

    second = build_evidence(
        "EV-B18-0004",
        datetime(2026, 9, 21, 11, 0, 0, tzinfo=timezone.utc),
    )

    groups = CorrelationEngine(time_window_seconds=300).correlate(
        [first, second]
    )

    assert len(groups) == 1
    assert groups[0].links[0].reason == "Same resource"
    assert groups[0].links[0].confidence == 0.80


def test_different_resources_are_not_correlated():
    first = build_evidence(
        "EV-B18-0005",
        datetime(2026, 9, 21, 10, 1, 0, tzinfo=timezone.utc),
        resource="pod/api-7d8f",
    )

    second = build_evidence(
        "EV-B18-0006",
        datetime(2026, 9, 21, 10, 2, 0, tzinfo=timezone.utc),
        resource="pod/database-1234",
    )

    groups = CorrelationEngine().correlate([first, second])

    assert groups == []


def test_missing_resource_does_not_create_resource_correlation():
    first = build_evidence(
        "EV-B18-0007",
        datetime(2026, 9, 21, 10, 1, 0, tzinfo=timezone.utc),
        resource=None,
    )

    second = build_evidence(
        "EV-B18-0008",
        datetime(2026, 9, 21, 10, 2, 0, tzinfo=timezone.utc),
        resource="pod/api-7d8f",
    )

    groups = CorrelationEngine().correlate([first, second])

    assert groups == []


def test_multiple_related_items_form_one_group():
    first = build_evidence(
        "EV-B18-0009",
        datetime(2026, 9, 21, 10, 1, 0, tzinfo=timezone.utc),
    )

    second = build_evidence(
        "EV-B18-0010",
        datetime(2026, 9, 21, 10, 2, 0, tzinfo=timezone.utc),
    )

    third = build_evidence(
        "EV-B18-0011",
        datetime(2026, 9, 21, 10, 3, 0, tzinfo=timezone.utc),
    )

    groups = CorrelationEngine().correlate(
        [first, second, third]
    )

    assert len(groups) == 1
    assert groups[0].evidence_ids == [
        "EV-B18-0009",
        "EV-B18-0010",
        "EV-B18-0011",
    ]
    assert len(groups[0].links) == 3


def test_unrelated_evidence_forms_separate_groups():
    first = build_evidence(
        "EV-B18-0012",
        datetime(2026, 9, 21, 10, 1, 0, tzinfo=timezone.utc),
        resource="pod/api-7d8f",
    )

    second = build_evidence(
        "EV-B18-0013",
        datetime(2026, 9, 21, 10, 2, 0, tzinfo=timezone.utc),
        resource="pod/database-1234",
    )

    third = build_evidence(
        "EV-B18-0014",
        datetime(2026, 9, 21, 10, 3, 0, tzinfo=timezone.utc),
        resource="pod/cache-5678",
    )

    groups = CorrelationEngine().correlate(
        [first, second, third]
    )

    assert groups == []


def test_negative_time_window_is_rejected():
    try:
        CorrelationEngine(time_window_seconds=-1)
    except ValueError as exc:
        assert str(exc) == "time_window_seconds must not be negative"
    else:
        raise AssertionError("Expected ValueError")


def test_empty_evidence_returns_no_groups():
    groups = CorrelationEngine().correlate([])

    assert groups == []
