
"""Governed workflow state machine for TAP B21.

State transitions organize the workflow; they do not independently
grant authorization or execute remediation actions.
"""

from enum import Enum


class WorkflowState(str, Enum):
    ACCEPTED = "ACCEPTED"
    INVESTIGATING = "INVESTIGATING"
    PLAN_PROPOSED = "PLAN_PROPOSED"
    GOVERNANCE_PENDING = "GOVERNANCE_PENDING"
    AUTHORIZED = "AUTHORIZED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    UNVERIFIED = "UNVERIFIED"


ALLOWED_TRANSITIONS = {
    WorkflowState.ACCEPTED: {
        WorkflowState.INVESTIGATING,
        WorkflowState.CANCELLED,
        WorkflowState.NEEDS_HUMAN,
    },
    WorkflowState.INVESTIGATING: {
        WorkflowState.PLAN_PROPOSED,
        WorkflowState.FAILED,
        WorkflowState.CANCELLED,
        WorkflowState.NEEDS_HUMAN,
    },
    WorkflowState.PLAN_PROPOSED: {
        WorkflowState.GOVERNANCE_PENDING,
        WorkflowState.REJECTED,
        WorkflowState.NEEDS_HUMAN,
        WorkflowState.CANCELLED,
    },
    WorkflowState.GOVERNANCE_PENDING: {
        WorkflowState.REJECTED,
        WorkflowState.NEEDS_HUMAN,
        WorkflowState.CANCELLED,
    },
    WorkflowState.AUTHORIZED: {
        WorkflowState.CANCELLED,
        WorkflowState.NEEDS_HUMAN,
    },
    WorkflowState.EXECUTING: {
        WorkflowState.VERIFYING,
        WorkflowState.FAILED,
        WorkflowState.NEEDS_HUMAN,
        WorkflowState.UNVERIFIED,
    },
    WorkflowState.VERIFYING: {
        WorkflowState.COMPLETED,
        WorkflowState.FAILED,
        WorkflowState.UNVERIFIED,
        WorkflowState.NEEDS_HUMAN,
    },
    WorkflowState.UNVERIFIED: {
        WorkflowState.VERIFYING,
        WorkflowState.NEEDS_HUMAN,
    },
    WorkflowState.NEEDS_HUMAN: {
        WorkflowState.INVESTIGATING,
        WorkflowState.GOVERNANCE_PENDING,
        WorkflowState.VERIFYING,
        WorkflowState.CANCELLED,
    },
    WorkflowState.REJECTED: set(),
    WorkflowState.FAILED: set(),
    WorkflowState.CANCELLED: set(),
    WorkflowState.COMPLETED: set(),
}


class InvalidTransitionError(ValueError):
    """Raised when a workflow attempts a forbidden state transition."""


class Workflow:
    """In-memory state machine for a single workflow."""

    def __init__(self, task_id: str):
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id must be a non-empty string")

        self.task_id = task_id
        self.state = WorkflowState.ACCEPTED
        self.authorization_grant_id: str | None = None

    def transition(self, next_state: WorkflowState) -> WorkflowState:
        """Perform an ordinary permitted workflow transition."""

        if not isinstance(next_state, WorkflowState):
            raise ValueError("next_state must be a WorkflowState")

        allowed = ALLOWED_TRANSITIONS[self.state]

        if next_state not in allowed:
            raise InvalidTransitionError(
                f"transition not allowed: {self.state.value} "
                f"-> {next_state.value}"
            )

        self.state = next_state
        return self.state

    def _authorize_after_trusted_checks(self, grant_id: str) -> WorkflowState:
        """Internal transition called by the trusted authorization service.

        This is an application-level guard, not a security boundary against
        arbitrary code running inside this Python process.
        """

        if not isinstance(grant_id, str) or not grant_id.strip():
            raise ValueError("grant_id must be a non-empty string")

        if self.state is not WorkflowState.GOVERNANCE_PENDING:
            raise InvalidTransitionError(
                "workflow must be GOVERNANCE_PENDING before authorization"
            )

        if self.authorization_grant_id is not None:
            raise InvalidTransitionError(
                "workflow already has an authorization grant"
            )

        self.authorization_grant_id = grant_id
        self.state = WorkflowState.AUTHORIZED
        return self.state

    def _begin_execution_after_trusted_checks(
        self,
        grant_id: str,
    ) -> WorkflowState:
        """Begin execution using the grant already accepted by trusted authorization.

        This checks the workflow state and exact grant ID match.
        It does not independently verify the grant signature or consume it.

        This is an application-level guard, not a security boundary against
        arbitrary code running inside this Python process.
        """

        if not isinstance(grant_id, str) or not grant_id.strip():
            raise ValueError("grant_id must be a non-empty string")

        if self.state is not WorkflowState.AUTHORIZED:
            raise ValueError(
                "workflow must be AUTHORIZED before execution"
            )

        if self.authorization_grant_id != grant_id:
            raise ValueError(
                "grant_id does not match the workflow authorization grant"
            )

        self.state = WorkflowState.EXECUTING
        return self.state
