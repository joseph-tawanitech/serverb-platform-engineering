from __future__ import annotations

from datetime import timedelta
from itertools import combinations
from typing import Iterable

from engine.evidence_model import Evidence
from engine.correlation_model import CorrelationGroup, CorrelationLink


class CorrelationEngine:
    """Correlate evidence using deterministic, explainable rules."""

    def __init__(self, time_window_seconds: int = 300):
        if time_window_seconds < 0:
            raise ValueError("time_window_seconds must not be negative")

        self.time_window = timedelta(seconds=time_window_seconds)

    def correlate(self, evidence_items: Iterable[Evidence]) -> list[CorrelationGroup]:
        """Build correlation groups from evidence relationships."""
        evidence = list(evidence_items)

        for item in evidence:
            item.validate()

        links: list[CorrelationLink] = []

        for first, second in combinations(evidence, 2):
            link = self._correlate_pair(first, second)

            if link is not None:
                links.append(link)

        return self._build_groups(links)

    def _correlate_pair(
        self,
        first: Evidence,
        second: Evidence,
    ) -> CorrelationLink | None:
        """Determine whether two evidence items are related."""
        same_resource = (
            first.resource is not None
            and second.resource is not None
            and first.resource.strip().lower() == second.resource.strip().lower()
        )

        first_time = first.observation_time or first.collected_at
        second_time = second.observation_time or second.collected_at

        within_time_window = (
            abs(first_time - second_time) <= self.time_window
        )

        if same_resource and within_time_window:
            return CorrelationLink(
                source_evidence_id=first.evidence_id,
                related_evidence_id=second.evidence_id,
                reason="Same resource within the configured time window",
                confidence=0.95,
                metadata={
                    "same_resource": True,
                    "within_time_window": True,
                },
            )

        if same_resource:
            return CorrelationLink(
                source_evidence_id=first.evidence_id,
                related_evidence_id=second.evidence_id,
                reason="Same resource",
                confidence=0.80,
                metadata={
                    "same_resource": True,
                    "within_time_window": False,
                },
            )

        return None

    @staticmethod
    def _build_groups(
        links: list[CorrelationLink],
    ) -> list[CorrelationGroup]:
        """Build connected evidence groups from correlation links."""
        groups: list[set[str]] = []

        for link in links:
            matching_groups = [
                group
                for group in groups
                if link.source_evidence_id in group
                or link.related_evidence_id in group
            ]

            if not matching_groups:
                groups.append(
                    {
                        link.source_evidence_id,
                        link.related_evidence_id,
                    }
                )
                continue

            merged = {
                link.source_evidence_id,
                link.related_evidence_id,
            }

            for group in matching_groups:
                merged.update(group)
                groups.remove(group)

            groups.append(merged)

        result: list[CorrelationGroup] = []

        for index, evidence_ids in enumerate(groups, start=1):
            group_links = [
                link
                for link in links
                if link.source_evidence_id in evidence_ids
                or link.related_evidence_id in evidence_ids
            ]

            result.append(
                CorrelationGroup(
                    correlation_id=f"CORR-B18-{index:04d}",
                    evidence_ids=sorted(evidence_ids),
                    links=group_links,
                )
            )

        return result
