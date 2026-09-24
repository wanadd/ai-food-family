from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.schemas.menu import MenuDayPlan, MenuIngredient, MenuMeal, MenuVariant  # noqa: E402
from app.services import menu_recipe_plan  # noqa: E402
from app.services.family_food_aggregation import (  # noqa: E402
    FamilyQuantityAggregation,
    PersonParticipation,
    PersonPortion,
    PersonProfileRef,
    PersonSafetyResult,
    aggregate_nutrition,
    aggregate_quantity,
    aggregate_safety,
    evaluate_person_nutrition,
    evaluate_person_safety,
    person_id_for_member,
    portion_for_person,
)
from app.services.shopping_list import build_items_from_ingredients  # noqa: E402


def _member(member_id: int, *, user_id: int | None = None, name: str = "Member"):
    return SimpleNamespace(id=member_id, user_id=user_id, display_name=name)


def _profile_ref(person_id: str, profile, *, member_id: int | None = None):
    return PersonProfileRef(
        person_id=person_id,
        family_member_id=member_id,
        user_id=None,
        display_name=person_id,
        profile_source="test",
        profile=profile,
    )


def _profile(**overrides):
    values = {
        "typed_safety_profile": [],
        "typed_medical_context": [],
        "allergies": [],
        "restrictions": [],
        "diets": [],
        "medical_restrictions": "",
        "banned_foods": "",
        "age_months": 360,
        "age": 30,
        "gender": "male",
        "physical_activity_group": "kfa_1_4",
        "life_stage": None,
        "nutrition_goal": "healthy",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _recipe(**overrides):
    values = {
        "id": 10,
        "ingredients": [],
        "allergen_facts": [],
        "tags": [],
        "diets": [],
        "restrictions": [],
        "allergens": [],
        "suitable_for_children": False,
        "nutrition_kcal_per_serving": 500.0,
        "nutrition_protein_per_serving": 30.0,
        "nutrition_fat_per_serving": 20.0,
        "nutrition_carbs_per_serving": 40.0,
        "nutrition_confidence": "exact",
        "nutrition_provenance_json": {"nutrition_source_kind": "external_verified"},
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_owner_and_virtual_member_ids_remain_distinct():
    owner = _member(1, user_id=100, name="Owner")
    child = _member(2, user_id=None, name="Child")

    assert person_id_for_member(owner) == "family_member:1"
    assert person_id_for_member(child) == "family_member:2"
    assert person_id_for_member(owner) != person_id_for_member(child)


def test_result_preserves_person_id_for_safety_and_nutrition():
    ref = _profile_ref("family_member:7", _profile(), member_id=7)
    safety = evaluate_person_safety(_recipe(), ref)
    portion = PersonPortion(
        person_id=ref.person_id,
        family_member_id=7,
        serving_factor=1.0,
        state="explicit",
        source="test",
        origin="explicit",
    )
    nutrition = evaluate_person_nutrition(_recipe(), ref, portion)

    assert safety.person_id == "family_member:7"
    assert nutrition.person_id == "family_member:7"


def test_non_participant_excluded_and_unknown_participation_not_zero():
    participant = PersonPortion("family_member:1", 1.0, "explicit", "test", "explicit", 1)
    non_participant = PersonPortion(
        "family_member:2",
        None,
        "unknown",
        "not_applicable_until_participation",
        "does_not_participate",
        2,
    )
    quantity = aggregate_quantity([participant])

    assert quantity.total_serving_factor == 1.0
    assert non_participant.serving_factor is None
    assert aggregate_quantity([participant, non_participant]).state == "incomplete"


def test_portion_defaults_are_labeled_and_child_adult_not_silently_equal():
    adult_ref = _profile_ref("family_member:1", _profile(age_months=360), member_id=1)
    child_ref = _profile_ref("family_member:2", _profile(age_months=84, age=7), member_id=2)
    participation = PersonParticipation(
        "family_member:1", "participates", "test", "explicit", 1
    )
    adult = portion_for_person(adult_ref, participation)
    child = portion_for_person(
        child_ref,
        PersonParticipation("family_member:2", "participates", "test", "explicit", 2),
    )

    assert adult.state == "derived_default"
    assert adult.source == "adult_portion_fallback"
    assert child.state == "derived_default"
    assert child.source == "age_based_child_portion_fallback"
    assert child.serving_factor != adult.serving_factor


def test_one_allergy_block_dominates_family_aggregate_and_safe_majority_cannot_cancel():
    safe_a = PersonSafetyResult("family_member:1", 10, "SAFE", [])
    blocked = evaluate_person_safety(
        _recipe(ingredients=[{"name": "арахис"}]),
        _profile_ref(
            "family_member:2",
            _profile(
                typed_safety_profile=[
                    {"kind": "allergy", "concept_id": "peanut", "origin": "user_declared"}
                ]
            ),
        ),
    )
    safe_c = PersonSafetyResult("family_member:3", 10, "SAFE", [])

    aggregate = aggregate_safety([safe_a, blocked, safe_c])

    assert blocked.decision == "BLOCK"
    assert aggregate.aggregate_decision == "BLOCK"
    assert [person.person_id for person in aggregate.blocking_people] == ["family_member:2"]


def test_celiac_unknown_and_medical_escalate_remain_visible():
    celiac = evaluate_person_safety(
        _recipe(ingredients=[{"name": "рис"}]),
        _profile_ref(
            "family_member:1",
            _profile(
                typed_safety_profile=[
                    {
                        "kind": "medical_condition",
                        "concept_id": "celiac_disease",
                        "origin": "user_declared",
                    }
                ]
            ),
        ),
    )
    medical = evaluate_person_safety(
        _recipe(),
        _profile_ref(
            "family_member:2",
            _profile(
                typed_medical_context=[
                    {"condition_id": "diabetes", "origin": "user_declared"}
                ]
            ),
        ),
    )

    aggregate = aggregate_safety([celiac, medical])

    assert celiac.decision == "UNKNOWN"
    assert medical.decision == "ESCALATE"
    assert aggregate.aggregate_decision == "ESCALATE"
    assert [person.person_id for person in aggregate.unknown_people] == ["family_member:1"]
    assert [person.person_id for person in aggregate.escalating_people] == ["family_member:2"]


def test_multiple_unsafe_members_all_remain_represented():
    a = PersonSafetyResult("family_member:1", 10, "BLOCK", ["peanut"])
    b = PersonSafetyResult("family_member:2", 10, "BLOCK", ["gluten"])

    aggregate = aggregate_safety([a, b])

    assert aggregate.aggregate_decision == "BLOCK"
    assert {person.person_id for person in aggregate.blocking_people} == {
        "family_member:1",
        "family_member:2",
    }


def test_ai_post_ai_path_cannot_erase_deterministic_family_block():
    safe = PersonSafetyResult("family_member:1", 10, "SAFE", [])
    deterministic_block = PersonSafetyResult("family_member:2", 10, "BLOCK", ["allergy"])

    aggregate = aggregate_safety([safe, deterministic_block])

    assert aggregate.aggregate_decision == "BLOCK"


def test_nutrition_targets_are_per_person_and_missing_facts_stay_unknown():
    adult = _profile_ref("family_member:1", _profile(age_months=360, age=30))
    child = _profile_ref("family_member:2", _profile(age_months=84, age=7, gender=None))
    portion = PersonPortion("family_member:1", 1.0, "explicit", "test", "explicit")
    adult_result = evaluate_person_nutrition(_recipe(), adult, portion)
    child_result = evaluate_person_nutrition(
        _recipe(nutrition_kcal_per_serving=None),
        child,
        PersonPortion("family_member:2", 0.75, "derived_default", "child", "fallback"),
    )

    assert adult_result.target_result.resolved is True
    assert adult_result.compliance_state == "within_applicable_target"
    assert child_result.compliance_state == "nutrient_facts_unavailable"
    assert child_result.calculated_values["kcal"] is None


def test_missing_target_remains_unknown_and_family_summary_preserves_outcomes():
    resolved = evaluate_person_nutrition(
        _recipe(),
        _profile_ref("family_member:1", _profile()),
        PersonPortion("family_member:1", 1.0, "explicit", "test", "explicit"),
    )
    missing_target = evaluate_person_nutrition(
        _recipe(),
        _profile_ref("family_member:2", _profile(age_months=None, age=None)),
        PersonPortion("family_member:2", 1.0, "explicit", "test", "explicit"),
    )

    family = aggregate_nutrition([resolved, missing_target])

    assert missing_target.compliance_state == "target_unavailable"
    assert family.summary_counts["within"] == 1
    assert family.summary_counts["unknown"] == 1
    assert len(family.participant_results) == 2


def test_two_people_can_have_different_compliance_for_same_recipe_without_family_target():
    inside = evaluate_person_nutrition(
        _recipe(nutrition_kcal_per_serving=500.0),
        _profile_ref("family_member:1", _profile(age_months=360, age=30)),
        PersonPortion("family_member:1", 1.0, "explicit", "test", "explicit"),
    )
    outside = evaluate_person_nutrition(
        _recipe(nutrition_kcal_per_serving=2500.0),
        _profile_ref("family_member:2", _profile(age_months=84, age=7)),
        PersonPortion("family_member:2", 1.0, "explicit", "test", "explicit"),
    )

    family = aggregate_nutrition([inside, outside])

    assert inside.compliance_state == "within_applicable_target"
    assert outside.compliance_state == "outside_applicable_target"
    assert family.summary_counts["within"] == 1
    assert family.summary_counts["outside"] == 1
    assert "family_target" not in family.summary_counts


def test_unknown_required_portion_produces_incomplete_quantity():
    quantity = aggregate_quantity(
        [
            PersonPortion("family_member:1", 1.0, "explicit", "test", "explicit"),
            PersonPortion("family_member:2", None, "unknown", "person_portion", "explicit"),
        ]
    )

    assert quantity.state == "incomplete"
    assert quantity.total_serving_factor is None
    assert quantity.reasons == ["family_member:2:portion_unknown"]


class _Db:
    def __init__(self, recipe):
        self.recipe = recipe

    def get(self, _model, recipe_id):
        return self.recipe if recipe_id == self.recipe.id else None


def test_shopping_quantity_consumes_canonical_aggregation(monkeypatch):
    recipe = SimpleNamespace(
        id=1,
        servings=2,
        ingredient_rows=[],
        ingredients=[{"name": "Carrot", "amount": "1 pc", "category": "other"}],
    )
    menu = MenuVariant(
        variant="balanced",
        title="Plan",
        explanation="",
        total_prep_minutes=20,
        meals=[
            MenuMeal(
                meal_type="dinner",
                name="Dinner",
                description="",
                prep_time_minutes=20,
                recipe_id=1,
                servings=1,
            )
        ],
        ingredients=[MenuIngredient(name="Old", amount="1 pc")],
        days=[
            MenuDayPlan(
                day_index=1,
                label="Day 1",
                date_iso="2026-06-01",
                meals=[
                    MenuMeal(
                        meal_type="dinner",
                        name="Dinner",
                        description="",
                        prep_time_minutes=20,
                        recipe_id=1,
                        servings=1,
                    )
                ],
            )
        ],
    )

    calls = []

    def _quantity(*_args, **kwargs):
        calls.append(kwargs.get("meal_type"))
        return FamilyQuantityAggregation(
            participant_portions=[
                PersonPortion("family_member:1", 1.0, "explicit", "test", "explicit"),
                PersonPortion("family_member:2", 1.0, "explicit", "test", "explicit"),
                PersonPortion("family_member:3", 0.75, "derived_default", "child", "fallback"),
            ],
            total_serving_factor=2.75,
            state="complete",
            reasons=[],
        )

    monkeypatch.setattr(
        menu_recipe_plan,
        "required_servings_for_meal",
        _quantity,
    )
    recomputed = menu_recipe_plan.recompute_menu_ingredients_from_active_meals(
        _Db(recipe),
        menu,
        user=SimpleNamespace(id=1),
        scope=SimpleNamespace(mode="family", is_family=True),
    )
    item = build_items_from_ingredients(recomputed.ingredients)[0]

    assert item.name.lower() == "carrot"
    assert calls == ["dinner"]
    assert item.quantity == "2"
