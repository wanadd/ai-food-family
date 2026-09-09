from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.nutrition.restriction_safety import (  # noqa: E402
    explain_recipe_restriction_conflicts,
    recipe_is_allowed_for_profile,
)
from app.nutrition.restrictions_catalog import get_restriction_definition  # noqa: E402
from app.schemas.nutrition_profile import NutritionProfileData  # noqa: E402
from app.services.member_age import (  # noqa: E402
    nutrition_target_age_band,
    resolve_age,
    resolve_age_for_profile,
)
from app.services.nutrition import target_resolver  # noqa: E402
from app.services.nutrition_profile import profile_to_nutrition_schema  # noqa: E402


@dataclass
class FakeRecipe:
    suitable_for_children: bool = False
    restrictions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    ingredients: list[dict] = field(default_factory=list)
    title: str = ""
    description: str = ""


@dataclass
class FakeProfile:
    age_months: int | None = None
    age: int | None = None
    restrictions: list[str] = field(default_factory=list)
    diets: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    banned_foods: str = ""
    medical_restrictions: str = ""


def test_exact_month_boundaries():
    expected = {
        0: ("infant_0_11_months", True, False, False),
        11: ("infant_0_11_months", True, False, False),
        12: ("child_1_2", False, True, False),
        35: ("child_1_2", False, True, False),
        36: ("child_3_6", False, True, False),
        83: ("child_3_6", False, True, False),
        84: ("child_7_10", False, True, False),
        131: ("child_7_10", False, True, False),
        132: ("child_11_14", False, True, False),
        179: ("child_11_14", False, True, False),
        180: ("child_15_17", False, True, False),
        215: ("child_15_17", False, True, False),
        216: ("adult_18_plus", False, False, True),
    }

    for months, (scope, infant, child, adult) in expected.items():
        resolution = resolve_age(age_months=months)
        assert resolution.population_scope == scope
        assert resolution.age_band == scope
        assert resolution.is_infant is infant
        assert resolution.is_child is child
        assert resolution.is_adult is adult
        assert resolution.resolution_status == "resolved"


def test_account_and_virtual_member_same_exact_age_resolve_identically():
    for months in (0, 11, 12, 35, 36, 83, 84, 131, 132, 179, 180, 215, 216):
        account = resolve_age_for_profile(SimpleNamespace(age_months=months, age=None))
        virtual = resolve_age(age_months=months)

        assert account.population_scope == virtual.population_scope
        assert account.age_band == virtual.age_band
        assert account.resolution_status == virtual.resolution_status


def test_legacy_years_keep_reduced_precision_without_fake_months():
    adult = resolve_age(age=18)
    child = resolve_age(age=10)

    assert adult.population_scope == "adult_18_plus"
    assert adult.resolution_status == "resolved_legacy_precision"
    assert adult.age_months is None
    assert child.population_scope == "child_7_10"
    assert child.resolution_status == "resolved_legacy_precision"
    assert child.age_months is None


def test_exact_age_months_wins_and_conflict_is_surfaced():
    compatible = resolve_age(age_months=35, age=2)
    conflict = resolve_age(age_months=35, age=3)

    assert compatible.resolution_status == "resolved"
    assert compatible.age_years_floor == 2
    assert compatible.population_scope == "child_1_2"
    assert conflict.resolution_status == "ambiguous_input"
    assert conflict.has_conflict is True
    assert conflict.age_months == 35
    assert conflict.population_scope == "child_1_2"


def test_profile_api_keeps_age_and_adds_age_months():
    payload = NutritionProfileData(age=2)
    exact_payload = NutritionProfileData(age=2, age_months=35)

    assert payload.age == 2
    assert payload.age_months is None
    assert exact_payload.age == 2
    assert exact_payload.age_months == 35


def test_profile_response_includes_age_months_without_fabricating_from_age():
    profile = SimpleNamespace(
        age=2,
        age_months=None,
        gender=None,
        height_cm=None,
        weight_kg=None,
        nutrition_goal="child",
        activity_level=None,
        physical_activity_group=None,
        life_stage=None,
        allergies=[],
        restrictions=[],
        medical_restrictions="",
        banned_foods="",
        diets=[],
        favorite_foods="",
        disliked_foods="",
        budget=None,
        cooking_time=None,
        dish_complexity=None,
        pro_data={},
        goal_details={},
    )

    response = profile_to_nutrition_schema(profile)

    assert response.age == 2
    assert response.age_months is None


def test_infant_generic_child_safe_is_not_verified_or_allowed():
    profile = FakeProfile(age_months=11, restrictions=["child_safe"])
    recipe = FakeRecipe(suitable_for_children=True)

    conflicts = explain_recipe_restriction_conflicts(recipe, profile)

    assert not recipe_is_allowed_for_profile(recipe, profile)
    assert any(c.restriction_key == "infant_unsupported_scope" for c in conflicts)
    assert any(c.evidence_status == "generic_unverified_for_age" for c in conflicts)


def test_child_safe_catalog_semantics_are_generic_unverified_for_age():
    definition = get_restriction_definition("child_safe")

    assert definition is not None
    assert definition.severity == "soft"
    assert "not verified age-specific pediatric safety" in definition.description_ru


def test_non_infant_child_safe_remains_soft_generic_signal():
    profile = FakeProfile(age_months=12, restrictions=["child_safe"])
    recipe = FakeRecipe(suitable_for_children=True)

    conflicts = explain_recipe_restriction_conflicts(recipe, profile)

    assert recipe_is_allowed_for_profile(recipe, profile)
    assert not any(c.restriction_key == "infant_unsupported_scope" for c in conflicts)


def test_p0_a2_target_boundaries_use_same_age_contract():
    expected = {
        12: "1-2",
        36: "3-6",
        84: "7-10",
        132: "11-14",
        180: "15-17",
        216: "18-29",
    }

    for months, target_band in expected.items():
        age = resolve_age(age_months=months)
        if months < 216:
            assert nutrition_target_age_band(age) == target_band
        result = target_resolver.resolve_evidence_targets(
            target_resolver.TargetResolverFacts(
                age_months=months,
                sex="male",
                physical_activity_group="kfa_1_4",
            )
        )
        if months == 216:
            assert result.resolution is not None
            assert result.resolution.calculation_inputs["selected_age_band"] == "18-29"
        else:
            assert result.resolution is not None
            assert result.resolution.calculation_inputs["selected_age_band"] == target_band


def test_infant_target_resolver_remains_unsupported_scope():
    result = target_resolver.resolve_evidence_targets(
        target_resolver.TargetResolverFacts(
            age_months=11,
            sex="male",
            physical_activity_group="kfa_1_4",
        )
    )

    assert result.status == "unsupported_scope"
    assert result.reason == "infant_scope"
