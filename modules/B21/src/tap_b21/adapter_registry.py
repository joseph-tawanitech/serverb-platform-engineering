
"""Registry of controlled execution adapters for TAP B21.

The registry maps supported channels and operations to explicitly
registered adapter implementations.

Registration and resolution do not grant execution authority.
Authorization must be independently enforced by the adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .contracts import SUPPORTED_CHANNELS

if TYPE_CHECKING:
    from .adapter_contracts import RemediationAdapter


class AdapterRegistryError(ValueError):
    """Base exception for adapter registry errors."""


class AdapterNotFoundError(AdapterRegistryError):
    """Raised when no registered adapter matches a request."""


class AmbiguousAdapterError(AdapterRegistryError):
    """Raised when multiple adapters match a request."""


@dataclass(frozen=True)
class _RegisteredAdapter:
    """Adapter reference and its validated registration metadata."""

    adapter: RemediationAdapter
    adapter_id: str
    supported_channels: frozenset[str]
    supported_operations: frozenset[str]


class AdapterRegistry:
    """Stores and resolves explicitly registered execution adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, _RegisteredAdapter] = {}

    @staticmethod
    def _validate_text_set(
        values: object,
        field_name: str,
    ) -> frozenset[str]:
        if not isinstance(values, (set, frozenset)):
            raise AdapterRegistryError(
                f"{field_name} must be a set or frozenset"
            )

        if not values:
            raise AdapterRegistryError(
                f"{field_name} must not be empty"
            )

        for value in values:
            if (
                not isinstance(value, str)
                or not value.strip()
                or value != value.strip()
            ):
                raise AdapterRegistryError(
                    f"{field_name} must contain non-empty, trimmed strings"
                )

        return frozenset(values)

    @classmethod
    def _inspect_adapter(
        cls,
        adapter: object,
    ) -> _RegisteredAdapter:
        adapter_id = getattr(adapter, "adapter_id", None)

        if (
            not isinstance(adapter_id, str)
            or not adapter_id.strip()
            or adapter_id != adapter_id.strip()
        ):
            raise AdapterRegistryError(
                "adapter_id must be a non-empty, trimmed string"
            )

        channels = cls._validate_text_set(
            getattr(adapter, "supported_channels", None),
            "supported_channels",
        )

        unsupported_channels = channels - SUPPORTED_CHANNELS

        if unsupported_channels:
            raise AdapterRegistryError(
                "adapter declares unsupported channels: "
                f"{sorted(unsupported_channels)}"
            )

        operations = cls._validate_text_set(
            getattr(adapter, "supported_operations", None),
            "supported_operations",
        )

        for method_name in (
            "validate_execution_request",
            "execute_approved_request",
        ):
            if not callable(getattr(adapter, method_name, None)):
                raise AdapterRegistryError(
                    f"adapter must implement {method_name}()"
                )

        return _RegisteredAdapter(
            adapter=adapter,
            adapter_id=adapter_id,
            supported_channels=channels,
            supported_operations=operations,
        )

    def register(self, adapter: RemediationAdapter) -> None:
        """Register an adapter after validating its interface."""

        registration = self._inspect_adapter(adapter)

        if registration.adapter_id in self._adapters:
            raise AdapterRegistryError(
                f"adapter already registered: {registration.adapter_id}"
            )

        self._adapters[registration.adapter_id] = registration

    def resolve(
        self,
        channel: str,
        operation: str,
    ) -> RemediationAdapter:
        """Resolve exactly one adapter for a channel and operation."""

        if (
            not isinstance(channel, str)
            or channel not in SUPPORTED_CHANNELS
        ):
            raise AdapterRegistryError(
                f"unsupported channel: {channel!r}"
            )

        if (
            not isinstance(operation, str)
            or not operation.strip()
            or operation != operation.strip()
        ):
            raise AdapterRegistryError(
                "operation must be a non-empty, trimmed string"
            )

        matches = [
            registration
            for registration in self._adapters.values()
            if channel in registration.supported_channels
            and operation in registration.supported_operations
        ]

        if not matches:
            raise AdapterNotFoundError(
                f"no adapter registered for {channel}/{operation}"
            )

        if len(matches) > 1:
            adapter_ids = sorted(
                registration.adapter_id
                for registration in matches
            )
            raise AmbiguousAdapterError(
                f"multiple adapters match {channel}/{operation}: "
                f"{adapter_ids}"
            )

        return matches[0].adapter

    @property
    def registered_adapter_ids(self) -> tuple[str, ...]:
        """Return registered adapter IDs in deterministic order."""

        return tuple(sorted(self._adapters))
