from __future__ import annotations

import os

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, insert, select

from app.cutover.backfill import Outcome
from app.cutover.environment import EnvironmentIdentity, RuntimeEnvironment
from app.cutover.guard import ExecutionApproval, ProductionGuard, RuntimeGuardError
from app.cutover.runtime_async import AsyncControl
from app.cutover.runtime_authority import AuthorityController
from app.cutover.runtime_backfill import PostgresBackfillEngine
from app.cutover.runtime_lock import RuntimeLock
from app.cutover.runtime_migration import AlembicMigrationOrchestrator
from app.cutover.runtime_pause import WritePause
from app.cutover.runtime_reconciliation import DatabaseReconciliation
from app.cutover.runtime_shadow import PostgresShadowEngine
from app.cutover.runtime_store import RuntimeStore


@pytest.fixture()
def engine():
    return create_engine("sqlite://")


def test_production_guard_fail_closed(monkeypatch):
    identity = EnvironmentIdentity(RuntimeEnvironment.PRODUCTION, "prod-db", "prod-db", "prod-host", "prod-host")
    approval = ExecutionApproval(identity, execute=True, token="secret", backup_reference="b", go_state=True, lock_held=True, current_state="PREFLIGHT_APPROVED")
    monkeypatch.setenv("PLANAM_CUTOVER_EXECUTE_TOKEN", "secret")
    ProductionGuard().authorize(approval)
    with pytest.raises(RuntimeGuardError):
        ProductionGuard().authorize(approval.__class__(identity, execute=True, token="bad", backup_reference="b", go_state=True, lock_held=True, current_state="PREFLIGHT_APPROVED"))


def test_persistent_state_lock_pause_authority_and_async(engine):
    store = RuntimeStore(engine)
    store.create_run("r1", "DISPOSABLE", "legacy", "target", dry_run=True)
    store.transition("r1", "PREFLIGHT_APPROVED", "validated")
    with RuntimeLock(engine, "r1").held():
        with pytest.raises(RuntimeError):
            RuntimeLock(engine, "r2").acquire()
    pause = WritePause(store)
    pause.pause("fixture")
    with pytest.raises(RuntimeError, match="WRITE_PAUSED"):
        pause.assert_allowed()
    pause.resume()
    AuthorityController(store, "r1").set("CORE", reader="V2", writer="V2")
    async_control = AsyncControl(engine, store)
    assert async_control.snapshot().pending == 0


def test_db_backfill_dry_run_execute_rerun_and_resume(engine):
    metadata = MetaData()
    legacy = Table("legacy_people", metadata, Column("id", Integer, primary_key=True), Column("name", String))
    target = Table("v2_people", metadata, Column("id", String, primary_key=True), Column("name", String))
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(insert(legacy), [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}])
    def classify(row):
        return Outcome.MIGRATED if row["name"] else Outcome.RECONFIRM_REQUIRED
    dry = PostgresBackfillEngine(engine, batch_size=1).run(run_id="r1", source_table="legacy_people", source_id_column="id", classify=classify)
    assert dry.processed == 2 and dry.unexplained_source_loss == 0
    def write(conn, row, target_id, outcome):
        conn.execute(insert(target).values(id=target_id, name=row["name"]))
    done = PostgresBackfillEngine(engine, batch_size=1).run(run_id="r1", source_table="legacy_people", source_id_column="id", classify=classify, write_v2=write, dry_run=False)
    again = PostgresBackfillEngine(engine, batch_size=1).run(run_id="r1", source_table="legacy_people", source_id_column="id", classify=classify, write_v2=write, dry_run=False)
    assert done.processed == again.processed == 2
    with engine.connect() as conn:
        assert conn.execute(select(target)).all()


def test_reconciliation_and_shadow_read_real_tables(engine):
    metadata = MetaData()
    legacy = Table("legacy_rows", metadata, Column("id", Integer, primary_key=True), Column("value", String))
    target = Table("v2_rows", metadata, Column("id", Integer, primary_key=True), Column("value", String))
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(insert(legacy), [{"id": 1, "value": "same"}, {"id": 2, "value": "lost"}])
        conn.execute(insert(target), [{"id": 1, "value": "same"}])
    report = DatabaseReconciliation(engine).compare_tables(legacy_table="legacy_rows", v2_table="v2_rows", legacy_id="id", v2_id="id", fields=("value",))
    shadow = PostgresShadowEngine(engine).run(legacy_table="legacy_rows", v2_table="v2_rows", legacy_id="id", v2_id="id", fields=("value",))
    assert report.counts()["MATCH"] == 1 and report.counts()["MISSING_V2"] == 1
    assert shadow.counts() == report.counts()


def test_migration_plan_checks_expected_start(engine):
    plan = AlembicMigrationOrchestrator(engine).plan("target", expected_start=None)
    assert plan.dry_run and plan.target_revision == "target"
