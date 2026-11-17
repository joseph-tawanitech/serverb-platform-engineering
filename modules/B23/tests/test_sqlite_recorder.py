import sqlite3
from dataclasses import replace

import pytest

from tap_b23.recorder import RecorderError
from tap_b23.sqlite_recorder import SQLiteAppendOnlyRecorder

from test_recorder import make_dispatch, make_verification
from test_verification_engine import make_dispatch as make_success_dispatch


def test_sqlite_recorder_persists_across_reopen(tmp_path):
    database = tmp_path / "tap-audit.db"

    dispatch = make_dispatch()
    verification = make_verification(dispatch)

    first = SQLiteAppendOnlyRecorder(database)
    first.record(dispatch, verification)

    second = SQLiteAppendOnlyRecorder(database)
    restored = second.get(dispatch.dispatch_id)

    assert restored.dispatch.dispatch_id == dispatch.dispatch_id
    assert restored.verification.dispatch_id == verification.dispatch_id
    assert restored.dispatch.action_records[0].status == (
        dispatch.action_records[0].status
    )
    assert second.list_records() == (restored,)
    assert len(second) == 1


def test_sqlite_recorder_round_trips_successful_adapter_result(tmp_path):
    database = tmp_path / "tap-audit-success.db"
    dispatch, _ = make_success_dispatch()
    verification = make_verification(dispatch)

    recorder = SQLiteAppendOnlyRecorder(database)
    original = recorder.record(dispatch, verification)

    reopened = SQLiteAppendOnlyRecorder(database)
    restored = reopened.get(dispatch.dispatch_id)

    original_adapter = dispatch.action_records[0].adapter_result
    restored_adapter = restored.dispatch.action_records[0].adapter_result

    assert original_adapter is not None
    assert restored_adapter == original_adapter
    assert restored.dispatch == dispatch
    assert restored.verification == verification
    assert restored == original


def test_sqlite_recorder_rejects_duplicate_dispatch(tmp_path):
    database = tmp_path / "tap-audit.db"
    dispatch = make_dispatch()
    verification = make_verification(dispatch)

    recorder = SQLiteAppendOnlyRecorder(database)
    recorder.record(dispatch, verification)

    with pytest.raises(RecorderError, match="already been recorded"):
        recorder.record(dispatch, verification)

    assert len(recorder) == 1


def test_sqlite_recorder_rejects_update_and_delete(tmp_path):
    database = tmp_path / "tap-audit.db"
    dispatch = make_dispatch()
    verification = make_verification(dispatch)

    recorder = SQLiteAppendOnlyRecorder(database)
    recorder.record(dispatch, verification)

    with sqlite3.connect(database) as connection:
        with pytest.raises(
            sqlite3.IntegrityError,
            match="append-only",
        ):
            connection.execute(
                "UPDATE recorded_dispatches SET task_id = 'changed'"
            )

        with pytest.raises(
            sqlite3.IntegrityError,
            match="append-only",
        ):
            connection.execute(
                "DELETE FROM recorded_dispatches"
            )

    assert len(recorder) == 1


def test_sqlite_recorder_rejects_invalid_entry(tmp_path):
    database = tmp_path / "tap-audit.db"
    dispatch = make_dispatch()
    verification = make_verification(dispatch)

    wrong_verification = replace(
        verification,
        dispatch_id="different-dispatch",
    )

    recorder = SQLiteAppendOnlyRecorder(database)

    with pytest.raises(ValueError):
        recorder.record(dispatch, wrong_verification)

    assert len(recorder) == 0


def test_sqlite_recorder_rejects_unknown_dispatch(tmp_path):
    recorder = SQLiteAppendOnlyRecorder(tmp_path / "tap-audit.db")

    with pytest.raises(RecorderError, match="has not been recorded"):
        recorder.get("unknown-dispatch")
