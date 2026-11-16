from dataclasses import replace
from datetime import datetime, timezone

import pytest

from tap_b21.adapter_dispatcher import (
    ActionExecutionRecord,
    ActionExecutionStatus,
    DispatchResult,
)

from tap_b23.contracts import VerificationStatus
from tap_b23.recorder import (
    AppendOnlyRecorder,
    RecorderError,
)
from tap_b23.verification_engine import VerificationEngine


def make_dispatch():
    now = datetime.now(timezone.utc)

    record = ActionExecutionRecord(
        dispatch_id="dispatch-recorder-001",
        attempt_id="attempt-recorder-001",
        attempt_number=1,
        task_id="task-recorder-001",
        plan_id="plan-recorder-001",
        action_id="action-recorder-001",
        adapter_id=None,
        selected_channel="ansible",
        grant_id="grant-recorder-001",
        status=ActionExecutionStatus.BLOCKED,
        prepared_at=now,
    )

    dispatch = DispatchResult(
        dispatch_id="dispatch-recorder-001",
        task_id="task-recorder-001",
        plan_id="plan-recorder-001",
        grant_id="grant-recorder-001",
        action_records=(record,),
        overall_status=ActionExecutionStatus.BLOCKED,
        started_at=now,
        completed_at=now,
        message="Blocked test dispatch.",
    )

    dispatch.validate()
    return dispatch


def make_verification(dispatch):
    engine = VerificationEngine(verifiers={})
    return engine.verify_dispatch(dispatch)


def test_recorder_stores_execution_and_verification():
    dispatch = make_dispatch()
    verification = make_verification(dispatch)
    recorder = AppendOnlyRecorder()

    entry = recorder.record(dispatch, verification)

    assert entry.dispatch is dispatch
    assert entry.verification is verification
    assert recorder.get(dispatch.dispatch_id) is entry
    assert len(recorder) == 1
    assert len(recorder.list_records()) == 1


def test_recorder_rejects_duplicate_dispatch():
    dispatch = make_dispatch()
    verification = make_verification(dispatch)
    recorder = AppendOnlyRecorder()

    recorder.record(dispatch, verification)

    with pytest.raises(RecorderError, match="already been recorded"):
        recorder.record(dispatch, verification)

    assert len(recorder) == 1


def test_recorder_rejects_mismatched_dispatch():
    dispatch = make_dispatch()
    verification = make_verification(dispatch)

    invalid_result = replace(
        verification.results[0],
        dispatch_id="different-dispatch",
    )
    invalid_verification = replace(
        verification,
        results=(invalid_result,),
    )

    recorder = AppendOnlyRecorder()

    with pytest.raises(ValueError):
        recorder.record(dispatch, invalid_verification)

    assert len(recorder) == 0


def test_recorder_rejects_unknown_dispatch_lookup():
    recorder = AppendOnlyRecorder()

    with pytest.raises(RecorderError, match="has not been recorded"):
        recorder.get("unknown-dispatch")


def test_blocked_action_is_preserved_without_execution_mutation():
    dispatch = make_dispatch()
    original_record = dispatch.action_records[0]
    verification = make_verification(dispatch)

    recorder = AppendOnlyRecorder()
    entry = recorder.record(dispatch, verification)

    assert entry.dispatch.action_records[0] is original_record
    assert entry.dispatch.action_records[0].status == ActionExecutionStatus.BLOCKED
    assert entry.verification.status == VerificationStatus.SKIPPED
