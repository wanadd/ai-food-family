from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData, String, Table, Text, func


runtime_metadata = MetaData()

cutover_runs = Table(
    "cutover_runtime_runs", runtime_metadata,
    Column("run_id", String(128), primary_key=True), Column("environment", String(32), nullable=False),
    Column("source_revision", String(128), nullable=False), Column("target_revision", String(128), nullable=False),
    Column("state", String(40), nullable=False), Column("backup_ref", String(512)), Column("dry_run", Boolean, nullable=False),
    Column("migration_result", Text), Column("backfill_checkpoint", String(256)), Column("reconciliation_result", Text),
    Column("reader_authority", String(32), nullable=False, default="LEGACY"), Column("writer_authority", String(32), nullable=False, default="LEGACY"),
    Column("point_of_no_simple_rollback", Boolean, nullable=False, default=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
cutover_transitions = Table(
    "cutover_runtime_transitions", runtime_metadata,
    Column("transition_id", Integer, primary_key=True, autoincrement=True), Column("run_id", String(128), nullable=False),
    Column("from_state", String(40), nullable=False), Column("to_state", String(40), nullable=False),
    Column("reason", Text, nullable=False), Column("result", String(32), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
cutover_locks = Table(
    "cutover_runtime_locks", runtime_metadata,
    Column("lock_name", String(128), primary_key=True), Column("run_id", String(128), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
cutover_authority = Table(
    "cutover_runtime_authority", runtime_metadata,
    Column("domain", String(64), primary_key=True), Column("reader_mode", String(32), nullable=False),
    Column("writer_mode", String(32), nullable=False), Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
cutover_control = Table(
    "cutover_runtime_control", runtime_metadata,
    Column("control_name", String(64), primary_key=True), Column("enabled", Boolean, nullable=False), Column("reason", Text),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
cutover_audit = Table(
    "cutover_runtime_audit", runtime_metadata,
    Column("audit_id", Integer, primary_key=True, autoincrement=True), Column("run_id", String(128), nullable=False),
    Column("action", String(96), nullable=False), Column("result", String(32), nullable=False), Column("details", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
backfill_mappings = Table(
    "cutover_runtime_backfill_mappings", runtime_metadata,
    Column("run_id", String(128), primary_key=True), Column("source_table", String(128), primary_key=True),
    Column("source_id", String(256), primary_key=True), Column("target_id", String(256), nullable=False),
    Column("outcome", String(40), nullable=False), Column("checkpoint", String(256), nullable=False),
    Column("payload_hash", String(128)), Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)


def create_runtime_schema(engine) -> None:
    runtime_metadata.create_all(engine)
