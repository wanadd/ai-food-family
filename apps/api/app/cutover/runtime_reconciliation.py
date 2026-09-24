from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import MetaData, Table, select

from app.cutover.reconciliation import IdentityResolution, IdentityResolutionStatus, ReconciliationLevel, ReconciliationReport


class ReconciliationIdentityAdapter:
    """Explicit identity bridge for domains whose V2 PK differs from legacy PK."""

    def __init__(self, *, legacy_id: str = "id", v2_id: str = "id") -> None:
        self.legacy_id, self.v2_id = legacy_id, v2_id

    def legacy_identity(self, row: dict[str, Any]) -> str:
        return str(row[self.legacy_id])

    def v2_identity(self, row: dict[str, Any]) -> str | None:
        return str(row[self.v2_id])

    def resolve_v2_identity(self, row: dict[str, Any], v2_by_identity: dict[str, list[dict[str, Any]]]) -> IdentityResolution:
        identity = self.legacy_identity(row)
        if identity in v2_by_identity:
            return IdentityResolution(IdentityResolutionStatus.RESOLVED, identity)
        return IdentityResolution(IdentityResolutionStatus.MISSING_MAPPING, reason="no persisted identity bridge")

    def select_v2_row(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return sorted(rows, key=lambda row: str(row.get("effective_from", "")))[-1]

    def payload_matches(self, legacy: dict[str, Any], v2: dict[str, Any], fields: tuple[str, ...]) -> bool:
        return not fields or not any(legacy.get(field) != v2.get(field) for field in fields)


@dataclass(frozen=True)
class DatabaseReconciliation:
    engine: Any

    def compare_tables(
        self,
        *,
        legacy_table: str,
        v2_table: str,
        legacy_id: str,
        v2_id: str,
        fields: tuple[str, ...] = (),
        identity_adapter: ReconciliationIdentityAdapter | None = None,
    ) -> ReconciliationReport:
        metadata = MetaData()
        legacy = Table(legacy_table, metadata, autoload_with=self.engine)
        v2 = Table(v2_table, metadata, autoload_with=self.engine)
        report = ReconciliationReport()
        with self.engine.connect() as conn:
            legacy_rows = conn.execute(select(legacy)).mappings().all()
            v2_rows = [dict(row) for row in conn.execute(select(v2)).mappings().all()]
        adapter = identity_adapter or ReconciliationIdentityAdapter(legacy_id=legacy_id, v2_id=v2_id)
        v2_by_identity: dict[str, list[dict[str, Any]]] = {}
        invalid_v2_rows: list[dict[str, Any]] = []
        for row in v2_rows:
            identity = adapter.v2_identity(row)
            if identity is None:
                invalid_v2_rows.append(row)
            else:
                v2_by_identity.setdefault(identity, []).append(row)
        expected_identities: dict[str, list[str]] = {}
        for row in legacy_rows:
            source_id = str(row[legacy_id])
            resolution = adapter.resolve_v2_identity(row, v2_by_identity)
            if resolution.status is not IdentityResolutionStatus.RESOLVED or resolution.canonical_id is None:
                report.add(source_id, ReconciliationLevel.MISSING_V2, resolution.reason or resolution.status.value, "P0_BLOCKER", resolution.status)
                continue
            expected_identities.setdefault(resolution.canonical_id, []).append(source_id)
            targets = v2_by_identity.get(resolution.canonical_id, [])
            if not targets:
                report.add(source_id, ReconciliationLevel.MISSING_V2, "mapped V2 entity absent", "P0_BLOCKER", IdentityResolutionStatus.RESOLVED)
                continue
            if len(expected_identities[resolution.canonical_id]) > 1:
                report.add(source_id, ReconciliationLevel.CONFLICT, "multiple legacy entities map to one V2 logical entity", "P0_BLOCKER", IdentityResolutionStatus.CONFLICTING_MAPPING)
                continue
            target = adapter.select_v2_row(targets)
            if not adapter.payload_matches(row, target, fields):
                report.add(source_id, ReconciliationLevel.CONFLICT, "selected fields differ", "P0_BLOCKER", IdentityResolutionStatus.RESOLVED)
            else:
                report.add(source_id, ReconciliationLevel.MATCH, identity_resolution=IdentityResolutionStatus.RESOLVED)
        resolved_ids = set(expected_identities)
        for target_id, targets in v2_by_identity.items():
            if target_id not in resolved_ids:
                report.add(target_id, ReconciliationLevel.UNEXPECTED_V2, "target has no legacy source", "P0_BLOCKER", IdentityResolutionStatus.INVALID_MAPPING)
        for index, row in enumerate(invalid_v2_rows):
            report.add(f"{v2_id}:{index}", ReconciliationLevel.UNEXPECTED_V2, "V2 row has invalid identity mapping", "P0_BLOCKER", IdentityResolutionStatus.INVALID_MAPPING)
        return report
