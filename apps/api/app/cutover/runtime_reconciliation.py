from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import MetaData, Table, select

from app.cutover.reconciliation import ReconciliationLevel, ReconciliationReport


@dataclass(frozen=True)
class DatabaseReconciliation:
    engine: Any

    def compare_tables(self, *, legacy_table: str, v2_table: str, legacy_id: str, v2_id: str, fields: tuple[str, ...] = ()) -> ReconciliationReport:
        metadata = MetaData()
        legacy = Table(legacy_table, metadata, autoload_with=self.engine)
        v2 = Table(v2_table, metadata, autoload_with=self.engine)
        report = ReconciliationReport()
        with self.engine.connect() as conn:
            legacy_rows = conn.execute(select(legacy)).mappings().all()
            v2_rows = {str(row[v2_id]): row for row in conn.execute(select(v2)).mappings().all()}
        for row in legacy_rows:
            source_id = str(row[legacy_id])
            target = v2_rows.get(source_id)
            if target is None:
                report.add(source_id, ReconciliationLevel.MISSING_V2, "target row absent")
                continue
            if fields and any(row.get(field) != target.get(field) for field in fields):
                report.add(source_id, ReconciliationLevel.CONFLICT, "selected fields differ", "P0_BLOCKER")
            else:
                report.add(source_id, ReconciliationLevel.MATCH)
        for target_id in set(v2_rows) - {str(row[legacy_id]) for row in legacy_rows}:
            report.add(target_id, ReconciliationLevel.UNEXPECTED_V2, "target has no legacy source")
        return report
