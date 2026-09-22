from __future__ import annotations

from dataclasses import dataclass

from ..ai.knowledge_content_resolver import ResolvedKnowledgeContext


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    passed: bool
    detail: str

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("name must not be empty")
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be a boolean")
        if not self.detail.strip():
            raise ValueError("detail must not be empty")


@dataclass(frozen=True)
class RAGReadinessResult:
    request_id: str
    investigation_id: str
    status: str
    ready_for_ai_investigation: bool
    checks: tuple[ReadinessCheck, ...]
    validated_items: int

    def validate(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id must not be empty")
        if not self.investigation_id.strip():
            raise ValueError("investigation_id must not be empty")
        if self.status not in {"READY", "NOT_READY"}:
            raise ValueError("status must be READY or NOT_READY")
        if not isinstance(self.ready_for_ai_investigation, bool):
            raise TypeError(
                "ready_for_ai_investigation must be a boolean"
            )
        if self.validated_items < 0:
            raise ValueError("validated_items must not be negative")

        for check in self.checks:
            if not isinstance(check, ReadinessCheck):
                raise TypeError(
                    "checks must contain ReadinessCheck objects"
                )
            check.validate()

        expected_status = all(check.passed for check in self.checks)

        if self.ready_for_ai_investigation != expected_status:
            raise ValueError(
                "readiness flag does not match validation checks"
            )

        expected_status_name = (
            "READY" if expected_status else "NOT_READY"
        )

        if self.status != expected_status_name:
            raise ValueError(
                "status does not match validation checks"
            )


class RAGReadinessValidator:
    """
    B19.12 deterministic RAG-to-AI investigation readiness validator.

    Validates the output of B19.11 without accessing the knowledge
    repository and without performing AI reasoning.

    This component does not:
    - call an AI model
    - perform RCA
    - generate remediation
    - select an AI provider
    - authorize execution
    - execute infrastructure actions
    - modify knowledge
    """

    def validate(
        self,
        context: ResolvedKnowledgeContext,
    ) -> RAGReadinessResult:
        if not isinstance(context, ResolvedKnowledgeContext):
            raise TypeError(
                "context must be a ResolvedKnowledgeContext"
            )

        context.validate()

        checks = (
            self._check_structure(context),
            self._check_grounding(context),
            self._check_provenance(context),
            self._check_bounds(context),
            self._check_identity(context),
        )

        ready = all(check.passed for check in checks)

        result = RAGReadinessResult(
            request_id=context.request_id,
            investigation_id=context.investigation_id,
            status="READY" if ready else "NOT_READY",
            ready_for_ai_investigation=ready,
            checks=checks,
            validated_items=len(context.items),
        )

        result.validate()
        return result

    @staticmethod
    def _check_structure(
        context: ResolvedKnowledgeContext,
    ) -> ReadinessCheck:
        ranks = [item.rank for item in context.items]
        expected_ranks = list(range(1, len(context.items) + 1))

        passed = ranks == expected_ranks

        return ReadinessCheck(
            name="structural_validation",
            passed=passed,
            detail=(
                "Resolved knowledge structure is valid."
                if passed
                else "Resolved knowledge ranks are not sequential."
            ),
        )

    @staticmethod
    def _check_grounding(
        context: ResolvedKnowledgeContext,
    ) -> ReadinessCheck:
        passed = all(
            item.document_id.strip()
            and item.title.strip()
            and item.content.strip()
            and item.source.strip()
            for item in context.items
        )

        return ReadinessCheck(
            name="grounding_validation",
            passed=passed,
            detail=(
                "All resolved items contain authoritative content and source identity."
                if passed
                else "One or more resolved items lack required grounding information."
            ),
        )

    @staticmethod
    def _check_provenance(
        context: ResolvedKnowledgeContext,
    ) -> ReadinessCheck:
        passed = all(
            item.provenance_reference is not None
            or item.provenance_checksum is not None
            for item in context.items
        )

        return ReadinessCheck(
            name="provenance_validation",
            passed=passed,
            detail=(
                "Resolved knowledge retains provenance information."
                if passed
                else "One or more resolved items lack provenance information."
            ),
        )

    @staticmethod
    def _check_bounds(
        context: ResolvedKnowledgeContext,
    ) -> ReadinessCheck:
        passed = (
            len(context.items) <= context.max_items
            and context.total_content_chars <= context.max_content_chars
        )

        return ReadinessCheck(
            name="bounds_validation",
            passed=passed,
            detail=(
                "Resolved knowledge remains within configured bounds."
                if passed
                else "Resolved knowledge exceeds configured bounds."
            ),
        )

    @staticmethod
    def _check_identity(
        context: ResolvedKnowledgeContext,
    ) -> ReadinessCheck:
        passed = (
            bool(context.request_id.strip())
            and bool(context.investigation_id.strip())
            and bool(context.purpose.strip())
        )

        return ReadinessCheck(
            name="context_identity_validation",
            passed=passed,
            detail=(
                "Request, investigation, and purpose identity are preserved."
                if passed
                else "Required context identity is incomplete."
            ),
        )
