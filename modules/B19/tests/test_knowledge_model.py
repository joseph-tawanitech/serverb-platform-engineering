from datetime import datetime, timedelta

import pytest

from modules.B19.engine.knowledge_model import (
    KnowledgeDocument,
    KnowledgeSourceType,
    KnowledgeType,
)


def make_valid_document() -> KnowledgeDocument:
    return KnowledgeDocument(
        document_id="KB-B18-001",
        title="B18 Root Cause Analysis",
        knowledge_type=KnowledgeType.RCA,
        source_type=KnowledgeSourceType.FILE,
        content="The incident investigation identified the root cause.",
        source="modules/B18/docs/B18.8-ROOT-CAUSE-ANALYSIS.md",
        created_at=datetime.now(),
        version="1.0",
        resource="server-b-tap",
        incident_id="INC-001",
        evidence_ids=["EVID-001", "EVID-002"],
        tags=["b18", "rca", "incident"],
        metadata={"authoritative": True},
    )


def test_valid_knowledge_document():
    document = make_valid_document()

    document.validate()


def test_empty_document_id_rejected():
    document = make_valid_document()
    document.document_id = "   "

    with pytest.raises(ValueError, match="document_id must not be empty"):
        document.validate()


def test_empty_title_rejected():
    document = make_valid_document()
    document.title = ""

    with pytest.raises(ValueError, match="title must not be empty"):
        document.validate()


def test_invalid_knowledge_type_rejected():
    document = make_valid_document()
    document.knowledge_type = "invalid"

    with pytest.raises(ValueError, match="knowledge_type must be a KnowledgeType"):
        document.validate()


def test_invalid_source_type_rejected():
    document = make_valid_document()
    document.source_type = "invalid"

    with pytest.raises(ValueError, match="source_type must be a KnowledgeSourceType"):
        document.validate()


def test_empty_content_rejected():
    document = make_valid_document()
    document.content = "   "

    with pytest.raises(ValueError, match="content must not be empty"):
        document.validate()


def test_empty_source_rejected():
    document = make_valid_document()
    document.source = ""

    with pytest.raises(ValueError, match="source must not be empty"):
        document.validate()


def test_updated_at_before_created_at_rejected():
    document = make_valid_document()
    document.updated_at = document.created_at - timedelta(seconds=1)

    with pytest.raises(
        ValueError,
        match="updated_at must not be earlier than created_at",
    ):
        document.validate()


def test_empty_version_rejected():
    document = make_valid_document()
    document.version = "   "

    with pytest.raises(
        ValueError,
        match="version must not be empty when provided",
    ):
        document.validate()


def test_empty_resource_rejected():
    document = make_valid_document()
    document.resource = "   "

    with pytest.raises(
        ValueError,
        match="resource must not be empty when provided",
    ):
        document.validate()


def test_empty_incident_id_rejected():
    document = make_valid_document()
    document.incident_id = " "

    with pytest.raises(
        ValueError,
        match="incident_id must not be empty when provided",
    ):
        document.validate()


def test_duplicate_evidence_ids_rejected():
    document = make_valid_document()
    document.evidence_ids = ["EVID-001", "EVID-001"]

    with pytest.raises(
        ValueError,
        match="evidence_ids must be unique",
    ):
        document.validate()


def test_duplicate_tags_rejected():
    document = make_valid_document()
    document.tags = ["b18", "b18"]

    with pytest.raises(
        ValueError,
        match="tags must be unique",
    ):
        document.validate()
