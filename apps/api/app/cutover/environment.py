from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RuntimeEnvironment(StrEnum):
    LOCAL = "LOCAL"
    TEST = "TEST"
    DISPOSABLE = "DISPOSABLE"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


@dataclass(frozen=True)
class EnvironmentIdentity:
    environment: RuntimeEnvironment
    database_identity: str
    expected_database_identity: str | None = None
    hostname: str | None = None
    expected_hostname: str | None = None

    def is_confirmed(self) -> bool:
        if not self.database_identity.strip() or self.expected_database_identity != self.database_identity:
            return False
        if self.expected_hostname is not None and self.hostname != self.expected_hostname:
            return False
        return True
