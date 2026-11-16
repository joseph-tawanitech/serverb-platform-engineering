"""Controlled Kubernetes execution adapter for TAP B22.

The initial implementation supports only a configured Deployment restart.

Execution is disabled by default. The adapter independently verifies the
authorization grant before any Kubernetes API operation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from tap_b21.adapter_contracts import (
    AdapterAuthorizationError,
    AdapterExecutionRequest,
    AdapterExecutionResult,
    ExecutionStatus,
    RemediationAdapter,
    verify_adapter_authorization,
)


class KubernetesAdapterError(RuntimeError):
    """Base error for Kubernetes adapter failures."""


class KubernetesTargetError(KubernetesAdapterError):
    """Raised when a requested target is not in trusted adapter config."""


class KubernetesExecutionDisabledError(KubernetesAdapterError):
    """Raised when execution has not been explicitly enabled."""


_DNS_LABEL = re.compile(r"^[a-z0-9](?:[-a-z0-9]*[a-z0-9])?$")


def _validate_dns_label(value: str, field_name: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) > 63
        or not _DNS_LABEL.fullmatch(value)
    ):
        raise ValueError(f"{field_name} must be a valid Kubernetes DNS label")


@dataclass(frozen=True)
class KubernetesDeploymentTarget:
    """Trusted mapping from a TAP target to one Kubernetes Deployment."""

    namespace: str
    deployment: str

    def validate(self) -> None:
        _validate_dns_label(self.namespace, "namespace")
        _validate_dns_label(self.deployment, "deployment")


class KubernetesAdapter(RemediationAdapter):
    """Kubernetes adapter with a narrow operation and target allowlist.

    Args:
        apps_api:
            Kubernetes AppsV1Api-compatible client. Injecting the client
            allows isolated unit tests and controlled deployment wiring.
        trusted_public_keys:
            Issuer keys from trusted deployment configuration.
        targets:
            Mapping of TAP target identifiers to configured Deployments.
        allowed_namespaces:
            Explicit namespace allowlist.
        execution_enabled:
            Must be explicitly True before the adapter can mutate a cluster.
        request_timeout_seconds:
            Timeout passed to Kubernetes API requests.
    """

    _ADAPTER_ID = "tap-b22-kubernetes"
    _CHANNELS = frozenset({"kubernetes"})
    _OPERATIONS = frozenset({"restart_deployment"})

    def __init__(
        self,
        *,
        apps_api,
        trusted_public_keys: Mapping[str, Ed25519PublicKey],
        targets: Mapping[str, KubernetesDeploymentTarget],
        allowed_namespaces: frozenset[str],
        execution_enabled: bool = False,
        request_timeout_seconds: float = 10.0,
    ) -> None:
        if apps_api is None:
            raise TypeError("apps_api is required")

        for method_name in (
            "read_namespaced_deployment",
            "patch_namespaced_deployment",
        ):
            if not callable(getattr(apps_api, method_name, None)):
                raise TypeError(
                    f"apps_api must implement {method_name}"
                )

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

        if not isinstance(allowed_namespaces, frozenset) or not allowed_namespaces:
            raise ValueError("allowed_namespaces must be a non-empty frozenset")

        for namespace in allowed_namespaces:
            _validate_dns_label(namespace, "allowed namespace")

        validated_targets = {}

        for target_id, target in targets.items():
            if not isinstance(target_id, str) or not target_id.strip():
                raise ValueError("target IDs must be non-empty strings")

            if not isinstance(target, KubernetesDeploymentTarget):
                raise TypeError(
                    f"target {target_id!r} must be a KubernetesDeploymentTarget"
                )

            target.validate()

            if target.namespace not in allowed_namespaces:
                raise ValueError(
                    f"target {target_id!r} uses a namespace outside the allowlist"
                )

            validated_targets[target_id] = target

        if not isinstance(execution_enabled, bool):
            raise TypeError("execution_enabled must be a boolean")

        if (
            isinstance(request_timeout_seconds, bool)
            or not isinstance(request_timeout_seconds, (int, float))
            or request_timeout_seconds <= 0
        ):
            raise ValueError("request_timeout_seconds must be positive")

        self._apps_api = apps_api
        self._trusted_public_keys = dict(trusted_public_keys)
        self._targets = dict(validated_targets)
        self._allowed_namespaces = allowed_namespaces
        self._execution_enabled = execution_enabled
        self._request_timeout_seconds = float(request_timeout_seconds)

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
        """Validate scope, operation, target and signed authorization."""

        if not isinstance(request, AdapterExecutionRequest):
            raise ValueError("request must be an AdapterExecutionRequest")

        request.validate()

        route = request.routed_action
        action = request.action

        if route.selected_channel not in self.supported_channels:
            raise KubernetesAdapterError(
                "router-selected channel is not supported by this adapter"
            )

        if route.operation not in self.supported_operations:
            raise KubernetesAdapterError(
                f"unsupported Kubernetes operation: {route.operation}"
            )

        target = self._targets.get(action.target)

        if target is None:
            raise KubernetesTargetError(
                "requested target is not present in trusted adapter configuration"
            )

        if target.namespace not in self._allowed_namespaces:
            raise KubernetesTargetError(
                "target namespace is outside the configured allowlist"
            )

        # The operation uses only the trusted target mapping. It does not
        # accept AI-supplied namespace, deployment or arbitrary patch data.
        if action.parameters:
            raise KubernetesAdapterError(
                "restart_deployment does not accept action parameters"
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

        # Fail during preflight, before the dispatcher invokes execution.
        if not self._execution_enabled:
            raise KubernetesExecutionDisabledError(
                "Kubernetes execution is disabled; explicitly enable it "
                "in trusted deployment configuration"
            )

    def execute_approved_request(
        self,
        request: AdapterExecutionRequest,
    ) -> AdapterExecutionResult:
        """Request a Deployment rollout restart after independent verification.

        SUCCEEDED means the Kubernetes API accepted the patch. It does not
        mean the Deployment rollout has completed; B23 must verify that.
        """

        self.validate_execution_request(request)

        if not self._execution_enabled:
            raise KubernetesExecutionDisabledError(
                "Kubernetes execution is disabled; explicitly enable it "
                "in trusted deployment configuration"
            )

        action = request.action
        target = self._targets[action.target]
        started_at = datetime.now(timezone.utc)

        patch_body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt":
                                started_at.isoformat(),
                        }
                    }
                }
            }
        }

        try:
            # Read first so a missing Deployment is detected before patching.
            self._apps_api.read_namespaced_deployment(
                name=target.deployment,
                namespace=target.namespace,
                _request_timeout=self._request_timeout_seconds,
            )

            # This modifies only the restart annotation on the Deployment
            # pod template. It does not accept arbitrary patch content.
            self._apps_api.patch_namespaced_deployment(
                name=target.deployment,
                namespace=target.namespace,
                body=patch_body,
                _request_timeout=self._request_timeout_seconds,
            )

        except Exception as exc:
            finished_at = datetime.now(timezone.utc)
            http_status = getattr(exc, "status", None)

            if isinstance(http_status, int) and 400 <= http_status < 500:
                status = ExecutionStatus.FAILED
                completed_at = finished_at
                message = (
                    "Kubernetes API rejected the Deployment restart "
                    f"(HTTP {http_status})"
                )
            elif isinstance(http_status, int) and http_status < 400:
                status = ExecutionStatus.UNKNOWN
                completed_at = None
                message = "Kubernetes returned an unexpected API outcome"
            else:
                # A timeout or transport failure may occur after the API
                # server has accepted the patch. Never claim it did not run.
                status = ExecutionStatus.UNKNOWN
                completed_at = None
                message = (
                    "Kubernetes operation outcome is unknown after "
                    f"{type(exc).__name__}"
                )

            result = AdapterExecutionResult(
                task_id=request.task.task_id,
                plan_id=request.plan.plan_id,
                action_id=action.action_id,
                adapter_id=self.adapter_id,
                selected_channel="kubernetes",
                operation=action.operation,
                target=action.target,
                environment=request.task.environment,
                status=status,
                started_at=started_at,
                completed_at=completed_at,
                message=message,
            )
            result.validate()
            return result

        completed_at = datetime.now(timezone.utc)

        result = AdapterExecutionResult(
            task_id=request.task.task_id,
            plan_id=request.plan.plan_id,
            action_id=action.action_id,
            adapter_id=self.adapter_id,
            selected_channel="kubernetes",
            operation=action.operation,
            target=action.target,
            environment=request.task.environment,
            status=ExecutionStatus.SUCCEEDED,
            started_at=started_at,
            completed_at=completed_at,
            message=(
                "Kubernetes API accepted the Deployment restart request; "
                "rollout completion requires independent verification"
            ),
        )
        result.validate()
        return result
