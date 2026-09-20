from __future__ import annotations

from collections.abc import Iterable

from engine.correlation_engine import CorrelationEngine
from engine.evidence_model import Evidence
from engine.evidence_normalizer import EvidenceNormalizer
from engine.evidence_sufficiency_evaluator import EvidenceSufficiencyEvaluator
from engine.hypothesis_generator import HypothesisGenerator
from engine.incident_model import Incident
from engine.investigation_model import InvestigationResult
from engine.rca_engine import RCAEngine
from engine.timeline_builder import TimelineBuilder


class InvestigationEngine:
    """
    B18.9 orchestration layer.

    Coordinates the existing B18 investigation components without
    duplicating their domain logic.
    """

    def __init__(
        self,
        correlation_engine: CorrelationEngine | None = None,
        required_sources: list[str] | None = None,
    ) -> None:
        self.correlation_engine = correlation_engine or CorrelationEngine()
        self.required_sources = list(required_sources or [])

    def investigate(
        self,
        incident: Incident,
        evidence_items: Iterable[Evidence],
    ) -> InvestigationResult:
        incident.validate()

        evidence = list(evidence_items)

        for item in evidence:
            item.validate()

        normalized_evidence = self._normalize_evidence(evidence)

        timeline = TimelineBuilder.build(normalized_evidence)

        correlations = self.correlation_engine.correlate(normalized_evidence)

        hypotheses = []

        for correlation in correlations:
            generated = HypothesisGenerator.generate(
                correlation,
                normalized_evidence,
            )
            hypotheses.extend(generated)

        sufficiency = []
        rca = []

        for hypothesis in hypotheses:
            assessment = EvidenceSufficiencyEvaluator.evaluate(
                hypothesis=hypothesis,
                evidence_items=normalized_evidence,
                required_sources=self.required_sources,
            )

            sufficiency.append(assessment)

            analysis = RCAEngine.analyze(
                incident_id=incident.incident_id,
                hypothesis=hypothesis,
                sufficiency=assessment,
                evidence=normalized_evidence,
            )

            rca.append(analysis)

        result = InvestigationResult(
            incident=incident,
            evidence=normalized_evidence,
            timeline=timeline,
            correlations=correlations,
            hypotheses=hypotheses,
            sufficiency=sufficiency,
            rca=rca,
            metadata={
                "engine": "B18.9",
                "required_sources": list(self.required_sources),
            },
        )

        result.validate()

        return result

    @staticmethod
    def _normalize_evidence(evidence: list[Evidence]) -> list[Evidence]:
        normalized = []

        for item in evidence:
            normalized.append(EvidenceNormalizer.normalize(item))

        return normalized
