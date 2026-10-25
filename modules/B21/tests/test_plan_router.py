import unittest

from tap_b21.channel_selector import Capability, CapabilityRegistry
from tap_b21.contracts import TaskRequest, RemediationAction, RemediationPlan
from tap_b21.plan_router import route_plan
from tap_b21.workflow import Workflow, WorkflowState


class TestPlanRouter(unittest.TestCase):

    def setUp(self):
        self.task = TaskRequest(
            task_id="task-001",
            incident_id="incident-001",
            target="server-01",
            environment="lab",
            requested_by="sre-user",
            objective="Restore service availability",
        )

        self.action = RemediationAction(
            action_id="action-001",
            channel="ansible",
            operation="restart_service",
            target="server-01",
            purpose="Restore the service",
            expected_state="service_active",
        )

        self.plan = RemediationPlan(
            plan_id="plan-001",
            task_id="task-001",
            summary="Restore service availability",
            actions=(self.action,),
            verification_requirements=("service_active",),
        )

        self.registry = CapabilityRegistry([
            Capability(
                channel="kubernetes",
                operation="restart_service",
                target="server-01",
            )
        ])

        self.workflow = Workflow("task-001")
        self.workflow.transition(WorkflowState.INVESTIGATING)
        self.workflow.transition(WorkflowState.PLAN_PROPOSED)

    def test_successful_routing_moves_to_governance_pending(self):
        result = route_plan(
            self.task, self.plan, self.registry, self.workflow
        )

        self.assertTrue(result.accepted)
        self.assertEqual(len(result.routed_actions), 1)
        self.assertEqual(
            result.routed_actions[0].selected_channel,
            "kubernetes",
        )
        self.assertEqual(
            self.workflow.state,
            WorkflowState.GOVERNANCE_PENDING,
        )

    def test_plan_task_mismatch_is_rejected(self):
        wrong_plan = RemediationPlan(
            plan_id="plan-002",
            task_id="another-task",
            summary="Wrong task",
            actions=(self.action,),
            verification_requirements=("service_active",),
        )

        result = route_plan(
            self.task, wrong_plan, self.registry, self.workflow
        )

        self.assertFalse(result.accepted)
        self.assertEqual(self.workflow.state, WorkflowState.PLAN_PROPOSED)

    def test_workflow_task_mismatch_is_rejected(self):
        wrong_workflow = Workflow("another-task")
        wrong_workflow.transition(WorkflowState.INVESTIGATING)
        wrong_workflow.transition(WorkflowState.PLAN_PROPOSED)

        result = route_plan(
            self.task, self.plan, self.registry, wrong_workflow
        )

        self.assertFalse(result.accepted)
        self.assertEqual(
            wrong_workflow.state,
            WorkflowState.PLAN_PROPOSED,
        )

    def test_missing_capability_rejects_plan(self):
        empty_registry = CapabilityRegistry()

        result = route_plan(
            self.task, self.plan, empty_registry, self.workflow
        )

        self.assertFalse(result.accepted)
        self.assertEqual(result.routed_actions, ())
        self.assertEqual(self.workflow.state, WorkflowState.PLAN_PROPOSED)

    def test_ambiguous_capabilities_reject_plan(self):
        ambiguous_registry = CapabilityRegistry([
            Capability("kubernetes", "restart_service", "server-01"),
            Capability("ansible", "restart_service", "server-01"),
        ])

        result = route_plan(
            self.task, self.plan, ambiguous_registry, self.workflow
        )

        self.assertFalse(result.accepted)
        self.assertEqual(result.routed_actions, ())
        self.assertEqual(self.workflow.state, WorkflowState.PLAN_PROPOSED)

    def test_wrong_workflow_state_rejects_plan(self):
        wrong_state_workflow = Workflow("task-001")

        result = route_plan(
            self.task, self.plan, self.registry, wrong_state_workflow
        )

        self.assertFalse(result.accepted)
        self.assertEqual(
            wrong_state_workflow.state,
            WorkflowState.ACCEPTED,
        )

    def test_partial_routing_is_not_returned(self):
        second_action = RemediationAction(
            action_id="action-002",
            channel="ansible",
            operation="unknown_operation",
            target="server-02",
            purpose="Perform another operation",
            expected_state="healthy",
        )

        multi_action_plan = RemediationPlan(
            plan_id="plan-003",
            task_id="task-001",
            summary="Two-action plan",
            actions=(self.action, second_action),
            verification_requirements=("service_active", "healthy"),
        )

        result = route_plan(
            self.task, multi_action_plan, self.registry, self.workflow
        )

        self.assertFalse(result.accepted)
        self.assertEqual(result.routed_actions, ())
        self.assertEqual(self.workflow.state, WorkflowState.PLAN_PROPOSED)


if __name__ == "__main__":
    unittest.main()
