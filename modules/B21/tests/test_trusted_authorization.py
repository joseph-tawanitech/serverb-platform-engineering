import base64
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from tap_b20.policy import SecurityPolicy, SecurityRisk

from tap_b21.authorization import (
    AuthorizationGrant,
    authorization_grant_signing_bytes,
    compute_plan_digest,
)
from tap_b21.authorization_ledger import (
    GrantStatus,
    InMemoryAuthorizationLedger,
)
from tap_b21.contracts import (
    RemediationAction,
    RemediationPlan,
    TaskRequest,
)
from tap_b21.plan_router import RoutedAction
from tap_b21.trusted_authorization import (
    TrustedAuthorizationError,
    TrustedAuthorizationService,
)
from tap_b21.workflow import Workflow, WorkflowState


class TrustedAuthorizationTests(unittest.TestCase):

    def setUp(self):
        self.now = datetime(
            2026, 10, 29, 10, 0, tzinfo=timezone.utc
        )

        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

        self.task = TaskRequest(
            task_id="task-sec-001",
            incident_id="incident-sec-001",
            target="server-01",
            environment="lab",
            requested_by="sre-user",
            objective="Restore service",
        )

        self.action = RemediationAction(
            action_id="action-sec-001",
            channel="ansible",
            operation="restart_service",
            target="server-01",
            purpose="Restore service",
            expected_state="service_active",
            parameters={"service": "nginx"},
        )

        self.plan = RemediationPlan(
            plan_id="plan-sec-001",
            task_id=self.task.task_id,
            summary="Restore service",
            actions=(self.action,),
            verification_requirements=("service_active",),
        )

        self.routes = (
            RoutedAction(
                action_id=self.action.action_id,
                operation=self.action.operation,
                target=self.action.target,
                environment="lab",
                selected_channel="ansible",
            ),
        )

        self.policy = self.make_policy(
            allowed_operations=("restart_service",)
        )

        self.ledger = InMemoryAuthorizationLedger()
        self.grant = self.make_grant(
            self.task, self.plan, self.routes
        )
        self.ledger.register(self.grant.grant_id)

        self.service = TrustedAuthorizationService(
            policy=self.policy,
            trusted_public_keys={
                "trusted-authority": self.public_key
            },
            ledger=self.ledger,
        )

        self.workflow = self.make_pending_workflow(
            self.task.task_id
        )

    def make_policy(
        self,
        allowed_operations=(),
        review_operations=(),
        blocked_operations=(),
    ):
        return SecurityPolicy(
            policy_id="POL-B20-001",
            name="Server B Test Policy",
            version="1.0",
            environment="lab",
            authorized_assets=("server-01",),
            allowed_operations=allowed_operations,
            review_operations=review_operations,
            blocked_operations=blocked_operations,
            max_risk=SecurityRisk.LOW,
            enabled=True,
        )

    def make_pending_workflow(self, task_id):
        workflow = Workflow(task_id)
        workflow.transition(WorkflowState.INVESTIGATING)
        workflow.transition(WorkflowState.PLAN_PROPOSED)
        workflow.transition(WorkflowState.GOVERNANCE_PENDING)
        return workflow

    def make_grant(self, task, plan, routes, grant_id='grant-sec-001'):
        digest = compute_plan_digest(task, plan, routes)

        unsigned = AuthorizationGrant(
            grant_id=grant_id,
            task_id=task.task_id,
            plan_id=plan.plan_id,
            plan_digest=digest,
            environment=task.environment,
            approved_by="human-approver",
            issuer_id="trusted-authority",
            issued_at="2026-10-29T09:00:00+00:00",
            expires_at="2026-10-29T11:00:00+00:00",
            signing_algorithm="Ed25519",
            signature="temporary-placeholder",
        )

        signature = self.private_key.sign(
            authorization_grant_signing_bytes(unsigned)
        )

        return replace(
            unsigned,
            signature=base64.b64encode(signature).decode("ascii"),
        )

    def test_valid_authorization_moves_workflow_to_authorized(self):
        result = self.service.authorize(
            self.task,
            self.plan,
            self.routes,
            self.grant,
            self.workflow,
            now=self.now,
        )

        self.assertEqual(
            self.workflow.state,
            WorkflowState.AUTHORIZED,
        )
        self.assertEqual(
            self.workflow.authorization_grant_id,
            self.grant.grant_id,
        )
        self.assertEqual(result.approved_actions, 1)
        self.assertEqual(
            self.ledger.get_status(self.grant.grant_id),
            GrantStatus.CONSUMED,
        )

    def test_review_decision_does_not_authorize(self):
        review_action = replace(
            self.action,
            operation="configuration_change",
        )
        review_plan = replace(
            self.plan,
            actions=(review_action,),
        )
        review_routes = (
            RoutedAction(
                action_id=review_action.action_id,
                operation=review_action.operation,
                target=review_action.target,
                environment="lab",
                selected_channel="ansible",
            ),
        )

        review_grant = self.make_grant(
            self.task, review_plan, review_routes,
            grant_id='grant-sec-review-001',
        )
        self.ledger.register(review_grant.grant_id)

        review_service = TrustedAuthorizationService(
            policy=self.make_policy(
                review_operations=("configuration_change",)
            ),
            trusted_public_keys={
                "trusted-authority": self.public_key
            },
            ledger=self.ledger,
        )

        with self.assertRaises(TrustedAuthorizationError):
            review_service.authorize(
                self.task,
                review_plan,
                review_routes,
                review_grant,
                self.workflow,
                now=self.now,
            )

        self.assertEqual(
            self.workflow.state,
            WorkflowState.GOVERNANCE_PENDING,
        )
        self.assertEqual(
            self.ledger.get_status(review_grant.grant_id),
            GrantStatus.ACTIVE,
        )

    def test_blocked_operation_does_not_authorize(self):
        blocked_policy = self.make_policy(
            blocked_operations=("restart_service",)
        )

        blocked_service = TrustedAuthorizationService(
            policy=blocked_policy,
            trusted_public_keys={
                "trusted-authority": self.public_key
            },
            ledger=self.ledger,
        )

        with self.assertRaises(TrustedAuthorizationError):
            blocked_service.authorize(
                self.task,
                self.plan,
                self.routes,
                self.grant,
                self.workflow,
                now=self.now,
            )

        self.assertEqual(
            self.workflow.state,
            WorkflowState.GOVERNANCE_PENDING,
        )
        self.assertEqual(
            self.ledger.get_status(self.grant.grant_id),
            GrantStatus.ACTIVE,
        )

    def test_invalid_signature_does_not_authorize(self):
        forged = replace(
            self.grant,
            signature=base64.b64encode(
                b"x" * 64
            ).decode("ascii"),
        )

        with self.assertRaises(TrustedAuthorizationError):
            self.service.authorize(
                self.task,
                self.plan,
                self.routes,
                forged,
                self.workflow,
                now=self.now,
            )

        self.assertEqual(
            self.workflow.state,
            WorkflowState.GOVERNANCE_PENDING,
        )
        self.assertEqual(
            self.ledger.get_status(self.grant.grant_id),
            GrantStatus.ACTIVE,
        )

    def test_consumed_grant_cannot_authorize_another_workflow(self):
        self.service.authorize(
            self.task,
            self.plan,
            self.routes,
            self.grant,
            self.workflow,
            now=self.now,
        )

        second_workflow = self.make_pending_workflow(
            self.task.task_id
        )

        with self.assertRaises(TrustedAuthorizationError):
            self.service.authorize(
                self.task,
                self.plan,
                self.routes,
                self.grant,
                second_workflow,
                now=self.now,
            )

        self.assertEqual(
            second_workflow.state,
            WorkflowState.GOVERNANCE_PENDING,
        )

    def test_wrong_workflow_task_does_not_authorize(self):
        wrong_workflow = self.make_pending_workflow(
            "different-task"
        )

        with self.assertRaises(TrustedAuthorizationError):
            self.service.authorize(
                self.task,
                self.plan,
                self.routes,
                self.grant,
                wrong_workflow,
                now=self.now,
            )

        self.assertEqual(
            wrong_workflow.state,
            WorkflowState.GOVERNANCE_PENDING,
        )
        self.assertEqual(
            self.ledger.get_status(self.grant.grant_id),
            GrantStatus.ACTIVE,
        )


if __name__ == "__main__":
    unittest.main()
