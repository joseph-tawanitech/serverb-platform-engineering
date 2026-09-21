from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json

from ..retrieval.retrieval_engine import RetrievalQuery, RetrievalResult


@dataclass(frozen=True)
class RAGContextItem:
    """
    B19.9 structured representation of one retrieved knowledge item.

    This model packages B19.8 retrieval results for future AI
    consumption without performing AI reasoning.
    """

    rank: int
    document_id: str
    title: str
    score: int
    score_breakdown: dict[str, int]
    knowledge_type: str
    source_type: str
    resource: str | None
    tags: tuple[str, ...]
    source: str
    provenance_reference: str | None
    provenance_version: str | None
    provenance_checksum: str | None
    provenance_collected_at: object
    provenance_collector: str

    def validate(self) -> None:
        if self.rank < 1:
            raise ValueError("rank must be greater than zero")

        if not self.document_id.strip():
            raise ValueError("document_id must not be empty")

        if not self.title.strip():
            raise ValueError("title must not be empty")

        if self.score < 0:
            raise ValueError("score must not be negative")

        if not isinstance(self.score_breakdown, dict):
            raise TypeError("score_breakdown must be a dictionary")

        if self.resource is not None and not self.resource.strip():
            raise ValueError(
                "resource must not be empty when provided"
            )

        if not self.source.strip():
            raise ValueError("source must not be empty")

        if not self.provenance_collector.strip():
            raise ValueError(
                "provenance_collector must not be empty"
            )

        if len(set(self.tags)) != len(self.tags):
            raise ValueError("tags must be unique")


@dataclass(frozen=True)
class RAGContext:
    """
    B19.9 assembled RAG context.

    Represents retrieved knowledge packaged for future AI reasoning.

    This object contains context only. It does not perform reasoning,
    authorization, remediation, or infrastructure execution.
    """

    context_id: str
    query_id: str
    query_text: str
    items: tuple[RAGContextItem, ...]
    created_at: datetime
    max_items: int

    def validate(self) -> None:
        if not self.context_id.strip():
            raise ValueError("context_id must not be empty")

        if not self.query_id.strip():
            raise ValueError("query_id must not be empty")

        if not self.query_text.strip():
            raise ValueError("query_text must not be empty")

        if self.max_items < 1:
            raise ValueError("max_items must be greater than zero")

        if len(self.items) > self.max_items:
            raise ValueError(
                "context contains more items than max_items"
            )

        expected_rank = 1

        for item in self.items:
            if not isinstance(item, RAGContextItem):
                raise TypeError(
                    "items must contain RAGContextItem objects"
                )

            item.validate()

            if item.rank != expected_rank:
                raise ValueError(
                    "context item ranks must be sequential"
                )

            expected_rank += 1

        document_ids = [item.document_id for item in self.items]

        if len(set(document_ids)) != len(document_ids):
            raise ValueError(
                "context items must contain unique document_ids"
            )

    def to_dict(self) -> dict[str, object]:
        """
        Produce deterministic structured context data.
        """

        self.validate()

        return {
            "context_id": self.context_id,
            "query_id": self.query_id,
            "query_text": self.query_text,
            "created_at": self.created_at.isoformat(),
            "max_items": self.max_items,
            "items": [
                {
                    "rank": item.rank,
                    "document_id": item.document_id,
                    "title": item.title,
                    "score": item.score,
                    "score_breakdown": dict(
                        sorted(item.score_breakdown.items())
                    ),
                    "knowledge_type": item.knowledge_type,
                    "source_type": item.source_type,
                    "resource": item.resource,
                    "tags": list(item.tags),
                    "source": item.source,
                    "provenance_reference": (
                        item.provenance_reference
                    ),
                    "provenance_version": (
                        item.provenance_version
                    ),
                    "provenance_checksum": (
                        item.provenance_checksum
                    ),
                    "provenance_collected_at": (
                        item.provenance_collected_at.isoformat()
                        if hasattr(
                            item.provenance_collected_at,
                            "isoformat",
                        )
                        else str(item.provenance_collected_at)
                    ),
                    "provenance_collector": (
                        item.provenance_collector
                    ),
                }
                for item in self.items
            ],
        }

    def to_json(self) -> str:
        """
        Serialize the context deterministically as JSON.
        """

        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )


class ContextAssembler:
    """
    B19.9 deterministic RAG context assembler.

    Converts B19.8 RetrievalResult objects into a structured
    RAGContext suitable for future AI consumption.

    This component does not:
    - invoke AI models
    - generate prompts
    - perform embeddings
    - perform vector search
    - perform AI reasoning
    - authorize actions
    - execute infrastructure changes
    """

    def assemble(
        self,
        *,
        context_id: str,
        query: RetrievalQuery,
        results: list[RetrievalResult],
        max_items: int | None = None,
        created_at: datetime | None = None,
    ) -> RAGContext:
        if not context_id.strip():
            raise ValueError("context_id must not be empty")

        if not isinstance(query, RetrievalQuery):
            raise TypeError(
                "query must be a RetrievalQuery"
            )

        if not isinstance(results, list):
            raise TypeError("results must be a list")

        query.validate()

        if max_items is None:
            max_items = query.limit

        if max_items < 1:
            raise ValueError(
                "max_items must be greater than zero"
            )

        if max_items > query.limit:
            raise ValueError(
                "max_items must not exceed query.limit"
            )

        if created_at is None:
            created_at = datetime.now(timezone.utc)

        selected_results = results[:max_items]

        items = tuple(
            self._to_context_item(
                rank=index,
                result=result,
            )
            for index, result in enumerate(
                selected_results,
                start=1,
            )
        )

        context = RAGContext(
            context_id=context_id,
            query_id=query.query_id,
            query_text=query.text,
            items=items,
            created_at=created_at,
            max_items=max_items,
        )

        context.validate()

        return context

    @staticmethod
    def _to_context_item(
        *,
        rank: int,
        result: RetrievalResult,
    ) -> RAGContextItem:
        if not isinstance(result, RetrievalResult):
            raise TypeError(
                "results must contain RetrievalResult objects"
            )

        return RAGContextItem(
            rank=rank,
            document_id=result.document_id,
            title=result.title,
            score=result.score,
            score_breakdown=dict(result.score_breakdown),
            knowledge_type=result.knowledge_type,
            source_type=result.source_type,
            resource=result.resource,
            tags=tuple(result.tags),
            source=result.source,
            provenance_reference=result.provenance_reference,
            provenance_version=result.provenance_version,
            provenance_checksum=result.provenance_checksum,
            provenance_collected_at=result.provenance_collected_at,
            provenance_collector=result.provenance_collector,
        )
