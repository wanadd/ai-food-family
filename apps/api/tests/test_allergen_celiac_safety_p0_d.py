from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.nutrition.allergen_ontology import (  # noqa: E402
    ALLERGEN_CONCEPTS,
    AllergenFact,
    LEGACY_BRIDGES,
    TypedSafetyEntry,
    aggregate_allergen_facts,
    decide_celiac_gluten_free,
    legacy_bridge_entries,
    typed_entries_from_profile,
)
from app.nutrition.restriction_safety import (  # noqa: E402
    explain_recipe_restriction_conflicts,
    recipe_is_allowed_for_profile,
)
from app.schemas.family_member_nutrition import VirtualNutritionProfile  # noqa: E402
from app.schemas.nutrition_profile import NutritionProfileData  # noqa: E402
from app.services.family_member_nutrition import (  # noqa: E402
    apply_virtual_nutrition_to_member,
    virtual_nutrition_from_member,
)
from app.services.nutrition.evidence_registry import (  # noqa: E402
    ALLERGEN_SAFETY_EVIDENCE_REGISTRY,
)
from app.services.normalization.profile import normalize_profile_payload  # noqa: E402


def _profile(*, typed=None, allergies=None, restrictions=None, diets=None, medical=""):
    return SimpleNamespace(
        typed_safety_profile=typed or [],
        allergies=allergies or [],
        restrictions=restrictions or [],
        diets=diets or [],
        medical_restrictions=medical,
        age_months=None,
        age=None,
    )


def _recipe(*, ingredients=None, allergen_facts=None, tags=None, gf_status=None, gf_prov=None):
    return SimpleNamespace(
        ingredients=ingredients or [],
        allergen_facts=allergen_facts or [],
        tags=tags or [],
        diets=[],
        restrictions=[],
        allergens=[],
        suitable_for_children=False,
        gluten_free_status=gf_status,
        gluten_free_provenance_status=gf_prov,
    )


def test_typed_profile_kinds_remain_distinct_through_normalization():
    payload = NutritionProfileData(
        typed_safety_profile=[
            {"kind": "allergy", "concept_id": "milk_protein", "origin": "user_declared"},
            {"kind": "intolerance", "concept_id": "lactose_intolerance", "origin": "user_declared"},
            {"kind": "preference", "concept_id": "no_cilantro", "origin": "user_declared"},
            {"kind": "medical_condition", "concept_id": "celiac_disease", "origin": "user_declared"},
        ],
    )
    normalized = normalize_profile_payload(payload)
    kinds = {(row["kind"], row["concept_id"]) for row in normalized.typed_safety_profile}
    assert ("allergy", "milk_protein") in kinds
    assert ("intolerance", "lactose_intolerance") in kinds
    assert ("preference", "no_cilantro") in kinds
    assert ("medical_condition", "celiac_disease") in kinds


def test_allergy_intolerance_invariants_reject_collapse():
    with pytest.raises(ValueError):
        TypedSafetyEntry(
            kind="allergy",
            concept_id="lactose_intolerance",
            origin="user_declared",
        )
    with pytest.raises(ValueError):
        TypedSafetyEntry(
            kind="intolerance",
            concept_id="milk_protein",
            origin="user_declared",
        )


def test_milk_protein_allergy_differs_from_lactose_intolerance():
    lactose_free_milk = _recipe(ingredients=[{"name": "молоко безлактозное"}])
    milk_allergy = _profile(
        typed=[{"kind": "allergy", "concept_id": "milk_protein", "origin": "user_declared"}]
    )
    lactose_intolerance = _profile(
        typed=[
            {
                "kind": "intolerance",
                "concept_id": "lactose_intolerance",
                "origin": "user_declared",
            }
        ]
    )
    assert recipe_is_allowed_for_profile(lactose_free_milk, lactose_intolerance)
    assert not recipe_is_allowed_for_profile(lactose_free_milk, milk_allergy)


def test_legacy_lactose_free_never_creates_milk_allergy():
    entries = legacy_bridge_entries(["lactose_free"])
    assert [(entry.kind, entry.concept_id) for entry in entries] == [
        ("intolerance_or_diet_legacy", "lactose_intolerance")
    ]


def test_peanut_and_tree_nut_are_distinct_canonical_concepts():
    assert "peanut" in ALLERGEN_CONCEPTS
    assert "tree_nut" in ALLERGEN_CONCEPTS
    peanut_recipe = _recipe(ingredients=[{"name": "арахис"}])
    peanut_profile = _profile(
        typed=[{"kind": "allergy", "concept_id": "peanut", "origin": "user_declared"}]
    )
    tree_profile = _profile(
        typed=[{"kind": "allergy", "concept_id": "tree_nut", "origin": "user_declared"}]
    )
    assert not recipe_is_allowed_for_profile(peanut_recipe, peanut_profile)
    assert recipe_is_allowed_for_profile(peanut_recipe, tree_profile)
    assert [entry.concept_id for entry in legacy_bridge_entries(["no_nuts"])] == [
        "peanut",
        "tree_nut",
    ]


def test_fish_crustacean_mollusc_are_distinct_and_legacy_seafood_expands():
    shrimp_recipe = _recipe(ingredients=[{"name": "креветки"}])
    fish_profile = _profile(
        typed=[{"kind": "allergy", "concept_id": "fish", "origin": "user_declared"}]
    )
    crustacean_profile = _profile(
        typed=[{"kind": "allergy", "concept_id": "crustacean", "origin": "user_declared"}]
    )
    assert recipe_is_allowed_for_profile(shrimp_recipe, fish_profile)
    assert not recipe_is_allowed_for_profile(shrimp_recipe, crustacean_profile)
    assert tuple(concept for _kind, concept in LEGACY_BRIDGES["no_seafood"]) == (
        "fish",
        "crustacean",
        "mollusc",
    )


def test_relation_type_is_preserved_and_not_upgraded():
    facts = [
        AllergenFact("peanut", "may_contain", "product_label"),
        AllergenFact("peanut", "cross_contact", "curated_reviewed"),
    ]
    aggregated = aggregate_allergen_facts(facts)
    assert aggregated["peanut"]["relation_type"] == "may_contain"
    profile = _profile(
        typed=[{"kind": "allergy", "concept_id": "peanut", "origin": "user_declared"}]
    )
    conflicts = explain_recipe_restriction_conflicts(
        _recipe(allergen_facts=[fact.to_dict() for fact in facts]),
        profile,
    )
    assert any("may_contain" in conflict.restriction_key for conflict in conflicts)
    assert not any(":contains" in conflict.restriction_key for conflict in conflicts)


def test_celiac_is_medical_condition_not_allergy_or_diet_alias():
    profile = _profile(medical="целиакия")
    entries = typed_entries_from_profile(profile)
    assert any(
        entry.kind == "medical_condition" and entry.concept_id == "celiac_disease"
        for entry in entries
    )
    assert not any(entry.kind == "allergy" and entry.concept_id == "celiac_disease" for entry in entries)


def test_celiac_wheat_is_not_gluten_free():
    decision = decide_celiac_gluten_free(_recipe(ingredients=[{"name": "мука пшеничная"}]))
    assert decision.status == "not_gluten_free"
    profile = _profile(
        typed=[
            {
                "kind": "medical_condition",
                "concept_id": "celiac_disease",
                "origin": "user_declared",
            }
        ]
    )
    assert not recipe_is_allowed_for_profile(_recipe(ingredients=[{"name": "мука пшеничная"}]), profile)


def test_celiac_no_keyword_or_gluten_free_tag_alone_is_unknown_not_verified():
    assert decide_celiac_gluten_free(_recipe(ingredients=[{"name": "рис"}])).status == "unknown"
    assert decide_celiac_gluten_free(_recipe(tags=["gluten_free"])).status == "unknown"


def test_verified_gluten_free_requires_accepted_provenance():
    verified = decide_celiac_gluten_free(
        _recipe(gf_status="verified_gluten_free", gf_prov="product_label")
    )
    ai_only = decide_celiac_gluten_free(
        _recipe(gf_status="verified_gluten_free", gf_prov="ai_unverified")
    )
    assert verified.status == "verified_gluten_free"
    assert verified.safe_for_celiac is True
    assert ai_only.status == "unknown"


def test_celiac_cross_contact_is_risk():
    decision = decide_celiac_gluten_free(
        _recipe(
            allergen_facts=[
                AllergenFact("wheat", "cross_contact", "product_label").to_dict()
            ]
        )
    )
    assert decision.status == "cross_contact_risk"


def test_virtual_member_typed_fields_survive_compatibility_mirroring():
    member = SimpleNamespace(
        is_virtual=True,
        user_id=None,
        nutrition_profile={},
        goals=[],
        restrictions=[],
    )
    nutrition = VirtualNutritionProfile(
        age_months=84,
        nutrition_goal="healthy",
        allergies=["nuts"],
        restrictions=["gluten_free"],
        typed_safety_profile=[
            {"kind": "allergy", "concept_id": "peanut", "origin": "guardian_declared"},
            {
                "kind": "medical_condition",
                "concept_id": "celiac_disease",
                "origin": "guardian_declared",
            },
        ],
    )
    apply_virtual_nutrition_to_member(member, nutrition)
    restored = virtual_nutrition_from_member(member)
    restored_pairs = {
        (row["kind"], row["concept_id"], row["origin"])
        for row in restored.typed_safety_profile
    }
    assert ("allergy", "peanut", "guardian_declared") in restored_pairs
    assert ("medical_condition", "celiac_disease", "guardian_declared") in restored_pairs
    assert "nuts" in member.restrictions
    assert "gluten_free" in member.restrictions


def test_evidence_registry_tracks_p0_d_foundation():
    assert ALLERGEN_SAFETY_EVIDENCE_REGISTRY["EV-AL-001"]["status"] == "match"
    assert ALLERGEN_SAFETY_EVIDENCE_REGISTRY["EV-AL-006"]["status"] == "match"
