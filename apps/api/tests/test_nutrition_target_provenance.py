from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.database import Base  # noqa: E402
from app.database_migrations import _schema_statements  # noqa: E402
from app.models.progress import NutritionTarget  # noqa: E402
from app.schemas.progress import NutritionTargetsResponse, NutritionTargetsUpdate  # noqa: E402
from app.services import progress as progress_service  # noqa: E402
from app.services.app_scope import AppScope  # noqa: E402
from app.services.nutrition.evidence_registry import (  # noqa: E402
    NUTRITION_TARGET_EVIDENCE_REGISTRY,
    NUTRITION_TARGET_SOURCE_REGISTRY,
)
from app.services.nutrition.target_provenance import (  # noqa: E402
    NutritionTargetResolution,
    NutritionTargetValues,
    validate_provenance,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[NutritionTarget.__table__])
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_legacy_nutrition_target_defaults_are_legacy(db_session):
    row = NutritionTarget(user_id=1, calories_target=1800)
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)

    assert row.target_origin == "legacy"
    assert row.provenance_status == "unreviewed"
    assert row.evidence_id is None
    assert row.source_id is None
    assert row.source_version is None


def test_migration_adds_legacy_provenance_without_evidence_backfill():
    migration_sql = "\n".join(_schema_statements())

    assert "ALTER TABLE nutrition_targets ADD COLUMN IF NOT EXISTS target_origin" in migration_sql
    assert "DEFAULT 'legacy'" in migration_sql
    assert "ALTER TABLE nutrition_targets ADD COLUMN IF NOT EXISTS evidence_id" in migration_sql
    assert "ck_nutrition_targets_evidence_auto_provenance" in migration_sql
    assert "ck_nutrition_targets_non_evidence_no_provenance" in migration_sql


def test_manual_update_marks_manual_and_clears_evidence(db_session, monkeypatch):
    monkeypatch.setattr(progress_service, "require_pro", lambda db, user: None)
    row = NutritionTarget(
        user_id=1,
        person_id=7,
        family_id=3,
        calories_target=1800,
        protein_target_g=90,
        target_origin="legacy",
    )
    db_session.add(row)
    db_session.commit()

    response = progress_service.update_nutrition_targets(
        db_session,
        SimpleNamespace(id=1),
        AppScope(mode="family", user_id=1, family_id=3),
        NutritionTargetsUpdate(calories_target=1900, protein_target_g=100),
    )
    db_session.refresh(row)

    assert response.target_origin == "manual"
    assert row.target_origin == "manual"
    assert row.provenance_status == "valid"
    assert row.evidence_id is None
    assert row.source_id is None
    assert row.source_version is None
    assert row.person_id == 7
    assert row.family_id == 3
    assert row.user_id == 1


def test_manual_target_has_no_fabricated_evidence_provenance():
    response = NutritionTargetsResponse(
        calories_target=1900,
        protein_target_g=100,
        fat_target_g=None,
        carbs_target_g=None,
        fiber_target_g=None,
        water_target_ml=None,
        goal_type="maintain",
        target_origin="manual",
        provenance_status="valid",
    )

    assert response.evidence_id is None
    assert response.source_id is None
    assert response.source_version is None
    assert response.calculation_method is None
    assert response.calculation_inputs_json is None
    assert response.calculated_at is None


def test_evidence_auto_contract_requires_full_provenance():
    with pytest.raises(ValueError, match="full provenance"):
        NutritionTargetResolution(
            targets=NutritionTargetValues(calories_target=2000),
            target_origin="evidence_auto",
            evidence_id="EV-NT-001",
            source_id="SRC-RU-MR-0253-21",
        )

    calculated_at = datetime.now(timezone.utc)
    resolution = NutritionTargetResolution(
        targets=NutritionTargetValues(calories_target=2000),
        target_origin="evidence_auto",
        evidence_id="EV-NT-001",
        source_id="SRC-RU-MR-0253-21",
        source_version="draft-record-v1",
        calculation_method="future_normative_resolver",
        calculation_inputs={"age": 30, "sex": "female"},
        calculated_at=calculated_at,
        provenance_status="valid",
    )

    assert resolution.evidence_id == "EV-NT-001"
    assert resolution.source_id == "SRC-RU-MR-0253-21"
    assert resolution.calculated_at == calculated_at


def test_clinician_target_is_distinguishable_from_manual_and_evidence_auto(
    db_session, monkeypatch
):
    monkeypatch.setattr(progress_service, "require_pro", lambda db, user: None)
    db_session.add(NutritionTarget(user_id=2, calories_target=2100))
    db_session.commit()

    response = progress_service.update_nutrition_targets(
        db_session,
        SimpleNamespace(id=2),
        AppScope(mode="personal", user_id=2),
        NutritionTargetsUpdate(calories_target=2050, target_origin="clinician"),
    )

    assert response.target_origin == "clinician"
    assert response.provenance_status == "needs_review"
    assert response.evidence_id is None


def test_existing_api_schema_remains_backward_compatible():
    response = NutritionTargetsResponse(
        calories_target=1800,
        protein_target_g=90,
        fat_target_g=56,
        carbs_target_g=210,
        fiber_target_g=25,
        water_target_ml=2310,
        goal_type="lose",
    )

    assert response.target_origin == "legacy"
    assert response.provenance_status == "unreviewed"
    assert response.model_dump()["calories_target"] == 1800


def test_invalid_provenance_combinations_are_rejected():
    with pytest.raises(ValueError, match="cannot include evidence provenance"):
        validate_provenance(
            target_origin="manual",
            evidence_id="EV-NT-001",
            source_id=None,
            source_version=None,
            calculation_method=None,
            calculation_inputs=None,
            calculated_at=None,
        )

    with pytest.raises(ValidationError):
        NutritionTargetsUpdate(target_origin="evidence_auto")


def test_no_new_unsourced_numeric_target_formula_introduced():
    profile = SimpleNamespace(weight_kg=70.0, nutrition_goal="maintain")
    target = progress_service._estimate_targets(profile)

    assert target.calories_target == 1680
    assert target.protein_target_g == 84
    assert target.fat_target_g == 52
    assert target.carbs_target_g == 219
    assert target.fiber_target_g == 25
    assert target.water_target_ml == 2310
    assert target.target_origin == "legacy"
    assert target.evidence_id is None


def test_evidence_registry_keeps_evidence_and_source_ids_separate():
    evidence_record = NUTRITION_TARGET_EVIDENCE_REGISTRY["EV-NT-001"]
    source_record = NUTRITION_TARGET_SOURCE_REGISTRY["SRC-RU-MR-0253-21"]

    assert evidence_record["source_id"] == "SRC-RU-MR-0253-21"
    assert evidence_record["source_id"] != "EV-NT-001"
    assert source_record["version"] == "MR-2.3.1.0253-21@2021-07-22"
