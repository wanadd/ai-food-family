from __future__ import annotations

import json

import pytest
from sqlalchemy import Column, MetaData, String, Table, create_engine, insert

from app.cutover.canary import OperationalCanaryOwner
from app.cutover.deployment_owner import DeploymentConfig, DockerDeploymentOwner
from app.cutover.jobs_outbox import JobsOutboxOwner
from app.cutover.provenance import CutoverTarget, REVISION_LABEL, build_labels
from app.cutover.ri_checks import check_ri2, check_ri3
from app.cutover.runtime_store import RuntimeStore


TARGET = "1" * 40


def test_ri_checks_fail_closed_on_non_postgresql():
    engine = create_engine("sqlite://")
    assert check_ri2(engine).status == "FAIL"
    assert check_ri3(engine).status == "FAIL"


def test_deployment_owner_rejects_mixed_or_wrong_provenance():
    owner = DockerDeploymentOwner(DeploymentConfig("docker-compose.local-parity.yml"))
    target = CutoverTarget.from_revision(TARGET)
    result = owner.validate_candidate(target, build_labels(TARGET), build_labels("2" * 40))
    assert result.status == "FAIL"
    assert owner.deploy(target).status == "FAIL"
    assert owner.validate_candidate(target, build_labels(TARGET, dirty=True), build_labels(TARGET, dirty=True)).status == "FAIL"


def test_jobs_outbox_owner_reuses_async_frozen_and_reports_quiescence():
    engine = create_engine("sqlite://")
    store = RuntimeStore(engine)
    owner = JobsOutboxOwner(engine, store)
    assert owner.status().quiescent is None
    metadata = MetaData()
    Table("durable_jobs_v2", metadata, Column("status", String, nullable=False))
    Table("outbox_events_v2", metadata, Column("status", String, nullable=False))
    metadata.create_all(engine)
    owner.freeze("test")
    result = owner.status()
    assert result.frozen is True
    assert result.quiescent is True
    owner.resume()
    assert owner.status().quiescent is False


def test_operational_canary_is_db_backed_and_idempotent():
    engine = create_engine("sqlite://")
    store = RuntimeStore(engine)
    store.create_run("run", "DISPOSABLE", "legacy", TARGET, dry_run=True)
    store.transition("run", "PREFLIGHT_APPROVED", "test")
    store.transition("run", "WRITE_PAUSED", "test")
    store.transition("run", "ASYNC_DRAINED", "test")
    store.transition("run", "MIGRATED", "test")
    store.transition("run", "BACKFILLING", "test")
    store.transition("run", "BACKFILLED", "test")
    store.transition("run", "RECONCILED", "test")
    store.transition("run", "SHADOW_VALIDATED", "test")
    store.transition("run", "V2_READ", "test")
    store.transition("run", "V2_WRITE", "test")
    store.set_authority("run", "CORE", reader="V2", writer="V2")
    result = OperationalCanaryOwner(store).run(run_id="run", target_revision=TARGET, canary_id="cutover:test")
    again = OperationalCanaryOwner(store).run(run_id="run", target_revision=TARGET, canary_id="cutover:test")
    assert result.status == "PASS" and result.read_after_write
    assert again.duplicate is True
