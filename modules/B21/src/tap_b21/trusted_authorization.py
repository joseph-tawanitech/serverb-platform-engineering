
"""Trusted authorization service for B21 remediation plans.

Coordinates B20 policy evaluation, cryptographic grant verification,
replay protection, and the B21 workflow authorization transition.

This is a development-stage orchestration component. Infrastructure
execution adapters must independently enforce authorization.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from tap_b20.action_service import evaluate_security_action
from tap_b20.actions import SecurityActionRequest
from tap_b20.models import SecurityDecision
from tap_b20.policy import SecurityPolicy

from .authorization import (
    AuthorizationGrant,
    AuthorizationVerificationError,
    verify_authorization_grant,
)
from .authorization_ledger import AuthorizationLedger
from .contracts import RemediationPlan, TaskRequest
from .plan_router import RoutedAction
from .workflow import Workflow, WorkflowState


class TrustedAuthorizationError(RuntimeError):
    """Raised when trusted authorization is rejected."""


@dataclass(frozen=True)
class TrustedAuthorizationResult:
    """Result of a successful trusted authorization operation."""

    task_id: str
    grant_id: str
    approved_actions: int
    status: str = "AUTHORIZED"


class TrustedAuthorizationService:
    """Coordinates trusted policy and authorization checks."""

    def __init__(
        self,
        policy: SecurityPolicy,
        trusted_public_keys: Mapping[str, Ed25519PublicKey],
        ledger: AuthorizationLedger,
    ) -> None:
        if not isinstance(policy, SecurityPolicy):
            raise TypeError("policy must be a trusted SecurityPolicy")

        if not isinstance(ledger, AuthorizationLedger):
            raise TypeError("ledger must implement AuthorizationLedger")

        if not isinstance(trusted_public_keys, Mapping):
            raise TypeError("trusted_public_keys must be a mapping")

        for issuer_id, public_key in trusted_public_keys.items():
            if not isinstance(issuer_id, str) or not issuer_id.strip():
                raise TypeError("issuer IDs must be non-empty strings")

            if not isinstance(public_key, Ed25519PublicKey):
                raise TypeError(
                    f"trusted key for {issuer_id!r} must be an Ed25519 public key"
                )

        self._policy = policy
        self._trusted_public_keys = dict(trusted_public_keys)
        self._ledger = ledger
        self._lock = RLock()

    def authorize(
        self,
        task: TaskRequest,
        plan: RemediationPlan,
        routed_actions: tuple[RoutedAction, ...],
        grant: AuthorizationGrant,
        workflow: Workflow,
        now: datetime | None = None,
    ) -> TrustedAuthorizationResult:
        """Authorize a plan only after all trusted checks succeed."""

        with self._lock:
            if not isinstance(task, TaskRequest):
                raise TrustedAuthorizationError("invalid task contract")

            if not isinstance(plan, RemediationPlan):
                raise TrustedAuthorizationError("invalid remediation plan")

            if not isinstance(grant, AuthorizationGrant):
                raise TrustedAuthorizationError("invalid authorization grant")

            if not isinstance(workflow, Workflow):
                raise TrustedAuthorizationError("invalid workflow")

            if not isinstance(routed_actions, tuple):
                raise TrustedAuthorizationError(
                    "routed_actions must be a tuple"
                )

            if workflow.task_id != task.task_id:
                raise TrustedAuthorizationError(
                    "workflow does not belong to this task"
                )

            if workflow.state is not WorkflowState.GOVERNANCE_PENDING:
                raise TrustedAuthorizationError(
                    "workflow is not awaiting authorization"
                )

            if plan.task_id != task.task_id:
                raise TrustedAuthorizationError(
                    "plan does not belong to this task"
                )

            if self._policy.environment != task.environment:
                raise TrustedAuthorizationError(
                    "trusted policy environment does not match task"
                )

            if len(routed_actions) != len(plan.actions):
                raise TrustedAuthorizationError(
                    "routed actions do not match the remediation plan"
                )

            # Evaluate every proposed action using the trusted B20 policy.
            decisions = []

            for action in plan.actions:
                if action.target != task.target:
                    raise TrustedAuthorizationError(
                        "action target does not match trusted task target"
                    )

                request_id = f"{task.task_id}:{action.action_id}"

                request = SecurityActionRequest(
                    action_id=action.action_id,
                    request_id=request_id,
                    operation=action.operation,
                    environment=task.environment,
                    asset=action.target,
                    requester=task.requested_by,
                    purpose=action.purpose,
                    recommendation=plan.summary,
                    risk=self._policy.max_risk,
                )

                decision = evaluate_security_action(
                    request,
                    self._policy,
                )

                if decision.action_id != action.action_id:
                    raise TrustedAuthorizationError(
                        "policy returned a mismatched action ID"
                    )

                if decision.request_id != request_id:
                    raise TrustedAuthorizationError(
                        "policy returned a mismatched request ID"
                    )

                if decision.decision is not SecurityDecision.ALLOW:
                    raise TrustedAuthorizationError(
                        f"B20 did not ALLOW action {action.action_id}: "
                        f"{decision.decision.value}"
                    )

                if not decision.authorization_required:
                    raise TrustedAuthorizationError(
                        "B20 did not require trusted authorization"
                    )

                decisions.append(decision)

            # Verify the signature, issuer, expiry, environment,
            # task identity, and exact plan digest.
            try:
                verify_authorization_grant(
                    grant=grant,
                    task=task,
                    plan=plan,
                    routed_actions=routed_actions,
                    trusted_public_keys=self._trusted_public_keys,
                    now=now or datetime.now(timezone.utc),
                )
            except AuthorizationVerificationError as exc:
                raise TrustedAuthorizationError(
                    "cryptographic authorization verification failed"
                ) from exc

            # Consume the grant exactly once to prevent replay.
            try:
                self._ledger.consume(grant.grant_id)
            except Exception as exc:
                raise TrustedAuthorizationError(
                    "authorization grant is not active or cannot be consumed"
                ) from exc

            # This internal workflow method must be implemented separately.
            workflow._authorize_after_trusted_checks(grant.grant_id)

            return TrustedAuthorizationResult(
                task_id=task.task_id,
                grant_id=grant.grant_id,
                approved_actions=len(decisions),
            )
