from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine, insert

from app.cutover.reconciliation import IdentityResolution, IdentityResolutionStatus, ReconciliationLevel
from app.cutover.runtime_reconciliation import DatabaseReconciliation, ReconciliationIdentityAdapter


class RenamedIdentityAdapter(ReconciliationIdentityAdapter):
    def __init__(self, mappings=None, ambiguous=False):
        self.mappings = mappings or {}
        self.ambiguous = ambiguous

    def legacy_identity(self, row):
        return f"logical:{row['id']}"

    def v2_identity(self, row):
        return row.get("logical_id")

    def resolve_v2_identity(self, row, v2_by_identity):
        if self.ambiguous:
            return IdentityResolution(IdentityResolutionStatus.AMBIGUOUS_MAPPING, reason="fixture ambiguity")
        canonical = self.mappings.get(str(row["id"]))
        if canonical is None:
            return IdentityResolution(IdentityResolutionStatus.MISSING_MAPPING, reason="fixture mapping absent")
        return IdentityResolution(IdentityResolutionStatus.RESOLVED, canonical)


def _tables(rows, v2_rows):
    engine = create_engine("sqlite://")
    metadata = MetaData()
    legacy = Table("legacy_targets", metadata, Column("id", Integer, primary_key=True), Column("value", Integer))
    v2 = Table("v2_targets", metadata, Column("target_id", String, primary_key=True), Column("logical_id", String), Column("value", Integer), Column("effective_from", DateTime))
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(insert(legacy), rows)
        if v2_rows:
            conn.execute(insert(v2), v2_rows)
    return engine


def test_renamed_identity_with_explicit_mapping_is_match():
    engine = _tables([{"id": 1, "value": 10}], [{"target_id": "stable-1", "logical_id": "logical:1", "value": 10}])
    report = DatabaseReconciliation(engine).compare_tables(legacy_table="legacy_targets", v2_table="v2_targets", legacy_id="id", v2_id="target_id", fields=("value",), identity_adapter=RenamedIdentityAdapter({"1": "logical:1"}))
    assert report.counts()[ReconciliationLevel.MATCH.value] == 1
    assert report.counts()[ReconciliationLevel.MISSING_V2.value] == 0


def test_missing_mapping_is_explicit_blocker():
    engine = _tables([{"id": 1, "value": 10}], [{"target_id": "stable-1", "logical_id": "logical:1", "value": 10}])
    report = DatabaseReconciliation(engine).compare_tables(legacy_table="legacy_targets", v2_table="v2_targets", legacy_id="id", v2_id="target_id", identity_adapter=RenamedIdentityAdapter())
    assert report.results[0].identity_resolution is IdentityResolutionStatus.MISSING_MAPPING
    assert report.counts()[ReconciliationLevel.MISSING_V2.value] == 1


def test_mapping_to_missing_v2_is_missing_v2():
    engine = _tables([{"id": 1, "value": 10}], [])
    report = DatabaseReconciliation(engine).compare_tables(legacy_table="legacy_targets", v2_table="v2_targets", legacy_id="id", v2_id="target_id", identity_adapter=RenamedIdentityAdapter({"1": "logical:1"}))
    assert report.results[0].identity_resolution is IdentityResolutionStatus.RESOLVED
    assert report.counts()[ReconciliationLevel.MISSING_V2.value] == 1


def test_extra_v2_entity_is_not_suppressed():
    engine = _tables([], [{"target_id": "stable-extra", "logical_id": "logical:extra", "value": 10}])
    report = DatabaseReconciliation(engine).compare_tables(legacy_table="legacy_targets", v2_table="v2_targets", legacy_id="id", v2_id="target_id", identity_adapter=RenamedIdentityAdapter())
    assert report.counts()[ReconciliationLevel.UNEXPECTED_V2.value] == 1


def test_ambiguous_mapping_is_blocking_and_typed():
    engine = _tables([{"id": 1, "value": 10}], [{"target_id": "stable-a", "logical_id": "logical:a", "value": 10}, {"target_id": "stable-b", "logical_id": "logical:b", "value": 10}])
    report = DatabaseReconciliation(engine).compare_tables(legacy_table="legacy_targets", v2_table="v2_targets", legacy_id="id", v2_id="target_id", identity_adapter=RenamedIdentityAdapter(ambiguous=True))
    assert report.results[0].identity_resolution is IdentityResolutionStatus.AMBIGUOUS_MAPPING
    assert report.results[0].severity == "P0_BLOCKER"


def test_identity_match_does_not_hide_payload_conflict():
    engine = _tables([{"id": 1, "value": 10}], [{"target_id": "stable-1", "logical_id": "logical:1", "value": 11}])
    report = DatabaseReconciliation(engine).compare_tables(legacy_table="legacy_targets", v2_table="v2_targets", legacy_id="id", v2_id="target_id", fields=("value",), identity_adapter=RenamedIdentityAdapter({"1": "logical:1"}))
    assert report.counts()[ReconciliationLevel.CONFLICT.value] == 1


def test_multiple_versions_share_logical_identity_and_latest_is_compared():
    engine = _tables([{"id": 1, "value": 11}], [
        {"target_id": "stable-old", "logical_id": "logical:1", "value": 10, "effective_from": datetime(2026, 1, 1)},
        {"target_id": "stable-current", "logical_id": "logical:1", "value": 11, "effective_from": datetime(2026, 2, 1)},
    ])
    report = DatabaseReconciliation(engine).compare_tables(legacy_table="legacy_targets", v2_table="v2_targets", legacy_id="id", v2_id="target_id", fields=("value",), identity_adapter=RenamedIdentityAdapter({"1": "logical:1"}))
    assert report.counts()[ReconciliationLevel.MATCH.value] == 1
    assert report.counts()[ReconciliationLevel.UNEXPECTED_V2.value] == 0


def test_reconciliation_rerun_is_deterministic():
    engine = _tables([{"id": 1, "value": 10}], [{"target_id": "stable-1", "logical_id": "logical:1", "value": 10}])
    reconciler = DatabaseReconciliation(engine)
    kwargs = dict(legacy_table="legacy_targets", v2_table="v2_targets", legacy_id="id", v2_id="target_id", fields=("value",), identity_adapter=RenamedIdentityAdapter({"1": "logical:1"}))
    first = reconciler.compare_tables(**kwargs)
    second = reconciler.compare_tables(**kwargs)
    assert first.results == second.results
