from __future__ import annotations

import os
from dataclasses import dataclass


class ProductionExecutionBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class ExecutionRequest:
    environment: str
    database_url: str
    dry_run: bool = True
    execute: bool = False
    confirmation_token: str | None = None


def assert_c1_safe(request: ExecutionRequest) -> None:
    identity = f"{request.environment} {request.database_url}".lower()
    if any(token in identity for token in ("prod", "production", "vps")):
        raise ProductionExecutionBlocked("C1 refuses production/VPS database identities")
    if request.execute and request.dry_run:
        raise ProductionExecutionBlocked("execute mode cannot also be dry-run")
    if request.execute and request.confirmation_token != os.getenv("PLANAM_C1_EXECUTE_TOKEN", "C1_LOCAL_EXECUTE"):
        raise ProductionExecutionBlocked("explicit C1 execute token required")


def startup_backfill_forbidden() -> None:
    raise ProductionExecutionBlocked("backfill must never run from application startup")
