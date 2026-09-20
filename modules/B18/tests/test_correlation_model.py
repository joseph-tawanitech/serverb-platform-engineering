from engine.correlation_model import CorrelationGroup, CorrelationLink


def build_link() -> CorrelationLink:
    return CorrelationLink(
        source_evidence_id="EV-B18-0001",
        related_evidence_id="EV-B18-0002",
        reason="Same Kubernetes resource and overlapping time window",
        confidence=0.9,
        metadata={"resource": "pod/api-7d8f"},
    )


def build_group() -> CorrelationGroup:
    return CorrelationGroup(
        correlation_id="CORR-B18-0001",
        evidence_ids=[
            "EV-B18-0001",
            "EV-B18-0002",
        ],
        links=[build_link()],
    )


def test_valid_correlation_link():
    link = build_link()

    link.validate()

    assert link.source_evidence_id == "EV-B18-0001"
    assert link.related_evidence_id == "EV-B18-0002"
    assert link.confidence == 0.9


def test_link_requires_source_evidence_id():
    link = build_link()
    link.source_evidence_id = ""

    try:
        link.validate()
    except ValueError as exc:
        assert str(exc) == "source_evidence_id must not be empty"
    else:
        raise AssertionError("Expected ValueError")


def test_link_requires_related_evidence_id():
    link = build_link()
    link.related_evidence_id = ""

    try:
        link.validate()
    except ValueError as exc:
        assert str(exc) == "related_evidence_id must not be empty"
    else:
        raise AssertionError("Expected ValueError")


def test_link_requires_reason():
    link = build_link()
    link.reason = ""

    try:
        link.validate()
    except ValueError as exc:
        assert str(exc) == "reason must not be empty"
    else:
        raise AssertionError("Expected ValueError")


def test_link_rejects_invalid_confidence():
    link = build_link()
    link.confidence = 1.1

    try:
        link.validate()
    except ValueError as exc:
        assert str(exc) == "confidence must be between 0.0 and 1.0"
    else:
        raise AssertionError("Expected ValueError")


def test_link_rejects_self_correlation():
    link = build_link()
    link.related_evidence_id = link.source_evidence_id

    try:
        link.validate()
    except ValueError as exc:
        assert str(exc) == "evidence items cannot correlate with themselves"
    else:
        raise AssertionError("Expected ValueError")


def test_valid_correlation_group():
    group = build_group()

    group.validate()

    assert group.correlation_id == "CORR-B18-0001"
    assert len(group.evidence_ids) == 2
    assert len(group.links) == 1


def test_group_requires_correlation_id():
    group = build_group()
    group.correlation_id = ""

    try:
        group.validate()
    except ValueError as exc:
        assert str(exc) == "correlation_id must not be empty"
    else:
        raise AssertionError("Expected ValueError")


def test_group_requires_evidence():
    group = build_group()
    group.evidence_ids = []

    try:
        group.validate()
    except ValueError as exc:
        assert str(exc) == "evidence_ids must not be empty"
    else:
        raise AssertionError("Expected ValueError")


def test_group_rejects_duplicate_evidence():
    group = build_group()
    group.evidence_ids.append("EV-B18-0001")

    try:
        group.validate()
    except ValueError as exc:
        assert str(exc) == "evidence_ids must be unique"
    else:
        raise AssertionError("Expected ValueError")
