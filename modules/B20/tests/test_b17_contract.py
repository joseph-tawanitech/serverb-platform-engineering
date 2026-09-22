from tap_b20.b17_contract import (
    B17ContractError,
    validate_b17_result,
)


def valid_b17_result() -> dict:
    return {
        "incident": {
            "id": "INC-B20-TEST-001",
            "summary": "Security investigation test",
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
        "observed_state": "Security evidence supplied.",
        "evidence": [
            {
                "source": "b20_test",
                "reference": "B20-EVIDENCE-001",
                "observation": "Read-only security evidence supplied.",
                "timestamp": None,
                "reliability": "high",
            }
        ],
        "timeline": [],
        "dependencies": [],
        "findings": [],
        "hypotheses": [],
        "confidence": "medium",
        "impact": {
            "availability": "Unknown",
            "performance": "Unknown",
            "data": "Unknown",
            "security": "Unknown",
            "customer": "Unknown",
            "dependencies": "Unknown",
        },
        "risk": {
            "level": "LOW",
            "basis": "Investigation only.",
            "reversibility": "No change proposed.",
            "blast_radius": "None.",
        },
        "recommendation": {
            "summary": "Collect additional evidence.",
            "actions": ["Perform read-only evidence collection."],
            "rationale": "Evidence is insufficient for remediation.",
        },
        "backup_requirement": {
            "required": False,
            "status": "not_required",
            "reason": "No change proposed.",
        },
        "authorization_requirement": {
            "required": False,
            "level": "NONE",
            "reason": "Investigation only.",
        },
        "missing_evidence": [],
        "verification_plan": [],
    }


def test_valid_b17_result_is_accepted():
    result = valid_b17_result()

    validated = validate_b17_result(result)

    assert validated == result


def test_invalid_b17_result_is_rejected():
    result = valid_b17_result()
    del result["risk"]

    try:
        validate_b17_result(result)
    except B17ContractError as exc:
        assert "risk" in str(exc)
    else:
        raise AssertionError("Invalid B17 result was accepted")
