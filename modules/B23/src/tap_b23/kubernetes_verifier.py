"""Independent, read-only Kubernetes Deployment verification for TAP B23."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Mapping

from tap_b21.adapter_dispatcher import (
    ActionExecutionRecord,
    ActionExecutionStatus,
)

from tap_b22.kubernetes_adapter import KubernetesDeploymentTarget

from .contracts import (
    VerificationResult,
    VerificationStatus,
    new_verification_id,
)


_RESTART_ANNOTATION = "kubectl.kubernetes.io/restartedAt"


class KubernetesDeploymentVerifier:
    """Verify a Deployment restart using independent Kubernetes reads."""

    def __init__(
        self,
        *,
        apps_api,
        targets: Mapping[str, KubernetesDeploymentTarget],
        timeout_seconds: float = 120.0,
        poll_interval_seconds: float = 2.0,
        request_timeout_seconds: float = 10.0,
    ) -> None:
        if apps_api is None or not callable(
            getattr(apps_api, "read_namespaced_deployment", None)
        ):
            raise TypeError("apps_api must provide read_namespaced_deployment")

        if not isinstance(targets, Mapping) or not targets:
            raise ValueError("targets must be a non-empty mapping")

        for target_id, target in targets.items():
            if not isinstance(target_id, str) or not target_id.strip():
                raise ValueError("target IDs must be non-empty strings")
            if not isinstance(target, KubernetesDeploymentTarget):
                raise TypeError("targets must contain KubernetesDeploymentTarget")
            target.validate()

        for name, value in (
            ("timeout_seconds", timeout_seconds),
            ("poll_interval_seconds", poll_interval_seconds),
            ("request_timeout_seconds", request_timeout_seconds),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value <= 0
            ):
                raise ValueError(f"{name} must be positive")

        self._apps_api = apps_api
        self._targets = dict(targets)
        self._timeout = float(timeout_seconds)
        self._poll_interval = float(poll_interval_seconds)
        self._request_timeout = float(request_timeout_seconds)

    def verify(self, record: ActionExecutionRecord) -> VerificationResult:
        """Verify an eligible Kubernetes restart without executing changes."""

        if not isinstance(record, ActionExecutionRecord):
            raise TypeError("record must be an ActionExecutionRecord")

        record.validate()

        started_at = datetime.now(timezone.utc)
        evidence: list[str] = []

        adapter_result = record.adapter_result

        if record.status not in {
            ActionExecutionStatus.SUCCEEDED,
            ActionExecutionStatus.UNKNOWN,
        }:
            return self._result(
                record,
                VerificationStatus.SKIPPED,
                started_at,
                evidence,
                "Execution status does not require Kubernetes reconciliation.",
            )

        if adapter_result is None:
            return self._result(
                record,
                VerificationStatus.UNVERIFIED,
                started_at,
                evidence,
                "Execution outcome has no adapter result; target reconciliation "
                "cannot be performed from this record.",
            )

        if (
            record.selected_channel != "kubernetes"
            or adapter_result.operation != "restart_deployment"
        ):
            return self._result(
                record,
                VerificationStatus.SKIPPED,
                started_at,
                evidence,
                "This verifier supports Kubernetes Deployment restarts only.",
            )

        target = self._targets.get(adapter_result.target)

        if target is None:
            return self._result(
                record,
                VerificationStatus.UNVERIFIED,
                started_at,
                evidence,
                "Target is absent from the verifier's trusted target mapping.",
            )

        expected_restart = adapter_result.started_at.isoformat()
        deadline = time.monotonic() + self._timeout
        last_observation = "Deployment rollout has not yet been observed."

        while True:
            try:
                deployment = self._apps_api.read_namespaced_deployment(
                    name=target.deployment,
                    namespace=target.namespace,
                    _request_timeout=self._request_timeout,
                )

                metadata = getattr(deployment, "metadata", None)
                spec = getattr(deployment, "spec", None)
                status = getattr(deployment, "status", None)

                generation = getattr(metadata, "generation", None) or 0
                observed_generation = (
                    getattr(status, "observed_generation", None) or 0
                )
                desired = getattr(spec, "replicas", None)
                desired = 1 if desired is None else desired

                updated = getattr(status, "updated_replicas", None) or 0
                available = getattr(status, "available_replicas", None) or 0
                unavailable = getattr(status, "unavailable_replicas", None) or 0

                template = getattr(spec, "template", None)
                template_metadata = getattr(template, "metadata", None)
                annotations = (
                    getattr(template_metadata, "annotations", None) or {}
                )
                observed_restart = annotations.get(_RESTART_ANNOTATION)

                rollout_complete = (
                    observed_generation >= generation
                    and updated == desired
                    and available == desired
                    and unavailable == 0
                )

                restart_observed = observed_restart == expected_restart

                evidence = [
                    f"Deployment: {target.namespace}/{target.deployment}",
                    f"Generation: {generation}",
                    f"Observed generation: {observed_generation}",
                    f"Desired replicas: {desired}",
                    f"Updated replicas: {updated}",
                    f"Available replicas: {available}",
                    f"Unavailable replicas: {unavailable}",
                    f"Restart annotation observed: {restart_observed}",
                    f"Rollout complete: {rollout_complete}",
                ]

                if desired == 0:
                    last_observation = (
                        "Deployment has zero desired replicas; restart "
                        "completion cannot be established."
                    )
                elif rollout_complete and restart_observed:
                    evidence.append(
                        "Deployment rollout and requested restart annotation "
                        "were independently observed."
                    )
                    return self._result(
                        record,
                        VerificationStatus.VERIFIED,
                        started_at,
                        evidence,
                        "Kubernetes Deployment restart independently verified.",
                    )
                else:
                    last_observation = (
                        "Deployment has not yet demonstrated both the "
                        "requested restart and completed rollout."
                    )

            except Exception as exc:
                if getattr(exc, "status", None) == 404:
                    evidence.append("Kubernetes API returned HTTP 404.")
                    return self._result(
                        record,
                        VerificationStatus.FAILED,
                        started_at,
                        evidence,
                        "The configured Deployment does not exist.",
                    )

                last_observation = (
                    "Kubernetes state could not be read: "
                    f"{type(exc).__name__}"
                )

            if time.monotonic() >= deadline:
                break

            time.sleep(
                min(self._poll_interval, max(0, deadline - time.monotonic()))
            )

        evidence.append(last_observation)

        return self._result(
            record,
            VerificationStatus.UNVERIFIED,
            started_at,
            evidence,
            "Verification deadline reached without sufficient evidence. "
            "The execution must not be treated as verified.",
        )

    @staticmethod
    def _result(
        record: ActionExecutionRecord,
        status: VerificationStatus,
        started_at: datetime,
        evidence: list[str],
        message: str,
    ) -> VerificationResult:
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
            completed_at=datetime.now(timezone.utc),
            evidence=tuple(evidence),
            message=message,
        )
        result.validate()
        return result
