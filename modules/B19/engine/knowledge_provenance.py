from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class KnowledgeProvenance:
    """
    B19.1 provenance record.

    Describes where a knowledge document came from and provides
    traceability information for future RAG retrieval.

    Provenance is informational metadata.
    It does not grant authority to execute actions.
    """

    source: str
    source_type: str
    collected_at: datetime
    collector: str
    version: str | None = None
    checksum: str | None = None
    reference: str | None = None

    def validate(self) -> None:
        if not self.source.strip():
            raise ValueError("source must not be empty")

        if not self.source_type.strip():
            raise ValueError("source_type must not be empty")

        if not self.collector.strip():
            raise ValueError("collector must not be empty")

        if self.version is not None and not self.version.strip():
            raise ValueError(
                "version must not be empty when provided"
            )

        if self.checksum is not None and not self.checksum.strip():
            raise ValueError(
                "checksum must not be empty when provided"
            )

        if self.reference is not None and not self.reference.strip():
            raise ValueError(
                "reference must not be empty when provided"
            )
