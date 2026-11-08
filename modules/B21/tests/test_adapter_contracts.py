import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from tap_b21.adapter_contracts import (
    AdapterExecutionRequest,
    AdapterExecutionResult,
    ExecutionStatus,
)
from tap_b21.authorization import AuthorizationGrant
from tap_b21.contracts import (
    RemediationAction,
    RemediationPlan,
    TaskRequest,
)
from tap_b21.plan_router import RoutedAction


class TestAdapterExecutionRequest(unittest.TestCase):

    def setUp(self):
        self.task = TaskRequest(
            task_id="task-adapter-001",
            incident_id="incident-adapter-001",
            target="server-01",
            environment="lab",
            requested_by="sre-user",
            objective="Restore service",
        )

        self.action = RemediationAction(
            action_id="action-adapter-001",
            channel="ansible",
            operation="restart_service",
            target="server-01",
            purpose="Restore Nginx",
            expected_state="service_active",
            parameters={"service": "nginx"},
        )

        self.plan = RemediationPlan(
            plan_id="plan-adapter-001",
            task_id="task-adapter-001",
            summary="Restore Nginx",
            actions=(self.action,),
            verification_requirements=("service_active",),
        )

        # The router selected Kubernetes even though the proposed
        # action originally requested Ansible.
        self.route = RoutedAction(
            action_id="action-adapter-001",
            operation="restart_service",
            target="server-01",
            environment="lab",
            selected_channel="kubernetes",
        )

        self.routes = (self.route,)

        self.grant = AuthorizationGrant(
            grant_id="grant-adapter-001",
            task_id="task-adapter-001",
            plan_id="plan-adapter-001",
            plan_digest="a" * 64,
            environment="lab",
            approved_by="human-approver",
            issuer_id="trusted-authority",
            issued_at="2026-10-29T10:00:00+00:00",
            expires_at="2026-10-29T11:00:00+00:00",
            signing_algorithm="Ed25519",
            signature="placeholder-signature",
        )

        self.request = AdapterExecutionRequest(
            task=self.task,
            plan=self.plan,
            action=self.action,
            routed_action=self.route,
            routed_actions=self.routes,
            authorization_grant=self.grant,
        )

    def test_valid_request_passes_structural_validation(self):
        self.request.validate()

    def test_selected_channel_can_differ_from_proposed_channel(self):
        self.assertEqual(self.action.channel, "ansible")
        self.assertEqual(self.route.selected_channel, "kubernetes")

        self.request.validate()

    def test_task_plan_mismatch_is_rejected(self):
        wrong_plan = replace(
            self.plan,
            task_id="another-task",
        )

        request = replace(self.request, plan=wrong_plan)

        with self.assertRaises(ValueError):
            request.validate()

    def test_action_outside_plan_is_rejected(self):
        outside_action = replace(
            self.action,
            action_id="another-action",
        )

        request = replace(self.request, action=outside_action)

        with self.assertRaises(ValueError):
            request.validate()

    def test_action_target_outside_task_scope_is_rejected(self):
        wrong_action = replace(
            self.action,
            target="server-02",
        )

        wrong_plan = replace(
            self.plan,
            actions=(wrong_action,),
        )

        request = replace(
            self.request,
            plan=wrong_plan,
            action=wrong_action,
        )

        with self.assertRaises(ValueError):
            request.validate()

    def test_routed_actions_must_be_a_tuple(self):
        request = replace(
            self.request,
            routed_actions=[self.route],
        )

        with self.assertRaises(ValueError):
            request.validate()

    def test_missing_route_is_rejected(self):
        request = replace(
            self.request,
            routed_actions=(),
        )

        with self.assertRaises(ValueError):
            request.validate()

    def test_duplicate_route_ids_are_rejected(self):
        second_action = replace(
            self.action,
            action_id="action-adapter-002",
        )

        second_plan = replace(
            self.plan,
            actions=(self.action, second_action),
        )

        request = replace(
            self.request,
            plan=second_plan,
            routed_actions=(self.route, self.route),
        )

        with self.assertRaisesRegex(
            ValueError,
            "routed action IDs must be unique",
        ):
            request.validate()

    def test_route_operation_mismatch_is_rejected(self):
        wrong_route = replace(
            self.route,
            operation="delete_service",
        )

        request = replace(
            self.request,
            routed_action=wrong_route,
            routed_actions=(wrong_route,),
        )

        with self.assertRaises(ValueError):
            request.validate()

    def test_route_target_mismatch_is_rejected(self):
        wrong_route = replace(
            self.route,
            target="server-02",
        )

        request = replace(
            self.request,
            routed_action=wrong_route,
            routed_actions=(wrong_route,),
        )

        with self.assertRaises(ValueError):
            request.validate()

    def test_route_environment_mismatch_is_rejected(self):
        wrong_route = replace(
            self.route,
            environment="production",
        )

        request = replace(
            self.request,
            routed_action=wrong_route,
            routed_actions=(wrong_route,),
        )

        with self.assertRaises(ValueError):
            request.validate()

    def test_unsupported_selected_channel_is_rejected(self):
        wrong_route = replace(
            self.route,
            selected_channel="terraform",
        )

        request = replace(
            self.request,
            routed_action=wrong_route,
            routed_actions=(wrong_route,),
        )

        with self.assertRaises(ValueError):
            request.validate()

    def test_grant_task_mismatch_is_rejected(self):
        wrong_grant = replace(
            self.grant,
            task_id="another-task",
        )

        request = replace(
            self.request,
            authorization_grant=wrong_grant,
        )

        with self.assertRaises(ValueError):
            request.validate()

    def test_grant_plan_mismatch_is_rejected(self):
        wrong_grant = replace(
            self.grant,
            plan_id="another-plan",
        )

        request = replace(
            self.request,
            authorization_grant=wrong_grant,
        )

        with self.assertRaises(ValueError):
            request.validate()

    def test_grant_environment_mismatch_is_rejected(self):
        wrong_grant = replace(
            self.grant,
            environment="production",
        )

        request = replace(
            self.request,
            authorization_grant=wrong_grant,
        )

        with self.assertRaises(ValueError):
            request.validate()


class TestAdapterExecutionResult(unittest.TestCase):

    def setUp(self):
        self.started = datetime(
            2026, 10, 29, 10, 0, tzinfo=timezone.utc
        )
        self.completed = self.started + timedelta(seconds=15)

    def make_result(self, **overrides):
        values = {
            "task_id": "task-adapter-001",
            "plan_id": "plan-adapter-001",
            "action_id": "action-adapter-001",
            "adapter_id": "ansible-runner-adapter",
            "selected_channel": "ansible",
            "operation": "restart_service",
            "target": "server-01",
            "environment": "lab",
            "status": ExecutionStatus.SUCCEEDED,
            "started_at": self.started,
            "completed_at": self.completed,
            "message": "Service restart completed.",
            "evidence_ids": ("execution-001",),
        }

        values.update(overrides)
        return AdapterExecutionResult(**values)

    def test_successful_result_passes(self):
        self.make_result().validate()

    def test_failed_result_passes_with_completion_time(self):
        result = self.make_result(
            status=ExecutionStatus.FAILED,
        )

        result.validate()

    def test_timeout_result_can_have_no_completion_time(self):
        result = self.make_result(
            status=ExecutionStatus.TIMED_OUT,
            completed_at=None,
        )

        result.validate()

    def test_unknown_result_can_have_no_completion_time(self):
        result = self.make_result(
            status=ExecutionStatus.UNKNOWN,
            completed_at=None,
        )

        result.validate()

    def test_all_four_execution_statuses_exist(self):
        self.assertEqual(
            {status.value for status in ExecutionStatus},
            {"SUCCEEDED", "FAILED", "TIMED_OUT", "UNKNOWN"},
        )

    def test_success_requires_completion_time(self):
        result = self.make_result(completed_at=None)

        with self.assertRaises(ValueError):
            result.validate()

    def test_failure_requires_completion_time(self):
        result = self.make_result(
            status=ExecutionStatus.FAILED,
            completed_at=None,
        )

        with self.assertRaises(ValueError):
            result.validate()

    def test_naive_start_time_is_rejected(self):
        result = self.make_result(
            started_at=datetime(2026, 10, 29, 10, 0),
        )

        with self.assertRaises(ValueError):
            result.validate()

    def test_naive_completion_time_is_rejected(self):
        result = self.make_result(
            completed_at=datetime(2026, 10, 29, 10, 15),
        )

        with self.assertRaises(ValueError):
            result.validate()

    def test_completion_before_start_is_rejected(self):
        result = self.make_result(
            completed_at=self.started - timedelta(seconds=1),
        )

        with self.assertRaises(ValueError):
            result.validate()

    def test_unsupported_channel_is_rejected(self):
        result = self.make_result(
            selected_channel="terraform",
        )

        with self.assertRaises(ValueError):
            result.validate()

    def test_invalid_status_type_is_rejected(self):
        result = self.make_result(status="SUCCEEDED")

        with self.assertRaises(ValueError):
            result.validate()

    def test_duplicate_evidence_ids_are_rejected(self):
        result = self.make_result(
            evidence_ids=("evidence-001", "evidence-001"),
        )

        with self.assertRaises(ValueError):
            result.validate()

    def test_evidence_ids_must_be_a_tuple(self):
        result = self.make_result(
            evidence_ids=["evidence-001"],
        )

        with self.assertRaises(ValueError):
            result.validate()


if __name__ == "__main__":
    unittest.main()
