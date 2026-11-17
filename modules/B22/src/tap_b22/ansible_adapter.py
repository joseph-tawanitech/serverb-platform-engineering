"""Controlled Ansible execution adapter for TAP B22.

Only trusted, preconfigured playbooks and inventory targets may execute.
Execution is disabled by default. B23 must independently verify outcomes.
"""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from tap_b21.adapter_contracts import (
    AdapterAuthorizationError,
    AdapterExecutionRequest,
    AdapterExecutionResult,
    ExecutionStatus,
    RemediationAdapter,
    verify_adapter_authorization,
)


class AnsibleAdapterError(RuntimeError):
    """Base error for Ansible adapter failures."""


class AnsibleTargetError(AnsibleAdapterError):
    """Raised when a target is not present in trusted configuration."""


class AnsibleExecutionDisabledError(AnsibleAdapterError):
    """Raised when Ansible execution has not been explicitly enabled."""


_HOST_ALIAS = re.compile(r"^[A-Za-z0-9_.-]+$")


def _trusted_file(value: str | Path, field_name: str) -> Path:
    """Resolve and validate a trusted configuration file."""
    if not isinstance(value, (str, Path)):
        raise TypeError(f"{field_name} must be a path")

    path = Path(value).expanduser()

    if not path.is_absolute():
        raise ValueError(f"{field_name} must be an absolute path")

    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"{field_name} does not exist") from exc

    if not resolved.is_file():
        raise ValueError(f"{field_name} must be a regular file")

    return resolved


@dataclass(frozen=True)
class AnsibleTarget:
    """Trusted inventory and host alias for one TAP target."""

    inventory_path: str | Path
    host_alias: str

    def validate(self) -> None:
        _trusted_file(self.inventory_path, "inventory_path")

        if (
            not isinstance(self.host_alias, str)
            or not _HOST_ALIAS.fullmatch(self.host_alias)
        ):
            raise ValueError(
                "host_alias must be a single trusted inventory alias"
            )


class AnsibleAdapter(RemediationAdapter):
    """Execute a narrow set of preconfigured Ansible operations."""

    _ADAPTER_ID = "tap-b22-ansible"
    _CHANNELS = frozenset({"ansible"})
    _OPERATIONS = frozenset({"restart_service"})

    def __init__(
        self,
        *,
        trusted_public_keys: Mapping[str, Ed25519PublicKey],
        targets: Mapping[str, AnsibleTarget],
        playbooks: Mapping[str, str | Path],
        working_directory: str | Path,
        ansible_playbook_executable: str | Path = "/usr/bin/ansible-playbook",
        execution_enabled: bool = False,
        timeout_seconds: float = 300.0,
        runner: Callable = subprocess.run,
    ) -> None:
        if not isinstance(trusted_public_keys, Mapping) or not trusted_public_keys:
            raise ValueError("trusted_public_keys must be a non-empty mapping")

        for issuer_id, public_key in trusted_public_keys.items():
            if not isinstance(issuer_id, str) or not issuer_id.strip():
                raise ValueError("trusted issuer IDs must be non-empty strings")
            if not isinstance(public_key, Ed25519PublicKey):
                raise TypeError(
                    f"trusted key for {issuer_id!r} must be an Ed25519 public key"
                )

        if not isinstance(targets, Mapping) or not targets:
            raise ValueError("targets must be a non-empty mapping")

        validated_targets: dict[str, AnsibleTarget] = {}

        for target_id, target in targets.items():
            if not isinstance(target_id, str) or not target_id.strip():
                raise ValueError("target IDs must be non-empty strings")
            if not isinstance(target, AnsibleTarget):
                raise TypeError(
                    f"target {target_id!r} must be an AnsibleTarget"
                )

            target.validate()
            validated_targets[target_id] = AnsibleTarget(
                inventory_path=_trusted_file(
                    target.inventory_path, "inventory_path"
                ),
                host_alias=target.host_alias,
            )

        if not isinstance(playbooks, Mapping) or not playbooks:
            raise ValueError("playbooks must be a non-empty mapping")

        unsupported = set(playbooks) - self._OPERATIONS
        if unsupported:
            raise ValueError(
                f"unsupported configured Ansible operations: {sorted(unsupported)}"
            )

        validated_playbooks = {
            operation: _trusted_file(path, f"playbook for {operation}")
            for operation, path in playbooks.items()
        }

        if not isinstance(execution_enabled, bool):
            raise TypeError("execution_enabled must be a boolean")

        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be positive")

        if not callable(runner):
            raise TypeError("runner must be callable")

        executable = _trusted_file(
            ansible_playbook_executable,
            "ansible_playbook_executable",
        )

        if not os.access(executable, os.X_OK):
            raise ValueError("ansible_playbook_executable is not executable")

        if not isinstance(working_directory, (str, Path)):
            raise TypeError("working_directory must be a path")

        workdir = Path(working_directory).expanduser()

        if not workdir.is_absolute():
            raise ValueError("working_directory must be an absolute path")

        try:
            workdir = workdir.resolve(strict=True)
        except OSError as exc:
            raise ValueError("working_directory does not exist") from exc

        if not workdir.is_dir():
            raise ValueError("working_directory must be a directory")

        self._trusted_public_keys = dict(trusted_public_keys)
        self._targets = validated_targets
        self._playbooks = validated_playbooks
        self._working_directory = workdir
        self._executable = executable
        self._execution_enabled = execution_enabled
        self._timeout_seconds = float(timeout_seconds)
        self._runner = runner

    @property
    def adapter_id(self) -> str:
        return self._ADAPTER_ID

    @property
    def supported_channels(self) -> frozenset[str]:
        return self._CHANNELS

    @property
    def supported_operations(self) -> frozenset[str]:
        return self._OPERATIONS

    def validate_execution_request(
        self,
        request: AdapterExecutionRequest,
    ) -> None:
        """Validate operation, trusted target and signed authorization."""

        if not isinstance(request, AdapterExecutionRequest):
            raise ValueError("request must be an AdapterExecutionRequest")

        request.validate()

        action = request.action
        route = request.routed_action

        if action.channel != "ansible" or route.selected_channel != "ansible":
            raise AnsibleAdapterError("request is not routed to Ansible")

        if action.operation not in self._OPERATIONS:
            raise AnsibleAdapterError(
                f"unsupported Ansible operation: {action.operation}"
            )

        if action.operation not in self._playbooks:
            raise AnsibleAdapterError(
                "operation has no trusted configured playbook"
            )

        if action.target not in self._targets:
            raise AnsibleTargetError(
                "requested target is not present in trusted configuration"
            )

        # Initial operation accepts no AI-supplied parameters.
        if action.parameters:
            raise AnsibleAdapterError(
                "restart_service does not accept action parameters"
            )

        try:
            verified = verify_adapter_authorization(
                request=request,
                trusted_public_keys=self._trusted_public_keys,
            )
        except AdapterAuthorizationError:
            raise

        if verified is not True:
            raise AdapterAuthorizationError(
                "authorization grant was not verified"
            )

        if not self._execution_enabled:
            raise AnsibleExecutionDisabledError(
                "Ansible execution is disabled; explicitly enable it "
                "in trusted deployment configuration"
            )

    def execute_approved_request(
        self,
        request: AdapterExecutionRequest,
    ) -> AdapterExecutionResult:
        """Run the trusted playbook; B23 must verify the resulting state."""

        self.validate_execution_request(request)

        action = request.action
        target = self._targets[action.target]
        playbook = self._playbooks[action.operation]
        started_at = datetime.now(timezone.utc)

        command = [
            str(self._executable),
            "--inventory",
            str(target.inventory_path),
            str(playbook),
            "--limit",
            target.host_alias,
            "--forks",
            "1",
        ]

        # Do not inherit arbitrary ANSIBLE_* or other environment variables.
        # SSH_AUTH_SOCK is retained when configured for the service account.
        environment = {
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "HOME": os.environ.get("HOME", str(self._working_directory)),
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
                cwd=str(self._working_directory),
                env=environment,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                check=False,
                shell=False,
            )

        except subprocess.TimeoutExpired:
            return self._result(
                request=request,
                status=ExecutionStatus.TIMED_OUT,
                started_at=started_at,
                completed_at=None,
                message=(
                    "Ansible exceeded its execution timeout. The target may "
                    "have been partially changed; independent verification "
                    "is required."
                ),
            )

        except Exception as exc:
            return self._result(
                request=request,
                status=ExecutionStatus.UNKNOWN,
                started_at=started_at,
                completed_at=None,
                message=(
                    "Ansible process outcome is unknown after "
                    f"{type(exc).__name__}; independent verification is required."
                ),
            )

        completed_at = datetime.now(timezone.utc)

        if completed.returncode == 0:
            return self._result(
                request=request,
                status=ExecutionStatus.SUCCEEDED,
                started_at=started_at,
                completed_at=completed_at,
                message=(
                    "Ansible playbook exited successfully. Independent "
                    "verification is still required."
                ),
            )

        return self._result(
            request=request,
            status=ExecutionStatus.FAILED,
            started_at=started_at,
            completed_at=completed_at,
            message=(
                f"Ansible exited with code {completed.returncode}. "
                "The playbook may have partially changed the target; "
                "independent verification is required."
            ),
        )

    def _result(
        self,
        *,
        request: AdapterExecutionRequest,
        status: ExecutionStatus,
        started_at: datetime,
        completed_at: datetime | None,
        message: str,
    ) -> AdapterExecutionResult:
        result = AdapterExecutionResult(
            task_id=request.task.task_id,
            plan_id=request.plan.plan_id,
            action_id=request.action.action_id,
            adapter_id=self.adapter_id,
            selected_channel="ansible",
            operation=request.action.operation,
            target=request.action.target,
            environment=request.task.environment,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            message=message,
        )
        result.validate()
        return result
