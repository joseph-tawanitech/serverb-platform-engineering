from datetime import datetime, timezone

import pytest

from modules.B19.ai.ai_context_contract import AIContextContract
from modules.B19.ai.knowledge_content_resolver import (
    KnowledgeContentResolver,
    ResolvedKnowledgeContent,
    ResolvedKnowledgeContext,
)
from modules.B19.context.context_assembler import ContextAssembler
from modules.B19.engine.knowledge_model import (
    KnowledgeDocument,
    KnowledgeSourceType,
    KnowledgeType,
)
from modules.B19.engine.knowledge_provenance import KnowledgeProvenance
from modules.B19.engine.knowledge_repository import KnowledgeRepository
from modules.B19.ingestion.knowledge_ingestor import KnowledgeIngestor
from modules.B19.indexing.evidence_index import EvidenceIndex
from modules.B19.retrieval.retrieval_engine import (
    RetrievalEngine,
    RetrievalQuery,
)


def make_document(
    document_id: str,
    *,
    content: str,
    title: str | None = None,
) -> KnowledgeDocument:
    return KnowledgeDocument(
        document_id=document_id,
        title=title or f"Document {document_id}",
        knowledge_type=KnowledgeType.RUNBOOK,
        source_type=KnowledgeSourceType.FILE,
        content=content,
        source=f"docs/{document_id}.md",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        version="1.0",
        resource="server-b",
        tags=["ops"],
    )


def make_context(repository: KnowledgeRepository):
    document = repository.get("DOC-001")

    index = EvidenceIndex()
    provenance = KnowledgeProvenance(
        source=document.source,
        source_type=document.source_type.value,
        collected_at=document.created_at,
        collector="test",
        version=document.version,
        checksum="sha256:test",
        reference="ref-001",
    )

    ingested = KnowledgeIngestor().ingest(
        document,
        provenance,
    )

    index.index(ingested)

    query = RetrievalQuery(
        query_id="Q-001",
        text="server-b runbook",
        resource="server-b",
        limit=5,
    )

    results = RetrievalEngine(index).retrieve(query)

    context = ContextAssembler().assemble(
        context_id="CTX-001",
        query=query,
        results=results,
        max_items=5,
        created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    return AIContextContract().create_request(
        request_id="REQ-001",
        investigation_id="INV-001",
        purpose="incident investigation",
        context=context,
        created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )


def test_resolves_authoritative_document_content():
    repository = KnowledgeRepository()
    repository.add(
        make_document(
            "DOC-001",
            content="Restart the affected service and verify health.",
        )
    )

    request = make_context(repository)
    result = KnowledgeContentResolver().resolve(
        request=request,
        repository=repository,
    )

    assert len(result.items) == 1
    assert result.items[0].document_id == "DOC-001"
    assert (
        result.items[0].content
        == "Restart the affected service and verify health."
    )


def test_preserves_document_metadata():
    repository = KnowledgeRepository()
    repository.add(
        make_document(
            "DOC-001",
            content="Runbook content.",
            title="Service Recovery Runbook",
        )
    )

    request = make_context(repository)
    item = KnowledgeContentResolver().resolve(
        request=request,
        repository=repository,
    ).items[0]

    assert item.title == "Service Recovery Runbook"
    assert item.source == "docs/DOC-001.md"
    assert item.knowledge_type == "runbook"
    assert item.source_type == "file"
    assert item.resource == "server-b"
    assert item.version == "1.0"


def test_preserves_rank_and_context_identity():
    repository = KnowledgeRepository()
    repository.add(make_document("DOC-001", content="Content A"))

    request = make_context(repository)
    result = KnowledgeContentResolver().resolve(
        request=request,
        repository=repository,
    )

    assert result.request_id == "REQ-001"
    assert result.investigation_id == "INV-001"
    assert result.purpose == "incident investigation"
    assert result.items[0].rank == 1


def test_preserves_provenance_metadata_from_rag_context():
    repository = KnowledgeRepository()
    repository.add(make_document("DOC-001", content="Content A"))

    request = make_context(repository)
    item = KnowledgeContentResolver().resolve(
        request=request,
        repository=repository,
    ).items[0]

    assert item.provenance_reference == "ref-001"
    assert item.provenance_checksum == "sha256:test"


def test_missing_document_is_rejected():
    repository = KnowledgeRepository()
    repository.add(make_document("DOC-001", content="Content A"))

    request = make_context(repository)
    repository.remove("DOC-001")

    with pytest.raises(KeyError, match="knowledge document not found"):
        KnowledgeContentResolver().resolve(
            request=request,
            repository=repository,
        )


def test_invalid_request_is_rejected():
    repository = KnowledgeRepository()

    with pytest.raises(TypeError, match="request must be an AIContextRequest"):
        KnowledgeContentResolver().resolve(
            request="invalid",
            repository=repository,
        )


def test_invalid_repository_is_rejected():
    repository = KnowledgeRepository()
    repository.add(make_document("DOC-001", content="Content A"))

    request = make_context(repository)

    with pytest.raises(TypeError, match="repository must be a KnowledgeRepository"):
        KnowledgeContentResolver().resolve(
            request=request,
            repository="invalid",
        )


def test_invalid_content_limit_is_rejected():
    repository = KnowledgeRepository()
    repository.add(make_document("DOC-001", content="Content A"))

    request = make_context(repository)

    with pytest.raises(
        ValueError,
        match="max_content_chars must be greater than zero",
    ):
        KnowledgeContentResolver().resolve(
            request=request,
            repository=repository,
            max_content_chars=0,
        )


def test_content_limit_prevents_oversized_resolution():
    repository = KnowledgeRepository()
    repository.add(
        make_document(
            "DOC-001",
            content="A" * 100,
        )
    )

    request = make_context(repository)

    with pytest.raises(
        ValueError,
        match="resolved context exceeds max_content_chars",
    ):
        KnowledgeContentResolver().resolve(
            request=request,
            repository=repository,
            max_content_chars=50,
        )


def test_total_content_chars_is_calculated():
    repository = KnowledgeRepository()
    repository.add(
        make_document(
            "DOC-001",
            content="12345",
        )
    )

    request = make_context(repository)
    result = KnowledgeContentResolver().resolve(
        request=request,
        repository=repository,
    )

    assert result.total_content_chars == 5


def test_resolution_does_not_modify_repository():
    repository = KnowledgeRepository()
    repository.add(
        make_document(
            "DOC-001",
            content="Original content",
        )
    )

    before = repository.get("DOC-001")
    request = make_context(repository)

    KnowledgeContentResolver().resolve(
        request=request,
        repository=repository,
    )

    after = repository.get("DOC-001")

    assert after is before
    assert after.content == "Original content"


def test_resolved_item_validation_rejects_empty_content():
    item = ResolvedKnowledgeContent(
        rank=1,
        document_id="DOC-001",
        title="Test",
        content="",
        source="test",
        knowledge_type="runbook",
        source_type="file",
        resource=None,
        incident_id=None,
        version=None,
        provenance_reference=None,
        provenance_checksum=None,
    )

    with pytest.raises(ValueError, match="content must not be empty"):
        item.validate()


def test_resolved_context_validation_detects_wrong_character_count():
    result = ResolvedKnowledgeContext(
        request_id="REQ-001",
        investigation_id="INV-001",
        purpose="test",
        items=(
            ResolvedKnowledgeContent(
                rank=1,
                document_id="DOC-001",
                title="Test",
                content="12345",
                source="test",
                knowledge_type="runbook",
                source_type="file",
                resource=None,
                incident_id=None,
                version=None,
                provenance_reference=None,
                provenance_checksum=None,
            ),
        ),
        max_items=1,
        max_content_chars=100,
        total_content_chars=99,
    )

    with pytest.raises(
        ValueError,
        match="total_content_chars does not match resolved content",
    ):
        result.validate()
