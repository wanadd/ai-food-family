from __future__ import annotations

import json

import pytest

from app.cutover.artifact_delivery import ArtifactDeliveryContract, ArtifactDeliveryError
from app.cutover.production_cutover import (
    LEGACY_STATE,
    PHASE_ORDER,
    TARGET_REVISION,
    CutoverError,
    DisposableCutoverAdapter,
    JsonCheckpointStore,
    LiveArmingError,
    PreflightReport,
    ProductionCutoverOrchestrator,
    StepResult,
    build_parser,
    main,
)
from app.cutover.provenance import (
    CREATED_LABEL,
    REVISION_LABEL,
    ProvenanceError,
    build_labels,
    verify_build_pair,
)


def healthy_report() -> PreflightReport:
    return PreflightReport(
        current_head="legacy-head",
        current_state=LEGACY_STATE,
        target_exists=True,
        target_provenance=True,
        target_buildable=True,
        api_healthy=True,
        web_healthy=True,
        database_healthy=True,
        redis_healthy=True,
        ingress={"planam": True, "dengi": True, "avito": True},
        runtime_available=True,
        migration_available=True,
        backfill_available=True,
        reconciliation_available=True,
        shadow_available=True,
        authority_available=True,
        canary_available=True,
        rollback_available=True,
    )


class FakeAdapter:
    def __init__(self, failures: set[str] | None = None):
        self.failures = failures or set()
        self.actions: list[str] = []
        self.rollback_calls = 0

    def preflight(self, target_revision: str) -> PreflightReport:
        self.actions.append("preflight")
        return healthy_report()

    def step(self, action: str, target_revision: str) -> StepResult:
        self.actions.append(action)
        if action in self.failures:
            raise RuntimeError(f"injected {action}")
        return StepResult(True, {"action": action})

    def rollback_before_migration(self, target_revision: str) -> StepResult:
        self.rollback_calls += 1
        self.actions.append("rollback_before_migration")
        return StepResult(True, {"legacy_restored": True})


def test_status_is_non_mutating(capsys):
    assert main(["status"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output == {"default_mutating": False, "mode": "status", "target": TARGET_REVISION}


def test_live_requires_independent_guards(monkeypatch):
    with pytest.raises(LiveArmingError, match="explicit"):
        ProductionCutoverOrchestrator.arm_live(
            environment="PRODUCTION", live=False, confirmation=None,
            expected_head="1348799afc3d1d76dd7a72a13efc2a49a03c5210",
            current_state=LEGACY_STATE,
        )
    monkeypatch.setenv("PLANAM_CUTOVER_LIVE_CONFIRMATION", "operator-confirmation")
    with pytest.raises(LiveArmingError, match="confirmation"):
        ProductionCutoverOrchestrator.arm_live(
            environment="PRODUCTION", live=True, confirmation="wrong",
            expected_head="1348799afc3d1d76dd7a72a13efc2a49a03c5210",
            current_state=LEGACY_STATE,
        )


def test_full_disposable_flow_persists_every_phase(tmp_path):
    adapter = DisposableCutoverAdapter()
    store = JsonCheckpointStore(tmp_path / "checkpoint.json")
    result = ProductionCutoverOrchestrator(adapter, store).run(environment="DISPOSABLE")
    assert [row["phase"] for row in result["phases"]] == [phase.value for phase in PHASE_ORDER]
    assert store.load()["phase"] == "STABILIZING"
    assert adapter.actions[0] == "preflight"
    assert "canary_verified" in adapter.actions
    assert adapter.state == "V2_TARGET"
    assert adapter.write_paused is False
    assert adapter.async_frozen is False


def test_failure_before_migration_rolls_back_and_never_calls_migration(tmp_path):
    adapter = FakeAdapter({"target_deployed"})
    with pytest.raises(RuntimeError, match="injected"):
        ProductionCutoverOrchestrator(adapter, JsonCheckpointStore(tmp_path / "checkpoint.json")).run()
    assert adapter.rollback_calls == 1
    assert "migrated" not in adapter.actions


def test_failure_after_migration_does_not_blindly_restore_database(tmp_path):
    adapter = FakeAdapter({"backfilled"})
    with pytest.raises(RuntimeError, match="injected"):
        ProductionCutoverOrchestrator(adapter, JsonCheckpointStore(tmp_path / "checkpoint.json")).run()
    assert adapter.rollback_calls == 0
    assert "backfilled" in adapter.actions


def test_disposable_adapter_failure_recovery_restores_legacy_state(tmp_path):
    adapter = DisposableCutoverAdapter(failures={"target_deployed"})
    with pytest.raises(CutoverError, match="injected disposable failure"):
        ProductionCutoverOrchestrator(adapter, JsonCheckpointStore(tmp_path / "checkpoint.json")).run()
    assert adapter.state == LEGACY_STATE
    assert adapter.write_paused is False
    assert adapter.async_frozen is False
    assert adapter.actions[-1] == "rollback_before_migration"


def test_resume_starts_after_durable_checkpoint(tmp_path):
    adapter = FakeAdapter()
    store = JsonCheckpointStore(tmp_path / "checkpoint.json")
    store.save({"target_revision": TARGET_REVISION, "phase": "WRITE_PAUSED", "phase_index": 3})
    result = ProductionCutoverOrchestrator(adapter, store).run(resume=True)
    assert result["phases"][3]["resumed"] is True
    assert adapter.actions[0] == "preflight"
    assert "preflight" in adapter.actions
    assert "async_frozen" in adapter.actions


def test_checkpoint_store_is_atomic_and_json(tmp_path):
    path = tmp_path / "nested" / "run.json"
    store = JsonCheckpointStore(path)
    store.save({"phase": "LOCKED", "phase_index": 2})
    assert json.loads(path.read_text())["phase"] == "LOCKED"
    assert not list(path.parent.glob(".*.run.json.*"))


def test_provenance_labels_and_pair_match():
    labels = build_labels(TARGET_REVISION, built_at="2026-09-25T00:00:00Z")
    assert labels[REVISION_LABEL] == TARGET_REVISION
    assert labels[CREATED_LABEL]
    verify_build_pair(labels, labels, TARGET_REVISION)


def test_provenance_rejects_wrong_revision():
    labels = build_labels(TARGET_REVISION)
    with pytest.raises(ProvenanceError, match="mismatch"):
        verify_build_pair(labels, build_labels("0" * 40), TARGET_REVISION)


def test_delivery_rejects_wrong_and_unreachable_targets():
    contract = ArtifactDeliveryContract(TARGET_REVISION, "git@github-planam:wanadd/ai-food-family.git")
    labels = build_labels(TARGET_REVISION, built_at="2026-09-25T00:00:00Z")
    with pytest.raises(ArtifactDeliveryError, match="authoritative ref"):
        contract.verify_target(advertised_refs={"refs/heads/main": "0" * 40}, reachable_revisions=[TARGET_REVISION], api_labels=labels, web_labels=labels)
    with pytest.raises(ArtifactDeliveryError, match="not reachable"):
        contract.verify_target(advertised_refs={"refs/heads/main": TARGET_REVISION}, reachable_revisions=[], api_labels=labels, web_labels=labels)


def test_delivery_accepts_exact_target_and_both_provenances():
    contract = ArtifactDeliveryContract(TARGET_REVISION, "git@github-planam:wanadd/ai-food-family.git")
    labels = build_labels(TARGET_REVISION, built_at="2026-09-25T00:00:00Z")
    contract.verify_target(
        advertised_refs={"refs/heads/main": TARGET_REVISION},
        reachable_revisions=[TARGET_REVISION],
        api_labels=labels,
        web_labels=labels,
    )


def test_default_live_cli_is_fail_closed():
    with pytest.raises(SystemExit, match="fail-closed"):
        main(["live", "--environment", "PRODUCTION", "--confirmation", "x"])


def test_plan_preserves_shared_services(tmp_path):
    adapter = FakeAdapter()
    orchestrator = ProductionCutoverOrchestrator(adapter, JsonCheckpointStore(tmp_path / "checkpoint.json"))
    plan = orchestrator.plan(healthy_report())
    assert "planam_money" in plan.untouched_containers
    assert "avito" in plan.untouched_containers
    assert plan.expected_workers == 2
