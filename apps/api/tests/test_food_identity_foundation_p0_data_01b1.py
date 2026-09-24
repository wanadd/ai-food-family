from __future__ import annotations

import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.services.nutrition.food_identity_foundation import (
    authoritative_match_readiness,
    classify_normalized_ingredient,
    classify_quantity,
    dry_run_food_match,
    match_plan_record,
    normalize_ingredient_name,
    normalize_unit_for_nutrition,
    safety_sensitive_flags,
)


def test_exact_canonical_match_retains_provenance():
    match = dry_run_food_match("рис")
    assert match.status == "matched"
    assert match.canonical_food_key == "rice"
    assert match.match_method == "EXACT_CANONICAL"
    assert match.match_confidence == "EXACT"
    assert match.source_id == "SRC-PLANAM-FOOD-IDENTITY-CURATED"
    assert match.source_record_locator


def test_exact_alias_match_is_deterministic():
    match = dry_run_food_match("курица")
    assert match.status == "matched"
    assert match.canonical_food_key == "chicken_fillet"
    assert match.match_method == "EXACT_ALIAS"
    assert match.match_confidence == "HIGH"


def test_generic_ingredient_remains_ambiguous():
    match = dry_run_food_match("сыр")
    assert match.status == "ambiguous"
    assert match.canonical_food_key is None
    assert match.review_reason == "generic_ingredient_requires_disambiguation"
    assert authoritative_match_readiness("сыр", match) == "NEEDS_DISAMBIGUATION"


def test_ambiguous_ingredient_is_not_auto_matched():
    assert dry_run_food_match("перец").status == "ambiguous"
    assert dry_run_food_match("рыба").status == "ambiguous"


def test_fuzzy_candidate_cannot_become_verified_automatically():
    match = dry_run_food_match("рисс", fuzzy_candidate="rice")
    assert match.status == "manual_review_required"
    assert match.canonical_food_key is None
    assert match.match_method == "REVIEW_CANDIDATE"
    assert match.match_confidence == "REVIEW_REQUIRED"


def test_gram_aliases_normalize_deterministically():
    for unit in ("г", "гр", "гр.", "грамм", "грамма", "граммов"):
        plan = normalize_unit_for_nutrition(unit)
        assert plan.canonical_unit == "г"
        assert plan.unit_class == "MASS_CONVERTIBLE"
        assert plan.multiplier_to_canonical == 1.0


def test_kilogram_conversion():
    quantity = classify_quantity("1.5", "кг")
    assert quantity.computability == "EXACT_MASS_COMPUTABLE"
    assert quantity.canonical_amount == 1500.0
    assert quantity.canonical_unit == "г"


def test_ml_and_liter_normalization():
    ml = classify_quantity("250", "мл")
    liter = classify_quantity("1.2", "л")
    assert ml.computability == "EXACT_VOLUME_COMPUTABLE"
    assert ml.canonical_amount == 250.0
    assert liter.computability == "EXACT_VOLUME_COMPUTABLE"
    assert liter.canonical_amount == 1200.0
    assert liter.canonical_unit == "мл"


def test_count_units_do_not_become_grams():
    quantity = classify_quantity("2", "шт")
    assert quantity.computability == "COUNT_WITHOUT_MASS"
    assert quantity.canonical_amount is None
    assert quantity.canonical_unit is None


def test_household_measures_do_not_become_grams_without_evidence():
    for unit in ("ст. л.", "ч.л.", "стак.", "пуч."):
        quantity = classify_quantity("1", unit)
        assert quantity.computability == "HOUSEHOLD_MEASURE_WITHOUT_CONVERSION"
        assert quantity.canonical_amount is None


def test_qualitative_amounts_remain_non_computable():
    assert classify_quantity("по вкусу", "шт").computability == "QUALITATIVE_AMOUNT"
    assert normalize_unit_for_nutrition("щепот.").unit_class == "QUALITATIVE"


def test_missing_quantity_remains_missing():
    assert classify_quantity("", "г").computability == "MISSING_QUANTITY"
    assert classify_quantity(None, "г").computability == "MISSING_QUANTITY"


def test_safety_sensitive_ambiguous_foods_require_review():
    record = match_plan_record("мука")
    assert record["match_status"] == "ambiguous"
    assert record["manual_review_required"] is True
    assert "gluten_grain" in record["safety_sensitive_flags"]


def test_no_allergen_gf_or_medical_fact_is_generated_by_stage():
    record = match_plan_record("молоко")
    assert "allergen_fact" not in record
    assert "gluten_free_status" not in record
    assert "medical_safety_fact" not in record
    assert "milk_dairy" in record["safety_sensitive_flags"]


def test_normalization_classification_examples():
    assert normalize_ingredient_name("  Лук репчатый, ") == "лук репчатый"
    assert classify_normalized_ingredient("лук") == "TOO_GENERIC"
    assert classify_normalized_ingredient("перец сладкий") == "VARIANT"
    assert classify_normalized_ingredient("крабовые палочки") == "BRAND_OR_PRODUCT"
    assert classify_normalized_ingredient("овсянка") == "SYNONYM"
