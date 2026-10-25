import sys
import unittest
from pathlib import Path

B21_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(B21_SRC))

from tap_b21.contracts import (
    RemediationAction,
    RemediationPlan,
    TaskRequest,
)


def make_action(action_id="action-1", channel="kubernetes"):
    return RemediationAction(
        action_id=action_id,
        channel=channel,
        operation="restart_registered_workload",
        target="payments-api",
        purpose="Restore the approved workload",
        expected_state="workload_available",
    )


def make_plan(actions=None):
    return RemediationPlan(
        plan_id="plan-1",
        task_id="task-1",
        summary="Proposed workload recovery",
        actions=tuple(actions or [make_action()]),
        verification_requirements=("workload_available",),
    )


class TaskRequestTests(unittest.TestCase):
    def test_valid_task_request(self):
        request = TaskRequest(
            task_id="task-1",
            incident_id="incident-1",
            target="payments-api",
            environment="test",
            requested_by="operator",
            objective="Investigate workload availability",
        )
        request.validate()

    def test_empty_task_id_is_rejected(self):
        request = TaskRequest(
            task_id=" ",
            incident_id="incident-1",
            target="payments-api",
            environment="test",
            requested_by="operator",
            objective="Investigate workload availability",
        )
        with self.assertRaises(ValueError):
            request.validate()


class RemediationActionTests(unittest.TestCase):
    def test_valid_action(self):
        make_action().validate()

    def test_unsupported_channel_is_rejected(self):
        with self.assertRaises(ValueError):
            make_action(channel="arbitrary_shell").validate()


class RemediationPlanTests(unittest.TestCase):
    def test_valid_plan(self):
        make_plan().validate()

    def test_duplicate_action_ids_are_rejected(self):
        plan = make_plan([
            make_action("duplicate"),
            make_action("duplicate", channel="ansible"),
        ])
        with self.assertRaises(ValueError):
            plan.validate()

    def test_empty_verification_requirements_are_rejected(self):
        plan = RemediationPlan(
            plan_id="plan-1",
            task_id="task-1",
            summary="Proposed recovery",
            actions=(make_action(),),
            verification_requirements=(),
        )
        with self.assertRaises(ValueError):
            plan.validate()


if __name__ == "__main__":
    unittest.main()
