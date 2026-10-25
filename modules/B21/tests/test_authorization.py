import unittest
from dataclasses import replace

from tap_b21.authorization import (
    AuthorizationGrant,
    compute_plan_digest,
)
from tap_b21.contracts import TaskRequest, RemediationAction, RemediationPlan
from tap_b21.plan_router import RoutedAction


class AuthorizationTests(unittest.TestCase):

    def setUp(self):
        self.task = TaskRequest(
            task_id="task-auth-001",
            incident_id="incident-auth-001",
            target="server-01",
            environment="lab",
            requested_by="sre-user",
            objective="Restore service",
        )

        self.action = RemediationAction(
            action_id="action-auth-001",
            channel="ansible",
            operation="restart_service",
            target="server-01",
            purpose="Restore service",
            expected_state="service_active",
            parameters={"service": "nginx"},
        )

        self.plan = RemediationPlan(
            plan_id="plan-auth-001",
            task_id="task-auth-001",
            summary="Restore service",
            actions=(self.action,),
            verification_requirements=("service_active",),
        )

        self.routes = (
            RoutedAction(
                action_id="action-auth-001",
                operation="restart_service",
                target="server-01",
                environment="lab",
                selected_channel="ansible",
            ),
        )

    def test_digest_is_deterministic(self):
        first = compute_plan_digest(
            self.task, self.plan, self.routes
        )
        second = compute_plan_digest(
            self.task, self.plan, self.routes
        )

        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_changed_action_parameters_change_digest(self):
        changed_action = replace(
            self.action,
            parameters={"service": "ssh"},
        )
        changed_plan = replace(
            self.plan,
            actions=(changed_action,),
        )

        original = compute_plan_digest(
            self.task, self.plan, self.routes
        )
        changed = compute_plan_digest(
            self.task, changed_plan, self.routes
        )

        self.assertNotEqual(original, changed)

    def test_changed_execution_channel_changes_digest(self):
        changed_routes = (
            replace(self.routes[0], selected_channel="kubernetes"),
        )

        original = compute_plan_digest(
            self.task, self.plan, self.routes
        )
        changed = compute_plan_digest(
            self.task, self.plan, changed_routes
        )

        self.assertNotEqual(original, changed)

    def test_changed_target_changes_digest(self):
        changed_task = replace(
            self.task,
            target="server-02",
        )

        original = compute_plan_digest(
            self.task, self.plan, self.routes
        )
        changed = compute_plan_digest(
            changed_task, self.plan, self.routes
        )

        self.assertNotEqual(original, changed)

    def test_plan_task_mismatch_is_rejected(self):
        changed_plan = replace(
            self.plan,
            task_id="another-task",
        )

        with self.assertRaises(ValueError):
            compute_plan_digest(
                self.task, changed_plan, self.routes
            )

    def test_missing_route_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_plan_digest(
                self.task, self.plan, ()
            )

    def test_invalid_grant_digest_is_rejected(self):
        grant = AuthorizationGrant(
            grant_id="grant-001",
            task_id="task-auth-001",
            plan_id="plan-auth-001",
            plan_digest="not-a-valid-digest",
            environment="lab",
            approved_by="human-approver",
            issuer_id="trusted-authority",
            issued_at="2026-10-29T10:00:00+00:00",
            expires_at="2026-10-29T11:00:00+00:00",
            signing_algorithm="Ed25519",
            signature="placeholder-signature",
        )

        with self.assertRaises(ValueError):
            grant.validate()

    def test_grant_requires_timezone_aware_timestamps(self):
        grant = AuthorizationGrant(
            grant_id="grant-001",
            task_id="task-auth-001",
            plan_id="plan-auth-001",
            plan_digest="a" * 64,
            environment="lab",
            approved_by="human-approver",
            issuer_id="trusted-authority",
            issued_at="2026-10-29T10:00:00",
            expires_at="2026-10-29T11:00:00+00:00",
            signing_algorithm="Ed25519",
            signature="placeholder-signature",
        )

        with self.assertRaises(ValueError):
            grant.validate()


if __name__ == "__main__":
    unittest.main()
