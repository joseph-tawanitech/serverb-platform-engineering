from datetime import datetime, timezone

import pytest

from ..context.context_assembler import (
    ContextAssembler,
    RAGContext,
    RAGContextItem,
)
from ..retrieval.retrieval_engine import (
    RetrievalQuery,
    RetrievalResult,
)


def make_query(limit: int = 3) -> RetrievalQuery:
    return RetrievalQuery(
        query_id="Q-B19.9-001",
        text="Kubernetes memory incident",
        resource="server-b-tap",
        limit=limit,
    )


def make_result(
    document_id: str,
    title: str,
    score: int,
) -> RetrievalResult:
    collected_at = datetime(
        2026,
        9,
        22,
        12,
        0,
        tzinfo=timezone.utc,
    )

    return RetrievalResult(
        document_id=document_id,
        title=title,
        score=score,
        score_breakdown={"title_match": score},
        knowledge_type="incident",
        source_type="incident_record",
        resource="server-b-tap",
        tags=("kubernetes", "memory"),
        source="incident-record",
        provenance_reference="INC-001",
        provenance_version="1",
        provenance_checksum="sha256:test",
        provenance_collected_at=collected_at,
        provenance_collector="pytest",
    )


def test_context_assembly_preserves_query_and_results() -> None:
    query = make_query()

    results = [
        make_result(
            "DOC-001",
            "Kubernetes Memory Incident",
            80,
        ),
        make_result(
            "DOC-002",
            "Kubernetes Memory Runbook",
            60,
        ),
    ]

    context = ContextAssembler().assemble(
        context_id="CTX-001",
        query=query,
        results=results,
        created_at=datetime(
            2026,
            9,
            22,
            13,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert isinstance(context, RAGContext)
    assert context.context_id == "CTX-001"
    assert context.query_id == "Q-B19.9-001"
    assert context.query_text == "Kubernetes memory incident"
    assert len(context.items) == 2


def test_context_items_receive_deterministic_ranks() -> None:
    query = make_query()

    results = [
        make_result("DOC-001", "First", 80),
        make_result("DOC-002", "Second", 70),
        make_result("DOC-003", "Third", 60),
    ]

    context = ContextAssembler().assemble(
        context_id="CTX-RANK",
        query=query,
        results=results,
    )

    assert [item.rank for item in context.items] == [1, 2, 3]
    assert [item.document_id for item in context.items] == [
        "DOC-001",
        "DOC-002",
        "DOC-003",
    ]


def test_context_preserves_relevance_and_provenance() -> None:
    query = make_query()

    result = make_result(
        "DOC-001",
        "Kubernetes Memory Incident",
        95,
    )

    context = ContextAssembler().assemble(
        context_id="CTX-PROVENANCE",
        query=query,
        results=[result],
    )

    item = context.items[0]

    assert item.score == 95
    assert item.score_breakdown == {"title_match": 95}
    assert item.provenance_reference == "INC-001"
    assert item.provenance_version == "1"
    assert item.provenance_checksum == "sha256:test"
    assert item.provenance_collector == "pytest"


def test_max_items_limits_context() -> None:
    query = make_query(limit=5)

    results = [
        make_result("DOC-001", "First", 100),
        make_result("DOC-002", "Second", 90),
        make_result("DOC-003", "Third", 80),
        make_result("DOC-004", "Fourth", 70),
    ]

    context = ContextAssembler().assemble(
        context_id="CTX-LIMIT",
        query=query,
        results=results,
        max_items=2,
    )

    assert len(context.items) == 2
    assert [item.document_id for item in context.items] == [
        "DOC-001",
        "DOC-002",
    ]


def test_empty_results_produce_valid_empty_context() -> None:
    query = make_query()

    context = ContextAssembler().assemble(
        context_id="CTX-EMPTY",
        query=query,
        results=[],
    )

    assert context.items == ()
    context.validate()


def test_max_items_cannot_exceed_query_limit() -> None:
    query = make_query(limit=2)

    with pytest.raises(ValueError, match="must not exceed query.limit"):
        ContextAssembler().assemble(
            context_id="CTX-INVALID-LIMIT",
            query=query,
            results=[],
            max_items=3,
        )


def test_invalid_result_type_is_rejected() -> None:
    query = make_query()

    with pytest.raises(
        TypeError,
        match="results must contain RetrievalResult objects",
    ):
        ContextAssembler().assemble(
            context_id="CTX-INVALID-RESULT",
            query=query,
            results=[object()],
        )


def test_duplicate_document_ids_are_rejected() -> None:
    query = make_query()

    result = make_result(
        "DOC-DUPLICATE",
        "Duplicate",
        50,
    )

    context = RAGContext(
        context_id="CTX-DUPLICATE",
        query_id=query.query_id,
        query_text=query.text,
        items=(
            RAGContextItem(
                rank=1,
                document_id=result.document_id,
                title=result.title,
                score=result.score,
                score_breakdown=result.score_breakdown,
                knowledge_type=result.knowledge_type,
                source_type=result.source_type,
                resource=result.resource,
                tags=result.tags,
                source=result.source,
                provenance_reference=result.provenance_reference,
                provenance_version=result.provenance_version,
                provenance_checksum=result.provenance_checksum,
                provenance_collected_at=result.provenance_collected_at,
                provenance_collector=result.provenance_collector,
            ),
            RAGContextItem(
                rank=2,
                document_id=result.document_id,
                title=result.title,
                score=result.score,
                score_breakdown=result.score_breakdown,
                knowledge_type=result.knowledge_type,
                source_type=result.source_type,
                resource=result.resource,
                tags=result.tags,
                source=result.source,
                provenance_reference=result.provenance_reference,
                provenance_version=result.provenance_version,
                provenance_checksum=result.provenance_checksum,
                provenance_collected_at=result.provenance_collected_at,
                provenance_collector=result.provenance_collector,
            ),
        ),
        created_at=datetime.now(timezone.utc),
        max_items=2,
    )

    with pytest.raises(
        ValueError,
        match="unique document_ids",
    ):
        context.validate()


def test_json_serialization_is_deterministic() -> None:
    query = make_query()

    result = make_result(
        "DOC-001",
        "Kubernetes Memory Incident",
        95,
    )

    created_at = datetime(
        2026,
        9,
        22,
        13,
        30,
        tzinfo=timezone.utc,
    )

    assembler = ContextAssembler()

    context_a = assembler.assemble(
        context_id="CTX-JSON",
        query=query,
        results=[result],
        created_at=created_at,
    )

    context_b = assembler.assemble(
        context_id="CTX-JSON",
        query=query,
        results=[result],
        created_at=created_at,
    )

    assert context_a.to_json() == context_b.to_json()


def test_json_contains_structured_context_fields() -> None:
    query = make_query()

    result = make_result(
        "DOC-001",
        "Kubernetes Memory Incident",
        95,
    )

    context = ContextAssembler().assemble(
        context_id="CTX-JSON-FIELDS",
        query=query,
        results=[result],
    )

    payload = context.to_dict()

    assert payload["context_id"] == "CTX-JSON-FIELDS"
    assert payload["query_id"] == query.query_id
    assert payload["items"][0]["document_id"] == "DOC-001"
    assert payload["items"][0]["rank"] == 1
    assert payload["items"][0]["score"] == 95
    assert payload["items"][0]["provenance_reference"] == "INC-001"
