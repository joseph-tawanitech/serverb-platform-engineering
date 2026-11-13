
import unittest
from dataclasses import FrozenInstanceError
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


class TestActionExecutionRecord(unittest.TestCase):

    def setUp(self):
        self.prepared = datetime(
            2026, 11, 13, 10, 0, tzinfo=timezone.utc
        )

    def make_adapter_result(self, **overrides):
        values = {
            "task_id": "task-001",
            "plan_id": "plan-001",
            "action_id": "action-001",
            "adapter_id": "ansible-runner-adapter",
            "selected_channel": "ansible",
            "operation": "restart_service",
            "target": "server-01",
            "environment": "lab",
            "status": ExecutionStatus.SUCCEEDED,
            "started_at": self.prepared + timedelta(seconds=10),
            "completed_at": self.prepared + timedelta(seconds=20),
            "message": "Service restart completed.",
            "evidence_ids": ("execution-001",),
        }
        values.update(overrides)
        return AdapterExecutionResult(**values)

    def make_record(self, **overrides):
        values = {
            "dispatch_id": "dispatch-001",
            "attempt_id": "attempt-001",
            "attempt_number": 1,
            "task_id": "task-001",
            "plan_id": "plan-001",
            "action_id": "action-001",
            "adapter_id": "ansible-runner-adapter",
            "selected_channel": "ansible",
            "grant_id": "grant-001",
            "status": ActionExecutionStatus.PREPARED,
            "prepared_at": self.prepared,
        }
        values.update(overrides)
        return ActionExecutionRecord(**values)

    def test_valid_prepared_record_passes(self):
        self.make_record().validate()

    def test_not_started_record_passes(self):
        self.make_record(
            status=ActionExecutionStatus.NOT_STARTED,
        ).validate()

    def test_blocked_record_passes(self):
        self.make_record(
            status=ActionExecutionStatus.BLOCKED,
            failure_code="RESOURCE_LIMIT",
            failure_message="Insufficient available memory.",
        ).validate()

    def test_executing_record_passes(self):
        self.make_record(
            status=ActionExecutionStatus.EXECUTING,
            authorization_confirmed_at=(
                self.prepared + timedelta(seconds=5)
            ),
        ).validate()

    def test_successful_record_requires_matching_adapter_result(self):
        record = self.make_record(
            status=ActionExecutionStatus.SUCCEEDED,
            adapter_result=self.make_adapter_result(),
        )
        record.validate()

    def test_failed_record_accepts_failed_adapter_result(self):
        result = self.make_adapter_result(
            status=ExecutionStatus.FAILED,
            message="Service restart failed.",
        )
        self.make_record(
            status=ActionExecutionStatus.FAILED,
            adapter_result=result,
        ).validate()

    def test_timeout_record_accepts_timeout_adapter_result(self):
        result = self.make_adapter_result(
            status=ExecutionStatus.TIMED_OUT,
            completed_at=None,
            message="Adapter execution timed out.",
        )
        self.make_record(
            status=ActionExecutionStatus.TIMED_OUT,
            adapter_result=result,
        ).validate()

    def test_unknown_record_accepts_unknown_adapter_result(self):
        result = self.make_adapter_result(
            status=ExecutionStatus.UNKNOWN,
            completed_at=None,
            message="Execution outcome is unknown.",
        )
        self.make_record(
            status=ActionExecutionStatus.UNKNOWN,
            adapter_result=result,
        ).validate()

    def test_success_without_adapter_result_is_rejected(self):
        record = self.make_record(
            status=ActionExecutionStatus.SUCCEEDED,
        )
        with self.assertRaises(ValueError):
            record.validate()

    def test_adapter_result_before_terminal_status_is_rejected(self):
        record = self.make_record(
            status=ActionExecutionStatus.PREPARED,
            adapter_result=self.make_adapter_result(),
        )
        with self.assertRaises(ValueError):
            record.validate()

    def test_adapter_result_task_mismatch_is_rejected(self):
        result = self.make_adapter_result(task_id="another-task")
        record = self.make_record(
            status=ActionExecutionStatus.SUCCEEDED,
            adapter_result=result,
        )
        with self.assertRaisesRegex(ValueError, "task ID mismatch"):
            record.validate()

    def test_adapter_result_plan_mismatch_is_rejected(self):
        result = self.make_adapter_result(plan_id="another-plan")
        record = self.make_record(
            status=ActionExecutionStatus.SUCCEEDED,
            adapter_result=result,
        )
        with self.assertRaisesRegex(ValueError, "plan ID mismatch"):
            record.validate()

    def test_adapter_result_action_mismatch_is_rejected(self):
        result = self.make_adapter_result(action_id="another-action")
        record = self.make_record(
            status=ActionExecutionStatus.SUCCEEDED,
            adapter_result=result,
        )
        with self.assertRaisesRegex(ValueError, "action ID mismatch"):
            record.validate()

    def test_adapter_result_adapter_mismatch_is_rejected(self):
        result = self.make_adapter_result(
            adapter_id="another-adapter"
        )
        record = self.make_record(
            status=ActionExecutionStatus.SUCCEEDED,
            adapter_result=result,
        )
        with self.assertRaisesRegex(ValueError, "adapter ID mismatch"):
            record.validate()

    def test_adapter_result_channel_mismatch_is_rejected(self):
        result = self.make_adapter_result(
            selected_channel="kubernetes"
        )
        record = self.make_record(
            status=ActionExecutionStatus.SUCCEEDED,
            adapter_result=result,
        )
        with self.assertRaisesRegex(ValueError, "channel mismatch"):
            record.validate()

    def test_adapter_result_status_mismatch_is_rejected(self):
        result = self.make_adapter_result(
            status=ExecutionStatus.FAILED,
        )
        record = self.make_record(
            status=ActionExecutionStatus.SUCCEEDED,
            adapter_result=result,
        )
        with self.assertRaisesRegex(ValueError, "status"):
            record.validate()

    def test_invalid_status_type_is_rejected(self):
        record = self.make_record(status="PREPARED")
        with self.assertRaises(ValueError):
            record.validate()

    def test_unsupported_channel_is_rejected(self):
        record = self.make_record(selected_channel="terraform")
        with self.assertRaises(ValueError):
            record.validate()

    def test_zero_attempt_number_is_rejected(self):
        record = self.make_record(attempt_number=0)
        with self.assertRaises(ValueError):
            record.validate()

    def test_boolean_attempt_number_is_rejected(self):
        record = self.make_record(attempt_number=True)
        with self.assertRaises(ValueError):
            record.validate()

    def test_naive_prepared_timestamp_is_rejected(self):
        record = self.make_record(
            prepared_at=datetime(2026, 11, 13, 10, 0)
        )
        with self.assertRaises(ValueError):
            record.validate()

    def test_resource_check_before_preparation_is_rejected(self):
        record = self.make_record(
            resource_checked_at=(
                self.prepared - timedelta(seconds=1)
            )
        )
        with self.assertRaises(ValueError):
            record.validate()

    def test_authorization_before_preparation_is_rejected(self):
        record = self.make_record(
            authorization_confirmed_at=(
                self.prepared - timedelta(seconds=1)
            )
        )
        with self.assertRaises(ValueError):
            record.validate()

    def test_record_is_immutable(self):
        record = self.make_record()
        with self.assertRaises(FrozenInstanceError):
            record.status = ActionExecutionStatus.BLOCKED


class TestDispatchResult(unittest.TestCase):

    def setUp(self):
        self.started = datetime(
            2026, 11, 13, 10, 0, tzinfo=timezone.utc
        )

    def make_adapter_result(self, **overrides):
        values = {
            "task_id": "task-001",
            "plan_id": "plan-001",
            "action_id": "action-001",
            "adapter_id": "ansible-runner-adapter",
            "selected_channel": "ansible",
            "operation": "restart_service",
            "target": "server-01",
            "environment": "lab",
            "status": ExecutionStatus.SUCCEEDED,
            "started_at": self.started + timedelta(seconds=10),
            "completed_at": self.started + timedelta(seconds=20),
            "message": "Service restart completed.",
            "evidence_ids": ("execution-001",),
        }
        values.update(overrides)
        return AdapterExecutionResult(**values)

    def make_adapter_result(self, **overrides):
        values = {
            "task_id": "task-001",
            "plan_id": "plan-001",
            "action_id": "action-001",
            "adapter_id": "ansible-runner-adapter",
            "selected_channel": "ansible",
            "operation": "restart_service",
            "target": "server-01",
            "environment": "lab",
            "status": ExecutionStatus.SUCCEEDED,
            "started_at": self.started + timedelta(seconds=10),
            "completed_at": self.started + timedelta(seconds=20),
            "message": "Service restart completed.",
            "evidence_ids": ("execution-001",),
        }
        values.update(overrides)
        return AdapterExecutionResult(**values)

    def make_record(self, **overrides):
        values = {
            "dispatch_id": "dispatch-001",
            "attempt_id": "attempt-001",
            "attempt_number": 1,
            "task_id": "task-001",
            "plan_id": "plan-001",
            "action_id": "action-001",
            "adapter_id": "ansible-runner-adapter",
            "selected_channel": "ansible",
            "grant_id": "grant-001",
            "status": ActionExecutionStatus.PREPARED,
            "prepared_at": self.started,
        }
        values.update(overrides)
        return ActionExecutionRecord(**values)

    def make_dispatch(self, **overrides):
        values = {
            "dispatch_id": "dispatch-001",
            "task_id": "task-001",
            "plan_id": "plan-001",
            "grant_id": "grant-001",
            "action_records": (self.make_record(),),
            "overall_status": ActionExecutionStatus.PREPARED,
            "started_at": self.started,
            "completed_at": None,
            "message": "Dispatch prepared.",
        }
        values.update(overrides)
        return DispatchResult(**values)

    def test_valid_dispatch_passes(self):
        self.make_dispatch().validate()

    def test_completed_dispatch_passes(self):
        completed = self.started + timedelta(seconds=30)
        record = self.make_record(
            status=ActionExecutionStatus.BLOCKED,
            failure_code="RESOURCE_LIMIT",
        )
        dispatch = self.make_dispatch(
            action_records=(record,),
            overall_status=ActionExecutionStatus.BLOCKED,
            completed_at=completed,
            message="Dispatch blocked by resource safety.",
        )
        dispatch.validate()

    def test_action_records_must_be_tuple(self):
        dispatch = self.make_dispatch(
            action_records=[self.make_record()]
        )
        with self.assertRaises(ValueError):
            dispatch.validate()

    def test_empty_action_records_are_rejected(self):
        dispatch = self.make_dispatch(action_records=())
        with self.assertRaises(ValueError):
            dispatch.validate()

    def test_dispatch_id_mismatch_is_rejected(self):
        record = self.make_record(dispatch_id="another-dispatch")
        dispatch = self.make_dispatch(action_records=(record,))
        with self.assertRaises(ValueError):
            dispatch.validate()

    def test_task_id_mismatch_is_rejected(self):
        record = self.make_record(task_id="another-task")
        dispatch = self.make_dispatch(action_records=(record,))
        with self.assertRaises(ValueError):
            dispatch.validate()

    def test_plan_id_mismatch_is_rejected(self):
        record = self.make_record(plan_id="another-plan")
        dispatch = self.make_dispatch(action_records=(record,))
        with self.assertRaises(ValueError):
            dispatch.validate()

    def test_grant_id_mismatch_is_rejected(self):
        record = self.make_record(grant_id="another-grant")
        dispatch = self.make_dispatch(action_records=(record,))
        with self.assertRaises(ValueError):
            dispatch.validate()

    def test_duplicate_attempt_ids_are_rejected(self):
        first = self.make_record()
        second = self.make_record(
            action_id="action-002",
            attempt_id="attempt-001",
        )
        dispatch = self.make_dispatch(
            action_records=(first, second)
        )
        with self.assertRaisesRegex(ValueError, "attempt IDs"):
            dispatch.validate()

    def test_duplicate_attempt_numbers_for_same_action_are_rejected(self):
        first = self.make_record()
        second = self.make_record(
            attempt_id="attempt-002",
            attempt_number=1,
        )
        dispatch = self.make_dispatch(
            action_records=(first, second)
        )
        with self.assertRaisesRegex(ValueError, "attempt numbers"):
            dispatch.validate()

    def test_distinct_attempts_for_same_action_are_allowed(self):
        first = self.make_record()
        second = self.make_record(
            attempt_id="attempt-002",
            attempt_number=2,
            status=ActionExecutionStatus.NOT_STARTED,
        )
        dispatch = self.make_dispatch(
            action_records=(first, second)
        )
        dispatch.validate()

    def test_partial_execution_records_are_preserved(self):
        succeeded_result = self.make_adapter_result()

        failed_result = self.make_adapter_result(
            action_id="action-002",
            target="server-02",
            status=ExecutionStatus.FAILED,
            message="Service restart failed.",
            evidence_ids=("execution-002",),
        )

        succeeded = self.make_record(
            status=ActionExecutionStatus.SUCCEEDED,
            adapter_result=succeeded_result,
        )

        failed = self.make_record(
            action_id="action-002",
            attempt_id="attempt-002",
            status=ActionExecutionStatus.FAILED,
            adapter_result=failed_result,
            failure_code="ADAPTER_EXECUTION_FAILED",
            failure_message="Service restart failed.",
        )

        not_started = self.make_record(
            action_id="action-003",
            attempt_id="attempt-003",
            status=ActionExecutionStatus.NOT_STARTED,
        )

        dispatch = self.make_dispatch(
            action_records=(succeeded, failed, not_started),
            overall_status=ActionExecutionStatus.FAILED,
            message="Dispatch completed with partial execution.",
        )

        dispatch.validate()

        self.assertEqual(len(dispatch.action_records), 3)
        self.assertEqual(
            dispatch.action_records[0].status,
            ActionExecutionStatus.SUCCEEDED,
        )
        self.assertEqual(
            dispatch.action_records[1].status,
            ActionExecutionStatus.FAILED,
        )
        self.assertEqual(
            dispatch.action_records[2].status,
            ActionExecutionStatus.NOT_STARTED,
        )

    def test_completed_before_started_is_rejected(self):
        dispatch = self.make_dispatch(
            completed_at=self.started - timedelta(seconds=1)
        )
        with self.assertRaises(ValueError):
            dispatch.validate()

    def test_naive_started_timestamp_is_rejected(self):
        dispatch = self.make_dispatch(
            started_at=datetime(2026, 11, 13, 10, 0)
        )
        with self.assertRaises(ValueError):
            dispatch.validate()

    def test_dispatch_is_immutable(self):
        dispatch = self.make_dispatch()
        with self.assertRaises(FrozenInstanceError):
            dispatch.message = "Changed."


if __name__ == "__main__":
    unittest.main()
