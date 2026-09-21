from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class KnowledgeType(str, Enum):
    DOCUMENTATION = "documentation"
    INCIDENT = "incident"
    RCA = "rca"
    EVIDENCE = "evidence"
    CONFIGURATION = "configuration"
    PROCEDURE = "procedure"
    ARCHITECTURE = "architecture"
    RUNBOOK = "runbook"
    OTHER = "other"


class KnowledgeSourceType(str, Enum):
    FILE = "file"
    DATABASE = "database"
    INCIDENT_RECORD = "incident_record"
    EVIDENCE_STORE = "evidence_store"
    MCP = "mcp"
    API = "api"
    MANUAL = "manual"
    OTHER = "other"


@dataclass
class KnowledgeDocument:
    """
    B19.1 foundational knowledge document.

    Represents a controlled piece of information that may later
    be indexed and retrieved by the RAG system.
    """

    document_id: str
    title: str
    knowledge_type: KnowledgeType
    source_type: KnowledgeSourceType
    content: str
    source: str
    created_at: datetime
    updated_at: datetime | None = None
    version: str | None = None
    resource: str | None = None
    incident_id: str | None = None
    evidence_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.document_id.strip():
            raise ValueError("document_id must not be empty")

        if not self.title.strip():
            raise ValueError("title must not be empty")

        if not isinstance(self.knowledge_type, KnowledgeType):
            raise ValueError("knowledge_type must be a KnowledgeType")

        if not isinstance(self.source_type, KnowledgeSourceType):
            raise ValueError("source_type must be a KnowledgeSourceType")

        if not self.content.strip():
            raise ValueError("content must not be empty")

        if not self.source.strip():
            raise ValueError("source must not be empty")

        if self.updated_at is not None and self.updated_at < self.created_at:
            raise ValueError("updated_at must not be earlier than created_at")

        if self.version is not None and not self.version.strip():
            raise ValueError("version must not be empty when provided")

        if self.resource is not None and not self.resource.strip():
            raise ValueError("resource must not be empty when provided")

        if self.incident_id is not None and not self.incident_id.strip():
            raise ValueError("incident_id must not be empty when provided")

        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids must be unique")

        if len(set(self.tags)) != len(self.tags):
            raise ValueError("tags must be unique")
