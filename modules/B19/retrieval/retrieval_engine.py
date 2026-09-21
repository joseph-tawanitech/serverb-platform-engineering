from __future__ import annotations

from dataclasses import dataclass, field

from ..indexing.evidence_index import (
    EvidenceIndex,
    EvidenceIndexEntry,
)


@dataclass(frozen=True)
class RetrievalQuery:
    """
    B19.8 structured retrieval request.

    Defines what knowledge the retrieval engine should look for.

    This is a retrieval request only. It does not grant authority
    to execute infrastructure actions.
    """

    query_id: str
    text: str
    resource: str | None = None
    knowledge_types: tuple[str, ...] = ()
    source_types: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    incident_id: str | None = None
    limit: int = 5

    def validate(self) -> None:
        if not self.query_id.strip():
            raise ValueError("query_id must not be empty")

        if not self.text.strip():
            raise ValueError("text must not be empty")

        if self.resource is not None and not self.resource.strip():
            raise ValueError(
                "resource must not be empty when provided"
            )

        if self.incident_id is not None and not self.incident_id.strip():
            raise ValueError(
                "incident_id must not be empty when provided"
            )

        if self.limit < 1:
            raise ValueError("limit must be greater than zero")

        if len(set(self.knowledge_types)) != len(self.knowledge_types):
            raise ValueError("knowledge_types must be unique")

        if len(set(self.source_types)) != len(self.source_types):
            raise ValueError("source_types must be unique")

        if len(set(self.tags)) != len(self.tags):
            raise ValueError("tags must be unique")


@dataclass(frozen=True)
class RetrievalCandidate:
    """
    B19.8 internal retrieval candidate.
    """

    document_id: str
    entry: EvidenceIndexEntry
    matched_fields: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RetrievalResult:
    """
    B19.8 ranked retrieval result.

    Retrieval results are informational. They do not grant
    execution or authorization authority.
    """

    document_id: str
    title: str
    score: int
    score_breakdown: dict[str, int]
    knowledge_type: str
    source_type: str
    resource: str | None
    tags: tuple[str, ...]
    source: str
    provenance_reference: str | None
    provenance_version: str | None
    provenance_checksum: str | None
    provenance_collected_at: object
    provenance_collector: str


class RetrievalEngine:
    """
    B19.8 deterministic retrieval and ranking engine.

    Uses the B19.4 EvidenceIndex as the candidate source.

    This engine:
    - reads indexed knowledge metadata
    - filters candidates
    - ranks candidates deterministically
    - preserves provenance

    This engine does not:
    - perform embeddings
    - perform vector search
    - invoke AI models
    - authorize actions
    - execute infrastructure changes
    """

    RESOURCE_SCORE = 30
    KNOWLEDGE_TYPE_SCORE = 20
    SOURCE_TYPE_SCORE = 15
    TAG_SCORE = 15
    TITLE_SCORE = 10

    def __init__(self, evidence_index: EvidenceIndex) -> None:
        if not isinstance(evidence_index, EvidenceIndex):
            raise TypeError(
                "evidence_index must be an EvidenceIndex"
            )

        self._evidence_index = evidence_index

    def retrieve(
        self,
        query: RetrievalQuery,
    ) -> list[RetrievalResult]:
        """
        Retrieve and rank knowledge for a structured query.
        """

        if not isinstance(query, RetrievalQuery):
            raise TypeError(
                "query must be a RetrievalQuery"
            )

        query.validate()

        candidates = self._discover_candidates(query)

        results = [
            self._rank_candidate(candidate, query)
            for candidate in candidates
        ]

        results.sort(
            key=lambda result: (
                -result.score,
                result.document_id,
            )
        )

        return results[: query.limit]

    def _discover_candidates(
        self,
        query: RetrievalQuery,
    ) -> list[RetrievalCandidate]:
        candidates: list[RetrievalCandidate] = []

        query_terms = self._tokenize(query.text)

        for entry in self._evidence_index.list_entries():
            matched_fields: list[str] = []

            if query.resource is not None:
                if entry.resource != query.resource:
                    continue

                matched_fields.append("resource")

            if query.knowledge_types:
                if entry.knowledge_type not in query.knowledge_types:
                    continue

                matched_fields.append("knowledge_type")

            if query.source_types:
                if entry.source_type not in query.source_types:
                    continue

                matched_fields.append("source_type")

            if query.tags:
                if not set(query.tags).intersection(entry.tags):
                    continue

                matched_fields.append("tags")

            if query.incident_id is not None:
                if entry.incident_id != query.incident_id:
                    continue

                matched_fields.append("incident_id")

            title_terms = self._tokenize(entry.title)

            if query_terms.intersection(title_terms):
                matched_fields.append("title")

            if not matched_fields and query_terms:
                continue

            candidates.append(
                RetrievalCandidate(
                    document_id=entry.document_id,
                    entry=entry,
                    matched_fields=tuple(matched_fields),
                )
            )

        return candidates

    def _rank_candidate(
        self,
        candidate: RetrievalCandidate,
        query: RetrievalQuery,
    ) -> RetrievalResult:
        entry = candidate.entry
        breakdown: dict[str, int] = {}

        if query.resource is not None and entry.resource == query.resource:
            breakdown["resource_match"] = self.RESOURCE_SCORE

        if (
            query.knowledge_types
            and entry.knowledge_type in query.knowledge_types
        ):
            breakdown["knowledge_type_match"] = (
                self.KNOWLEDGE_TYPE_SCORE
            )

        if (
            query.source_types
            and entry.source_type in query.source_types
        ):
            breakdown["source_type_match"] = (
                self.SOURCE_TYPE_SCORE
            )

        if query.tags:
            matching_tags = set(query.tags).intersection(entry.tags)

            if matching_tags:
                breakdown["tag_match"] = self.TAG_SCORE

        query_terms = self._tokenize(query.text)
        title_terms = self._tokenize(entry.title)

        if query_terms.intersection(title_terms):
            breakdown["title_match"] = self.TITLE_SCORE

        score = sum(breakdown.values())

        return RetrievalResult(
            document_id=entry.document_id,
            title=entry.title,
            score=score,
            score_breakdown=breakdown,
            knowledge_type=entry.knowledge_type,
            source_type=entry.source_type,
            resource=entry.resource,
            tags=entry.tags,
            source=entry.source,
            provenance_reference=entry.provenance_reference,
            provenance_version=entry.provenance_version,
            provenance_checksum=entry.provenance_checksum,
            provenance_collected_at=entry.provenance_collected_at,
            provenance_collector=entry.provenance_collector,
        )

    @staticmethod
    def _tokenize(value: str) -> set[str]:
        return {
            term.strip(".,:;!?()[]{}\"'").lower()
            for term in value.split()
            if term.strip(".,:;!?()[]{}\"'")
        }
