
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone

from tap_b21.adapter_dispatcher import (
    PreparedAction,
    prepare_action,
)
from tap_b21.adapter_registry import (
    AdapterNotFoundError,
    AdapterRegistry,
    AmbiguousAdapterError,
)
from tap_b21.authorization import AuthorizationGrant
from tap_b21.contracts import (
    RemediationAction,
    RemediationPlan,
    TaskRequest,
)
from tap_b21.plan_router import RoutedAction


class PreparationTestAdapter:
    """Test adapter that records calls but never executes infrastructure."""

    def __init__(self, adapter_id="test-kubernetes-adapter"):
        self._adapter_id = adapter_id
        self.validation_calls = 0
        self.execution_calls = 0

    @property
    def adapter_id(self):
        return self._adapter_id

    @property
    def supported_channels(self):
        return frozenset({"kubernetes"})

    @property
    def supported_operations(self):
        return frozenset({"restart_service"})

    def validate_execution_request(self, request):
        self.validation_calls += 1

    def execute_approved_request(self, request):
        self.execution_calls += 1
        raise AssertionError(
            "Preparation must not execute infrastructure changes"
        )


class TestAdapterPreparation(unittest.TestCase):

    def setUp(self):
        self.task = TaskRequest(
            task_id="task-preparation-001",
            incident_id="incident-preparation-001",
            target="server-01",
            environment="lab",
            requested_by="sre-user",
            objective="Restore service",
        )

        self.action = RemediationAction(
            action_id="action-preparation-001",
            channel="ansible",
            operation="restart_service",
            target="server-01",
            purpose="Restore Nginx",
            expected_state="service_active",
            parameters={"service": "nginx"},
        )

        self.plan = RemediationPlan(
            plan_id="plan-preparation-001",
            task_id="task-preparation-001",
            summary="Restore Nginx",
            actions=(self.action,),
            verification_requirements=("service_active",),
        )

        # The router selects Kubernetes even though the original
        # proposed action channel is Ansible.
        self.route = RoutedAction(
            action_id="action-preparation-001",
            operation="restart_service",
            target="server-01",
            environment="lab",
            selected_channel="kubernetes",
        )

        self.routes = (self.route,)

        self.grant = AuthorizationGrant(
            grant_id="grant-preparation-001",
            task_id="task-preparation-001",
            plan_id="plan-preparation-001",
            plan_digest="a" * 64,
            environment="lab",
            approved_by="human-approver",
            issuer_id="trusted-authority",
            issued_at="2026-10-29T10:00:00+00:00",
            expires_at="2026-10-29T11:00:00+00:00",
            signing_algorithm="Ed25519",
            signature="placeholder-signature",
        )

        self.registry = AdapterRegistry()
        self.adapter = PreparationTestAdapter()
        self.registry.register(self.adapter)

        self.prepared_at = datetime(
            2026, 11, 13, 12, 0, 0, tzinfo=timezone.utc
        )

    def prepare(self, **overrides):
        arguments = {
            "registry": self.registry,
            "task": self.task,
            "plan": self.plan,
            "action": self.action,
            "routed_action": self.route,
            "routed_actions": self.routes,
            "authorization_grant": self.grant,
            "prepared_at": self.prepared_at,
        }
        arguments.update(overrides)
        return prepare_action(**arguments)

    def test_successful_preparation_returns_prepared_action(self):
        prepared = self.prepare()

        self.assertIsInstance(prepared, PreparedAction)
        self.assertEqual(
            prepared.adapter_id,
            "test-kubernetes-adapter",
        )
        self.assertIs(prepared.adapter, self.adapter)
        self.assertEqual(
            prepared.request.task.task_id,
            self.task.task_id,
        )
        self.assertEqual(prepared.prepared_at, self.prepared_at)

    def test_preparation_uses_router_selected_channel(self):
        self.assertEqual(self.action.channel, "ansible")
        self.assertEqual(
            self.route.selected_channel,
            "kubernetes",
        )

        prepared = self.prepare()

        self.assertEqual(
            prepared.request.routed_action.selected_channel,
            "kubernetes",
        )
        self.assertIs(prepared.adapter, self.adapter)

    def test_missing_adapter_is_rejected(self):
        empty_registry = AdapterRegistry()

        with self.assertRaises(AdapterNotFoundError):
            self.prepare(registry=empty_registry)

    def test_ambiguous_adapter_is_rejected(self):
        second_adapter = PreparationTestAdapter(
            adapter_id="second-kubernetes-adapter"
        )
        self.registry.register(second_adapter)

        with self.assertRaises(AmbiguousAdapterError):
            self.prepare()

    def test_invalid_request_is_rejected_before_adapter_resolution(self):
        empty_registry = AdapterRegistry()

        wrong_plan = replace(
            self.plan,
            task_id="another-task",
        )

        with self.assertRaises(ValueError):
            self.prepare(
                registry=empty_registry,
                plan=wrong_plan,
            )

    def test_adapter_validation_is_not_called_during_preparation(self):
        self.prepare()

        self.assertEqual(self.adapter.validation_calls, 0)

    def test_adapter_execution_is_not_called_during_preparation(self):
        self.prepare()

        self.assertEqual(self.adapter.execution_calls, 0)

    def test_preparation_retains_authorization_grant(self):
        prepared = self.prepare()

        self.assertIs(
            prepared.request.authorization_grant,
            self.grant,
        )

    def test_injected_preparation_timestamp_is_preserved(self):
        prepared = self.prepare()

        self.assertEqual(
            prepared.prepared_at,
            self.prepared_at,
        )

    def test_naive_preparation_timestamp_is_rejected(self):
        naive_timestamp = datetime(2026, 11, 13, 12, 0, 0)

        with self.assertRaises(ValueError):
            self.prepare(prepared_at=naive_timestamp)

    def test_prepared_action_is_immutable(self):
        prepared = self.prepare()

        with self.assertRaises(FrozenInstanceError):
            prepared.adapter_id = "changed-adapter"


if __name__ == "__main__":
    unittest.main()
