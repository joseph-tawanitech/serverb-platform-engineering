"""Governed remediation-plan routing for TAP B21."""

from dataclasses import dataclass

from tap_b21.channel_selector import (
    CapabilityRegistry,
    SelectionStatus,
    select_channel,
)
from tap_b21.contracts import RemediationPlan, TaskRequest
from tap_b21.workflow import Workflow, WorkflowState


@dataclass(frozen=True)
class RoutedAction:
    action_id: str
    operation: str
    target: str
    environment: str
    selected_channel: str


@dataclass(frozen=True)
class RoutingResult:
    accepted: bool
    task_id: str
    routed_actions: tuple[RoutedAction, ...]
    reason: str


def route_plan(
    task: TaskRequest,
    plan: RemediationPlan,
    registry: CapabilityRegistry,
    workflow: Workflow,
) -> RoutingResult:
    """Route every proposed action before governance evaluation."""

    task.validate()
    plan.validate()

    if plan.task_id != task.task_id:
        return RoutingResult(
            False, task.task_id, (),
            "Plan task_id does not match request task_id.",
        )

    if workflow.task_id != task.task_id:
        return RoutingResult(
            False, task.task_id, (),
            "Workflow task_id does not match request task_id.",
        )

    if workflow.state != WorkflowState.PLAN_PROPOSED:
        return RoutingResult(
            False, task.task_id, (),
            "Workflow must be in PLAN_PROPOSED before routing.",
        )

    routed = []

    for action in plan.actions:
        if action.target != task.target:
            return RoutingResult(
                False,
                task.task_id,
                (),
                f"Action {action.action_id} targets a resource "
                "outside the task target scope.",
            )

        selection = select_channel(
            action,
            registry,
            environment=task.environment,
        )

        if selection.status != SelectionStatus.SELECTED:
            return RoutingResult(
                False,
                task.task_id,
                (),
                f"Action {action.action_id} routing failed: "
                f"{selection.status.value}. {selection.reason}",
            )

        routed.append(
            RoutedAction(
                action_id=action.action_id,
                operation=action.operation,
                target=action.target,
                environment=task.environment,
                selected_channel=selection.selected_channel,
            )
        )

    workflow.transition(WorkflowState.GOVERNANCE_PENDING)

    return RoutingResult(
        True,
        task.task_id,
        tuple(routed),
        "All actions have unique registered routes. Governance evaluation is next.",
    )
