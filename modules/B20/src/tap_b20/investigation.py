"""Security investigation contracts for TAP B20."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .evidence import SecurityEvidence


@dataclass(frozen=True)
class SecurityInvestigation:
    """Deterministic security investigation context."""

    investigation_id: str
    environment: str
    asset: str
    question: str
    evidence: tuple[SecurityEvidence, ...] = ()
    knowledge_context: dict[str, Any] = field(default_factory=dict)
    missing_evidence: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def validate(self) -> None:
        if not self.investigation_id.strip():
            raise ValueError("investigation_id must not be empty")

        if not self.environment.strip():
            raise ValueError("environment must not be empty")

        if not self.asset.strip():
            raise ValueError("asset must not be empty")

        if not self.question.strip():
            raise ValueError("question must not be empty")

        for item in self.evidence:
            if not isinstance(item, SecurityEvidence):
                raise TypeError(
                    "evidence must contain SecurityEvidence objects"
                )

            if not item.is_utc():
                raise ValueError(
                    "security evidence timestamps must be UTC"
                )

        if not isinstance(self.knowledge_context, dict):
            raise TypeError(
                "knowledge_context must be a dictionary"
            )

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "metadata must be a dictionary"
            )

        if not isinstance(self.created_at, datetime):
            raise TypeError(
                "created_at must be a datetime"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
            or self.created_at.utcoffset().total_seconds() != 0
        ):
            raise ValueError(
                "created_at must be timezone-aware UTC"
            )


@dataclass(frozen=True)
class InvestigationSummary:
    """Deterministic summary of available investigation evidence."""

    investigation_id: str
    evidence_count: int
    highest_severity: str | None
    evidence_sources: tuple[str, ...]
    missing_evidence: tuple[str, ...]

    def validate(self) -> None:
        if not self.investigation_id.strip():
            raise ValueError(
                "investigation_id must not be empty"
            )

        if self.evidence_count < 0:
            raise ValueError(
                "evidence_count must not be negative"
            )

        if len(set(self.evidence_sources)) != len(
            self.evidence_sources
        ):
            raise ValueError(
                "evidence_sources must be unique"
            )


class SecurityInvestigationBuilder:
    """Build deterministic investigation context from authorized evidence."""

    def build(
        self,
        *,
        investigation_id: str,
        environment: str,
        asset: str,
        question: str,
        evidence: list[SecurityEvidence],
        knowledge_context: dict[str, Any] | None = None,
        missing_evidence: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> SecurityInvestigation:
        if not isinstance(evidence, list):
            raise TypeError(
                "evidence must be a list"
            )

        if knowledge_context is None:
            knowledge_context = {}

        if metadata is None:
            metadata = {}

        if created_at is None:
            created_at = datetime.now(timezone.utc)

        investigation = SecurityInvestigation(
            investigation_id=investigation_id,
            environment=environment,
            asset=asset,
            question=question,
            evidence=tuple(evidence),
            knowledge_context=knowledge_context,
            missing_evidence=missing_evidence,
            metadata=metadata,
            created_at=created_at,
        )

        investigation.validate()
        return investigation

    def summarize(
        self,
        investigation: SecurityInvestigation,
    ) -> InvestigationSummary:
        if not isinstance(
            investigation,
            SecurityInvestigation,
        ):
            raise TypeError(
                "investigation must be a SecurityInvestigation"
            )

        investigation.validate()

        severities = [
            evidence.severity.value
            for evidence in investigation.evidence
        ]

        severity_order = {
            "INFO": 0,
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4,
        }

        highest_severity = (
            max(
                severities,
                key=lambda value: severity_order.get(
                    value,
                    -1,
                ),
            )
            if severities
            else None
        )

        sources = tuple(
            sorted(
                {
                    evidence.source
                    for evidence in investigation.evidence
                }
            )
        )

        summary = InvestigationSummary(
            investigation_id=investigation.investigation_id,
            evidence_count=len(investigation.evidence),
            highest_severity=highest_severity,
            evidence_sources=sources,
            missing_evidence=investigation.missing_evidence,
        )

        summary.validate()
        return summary
