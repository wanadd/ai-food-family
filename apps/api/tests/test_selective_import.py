from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.core.models import CoreAccount, CoreAuthIdentity, CoreHousehold, CoreMembership, CorePerson, LegacyIdMapping
from app.database import Base
from app.food.profile_models import FoodProfile, FoodProfileFact, FoodProfileReconfirmation
from app.recipes.v2_models import CanonicalArchiveFallback, CanonicalLegacyMapping, CanonicalRecipe, CanonicalRecipeVersion
from app.selective_import.pipeline import ImportConfig, ImportPipelineError, SelectiveImportPipeline


FIXTURE = Path(__file__).parent / "fixtures" / "v2_selective_import_fixture.json"


def _session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'target.sqlite'}")
    tables = [
        CorePerson.__table__, CoreAccount.__table__, CoreAuthIdentity.__table__,
        CoreHousehold.__table__, CoreMembership.__table__, LegacyIdMapping.__table__,
        FoodProfile.__table__, FoodProfileFact.__table__, FoodProfileReconfirmation.__table__,
        CanonicalRecipe.__table__, CanonicalRecipeVersion.__table__,
        CanonicalLegacyMapping.__table__, CanonicalArchiveFallback.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)
    return engine, sessionmaker(bind=engine)()


def _source() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_dry_run_does_not_mutate_and_keeps_ambiguous_data_pending(tmp_path):
    engine, db = _session(tmp_path)
    try:
        source = _source()
        report = SelectiveImportPipeline(db, target_url="sqlite:///disposable", config=ImportConfig()).run(
            source, source_hash="fixture", dry_run=True
        )
        assert report.target_records_created == 0
        assert report.reconfirmation_count == 4
        assert report.classifications["notifications"]["DROP"] == 1
        assert report.classifications["admin_sessions"]["DROP"] == 1
        assert db.scalar(select(func.count()).select_from(CoreAccount)) == 0
    finally:
        db.close()
        engine.dispose()


def test_apply_is_idempotent_and_does_not_import_admin_or_pending_delivery(tmp_path):
    engine, db = _session(tmp_path)
    try:
        source = _source()
        pipeline = SelectiveImportPipeline(db, target_url="sqlite:///disposable", config=ImportConfig())
        first = pipeline.run(source, source_hash="fixture", dry_run=False)
        second = pipeline.run(source, source_hash="fixture", dry_run=False)
        assert first.target_records_created == 11
        assert second.target_records_created == 0
        assert first.target_counts == second.target_counts
        assert second.collisions == []
        assert db.scalar(select(func.count()).select_from(CoreAuthIdentity)) == 1
        assert db.scalar(select(func.count()).select_from(FoodProfileFact)) == 1
        assert db.scalar(select(func.count()).select_from(FoodProfileReconfirmation)) == 2
    finally:
        db.close()
        engine.dispose()


def test_production_like_target_is_rejected(tmp_path):
    engine, db = _session(tmp_path)
    try:
        with pytest.raises(ImportPipelineError, match="production-like"):
            SelectiveImportPipeline(db, target_url="postgresql://app@production/planam").run(
                _source(), source_hash="fixture", dry_run=True
            )
    finally:
        db.close()
        engine.dispose()


def test_duplicate_candidate_is_not_auto_merged(tmp_path):
    engine, db = _session(tmp_path)
    try:
        source = copy.deepcopy(_source())
        source["users"][0]["duplicate_candidate"] = True
        report = SelectiveImportPipeline(db, target_url="sqlite:///disposable").run(
            source, source_hash="fixture", dry_run=True
        )
        assert any(item["reason"] == "POSSIBLE_DUPLICATE_ACCOUNT" for item in report.reconfirmations)
        assert report.classifications["external_identities"]["RECONFIRM_REQUIRED"] == 2
    finally:
        db.close()
        engine.dispose()
