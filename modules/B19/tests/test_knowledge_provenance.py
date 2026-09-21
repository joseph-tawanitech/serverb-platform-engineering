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
