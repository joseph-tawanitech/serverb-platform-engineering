
import unittest

from tap_b21.adapter_registry import (
    AdapterNotFoundError,
    AdapterRegistry,
    AdapterRegistryError,
)


class MockAdapter:

    def __init__(
        self,
        adapter_id="mock-adapter",
        channels=frozenset({"kubernetes"}),
        operations=frozenset({"restart_service"}),
    ):
        self._adapter_id = adapter_id
        self._channels = channels
        self._operations = operations

    @property
    def adapter_id(self):
        return self._adapter_id

    @property
    def supported_channels(self):
        return self._channels

    @property
    def supported_operations(self):
        return self._operations

    def validate_execution_request(self, request):
        pass

    def execute_approved_request(self, request):
        raise NotImplementedError


class InvalidAdapter:
    adapter_id = "invalid-adapter"
    supported_channels = frozenset({"kubernetes"})
    supported_operations = frozenset({"restart_service"})


class AdapterRegistryTests(unittest.TestCase):

    def setUp(self):
        self.registry = AdapterRegistry()
        self.adapter = MockAdapter()

    def test_valid_adapter_can_be_registered(self):
        self.registry.register(self.adapter)

        self.assertEqual(
            self.registry.registered_adapter_ids,
            ("mock-adapter",),
        )

    def test_registered_adapter_can_be_resolved(self):
        self.registry.register(self.adapter)

        result = self.registry.resolve(
            "kubernetes",
            "restart_service",
        )

        self.assertIs(result, self.adapter)

    def test_duplicate_adapter_id_is_rejected(self):
        self.registry.register(self.adapter)

        duplicate = MockAdapter()

        with self.assertRaises(AdapterRegistryError):
            self.registry.register(duplicate)

    def test_missing_adapter_is_rejected(self):
        with self.assertRaises(AdapterNotFoundError):
            self.registry.resolve(
                "kubernetes",
                "restart_service",
            )

    def test_unsupported_channel_is_rejected(self):
        with self.assertRaises(AdapterRegistryError):
            self.registry.resolve(
                "terraform",
                "restart_service",
            )

    def test_unsupported_operation_has_no_match(self):
        self.registry.register(self.adapter)

        with self.assertRaises(AdapterNotFoundError):
            self.registry.resolve(
                "kubernetes",
                "delete_server",
            )

    def test_adapter_with_multiple_channels_can_be_registered(self):
        adapter = MockAdapter(
            channels=frozenset({"kubernetes", "ansible"}),
        )

        self.registry.register(adapter)

        self.assertIs(
            self.registry.resolve("kubernetes", "restart_service"),
            adapter,
        )

        self.assertIs(
            self.registry.resolve("ansible", "restart_service"),
            adapter,
        )

    def test_multiple_matching_adapters_are_rejected(self):
        self.registry.register(self.adapter)

        second = MockAdapter(adapter_id="second-adapter")
        self.registry.register(second)

        from tap_b21.adapter_registry import AmbiguousAdapterError

        with self.assertRaises(AmbiguousAdapterError):
            self.registry.resolve(
                "kubernetes",
                "restart_service",
            )

    def test_adapter_without_required_methods_is_rejected(self):
        with self.assertRaises(AdapterRegistryError):
            self.registry.register(InvalidAdapter())

    def test_empty_adapter_id_is_rejected(self):
        adapter = MockAdapter(adapter_id=" ")

        with self.assertRaises(AdapterRegistryError):
            self.registry.register(adapter)

    def test_empty_supported_operations_are_rejected(self):
        adapter = MockAdapter(operations=frozenset())

        with self.assertRaises(AdapterRegistryError):
            self.registry.register(adapter)

    def test_unsupported_registered_channel_is_rejected(self):
        adapter = MockAdapter(
            channels=frozenset({"terraform"}),
        )

        with self.assertRaises(AdapterRegistryError):
            self.registry.register(adapter)

    def test_registered_ids_are_sorted(self):
        self.registry.register(
            MockAdapter(adapter_id="z-adapter")
        )
        self.registry.register(
            MockAdapter(adapter_id="a-adapter")
        )

        self.assertEqual(
            self.registry.registered_adapter_ids,
            ("a-adapter", "z-adapter"),
        )


if __name__ == "__main__":
    unittest.main()
