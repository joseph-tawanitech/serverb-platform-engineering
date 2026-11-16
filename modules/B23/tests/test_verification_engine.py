from datetime import datetime, timedelta, timezone

from tap_b21.adapter_contracts import (
    AdapterExecutionResult,
    ExecutionStatus,
)
from tap_b21.adapter_dispatcher import (
    ActionExecutionRecord,
    ActionExecutionStatus,
    DispatchResult,
)

from tap_b23.contracts import (
    VerificationResult,
    VerificationStatus,
)
from tap_b23.verification_engine import VerificationEngine


def make_dispatch(status=ActionExecutionStatus.SUCCEEDED, channel="kubernetes"):
    now = datetime.now(timezone.utc)

    adapter_result = None
    adapter_id = "tap-b22-kubernetes" if channel == "kubernetes" else None

    if status == ActionExecutionStatus.SUCCEEDED:
        adapter_result = AdapterExecutionResult(
            task_id="task-001",
            plan_id="plan-001",
            action_id="action-001",
            adapter_id=adapter_id,
            selected_channel=channel,
            operation="restart_deployment",
            target="test-web",
            environment="test",
            status=ExecutionStatus.SUCCEEDED,
            started_at=now,
            completed_at=now + timedelta(seconds=1),
            message="Execution completed.",
        )

    record = ActionExecutionRecord(
        dispatch_id="dispatch-001",
        attempt_id="attempt-001",
        attempt_number=1,
        task_id="task-001",
        plan_id="plan-001",
        action_id="action-001",
        adapter_id=adapter_id,
        selected_channel=channel,
        grant_id="grant-001",
        status=status,
        prepared_at=now - timedelta(seconds=2),
        resource_checked_at=now - timedelta(seconds=1),
        authorization_confirmed_at=now - timedelta(seconds=1),
        adapter_result=adapter_result,
    )

    dispatch = DispatchResult(
        dispatch_id="dispatch-001",
        task_id="task-001",
        plan_id="plan-001",
        grant_id="grant-001",
        action_records=(record,),
        overall_status=status,
        started_at=now - timedelta(seconds=2),
        completed_at=now + timedelta(seconds=1),
        message="Test dispatch.",
    )

    dispatch.validate()
    return dispatch, record


class FakeVerifier:
    def __init__(self, status):
        self.status = status
        self.calls = []

    def verify(self, record):
        self.calls.append(record)

        now = datetime.now(timezone.utc)

        result = VerificationResult(
            verification_id="verification-001",
            dispatch_id=record.dispatch_id,
            attempt_id=record.attempt_id,
            task_id=record.task_id,
            plan_id=record.plan_id,
            action_id=record.action_id,
            selected_channel=record.selected_channel,
            execution_status=record.status,
            status=self.status,
            started_at=now,
            completed_at=now,
            evidence=(
                ("Deployment rollout independently verified.",)
                if self.status == VerificationStatus.VERIFIED
                else ()
            ),
            message="Simulated verification result.",
        )

        result.validate()
        return result


def test_all_actions_verified():
    dispatch, record = make_dispatch()
    verifier = FakeVerifier(VerificationStatus.VERIFIED)

    engine = VerificationEngine(
        verifiers={"kubernetes": verifier}
    )

    report = engine.verify_dispatch(dispatch)

    assert report.status == VerificationStatus.VERIFIED
    assert len(report.results) == 1
    assert report.results[0].status == VerificationStatus.VERIFIED
    assert verifier.calls == [record]


def test_unverified_action_produces_unverified_report():
    dispatch, _ = make_dispatch()
    verifier = FakeVerifier(VerificationStatus.UNVERIFIED)

    engine = VerificationEngine(
        verifiers={"kubernetes": verifier}
    )

    report = engine.verify_dispatch(dispatch)

    assert report.status == VerificationStatus.UNVERIFIED
    assert report.results[0].status == VerificationStatus.UNVERIFIED


def test_missing_verifier_produces_skipped_report():
    dispatch, _ = make_dispatch(
        status=ActionExecutionStatus.BLOCKED,
        channel="ansible",
    )

    engine = VerificationEngine(verifiers={})

    report = engine.verify_dispatch(dispatch)

    assert report.status == VerificationStatus.SKIPPED
    assert report.results[0].status == VerificationStatus.SKIPPED
    assert "No independent verifier" in report.results[0].message


def test_failed_verification_produces_failed_report():
    dispatch, _ = make_dispatch()
    verifier = FakeVerifier(VerificationStatus.FAILED)

    engine = VerificationEngine(
        verifiers={"kubernetes": verifier}
    )

    report = engine.verify_dispatch(dispatch)

    assert report.status == VerificationStatus.FAILED
    assert report.results[0].status == VerificationStatus.FAILED
