from __future__ import annotations

from dataclasses import dataclass

from ..ingestion.knowledge_ingestor import IngestedKnowledge


@dataclass(frozen=True)
class EvidenceIndexEntry:
    """
    Deterministic index entry for B19 evidence.

    The index stores searchable metadata and traceability references.
    It does not store embeddings or perform semantic retrieval.
    """

    document_id: str
    title: str
    knowledge_type: str
    source_type: str
    resource: str | None
    tags: tuple[str, ...]
    source: str
    provenance_reference: str | None


class EvidenceIndex:
    """
    B19.4 deterministic evidence index.

    Provides metadata-based indexing of successfully ingested
    knowledge.

    This module does not perform:
    - embeddings
    - vector search
    - semantic retrieval
    - AI reasoning
    - authorization
    - infrastructure execution
    """

    def __init__(self) -> None:
        self._entries: dict[str, EvidenceIndexEntry] = {}

    def index(
        self,
        knowledge: IngestedKnowledge,
    ) -> EvidenceIndexEntry:
        """
        Add validated ingested knowledge to the evidence index.
        """

        if not isinstance(knowledge, IngestedKnowledge):
            raise TypeError(
                "knowledge must be an IngestedKnowledge"
            )

        document = knowledge.document
        provenance = knowledge.provenance

        entry = EvidenceIndexEntry(
            document_id=document.document_id,
            title=document.title,
            knowledge_type=document.knowledge_type.value,
            source_type=document.source_type.value,
            resource=document.resource,
            tags=tuple(document.tags),
            source=provenance.source,
            provenance_reference=provenance.reference,
        )

        self._entries[entry.document_id] = entry

        return entry

    def get(
        self,
        document_id: str,
    ) -> EvidenceIndexEntry | None:
        """Return an indexed entry by document ID."""

        return self._entries.get(document_id)

    def remove(
        self,
        document_id: str,
    ) -> EvidenceIndexEntry | None:
        """Remove and return an indexed entry."""

        return self._entries.pop(document_id, None)

    def list_entries(self) -> list[EvidenceIndexEntry]:
        """Return all indexed entries."""

        return list(self._entries.values())

    def count(self) -> int:
        """Return the number of indexed entries."""

        return len(self._entries)

    def clear(self) -> None:
        """Remove all indexed entries."""

        self._entries.clear()
