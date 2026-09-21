from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json

from ..context.context_assembler import RAGContext


@dataclass(frozen=True)
class AIContextRequest:
    """
    B19.10 provider-neutral contract between the deterministic RAG
    context layer and future AI investigation.

    This object transports an already assembled RAGContext to a
    future AI consumer without performing AI reasoning.

    This component does not:
    - invoke AI models
    - select AI providers
    - generate prompts
    - perform retrieval
    - perform embeddings
    - perform RCA
    - authorize actions
    - execute infrastructure changes
    """

    request_id: str
    investigation_id: str
    purpose: str
    context: RAGContext
    created_at: datetime

    def validate(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id must not be empty")

        if not self.investigation_id.strip():
            raise ValueError("investigation_id must not be empty")

        if not self.purpose.strip():
            raise ValueError("purpose must not be empty")

        if not isinstance(self.context, RAGContext):
            raise TypeError("context must be a RAGContext")

        self.context.validate()

        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime")

    def to_dict(self) -> dict[str, object]:
        self.validate()

        return {
            "request_id": self.request_id,
            "investigation_id": self.investigation_id,
            "purpose": self.purpose,
            "created_at": self.created_at.isoformat(),
            "context": self.context.to_dict(),
        }

    def to_json(self) -> str:
        """
        Return deterministic JSON representation of the AI context
        consumption request.
        """
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )


class AIContextContract:
    """
    B19.10 deterministic AI-context contract.

    Wraps a validated B19.9 RAGContext in an explicit request
    boundary for future AI investigation.

    The contract remains provider-neutral and contains no model,
    vendor, prompt, or execution logic.
    """

    def create_request(
        self,
        *,
        request_id: str,
        investigation_id: str,
        purpose: str,
        context: RAGContext,
        created_at: datetime | None = None,
    ) -> AIContextRequest:
        if created_at is None:
            created_at = datetime.now(timezone.utc)

        request = AIContextRequest(
            request_id=request_id,
            investigation_id=investigation_id,
            purpose=purpose,
            context=context,
            created_at=created_at,
        )

        request.validate()
        return request
