from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib


@dataclass(frozen=True)
class KnowledgeProvenance:
    """
    B19.7 document provenance record.

    Describes where a knowledge document came from and provides
    traceability and integrity information for RAG retrieval.

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


@dataclass(frozen=True)
class KnowledgeRetrievalRecord:
    """
    B19.7 retrieval provenance record.

    Records how and when a knowledge document was retrieved.

    Retrieval provenance is informational metadata.
    It does not grant authority to execute actions.
    """

    retrieval_id: str
    document_id: str
    retrieved_at: datetime
    retrieval_method: str
    source: str

    def validate(self) -> None:
        if not self.retrieval_id.strip():
            raise ValueError("retrieval_id must not be empty")

        if not self.document_id.strip():
            raise ValueError("document_id must not be empty")

        if not self.retrieval_method.strip():
            raise ValueError(
                "retrieval_method must not be empty"
            )

        if not self.source.strip():
            raise ValueError("source must not be empty")


def calculate_content_checksum(content: str) -> str:
    """Return the SHA-256 checksum for knowledge content."""

    if not isinstance(content, str):
        raise TypeError("content must be a string")

    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"


def verify_content_checksum(
    content: str,
    checksum: str,
) -> bool:
    """Verify knowledge content against a SHA-256 checksum."""

    if not isinstance(content, str):
        raise TypeError("content must be a string")

    if not isinstance(checksum, str) or not checksum.strip():
        raise ValueError("checksum must not be empty")

    return calculate_content_checksum(content) == checksum
