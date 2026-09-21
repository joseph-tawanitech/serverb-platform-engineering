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
)
from modules.B19.ingestion.knowledge_ingestor import (
    IngestedKnowledge,
    KnowledgeIngestor,
)


def make_document() -> KnowledgeDocument:
    return KnowledgeDocument(
        document_id="DOC-B19-001",
        title="Example Infrastructure Runbook",
        knowledge_type=KnowledgeType.RUNBOOK,
        source_type=KnowledgeSourceType.FILE,
        content="Restart procedure for the example service.",
        source="docs/runbooks/example-service.md",
        created_at=datetime.now(timezone.utc),
        version="1.0",
        resource="example-service",
        tags=["runbook", "service"],
    )


def make_provenance() -> KnowledgeProvenance:
    return KnowledgeProvenance(
        source="docs/runbooks/example-service.md",
        source_type="file",
        collected_at=datetime.now(timezone.utc),
        collector="server-b-tap-b19",
        version="1.0",
        checksum="sha256:example",
        reference="DOC-B19-001",
    )


def test_valid_knowledge_is_ingested() -> None:
    ingestor = KnowledgeIngestor()

    result = ingestor.ingest(
        make_document(),
        make_provenance(),
    )

    assert isinstance(result, IngestedKnowledge)
    assert result.document.document_id == "DOC-B19-001"
    assert result.provenance.source == (
        "docs/runbooks/example-service.md"
    )


def test_invalid_document_is_rejected() -> None:
    ingestor = KnowledgeIngestor()

    document = make_document()
    document.content = ""

    with pytest.raises(ValueError, match="content must not be empty"):
        ingestor.ingest(document, make_provenance())


def test_invalid_provenance_is_rejected() -> None:
    ingestor = KnowledgeIngestor()

    provenance = make_provenance()
    provenance = KnowledgeProvenance(
        source="",
        source_type=provenance.source_type,
        collected_at=provenance.collected_at,
        collector=provenance.collector,
        version=provenance.version,
        checksum=provenance.checksum,
        reference=provenance.reference,
    )

    with pytest.raises(ValueError, match="source must not be empty"):
        ingestor.ingest(make_document(), provenance)


def test_invalid_document_type_is_rejected() -> None:
    ingestor = KnowledgeIngestor()

    with pytest.raises(
        TypeError,
        match="document must be a KnowledgeDocument",
    ):
        ingestor.ingest(
            "invalid-document",
            make_provenance(),
        )


def test_invalid_provenance_type_is_rejected() -> None:
    ingestor = KnowledgeIngestor()

    with pytest.raises(
        TypeError,
        match="provenance must be a KnowledgeProvenance",
    ):
        ingestor.ingest(
            make_document(),
            "invalid-provenance",
        )
