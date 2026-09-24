from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import delete, insert, inspect, select, update

from app.cutover.runtime_schema import (
    cutover_audit, cutover_authority, cutover_control, cutover_locks, cutover_runs, cutover_transitions,
    create_runtime_schema,
)
from app.cutover.state import CutoverState


RUNTIME_STATES = frozenset({"LEGACY", "PREFLIGHT_APPROVED", "WRITE_PAUSED", "ASYNC_DRAINED", "MIGRATED", "BACKFILLING", "BACKFILLED", "RECONCILED", "SHADOW_VALIDATED", "V2_READ", "V2_WRITE", "STABILIZING", "V2_ONLY"})
TRANSITIONS = {
    "LEGACY": {"PREFLIGHT_APPROVED"}, "PREFLIGHT_APPROVED": {"WRITE_PAUSED", "LEGACY"},
    "WRITE_PAUSED": {"ASYNC_DRAINED", "LEGACY"}, "ASYNC_DRAINED": {"MIGRATED", "LEGACY"},
    "MIGRATED": {"BACKFILLING", "LEGACY"}, "BACKFILLING": {"BACKFILLED", "LEGACY"},
    "BACKFILLED": {"RECONCILED", "BACKFILLING"}, "RECONCILED": {"SHADOW_VALIDATED", "BACKFILLED"},
    "SHADOW_VALIDATED": {"V2_READ", "RECONCILED"}, "V2_READ": {"V2_WRITE", "SHADOW_VALIDATED"},
    "V2_WRITE": {"STABILIZING", "V2_READ"}, "STABILIZING": {"V2_ONLY", "V2_WRITE"},
    "V2_ONLY": {"STABILIZING"},
}


class RuntimeStore:
    def __init__(self, engine, *, initialize: bool = True) -> None:
        self.engine = engine
        if initialize:
            create_runtime_schema(engine)

    def create_run(self, run_id: str, environment: str, source_revision: str, target_revision: str, *, dry_run: bool, backup_ref: str | None = None) -> None:
        with self.engine.begin() as conn:
            conn.execute(insert(cutover_runs).values(run_id=run_id, environment=environment, source_revision=source_revision, target_revision=target_revision, state="LEGACY", dry_run=dry_run, backup_ref=backup_ref, reader_authority="LEGACY", writer_authority="LEGACY", point_of_no_simple_rollback=False))
            self.audit(conn, run_id, "CREATE_RUN", "PASS", {"dry_run": dry_run})

    def get_run(self, run_id: str) -> dict | None:
        if not inspect(self.engine).has_table(cutover_runs.name):
            return None
        with self.engine.connect() as conn:
            row = conn.execute(select(cutover_runs).where(cutover_runs.c.run_id == run_id)).mappings().first()
            return dict(row) if row else None

    def transition(self, run_id: str, target: str, reason: str) -> None:
        with self.engine.begin() as conn:
            row = conn.execute(select(cutover_runs).where(cutover_runs.c.run_id == run_id)).mappings().first()
            if not row:
                raise ValueError("unknown cutover run")
            current = row["state"]
            if target not in TRANSITIONS.get(current, set()):
                raise ValueError(f"invalid cutover transition {current}->{target}")
            conn.execute(update(cutover_runs).where(cutover_runs.c.run_id == run_id).values(state=target, updated_at=datetime.now(timezone.utc)))
            conn.execute(insert(cutover_transitions).values(run_id=run_id, from_state=current, to_state=target, reason=reason, result="PASS"))
            self.audit(conn, run_id, "TRANSITION", "PASS", {"from": current, "to": target, "reason": reason})

    def audit(self, conn, run_id: str, action: str, result: str, details: dict | None = None) -> None:
        conn.execute(insert(cutover_audit).values(run_id=run_id, action=action, result=result, details=json.dumps(details or {}, sort_keys=True)))

    def set_authority(self, run_id: str, domain: str, *, reader: str, writer: str) -> None:
        if reader not in {"LEGACY", "SHADOW", "V2_COMPAT", "V2"} or writer not in {"LEGACY", "V2"}:
            raise ValueError("unknown authority mode")
        with self.engine.begin() as conn:
            conn.execute(delete(cutover_authority).where(cutover_authority.c.domain == domain))
            conn.execute(insert(cutover_authority).values(domain=domain, reader_mode=reader, writer_mode=writer))
            run = conn.execute(select(cutover_runs.c.run_id).where(cutover_runs.c.run_id == run_id)).first()
            if run:
                conn.execute(update(cutover_runs).where(cutover_runs.c.run_id == run_id).values(reader_authority=reader, writer_authority=writer))
            self.audit(conn, run_id, "AUTHORITY", "PASS", {"domain": domain, "reader": reader, "writer": writer})

    def set_control(self, name: str, enabled: bool, reason: str = "") -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(cutover_control).where(cutover_control.c.control_name == name))
            conn.execute(insert(cutover_control).values(control_name=name, enabled=enabled, reason=reason))

    def control_enabled(self, name: str) -> bool:
        with self.engine.connect() as conn:
            row = conn.execute(select(cutover_control.c.enabled).where(cutover_control.c.control_name == name)).first()
            return bool(row[0]) if row else False
