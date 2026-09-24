from __future__ import annotations

from dataclasses import dataclass

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from app.cutover.guard import ExecutionApproval, ProductionGuard


@dataclass(frozen=True)
class MigrationPlan:
    current_revision: str | None
    target_revision: str
    dry_run: bool


class AlembicMigrationOrchestrator:
    def __init__(self, engine, alembic_ini: str = "alembic.ini") -> None:
        self.engine, self.alembic_ini = engine, alembic_ini

    def current_revision(self) -> str | None:
        if not inspect(self.engine).has_table("alembic_version"):
            return None
        with self.engine.connect() as conn:
            row = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).first()
            return str(row[0]) if row else None

    def plan(self, target_revision: str, *, expected_start: str | None = None) -> MigrationPlan:
        current = self.current_revision()
        if expected_start is not None and current != expected_start:
            raise RuntimeError(f"unexpected migration start {current!r}, expected {expected_start!r}")
        return MigrationPlan(current, target_revision, True)

    def upgrade(self, target_revision: str, approval: ExecutionApproval, *, expected_start: str | None = None) -> MigrationPlan:
        ProductionGuard().authorize(approval)
        plan = self.plan(target_revision, expected_start=expected_start)
        config = Config(self.alembic_ini)
        config.set_main_option("sqlalchemy.url", str(self.engine.url))
        command.upgrade(config, target_revision)
        return MigrationPlan(plan.current_revision, self.current_revision() or "", False)
