"""Authorization grant lifecycle and replay-protection contracts.

The in-memory implementation is intended for B21 development and tests.
It is not a production authorization store.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from threading import RLock


class GrantStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    CONSUMED = "CONSUMED"


@dataclass(frozen=True)
class GrantRecord:
    grant_id: str
    status: GrantStatus = GrantStatus.ACTIVE


class AuthorizationLedgerError(ValueError):
    """Raised when an authorization ledger operation is rejected."""


class AuthorizationLedger(ABC):
    """Interface for trusted authorization grant lifecycle storage."""

    @abstractmethod
    def register(self, grant_id: str) -> None:
        """Register a newly issued grant."""

    @abstractmethod
    def revoke(self, grant_id: str) -> None:
        """Revoke an active grant."""

    @abstractmethod
    def get_status(self, grant_id: str) -> GrantStatus:
        """Return the current grant status."""

    @abstractmethod
    def consume(self, grant_id: str) -> None:
        """Atomically consume an active grant exactly once."""


class InMemoryAuthorizationLedger(AuthorizationLedger):
    """Thread-safe, process-local ledger for development and tests only."""

    def __init__(self) -> None:
        self._records: dict[str, GrantRecord] = {}
        self._lock = RLock()

    def register(self, grant_id: str) -> None:
        if not isinstance(grant_id, str) or not grant_id.strip():
            raise AuthorizationLedgerError(
                "grant_id must be a non-empty string"
            )

        with self._lock:
            if grant_id in self._records:
                raise AuthorizationLedgerError(
                    "grant is already registered"
                )

            self._records[grant_id] = GrantRecord(grant_id=grant_id)

    def revoke(self, grant_id: str) -> None:
        with self._lock:
            record = self._records.get(grant_id)

            if record is None:
                raise AuthorizationLedgerError("grant is not registered")

            if record.status is not GrantStatus.ACTIVE:
                raise AuthorizationLedgerError(
                    "only an active grant can be revoked"
                )

            self._records[grant_id] = GrantRecord(
                grant_id=grant_id,
                status=GrantStatus.REVOKED,
            )

    def get_status(self, grant_id: str) -> GrantStatus:
        with self._lock:
            record = self._records.get(grant_id)

            if record is None:
                raise AuthorizationLedgerError("grant is not registered")

            return record.status

    def consume(self, grant_id: str) -> None:
        with self._lock:
            record = self._records.get(grant_id)

            if record is None:
                raise AuthorizationLedgerError("grant is not registered")

            if record.status is GrantStatus.REVOKED:
                raise AuthorizationLedgerError("grant has been revoked")

            if record.status is GrantStatus.CONSUMED:
                raise AuthorizationLedgerError("grant has already been consumed")

            self._records[grant_id] = GrantRecord(
                grant_id=grant_id,
                status=GrantStatus.CONSUMED,
            )
