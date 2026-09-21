from __future__ import annotations

from dataclasses import dataclass, field

from .knowledge_model import KnowledgeDocument


@dataclass
class KnowledgeRepository:
    """
    B19.1 deterministic in-memory knowledge repository.

    Provides basic controlled storage and retrieval of validated
    KnowledgeDocument objects.

    This foundation intentionally does not perform:
    - embeddings
    - vector search
    - semantic retrieval
    - AI reasoning
    - authorization
    """

    _documents: dict[str, KnowledgeDocument] = field(default_factory=dict)

    def add(self, document: KnowledgeDocument) -> None:
        """Validate and add a knowledge document."""
        document.validate()

        if document.document_id in self._documents:
            raise ValueError(
                f"document already exists: {document.document_id}"
            )

        self._documents[document.document_id] = document

    def get(self, document_id: str) -> KnowledgeDocument:
        """Return a document by ID."""
        if not document_id.strip():
            raise ValueError("document_id must not be empty")

        try:
            return self._documents[document_id]
        except KeyError as exc:
            raise KeyError(
                f"knowledge document not found: {document_id}"
            ) from exc

    def remove(self, document_id: str) -> None:
        """Remove a document by ID."""
        if not document_id.strip():
            raise ValueError("document_id must not be empty")

        if document_id not in self._documents:
            raise KeyError(
                f"knowledge document not found: {document_id}"
            )

        del self._documents[document_id]

    def list_documents(self) -> list[KnowledgeDocument]:
        """Return all stored documents."""
        return list(self._documents.values())

    def count(self) -> int:
        """Return the number of stored documents."""
        return len(self._documents)

    def clear(self) -> None:
        """Remove all stored documents."""
        self._documents.clear()
