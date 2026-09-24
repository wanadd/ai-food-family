from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.database import Base  # noqa: E402
from app.models.progress import NutritionTarget  # noqa: E402
from app.services import progress as progress_service  # noqa: E402
from app.services.app_scope import AppScope  # noqa: E402
from app.services.nutrition import target_resolver as resolver  # noqa: E402


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[NutritionTarget.__table__])
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _resolve(**kwargs):
    return resolver.resolve_evidence_targets(resolver.TargetResolverFacts(**kwargs))


def _targets(result):
    assert result.status == "resolved"
    assert result.resolution is not None
    return result.resolution.targets


def test_dataset_integrity_and_checksum():
    data = resolver.load_dataset()
    checksum = hashlib.sha256(resolver.DATASET_PATH.read_bytes()).hexdigest()

    assert checksum == "895a8a9a0e10136b090b061f2a753082f4d65a9af1b710dbf458e575ae2db27f"
    assert resolver.validate_dataset(data) is None
    assert data["dataset_id"] == resolver.DATASET_ID
    assert data["source_id"] == resolver.SOURCE_ID
    assert data["source_version"] == resolver.SOURCE_VERSION


@pytest.mark.parametrize(
    ("age_years", "expected_band"),
    [
        (18, "18-29"),
        (29, "18-29"),
        (30, "30-44"),
        (44, "30-44"),
        (45, "45-64"),
        (64, "45-64"),
        (65, "65-74"),
        (74, "65-74"),
        (75, "75+"),
    ],
)
def test_adult_boundary_resolution(age_years, expected_band):
    activity = "kfa_1_7_desired" if age_years >= 65 else "kfa_1_4"
    result = _resolve(
        age_years=age_years,
        sex="male",
        physical_activity_group=activity,
    )

    assert result.status == "resolved"
    assert result.resolution is not None
    assert result.resolution.calculation_inputs["population"] == "adult"
    assert result.resolution.calculation_inputs["selected_age_band"] == expected_band


@pytest.mark.parametrize(
    ("age_months", "expected_status", "expected_band"),
    [
        (11, "unsupported_scope", None),
        (12, "resolved", "1-2"),
        (35, "resolved", "1-2"),
        (36, "resolved", "3-6"),
        (83, "resolved", "3-6"),
        (84, "resolved", "7-10"),
        (131, "resolved", "7-10"),
        (132, "resolved", "11-14"),
        (179, "resolved", "11-14"),
        (180, "resolved", "15-17"),
        (215, "resolved", "15-17"),
        (216, "resolved", "18-29"),
    ],
)
def test_child_boundary_resolution(age_months, expected_status, expected_band):
    result = _resolve(
        age_months=age_months,
        sex="male",
        physical_activity_group="kfa_1_4",
    )

    assert result.status == expected_status
    if expected_status == "resolved":
        assert result.resolution is not None
        assert result.resolution.calculation_inputs["selected_age_band"] == expected_band
        if age_months < 216:
            assert result.resolution.calculation_inputs["population"] == "child"
        else:
            assert result.resolution.calculation_inputs["population"] == "adult"


def test_sex_requirements_are_not_guessed():
    assert _resolve(age_years=30, physical_activity_group="kfa_1_4").status == "insufficient_data"
    assert _resolve(age_months=132).status == "insufficient_data"
    assert _resolve(age_months=84).status == "resolved"


def test_activity_requires_canonical_kfa_without_string_guessing():
    assert _resolve(age_years=30, sex="male").status == "insufficient_data"
    assert (
        _resolve(age_years=30, sex="male", physical_activity_group="moderate").status
        == "ambiguous_input"
    )
    assert (
        _resolve(age_years=30, sex="male", physical_activity_group="sport").status
        == "ambiguous_input"
    )


@pytest.mark.parametrize(
    ("facts", "expected"),
    [
        (
            {"age_years": 18, "sex": "male", "physical_activity_group": "kfa_1_4"},
            (2400, 84, 80, 336),
        ),
        (
            {"age_years": 30, "sex": "male", "physical_activity_group": "kfa_1_6"},
            (2650, 86, 88, 378),
        ),
        (
            {"age_years": 18, "sex": "female", "physical_activity_group": "kfa_1_4"},
            (1900, 67, 63, 266),
        ),
        (
            {"age_years": 45, "sex": "female", "physical_activity_group": "kfa_2_2"},
            (2700, 81, 90, 392),
        ),
        ({"age_months": 12}, (1300, 39, 44, 188)),
        ({"age_months": 36}, (1800, 54, 60, 261)),
        ({"age_months": 84}, (2100, 63, 70, 305)),
        ({"age_months": 132, "sex": "male"}, (2500, 75, 83, 365)),
        ({"age_months": 132, "sex": "female"}, (2300, 69, 77, 334)),
        ({"age_months": 180, "sex": "male"}, (2900, 87, 97, 421)),
        ({"age_months": 180, "sex": "female"}, (2500, 75, 83, 363)),
    ],
)
def test_numeric_spot_checks(facts, expected):
    targets = _targets(_resolve(**facts))

    assert (
        targets.calories_target,
        targets.protein_target_g,
        targets.fat_target_g,
        targets.carbs_target_g,
    ) == expected


@pytest.mark.parametrize(
    ("life_stage", "expected_add"),
    [
        ("pregnancy_trimester_1", (0, 0, 0, 0)),
        ("pregnancy_trimester_2", (250, 10, 10, 30)),
        ("pregnancy_trimester_3", (350, 30, 12, 30)),
        ("lactation_months_1_6", (500, 40, 15, 50)),
        ("lactation_months_7_12", (450, 30, 15, 50)),
    ],
)
def test_typed_life_stage_adjustments(life_stage, expected_add):
    base = _targets(
        _resolve(age_years=30, sex="female", physical_activity_group="kfa_1_4")
    )
    adjusted_result = _resolve(
        age_years=30,
        sex="female",
        physical_activity_group="kfa_1_4",
        life_stage=life_stage,
    )
    adjusted = _targets(adjusted_result)

    assert adjusted.calories_target == base.calories_target + expected_add[0]
    assert adjusted.protein_target_g == base.protein_target_g + expected_add[1]
    assert adjusted.fat_target_g == base.fat_target_g + expected_add[2]
    assert adjusted.carbs_target_g == base.carbs_target_g + expected_add[3]
    assert adjusted_result.resolution is not None
    assert adjusted_result.resolution.calculation_inputs["applied_adjustments"]


def test_resolved_provenance_is_complete_and_fiber_range_is_preserved():
    result = _resolve(
        age_years=18,
        sex="male",
        physical_activity_group="kfa_1_4",
        nutrition_goal="lose",
    )

    assert result.resolution is not None
    resolution = result.resolution
    assert resolution.target_origin == "evidence_auto"
    assert resolution.provenance_status == "verified"
    assert resolution.evidence_id == "EV-NT-001"
    assert resolution.source_id == "SRC-RU-MR-0253-21"
    assert resolution.source_version == "MR-2.3.1.0253-21@2021-07-22"
    assert resolution.calculation_method == "mr_2_3_1_0253_21_table_lookup_v1"
    assert resolution.calculation_inputs["selected_dataset_row_key"] == "adult|male|18-29|kfa_1_4"
    assert resolution.targets.fiber_target_g is None
    assert resolution.targets.fiber_target_g_range == (20, 25)
    assert resolution.targets.water_target_ml is None


@pytest.mark.parametrize(
    "facts",
    [
        {},
        {"age_years": 30, "physical_activity_group": "kfa_1_4"},
        {"age_years": 30, "sex": "male"},
        {"age_months": 11, "sex": "male"},
    ],
)
def test_unresolved_cases_do_not_return_numeric_targets(facts):
    result = _resolve(**facts)

    assert result.status != "resolved"
    assert result.resolution is None


def test_get_nutrition_targets_does_not_create_legacy_fallback_for_missing_data(
    db_session, monkeypatch
):
    monkeypatch.setattr(
        progress_service,
        "get_or_create_profile",
        lambda db, user: SimpleNamespace(
            age=30,
            gender="male",
            physical_activity_group=None,
            life_stage=None,
            nutrition_goal=None,
            weight_kg=70,
        ),
    )

    response = progress_service.get_nutrition_targets(
        db_session,
        SimpleNamespace(id=1),
        AppScope(mode="personal", user_id=1),
    )

    assert response.resolution_status == "insufficient_data"
    assert response.calories_target is None
    assert response.water_target_ml is None
    assert db_session.query(NutritionTarget).count() == 0


def test_get_nutrition_targets_persists_evidence_auto_when_resolved(
    db_session, monkeypatch
):
    monkeypatch.setattr(
        progress_service,
        "get_or_create_profile",
        lambda db, user: SimpleNamespace(
            age=18,
            gender="male",
            physical_activity_group="kfa_1_4",
            life_stage=None,
            nutrition_goal="healthy",
        ),
    )

    response = progress_service.get_nutrition_targets(
        db_session,
        SimpleNamespace(id=2),
        AppScope(mode="personal", user_id=2),
    )
    row = db_session.query(NutritionTarget).one()

    assert response.calories_target == 2400
    assert response.target_origin == "evidence_auto"
    assert response.provenance_status == "verified"
    assert response.fiber_target_g is None
    assert response.fiber_target_g_range == (20, 25)
    assert row.source_version == resolver.SOURCE_VERSION
    assert row.calculation_inputs_json["selected_dataset_row_key"] == "adult|male|18-29|kfa_1_4"


@pytest.mark.parametrize("origin", ["manual", "clinician"])
def test_manual_and_clinician_targets_are_not_overwritten(db_session, monkeypatch, origin):
    monkeypatch.setattr(
        progress_service,
        "get_or_create_profile",
        lambda db, user: SimpleNamespace(
            age=18,
            gender="male",
            physical_activity_group="kfa_1_4",
            life_stage=None,
            nutrition_goal=None,
        ),
    )
    db_session.add(
        NutritionTarget(
            user_id=3,
            calories_target=1777,
            protein_target_g=77,
            target_origin=origin,
            provenance_status="needs_review" if origin == "clinician" else "valid",
        )
    )
    db_session.commit()

    response = progress_service.get_nutrition_targets(
        db_session,
        SimpleNamespace(id=3),
        AppScope(mode="personal", user_id=3),
    )

    assert response.calories_target == 1777
    assert response.protein_target_g == 77
    assert response.target_origin == origin


def test_legacy_row_remains_readable_when_reresolution_is_insufficient(
    db_session, monkeypatch
):
    monkeypatch.setattr(
        progress_service,
        "get_or_create_profile",
        lambda db, user: SimpleNamespace(
            age=30,
            gender="male",
            physical_activity_group=None,
            life_stage=None,
            nutrition_goal=None,
        ),
    )
    db_session.add(
        NutritionTarget(
            user_id=4,
            calories_target=1680,
            protein_target_g=84,
            water_target_ml=2310,
            target_origin="legacy",
            provenance_status="unreviewed",
        )
    )
    db_session.commit()

    response = progress_service.get_nutrition_targets(
        db_session,
        SimpleNamespace(id=4),
        AppScope(mode="personal", user_id=4),
    )

    assert response.target_origin == "legacy"
    assert response.resolution_status == "insufficient_data"
    assert response.calories_target == 1680
    assert response.water_target_ml == 2310
