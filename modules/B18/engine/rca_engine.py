from __future__ import annotations

from engine.evidence_model import Evidence
from engine.evidence_sufficiency_model import (
    EvidenceSufficiency,
    SufficiencyStatus,
)
from engine.hypothesis_model import Hypothesis
from engine.rca_model import RCAStatus, RootCauseAnalysis


class RCAEngine:
    """Produce a deterministic RCA conclusion from investigation results."""

    @staticmethod
    def analyze(
        incident_id: str,
        hypothesis: Hypothesis,
        sufficiency: EvidenceSufficiency,
        evidence: list[Evidence],
    ) -> RootCauseAnalysis:
        """Evaluate a hypothesis and produce a structured RCA."""

        if not incident_id.strip():
            raise ValueError("incident_id must not be empty")

        hypothesis.validate()
        sufficiency.validate()

        evidence_by_id = {
            item.evidence_id: item
            for item in evidence
        }

        supporting_ids = list(hypothesis.supporting_evidence_ids)
        contradicting_ids = list(hypothesis.contradicting_evidence_ids)

        affected_resources = list(hypothesis.affected_resources)

        limitations = list(sufficiency.missing_sources)

        missing_evidence_ids = [
            evidence_id
            for evidence_id in (
                supporting_ids + contradicting_ids
            )
            if evidence_id not in evidence_by_id
        ]

        if missing_evidence_ids:
            limitations.append(
                "Referenced evidence is missing from the supplied evidence set"
            )

        limitations = list(dict.fromkeys(limitations))

        root_cause_location = RCAEngine._determine_location(
            hypothesis,
            evidence_by_id,
        )

        if sufficiency.status == SufficiencyStatus.INSUFFICIENT:
            rca = RootCauseAnalysis(
                incident_id=incident_id,
                status=RCAStatus.NOT_ESTABLISHED,
                hypothesis_id=hypothesis.hypothesis_id,
                supporting_evidence_ids=supporting_ids,
                contradicting_evidence_ids=contradicting_ids,
                affected_resources=affected_resources,
                root_cause_location=root_cause_location,
                confidence=0.0,
                reasoning=(
                    "The available evidence is insufficient to establish "
                    "a root cause."
                ),
                limitations=limitations,
            )

        elif contradicting_ids:
            rca = RootCauseAnalysis(
                incident_id=incident_id,
                status=RCAStatus.REJECTED,
                hypothesis_id=hypothesis.hypothesis_id,
                supporting_evidence_ids=supporting_ids,
                contradicting_evidence_ids=contradicting_ids,
                affected_resources=affected_resources,
                root_cause_location=root_cause_location,
                confidence=0.0,
                reasoning=(
                    "The hypothesis has contradicting evidence and therefore "
                    "cannot be accepted as the root cause."
                ),
                limitations=limitations,
            )

        elif sufficiency.status == SufficiencyStatus.PARTIAL:
            rca = RootCauseAnalysis(
                incident_id=incident_id,
                status=RCAStatus.PROVISIONAL,
                root_cause=hypothesis.statement,
                hypothesis_id=hypothesis.hypothesis_id,
                supporting_evidence_ids=supporting_ids,
                contradicting_evidence_ids=contradicting_ids,
                affected_resources=affected_resources,
                root_cause_location=root_cause_location,
                confidence=sufficiency.confidence,
                reasoning=(
                    "The available evidence supports the hypothesis, "
                    "but evidence gaps remain."
                ),
                limitations=limitations,
            )

        else:
            rca = RootCauseAnalysis(
                incident_id=incident_id,
                status=RCAStatus.CONFIRMED,
                root_cause=hypothesis.statement,
                hypothesis_id=hypothesis.hypothesis_id,
                supporting_evidence_ids=supporting_ids,
                contradicting_evidence_ids=contradicting_ids,
                affected_resources=affected_resources,
                root_cause_location=root_cause_location,
                confidence=sufficiency.confidence,
                reasoning=(
                    "The hypothesis satisfies the configured evidence "
                    "sufficiency criteria and has no contradicting evidence."
                ),
                limitations=limitations,
            )

        rca.validate()
        return rca

    @staticmethod
    def _determine_location(
        hypothesis: Hypothesis,
        evidence_by_id: dict[str, Evidence],
    ) -> str | None:
        """Return a root-cause location only when evidence supports one."""

        resources = []

        for evidence_id in hypothesis.supporting_evidence_ids:
            evidence = evidence_by_id.get(evidence_id)

            if evidence is not None and evidence.resource:
                resources.append(evidence.resource)

        unique_resources = list(dict.fromkeys(resources))

        if len(unique_resources) == 1:
            return unique_resources[0]

        return None
