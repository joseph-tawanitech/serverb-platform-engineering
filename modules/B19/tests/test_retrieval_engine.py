from __future__ import annotations

from datetime import datetime, timezone

import pytest

from modules.B19.engine.knowledge_model import (
    KnowledgeDocument,
    KnowledgeSourceType,
    KnowledgeType,
)
from modules.B19.engine.knowledge_provenance import (
    KnowledgeProvenance,
    calculate_content_checksum,
)
from modules.B19.indexing.evidence_index import EvidenceIndex
from modules.B19.ingestion.knowledge_ingestor import KnowledgeIngestor
from modules.B19.retrieval.retrieval_engine import (
    RetrievalEngine,
    RetrievalQuery,
)


def make_index() -> EvidenceIndex:
    index = EvidenceIndex()
    ingestor = KnowledgeIngestor()

    documents = [
        (
            "DOC-001",
            "Kubernetes Memory Incident",
            KnowledgeType.INCIDENT,
            KnowledgeSourceType.INCIDENT_RECORD,
            "server-b-tap",
            ("kubernetes", "memory"),
        ),
        (
            "DOC-002",
            "Kubernetes Memory RCA",
            KnowledgeType.RCA,
            KnowledgeSourceType.INCIDENT_RECORD,
            "server-b-tap",
            ("kubernetes", "memory"),
        ),
        (
            "DOC-003",
            "Ansible Kubernetes Recovery Procedure",
            KnowledgeType.PROCEDURE,
            KnowledgeSourceType.ANSIBLE
            if hasattr(KnowledgeSourceType, "ANSIBLE")
            else KnowledgeSourceType.FILE,
            "server-b-tap",
            ("kubernetes", "recovery"),
        ),
        (
            "DOC-004",
            "Network Troubleshooting Procedure",
            KnowledgeType.PROCEDURE,
            KnowledgeSourceType.FILE,
            "network-service",
            ("network", "troubleshooting"),
        ),
    ]

    now = datetime.now(timezone.utc)

    for (
        document_id,
        title,
        knowledge_type,
        source_type,
        resource,
        tags,
    ) in documents:
        content = f"{title} operational knowledge."

        document = KnowledgeDocument(
            document_id=document_id,
            title=title,
            knowledge_type=knowledge_type,
            source_type=source_type,
            content=content,
            source="test-fixture",
            created_at=now,
            resource=resource,
            tags=list(tags),
        )

        checksum = calculate_content_checksum(content)

        provenance = KnowledgeProvenance(
            source="test-fixture",
            source_type="test",
            collected_at=now,
            collector="pytest",
            version="1",
            checksum=checksum,
            reference=document_id,
        )

        ingested = ingestor.ingest(
            document,
            provenance,
            verify_integrity=True,
        )

        index.index(ingested)

    return index


def test_resource_filter() -> None:
    engine = RetrievalEngine(make_index())

    query = RetrievalQuery(
        query_id="Q-001",
        text="Kubernetes memory",
        resource="server-b-tap",
    )

    results = engine.retrieve(query)

    assert results
    assert all(
        result.resource == "server-b-tap"
        for result in results
    )


def test_knowledge_type_filter() -> None:
    engine = RetrievalEngine(make_index())

    query = RetrievalQuery(
        query_id="Q-002",
        text="Kubernetes memory",
        knowledge_types=("rca",),
    )

    results = engine.retrieve(query)

    assert len(results) == 1
    assert results[0].document_id == "DOC-002"
    assert results[0].knowledge_type == "rca"


def test_source_type_filter() -> None:
    engine = RetrievalEngine(make_index())

    query = RetrievalQuery(
        query_id="Q-003",
        text="Network troubleshooting",
        source_types=("file",),
    )

    results = engine.retrieve(query)

    assert results
    assert all(
        result.source_type == "file"
        for result in results
    )


def test_tag_filter() -> None:
    engine = RetrievalEngine(make_index())

    query = RetrievalQuery(
        query_id="Q-004",
        text="Kubernetes memory",
        tags=("memory",),
    )

    results = engine.retrieve(query)

    assert len(results) == 2
    assert all("memory" in result.tags for result in results)


def test_resource_match_contributes_to_score() -> None:
    engine = RetrievalEngine(make_index())

    query = RetrievalQuery(
        query_id="Q-005",
        text="Kubernetes memory",
        resource="server-b-tap",
    )

    results = engine.retrieve(query)

    assert results
    assert results[0].score_breakdown["resource_match"] == 30


def test_title_match_contributes_to_score() -> None:
    engine = RetrievalEngine(make_index())

    query = RetrievalQuery(
        query_id="Q-006",
        text="Kubernetes",
    )

    results = engine.retrieve(query)

    assert results
    assert all(
        "title_match" in result.score_breakdown
        for result in results
    )


def test_results_are_deterministically_ordered() -> None:
    engine = RetrievalEngine(make_index())

    query = RetrievalQuery(
        query_id="Q-007",
        text="Kubernetes memory",
        resource="server-b-tap",
    )

    first = engine.retrieve(query)
    second = engine.retrieve(query)

    assert [
        result.document_id for result in first
    ] == [
        result.document_id for result in second
    ]

    assert [
        result.score for result in first
    ] == [
        result.score for result in second
    ]


def test_limit_is_respected() -> None:
    engine = RetrievalEngine(make_index())

    query = RetrievalQuery(
        query_id="Q-008",
        text="Kubernetes",
        limit=1,
    )

    results = engine.retrieve(query)

    assert len(results) == 1


def test_provenance_is_preserved() -> None:
    engine = RetrievalEngine(make_index())

    query = RetrievalQuery(
        query_id="Q-009",
        text="Kubernetes memory",
    )

    results = engine.retrieve(query)

    assert results

    result = results[0]

    assert result.provenance_reference is not None
    assert result.provenance_version == "1"
    assert result.provenance_checksum is not None
    assert result.provenance_collector == "pytest"


def test_no_matching_query_returns_empty_results() -> None:
    engine = RetrievalEngine(make_index())

    query = RetrievalQuery(
        query_id="Q-010",
        text="Database replication failure",
    )

    results = engine.retrieve(query)

    assert results == []


def test_invalid_engine_dependency_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="evidence_index must be an EvidenceIndex",
    ):
        RetrievalEngine(object())


def test_invalid_query_type_rejected() -> None:
    engine = RetrievalEngine(make_index())

    with pytest.raises(
        TypeError,
        match="query must be a RetrievalQuery",
    ):
        engine.retrieve(object())  # type: ignore[arg-type]


def test_incident_id_filter() -> None:
    index = make_index()
    ingestor = KnowledgeIngestor()

    now = datetime.now(timezone.utc)

    document = KnowledgeDocument(
        document_id="DOC-INCIDENT-001",
        title="Kubernetes Memory Incident INC-001",
        knowledge_type=KnowledgeType.INCIDENT,
        source_type=KnowledgeSourceType.INCIDENT_RECORD,
        content="Incident-specific Kubernetes memory evidence.",
        source="incident-record",
        created_at=now,
        resource="server-b-tap",
        incident_id="INC-001",
        tags=["kubernetes", "memory"],
    )

    provenance = KnowledgeProvenance(
        source="incident-record",
        source_type="incident_record",
        collected_at=now,
        collector="pytest",
        version="1",
        checksum=calculate_content_checksum(document.content),
        reference="INC-001",
    )

    ingested = ingestor.ingest(
        document,
        provenance,
        verify_integrity=True,
    )

    index.index(ingested)

    engine = RetrievalEngine(index)

    query = RetrievalQuery(
        query_id="Q-INC-001",
        text="Kubernetes memory incident",
        incident_id="INC-001",
    )

    results = engine.retrieve(query)

    assert len(results) == 1
    assert results[0].document_id == "DOC-INCIDENT-001"
    assert results[0].provenance_reference == "INC-001"


def test_unknown_incident_returns_empty_results() -> None:
    engine = RetrievalEngine(make_index())

    query = RetrievalQuery(
        query_id="Q-INC-UNKNOWN",
        text="Kubernetes memory",
        incident_id="INC-DOES-NOT-EXIST",
    )

    results = engine.retrieve(query)

    assert results == []
