"""Read-only independent verification for TAP Ansible service restarts."""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path

from tap_b21.adapter_dispatcher import (
    ActionExecutionRecord,
    ActionExecutionStatus,
)
from tap_b22.ansible_adapter import AnsibleTarget

from .contracts import (
    VerificationResult,
    VerificationStatus,
    new_verification_id,
)


_SERVICE_NAME = re.compile(r"^[A-Za-z0-9_.@:-]+\.service$")


class AnsibleServiceVerifier:
    """Verify service state using a trusted, read-only Ansible command."""

    def __init__(
        self,
        *,
        targets: Mapping[str, AnsibleTarget],
        services: Mapping[str, str],
        ansible_executable: str | Path = "/usr/bin/ansible",
        timeout_seconds: float = 30.0,
        runner: Callable = subprocess.run,
    ) -> None:
        if not isinstance(targets, Mapping) or not targets:
            raise ValueError("targets must be a non-empty mapping")

        if not isinstance(services, Mapping) or not services:
            raise ValueError("services must be a non-empty mapping")

        if set(targets) != set(services):
            raise ValueError(
                "services must define exactly the configured target IDs"
            )

        validated_targets: dict[str, AnsibleTarget] = {}

        for target_id, target in targets.items():
            if not isinstance(target_id, str) or not target_id.strip():
                raise ValueError("target IDs must be non-empty strings")

            if not isinstance(target, AnsibleTarget):
                raise TypeError(
                    f"target {target_id!r} must be an AnsibleTarget"
                )

            target.validate()
            inventory = Path(target.inventory_path).expanduser().resolve(
                strict=True
            )

            if not inventory.is_file():
                raise ValueError(
                    f"inventory for target {target_id!r} must be a file"
                )

            validated_targets[target_id] = AnsibleTarget(
                inventory_path=inventory,
                host_alias=target.host_alias,
            )

        validated_services: dict[str, str] = {}

        for target_id, service in services.items():
            if (
                not isinstance(service, str)
                or not _SERVICE_NAME.fullmatch(service)
            ):
                raise ValueError(
                    f"service for target {target_id!r} must be a "
                    "trusted systemd .service unit name"
                )

            validated_services[target_id] = service

        executable_path = Path(ansible_executable).expanduser()

        if not executable_path.is_absolute():
            raise ValueError("ansible_executable must be an absolute path")

        executable_path = executable_path.resolve(strict=True)

        if not executable_path.is_file() or not os.access(
            executable_path, os.X_OK
        ):
            raise ValueError("ansible_executable must be executable")

        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be positive")

        if not callable(runner):
            raise TypeError("runner must be callable")

        self._targets = validated_targets
        self._services = validated_services
        self._executable = executable_path
        self._timeout_seconds = float(timeout_seconds)
        self._runner = runner

    def verify(self, record: ActionExecutionRecord) -> VerificationResult:
        """Check the configured service without changing remote state."""
        if not isinstance(record, ActionExecutionRecord):
            raise TypeError("record must be an ActionExecutionRecord")

        record.validate()
        started_at = datetime.now(timezone.utc)

        if record.status not in {
            ActionExecutionStatus.SUCCEEDED,
            ActionExecutionStatus.UNKNOWN,
        }:
            return self._result(
                record=record,
                status=VerificationStatus.SKIPPED,
                started_at=started_at,
                message="Execution status does not require reconciliation.",
            )

        adapter_result = record.adapter_result

        if adapter_result is None:
            return self._result(
                record=record,
                status=VerificationStatus.UNVERIFIED,
                started_at=started_at,
                message="No adapter result is available for verification.",
            )

        if (
            record.selected_channel != "ansible"
            or adapter_result.selected_channel != "ansible"
            or adapter_result.operation != "restart_service"
        ):
            return self._result(
                record=record,
                status=VerificationStatus.SKIPPED,
                started_at=started_at,
                message="Record is not a supported Ansible service restart.",
            )

        target_id = adapter_result.target
        target = self._targets.get(target_id)
        service = self._services.get(target_id)

        if target is None or service is None:
            return self._result(
                record=record,
                status=VerificationStatus.UNVERIFIED,
                started_at=started_at,
                message="Target is not present in trusted verifier configuration.",
            )

        command = [
            str(self._executable),
            target.host_alias,
            "--inventory",
            str(target.inventory_path),
            "--module-name",
            "ansible.builtin.command",
            "--args",
            json.dumps(
                {"argv": ["systemctl", "is-active", service]},
                separators=(",", ":"),
            ),
            "--one-line",
            "--forks",
            "1",
        ]

        environment = {
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "HOME": os.environ.get("HOME", "/"),
            "LANG": "C.UTF-8",
            "ANSIBLE_NOCOLOR": "1",
            "ANSIBLE_HOST_KEY_CHECKING": "True",
        }

        ssh_auth_sock = os.environ.get("SSH_AUTH_SOCK")
        if ssh_auth_sock:
            environment["SSH_AUTH_SOCK"] = ssh_auth_sock

        try:
            completed = self._runner(
                command,
                cwd="/",
                env=environment,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                check=False,
                shell=False,
            )

            return_code = completed.returncode
            stdout = completed.stdout

            if not isinstance(return_code, int) or not isinstance(stdout, str):
                raise ValueError("Ansible returned an invalid process result")

            result_line = next(
                (
                    line
                    for line in stdout.splitlines()
                    if line.startswith(f"{target.host_alias} ")
                    and "=>" in line
                ),
                None,
            )

            if result_line is None:
                raise ValueError("Ansible returned no result for the target")

            payload = result_line.split("=>", 1)[1].strip()
            remote_result = json.loads(payload)

            if not isinstance(remote_result, dict):
                raise ValueError("Ansible returned an invalid result payload")

            state = remote_result.get("stdout", "").strip().lower()
            remote_rc = remote_result.get("rc")

        except subprocess.TimeoutExpired:
            return self._result(
                record=record,
                status=VerificationStatus.UNVERIFIED,
                started_at=started_at,
                message="Ansible service-state verification timed out.",
            )

        except Exception as exc:
            return self._result(
                record=record,
                status=VerificationStatus.UNVERIFIED,
                started_at=started_at,
                message=(
                    "Ansible service-state result was inconclusive: "
                    f"{type(exc).__name__}."
                ),
            )

        evidence = (
            f"Read-only systemd probe: host={target.host_alias}, "
            f"service={service}, state={state or 'unknown'}, "
            f"remote_rc={remote_rc!r}, ansible_rc={return_code}.",
        )

        if (
            return_code == 0
            and remote_result.get("failed") is not True
            and remote_result.get("unreachable") is not True
            and remote_rc == 0
            and state == "active"
        ):
            return self._result(
                record=record,
                status=VerificationStatus.VERIFIED,
                started_at=started_at,
                evidence=evidence,
                message="The configured systemd service is independently confirmed active.",
            )

        if (
            remote_result.get("unreachable") is not True
            and remote_rc != 0
            and state in {"inactive", "failed"}
        ):
            return self._result(
                record=record,
                status=VerificationStatus.FAILED,
                started_at=started_at,
                evidence=evidence,
                message="The configured systemd service is confirmed inactive or failed.",
            )

        return self._result(
            record=record,
            status=VerificationStatus.UNVERIFIED,
            started_at=started_at,
            evidence=evidence,
            message="The service state could not be conclusively verified.",
        )

    @staticmethod
    def _result(
        *,
        record: ActionExecutionRecord,
        status: VerificationStatus,
        started_at: datetime,
        message: str,
        evidence: tuple[str, ...] = (),
    ) -> VerificationResult:
        now = datetime.now(timezone.utc)

        result = VerificationResult(
            verification_id=new_verification_id(),
            dispatch_id=record.dispatch_id,
            attempt_id=record.attempt_id,
            task_id=record.task_id,
            plan_id=record.plan_id,
            action_id=record.action_id,
            selected_channel=record.selected_channel,
            execution_status=record.status,
            status=status,
            started_at=started_at,
            completed_at=now,
            evidence=evidence,
            message=message,
        )
        result.validate()
        return result
