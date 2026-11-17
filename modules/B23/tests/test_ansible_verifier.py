import json
import subprocess
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from tap_b21.adapter_contracts import (
    AdapterExecutionResult,
    ExecutionStatus,
)
from tap_b21.adapter_dispatcher import (
    ActionExecutionRecord,
    ActionExecutionStatus,
)
from tap_b22.ansible_adapter import AnsibleTarget
from tap_b23.ansible_verifier import AnsibleServiceVerifier
from tap_b23.contracts import VerificationStatus


def make_record(
    execution_status=ActionExecutionStatus.SUCCEEDED,
):
    now = datetime.now(timezone.utc)

    adapter_status = (
        ExecutionStatus.UNKNOWN
        if execution_status == ActionExecutionStatus.UNKNOWN
        else ExecutionStatus.SUCCEEDED
    )

    adapter_result = None

    if execution_status in {
        ActionExecutionStatus.SUCCEEDED,
        ActionExecutionStatus.UNKNOWN,
    }:
        adapter_result = AdapterExecutionResult(
            task_id="task-001",
            plan_id="plan-001",
            action_id="action-001",
            adapter_id="tap-b22-ansible",
            selected_channel="ansible",
            operation="restart_service",
            target="test-server",
            environment="test",
            status=adapter_status,
            started_at=now,
            completed_at=(
                now + timedelta(seconds=1)
                if adapter_status == ExecutionStatus.SUCCEEDED
                else None
            ),
            message="Ansible service restart requested.",
        )

    record = ActionExecutionRecord(
        dispatch_id="dispatch-001",
        attempt_id="attempt-001",
        attempt_number=1,
        task_id="task-001",
        plan_id="plan-001",
        action_id="action-001",
        adapter_id="tap-b22-ansible",
        selected_channel="ansible",
        grant_id="grant-001",
        status=execution_status,
        prepared_at=now - timedelta(seconds=2),
        resource_checked_at=now - timedelta(seconds=1),
        authorization_confirmed_at=now - timedelta(seconds=1),
        adapter_result=adapter_result,
    )
    record.validate()
    return record


def make_verifier(tmp_path, runner, *, service="nginx.service"):
    inventory = tmp_path / "inventory.ini"
    inventory.write_text("[servers]\ntest-host\n", encoding="utf-8")

    executable = tmp_path / "ansible"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)

    return AnsibleServiceVerifier(
        targets={
            "test-server": AnsibleTarget(
                inventory_path=inventory,
                host_alias="test-host",
            )
        },
        services={"test-server": service},
        ansible_executable=executable,
        runner=runner,
    )


def ansible_response(payload, *, returncode=0):
    return SimpleNamespace(
        returncode=returncode,
        stdout=f"test-host | SUCCESS => {json.dumps(payload)}\n",
        stderr="",
    )


def test_active_service_is_verified(tmp_path):
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return ansible_response(
            {"changed": False, "stdout": "active", "rc": 0}
        )

    verifier = make_verifier(tmp_path, runner)
    record = make_record()

    result = verifier.verify(record)

    assert result.status == VerificationStatus.VERIFIED
    assert result.dispatch_id == record.dispatch_id
    assert result.attempt_id == record.attempt_id
    assert result.execution_status == ActionExecutionStatus.SUCCEEDED
    assert result.evidence
    assert len(calls) == 1


def test_inactive_service_is_failed(tmp_path):
    def runner(command, **kwargs):
        return SimpleNamespace(
            returncode=2,
            stdout=(
                'test-host | FAILED! => '
                '{"changed": false, "stdout": "inactive", "rc": 3}\n'
            ),
            stderr="",
        )

    verifier = make_verifier(tmp_path, runner)
    result = verifier.verify(make_record())

    assert result.status == VerificationStatus.FAILED
    assert "inactive" in result.message.lower()


def test_unreachable_host_is_unverified(tmp_path):
    def runner(command, **kwargs):
        return SimpleNamespace(
            returncode=4,
            stdout=(
                'test-host | UNREACHABLE! => '
                '{"unreachable": true, "msg": "connection failed"}\n'
            ),
            stderr="",
        )

    verifier = make_verifier(tmp_path, runner)
    result = verifier.verify(make_record())

    assert result.status == VerificationStatus.UNVERIFIED


def test_timeout_is_unverified(tmp_path):
    def runner(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 30)

    verifier = make_verifier(tmp_path, runner)
    result = verifier.verify(make_record())

    assert result.status == VerificationStatus.UNVERIFIED
    assert "timed out" in result.message.lower()


def test_malformed_output_is_unverified(tmp_path):
    def runner(command, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout="unexpected Ansible output\n",
            stderr="",
        )

    verifier = make_verifier(tmp_path, runner)
    result = verifier.verify(make_record())

    assert result.status == VerificationStatus.UNVERIFIED


def test_command_uses_trusted_target_and_read_only_probe(tmp_path):
    captured = {}

    def runner(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return ansible_response(
            {"changed": False, "stdout": "active", "rc": 0}
        )

    verifier = make_verifier(tmp_path, runner)
    verifier.verify(make_record())

    command = captured["command"]
    kwargs = captured["kwargs"]

    assert command[0] == str(tmp_path / "ansible")
    assert "test-host" in command
    assert str(tmp_path / "inventory.ini") in command
    assert "ansible.builtin.command" in command
    args_index = command.index("--args")
    remote_args = json.loads(command[args_index + 1])

    assert remote_args["argv"] == [
        "systemctl",
        "is-active",
        "nginx.service",
    ]

    assert kwargs["shell"] is False
    assert kwargs["cwd"] == "/"
    assert kwargs["check"] is False
    assert kwargs["capture_output"] is True


def test_blocked_execution_is_skipped_without_running_ansible(tmp_path):
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        return ansible_response(
            {"changed": False, "stdout": "active", "rc": 0}
        )

    verifier = make_verifier(tmp_path, runner)
    record = make_record(ActionExecutionStatus.BLOCKED)

    result = verifier.verify(record)

    assert result.status == VerificationStatus.SKIPPED
    assert result.execution_status == ActionExecutionStatus.BLOCKED
    assert calls == []
