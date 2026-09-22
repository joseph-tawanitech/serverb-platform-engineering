"""Deterministic operational security policy evaluation for TAP B20."""

from .models import SecurityDecision, SecurityRequest
from .policy import PolicyDecision, SecurityPolicy, SecurityRisk


def evaluate_policy(
    request: SecurityRequest,
    policy: SecurityPolicy,
) -> PolicyDecision:
    """Evaluate a security request against an operational security policy."""

    if not policy.enabled:
        return PolicyDecision(
            policy_id=policy.policy_id,
            policy_version=policy.version,
            request_id=request.request_id,
            decision=SecurityDecision.REVIEW,
            risk=policy.max_risk,
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
            risk=policy.max_risk,
            message="Requested operation is explicitly blocked by policy.",
        )

    if request.operation in policy.review_operations:
        return PolicyDecision(
            policy_id=policy.policy_id,
            policy_version=policy.version,
            request_id=request.request_id,
            decision=SecurityDecision.REVIEW,
            risk=policy.max_risk,
            message="Requested operation requires policy review.",
        )

    if request.operation in policy.allowed_operations:
        return PolicyDecision(
            policy_id=policy.policy_id,
            policy_version=policy.version,
            request_id=request.request_id,
            decision=SecurityDecision.ALLOW,
            risk=policy.max_risk,
            message="Requested operation is allowed by policy.",
        )

    return PolicyDecision(
        policy_id=policy.policy_id,
        policy_version=policy.version,
        request_id=request.request_id,
        decision=SecurityDecision.REVIEW,
        risk=policy.max_risk,
        message="Requested operation is not explicitly classified by policy.",
    )
