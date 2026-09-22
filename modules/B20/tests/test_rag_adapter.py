from datetime import datetime, timezone

from B19.ai.ai_context_contract import AIContextRequest
from B19.engine.knowledge_model import (
    KnowledgeDocument,
    KnowledgeSourceType,
    KnowledgeType,
)
from B19.indexing.evidence_index import EvidenceIndex
from B19.ingestion.knowledge_ingestor import KnowledgeIngestor
from B19.engine.knowledge_provenance import KnowledgeProvenance
from B19.retrieval.retrieval_engine import RetrievalEngine

from tap_b20.investigation import SecurityInvestigationBuilder
from tap_b20.rag_adapter import SecurityRAGAdapter


def make_index() -> EvidenceIndex:
    index = EvidenceIndex()
    ingestor = KnowledgeIngestor()

    documents = [
        KnowledgeDocument(
            document_id="SEC-001",
            title="Kubernetes Security Incident",
            knowledge_type=KnowledgeType.INCIDENT,
            source_type=KnowledgeSourceType.INCIDENT_RECORD,
            content="Previous Kubernetes security incident.",
            source="incident-record",
            created_at=datetime(
                2026, 9, 22, 10, 0, tzinfo=timezone.utc
            ),
            resource="server-b-tap",
            tags=["security", "kubernetes"],
        ),
        KnowledgeDocument(
            document_id="SEC-002",
            title="Kubernetes Security RCA",
            knowledge_type=KnowledgeType.RCA,
            source_type=KnowledgeSourceType.INCIDENT_RECORD,
            content="Root cause analysis for a Kubernetes security incident.",
            source="rca-record",
            created_at=datetime(
                2026, 9, 22, 10, 5, tzinfo=timezone.utc
            ),
            resource="server-b-tap",
            tags=["security", "kubernetes"],
        ),
        KnowledgeDocument(
            document_id="SEC-003",
            title="Kubernetes Security Runbook",
            knowledge_type=KnowledgeType.RUNBOOK,
            source_type=KnowledgeSourceType.FILE,
            content="Security investigation runbook.",
            source="security-runbook",
            created_at=datetime(
                2026, 9, 22, 10, 10, tzinfo=timezone.utc
            ),
            resource="server-b-tap",
            tags=["security", "kubernetes"],
        ),
        KnowledgeDocument(
            document_id="OTHER-001",
            title="Network Security Procedure",
            knowledge_type=KnowledgeType.PROCEDURE,
            source_type=KnowledgeSourceType.FILE,
            content="Network security procedure for another resource.",
            source="network-procedure",
            created_at=datetime(
                2026, 9, 22, 10, 15, tzinfo=timezone.utc
            ),
            resource="other-resource",
            tags=["security", "network"],
        ),
    ]

    for document in documents:
        provenance = KnowledgeProvenance(
            source=document.source,
            source_type=document.source_type.value,
            collected_at=datetime(
                2026, 9, 22, 12, 0, tzinfo=timezone.utc
            ),
            collector="B20.6-test",
            reference=f"test:{document.document_id}",
        )

        ingested = ingestor.ingest(
            document,
            provenance,
        )
        index.index(ingested)

    return index


def make_investigation() -> object:
    return SecurityInvestigationBuilder().build(
        investigation_id="INV-RAG-001",
        environment="test",
        asset="server-b-tap",
        question="Kubernetes security incident",
        evidence=[],
    )


def test_security_rag_adapter_retrieves_b19_knowledge() -> None:
    engine = RetrievalEngine(make_index())
    adapter = SecurityRAGAdapter(engine)
    investigation = make_investigation()

    result = adapter.build_ai_context(
        investigation,
        request_id="AICTX-RAG-001",
        context_id="CTX-RAG-001",
        limit=3,
    )

    assert isinstance(result, AIContextRequest)
    assert result.investigation_id == "INV-RAG-001"
    assert result.context.query_id == "INV-RAG-001-RAG"
    assert result.context.max_items == 3
    assert len(result.context.items) == 3

    document_ids = [
        item.document_id
        for item in result.context.items
    ]

    assert "SEC-001" in document_ids
    assert "OTHER-001" not in document_ids


def test_security_rag_adapter_preserves_ranking_and_provenance() -> None:
    engine = RetrievalEngine(make_index())
    adapter = SecurityRAGAdapter(engine)
    investigation = make_investigation()

    result = adapter.build_ai_context(
        investigation,
        request_id="AICTX-RAG-002",
        context_id="CTX-RAG-002",
        limit=3,
    )

    first = result.context.items[0]

    assert first.rank == 1
    assert first.score >= 0
    assert first.provenance_reference == f"test:{first.document_id}"
    assert first.provenance_collector == "B20.6-test"


def test_security_rag_adapter_rejects_invalid_limit() -> None:
    engine = RetrievalEngine(make_index())
    adapter = SecurityRAGAdapter(engine)
    investigation = make_investigation()

    try:
        adapter.build_ai_context(
            investigation,
            request_id="AICTX-RAG-003",
            context_id="CTX-RAG-003",
            limit=0,
        )
    except ValueError as exc:
        assert "limit must be greater than zero" in str(exc)
    else:
        raise AssertionError("expected ValueError")
