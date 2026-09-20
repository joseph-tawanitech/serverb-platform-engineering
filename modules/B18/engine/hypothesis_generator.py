from __future__ import annotations

from engine.correlation_model import CorrelationGroup
from engine.evidence_model import Evidence
from engine.hypothesis_model import Hypothesis


class HypothesisGenerator:
    """Generate deterministic hypotheses from correlated evidence."""

    @staticmethod
    def generate(
        correlation_group: CorrelationGroup,
        evidence_items: list[Evidence],
    ) -> list[Hypothesis]:
        """Generate possible explanations for a correlation group."""
        correlation_group.validate()

        evidence_by_id = {
            evidence.evidence_id: evidence
            for evidence in evidence_items
        }

        group_evidence = [
            evidence_by_id[evidence_id]
            for evidence_id in correlation_group.evidence_ids
            if evidence_id in evidence_by_id
        ]

        if not group_evidence:
            return []

        resources = sorted(
            {
                evidence.resource
                for evidence in group_evidence
                if evidence.resource
            }
        )

        supporting_ids = [
            evidence.evidence_id
            for evidence in group_evidence
        ]

        resource_description = (
            ", ".join(resources)
            if resources
            else "the affected resources"
        )

        hypothesis = Hypothesis(
            hypothesis_id=f"HYP-{correlation_group.correlation_id}",
            statement=(
                "The correlated evidence indicates that a common "
                f"condition may have affected {resource_description}."
            ),
            supporting_evidence_ids=supporting_ids,
            affected_resources=resources,
            reasoning=(
                "The hypothesis was generated because the evidence "
                "items belong to the same correlation group. "
                "This establishes a possible relationship, not causation."
            ),
        )

        hypothesis.validate()

        return [hypothesis]
