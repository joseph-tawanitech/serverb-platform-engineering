"""Trusted authorization contracts for TAP B21.

This module defines authorization data and exact-plan binding.
It does not verify signatures or grant execution permission.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import hashlib
import json
import re
from typing import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from tap_b21.channel_selector import SUPPORTED_CHANNELS
from tap_b21.contracts import RemediationPlan, TaskRequest
from tap_b21.plan_router import RoutedAction


@dataclass(frozen=True)
class AuthorizationGrant:
    grant_id: str
    task_id: str
    plan_id: str
    plan_digest: str
    environment: str
    approved_by: str
    issuer_id: str
    issued_at: str
    expires_at: str
    signing_algorithm: str
    signature: str

    def validate(self) -> None:
        required = (
            ("grant_id", self.grant_id),
            ("task_id", self.task_id),
            ("plan_id", self.plan_id),
            ("environment", self.environment),
            ("approved_by", self.approved_by),
            ("issuer_id", self.issuer_id),
            ("signing_algorithm", self.signing_algorithm),
            ("signature", self.signature),
        )

        for name, value in required:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        if not isinstance(self.plan_digest, str) or not re.fullmatch(
            r"[0-9a-f]{64}", self.plan_digest
        ):
            raise ValueError("plan_digest must be a lowercase SHA-256 hex digest")

        try:
            issued = datetime.fromisoformat(self.issued_at)
            expires = datetime.fromisoformat(self.expires_at)
        except (TypeError, ValueError) as exc:
            raise ValueError("timestamps must be valid ISO-8601 values") from exc

        if issued.tzinfo is None or issued.utcoffset() is None:
            raise ValueError("issued_at must include a timezone")

        if expires.tzinfo is None or expires.utcoffset() is None:
            raise ValueError("expires_at must include a timezone")

        if expires <= issued:
            raise ValueError("expires_at must be later than issued_at")


def compute_plan_digest(
    task: TaskRequest,
    plan: RemediationPlan,
    routed_actions: tuple[RoutedAction, ...],
) -> str:
    """Hash the exact task, proposed plan and selected execution routes."""

    task.validate()
    plan.validate()

    if plan.task_id != task.task_id:
        raise ValueError("plan task_id does not match task")

    if not isinstance(routed_actions, tuple):
        raise TypeError("routed_actions must be a tuple")

    if len(routed_actions) != len(plan.actions):
        raise ValueError("every plan action must have exactly one route")

    plan_actions = {action.action_id: action for action in plan.actions}
    routed_by_id = {}

    for route in routed_actions:
        if not isinstance(route, RoutedAction):
            raise TypeError("every route must be a RoutedAction")

        if route.action_id in routed_by_id:
            raise ValueError("duplicate routed action ID")

        routed_by_id[route.action_id] = route

    if set(plan_actions) != set(routed_by_id):
        raise ValueError("routed actions do not match plan actions")

    for action_id, action in plan_actions.items():
        route = routed_by_id[action_id]

        if (
            route.operation != action.operation
            or route.target != action.target
            or route.environment != task.environment
            or route.selected_channel not in SUPPORTED_CHANNELS
        ):
            raise ValueError(
                f"route does not correctly bind action {action_id}"
            )

    payload = {
        "task": {
            "task_id": task.task_id,
            "incident_id": task.incident_id,
            "target": task.target,
            "environment": task.environment,
            "requested_by": task.requested_by,
            "objective": task.objective,
            "metadata": task.metadata,
        },
        "plan": {
            "plan_id": plan.plan_id,
            "task_id": plan.task_id,
            "summary": plan.summary,
            "source": plan.source,
            "metadata": plan.metadata,
            "verification_requirements": list(
                plan.verification_requirements
            ),
            "actions": [
                {
                    "action_id": action.action_id,
                    "channel": action.channel,
                    "operation": action.operation,
                    "target": action.target,
                    "purpose": action.purpose,
                    "expected_state": action.expected_state,
                    "parameters": action.parameters,
                }
                for action in plan.actions
            ],
        },
        "routed_actions": [
            {
                "action_id": route.action_id,
                "operation": route.operation,
                "target": route.target,
                "environment": route.environment,
                "selected_channel": route.selected_channel,
            }
            for route in sorted(
                routed_actions, key=lambda item: item.action_id
            )
        ],
    }

    try:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "task and plan data must contain JSON-compatible values"
        ) from exc

    return hashlib.sha256(canonical).hexdigest()


class AuthorizationVerificationError(ValueError):
    """Raised when a trusted authorization grant cannot be verified."""


def authorization_grant_signing_bytes(
    grant: AuthorizationGrant,
) -> bytes:
    """Return canonical grant data, excluding the signature itself."""

    grant.validate()

    payload = {
        "grant_id": grant.grant_id,
        "task_id": grant.task_id,
        "plan_id": grant.plan_id,
        "plan_digest": grant.plan_digest,
        "environment": grant.environment,
        "approved_by": grant.approved_by,
        "issuer_id": grant.issuer_id,
        "issued_at": grant.issued_at,
        "expires_at": grant.expires_at,
        "signing_algorithm": grant.signing_algorithm,
    }

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def verify_authorization_grant(
    grant: AuthorizationGrant,
    task: TaskRequest,
    plan: RemediationPlan,
    routed_actions: tuple[RoutedAction, ...],
    trusted_public_keys: Mapping[str, Ed25519PublicKey],
    now: datetime | None = None,
) -> bool:
    """Verify issuer signature, grant lifetime and exact plan binding.

    trusted_public_keys must come from trusted deployment configuration,
    never from an AI-generated request or remediation plan.
    """

    grant.validate()
    task.validate()
    plan.validate()

    if grant.signing_algorithm != "Ed25519":
        raise AuthorizationVerificationError(
            "unsupported signing algorithm"
        )

    if grant.issuer_id not in trusted_public_keys:
        raise AuthorizationVerificationError(
            "authorization issuer is not trusted"
        )

    public_key = trusted_public_keys[grant.issuer_id]

    if not isinstance(public_key, Ed25519PublicKey):
        raise AuthorizationVerificationError(
            "trusted issuer key is not an Ed25519 public key"
        )

    if grant.task_id != task.task_id:
        raise AuthorizationVerificationError("task ID mismatch")

    if grant.plan_id != plan.plan_id:
        raise AuthorizationVerificationError("plan ID mismatch")

    if grant.environment != task.environment:
        raise AuthorizationVerificationError("environment mismatch")

    expected_digest = compute_plan_digest(
        task, plan, routed_actions
    )

    if grant.plan_digest != expected_digest:
        raise AuthorizationVerificationError(
            "approved plan digest does not match"
        )

    issued = datetime.fromisoformat(grant.issued_at)
    expires = datetime.fromisoformat(grant.expires_at)

    verification_time = now or datetime.now(timezone.utc)

    if (
        verification_time.tzinfo is None
        or verification_time.utcoffset() is None
    ):
        raise AuthorizationVerificationError(
            "verification time must include a timezone"
        )

    if issued > verification_time:
        raise AuthorizationVerificationError(
            "authorization grant is not yet valid"
        )

    if verification_time >= expires:
        raise AuthorizationVerificationError(
            "authorization grant has expired"
        )

    try:
        signature = base64.b64decode(
            grant.signature,
            validate=True,
        )
    except (ValueError, TypeError) as exc:
        raise AuthorizationVerificationError(
            "signature is not valid Base64"
        ) from exc

    try:
        public_key.verify(
            signature,
            authorization_grant_signing_bytes(grant),
        )
    except InvalidSignature as exc:
        raise AuthorizationVerificationError(
            "authorization signature is invalid"
        ) from exc

    return True
