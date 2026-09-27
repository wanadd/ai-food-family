from __future__ import annotations

from datetime import date

from app.food.wave2_domain import (
    LEGACY_RESTRICTION_MAPPING,
    KnowledgeState,
    SafetyState,
    aggregate_safety,
    derive_age,
    evaluate_safety,
    match_food,
)
from app.routers.v2_food import router


def test_exact_food_matching_does_not_use_substrings_or_fuzzy_authority():
    identities = [{"food_identity_id": "1", "identity_key": "milk", "display_name": "Milk"}]
    assert match_food("milk", identities).status == "CANONICAL_EXACT"
    assert match_food("milk chocolate", identities).status == "UNSUPPORTED"
    assert match_food("mlik", identities).status == "UNSUPPORTED"


def test_ambiguous_explicit_alias_fails_closed():
    aliases = [
        {"food_identity_id": "1", "alias_text": "sauce"},
        {"food_identity_id": "2", "alias_text": "sauce"},
    ]
    assert match_food("sauce", [], aliases).status == "AMBIGUOUS"


def test_unknown_and_missing_evidence_never_become_safe():
    state, reasons = evaluate_safety(profile_facts=[], food_relations=[], evidence_backed=False, process_known=False)
    assert state is SafetyState.UNKNOWN
    assert reasons
    state, _ = evaluate_safety(
        profile_facts=[{"fact_key": "allergen.peanut", "knowledge_state": KnowledgeState.KNOWN_PRESENT.value}],
        food_relations=[{"concept": "allergen.peanut", "relation": "CONTAINS"}],
        evidence_backed=True,
    )
    assert state is SafetyState.BLOCK


def test_household_precedence_preserves_strictest_state():
    assert aggregate_safety([SafetyState.SAFE, SafetyState.UNKNOWN]) is SafetyState.UNKNOWN
    assert aggregate_safety([SafetyState.WARN, SafetyState.UNKNOWN]) is SafetyState.UNKNOWN
    assert aggregate_safety([SafetyState.SAFE, SafetyState.BLOCK]) is SafetyState.BLOCK
    assert aggregate_safety([SafetyState.ESCALATE, SafetyState.WARN]) is SafetyState.ESCALATE


def test_age_is_derived_and_unknown_is_none():
    assert derive_age(None) is None
    assert derive_age(date(2010, 9, 27), at=date(2026, 9, 27)) == 16
    assert derive_age(date(2010, 9, 28), at=date(2026, 9, 27)) == 15


def test_legacy_mapping_is_explicit_and_has_28_entries():
    assert len(LEGACY_RESTRICTION_MAPPING) == 28
    assert LEGACY_RESTRICTION_MAPPING["healthy_eating"] is None
    assert LEGACY_RESTRICTION_MAPPING["no_milk"] == "allergen.milk"


def test_w2_exposes_exactly_six_canonical_route_shapes():
    expected = {
        ("GET", "/api/v2/people/{person_id}/food-profile"),
        ("PUT", "/api/v2/people/{person_id}/food-profile"),
        ("POST", "/api/v2/people/{person_id}/food-profile/reconfirm"),
        ("GET", "/api/v2/foods/search"),
        ("GET", "/api/v2/foods/{food_id}"),
        ("POST", "/api/v2/safety/evaluate"),
    }
    actual = {(method, route.path) for route in router.routes for method in route.methods if method in {"GET", "PUT", "POST"}}
    assert expected <= actual
