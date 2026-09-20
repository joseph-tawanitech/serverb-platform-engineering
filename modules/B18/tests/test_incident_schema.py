import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator


SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "incident.schema.json"
)


def build_valid_incident():
    return {
        "incident_id": "INC-B18-0001",
        "title": "Kubernetes workload unavailable",
        "severity": "high",
        "status": "detected",
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "source": "kubernetes",
        "affected_resources": [
            "deployment/api"
        ],
        "symptoms": [
            "API workload unavailable"
        ],
        "evidence": [
            {
                "evidence_id": "EV-B18-0001",
                "source": "kubernetes",
                "description": "Deployment unavailable",
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "location": "cluster",
                "metadata": {}
            }
        ],
        "timeline": [],
        "impact": [],
        "hypotheses": [],
        "root_cause": None,
        "recommendations": [],
        "confidence": None,
        "metadata": {}
    }


def test_valid_incident_matches_schema():
    schema = json.loads(SCHEMA_PATH.read_text())
    incident = build_valid_incident()

    validator = Draft202012Validator(schema)

    errors = list(validator.iter_errors(incident))

    assert errors == []
