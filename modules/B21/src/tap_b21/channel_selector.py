"""Environment-aware capability selection for TAP B21.

Selection identifies registered capabilities. It does not authorize
or execute remediation operations.
"""

from dataclasses import dataclass
from enum import Enum

from tap_b21.contracts import RemediationAction, SUPPORTED_CHANNELS


class SelectionStatus(str, Enum):
    SELECTED = "SELECTED"
    NO_ELIGIBLE_CHANNEL = "NO_ELIGIBLE_CHANNEL"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class Capability:
    channel: str
    operation: str
    target: str
    environment: str = "lab"

    def validate(self) -> None:
        if self.channel not in SUPPORTED_CHANNELS:
            raise ValueError(f"unsupported channel: {self.channel}")

        for name, value in (
            ("operation", self.operation),
            ("target", self.target),
            ("environment", self.environment),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True)
class ChannelSelection:
    status: SelectionStatus
    selected_channel: str | None
    matching_channels: tuple[str, ...]
    reason: str


class CapabilityRegistry:
    """Stores explicitly registered channel capabilities."""

    def __init__(self, capabilities: tuple[Capability, ...] = ()):
        self._capabilities: list[Capability] = []
        for capability in capabilities:
            self.register(capability)

    def register(self, capability: Capability) -> None:
        if not isinstance(capability, Capability):
            raise TypeError("capability must be a Capability")

        capability.validate()

        if capability in self._capabilities:
            raise ValueError("duplicate capability registration")

        self._capabilities.append(capability)

    def find_matches(
        self,
        action: RemediationAction,
        environment: str = "lab",
    ) -> tuple[str, ...]:
        """Find capabilities matching operation, target and environment."""

        action.validate()

        if not isinstance(environment, str) or not environment.strip():
            raise ValueError("environment must be a non-empty string")

        matches = {
            capability.channel
            for capability in self._capabilities
            if capability.operation == action.operation
            and capability.target == action.target
            and capability.environment == environment
        }

        return tuple(sorted(matches))


def select_channel(
    action: RemediationAction,
    registry: CapabilityRegistry,
    environment: str = "lab",
) -> ChannelSelection:
    """Select a channel only when exactly one capability matches."""

    if not isinstance(action, RemediationAction):
        raise TypeError("action must be a RemediationAction")

    if not isinstance(registry, CapabilityRegistry):
        raise TypeError("registry must be a CapabilityRegistry")

    action.validate()

    matches = registry.find_matches(action, environment)

    if not matches:
        return ChannelSelection(
            status=SelectionStatus.NO_ELIGIBLE_CHANNEL,
            selected_channel=None,
            matching_channels=(),
            reason=(
                "No registered capability matches this operation, "
                "target and environment."
            ),
        )

    if len(matches) > 1:
        return ChannelSelection(
            status=SelectionStatus.AMBIGUOUS,
            selected_channel=None,
            matching_channels=matches,
            reason=(
                "Multiple channels match; explicit selection policy "
                "or human review is required."
            ),
        )

    selected = matches[0]

    return ChannelSelection(
        status=SelectionStatus.SELECTED,
        selected_channel=selected,
        matching_channels=matches,
        reason=(
            "Exactly one registered capability matches the operation, "
            "target and environment."
        ),
    )
