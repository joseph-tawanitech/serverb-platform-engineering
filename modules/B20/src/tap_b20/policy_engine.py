"""Deterministic operational security policy evaluation for TAP B20."""

from .models import SecurityDecision, SecurityRequest
from .policy import PolicyDecision, SecurityPolicy, SecurityRisk


_RISK_ORDER = {
    SecurityRisk.LOW: 1,
    SecurityRisk.MEDIUM: 2,
    SecurityRisk.HIGH: 3,
    SecurityRisk.CRITICAL: 4,
}


def evaluate_policy(
    request: SecurityRequest,
    policy: SecurityPolicy,
) -> PolicyDecision:
    """Evaluate a security request against an operational security policy.

    When requested_risk is present, it represents the action's assessed risk
    and must not exceed the policy's maximum permitted risk.

    Legacy requests without requested_risk retain the policy max_risk as
    their effective risk classification.
    """

    raw_requested_risk = request.metadata.get("requested_risk")

    if raw_requested_risk is None:
        requested_risk = policy.max_risk
    else:
        try:
            requested_risk = SecurityRisk(raw_requested_risk)
        except (TypeError, ValueError):
            return PolicyDecision(
                policy_id=policy.policy_id,
                policy_version=policy.version,
                request_id=request.request_id,
                decision=SecurityDecision.BLOCK,
                risk=SecurityRisk.CRITICAL,
                message="Requested risk is missing a valid classification.",
            )

    if _RISK_ORDER[requested_risk] > _RISK_ORDER[policy.max_risk]:
        return PolicyDecision(
            policy_id=policy.policy_id,
            policy_version=policy.version,
            request_id=request.request_id,
            decision=SecurityDecision.BLOCK,
            risk=requested_risk,
            message=(
                f"Requested risk {requested_risk.value} exceeds "
                f"the policy maximum {policy.max_risk.value}."
            ),
        )

    if not policy.enabled:
        return PolicyDecision(
            policy_id=policy.policy_id,
            policy_version=policy.version,
            request_id=request.request_id,
            decision=SecurityDecision.REVIEW,
            risk=requested_risk,
            message="Security policy is disabled and requires review.",
        )

    if request.environment != policy.environment:
        return PolicyDecision(
            policy_id=policy.policy_id,
            policy_version=policy.version,
            request_id=request.request_id,
            decision=SecurityDecision.BLOCK,
            risk=SecurityRisk.CRITICAL,
            message="Request environment is outside the policy scope.",
        )

    if request.asset not in policy.authorized_assets:
        return PolicyDecision(
            policy_id=policy.policy_id,
            policy_version=policy.version,
            request_id=request.request_id,
            decision=SecurityDecision.BLOCK,
            risk=SecurityRisk.HIGH,
            message="Requested asset is not authorized by the policy.",
        )

    if request.operation in policy.blocked_operations:
        return PolicyDecision(
            policy_id=policy.policy_id,
            policy_version=policy.version,
            request_id=request.request_id,
            decision=SecurityDecision.BLOCK,
            risk=requested_risk,
            message="Requested operation is explicitly blocked by policy.",
        )

    if request.operation in policy.review_operations:
        return PolicyDecision(
            policy_id=policy.policy_id,
            policy_version=policy.version,
            request_id=request.request_id,
            decision=SecurityDecision.REVIEW,
            risk=requested_risk,
            message="Requested operation requires policy review.",
        )

    if request.operation in policy.allowed_operations:
        return PolicyDecision(
            policy_id=policy.policy_id,
            policy_version=policy.version,
            request_id=request.request_id,
            decision=SecurityDecision.ALLOW,
            risk=requested_risk,
            message="Requested operation is allowed by policy.",
        )

    return PolicyDecision(
        policy_id=policy.policy_id,
        policy_version=policy.version,
        request_id=request.request_id,
        decision=SecurityDecision.REVIEW,
        risk=requested_risk,
        message="Requested operation is not explicitly classified by policy.",
    )
