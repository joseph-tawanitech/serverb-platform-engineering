import threading
import unittest

from tap_b21.authorization_ledger import (
    AuthorizationLedgerError,
    GrantStatus,
    InMemoryAuthorizationLedger,
)


class AuthorizationLedgerTests(unittest.TestCase):

    def setUp(self):
        self.ledger = InMemoryAuthorizationLedger()

    def test_register_creates_active_grant(self):
        self.ledger.register("grant-001")
        self.assertEqual(
            self.ledger.get_status("grant-001"),
            GrantStatus.ACTIVE,
        )

    def test_duplicate_registration_is_rejected(self):
        self.ledger.register("grant-001")
        with self.assertRaises(AuthorizationLedgerError):
            self.ledger.register("grant-001")

    def test_revoked_grant_cannot_be_consumed(self):
        self.ledger.register("grant-001")
        self.ledger.revoke("grant-001")
        with self.assertRaises(AuthorizationLedgerError):
            self.ledger.consume("grant-001")

    def test_consumed_grant_cannot_be_reused(self):
        self.ledger.register("grant-001")
        self.ledger.consume("grant-001")
        with self.assertRaises(AuthorizationLedgerError):
            self.ledger.consume("grant-001")

    def test_unknown_grant_is_rejected(self):
        with self.assertRaises(AuthorizationLedgerError):
            self.ledger.consume("unknown-grant")

    def test_empty_grant_id_is_rejected(self):
        with self.assertRaises(AuthorizationLedgerError):
            self.ledger.register(" ")

    def test_concurrent_consumption_allows_only_one_request(self):
        self.ledger.register("grant-001")
        barrier = threading.Barrier(2)
        results = []
        results_lock = threading.Lock()

        def attempt_consumption():
            barrier.wait()
            try:
                self.ledger.consume("grant-001")
                result = "accepted"
            except AuthorizationLedgerError:
                result = "rejected"

            with results_lock:
                results.append(result)

        threads = [
            threading.Thread(target=attempt_consumption)
            for _ in range(2)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(results.count("accepted"), 1)
        self.assertEqual(results.count("rejected"), 1)


if __name__ == "__main__":
    unittest.main()
