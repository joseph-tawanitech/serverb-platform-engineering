import json
from pathlib import Path

from jsonschema import Draft202012Validator


SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "recommendation.schema.json"
)


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def valid_sample() -> dict:
    return {
        "incident": {
            "id": "INC-B17-TEST-001",
            "summary": "Read-only server health investigation",
            "status": "investigating",
        },
        "asset": {
            "name": "server-b-tap",
            "id": None,
            "type": "server",
            "environment": "lab",
            "hostname": "server-b-tap",
            "ip": None,
        },
        "observed_state": "System health evidence was supplied for investigation.",
        "evidence": [
            {
                "source": "test_fixture",
                "reference": "B17-TEST-EVIDENCE-001",
                "observation": "CPU, memory, disk, and service state evidence supplied.",
                "timestamp": None,
                "reliability": "high",
            }
        ],
        "timeline": [
            {
                "timestamp": "2026-09-19T00:00:00Z",
                "event": "Investigation evidence received.",
                "source": "test_fixture",
            }
        ],
        "dependencies": [],
        "findings": [
            {
                "finding": "The supplied evidence is sufficient for a preliminary assessment.",
                "basis": "Evidence was explicitly provided by the test fixture.",
                "confidence": "high",
            }
        ],
        "hypotheses": [
            {
                "hypothesis": "No confirmed infrastructure fault can be established from this fixture alone.",
                "supporting_evidence": [
                    "The fixture contains no confirmed fault indication."
                ],
                "contradicting_evidence": [],
                "missing_evidence": [
                    "Live service and metric evidence."
                ],
                "confidence": "medium",
            }
        ],
        "confidence": "medium",
        "impact": {
            "availability": "Unknown",
            "performance": "Unknown",
            "data": "No impact established.",
            "security": "No impact established.",
            "customer": "Unknown",
            "dependencies": "Unknown",
        },
        "risk": {
            "level": "LOW",
            "basis": "Read-only investigation with no execution.",
            "reversibility": "No infrastructure change proposed.",
            "blast_radius": "None from investigation-only activity.",
        },
        "recommendation": {
            "summary": "Collect additional evidence before considering remediation.",
            "actions": [
                "Perform read-only evidence collection."
            ],
            "rationale": "The available evidence does not establish a confirmed root cause.",
        },
        "backup_requirement": {
            "required": False,
            "status": "not_required",
            "reason": "No infrastructure change is proposed.",
        },
        "authorization_requirement": {
            "required": False,
            "level": "NONE",
            "reason": "This fixture represents analysis only.",
        },
        "missing_evidence": [
            "Live service health evidence.",
            "Current resource metrics.",
        ],
        "verification_plan": [
            {
                "criterion": "Evidence collection completes without infrastructure modification.",
                "method": "Review the recorded read-only evidence request.",
                "expected_result": "No execution or configuration change occurs.",
            }
        ],
    }


def test_valid_output_contract():
    schema = load_schema()
    instance = valid_sample()

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda error: error.path)

    assert not errors, "\n".join(
        f"{list(error.path)}: {error.message}" for error in errors
    )


if __name__ == "__main__":
    test_valid_output_contract()
    print("B17 output contract: PASS")
