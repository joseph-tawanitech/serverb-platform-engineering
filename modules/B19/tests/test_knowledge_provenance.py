from datetime import datetime

import pytest

from modules.B19.engine.knowledge_provenance import KnowledgeProvenance


def make_provenance() -> KnowledgeProvenance:
    return KnowledgeProvenance(
        source="docs/B18.8-ROOT-CAUSE-ANALYSIS.md",
        source_type="file",
        collected_at=datetime.now(),
        collector="server-b-tap-b19",
        version="1.0",
        checksum="sha256:example",
        reference="B18.8",
    )


def test_valid_provenance():
    provenance = make_provenance()

    provenance.validate()


def test_empty_source_rejected():
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

    with pytest.raises(
        ValueError,
        match="source must not be empty",
    ):
        provenance.validate()


def test_empty_source_type_rejected():
    provenance = make_provenance()
    provenance = KnowledgeProvenance(
        source=provenance.source,
        source_type=" ",
        collected_at=provenance.collected_at,
        collector=provenance.collector,
        version=provenance.version,
        checksum=provenance.checksum,
        reference=provenance.reference,
    )

    with pytest.raises(
        ValueError,
        match="source_type must not be empty",
    ):
        provenance.validate()


def test_empty_collector_rejected():
    provenance = make_provenance()
    provenance = KnowledgeProvenance(
        source=provenance.source,
        source_type=provenance.source_type,
        collected_at=provenance.collected_at,
        collector=" ",
        version=provenance.version,
        checksum=provenance.checksum,
        reference=provenance.reference,
    )

    with pytest.raises(
        ValueError,
        match="collector must not be empty",
    ):
        provenance.validate()


def test_empty_version_rejected():
    provenance = make_provenance()
    provenance = KnowledgeProvenance(
        source=provenance.source,
        source_type=provenance.source_type,
        collected_at=provenance.collected_at,
        collector=provenance.collector,
        version=" ",
        checksum=provenance.checksum,
        reference=provenance.reference,
    )

    with pytest.raises(
        ValueError,
        match="version must not be empty when provided",
    ):
        provenance.validate()


def test_empty_checksum_rejected():
    provenance = make_provenance()
    provenance = KnowledgeProvenance(
        source=provenance.source,
        source_type=provenance.source_type,
        collected_at=provenance.collected_at,
        collector=provenance.collector,
        version=provenance.version,
        checksum=" ",
        reference=provenance.reference,
    )

    with pytest.raises(
        ValueError,
        match="checksum must not be empty when provided",
    ):
        provenance.validate()


def test_empty_reference_rejected():
    provenance = make_provenance()
    provenance = KnowledgeProvenance(
        source=provenance.source,
        source_type=provenance.source_type,
        collected_at=provenance.collected_at,
        collector=provenance.collector,
        version=provenance.version,
        checksum=provenance.checksum,
        reference=" ",
    )

    with pytest.raises(
        ValueError,
        match="reference must not be empty when provided",
    ):
        provenance.validate()


def test_retrieval_record_is_valid() -> None:
    from modules.B19.engine.knowledge_provenance import (
        KnowledgeRetrievalRecord,
    )

    record = KnowledgeRetrievalRecord(
        retrieval_id="RETRIEVAL-B19-001",
        document_id="DOC-B19-001",
        retrieved_at=datetime.now(),
        retrieval_method="deterministic-index",
        source="docs/runbooks/example-service.md",
    )

    record.validate()


def test_empty_retrieval_id_rejected() -> None:
    from modules.B19.engine.knowledge_provenance import (
        KnowledgeRetrievalRecord,
    )

    record = KnowledgeRetrievalRecord(
        retrieval_id=" ",
        document_id="DOC-B19-001",
        retrieved_at=datetime.now(),
        retrieval_method="deterministic-index",
        source="docs/example.md",
    )

    with pytest.raises(
        ValueError,
        match="retrieval_id must not be empty",
    ):
        record.validate()


def test_empty_retrieval_document_id_rejected() -> None:
    from modules.B19.engine.knowledge_provenance import (
        KnowledgeRetrievalRecord,
    )

    record = KnowledgeRetrievalRecord(
        retrieval_id="RETRIEVAL-B19-002",
        document_id=" ",
        retrieved_at=datetime.now(),
        retrieval_method="deterministic-index",
        source="docs/example.md",
    )

    with pytest.raises(
        ValueError,
        match="document_id must not be empty",
    ):
        record.validate()


def test_empty_retrieval_method_rejected() -> None:
    from modules.B19.engine.knowledge_provenance import (
        KnowledgeRetrievalRecord,
    )

    record = KnowledgeRetrievalRecord(
        retrieval_id="RETRIEVAL-B19-003",
        document_id="DOC-B19-001",
        retrieved_at=datetime.now(),
        retrieval_method=" ",
        source="docs/example.md",
    )

    with pytest.raises(
        ValueError,
        match="retrieval_method must not be empty",
    ):
        record.validate()


def test_empty_retrieval_source_rejected() -> None:
    from modules.B19.engine.knowledge_provenance import (
        KnowledgeRetrievalRecord,
    )

    record = KnowledgeRetrievalRecord(
        retrieval_id="RETRIEVAL-B19-004",
        document_id="DOC-B19-001",
        retrieved_at=datetime.now(),
        retrieval_method="deterministic-index",
        source=" ",
    )

    with pytest.raises(
        ValueError,
        match="source must not be empty",
    ):
        record.validate()


def test_content_checksum_is_deterministic() -> None:
    from modules.B19.engine.knowledge_provenance import (
        calculate_content_checksum,
    )

    content = "Example infrastructure evidence."

    first = calculate_content_checksum(content)
    second = calculate_content_checksum(content)

    assert first == second
    assert first.startswith("sha256:")
    assert len(first) == len("sha256:") + 64


def test_content_checksum_changes_when_content_changes() -> None:
    from modules.B19.engine.knowledge_provenance import (
        calculate_content_checksum,
    )

    original = calculate_content_checksum(
        "Example infrastructure evidence."
    )

    modified = calculate_content_checksum(
        "Modified infrastructure evidence."
    )

    assert original != modified


def test_content_checksum_verification_succeeds() -> None:
    from modules.B19.engine.knowledge_provenance import (
        calculate_content_checksum,
        verify_content_checksum,
    )

    content = "Example infrastructure evidence."
    checksum = calculate_content_checksum(content)

    assert verify_content_checksum(content, checksum) is True


def test_content_checksum_verification_detects_tampering() -> None:
    from modules.B19.engine.knowledge_provenance import (
        calculate_content_checksum,
        verify_content_checksum,
    )

    original = "Example infrastructure evidence."
    checksum = calculate_content_checksum(original)

    modified = "Tampered infrastructure evidence."

    assert verify_content_checksum(modified, checksum) is False


def test_checksum_requires_string_content() -> None:
    from modules.B19.engine.knowledge_provenance import (
        calculate_content_checksum,
    )

    with pytest.raises(
        TypeError,
        match="content must be a string",
    ):
        calculate_content_checksum(123)  # type: ignore[arg-type]


def test_checksum_verification_requires_checksum() -> None:
    from modules.B19.engine.knowledge_provenance import (
        verify_content_checksum,
    )

    with pytest.raises(
        ValueError,
        match="checksum must not be empty",
    ):
        verify_content_checksum(
            "Example infrastructure evidence.",
            " ",
        )
