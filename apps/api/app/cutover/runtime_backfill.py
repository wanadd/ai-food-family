from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable

from sqlalchemy import MetaData, Table, insert, select

from app.cutover.backfill import Outcome
from app.cutover.runtime_schema import backfill_mappings
from app.cutover.runtime_schema import create_runtime_schema


@dataclass(frozen=True)
class DatabaseBackfillResult:
    run_id: str
    dry_run: bool
    processed: int = 0
    migrated: int = 0
    recomputed: int = 0
    reconfirm_required: int = 0
    archived: int = 0
    skipped_by_policy: int = 0
    errors: int = 0
    checkpoint: str | None = None

    @property
    def unexplained_source_loss(self) -> int:
        return self.processed - sum((self.migrated, self.recomputed, self.reconfirm_required, self.archived, self.skipped_by_policy, self.errors))

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__ | {"unexplained_source_loss": self.unexplained_source_loss}


class PostgresBackfillEngine:
    """Bounded, transactional DB backfill. The callback performs domain-specific V2 writes."""

    def __init__(self, engine, *, batch_size: int = 100) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        self.engine, self.batch_size = engine, batch_size
        create_runtime_schema(engine)

    @staticmethod
    def stable_target_id(source_table: str, source_id: str) -> str:
        return hashlib.sha256(f"planam-v2:{source_table}:{source_id}".encode()).hexdigest()[:32]

    def run(self, *, run_id: str, source_table: str, source_id_column: str, classify: Callable[[dict[str, Any]], Outcome], write_v2: Callable[[Any, dict[str, Any], str, Outcome], None] | None = None, dry_run: bool = True, resume_checkpoint: str | None = None) -> DatabaseBackfillResult:
        metadata = MetaData()
        source = Table(source_table, metadata, autoload_with=self.engine)
        result = DatabaseBackfillResult(run_id=run_id, dry_run=dry_run)
        last = resume_checkpoint
        counts = {"processed": 0, "migrated": 0, "recomputed": 0, "reconfirm_required": 0, "archived": 0, "skipped_by_policy": 0, "errors": 0}
        while True:
            with self.engine.connect() as conn:
                query = select(source).order_by(source.c[source_id_column]).limit(self.batch_size)
                if last is not None:
                    query = query.where(source.c[source_id_column] > last)
                rows = [dict(row) for row in conn.execute(query).mappings().all()]
            if not rows:
                break
            with self.engine.begin() as conn:
                for row in rows:
                    source_id = str(row[source_id_column])
                    target_id = self.stable_target_id(source_table, source_id)
                    outcome = classify(row)
                    counts["processed"] += 1
                    key = {Outcome.MIGRATED: "migrated", Outcome.RECOMPUTED: "recomputed", Outcome.RECONFIRM_REQUIRED: "reconfirm_required", Outcome.ARCHIVED: "archived", Outcome.SKIPPED_BY_POLICY: "skipped_by_policy", Outcome.ERROR: "errors"}[outcome]
                    counts[key] += 1
                    if not dry_run:
                        if write_v2 is None:
                            raise ValueError("write_v2 callback is required for execute mode")
                        existing = conn.execute(select(backfill_mappings.c.target_id).where(backfill_mappings.c.run_id == run_id, backfill_mappings.c.source_table == source_table, backfill_mappings.c.source_id == source_id)).first()
                        if existing is None:
                            write_v2(conn, row, target_id, outcome)
                            conn.execute(insert(backfill_mappings).values(run_id=run_id, source_table=source_table, source_id=source_id, target_id=target_id, outcome=outcome.value, checkpoint=source_id, payload_hash=hashlib.sha256(json.dumps(row, default=str, sort_keys=True).encode()).hexdigest()))
                    last = source_id
        return DatabaseBackfillResult(run_id=run_id, dry_run=dry_run, checkpoint=last, **counts)
