"""Adapter for the existing B17 investigation output contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


B17_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "B17"
    / "schemas"
    / "recommendation.schema.json"
)


class B17ContractError(ValueError):
    """Raised when an AI response violates the B17 output contract."""


def load_b17_schema() -> dict[str, Any]:
    """Load the existing B17 investigation schema from the repository."""

    return json.loads(B17_SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_b17_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate and return a B17 investigation result."""

    if not isinstance(result, dict):
        raise B17ContractError("B17 result must be a JSON object")

    schema = load_b17_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(result),
        key=lambda error: list(error.path),
    )

    if errors:
        details = "; ".join(
            f"{list(error.path)}: {error.message}"
            for error in errors
        )
        raise B17ContractError(
            f"B17 investigation output violates the schema: {details}"
        )

    return result
