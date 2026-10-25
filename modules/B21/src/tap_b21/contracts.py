"""Validated task and remediation-plan contracts for TAP B21.

These contracts describe requests and proposals. They do not grant
authorization and do not execute infrastructure operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SUPPORTED_CHANNELS = frozenset({
    "kubernetes",
    "ansible",
    "service_api",
})


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


@dataclass(frozen=True)
class TaskRequest:
    """A validated request for a governed TAP workflow."""

    task_id: str
    incident_id: str
    target: str
    environment: str
    requested_by: str
    objective: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        for name in (
            "task_id",
            "incident_id",
            "target",
            "environment",
            "requested_by",
            "objective",
        ):
            _require_text(getattr(self, name), name)

        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")


@dataclass(frozen=True)
class RemediationAction:
    """A proposed operation, not an executable command."""

    action_id: str
    channel: str
    operation: str
    target: str
    purpose: str
    expected_state: str
    parameters: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        for name in (
            "action_id",
            "channel",
            "operation",
            "target",
            "purpose",
            "expected_state",
        ):
            _require_text(getattr(self, name), name)

        if self.channel not in SUPPORTED_CHANNELS:
            raise ValueError(
                f"unsupported remediation channel: {self.channel}"
            )

        if not isinstance(self.parameters, dict):
            raise ValueError("parameters must be a dictionary")


@dataclass(frozen=True)
class RemediationPlan:
    """A validated collection of proposed remediation actions."""

    plan_id: str
    task_id: str
    summary: str
    actions: tuple[RemediationAction, ...]
    verification_requirements: tuple[str, ...]
    source: str = "ai_recommendation"
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        for name in ("plan_id", "task_id", "summary", "source"):
            _require_text(getattr(self, name), name)

        if not isinstance(self.actions, tuple) or not self.actions:
            raise ValueError("actions must be a non-empty tuple")

        action_ids: list[str] = []

        for action in self.actions:
            if not isinstance(action, RemediationAction):
                raise ValueError(
                    "every plan action must be a RemediationAction"
                )
            action.validate()
            action_ids.append(action.action_id)

        if len(action_ids) != len(set(action_ids)):
            raise ValueError("action IDs must be unique within a plan")

        if not isinstance(self.verification_requirements, tuple):
            raise ValueError(
                "verification_requirements must be a tuple"
            )

        if not self.verification_requirements:
            raise ValueError(
                "at least one verification requirement is required"
            )

        for requirement in self.verification_requirements:
            _require_text(requirement, "verification requirement")

        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")
