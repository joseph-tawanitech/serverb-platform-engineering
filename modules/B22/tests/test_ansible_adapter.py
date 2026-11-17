"""Tests for the TAP B22 Ansible adapter."""

import base64
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from tap_b21.adapter_contracts import (
    AdapterAuthorizationError,
    AdapterExecutionRequest,
    ExecutionStatus,
)
from tap_b21.authorization import (
    AuthorizationGrant,
    authorization_grant_signing_bytes,
    compute_plan_digest,
)
from tap_b21.contracts import (
    RemediationAction,
    RemediationPlan,
    TaskRequest,
)
from tap_b21.plan_router import RoutedAction

from tap_b22.ansible_adapter import (
    AnsibleAdapter,
    AnsibleAdapterError,
    AnsibleExecutionDisabledError,
    AnsibleTarget,
    AnsibleTargetError,
)


class AnsibleAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.root = Path(self.temp.name)
        self.inventory = self.root / "inventory.ini"
        self.playbook = self.root / "restart_service.yml"
        self.executable = self.root / "ansible-playbook"
        self.workdir = self.root / "work"

        self.inventory.write_text(
            "[application]\napp01 ansible_host=127.0.0.1\n",
            encoding="utf-8",
        )
        self.playbook.write_text(
            "---\n- name: Restart approved service\n  hosts: all\n",
            encoding="utf-8",
        )
        self.executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.executable.chmod(0o755)
        self.workdir.mkdir()

        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.now = datetime.now(timezone.utc)

        self.task = TaskRequest(
            task_id="task-ansible-001",
            incident_id="incident-ansible-001",
            target="server-b-lab",
            environment="lab",
            requested_by="sre-user",
            objective="Restart an approved service",
        )

        self.action = RemediationAction(
            action_id="action-ansible-001",
            channel="ansible",
            operation="restart_service",
            target="server-b-lab",
            purpose="Restart an approved service",
            expected_state="service_active",
            parameters={},
        )

        self.plan = RemediationPlan(
            plan_id="plan-ansible-001",
            task_id=self.task.task_id,
            summary="Restart approved service",
            actions=(self.action,),
            verification_requirements=("service_active",),
        )

        self.route = RoutedAction(
            action_id=self.action.action_id,
            operation=self.action.operation,
            target=self.action.target,
            environment=self.task.environment,
            selected_channel="ansible",
        )
        self.routes = (self.route,)

        self.grant = self.make_grant()
        self.request = AdapterExecutionRequest(
            task=self.task,
            plan=self.plan,
            action=self.action,
            routed_action=self.route,
            routed_actions=self.routes,
            authorization_grant=self.grant,
        )

        self.runner_calls = []

    def make_grant(self):
        digest = compute_plan_digest(
            self.task,
            self.plan,
            self.routes,
        )

        unsigned = AuthorizationGrant(
            grant_id="grant-ansible-001",
            task_id=self.task.task_id,
            plan_id=self.plan.plan_id,
            plan_digest=digest,
            environment=self.task.environment,
            approved_by="human-approver",
            issuer_id="trusted-authority",
            issued_at=(self.now - timedelta(minutes=1)).isoformat(),
            expires_at=(self.now + timedelta(hours=1)).isoformat(),
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

    def fake_runner(self, command, **kwargs):
        self.runner_calls.append((command, kwargs))
        return SimpleNamespace(returncode=0)

    def make_adapter(
        self,
        *,
        execution_enabled=False,
        targets=None,
        runner=None,
    ):
        if targets is None:
            targets = {
                "server-b-lab": AnsibleTarget(
                    inventory_path=self.inventory,
                    host_alias="app01",
                )
            }

        return AnsibleAdapter(
            trusted_public_keys={
                "trusted-authority": self.public_key,
            },
            targets=targets,
            playbooks={
                "restart_service": self.playbook,
            },
            working_directory=self.workdir,
            ansible_playbook_executable=self.executable,
            execution_enabled=execution_enabled,
            timeout_seconds=10,
            runner=runner or self.fake_runner,
        )

    def test_adapter_exposes_expected_contract(self):
        adapter = self.make_adapter(execution_enabled=True)

        self.assertEqual(adapter.adapter_id, "tap-b22-ansible")
        self.assertEqual(adapter.supported_channels, frozenset({"ansible"}))
        self.assertEqual(
            adapter.supported_operations,
            frozenset({"restart_service"}),
        )

    def test_valid_signed_request_passes_validation(self):
        adapter = self.make_adapter(execution_enabled=True)

        adapter.validate_execution_request(self.request)

        self.assertEqual(self.runner_calls, [])

    def test_execution_is_disabled_by_default(self):
        adapter = self.make_adapter()

        with self.assertRaises(AnsibleExecutionDisabledError):
            adapter.validate_execution_request(self.request)

        self.assertEqual(self.runner_calls, [])

    def test_unknown_target_is_rejected(self):
        adapter = self.make_adapter(
            execution_enabled=True,
            targets={
                "another-target": AnsibleTarget(
                    inventory_path=self.inventory,
                    host_alias="app01",
                )
            },
        )

        with self.assertRaises(AnsibleTargetError):
            adapter.validate_execution_request(self.request)

        self.assertEqual(self.runner_calls, [])

    def test_ai_supplied_parameters_are_rejected(self):
        adapter = self.make_adapter(execution_enabled=True)

        modified_action = replace(
            self.action,
            parameters={"service": "untrusted-service"},
        )
        modified_plan = replace(
            self.plan,
            actions=(modified_action,),
        )
        modified_request = replace(
            self.request,
            action=modified_action,
            plan=modified_plan,
        )

        with self.assertRaises(AnsibleAdapterError):
            adapter.validate_execution_request(modified_request)

        self.assertEqual(self.runner_calls, [])

    def test_invalid_signature_is_rejected_before_runner(self):
        adapter = self.make_adapter(execution_enabled=True)

        forged_grant = replace(
            self.grant,
            signature=base64.b64encode(b"x" * 64).decode("ascii"),
        )
        forged_request = replace(
            self.request,
            authorization_grant=forged_grant,
        )

        with self.assertRaises(AdapterAuthorizationError):
            adapter.validate_execution_request(forged_request)

        self.assertEqual(self.runner_calls, [])

    def test_successful_execution_uses_only_trusted_paths_and_target(self):
        adapter = self.make_adapter(execution_enabled=True)

        result = adapter.execute_approved_request(self.request)

        self.assertEqual(result.status, ExecutionStatus.SUCCEEDED)
        self.assertEqual(len(self.runner_calls), 1)

        command, kwargs = self.runner_calls[0]

        self.assertEqual(command[0], str(self.executable))
        self.assertIn(str(self.inventory), command)
        self.assertIn(str(self.playbook), command)
        self.assertIn("--limit", command)
        self.assertEqual(command[command.index("--limit") + 1], "app01")

        self.assertEqual(kwargs["cwd"], str(self.workdir))
        self.assertFalse(kwargs["shell"])
        self.assertTrue(kwargs["capture_output"])
        self.assertEqual(kwargs["timeout"], 10)

        self.assertIn(
            "Independent verification is still required",
            result.message,
        )

    def test_nonzero_exit_returns_failed(self):
        def failed_runner(command, **kwargs):
            return SimpleNamespace(returncode=2)

        adapter = self.make_adapter(
            execution_enabled=True,
            runner=failed_runner,
        )

        result = adapter.execute_approved_request(self.request)

        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertIn("may have partially changed", result.message)

    def test_process_timeout_returns_timed_out(self):
        def timeout_runner(command, **kwargs):
            raise subprocess.TimeoutExpired(
                cmd=command,
                timeout=kwargs["timeout"],
            )

        adapter = self.make_adapter(
            execution_enabled=True,
            runner=timeout_runner,
        )

        result = adapter.execute_approved_request(self.request)

        self.assertEqual(result.status, ExecutionStatus.TIMED_OUT)
        self.assertIsNone(result.completed_at)
        self.assertIn("independent verification", result.message)

    def test_unexpected_runner_exception_returns_unknown(self):
        def broken_runner(command, **kwargs):
            raise OSError("simulated process launch failure")

        adapter = self.make_adapter(
            execution_enabled=True,
            runner=broken_runner,
        )

        result = adapter.execute_approved_request(self.request)

        self.assertEqual(result.status, ExecutionStatus.UNKNOWN)
        self.assertIsNone(result.completed_at)
        self.assertIn("independent verification", result.message)


if __name__ == "__main__":
    unittest.main()
