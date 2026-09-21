from datetime import datetime, timezone

import pytest

from modules.B19.ai.ai_context_contract import (
    AIContextContract,
    AIContextRequest,
)
from modules.B19.context.context_assembler import RAGContext


def make_context() -> RAGContext:
    return RAGContext(
        context_id="CTX-001",
        query_id="QUERY-001",
        query_text="investigate nginx failure",
        items=(),
        created_at=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        max_items=5,
    )


def test_create_request_preserves_identity_and_context():
    context = make_context()

    request = AIContextContract().create_request(
        request_id="AICTX-001",
        investigation_id="INV-001",
        purpose="AI incident investigation",
        context=context,
        created_at=datetime(2026, 9, 22, 12, 1, tzinfo=timezone.utc),
    )

    assert request.request_id == "AICTX-001"
    assert request.investigation_id == "INV-001"
    assert request.purpose == "AI incident investigation"
    assert request.context is context
    assert request.context.context_id == "CTX-001"
    assert request.context.query_id == "QUERY-001"


def test_create_request_generates_timestamp_when_not_provided():
    context = make_context()

    request = AIContextContract().create_request(
        request_id="AICTX-002",
        investigation_id="INV-002",
        purpose="RCA investigation",
        context=context,
    )

    assert isinstance(request.created_at, datetime)
    assert request.created_at.tzinfo is not None


def test_request_validation_rejects_empty_request_id():
    request = AIContextRequest(
        request_id="",
        investigation_id="INV-001",
        purpose="investigation",
        context=make_context(),
        created_at=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError, match="request_id"):
        request.validate()


def test_request_validation_rejects_empty_investigation_id():
    request = AIContextRequest(
        request_id="AICTX-003",
        investigation_id="",
        purpose="investigation",
        context=make_context(),
        created_at=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError, match="investigation_id"):
        request.validate()


def test_request_validation_rejects_empty_purpose():
    request = AIContextRequest(
        request_id="AICTX-004",
        investigation_id="INV-004",
        purpose="",
        context=make_context(),
        created_at=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError, match="purpose"):
        request.validate()


def test_request_validation_rejects_invalid_context_type():
    request = AIContextRequest(
        request_id="AICTX-005",
        investigation_id="INV-005",
        purpose="investigation",
        context="invalid-context",
        created_at=datetime.now(timezone.utc),
    )

    with pytest.raises(TypeError, match="RAGContext"):
        request.validate()


def test_request_validation_rejects_invalid_created_at_type():
    request = AIContextRequest(
        request_id="AICTX-006",
        investigation_id="INV-006",
        purpose="investigation",
        context=make_context(),
        created_at="2026-09-22T12:00:00Z",
    )

    with pytest.raises(TypeError, match="datetime"):
        request.validate()


def test_to_dict_preserves_contract_structure():
    request = AIContextContract().create_request(
        request_id="AICTX-007",
        investigation_id="INV-007",
        purpose="incident investigation",
        context=make_context(),
        created_at=datetime(2026, 9, 22, 12, 2, tzinfo=timezone.utc),
    )

    payload = request.to_dict()

    assert payload["request_id"] == "AICTX-007"
    assert payload["investigation_id"] == "INV-007"
    assert payload["purpose"] == "incident investigation"
    assert payload["created_at"] == "2026-09-22T12:02:00+00:00"
    assert payload["context"]["context_id"] == "CTX-001"
    assert payload["context"]["query_id"] == "QUERY-001"


def test_to_json_is_deterministic():
    request = AIContextContract().create_request(
        request_id="AICTX-008",
        investigation_id="INV-008",
        purpose="deterministic context test",
        context=make_context(),
        created_at=datetime(2026, 9, 22, 12, 3, tzinfo=timezone.utc),
    )

    first = request.to_json()
    second = request.to_json()

    assert first == second


def test_to_json_is_valid_json():
    import json

    request = AIContextContract().create_request(
        request_id="AICTX-009",
        investigation_id="INV-009",
        purpose="serialization test",
        context=make_context(),
        created_at=datetime(2026, 9, 22, 12, 4, tzinfo=timezone.utc),
    )

    payload = json.loads(request.to_json())

    assert payload["request_id"] == "AICTX-009"
    assert payload["context"]["context_id"] == "CTX-001"


def test_contract_does_not_modify_rag_context():
    context = make_context()

    original = context.to_json()

    AIContextContract().create_request(
        request_id="AICTX-010",
        investigation_id="INV-010",
        purpose="boundary test",
        context=context,
        created_at=datetime(2026, 9, 22, 12, 5, tzinfo=timezone.utc),
    )

    assert context.to_json() == original
