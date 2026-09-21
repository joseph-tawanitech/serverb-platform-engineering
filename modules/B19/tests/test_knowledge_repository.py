from datetime import datetime

import pytest

from modules.B19.engine.knowledge_model import (
    KnowledgeDocument,
    KnowledgeSourceType,
    KnowledgeType,
)
from modules.B19.engine.knowledge_repository import KnowledgeRepository


def make_document(
    document_id: str = "KB-001",
) -> KnowledgeDocument:
    return KnowledgeDocument(
        document_id=document_id,
        title="Server B Architecture",
        knowledge_type=KnowledgeType.ARCHITECTURE,
        source_type=KnowledgeSourceType.FILE,
        content="Server B provides the TAP infrastructure platform.",
        source="docs/server-b-architecture.md",
        created_at=datetime.now(),
        tags=["server-b", "architecture"],
    )


def test_add_and_get_document():
    repository = KnowledgeRepository()
    document = make_document()

    repository.add(document)

    assert repository.get("KB-001") is document


def test_count_documents():
    repository = KnowledgeRepository()

    repository.add(make_document("KB-001"))
    repository.add(make_document("KB-002"))

    assert repository.count() == 2


def test_list_documents():
    repository = KnowledgeRepository()

    document_one = make_document("KB-001")
    document_two = make_document("KB-002")

    repository.add(document_one)
    repository.add(document_two)

    documents = repository.list_documents()

    assert documents == [document_one, document_two]


def test_duplicate_document_id_rejected():
    repository = KnowledgeRepository()

    repository.add(make_document("KB-001"))

    with pytest.raises(
        ValueError,
        match="document already exists: KB-001",
    ):
        repository.add(make_document("KB-001"))


def test_invalid_document_rejected():
    repository = KnowledgeRepository()
    document = make_document()
    document.content = ""

    with pytest.raises(
        ValueError,
        match="content must not be empty",
    ):
        repository.add(document)


def test_missing_document_rejected():
    repository = KnowledgeRepository()

    with pytest.raises(
        KeyError,
        match="knowledge document not found: KB-404",
    ):
        repository.get("KB-404")


def test_empty_document_id_rejected_on_get():
    repository = KnowledgeRepository()

    with pytest.raises(
        ValueError,
        match="document_id must not be empty",
    ):
        repository.get("   ")


def test_remove_document():
    repository = KnowledgeRepository()
    repository.add(make_document())

    repository.remove("KB-001")

    assert repository.count() == 0

    with pytest.raises(
        KeyError,
        match="knowledge document not found: KB-001",
    ):
        repository.get("KB-001")


def test_remove_missing_document_rejected():
    repository = KnowledgeRepository()

    with pytest.raises(
        KeyError,
        match="knowledge document not found: KB-404",
    ):
        repository.remove("KB-404")


def test_clear_repository():
    repository = KnowledgeRepository()

    repository.add(make_document("KB-001"))
    repository.add(make_document("KB-002"))

    repository.clear()

    assert repository.count() == 0
    assert repository.list_documents() == []
