from datetime import datetime, timezone

from engine.evidence_collector import (
    EvidenceCollector,
    StaticEvidenceCollector,
)
from engine.evidence_model import (
    Evidence,
    EvidenceReliability,
    EvidenceStatus,
    EvidenceType,
)


def build_evidence() -> Evidence:
    return Evidence(
        evidence_id="EV-B18-0001",
        source="static",
        evidence_type=EvidenceType.METRIC,
        collected_at=datetime.now(timezone.utc),
        resource="deployment/api",
        content={"value": 1250},
        reliability=EvidenceReliability.HIGH,
        status=EvidenceStatus.COLLECTED,
    )


def test_static_collector_is_collector():
    collector = StaticEvidenceCollector([build_evidence()])

    assert isinstance(collector, EvidenceCollector)


def test_static_collector_source():
    collector = StaticEvidenceCollector([build_evidence()])

    assert collector.source == "static"


def test_static_collector_returns_evidence():
    evidence = build_evidence()
    collector = StaticEvidenceCollector([evidence])

    result = collector.collect({"resource": "deployment/api"})

    assert len(result) == 1
    assert result[0].evidence_id == "EV-B18-0001"
    assert result[0].source == "static"


def test_static_collector_does_not_modify_original_list():
    evidence = build_evidence()
    original = [evidence]
    collector = StaticEvidenceCollector(original)

    result = collector.collect({})

    assert result is not original
    assert result == original


def test_static_collector_accepts_empty_result():
    collector = StaticEvidenceCollector([])

    result = collector.collect({})

    assert result == []
