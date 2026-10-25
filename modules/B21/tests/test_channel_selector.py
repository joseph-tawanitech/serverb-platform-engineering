import sys
import unittest
from pathlib import Path

B21_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(B21_SRC))

from tap_b21.contracts import RemediationAction
from tap_b21.channel_selector import (
    Capability,
    CapabilityRegistry,
    SelectionStatus,
    select_channel,
)


def make_action(channel="ansible", operation="restart_registered_workload",
                target="payments-api"):
    return RemediationAction(
        action_id="action-1",
        channel=channel,
        operation=operation,
        target=target,
        purpose="Restore the approved workload",
        expected_state="workload_available",
    )


class ChannelSelectorTests(unittest.TestCase):
    def test_selects_unique_matching_channel(self):
        registry = CapabilityRegistry((
            Capability(
                channel="kubernetes",
                operation="restart_registered_workload",
                target="payments-api",
            ),
        ))

        result = select_channel(make_action(), registry)

        self.assertEqual(result.status, SelectionStatus.SELECTED)
        self.assertEqual(result.selected_channel, "kubernetes")

    def test_no_match_returns_no_eligible_channel(self):
        registry = CapabilityRegistry((
            Capability(
                channel="ansible",
                operation="apply_server_configuration",
                target="web-server-1",
            ),
        ))

        result = select_channel(make_action(), registry)

        self.assertEqual(
            result.status,
            SelectionStatus.NO_ELIGIBLE_CHANNEL,
        )
        self.assertIsNone(result.selected_channel)

    def test_multiple_matches_require_resolution(self):
        registry = CapabilityRegistry((
            Capability(
                channel="kubernetes",
                operation="restart_registered_workload",
                target="payments-api",
            ),
            Capability(
                channel="ansible",
                operation="restart_registered_workload",
                target="payments-api",
            ),
        ))

        result = select_channel(make_action(), registry)

        self.assertEqual(result.status, SelectionStatus.AMBIGUOUS)
        self.assertIsNone(result.selected_channel)
        self.assertEqual(
            result.matching_channels,
            ("ansible", "kubernetes"),
        )

    def test_ai_channel_suggestion_cannot_override_registry(self):
        # The proposed action says "ansible", but only Kubernetes
        # has the registered capability for this exact operation/target.
        registry = CapabilityRegistry((
            Capability(
                channel="kubernetes",
                operation="restart_registered_workload",
                target="payments-api",
            ),
        ))

        result = select_channel(
            make_action(channel="ansible"),
            registry,
        )

        self.assertEqual(result.status, SelectionStatus.SELECTED)
        self.assertEqual(result.selected_channel, "kubernetes")

    def test_duplicate_capability_registration_is_rejected(self):
        capability = Capability(
            channel="kubernetes",
            operation="restart_registered_workload",
            target="payments-api",
        )
        registry = CapabilityRegistry((capability,))

        with self.assertRaises(ValueError):
            registry.register(capability)


if __name__ == "__main__":
    unittest.main()
