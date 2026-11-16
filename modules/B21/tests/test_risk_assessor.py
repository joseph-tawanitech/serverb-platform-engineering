"""Tests for deterministic B21 action risk assessment."""

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from tap_b20.policy import SecurityRisk
from tap_b21.risk_assessor import (
    ActionRiskAssessor,
    ActionRiskEvidence,
    RiskAssessmentError,
)


def make_evidence(**overrides):
    values = {
        "impact": SecurityRisk.LOW,
        "scope": SecurityRisk.LOW,
        "availability": SecurityRisk.LOW,
        "reversibility": SecurityRisk.LOW,
        "security": SecurityRisk.LOW,
        "uncertainty": SecurityRisk.LOW,
        "resource_impact": SecurityRisk.LOW,
        "evidence_refs": ("evidence://task-001/assessment-001",),
        "assessor_id": "tap-risk-assessor-v1",
        "assessed_at": datetime.now(timezone.utc),
    }
    values.update(overrides)
    return ActionRiskEvidence(**values)


def test_low_risk_evidence_produces_low_assessment():
    result = ActionRiskAssessor().assess(
        "action-001",
        make_evidence(),
    )

    assert result.action_id == "action-001"
    assert result.risk is SecurityRisk.LOW
    assert len(result.dimensions) == 7


@pytest.mark.parametrize(
    "dimension",
    (
        "impact",
        "scope",
        "availability",
        "reversibility",
        "security",
        "uncertainty",
        "resource_impact",
    ),
)
def test_highest_factor_determines_overall_risk(dimension):
    result = ActionRiskAssessor().assess(
        "action-002",
        make_evidence(**{dimension: SecurityRisk.CRITICAL}),
    )

    assert result.risk is SecurityRisk.CRITICAL
    assert dict(result.dimensions)[dimension] is SecurityRisk.CRITICAL


def test_assessment_preserves_evidence_provenance():
    evidence = make_evidence()
    result = ActionRiskAssessor().assess("action-003", evidence)

    assert result.evidence_refs == evidence.evidence_refs
    assert result.assessor_id == evidence.assessor_id
    assert result.assessed_at == evidence.assessed_at


@pytest.mark.parametrize(
    "dimension",
    (
        "impact",
        "scope",
        "availability",
        "reversibility",
        "security",
        "uncertainty",
        "resource_impact",
    ),
)
def test_missing_factor_fails_closed(dimension):
    evidence = make_evidence(**{dimension: None})

    with pytest.raises(RiskAssessmentError):
        ActionRiskAssessor().assess("action-004", evidence)


def test_invalid_factor_fails_closed():
    evidence = make_evidence(impact="LOW")

    with pytest.raises(RiskAssessmentError):
        ActionRiskAssessor().assess("action-005", evidence)


def test_missing_evidence_references_fail_closed():
    evidence = make_evidence(evidence_refs=())

    with pytest.raises(RiskAssessmentError):
        ActionRiskAssessor().assess("action-006", evidence)


def test_empty_evidence_reference_fails_closed():
    evidence = make_evidence(evidence_refs=(" ",))

    with pytest.raises(RiskAssessmentError):
        ActionRiskAssessor().assess("action-007", evidence)


def test_naive_assessment_timestamp_fails_closed():
    evidence = make_evidence(assessed_at=datetime(2026, 11, 17))

    with pytest.raises(RiskAssessmentError):
        ActionRiskAssessor().assess("action-008", evidence)


def test_empty_assessor_identity_fails_closed():
    evidence = make_evidence(assessor_id=" ")

    with pytest.raises(RiskAssessmentError):
        ActionRiskAssessor().assess("action-009", evidence)


def test_empty_action_id_fails_closed():
    with pytest.raises(RiskAssessmentError):
        ActionRiskAssessor().assess(" ", make_evidence())


def test_assessment_validation_rejects_tampered_overall_risk():
    result = ActionRiskAssessor().assess(
        "action-010",
        make_evidence(impact=SecurityRisk.HIGH),
    )

    tampered = replace(result, risk=SecurityRisk.LOW)

    with pytest.raises(RiskAssessmentError):
        tampered.validate()
