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
from modules.B19.indexing.evidence_index import (
    EvidenceIndex,
    EvidenceIndexEntry,
)
from modules.B19.ingestion.knowledge_ingestor import (
    KnowledgeIngestor,
)


def make_knowledge():
    document = KnowledgeDocument(
        document_id="DOC-B19-INDEX-001",
        title="Example Evidence",
        knowledge_type=KnowledgeType.EVIDENCE,
        source_type=KnowledgeSourceType.EVIDENCE_STORE,
        content="Example infrastructure evidence.",
        source="evidence/server-b/example.txt",
        created_at=datetime.now(timezone.utc),
        version="1.0",
        resource="server-b-tap",
        tags=["evidence", "server-b", "infrastructure"],
    )

    provenance = KnowledgeProvenance(
        source="evidence/server-b/example.txt",
        source_type="evidence_store",
        collected_at=datetime.now(timezone.utc),
        collector="server-b-tap-b19",
        version="1.0",
        checksum="sha256:example-index",
        reference="EVIDENCE-B19-INDEX-001",
    )

    return KnowledgeIngestor().ingest(
        document,
        provenance,
    )


def test_valid_knowledge_is_indexed() -> None:
    index = EvidenceIndex()

    result = index.index(make_knowledge())

    assert isinstance(result, EvidenceIndexEntry)
    assert result.document_id == "DOC-B19-INDEX-001"
    assert result.knowledge_type == "evidence"
    assert result.source_type == "evidence_store"


def test_indexed_entry_can_be_retrieved() -> None:
    index = EvidenceIndex()

    index.index(make_knowledge())

    result = index.get("DOC-B19-INDEX-001")

    assert result is not None
    assert result.title == "Example Evidence"


def test_missing_entry_returns_none() -> None:
    index = EvidenceIndex()

    assert index.get("DOES-NOT-EXIST") is None


def test_invalid_input_is_rejected() -> None:
    index = EvidenceIndex()

    with pytest.raises(
        TypeError,
        match="knowledge must be an IngestedKnowledge",
    ):
        index.index("invalid")


def test_index_count() -> None:
    index = EvidenceIndex()

    assert index.count() == 0

    index.index(make_knowledge())

    assert index.count() == 1


def test_list_entries() -> None:
    index = EvidenceIndex()

    index.index(make_knowledge())

    entries = index.list_entries()

    assert len(entries) == 1
    assert entries[0].document_id == "DOC-B19-INDEX-001"


def test_remove_entry() -> None:
    index = EvidenceIndex()

    index.index(make_knowledge())

    removed = index.remove("DOC-B19-INDEX-001")

    assert removed is not None
    assert removed.document_id == "DOC-B19-INDEX-001"
    assert index.count() == 0


def test_clear_index() -> None:
    index = EvidenceIndex()

    index.index(make_knowledge())

    assert index.count() == 1

    index.clear()

    assert index.count() == 0


def test_index_preserves_complete_provenance() -> None:
    knowledge = make_knowledge()
    index = EvidenceIndex()

    result = index.index(knowledge)

    assert result.document_id == knowledge.document.document_id
    assert result.source == knowledge.provenance.source
    assert (
        result.provenance_reference
        == knowledge.provenance.reference
    )
    assert (
        result.provenance_version
        == knowledge.provenance.version
    )
    assert (
        result.provenance_checksum
        == knowledge.provenance.checksum
    )
    assert (
        result.provenance_collected_at
        == knowledge.provenance.collected_at
    )
    assert (
        result.provenance_collector
        == knowledge.provenance.collector
    )


def test_index_preserves_incident_id() -> None:
    knowledge = make_knowledge()

    knowledge.document.incident_id = "INC-B19-001"

    index = EvidenceIndex()

    result = index.index(knowledge)

    assert result.incident_id == "INC-B19-001"
