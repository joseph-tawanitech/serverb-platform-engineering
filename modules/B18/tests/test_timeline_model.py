from datetime import datetime, timezone

import pytest

from engine.timeline_model import TimelineEvent


def build_event() -> TimelineEvent:
    return TimelineEvent(
        event_id="TL-B18-0001",
        timestamp=datetime(
            2026, 9, 21, 10, 1, 12,
            tzinfo=timezone.utc,
        ),
        evidence_id="EV-B18-0001",
        source="kubernetes",
        event_type="pod_restart",
        description="API pod restarted",
        resource="pod/api-7d8f",
        metadata={"namespace": "production"},
    )


def test_valid_timeline_event():
    event = build_event()

    event.validate()

    assert event.event_id == "TL-B18-0001"
    assert event.timestamp.year == 2026
    assert event.timestamp.month == 9
    assert event.timestamp.day == 21
    assert event.timestamp.hour == 10
    assert event.timestamp.minute == 1
    assert event.timestamp.second == 12


def test_event_requires_event_id():
    event = build_event()
    event.event_id = ""

    with pytest.raises(ValueError, match="event_id must not be empty"):
        event.validate()


def test_event_requires_evidence_id():
    event = build_event()
    event.evidence_id = ""

    with pytest.raises(ValueError, match="evidence_id must not be empty"):
        event.validate()


def test_event_requires_source():
    event = build_event()
    event.source = ""

    with pytest.raises(ValueError, match="source must not be empty"):
        event.validate()


def test_event_requires_event_type():
    event = build_event()
    event.event_type = ""

    with pytest.raises(ValueError, match="event_type must not be empty"):
        event.validate()


def test_event_requires_description():
    event = build_event()
    event.description = ""

    with pytest.raises(ValueError, match="description must not be empty"):
        event.validate()


def test_naive_timestamp_rejected():
    event = build_event()
    event.timestamp = datetime(2026, 9, 21, 10, 1, 12)

    with pytest.raises(ValueError, match="timestamp must be timezone-aware"):
        event.validate()
