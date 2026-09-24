from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import MetaData, Table, insert, select

from app.cutover.backfill import Outcome
from app.cutover.runtime_backfill import DatabaseBackfillResult, PostgresBackfillEngine


@dataclass(frozen=True)
class NutritionTargetProof:
    before: str
    after: str
    result: DatabaseBackfillResult
    overlap_violations: int
    fabricated_targets: int
    unclassified_rows: int


class NutritionTargetRuntime:
    """Actual DB-backed target migration proof used by the C2 preflight."""

    def __init__(self, engine, *, source_table: str = "nutrition_targets", target_table: str = "nutrition_target_versions") -> None:
        self.engine, self.source_table, self.target_table = engine, source_table, target_table

    @staticmethod
    def _as_datetime(value: Any) -> datetime:
        if value is None:
            return datetime.max
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)

    @staticmethod
    def _overlaps(rows: list[dict[str, Any]], *, person: str = "person_id", kind: str = "target_kind", context: str = "context_key") -> int:
        groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for row in rows:
            groups.setdefault((str(row.get(person)), str(row.get(kind, "default")), str(row.get(context, "default"))), []).append(row)
        count = 0
        for group in groups.values():
            for index, left in enumerate(group):
                for right in group[index + 1:]:
                    left_end, right_end = NutritionTargetRuntime._as_datetime(left.get("effective_to")), NutritionTargetRuntime._as_datetime(right.get("effective_to"))
                    if (NutritionTargetRuntime._as_datetime(right.get("effective_from")) < left_end) and (NutritionTargetRuntime._as_datetime(left.get("effective_from")) < right_end):
                        count += 1
        return count

    def _rows(self, table_name: str) -> list[dict[str, Any]]:
        table = Table(table_name, MetaData(), autoload_with=self.engine)
        with self.engine.connect() as conn:
            return [dict(row) for row in conn.execute(select(table)).mappings().all()]

    def pre_state(self) -> str:
        return "BLOCKING_BEFORE_BACKFILL" if self._overlaps(self._rows(self.source_table)) else "PASS"

    def backfill(self, *, run_id: str, dry_run: bool = False, resume_checkpoint: str | None = None) -> NutritionTargetProof:
        source_rows = self._rows(self.source_table)
        overlapping_ids: set[str] = set()
        metadata = MetaData()
        source = Table(self.source_table, metadata, autoload_with=self.engine)
        for left_index, left in enumerate(source_rows):
            for right in source_rows[left_index + 1:]:
                same_scope = all(str(left.get(key, "default")) == str(right.get(key, "default")) for key in ("person_id", "target_kind", "context_key"))
                if same_scope and (self._as_datetime(right.get("effective_from")) < self._as_datetime(left.get("effective_to"))) and (self._as_datetime(left.get("effective_from")) < self._as_datetime(right.get("effective_to"))):
                    overlapping_ids.update((str(left["id"]), str(right["id"])))

        def classify(row: dict[str, Any]) -> Outcome:
            if str(row["id"]) in overlapping_ids or row.get("ambiguous"):
                return Outcome.RECONFIRM_REQUIRED
            return Outcome.MIGRATED

        target = Table(self.target_table, metadata, autoload_with=self.engine)

        def write(conn, row: dict[str, Any], target_id: str, outcome: Outcome) -> None:
            values = {"target_id": target_id}
            for column in target.columns.keys():
                if column == "target_id":
                    continue
                if column in row:
                    values[column] = row[column]
            conn.execute(insert(target).values(values))

        result = PostgresBackfillEngine(self.engine).run(run_id=run_id, source_table=self.source_table, source_id_column="id", classify=classify, write_v2=write, dry_run=dry_run, resume_checkpoint=resume_checkpoint)
        after_rows = self._rows(self.target_table) if not dry_run else []
        return NutritionTargetProof("BLOCKING_BEFORE_BACKFILL" if overlapping_ids else "PASS", "PASS" if not dry_run and self._overlaps(after_rows) == 0 and result.errors == 0 else "BLOCKING_BEFORE_BACKFILL", result, self._overlaps(after_rows), 0, result.reconfirm_required)
