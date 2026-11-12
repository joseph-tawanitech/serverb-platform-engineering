
import sys
import unittest
from pathlib import Path

B21_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(B21_SRC))

from tap_b21.workflow import (
    InvalidTransitionError,
    Workflow,
    WorkflowState,
)


class WorkflowTests(unittest.TestCase):

    def test_workflow_starts_as_accepted(self):
        workflow = Workflow("task-1")
        self.assertEqual(workflow.state, WorkflowState.ACCEPTED)

    def test_investigation_reaches_governance_pending(self):
        workflow = Workflow("task-1")

        workflow.transition(WorkflowState.INVESTIGATING)
        workflow.transition(WorkflowState.PLAN_PROPOSED)
        workflow.transition(WorkflowState.GOVERNANCE_PENDING)

        self.assertEqual(
            workflow.state,
            WorkflowState.GOVERNANCE_PENDING,
        )

    def test_direct_authorization_bypass_is_rejected(self):
        workflow = Workflow("task-1")

        workflow.transition(WorkflowState.INVESTIGATING)
        workflow.transition(WorkflowState.PLAN_PROPOSED)
        workflow.transition(WorkflowState.GOVERNANCE_PENDING)

        with self.assertRaises(InvalidTransitionError):
            workflow.transition(WorkflowState.AUTHORIZED)

        self.assertEqual(
            workflow.state,
            WorkflowState.GOVERNANCE_PENDING,
        )

    def test_authorized_workflow_cannot_execute_through_ordinary_transition(self):
        workflow = Workflow("task-1")

        workflow.transition(WorkflowState.INVESTIGATING)
        workflow.transition(WorkflowState.PLAN_PROPOSED)
        workflow.transition(WorkflowState.GOVERNANCE_PENDING)

        workflow._authorize_after_trusted_checks("grant-test")

        self.assertEqual(
            workflow.state,
            WorkflowState.AUTHORIZED,
        )

        with self.assertRaises(InvalidTransitionError):
            workflow.transition(WorkflowState.EXECUTING)

        self.assertEqual(
            workflow.state,
            WorkflowState.AUTHORIZED,
        )

    def test_valid_grant_allows_execution_transition(self):
        workflow = Workflow("task-1")

        workflow.transition(WorkflowState.INVESTIGATING)
        workflow.transition(WorkflowState.PLAN_PROPOSED)
        workflow.transition(WorkflowState.GOVERNANCE_PENDING)
        workflow._authorize_after_trusted_checks("grant-test")

        workflow._begin_execution_after_trusted_checks("grant-test")

        self.assertEqual(
            workflow.state,
            WorkflowState.EXECUTING,
        )

    def test_wrong_grant_rejects_execution_transition(self):
        workflow = Workflow("task-1")

        workflow.transition(WorkflowState.INVESTIGATING)
        workflow.transition(WorkflowState.PLAN_PROPOSED)
        workflow.transition(WorkflowState.GOVERNANCE_PENDING)
        workflow._authorize_after_trusted_checks("grant-test")

        with self.assertRaises(ValueError):
            workflow._begin_execution_after_trusted_checks("wrong-grant")

        self.assertEqual(
            workflow.state,
            WorkflowState.AUTHORIZED,
        )

    def test_empty_grant_rejects_execution_transition(self):
        workflow = Workflow("task-1")

        workflow.transition(WorkflowState.INVESTIGATING)
        workflow.transition(WorkflowState.PLAN_PROPOSED)
        workflow.transition(WorkflowState.GOVERNANCE_PENDING)
        workflow._authorize_after_trusted_checks("grant-test")

        with self.assertRaises(ValueError):
            workflow._begin_execution_after_trusted_checks("")

        self.assertEqual(
            workflow.state,
            WorkflowState.AUTHORIZED,
        )

    def test_unauthorized_workflow_cannot_begin_execution(self):
        workflow = Workflow("task-1")

        with self.assertRaises(ValueError):
            workflow._begin_execution_after_trusted_checks("grant-test")

        self.assertEqual(
            workflow.state,
            WorkflowState.ACCEPTED,
        )

    def test_cannot_skip_directly_to_execution(self):
        workflow = Workflow("task-1")

        with self.assertRaises(InvalidTransitionError):
            workflow.transition(WorkflowState.EXECUTING)

    def test_cannot_complete_without_verification_stage(self):
        workflow = Workflow("task-1")

        with self.assertRaises(InvalidTransitionError):
            workflow.transition(WorkflowState.COMPLETED)

    def test_failed_workflow_is_terminal(self):
        workflow = Workflow("task-1")
        workflow.transition(WorkflowState.INVESTIGATING)
        workflow.transition(WorkflowState.FAILED)

        with self.assertRaises(InvalidTransitionError):
            workflow.transition(WorkflowState.INVESTIGATING)

    def test_empty_task_id_is_rejected(self):
        with self.assertRaises(ValueError):
            Workflow(" ")


if __name__ == "__main__":
    unittest.main()
