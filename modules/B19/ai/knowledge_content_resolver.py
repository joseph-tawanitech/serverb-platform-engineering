from __future__ import annotations

from dataclasses import dataclass

from ..engine.knowledge_model import KnowledgeDocument
from ..engine.knowledge_repository import KnowledgeRepository
from .ai_context_contract import AIContextRequest


@dataclass(frozen=True)
class ResolvedKnowledgeContent:
    """
    B19.11 resolved authoritative knowledge content.

    Represents knowledge selected by the B19 RAG pipeline after
    controlled resolution through the KnowledgeRepository.

    This component does not perform:
    - AI reasoning
    - prompt generation
    - model selection
    - retrieval or ranking
    - authorization
    - infrastructure execution
    """

    rank: int
    document_id: str
    title: str
    content: str
    source: str
    knowledge_type: str
    source_type: str
    resource: str | None
    incident_id: str | None
    version: str | None
    provenance_reference: str | None
    provenance_checksum: str | None

    def validate(self) -> None:
        if self.rank < 1:
            raise ValueError("rank must be greater than zero")
        if not self.document_id.strip():
            raise ValueError("document_id must not be empty")
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not self.content.strip():
            raise ValueError("content must not be empty")
        if not self.source.strip():
            raise ValueError("source must not be empty")
        if self.resource is not None and not self.resource.strip():
            raise ValueError("resource must not be empty when provided")
        if self.incident_id is not None and not self.incident_id.strip():
            raise ValueError("incident_id must not be empty when provided")
        if self.version is not None and not self.version.strip():
            raise ValueError("version must not be empty when provided")
        if (
            self.provenance_reference is not None
            and not self.provenance_reference.strip()
        ):
            raise ValueError(
                "provenance_reference must not be empty when provided"
            )
        if (
            self.provenance_checksum is not None
            and not self.provenance_checksum.strip()
        ):
            raise ValueError(
                "provenance_checksum must not be empty when provided"
            )


@dataclass(frozen=True)
class ResolvedKnowledgeContext:
    """
    B19.11 controlled collection of resolved knowledge content.
    """

    request_id: str
    investigation_id: str
    purpose: str
    items: tuple[ResolvedKnowledgeContent, ...]
    max_items: int
    max_content_chars: int
    total_content_chars: int

    def validate(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id must not be empty")
        if not self.investigation_id.strip():
            raise ValueError("investigation_id must not be empty")
        if not self.purpose.strip():
            raise ValueError("purpose must not be empty")
        if self.max_items < 1:
            raise ValueError("max_items must be greater than zero")
        if self.max_content_chars < 1:
            raise ValueError("max_content_chars must be greater than zero")
        if len(self.items) > self.max_items:
            raise ValueError("resolved context exceeds max_items")

        expected_rank = 1
        calculated_chars = 0

        for item in self.items:
            if not isinstance(item, ResolvedKnowledgeContent):
                raise TypeError(
                    "items must contain ResolvedKnowledgeContent objects"
                )

            item.validate()

            if item.rank != expected_rank:
                raise ValueError(
                    "resolved content ranks must be sequential"
                )

            expected_rank += 1
            calculated_chars += len(item.content)

        if calculated_chars != self.total_content_chars:
            raise ValueError(
                "total_content_chars does not match resolved content"
            )

        if calculated_chars > self.max_content_chars:
            raise ValueError(
                "resolved context exceeds max_content_chars"
            )


class KnowledgeContentResolver:
    """
    B19.11 controlled knowledge content resolution boundary.

    Resolves document IDs already selected by the B19 RAG pipeline
    through the authoritative KnowledgeRepository.

    Resolution is read-only and provider-neutral.
    """

    def resolve(
        self,
        *,
        request: AIContextRequest,
        repository: KnowledgeRepository,
        max_content_chars: int = 20000,
    ) -> ResolvedKnowledgeContext:
        if not isinstance(request, AIContextRequest):
            raise TypeError("request must be an AIContextRequest")

        if not isinstance(repository, KnowledgeRepository):
            raise TypeError(
                "repository must be a KnowledgeRepository"
            )

        if max_content_chars < 1:
            raise ValueError(
                "max_content_chars must be greater than zero"
            )

        request.validate()

        resolved_items: list[ResolvedKnowledgeContent] = []
        total_chars = 0

        for context_item in request.context.items:
            document = repository.get(context_item.document_id)

            if not isinstance(document, KnowledgeDocument):
                raise TypeError(
                    "repository returned an invalid KnowledgeDocument"
                )

            content_length = len(document.content)

            if total_chars + content_length > max_content_chars:
                raise ValueError(
                    "resolved context exceeds max_content_chars"
                )

            resolved_items.append(
                self._resolve_item(
                    rank=context_item.rank,
                    document=document,
                    provenance_reference=context_item.provenance_reference,
                    provenance_checksum=context_item.provenance_checksum,
                )
            )

            total_chars += content_length

        result = ResolvedKnowledgeContext(
            request_id=request.request_id,
            investigation_id=request.investigation_id,
            purpose=request.purpose,
            items=tuple(resolved_items),
            max_items=request.context.max_items,
            max_content_chars=max_content_chars,
            total_content_chars=total_chars,
        )

        result.validate()
        return result

    @staticmethod
    def _resolve_item(
        *,
        rank: int,
        document: KnowledgeDocument,
        provenance_reference: str | None,
        provenance_checksum: str | None,
    ) -> ResolvedKnowledgeContent:
        return ResolvedKnowledgeContent(
            rank=rank,
            document_id=document.document_id,
            title=document.title,
            content=document.content,
            source=document.source,
            knowledge_type=document.knowledge_type.value,
            source_type=document.source_type.value,
            resource=document.resource,
            incident_id=document.incident_id,
            version=document.version,
            provenance_reference=provenance_reference,
            provenance_checksum=provenance_checksum,
        )
