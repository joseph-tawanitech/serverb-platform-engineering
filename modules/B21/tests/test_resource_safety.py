from dataclasses import FrozenInstanceError

import pytest

from tap_b21.resource_safety import (
    ResourceImpact,
    ResourceSafetyDecision,
    ResourceSafetyGate,
    ResourceSafetyLimits,
    ResourceSnapshot,
    SimulatedResourceSafetyGate,
)


def safe_snapshot():
    return ResourceSnapshot(
        ram_used_percent=50.0,
        cpu_used_percent=50.0,
        disk_used_percent=50.0,
    )


def safe_impact():
    return ResourceImpact(
        ram_increase_percent=5.0,
        cpu_increase_percent=5.0,
        disk_increase_percent=5.0,
    )


def test_safe_resource_usage_is_allowed():
    gate = SimulatedResourceSafetyGate()

    result = gate.assess(safe_snapshot(), safe_impact())

    assert result.decision == ResourceSafetyDecision.ALLOW
    assert result.projected_usage == (
        ("ram", 55.0),
        ("cpu", 55.0),
        ("disk", 55.0),
    )
    result.validate()


@pytest.mark.parametrize(
    ("metric", "review_limit", "hard_limit"),
    [
        ("ram", 80.0, 90.0),
        ("cpu", 85.0, 95.0),
        ("disk", 80.0, 90.0),
    ],
)
def test_projected_review_threshold_requires_human(
    metric,
    review_limit,
    hard_limit,
):
    snapshot_values = {
        "ram_used_percent": 50.0,
        "cpu_used_percent": 50.0,
        "disk_used_percent": 50.0,
    }
    impact_values = {
        "ram_increase_percent": 5.0,
        "cpu_increase_percent": 5.0,
        "disk_increase_percent": 5.0,
    }

    snapshot_values[f"{metric}_used_percent"] = review_limit - 5.0
    impact_values[f"{metric}_increase_percent"] = 5.0

    gate = SimulatedResourceSafetyGate()

    result = gate.assess(
        ResourceSnapshot(**snapshot_values),
        ResourceImpact(**impact_values),
    )

    assert result.decision == ResourceSafetyDecision.NEEDS_HUMAN


@pytest.mark.parametrize(
    ("metric", "hard_limit"),
    [
        ("ram", 90.0),
        ("cpu", 95.0),
        ("disk", 90.0),
    ],
)
def test_projected_hard_limit_blocks_execution(
    metric,
    hard_limit,
):
    snapshot_values = {
        "ram_used_percent": 50.0,
        "cpu_used_percent": 50.0,
        "disk_used_percent": 50.0,
    }
    impact_values = {
        "ram_increase_percent": 5.0,
        "cpu_increase_percent": 5.0,
        "disk_increase_percent": 5.0,
    }

    snapshot_values[f"{metric}_used_percent"] = hard_limit - 5.0

    gate = SimulatedResourceSafetyGate()

    result = gate.assess(
        ResourceSnapshot(**snapshot_values),
        ResourceImpact(**impact_values),
    )

    assert result.decision == ResourceSafetyDecision.BLOCK
    assert any(
        "Hard resource limits cannot be overridden by approval" in reason
        for reason in result.reasons
    )


def test_current_hard_limit_blocks_even_when_impact_is_missing():
    gate = SimulatedResourceSafetyGate()

    snapshot = ResourceSnapshot(
        ram_used_percent=90.0,
        cpu_used_percent=50.0,
        disk_used_percent=50.0,
    )

    impact = ResourceImpact(
        ram_increase_percent=None,
        cpu_increase_percent=5.0,
        disk_increase_percent=5.0,
    )

    result = gate.assess(snapshot, impact)

    assert result.decision == ResourceSafetyDecision.BLOCK


def test_missing_current_reading_requires_human():
    gate = SimulatedResourceSafetyGate()

    snapshot = ResourceSnapshot(
        ram_used_percent=None,
        cpu_used_percent=50.0,
        disk_used_percent=50.0,
    )

    result = gate.assess(snapshot, safe_impact())

    assert result.decision == ResourceSafetyDecision.NEEDS_HUMAN
    assert any("Missing current RAM reading" in reason
               for reason in result.reasons)


def test_missing_projected_impact_requires_human():
    gate = SimulatedResourceSafetyGate()

    impact = ResourceImpact(
        ram_increase_percent=None,
        cpu_increase_percent=5.0,
        disk_increase_percent=5.0,
    )

    result = gate.assess(safe_snapshot(), impact)

    assert result.decision == ResourceSafetyDecision.NEEDS_HUMAN
    assert any("Missing projected RAM impact" in reason
               for reason in result.reasons)


@pytest.mark.parametrize(
    "invalid_value",
    [
        -1.0,
        101.0,
        float("nan"),
        float("inf"),
        True,
        "50",
    ],
)
def test_invalid_snapshot_readings_are_rejected(invalid_value):
    snapshot = ResourceSnapshot(
        ram_used_percent=invalid_value,
        cpu_used_percent=50.0,
        disk_used_percent=50.0,
    )

    with pytest.raises(ValueError):
        snapshot.validate()


@pytest.mark.parametrize(
    "invalid_value",
    [
        -1.0,
        float("nan"),
        float("inf"),
        True,
        "5",
    ],
)
def test_invalid_resource_impacts_are_rejected(invalid_value):
    impact = ResourceImpact(
        ram_increase_percent=invalid_value,
        cpu_increase_percent=5.0,
        disk_increase_percent=5.0,
    )

    with pytest.raises(ValueError):
        impact.validate()


def test_invalid_resource_limits_are_rejected():
    limits = ResourceSafetyLimits(
        ram_review_percent=90.0,
        ram_hard_limit_percent=90.0,
    )

    with pytest.raises(ValueError):
        SimulatedResourceSafetyGate(limits)


def test_gate_rejects_wrong_input_types():
    gate = SimulatedResourceSafetyGate()

    with pytest.raises(ValueError):
        gate.assess(object(), safe_impact())

    with pytest.raises(ValueError):
        gate.assess(safe_snapshot(), object())


def test_assessment_is_immutable():
    gate = SimulatedResourceSafetyGate()

    result = gate.assess(safe_snapshot(), safe_impact())

    with pytest.raises(FrozenInstanceError):
        result.decision = ResourceSafetyDecision.BLOCK


def test_simulated_gate_exposes_assessment_interface():
    gate = SimulatedResourceSafetyGate()

    assert callable(gate.assess)
