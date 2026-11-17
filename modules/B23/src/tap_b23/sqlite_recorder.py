"""Durable SQLite-backed append-only recording for TAP B23."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from tap_b21.adapter_contracts import (
    AdapterExecutionResult,
    ExecutionStatus,
)
from tap_b21.adapter_dispatcher import (
    ActionExecutionRecord,
    ActionExecutionStatus,
    DispatchResult,
)

from .contracts import (
    VerificationReport,
    VerificationResult,
    VerificationStatus,
)
from .recorder import RecordedDispatch, RecorderError


def _date(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_date(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value is not None else None


def _encode_entry(entry: RecordedDispatch) -> str:
    dispatch = entry.dispatch

    actions = []
    for record in dispatch.action_records:
        adapter_result = record.adapter_result

        actions.append({
            "dispatch_id": record.dispatch_id,
            "attempt_id": record.attempt_id,
            "attempt_number": record.attempt_number,
            "task_id": record.task_id,
            "plan_id": record.plan_id,
            "action_id": record.action_id,
            "adapter_id": record.adapter_id,
            "selected_channel": record.selected_channel,
            "grant_id": record.grant_id,
            "status": record.status.value,
            "prepared_at": _date(record.prepared_at),
            "resource_checked_at": _date(record.resource_checked_at),
            "authorization_confirmed_at": _date(
                record.authorization_confirmed_at
            ),
            "failure_code": record.failure_code,
            "failure_message": record.failure_message,
            "adapter_result": (
                {
                    "task_id": adapter_result.task_id,
                    "plan_id": adapter_result.plan_id,
                    "action_id": adapter_result.action_id,
                    "adapter_id": adapter_result.adapter_id,
                    "selected_channel": adapter_result.selected_channel,
                    "operation": adapter_result.operation,
                    "target": adapter_result.target,
                    "environment": adapter_result.environment,
                    "status": adapter_result.status.value,
                    "started_at": _date(adapter_result.started_at),
                    "completed_at": _date(adapter_result.completed_at),
                    "message": adapter_result.message,
                    "evidence_ids": list(adapter_result.evidence_ids),
                }
                if adapter_result is not None
                else None
            ),
        })

    verification = entry.verification

    verification_results = [
        {
            "verification_id": result.verification_id,
            "dispatch_id": result.dispatch_id,
            "attempt_id": result.attempt_id,
            "task_id": result.task_id,
            "plan_id": result.plan_id,
            "action_id": result.action_id,
            "selected_channel": result.selected_channel,
            "execution_status": result.execution_status.value,
            "status": result.status.value,
            "started_at": _date(result.started_at),
            "completed_at": _date(result.completed_at),
            "evidence": list(result.evidence),
            "message": result.message,
        }
        for result in verification.results
    ]

    payload = {
        "dispatch": {
            "dispatch_id": dispatch.dispatch_id,
            "task_id": dispatch.task_id,
            "plan_id": dispatch.plan_id,
            "grant_id": dispatch.grant_id,
            "action_records": actions,
            "overall_status": dispatch.overall_status.value,
            "started_at": _date(dispatch.started_at),
            "completed_at": _date(dispatch.completed_at),
            "message": dispatch.message,
        },
        "verification": {
            "dispatch_id": verification.dispatch_id,
            "status": verification.status.value,
            "results": verification_results,
            "started_at": _date(verification.started_at),
            "completed_at": _date(verification.completed_at),
            "message": verification.message,
        },
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _decode_entry(payload: str) -> RecordedDispatch:
    data = json.loads(payload)
    dispatch_data = data["dispatch"]

    actions = []
    for item in dispatch_data["action_records"]:
        adapter_data = item["adapter_result"]

        adapter_result = (
            AdapterExecutionResult(
                task_id=adapter_data["task_id"],
                plan_id=adapter_data["plan_id"],
                action_id=adapter_data["action_id"],
                adapter_id=adapter_data["adapter_id"],
                selected_channel=adapter_data["selected_channel"],
                operation=adapter_data["operation"],
                target=adapter_data["target"],
                environment=adapter_data["environment"],
                status=ExecutionStatus(adapter_data["status"]),
                started_at=_parse_date(adapter_data["started_at"]),
                completed_at=_parse_date(adapter_data["completed_at"]),
                message=adapter_data["message"],
                evidence_ids=tuple(adapter_data["evidence_ids"]),
            )
            if adapter_data is not None
            else None
        )

        actions.append(
            ActionExecutionRecord(
                dispatch_id=item["dispatch_id"],
                attempt_id=item["attempt_id"],
                attempt_number=item["attempt_number"],
                task_id=item["task_id"],
                plan_id=item["plan_id"],
                action_id=item["action_id"],
                adapter_id=item["adapter_id"],
                selected_channel=item["selected_channel"],
                grant_id=item["grant_id"],
                status=ActionExecutionStatus(item["status"]),
                prepared_at=_parse_date(item["prepared_at"]),
                resource_checked_at=_parse_date(
                    item["resource_checked_at"]
                ),
                authorization_confirmed_at=_parse_date(
                    item["authorization_confirmed_at"]
                ),
                adapter_result=adapter_result,
                failure_code=item["failure_code"],
                failure_message=item["failure_message"],
            )
        )

    dispatch = DispatchResult(
        dispatch_id=dispatch_data["dispatch_id"],
        task_id=dispatch_data["task_id"],
        plan_id=dispatch_data["plan_id"],
        grant_id=dispatch_data["grant_id"],
        action_records=tuple(actions),
        overall_status=ActionExecutionStatus(
            dispatch_data["overall_status"]
        ),
        started_at=_parse_date(dispatch_data["started_at"]),
        completed_at=_parse_date(dispatch_data["completed_at"]),
        message=dispatch_data["message"],
    )

    verification_data = data["verification"]

    verification_results = tuple(
        VerificationResult(
            verification_id=item["verification_id"],
            dispatch_id=item["dispatch_id"],
            attempt_id=item["attempt_id"],
            task_id=item["task_id"],
            plan_id=item["plan_id"],
            action_id=item["action_id"],
            selected_channel=item["selected_channel"],
            execution_status=ActionExecutionStatus(
                item["execution_status"]
            ),
            status=VerificationStatus(item["status"]),
            started_at=_parse_date(item["started_at"]),
            completed_at=_parse_date(item["completed_at"]),
            evidence=tuple(item["evidence"]),
            message=item["message"],
        )
        for item in verification_data["results"]
    )

    verification = VerificationReport(
        dispatch_id=verification_data["dispatch_id"],
        status=VerificationStatus(verification_data["status"]),
        results=verification_results,
        started_at=_parse_date(verification_data["started_at"]),
        completed_at=_parse_date(verification_data["completed_at"]),
        message=verification_data["message"],
    )

    entry = RecordedDispatch(
        dispatch=dispatch,
        verification=verification,
    )
    entry.validate()
    return entry


class SQLiteAppendOnlyRecorder:
    """Durable SQLite recorder with update/delete protection triggers."""

    def __init__(self, database_path: str | Path) -> None:
        if str(database_path) == ":memory:":
            raise RecorderError(
                "a file-backed SQLite database is required"
            )

        path = Path(database_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._database_path = path.resolve()

        with closing(self._connect()) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS recorded_dispatches (
                    dispatch_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    plan_id TEXT NOT NULL,
                    overall_status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    payload TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                );

                CREATE TRIGGER IF NOT EXISTS prevent_dispatch_update
                BEFORE UPDATE ON recorded_dispatches
                BEGIN
                    SELECT RAISE(ABORT, 'dispatch records are append-only');
                END;

                CREATE TRIGGER IF NOT EXISTS prevent_dispatch_delete
                BEFORE DELETE ON recorded_dispatches
                BEGIN
                    SELECT RAISE(ABORT, 'dispatch records are append-only');
                END;
                """
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            str(self._database_path),
            timeout=10,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def record(
        self,
        dispatch: DispatchResult,
        verification: VerificationReport,
    ) -> RecordedDispatch:
        entry = RecordedDispatch(
            dispatch=dispatch,
            verification=verification,
        )
        entry.validate()
        payload = _encode_entry(entry)

        try:
            with closing(self._connect()) as connection:
                with connection:
                    connection.execute(
                        """
                        INSERT INTO recorded_dispatches (
                            dispatch_id,
                            task_id,
                            plan_id,
                            overall_status,
                            started_at,
                            completed_at,
                            payload
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            dispatch.dispatch_id,
                            dispatch.task_id,
                            dispatch.plan_id,
                            dispatch.overall_status.value,
                            dispatch.started_at.isoformat(),
                            _date(dispatch.completed_at),
                            payload,
                        ),
                    )
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise RecorderError(
                    "dispatch has already been recorded"
                ) from exc
            raise RecorderError("SQLite rejected the recording") from exc
        except sqlite3.Error as exc:
            raise RecorderError("SQLite recording failed") from exc

        return entry

    def get(self, dispatch_id: str) -> RecordedDispatch:
        if not isinstance(dispatch_id, str) or not dispatch_id.strip():
            raise RecorderError("dispatch_id must be non-empty text")

        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    """
                    SELECT payload
                    FROM recorded_dispatches
                    WHERE dispatch_id = ?
                    """,
                    (dispatch_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise RecorderError("SQLite lookup failed") from exc

        if row is None:
            raise RecorderError("dispatch has not been recorded")

        try:
            return _decode_entry(row["payload"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RecorderError("stored dispatch record is invalid") from exc

    def list_records(self) -> tuple[RecordedDispatch, ...]:
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    """
                    SELECT payload
                    FROM recorded_dispatches
                    ORDER BY rowid
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            raise RecorderError("SQLite listing failed") from exc

        try:
            return tuple(_decode_entry(row["payload"]) for row in rows)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RecorderError("stored dispatch record is invalid") from exc

    def __len__(self) -> int:
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT COUNT(*) AS record_count "
                    "FROM recorded_dispatches"
                ).fetchone()
                return int(row["record_count"])
        except sqlite3.Error as exc:
            raise RecorderError("SQLite count failed") from exc
