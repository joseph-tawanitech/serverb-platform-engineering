import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator


SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "evidence.schema.json"
)


def load_schema():
    return json.loads(SCHEMA_PATH.read_text())


def build_valid_evidence():
    timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "evidence_id": "EV-B18-0001",
        "source": "prometheus",
        "evidence_type": "metric",
        "collected_at": timestamp,
        "observation_time": timestamp,
        "resource": "deployment/api",
        "content": {
            "metric": "http_requests_total",
            "value": 1250
        },
        "location": None,
        "reliability": "high",
        "status": "collected",
        "metadata": {}
    }


def test_valid_evidence_schema():
    schema = load_schema()
    validator = Draft202012Validator(schema)

    validator.validate(build_valid_evidence())


def test_invalid_evidence_type_rejected():
    schema = load_schema()
    validator = Draft202012Validator(schema)

    evidence = build_valid_evidence()
    evidence["evidence_type"] = "invalid_type"

    errors = list(validator.iter_errors(evidence))

    assert errors
    assert any(error.path[-1] == "evidence_type" for error in errors)


def test_invalid_reliability_rejected():
    schema = load_schema()
    validator = Draft202012Validator(schema)

    evidence = build_valid_evidence()
    evidence["reliability"] = "invalid_reliability"

    errors = list(validator.iter_errors(evidence))

    assert errors
    assert any(error.path[-1] == "reliability" for error in errors)


def test_invalid_status_rejected():
    schema = load_schema()
    validator = Draft202012Validator(schema)

    evidence = build_valid_evidence()
    evidence["status"] = "invalid_status"

    errors = list(validator.iter_errors(evidence))

    assert errors
    assert any(error.path[-1] == "status" for error in errors)
