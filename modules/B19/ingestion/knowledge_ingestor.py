from __future__ import annotations

from dataclasses import dataclass

from ..engine.knowledge_model import KnowledgeDocument
from ..engine.knowledge_provenance import (
    KnowledgeProvenance,
    verify_content_checksum,
)


@dataclass(frozen=True)
class IngestedKnowledge:
    """
    B19.3 controlled ingestion result.

    Represents a validated knowledge document together with
    its provenance after successful ingestion.

    Ingestion does not perform:
    - embeddings
    - vector search
    - AI reasoning
    - infrastructure execution
    - authorization
    """

    document: KnowledgeDocument
    provenance: KnowledgeProvenance


class KnowledgeIngestor:
    """
    B19.3 controlled knowledge ingestion boundary.

    Validates a KnowledgeDocument and its provenance before
    allowing the information to enter the B19 knowledge layer.
    """

    def ingest(
        self,
        document: KnowledgeDocument,
        provenance: KnowledgeProvenance,
        *,
        verify_integrity: bool = False,
    ) -> IngestedKnowledge:
        """
        Validate and ingest a knowledge document with provenance.
        """

        if not isinstance(document, KnowledgeDocument):
            raise TypeError(
                "document must be a KnowledgeDocument"
            )

        if not isinstance(provenance, KnowledgeProvenance):
            raise TypeError(
                "provenance must be a KnowledgeProvenance"
            )

        document.validate()
        provenance.validate()

        if verify_integrity:
            if provenance.checksum is None:
                raise ValueError(
                    "checksum is required when integrity verification is enabled"
                )

            if not verify_content_checksum(
                document.content,
                provenance.checksum,
            ):
                raise ValueError(
                    "content checksum verification failed"
                )

        return IngestedKnowledge(
            document=document,
            provenance=provenance,
        )
