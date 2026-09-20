from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.correlation_model import CorrelationGroup
from engine.evidence_model import Evidence
from engine.evidence_sufficiency_model import EvidenceSufficiency
from engine.hypothesis_model import Hypothesis
from engine.incident_model import Incident
from engine.rca_model import RootCauseAnalysis
from engine.timeline_model import TimelineEvent


@dataclass
class InvestigationResult:
    """Complete structured output of a B18 incident investigation."""

    incident: Incident
    evidence: list[Evidence] = field(default_factory=list)
    timeline: list[TimelineEvent] = field(default_factory=list)
    correlations: list[CorrelationGroup] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    sufficiency: list[EvidenceSufficiency] = field(default_factory=list)
    rca: list[RootCauseAnalysis] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate the structural integrity of the investigation result."""

        self.incident.validate()

        if not self.incident.incident_id.strip():
            raise ValueError("incident_id must not be empty")

        for evidence in self.evidence:
            evidence.validate()

        for event in self.timeline:
            event.validate()

        for correlation in self.correlations:
            correlation.validate()

        for hypothesis in self.hypotheses:
            hypothesis.validate()

        for assessment in self.sufficiency:
            assessment.validate()

        for analysis in self.rca:
            analysis.validate()

        evidence_ids = [item.evidence_id for item in self.evidence]

        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("evidence IDs must be unique")

        hypothesis_ids = [item.hypothesis_id for item in self.hypotheses]

        if len(set(hypothesis_ids)) != len(hypothesis_ids):
            raise ValueError("hypothesis IDs must be unique")

        sufficiency_ids = [
            item.hypothesis_id
            for item in self.sufficiency
        ]

        if len(set(sufficiency_ids)) != len(sufficiency_ids):
            raise ValueError("sufficiency hypothesis IDs must be unique")

        rca_hypothesis_ids = [
            item.hypothesis_id
            for item in self.rca
            if item.hypothesis_id is not None
        ]

        if len(set(rca_hypothesis_ids)) != len(rca_hypothesis_ids):
            raise ValueError("RCA hypothesis IDs must be unique")

        for analysis in self.rca:
            if analysis.incident_id != self.incident.incident_id:
                raise ValueError(
                    "RCA incident_id must match investigation incident_id"
                )
