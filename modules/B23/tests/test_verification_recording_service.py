import pytest

from tap_b23 import (
    AppendOnlyRecorder,
    SQLiteAppendOnlyRecorder,
    VerificationEngine,
    VerificationRecordingService,
    VerificationStatus,
)

from test_recorder import make_dispatch


@pytest.mark.parametrize("recorder_type", ["memory", "sqlite"])
def test_service_verifies_and_records_dispatch(
    recorder_type,
    tmp_path,
):
    dispatch = make_dispatch()
    engine = VerificationEngine(verifiers={})

    if recorder_type == "memory":
        recorder = AppendOnlyRecorder()
    else:
        recorder = SQLiteAppendOnlyRecorder(
            tmp_path / "tap-audit.db"
        )

    service = VerificationRecordingService(
        verification_engine=engine,
        recorder=recorder,
    )

    entry = service.verify_and_record(dispatch)

    assert entry.dispatch.dispatch_id == dispatch.dispatch_id
    assert entry.verification.dispatch_id == dispatch.dispatch_id
    assert entry.verification.status == VerificationStatus.SKIPPED
    assert len(entry.verification.results) == 1
    assert entry.verification.results[0].status == VerificationStatus.SKIPPED

    restored = recorder.get(dispatch.dispatch_id)

    assert restored.dispatch.dispatch_id == dispatch.dispatch_id
    assert restored.verification.status == VerificationStatus.SKIPPED
    assert len(recorder) == 1


def test_service_propagates_duplicate_recording_error():
    dispatch = make_dispatch()
    recorder = AppendOnlyRecorder()

    service = VerificationRecordingService(
        verification_engine=VerificationEngine(verifiers={}),
        recorder=recorder,
    )

    service.verify_and_record(dispatch)

    with pytest.raises(ValueError, match="already been recorded"):
        service.verify_and_record(dispatch)

    assert len(recorder) == 1


def test_service_rejects_invalid_dispatch():
    service = VerificationRecordingService(
        verification_engine=VerificationEngine(verifiers={}),
        recorder=AppendOnlyRecorder(),
    )

    with pytest.raises(TypeError, match="DispatchResult"):
        service.verify_and_record("not-a-dispatch")
