"""Execution adapter contracts for TAP B21.

These contracts define the boundary between B21 orchestration and
controlled execution adapters.

An adapter must independently enforce authorization before execution.
A valid request object alone does not grant execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from .authorization import AuthorizationGrant
from .contracts import (
    SUPPORTED_CHANNELS,
    RemediationAction,
    RemediationPlan,
    TaskRequest,
)
from .plan_router import RoutedAction


class ExecutionStatus(str, Enum):
    """Outcome reported by an execution adapter."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    UNKNOWN = "UNKNOWN"


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_aware_datetime(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


@dataclass(frozen=True)
class AdapterExecutionRequest:
    """A scoped request presented to a controlled execution adapter.

    The authorization grant is supplied for independent adapter-side
    verification. This contract does not itself verify the grant.
    """

    task: TaskRequest
    plan: RemediationPlan
    action: RemediationAction
    routed_action: RoutedAction
    routed_actions: tuple[RoutedAction, ...]
    authorization_grant: AuthorizationGrant

    def validate(self) -> None:
        if not isinstance(self.task, TaskRequest):
            raise ValueError("task must be a TaskRequest")

        if not isinstance(self.plan, RemediationPlan):
            raise ValueError("plan must be a RemediationPlan")

        if not isinstance(self.action, RemediationAction):
            raise ValueError("action must be a RemediationAction")

        if not isinstance(self.routed_action, RoutedAction):
            raise ValueError("routed_action must be a RoutedAction")

        if not isinstance(self.authorization_grant, AuthorizationGrant):
            raise ValueError(
                "authorization_grant must be an AuthorizationGrant"
            )

        self.task.validate()
        self.plan.validate()
        self.authorization_grant.validate()
        self.action.validate()

        if self.task.task_id != self.plan.task_id:
            raise ValueError("task and plan IDs do not match")

        if self.action not in self.plan.actions:
            raise ValueError("action does not belong to the supplied plan")

        if self.action.target != self.task.target:
            raise ValueError("action target is outside the task target")

        if not isinstance(self.routed_actions, tuple):
            raise ValueError("routed_actions must be a tuple")

        if len(self.routed_actions) != len(self.plan.actions):
            raise ValueError(
                "routed_actions must cover every plan action"
            )

        routes_by_id: dict[str, RoutedAction] = {}

        for route in self.routed_actions:
            if not isinstance(route, RoutedAction):
                raise ValueError(
                    "every routed action must be a RoutedAction"
                )

            if route.action_id in routes_by_id:
                raise ValueError("routed action IDs must be unique")

            routes_by_id[route.action_id] = route

        plan_actions = {
            plan_action.action_id: plan_action
            for plan_action in self.plan.actions
        }

        if set(routes_by_id) != set(plan_actions):
            raise ValueError(
                "routed actions must match all plan action IDs"
            )

        for action_id, route in routes_by_id.items():
            plan_action = plan_actions[action_id]

            if route.operation != plan_action.operation:
                raise ValueError(
                    f"routed operation mismatch for action {action_id}"
                )

            if route.target != plan_action.target:
                raise ValueError(
                    f"routed target mismatch for action {action_id}"
                )

            if route.environment != self.task.environment:
                raise ValueError(
                    f"routed environment mismatch for action {action_id}"
                )

            if route.selected_channel not in SUPPORTED_CHANNELS:
                raise ValueError(
                    f"unsupported selected channel for action {action_id}"
                )

        expected_route = routes_by_id.get(self.action.action_id)

        if expected_route != self.routed_action:
            raise ValueError(
                "routed_action does not match the supplied action"
            )

        grant = self.authorization_grant

        if grant.task_id != self.task.task_id:
            raise ValueError("authorization grant task ID mismatch")

        if grant.plan_id != self.plan.plan_id:
            raise ValueError("authorization grant plan ID mismatch")

        if grant.environment != self.task.environment:
            raise ValueError("authorization grant environment mismatch")


@dataclass(frozen=True)
class AdapterExecutionResult:
    """Structured execution outcome returned by an adapter."""

    task_id: str
    plan_id: str
    action_id: str
    adapter_id: str
    selected_channel: str
    operation: str
    target: str
    environment: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: datetime | None
    message: str
    evidence_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        for name in (
            "task_id",
            "plan_id",
            "action_id",
            "adapter_id",
            "selected_channel",
            "operation",
            "target",
            "environment",
            "message",
        ):
            _require_text(getattr(self, name), name)

        if self.selected_channel not in SUPPORTED_CHANNELS:
            raise ValueError(
                f"unsupported selected channel: {self.selected_channel}"
            )

        if not isinstance(self.status, ExecutionStatus):
            raise ValueError("status must be an ExecutionStatus")

        _require_aware_datetime(self.started_at, "started_at")

        if self.completed_at is not None:
            _require_aware_datetime(self.completed_at, "completed_at")

            if self.completed_at < self.started_at:
                raise ValueError(
                    "completed_at must not be earlier than started_at"
                )

        if self.status in {
            ExecutionStatus.SUCCEEDED,
            ExecutionStatus.FAILED,
        } and self.completed_at is None:
            raise ValueError(
                "completed_at is required for SUCCEEDED and FAILED"
            )

        if not isinstance(self.evidence_ids, tuple):
            raise ValueError("evidence_ids must be a tuple")

        for evidence_id in self.evidence_ids:
            _require_text(evidence_id, "evidence_id")

        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("evidence_ids must be unique")


class RemediationAdapter(Protocol):
    """Interface implemented by each controlled execution adapter.

    Implementations may be local processes or remote service clients.
    They must validate the request and independently enforce authorization
    before executing any operation.
    """

    @property
    def adapter_id(self) -> str:
        """Return the unique adapter identifier."""
        ...

    @property
    def supported_channels(self) -> frozenset[str]:
        """Return the channels handled by this adapter."""
        ...

    @property
    def supported_operations(self) -> frozenset[str]:
        """Return the explicitly supported operation names."""
        ...

    def validate_execution_request(
        self,
        request: AdapterExecutionRequest,
    ) -> None:
        """Validate scope, operation, parameters and authorization.

        Raise an exception if the request is not safe and authorized.
        """
        ...

    def execute_approved_request(
        self,
        request: AdapterExecutionRequest,
    ) -> AdapterExecutionResult:
        """Execute a validated and authorized request.

        Return a structured result. Do not treat a timeout or unknown
        outcome as proof that the operation did not execute.
        """
        ...


class AdapterAuthorizationError(RuntimeError):
    """Raised when adapter-side authorization verification fails."""


def verify_adapter_authorization(
    request: AdapterExecutionRequest,
    trusted_public_keys,
    now: datetime | None = None,
) -> bool:
    """Independently verify authorization before adapter execution.

    Trusted public keys must come from trusted adapter deployment
    configuration, never from the incoming execution request.

    This function verifies the grant but does not consume it.
    """

    from collections.abc import Mapping

    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PublicKey,
    )

    from .authorization import (
        AuthorizationVerificationError,
        verify_authorization_grant,
    )

    if not isinstance(request, AdapterExecutionRequest):
        raise AdapterAuthorizationError(
            "invalid adapter execution request"
        )

    # Validate the execution contract before checking authorization.
    request.validate()

    if not isinstance(trusted_public_keys, Mapping):
        raise AdapterAuthorizationError(
            "trusted public keys must be a mapping"
        )

    for issuer_id, public_key in trusted_public_keys.items():
        if not isinstance(issuer_id, str) or not issuer_id.strip():
            raise AdapterAuthorizationError(
                "trusted issuer IDs must be non-empty strings"
            )

        if not isinstance(public_key, Ed25519PublicKey):
            raise AdapterAuthorizationError(
                f"trusted key for {issuer_id!r} is not an Ed25519 public key"
            )

    try:
        return verify_authorization_grant(
            grant=request.authorization_grant,
            task=request.task,
            plan=request.plan,
            routed_actions=request.routed_actions,
            trusted_public_keys=trusted_public_keys,
            now=now,
        )

    except (
        AuthorizationVerificationError,
        ValueError,
        TypeError,
    ) as exc:
        raise AdapterAuthorizationError(
            "adapter-side authorization verification failed"
        ) from exc
