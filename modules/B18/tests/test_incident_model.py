from datetime import datetime, timezone

import pytest

from engine.incident_model import (
    EvidenceReference,
    Incident,
    IncidentSeverity,
    IncidentStatus,
)


def build_valid_incident() -> Incident:
    return Incident(
        incident_id="INC-B18-0001",
        title="Kubernetes workload unavailable",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        detected_at=datetime.now(timezone.utc),
        source="kubernetes",
        affected_resources=["deployment/api"],
        symptoms=["API workload unavailable"],
        evidence=[
            EvidenceReference(
                evidence_id="EV-B18-0001",
                source="kubernetes",
                description="Deployment has unavailable replicas",
            )
        ],
    )


def test_valid_incident():
    incident = build_valid_incident()

    incident.validate()

    assert incident.incident_id == "INC-B18-0001"
    assert incident.severity == IncidentSeverity.HIGH
    assert incident.status == IncidentStatus.DETECTED


def test_empty_incident_id_rejected():
    incident = build_valid_incident()
    incident.incident_id = ""

    with pytest.raises(ValueError, match="incident_id"):
        incident.validate()


def test_empty_title_rejected():
    incident = build_valid_incident()
    incident.title = ""

    with pytest.raises(ValueError, match="title"):
        incident.validate()


def test_empty_source_rejected():
    incident = build_valid_incident()
    incident.source = ""

    with pytest.raises(ValueError, match="source"):
        incident.validate()


def test_invalid_confidence_rejected():
    incident = build_valid_incident()
    incident.confidence = 1.5

    with pytest.raises(ValueError, match="confidence"):
        incident.validate()
