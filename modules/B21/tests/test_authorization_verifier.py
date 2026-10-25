import base64
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from tap_b21.authorization import (
    AuthorizationGrant,
    AuthorizationVerificationError,
    authorization_grant_signing_bytes,
    compute_plan_digest,
    verify_authorization_grant,
)
from tap_b21.contracts import (
    TaskRequest,
    RemediationAction,
    RemediationPlan,
)
from tap_b21.plan_router import RoutedAction


class AuthorizationVerifierTests(unittest.TestCase):

    def setUp(self):
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
            task_id="task-sec-001",
            summary="Restore service",
            actions=(self.action,),
            verification_requirements=("service_active",),
        )

        self.routes = (
            RoutedAction(
                action_id="action-sec-001",
                operation="restart_service",
                target="server-01",
                environment="lab",
                selected_channel="ansible",
            ),
        )

        self.now = datetime(
            2026, 10, 29, 10, 0, tzinfo=timezone.utc
        )

        self.grant = self.create_signed_grant()

        self.trusted_keys = {
            "trusted-authority": self.public_key,
        }

    def create_signed_grant(self):
        digest = compute_plan_digest(
            self.task, self.plan, self.routes
        )

        unsigned = AuthorizationGrant(
            grant_id="grant-sec-001",
            task_id=self.task.task_id,
            plan_id=self.plan.plan_id,
            plan_digest=digest,
            environment=self.task.environment,
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

    def test_valid_signed_grant_is_accepted(self):
        result = verify_authorization_grant(
            self.grant,
            self.task,
            self.plan,
            self.routes,
            self.trusted_keys,
            now=self.now,
        )

        self.assertTrue(result)

    def test_unknown_issuer_is_rejected(self):
        with self.assertRaises(AuthorizationVerificationError):
            verify_authorization_grant(
                self.grant,
                self.task,
                self.plan,
                self.routes,
                {},
                now=self.now,
            )

    def test_forged_signature_is_rejected(self):
        forged = replace(
            self.grant,
            signature=base64.b64encode(b"x" * 64).decode("ascii"),
        )

        with self.assertRaises(AuthorizationVerificationError):
            verify_authorization_grant(
                forged,
                self.task,
                self.plan,
                self.routes,
                self.trusted_keys,
                now=self.now,
            )

    def test_modified_grant_is_rejected(self):
        modified = replace(
            self.grant,
            approved_by="different-person",
        )

        with self.assertRaises(AuthorizationVerificationError):
            verify_authorization_grant(
                modified,
                self.task,
                self.plan,
                self.routes,
                self.trusted_keys,
                now=self.now,
            )

    def test_modified_plan_is_rejected(self):
        changed_action = replace(
            self.action,
            parameters={"service": "ssh"},
        )

        changed_plan = replace(
            self.plan,
            actions=(changed_action,),
        )

        with self.assertRaises(AuthorizationVerificationError):
            verify_authorization_grant(
                self.grant,
                self.task,
                changed_plan,
                self.routes,
                self.trusted_keys,
                now=self.now,
            )

    def test_expired_grant_is_rejected(self):
        later = datetime(
            2026, 10, 29, 12, 0, tzinfo=timezone.utc
        )

        with self.assertRaises(AuthorizationVerificationError):
            verify_authorization_grant(
                self.grant,
                self.task,
                self.plan,
                self.routes,
                self.trusted_keys,
                now=later,
            )


if __name__ == "__main__":
    unittest.main()
