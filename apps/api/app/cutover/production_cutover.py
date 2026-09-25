"""Fail-closed production cutover orchestration contract.

The adapter owns deployment and domain operations. Existing RuntimeLock,
WritePause, AsyncControl, migration, backfill, reconciliation, shadow, and
authority modules remain the business-operation owners; this module owns only
ordering, durable checkpoints, guards, and stage-aware recovery.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from app.cutover.provenance import ProvenanceError, verify_build_pair


TARGET_REVISION = "fe15c41da8ccd386224b1d690638e231b8d48db4"
LEGACY_STATE = "LEGACY"


class CutoverError(RuntimeError):
    pass


class LiveArmingError(CutoverError):
    pass


class Phase(StrEnum):
    PREFLIGHT = "PREFLIGHT"
    BACKUP_VERIFIED = "BACKUP_VERIFIED"
    LOCKED = "LOCKED"
    WRITE_PAUSED = "WRITE_PAUSED"
    ASYNC_FROZEN = "ASYNC_FROZEN"
    TARGET_DEPLOYED = "TARGET_DEPLOYED"
    PRE_ALEMBIC_VERIFIED = "PRE_ALEMBIC_VERIFIED"
    MIGRATED = "MIGRATED"
    BACKFILLED = "BACKFILLED"
    RECONCILED = "RECONCILED"
    READER_V2 = "READER_V2"
    WRITER_V2 = "WRITER_V2"
    CANARY_VERIFIED = "CANARY_VERIFIED"
    WRITES_REOPENED = "WRITES_REOPENED"
    ASYNC_RESUMED = "ASYNC_RESUMED"
    OBSERVING = "OBSERVING"
    STABILIZING = "STABILIZING"


PHASE_ORDER = (
    Phase.PREFLIGHT,
    Phase.BACKUP_VERIFIED,
    Phase.LOCKED,
    Phase.WRITE_PAUSED,
    Phase.ASYNC_FROZEN,
    Phase.TARGET_DEPLOYED,
    Phase.PRE_ALEMBIC_VERIFIED,
    Phase.MIGRATED,
    Phase.BACKFILLED,
    Phase.RECONCILED,
    Phase.READER_V2,
    Phase.WRITER_V2,
    Phase.CANARY_VERIFIED,
    Phase.WRITES_REOPENED,
    Phase.ASYNC_RESUMED,
    Phase.OBSERVING,
    Phase.STABILIZING,
)


@dataclass(frozen=True)
class CutoverPlan:
    current_head: str
    target_head: str
    delivery_method: str
    api_action: str
    web_action: str
    preserved_server_files: tuple[str, ...]
    affected_containers: tuple[str, ...]
    untouched_containers: tuple[str, ...]
    expected_workers: int
    rollback_artifact: str


@dataclass(frozen=True)
class PreflightReport:
    current_head: str
    current_state: str
    target_exists: bool
    target_provenance: bool
    target_buildable: bool
    api_healthy: bool
    web_healthy: bool
    database_healthy: bool
    redis_healthy: bool
    ingress: dict[str, bool]
    runtime_available: bool
    migration_available: bool
    backfill_available: bool
    reconciliation_available: bool
    shadow_available: bool
    authority_available: bool
    canary_available: bool
    rollback_available: bool

    def failures(self) -> list[str]:
        checks = asdict(self)
        failures: list[str] = []
        for key, value in checks.items():
            if key == "ingress":
                failures.extend(f"ingress:{name}" for name, ok in value.items() if not ok)
            elif key not in {"current_head", "current_state"} and value is False:
                failures.append(key)
        return failures


@dataclass(frozen=True)
class StepResult:
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)


class CutoverAdapter(Protocol):
    """Adapter boundary for accepted deployment/domain owners.

    A production adapter must call the existing accepted modules and must not
    silently substitute fixture logic. The default CLI has no live adapter.
    """

    def preflight(self, target_revision: str) -> PreflightReport: ...

    def step(self, action: str, target_revision: str) -> StepResult: ...

    def rollback_before_migration(self, target_revision: str) -> StepResult: ...


class CheckpointStore(Protocol):
    def load(self) -> dict[str, Any] | None: ...

    def save(self, payload: dict[str, Any]) -> None: ...


class JsonCheckpointStore:
    """Atomic durable checkpoint store for disposable/rehearsal runs."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)


class ProductionCutoverOrchestrator:
    """Order and gate a cutover without owning domain mutation logic."""

    def __init__(self, adapter: CutoverAdapter, checkpoints: CheckpointStore, *, target_revision: str = TARGET_REVISION) -> None:
        self.adapter = adapter
        self.checkpoints = checkpoints
        self.target_revision = target_revision

    @staticmethod
    def arm_live(*, environment: str, live: bool, confirmation: str | None, expected_head: str, current_state: str, expected_target: str = TARGET_REVISION) -> None:
        if environment.upper() != "PRODUCTION":
            raise LiveArmingError("production environment is required")
        if not live:
            raise LiveArmingError("explicit --live is required")
        if expected_target != TARGET_REVISION:
            raise LiveArmingError("unexpected target revision")
        if expected_head != "1348799afc3d1d76dd7a72a13efc2a49a03c5210":
            raise LiveArmingError("unexpected current production HEAD")
        if current_state != LEGACY_STATE:
            raise LiveArmingError("production must start in LEGACY")
        expected_confirmation = os.getenv("PLANAM_CUTOVER_LIVE_CONFIRMATION")
        if not expected_confirmation or confirmation != expected_confirmation:
            raise LiveArmingError("live confirmation does not match operator environment")

    def plan(self, report: PreflightReport, *, delivery_method: str = "immutable-source-revision") -> CutoverPlan:
        return CutoverPlan(
            current_head=report.current_head,
            target_head=self.target_revision,
            delivery_method=delivery_method,
            api_action="build/deploy API image with immutable revision provenance",
            web_action="build/deploy web image with immutable revision provenance",
            preserved_server_files=("docker-compose.prod.yml", "nginx/shared ingress", "production env files"),
            affected_containers=("ai-food-family-api-1", "ai-food-family-web-1"),
            untouched_containers=("planam_money", "avito", "telegram relay", "nginx"),
            expected_workers=2,
            rollback_artifact="previous coherent legacy API/web artifacts",
        )

    def run(self, *, live: bool = False, environment: str = "DISPOSABLE", confirmation: str | None = None, resume: bool = False) -> dict[str, Any]:
        report = self.adapter.preflight(self.target_revision)
        if report.failures():
            raise CutoverError("preflight failed: " + ", ".join(report.failures()))
        if live:
            self.arm_live(environment=environment, live=live, confirmation=confirmation, expected_head=report.current_head, current_state=report.current_state, expected_target=self.target_revision)

        previous = self.checkpoints.load() if resume else None
        start = int(previous.get("phase_index", -1)) + 1 if previous else 0
        results: dict[str, Any] = {"target_revision": self.target_revision, "environment": environment, "phases": []}
        for index, phase in enumerate(PHASE_ORDER):
            if index < start:
                results["phases"].append({"phase": phase.value, "resumed": True})
                continue
            action = phase.value.lower()
            try:
                result = self.adapter.step(action, self.target_revision)
                if not result.passed:
                    raise CutoverError(f"{phase.value} gate failed")
            except Exception:
                if index < PHASE_ORDER.index(Phase.MIGRATED):
                    recovery = self.adapter.rollback_before_migration(self.target_revision)
                    if not recovery.passed:
                        raise CutoverError(f"{phase.value} failed and pre-migration rollback failed")
                raise
            checkpoint = {"target_revision": self.target_revision, "phase": phase.value, "phase_index": index, "details": result.details}
            self.checkpoints.save(checkpoint)
            results["phases"].append({"phase": phase.value, **result.details})
        return results


class NoLiveAdapter:
    """Explicitly non-mutating default for CLI and operator review."""

    def preflight(self, target_revision: str) -> PreflightReport:
        return PreflightReport("", LEGACY_STATE, False, False, False, False, False, False, False, {}, False, False, False, False, False, False, False, False)

    def step(self, action: str, target_revision: str) -> StepResult:
        raise CutoverError("no live adapter is configured")

    def rollback_before_migration(self, target_revision: str) -> StepResult:
        return StepResult(True, {"recovery": "not required"})


class DisposableCutoverAdapter:
    """Deterministic disposable adapter for rehearsal and failure testing.

    It models only operational state transitions. Production adapters must
    delegate each action to the accepted runtime, migration, backfill,
    reconciliation, and canary owners instead of using this fixture.
    """

    def __init__(self, *, failures: set[str] | None = None) -> None:
        self.failures = failures or set()
        self.actions: list[str] = []
        self.state = LEGACY_STATE
        self.write_paused = False
        self.async_frozen = False

    def preflight(self, target_revision: str) -> PreflightReport:
        self.actions.append("preflight")
        return PreflightReport(
            current_head="disposable-legacy",
            current_state=LEGACY_STATE,
            target_exists=True,
            target_provenance=True,
            target_buildable=True,
            api_healthy=True,
            web_healthy=True,
            database_healthy=True,
            redis_healthy=True,
            ingress={"planam": True, "dengi": True, "avito": True},
            runtime_available=True,
            migration_available=True,
            backfill_available=True,
            reconciliation_available=True,
            shadow_available=True,
            authority_available=True,
            canary_available=True,
            rollback_available=True,
        )

    def step(self, action: str, target_revision: str) -> StepResult:
        self.actions.append(action)
        if action in self.failures:
            raise CutoverError(f"injected disposable failure: {action}")
        if action == Phase.WRITE_PAUSED.value.lower():
            self.write_paused = True
        elif action == Phase.ASYNC_FROZEN.value.lower():
            self.async_frozen = True
        elif action == Phase.TARGET_DEPLOYED.value.lower():
            self.state = "V2_TARGET"
        elif action == Phase.WRITES_REOPENED.value.lower():
            self.write_paused = False
        elif action == Phase.ASYNC_RESUMED.value.lower():
            self.async_frozen = False
        return StepResult(True, {"action": action, "state": self.state})

    def rollback_before_migration(self, target_revision: str) -> StepResult:
        self.actions.append("rollback_before_migration")
        self.state = LEGACY_STATE
        self.write_paused = False
        self.async_frozen = False
        return StepResult(True, {"legacy_restored": True})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PLANAM fail-closed production cutover orchestrator")
    parser.add_argument("mode", choices=("status", "preflight", "rehearse", "live", "resume", "postcheck"), nargs="?", default="status")
    parser.add_argument("--environment", default="DISPOSABLE")
    parser.add_argument("--target", default=TARGET_REVISION)
    parser.add_argument("--confirmation")
    parser.add_argument("--checkpoint", default=".local/cutover-checkpoint.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.target != TARGET_REVISION:
        raise SystemExit("target must equal the accepted immutable revision")
    if args.mode == "status":
        print(json.dumps({"mode": "status", "target": TARGET_REVISION, "default_mutating": False}, sort_keys=True))
        return 0
    if args.mode == "preflight":
        print(json.dumps({"mode": "preflight", "target": TARGET_REVISION, "mutates": False, "adapter": "operator-supplied"}, sort_keys=True))
        return 0
    if args.mode in {"live", "resume"}:
        raise SystemExit("live execution requires an explicitly wired production adapter; CLI default is fail-closed")
    print(json.dumps({"mode": args.mode, "target": TARGET_REVISION, "mutates": False, "checkpoint": args.checkpoint}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
