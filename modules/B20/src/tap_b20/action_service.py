"""Governed security action evaluation for TAP B20.7."""

from .actions import SecurityActionDecision, SecurityActionRequest
from .models import SecurityDecision, SecurityRequest
from .policy import SecurityPolicy
from .policy_engine import evaluate_policy


def evaluate_security_action(
    action: SecurityActionRequest,
    policy: SecurityPolicy,
) -> SecurityActionDecision:
    """Evaluate a proposed security action using the existing B20.2 policy engine."""

    request = SecurityRequest(
        request_id=action.request_id,
        operation=action.operation,
        environment=action.environment,
        asset=action.asset,
        requester=action.requester,
        purpose=action.purpose,
        metadata={
            **action.metadata,
            "action_id": action.action_id,
            "recommendation": action.recommendation,
            "requested_risk": action.risk.value,
        },
    )

    policy_decision = evaluate_policy(request, policy)

    return SecurityActionDecision(
        action_id=action.action_id,
        request_id=action.request_id,
        decision=policy_decision.decision,
        risk=policy_decision.risk,
        policy_id=policy_decision.policy_id,
        policy_version=policy_decision.policy_version,
        authorization_required=policy_decision.decision
        in (
            SecurityDecision.REVIEW,
            SecurityDecision.ALLOW,
        ),
        message=policy_decision.message,
    )
