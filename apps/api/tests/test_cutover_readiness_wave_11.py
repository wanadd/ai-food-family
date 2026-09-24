from pathlib import Path

import pytest

from app.cutover.backfill import BackfillEngine, BackfillRecord, Outcome
from app.cutover.backup import BackupManifest, restore_local_backup, write_local_backup
from app.cutover.cli import main
from app.cutover.inventory import inventory_counts
from app.cutover.manifest import MigrationClass, manifest_class_counts, manifest_as_dicts
from app.cutover.operations import collect_inventory_report
from app.cutover.reconciliation import ReconciliationLevel, ReconciliationReport, accounting, compare_logical
from app.cutover.safety import ExecutionRequest, ProductionExecutionBlocked, assert_c1_safe, startup_backfill_forbidden
from app.cutover.shadow import run_shadow_read, supported_shadow_flows
from app.cutover.state import CutoverState, CutoverStateMachine


def records():
    return [
        BackfillRecord("identity", "users", "1", MigrationClass.AUTO_MIGRATE),
        BackfillRecord("profile", "user_profiles", "1", MigrationClass.RECONFIRM, ambiguous=True),
        BackfillRecord("health", "health", "1", MigrationClass.RECOMPUTE),
        BackfillRecord("recipes", "recipes", "1", MigrationClass.ARCHIVE_ONLY),
        BackfillRecord("shopping", "shopping_items", "1", MigrationClass.DO_NOT_MIGRATE),
        BackfillRecord("receipts", "receipt_ocr", "1", MigrationClass.RECONFIRM, conflicting=True),
    ]


def test_manifest_is_machine_readable_and_complete():
    manifest = manifest_as_dicts()
    assert manifest
    assert {row["migration_class"] for row in manifest} == {kind.value for kind in MigrationClass}
    assert all(row["legacy_source"] and row["transform_id"] and row["validation_id"] for row in manifest)


def test_backfill_dry_run_execute_is_idempotent_and_preserves_stable_mapping():
    engine = BackfillEngine()
    dry = engine.run(records(), run_id="dry", dry_run=True)
    assert dry.unexplained_source_loss == 0
    assert engine.mapping_store == {}
    first = engine.run(records(), run_id="execute", dry_run=False)
    second = engine.run(records(), run_id="execute-again", dry_run=False)
    assert first.unexplained_source_loss == 0
    assert second.unexplained_source_loss == 0
    assert len(engine.mapping_store) == len(records())
    assert first.reconfirm_required == 2
    assert engine.stable_v2_id("users", "1") == engine.stable_v2_id("users", "1")


def test_backfill_checkpoint_resume_and_failure_classification():
    engine = BackfillEngine()
    with pytest.raises(RuntimeError, match="BACKFILL_INTERRUPTED"):
        engine.run(records(), run_id="resume", dry_run=False, fail_after=2)
    checkpoint = engine.checkpoints["resume"]
    resumed = engine.run(records(), run_id="resume-2", dry_run=False, resume_from=checkpoint)
    assert resumed.processed >= 1
    assert resumed.unexplained_source_loss == 0
    assert Outcome.RECONFIRM_REQUIRED.value == "RECONFIRM_REQUIRED"


def test_reconciliation_levels_and_accounting():
    report = ReconciliationReport()
    report.results.extend(
        [
            compare_logical("same", 1, 1),
            compare_logical("checked", True, False, expected_difference=True, reason="checked is not purchase"),
            compare_logical("missing", 1, None),
        ]
    )
    assert report.counts()[ReconciliationLevel.MATCH.value] == 1
    assert report.counts()[ReconciliationLevel.EXPECTED_DIFFERENCE.value] == 1
    assert report.unexplained_source_loss == 1
    assert accounting(6, {"MIGRATED": 1, "RECOMPUTED": 1, "RECONFIRM_REQUIRED": 2, "ARCHIVED": 1, "SKIPPED_BY_POLICY": 1})


def test_shadow_targets_and_expected_differences():
    assert len(supported_shadow_flows()) == 10
    comparison = run_shadow_read("explicit_empty", lambda: "legacy_missing", lambda: "EMPTY", expected_difference=True)
    assert comparison.result.level is ReconciliationLevel.EXPECTED_DIFFERENCE


def test_cutover_state_machine_rejects_invalid_transitions_and_dual_writers():
    machine = CutoverStateMachine()
    machine.transition(CutoverState.SHADOW)
    machine.transition(CutoverState.WRITE_PAUSED)
    with pytest.raises(ValueError):
        machine.set_writer("V2")
    machine.transition(CutoverState.BACKFILLED)
    machine.transition(CutoverState.RECONCILED)
    machine.set_writer("V2")
    machine.set_reader("V2_COMPAT")
    machine.transition(CutoverState.V2_ACTIVE)
    assert machine.writer_mode == "V2"
    assert machine.reader_mode == "V2_COMPAT"


def test_write_pause_lock_and_release_after_exception():
    machine = CutoverStateMachine()
    with machine.cutover_lock():
        with pytest.raises(RuntimeError, match="CUTOVER_LOCK_HELD"):
            with machine.cutover_lock():
                pass
    with machine.cutover_lock():
        pass
    machine.transition(CutoverState.SHADOW)
    machine.transition(CutoverState.WRITE_PAUSED)
    with pytest.raises(RuntimeError, match="CUTOVER_WRITE_PAUSED"):
        machine.assert_write_allowed()


def test_production_guard_requires_explicit_local_execute_token():
    assert_c1_safe(ExecutionRequest("local", "postgresql://127.0.0.1/test", dry_run=True))
    with pytest.raises(ProductionExecutionBlocked):
        assert_c1_safe(ExecutionRequest("production", "postgresql://db/test"))
    with pytest.raises(ProductionExecutionBlocked):
        assert_c1_safe(ExecutionRequest("local", "postgresql://127.0.0.1/test", dry_run=False, execute=True, confirmation_token="wrong"))
    with pytest.raises(ProductionExecutionBlocked):
        startup_backfill_forbidden()


def test_c1_cli_is_dry_run_by_default(capsys):
    assert main(["preflight", "--environment", "local"]) == 0
    assert "legacy_surfaces" in capsys.readouterr().out


def test_backup_restore_drill_is_local_and_preserves_manifest(tmp_path: Path):
    path = tmp_path / "cutover-backup.json"
    expected = BackupManifest("commit", "20260924_0010", "RECONCILED", "report", {"persons": 2})
    write_local_backup(path, expected, {"explicit_empty": True})
    restored, payload = restore_local_backup(path)
    assert restored == expected
    assert payload == {"explicit_empty": True}


def test_inventory_is_fully_classified_and_authority_is_zero():
    counts = inventory_counts()
    assert counts["legacy_surfaces"] == 25
    assert counts["unclassified_writers"] == 0
    assert counts["unclassified_readers"] == 0
    report = collect_inventory_report()
    assert report.v2_pre_c1 == 59
    assert report.physical_union_pre_c1 == 120
    assert report.authority_overlaps == 0
    assert sum(manifest_class_counts().values()) == len(manifest_as_dicts())
