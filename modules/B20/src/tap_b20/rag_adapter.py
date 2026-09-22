from __future__ import annotations

from B19.ai.ai_context_contract import AIContextContract, AIContextRequest
from B19.context.context_assembler import ContextAssembler
from B19.retrieval.retrieval_engine import RetrievalEngine, RetrievalQuery
from B19.engine.knowledge_model import KnowledgeType

from .investigation import SecurityInvestigation


class SecurityRAGAdapter:
    """
    B20.6 adapter between security investigations and the existing
    B19 deterministic RAG retrieval/context pipeline.

    B20.6 owns the security investigation workflow.
    B19 owns retrieval, ranking, context assembly, and the
    provider-neutral AI context contract.

    This adapter does not:
    - perform embeddings
    - invoke AI models
    - generate prompts
    - authorize actions
    - execute infrastructure changes
    """

    DEFAULT_KNOWLEDGE_TYPES = (
        KnowledgeType.INCIDENT.value,
        KnowledgeType.RCA.value,
        KnowledgeType.EVIDENCE.value,
        KnowledgeType.CONFIGURATION.value,
        KnowledgeType.PROCEDURE.value,
        KnowledgeType.RUNBOOK.value,
        KnowledgeType.DOCUMENTATION.value,
    )

    def __init__(
        self,
        retrieval_engine: RetrievalEngine,
        *,
        context_assembler: ContextAssembler | None = None,
        context_contract: AIContextContract | None = None,
    ) -> None:
        if not isinstance(retrieval_engine, RetrievalEngine):
            raise TypeError(
                "retrieval_engine must be a RetrievalEngine"
            )

        self._retrieval_engine = retrieval_engine
        self._context_assembler = (
            context_assembler
            if context_assembler is not None
            else ContextAssembler()
        )
        self._context_contract = (
            context_contract
            if context_contract is not None
            else AIContextContract()
        )

    def build_ai_context(
        self,
        investigation: SecurityInvestigation,
        *,
        request_id: str,
        context_id: str,
        limit: int = 5,
    ) -> AIContextRequest:
        """
        Retrieve relevant B19 knowledge for a security investigation
        and package it as a provider-neutral AIContextRequest.
        """

        if not isinstance(
            investigation,
            SecurityInvestigation,
        ):
            raise TypeError(
                "investigation must be a SecurityInvestigation"
            )

        investigation.validate()

        if not request_id.strip():
            raise ValueError(
                "request_id must not be empty"
            )

        if not context_id.strip():
            raise ValueError(
                "context_id must not be empty"
            )

        if limit < 1:
            raise ValueError(
                "limit must be greater than zero"
            )

        query = RetrievalQuery(
            query_id=f"{investigation.investigation_id}-RAG",
            text=investigation.question,
            resource=investigation.asset,
            knowledge_types=self.DEFAULT_KNOWLEDGE_TYPES,
            limit=limit,
        )

        results = self._retrieval_engine.retrieve(query)

        context = self._context_assembler.assemble(
            context_id=context_id,
            query=query,
            results=results,
            max_items=limit,
        )

        return self._context_contract.create_request(
            request_id=request_id,
            investigation_id=investigation.investigation_id,
            purpose="AI security investigation",
            context=context,
        )
