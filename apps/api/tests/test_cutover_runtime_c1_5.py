from __future__ import annotations

import os

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, insert, select, text

from app.cutover.backfill import Outcome
from app.cutover.environment import EnvironmentIdentity, RuntimeEnvironment
from app.cutover.application_boundary import ApplicationMutationBlocked, CutoverExecutionContext, async_execution, cutover_execution
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
from app.cutover.writer_inventory import writer_coverage
from app.cutover.nutrition_target_runtime import NutritionTargetRuntime
from datetime import datetime, timedelta


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


def test_application_session_boundary_blocks_pause_and_authority(engine):
    from sqlalchemy.orm import DeclarativeBase, Session

    class Base(DeclarativeBase):
        pass

    class LegacyRow(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        name = Column(String)

    Base.metadata.create_all(engine)
    store = RuntimeStore(engine)
    store.set_control("WRITE_PAUSED", True, "test")
    with pytest.raises(ApplicationMutationBlocked):
        with Session(engine) as session:
            session.add(LegacyRow(id=1, name="blocked"))
            session.commit()
    store.set_control("WRITE_PAUSED", False, "resume")
    store.set_authority("r1", "CORE", reader="LEGACY", writer="V2")
    with pytest.raises(ApplicationMutationBlocked, match="WRITER_AUTHORITY"):
        with Session(engine) as session:
            session.add(LegacyRow(id=2, name="blocked"))
            session.commit()
    store.set_authority("r1", "CORE", reader="LEGACY", writer="LEGACY")
    store.set_control("ASYNC_FROZEN", True, "test")
    with pytest.raises(ApplicationMutationBlocked, match="ASYNC_FROZEN"):
        with async_execution(), Session(engine) as session:
            session.add(LegacyRow(id=3, name="blocked"))
            session.commit()


def test_application_session_boundary_blocks_raw_dml(engine):
    from sqlalchemy.orm import Session

    metadata = MetaData()
    Table("users", metadata, Column("id", Integer, primary_key=True), Column("name", String))
    metadata.create_all(engine)
    store = RuntimeStore(engine)
    store.set_control("WRITE_PAUSED", True, "raw-dml")
    with pytest.raises(ApplicationMutationBlocked, match="CUTOVER_WRITE_PAUSED"):
        with Session(engine) as session:
            session.execute(text("INSERT INTO users (id, name) VALUES (1, 'blocked')"))
            session.commit()


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


def test_writer_inventory_is_fully_guarded():
    coverage = writer_coverage()
    assert coverage["unclassified"] == 0
    assert coverage["unguarded"] == 0
    assert coverage["coverage_percent"] == 100.0


def test_nutrition_target_runtime_proves_blocking_to_pass(engine):
    metadata = MetaData()
    source = Table("nutrition_targets", metadata, Column("id", Integer, primary_key=True), Column("person_id", String), Column("target_kind", String), Column("context_key", String), Column("effective_from", String), Column("effective_to", String), Column("ambiguous", Integer, default=0))
    target = Table("nutrition_target_versions", metadata, Column("target_id", String, primary_key=True), Column("person_id", String), Column("target_kind", String), Column("context_key", String), Column("effective_from", String), Column("effective_to", String))
    metadata.create_all(engine)
    start = datetime(2026, 1, 1).isoformat()
    overlap = datetime(2026, 1, 10).isoformat()
    end = datetime(2026, 2, 1).isoformat()
    with engine.begin() as conn:
        conn.execute(insert(source), [{"id": 1, "person_id": "p1", "target_kind": "CALORIES", "context_key": "default", "effective_from": start, "effective_to": end}, {"id": 2, "person_id": "p1", "target_kind": "CALORIES", "context_key": "default", "effective_from": overlap, "effective_to": None}])
    runtime = NutritionTargetRuntime(engine)
    assert runtime.pre_state() == "BLOCKING_BEFORE_BACKFILL"
    proof = runtime.backfill(run_id="nutrition", dry_run=False)
    assert proof.after == "PASS"
    assert proof.overlap_violations == 0
    assert proof.result.reconfirm_required == 2


def test_invalid_bypass_and_resume_are_rejected(engine):
    store = RuntimeStore(engine)
    store.create_run("r-bypass", "DISPOSABLE", "legacy", "target", dry_run=False)
    from sqlalchemy.orm import DeclarativeBase, Session

    class Base(DeclarativeBase):
        pass

    class Row(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        name = Column(String)

    Base.metadata.create_all(engine)
    with pytest.raises(ApplicationMutationBlocked, match="INVALID_CUTOVER"):
        with cutover_execution(CutoverExecutionContext("r-bypass", "PRODUCTION")), Session(engine) as session:
            session.add(Row(id=1, name="blocked"))
            session.commit()
    metadata = MetaData()
    source = Table("resume_source", metadata, Column("id", Integer, primary_key=True))
    metadata.create_all(engine)
    with pytest.raises(ValueError, match="INVALID_BACKFILL_CHECKPOINT"):
        PostgresBackfillEngine(engine).run(run_id="resume", source_table="resume_source", source_id_column="id", classify=lambda _: Outcome.MIGRATED, resume_checkpoint="missing")
