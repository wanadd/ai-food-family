from __future__ import annotations

import hmac
import os
from dataclasses import dataclass

from app.cutover.environment import EnvironmentIdentity, RuntimeEnvironment


class RuntimeGuardError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExecutionApproval:
    identity: EnvironmentIdentity
    execute: bool = False
    token: str | None = None
    backup_reference: str | None = None
    go_state: bool = False
    lock_held: bool = False
    current_state: str = "LEGACY"
    expected_state: str = "PREFLIGHT_APPROVED"
    source_revision: str | None = None
    expected_source_revision: str | None = None


class ProductionGuard:
    """Fail-closed authorization boundary for runtime mutation."""

    def __init__(self, token_env: str = "PLANAM_CUTOVER_EXECUTE_TOKEN") -> None:
        self.token_env = token_env

    def authorize(self, approval: ExecutionApproval) -> None:
        if not approval.execute:
            raise RuntimeGuardError("execute authorization is required")
        if approval.identity.environment is not RuntimeEnvironment.PRODUCTION:
            raise RuntimeGuardError("production execution requires PRODUCTION environment")
        if not approval.identity.is_confirmed():
            raise RuntimeGuardError("production database identity is not confirmed")
        expected = os.getenv(self.token_env)
        if not expected or not approval.token or not hmac.compare_digest(expected, approval.token):
            raise RuntimeGuardError("invalid or missing execute token")
        if not approval.backup_reference:
            raise RuntimeGuardError("backup reference is required")
        if not approval.go_state:
            raise RuntimeGuardError("preflight GO state is required")
        if not approval.lock_held:
            raise RuntimeGuardError("cutover lock is required")
        if approval.current_state != approval.expected_state:
            raise RuntimeGuardError("unexpected cutover state")
        if approval.expected_source_revision is not None and approval.source_revision != approval.expected_source_revision:
            raise RuntimeGuardError("unexpected schema revision")

    @staticmethod
    def assert_dry_run(identity: EnvironmentIdentity) -> None:
        if not identity.database_identity or not identity.is_confirmed():
            raise RuntimeGuardError("dry-run database identity is not confirmed")
