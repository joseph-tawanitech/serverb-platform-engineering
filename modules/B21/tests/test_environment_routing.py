import unittest

from tap_b21.channel_selector import Capability, CapabilityRegistry
from tap_b21.contracts import TaskRequest, RemediationAction, RemediationPlan
from tap_b21.plan_router import route_plan
from tap_b21.workflow import Workflow, WorkflowState


class EnvironmentRoutingTests(unittest.TestCase):

    def setUp(self):
        self.task = TaskRequest(
            task_id="task-env-001",
            incident_id="incident-env-001",
            target="server-01",
            environment="lab",
            requested_by="sre-user",
            objective="Restore service",
        )

        self.action = RemediationAction(
            action_id="action-env-001",
            channel="ansible",
            operation="restart_service",
            target="server-01",
            purpose="Restore service",
            expected_state="service_active",
        )

        self.plan = RemediationPlan(
            plan_id="plan-env-001",
            task_id="task-env-001",
            summary="Restore service",
            actions=(self.action,),
            verification_requirements=("service_active",),
        )

        self.workflow = Workflow("task-env-001")
        self.workflow.transition(WorkflowState.INVESTIGATING)
        self.workflow.transition(WorkflowState.PLAN_PROPOSED)

    def test_production_capability_cannot_route_lab_task(self):
        registry = CapabilityRegistry([
            Capability(
                "ansible",
                "restart_service",
                "server-01",
                "production",
            )
        ])

        result = route_plan(
            self.task, self.plan, registry, self.workflow
        )

        self.assertFalse(result.accepted)
        self.assertEqual(result.routed_actions, ())
        self.assertEqual(
            self.workflow.state,
            WorkflowState.PLAN_PROPOSED,
        )

    def test_matching_environment_allows_routing(self):
        registry = CapabilityRegistry([
            Capability(
                "ansible",
                "restart_service",
                "server-01",
                "lab",
            )
        ])

        result = route_plan(
            self.task, self.plan, registry, self.workflow
        )

        self.assertTrue(result.accepted)
        self.assertEqual(
            result.routed_actions[0].environment,
            "lab",
        )
        self.assertEqual(
            self.workflow.state,
            WorkflowState.GOVERNANCE_PENDING,
        )

    def test_action_outside_task_target_scope_is_rejected(self):
        wrong_target_action = RemediationAction(
            action_id="action-env-002",
            channel="ansible",
            operation="restart_service",
            target="server-02",
            purpose="Restore another service",
            expected_state="service_active",
        )

        wrong_target_plan = RemediationPlan(
            plan_id="plan-env-002",
            task_id="task-env-001",
            summary="Target scope test",
            actions=(wrong_target_action,),
            verification_requirements=("service_active",),
        )

        registry = CapabilityRegistry([
            Capability(
                "ansible",
                "restart_service",
                "server-02",
                "lab",
            )
        ])

        result = route_plan(
            self.task, wrong_target_plan, registry, self.workflow
        )

        self.assertFalse(result.accepted)
        self.assertEqual(result.routed_actions, ())
        self.assertEqual(
            self.workflow.state,
            WorkflowState.PLAN_PROPOSED,
        )


if __name__ == "__main__":
    unittest.main()
