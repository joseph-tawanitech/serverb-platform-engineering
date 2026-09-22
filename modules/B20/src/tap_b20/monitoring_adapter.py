"""Adapters connecting B20 security monitoring to security evidence."""

from .evidence import SecurityEvidence
from .evidence_normalizer import normalize_security_observation
from .monitoring import SecurityObservation


def observation_to_evidence(
    observation: SecurityObservation,
    *,
    policy_reference: str | None = None,
    risk: str | None = None,
) -> SecurityEvidence:
    """Convert a monitoring observation into normalized security evidence."""

    return normalize_security_observation(
        evidence_id=observation.observation_id,
        source=observation.source,
        environment=observation.environment,
        asset=observation.asset,
        observation=observation.observation,
        category=observation.category,
        severity=observation.severity,
        evidence=observation.data,
        policy_reference=policy_reference,
        risk=risk,
        provenance={
            "monitoring_source": observation.source,
            "observation_id": observation.observation_id,
        },
    )
