from datetime import datetime, timezone

import pytest

from modules.B19.ai.ai_context_contract import AIContextContract
from modules.B19.ai.knowledge_content_resolver import KnowledgeContentResolver
from modules.B19.context.context_assembler import ContextAssembler
from modules.B19.engine.knowledge_model import (
    KnowledgeDocument,
    KnowledgeSourceType,
    KnowledgeType,
)
from modules.B19.engine.knowledge_provenance import KnowledgeProvenance
from modules.B19.engine.knowledge_repository import KnowledgeRepository
from modules.B19.indexing.evidence_index import EvidenceIndex
from modules.B19.ingestion.knowledge_ingestor import KnowledgeIngestor
from modules.B19.retrieval.retrieval_engine import (
    RetrievalEngine,
    RetrievalQuery,
)
from modules.B19.validation.readiness_validator import (
    RAGReadinessValidator,
    ReadinessCheck,
    RAGReadinessResult,
)


def make_document(
    document_id: str,
    *,
    content: str = "Service recovery runbook content.",
) -> KnowledgeDocument:
    return KnowledgeDocument(
        document_id=document_id,
        title=f"Document {document_id}",
        knowledge_type=KnowledgeType.RUNBOOK,
        source_type=KnowledgeSourceType.FILE,
        content=content,
        source=f"docs/{document_id}.md",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        version="1.0",
        resource="server-b",
        tags=["ops"],
    )


def make_context(
    repository: KnowledgeRepository,
    document_id: str = "DOC-001",
):
    document = repository.get(document_id)

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


def make_resolved_context(
    repository: KnowledgeRepository,
):
    request = make_context(repository)

    return KnowledgeContentResolver().resolve(
        request=request,
        repository=repository,
    )


def test_valid_resolved_context_is_ready_for_ai_investigation():
    repository = KnowledgeRepository()
    repository.add(make_document("DOC-001"))

    context = make_resolved_context(repository)

    result = RAGReadinessValidator().validate(context)

    assert result.status == "READY"
    assert result.ready_for_ai_investigation is True
    assert result.request_id == "REQ-001"
    assert result.investigation_id == "INV-001"
    assert result.validated_items == 1
    assert all(check.passed for check in result.checks)


def test_readiness_result_contains_expected_validation_checks():
    repository = KnowledgeRepository()
    repository.add(make_document("DOC-001"))

    context = make_resolved_context(repository)

    result = RAGReadinessValidator().validate(context)

    check_names = [check.name for check in result.checks]

    assert check_names == [
        "structural_validation",
        "grounding_validation",
        "provenance_validation",
        "bounds_validation",
        "context_identity_validation",
    ]


def test_missing_provenance_prevents_readiness():
    repository = KnowledgeRepository()
    repository.add(make_document("DOC-001"))

    context = make_resolved_context(repository)

    item = context.items[0]
    item_without_provenance = type(item)(
        rank=item.rank,
        document_id=item.document_id,
        title=item.title,
        content=item.content,
        source=item.source,
        knowledge_type=item.knowledge_type,
        source_type=item.source_type,
        resource=item.resource,
        incident_id=item.incident_id,
        version=item.version,
        provenance_reference=None,
        provenance_checksum=None,
    )

    modified_context = type(context)(
        request_id=context.request_id,
        investigation_id=context.investigation_id,
        purpose=context.purpose,
        items=(item_without_provenance,),
        max_items=context.max_items,
        max_content_chars=context.max_content_chars,
        total_content_chars=context.total_content_chars,
    )

    result = RAGReadinessValidator().validate(modified_context)

    assert result.status == "NOT_READY"
    assert result.ready_for_ai_investigation is False

    provenance_check = next(
        check
        for check in result.checks
        if check.name == "provenance_validation"
    )

    assert provenance_check.passed is False


def test_invalid_context_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="context must be a ResolvedKnowledgeContext",
    ):
        RAGReadinessValidator().validate("invalid")


def test_readiness_result_validation_rejects_invalid_status():
    result = RAGReadinessResult(
        request_id="REQ-001",
        investigation_id="INV-001",
        status="INVALID",
        ready_for_ai_investigation=False,
        checks=(),
        validated_items=0,
    )

    with pytest.raises(
        ValueError,
        match="status must be READY or NOT_READY",
    ):
        result.validate()


def test_readiness_check_validation_rejects_empty_name():
    check = ReadinessCheck(
        name="",
        passed=True,
        detail="valid",
    )

    with pytest.raises(
        ValueError,
        match="name must not be empty",
    ):
        check.validate()


def test_validation_is_read_only():
    repository = KnowledgeRepository()
    repository.add(
        make_document(
            "DOC-001",
            content="Original runbook content.",
        )
    )

    before = repository.get("DOC-001")

    context = make_resolved_context(repository)
    RAGReadinessValidator().validate(context)

    after = repository.get("DOC-001")

    assert after is before
    assert after.content == "Original runbook content."
