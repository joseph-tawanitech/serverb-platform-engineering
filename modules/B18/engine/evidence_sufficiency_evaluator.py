from __future__ import annotations

from engine.evidence_model import Evidence, EvidenceReliability
from engine.evidence_sufficiency_model import (
    EvidenceSufficiency,
    SufficiencyStatus,
)
from engine.hypothesis_model import Hypothesis


class EvidenceSufficiencyEvaluator:
    """Evaluate whether evidence is sufficient for a hypothesis."""

    RELIABLE_LEVELS = {
        EvidenceReliability.MEDIUM,
        EvidenceReliability.HIGH,
    }

    @staticmethod
    def evaluate(
        hypothesis: Hypothesis,
        evidence_items: list[Evidence],
        required_sources: list[str] | None = None,
    ) -> EvidenceSufficiency:
        """Create a deterministic evidence-sufficiency assessment."""
        hypothesis.validate()

        for evidence in evidence_items:
            evidence.validate()

        evidence_by_id = {
            evidence.evidence_id: evidence
            for evidence in evidence_items
        }

        referenced_ids = set(hypothesis.supporting_evidence_ids)
        referenced_ids.update(hypothesis.contradicting_evidence_ids)

        missing_evidence_ids = sorted(
            evidence_id
            for evidence_id in referenced_ids
            if evidence_id not in evidence_by_id
        )

        supporting = [
            evidence_by_id[evidence_id]
            for evidence_id in hypothesis.supporting_evidence_ids
            if evidence_id in evidence_by_id
        ]

        contradicting = [
            evidence_by_id[evidence_id]
            for evidence_id in hypothesis.contradicting_evidence_ids
            if evidence_id in evidence_by_id
        ]

        reliable_supporting = [
            evidence
            for evidence in supporting
            if evidence.reliability in EvidenceSufficiencyEvaluator.RELIABLE_LEVELS
        ]

        missing_sources = EvidenceSufficiencyEvaluator._missing_sources(
            evidence_items,
            required_sources or [],
        )

        status = EvidenceSufficiencyEvaluator._determine_status(
            supporting_count=len(supporting),
            reliable_supporting_count=len(reliable_supporting),
            contradicting_count=len(contradicting),
            missing_evidence_count=len(missing_evidence_ids),
            missing_sources_count=len(missing_sources),
        )

        confidence = {
            SufficiencyStatus.INSUFFICIENT: 0.0,
            SufficiencyStatus.PARTIAL: 0.5,
            SufficiencyStatus.SUFFICIENT: 0.9,
        }[status]

        reasoning = EvidenceSufficiencyEvaluator._build_reasoning(
            status=status,
            supporting_count=len(supporting),
            reliable_supporting_count=len(reliable_supporting),
            contradicting_count=len(contradicting),
            missing_evidence_ids=missing_evidence_ids,
            missing_sources=missing_sources,
        )

        assessment = EvidenceSufficiency(
            hypothesis_id=hypothesis.hypothesis_id,
            status=status,
            evidence_ids=sorted(referenced_ids),
            supporting_evidence_count=len(supporting),
            contradicting_evidence_count=len(contradicting),
            reliable_evidence_count=len(reliable_supporting),
            missing_sources=missing_sources,
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                "missing_evidence_ids": missing_evidence_ids,
                "required_sources": sorted(
                    {source.strip().lower() for source in required_sources or []}
                ),
            },
        )

        assessment.validate()

        return assessment

    @staticmethod
    def _determine_status(
        supporting_count: int,
        reliable_supporting_count: int,
        contradicting_count: int,
        missing_evidence_count: int,
        missing_sources_count: int,
    ) -> SufficiencyStatus:
        """Apply deterministic sufficiency rules."""
        if supporting_count == 0:
            return SufficiencyStatus.INSUFFICIENT

        if reliable_supporting_count == 0:
            return SufficiencyStatus.INSUFFICIENT

        if (
            missing_evidence_count > 0
            or contradicting_count > 0
            or missing_sources_count > 0
        ):
            return SufficiencyStatus.PARTIAL

        if supporting_count >= 2 and reliable_supporting_count >= 2:
            return SufficiencyStatus.SUFFICIENT

        return SufficiencyStatus.PARTIAL

    @staticmethod
    def _missing_sources(
        evidence_items: list[Evidence],
        required_sources: list[str],
    ) -> list[str]:
        """Return required evidence sources that are not represented."""
        available_sources = {
            evidence.source.strip().lower()
            for evidence in evidence_items
            if evidence.source.strip()
        }

        normalized_required = {
            source.strip().lower()
            for source in required_sources
            if source.strip()
        }

        return sorted(normalized_required - available_sources)

    @staticmethod
    def _build_reasoning(
        status: SufficiencyStatus,
        supporting_count: int,
        reliable_supporting_count: int,
        contradicting_count: int,
        missing_evidence_ids: list[str],
        missing_sources: list[str],
    ) -> str:
        """Create an explainable assessment summary."""
        if status == SufficiencyStatus.INSUFFICIENT:
            return (
                "Evidence is insufficient because there is not enough "
                "reliable supporting evidence for the hypothesis."
            )

        if status == SufficiencyStatus.PARTIAL:
            reasons = [
                f"{supporting_count} supporting evidence item(s)",
                f"{reliable_supporting_count} reliable supporting evidence item(s)",
            ]

            if contradicting_count:
                reasons.append(
                    f"{contradicting_count} contradicting evidence item(s)"
                )

            if missing_evidence_ids:
                reasons.append(
                    "missing referenced evidence: "
                    + ", ".join(missing_evidence_ids)
                )

            if missing_sources:
                reasons.append(
                    "missing required sources: "
                    + ", ".join(missing_sources)
                )

            return (
                "Evidence is partially sufficient because "
                + "; ".join(reasons)
                + "."
            )

        return (
            "Evidence is sufficient because at least two supporting "
            "evidence items are available, at least two are reliable, "
            "and no contradictions or required-source gaps were identified."
        )
