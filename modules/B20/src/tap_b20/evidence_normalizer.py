"""Normalization of security observations into TAP B20 evidence."""

from typing import Any

from .evidence import SecurityEvidence
from .models import SecuritySeverity


def normalize_security_observation(
    *,
    evidence_id: str,
    source: str,
    environment: str,
    asset: str,
    observation: str,
    category: str,
    severity: SecuritySeverity,
    evidence: dict[str, Any] | None = None,
    policy_reference: str | None = None,
    risk: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> SecurityEvidence:
    """Convert a raw security observation into normalized TAP evidence."""

    return SecurityEvidence(
        evidence_id=evidence_id,
        source=source,
        environment=environment,
        asset=asset,
        observation=observation,
        category=category,
        severity=severity,
        evidence=evidence or {},
        policy_reference=policy_reference,
        risk=risk,
        provenance=provenance or {},
    )
