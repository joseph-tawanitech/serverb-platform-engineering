from datetime import datetime, timezone

from engine.evidence_model import (
    Evidence,
    EvidenceReliability,
    EvidenceStatus,
    EvidenceType,
)
from engine.timeline_builder import TimelineBuilder


def build_evidence(
    evidence_id: str,
    collected_at: datetime,
    observation_time: datetime | None = None,
    resource: str | None = "pod/api-7d8f",
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source="Kubernetes",
        evidence_type=EvidenceType.EVENT,
        collected_at=collected_at,
        observation_time=observation_time,
        resource=resource,
        content={"description": "API pod restarted"},
        location="cluster/server-b-tap",
        reliability=EvidenceReliability.HIGH,
        status=EvidenceStatus.COLLECTED,
        metadata={"namespace": "production"},
    )


def test_observation_time_is_preferred():
    collected_at = datetime(2026, 9, 21, 10, 5, 0, tzinfo=timezone.utc)
    observation_time = datetime(2026, 9, 21, 10, 1, 12, tzinfo=timezone.utc)

    evidence = build_evidence(
        "EV-B18-0001",
        collected_at,
        observation_time,
    )

    event = TimelineBuilder.from_evidence(evidence)

    assert event.timestamp == observation_time


def test_collected_time_is_used_when_observation_time_missing():
    collected_at = datetime(2026, 9, 21, 10, 5, 0, tzinfo=timezone.utc)

    evidence = build_evidence(
        "EV-B18-0002",
        collected_at,
    )

    event = TimelineBuilder.from_evidence(evidence)

    assert event.timestamp == collected_at


def test_evidence_identity_is_preserved():
    collected_at = datetime(2026, 9, 21, 10, 5, 0, tzinfo=timezone.utc)

    evidence = build_evidence(
        "EV-B18-0003",
        collected_at,
    )

    event = TimelineBuilder.from_evidence(evidence)

    assert event.event_id == "TL-EV-B18-0003"
    assert event.evidence_id == "EV-B18-0003"


def test_source_type_resource_and_description_are_preserved():
    collected_at = datetime(2026, 9, 21, 10, 5, 0, tzinfo=timezone.utc)

    evidence = build_evidence(
        "EV-B18-0004",
        collected_at,
    )

    event = TimelineBuilder.from_evidence(evidence)

    assert event.source == "Kubernetes"
    assert event.event_type == "event"
    assert event.resource == "pod/api-7d8f"
    assert event.description == "API pod restarted"


def test_evidence_metadata_is_carried_into_timeline():
    collected_at = datetime(2026, 9, 21, 10, 5, 0, tzinfo=timezone.utc)

    evidence = build_evidence(
        "EV-B18-0005",
        collected_at,
    )

    event = TimelineBuilder.from_evidence(evidence)

    assert event.metadata["namespace"] == "production"
    assert event.metadata["evidence_status"] == "collected"
    assert event.metadata["evidence_reliability"] == "high"


def test_multiple_evidence_items_are_sorted_chronologically():
    first = build_evidence(
        "EV-B18-0006",
        datetime(2026, 9, 21, 10, 5, 0, tzinfo=timezone.utc),
    )

    second = build_evidence(
        "EV-B18-0007",
        datetime(2026, 9, 21, 10, 1, 0, tzinfo=timezone.utc),
    )

    third = build_evidence(
        "EV-B18-0008",
        datetime(2026, 9, 21, 10, 3, 0, tzinfo=timezone.utc),
    )

    timeline = TimelineBuilder.build([first, second, third])

    assert [event.evidence_id for event in timeline] == [
        "EV-B18-0007",
        "EV-B18-0008",
        "EV-B18-0006",
    ]


def test_empty_evidence_collection_returns_empty_timeline():
    timeline = TimelineBuilder.build([])

    assert timeline == []
