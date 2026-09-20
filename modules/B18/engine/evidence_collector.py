from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from engine.evidence_model import Evidence


class EvidenceCollector(ABC):
    """Interface for controlled B18 evidence collectors."""

    @property
    @abstractmethod
    def source(self) -> str:
        """Return the evidence source identifier."""
        raise NotImplementedError

    @abstractmethod
    def collect(self, query: dict[str, Any]) -> list[Evidence]:
        """Collect evidence using a controlled query."""
        raise NotImplementedError


class StaticEvidenceCollector(EvidenceCollector):
    """Test collector that returns predefined evidence."""

    def __init__(self, evidence: list[Evidence]) -> None:
        self._evidence = evidence

    @property
    def source(self) -> str:
        return "static"

    def collect(self, query: dict[str, Any]) -> list[Evidence]:
        """Return predefined evidence.

        The query is accepted to preserve the collector interface,
        but no external system is contacted.
        """
        return list(self._evidence)
