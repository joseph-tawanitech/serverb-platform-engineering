import base64
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from tap_b21.authorization import (
    AuthorizationGrant,
    authorization_grant_signing_bytes,
    compute_plan_digest,
)
from tap_b21.adapter_contracts import (
    AdapterAuthorizationError,
    AdapterExecutionRequest,
    verify_adapter_authorization,
)
from tap_b21.contracts import (
    TaskRequest,
    RemediationAction,
    RemediationPlan,
)
from tap_b21.plan_router import RoutedAction


class AdapterAuthorizationTests(unittest.TestCase):

    def setUp(self):
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

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
            purpose="Restore service",
            expected_state="service_active",
            parameters={"service": "nginx"},
        )

        self.plan = RemediationPlan(
            plan_id="plan-adapter-001",
            task_id="task-adapter-001",
            summary="Restore service",
            actions=(self.action,),
            verification_requirements=("service_active",),
        )

        self.routes = (
            RoutedAction(
                action_id="action-adapter-001",
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

        self.request = AdapterExecutionRequest(
            task=self.task,
            plan=self.plan,
            action=self.action,
            routed_action=self.routes[0],
            routed_actions=self.routes,
            authorization_grant=self.grant,
        )

    def create_signed_grant(self):
        digest = compute_plan_digest(
            self.task,
            self.plan,
            self.routes,
        )

        unsigned = AuthorizationGrant(
            grant_id="grant-adapter-001",
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

    def verify(self, request=None, trusted_keys=None, now=None):
        return verify_adapter_authorization(
            request=request or self.request,
            trusted_public_keys=(
                self.trusted_keys if trusted_keys is None else trusted_keys
            ),
            now=self.now if now is None else now,
        )

    def test_valid_signed_grant_is_accepted(self):
        self.assertTrue(self.verify())

    def test_forged_signature_is_rejected(self):
        forged = replace(
            self.grant,
            signature=base64.b64encode(b"x" * 64).decode("ascii"),
        )

        request = replace(
            self.request,
            authorization_grant=forged,
        )

        with self.assertRaises(AdapterAuthorizationError):
            self.verify(request=request)

    def test_expired_grant_is_rejected(self):
        later = datetime(
            2026, 10, 29, 12, 0, tzinfo=timezone.utc
        )

        with self.assertRaises(AdapterAuthorizationError):
            self.verify(now=later)

    def test_unknown_issuer_is_rejected(self):
        with self.assertRaises(AdapterAuthorizationError):
            self.verify(trusted_keys={})

    def test_modified_plan_is_rejected(self):
        changed_action = replace(
            self.action,
            parameters={"service": "ssh"},
        )

        changed_plan = replace(
            self.plan,
            actions=(changed_action,),
        )

        request = replace(
            self.request,
            plan=changed_plan,
            action=changed_action,
        )

        with self.assertRaises(AdapterAuthorizationError):
            self.verify(request=request)

    def test_invalid_public_key_mapping_is_rejected(self):
        with self.assertRaises(AdapterAuthorizationError):
            self.verify(trusted_keys=[])

    def test_invalid_public_key_type_is_rejected(self):
        with self.assertRaises(AdapterAuthorizationError):
            self.verify(
                trusted_keys={"trusted-authority": "not-a-public-key"}
            )

    def test_invalid_request_is_rejected(self):
        with self.assertRaises(AdapterAuthorizationError):
            self.verify(request=object())


if __name__ == "__main__":
    unittest.main()
