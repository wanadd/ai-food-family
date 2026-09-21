"""PKU/phenylalanine dry-run foundation for P0-DATA-FOUNDATION-01B5.

The pilot reuses the existing ``FoodNutrientFact`` provenance contract and
does not write recipe, food, nutrient, or medical safety data.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Any, Literal

from app.services.nutrition.authoritative_food_nutrient_pilot import (
    AUTHORITATIVE_FOOD_MATCHES,
    FDC_FOUNDATION_SOURCE,
    facts_by_nutrient,
    resolve_authoritative_food_match,
)
from app.services.nutrition.food_identity_foundation import dry_run_food_match
from app.services.nutrition.recipe_nutrition_provenance import FoodNutrientFact

PHE_NUTRIENT_ID = "1217"
PHE_NUTRIENT_NAME = "Phenylalanine"

PheFoodMatchStatus = Literal[
    "EXACT",
    "HIGH_CONFIDENCE_CURATED",
    "REVIEW_REQUIRED",
    "AMBIGUOUS",
    "UNMATCHED",
]
RecipePheStatus = Literal[
    "FULLY_PHE_COMPUTABLE",
    "PARTIALLY_PHE_COMPUTABLE",
    "NOT_PHE_COMPUTABLE",
]

SOURCE_INVENTORY: dict[str, dict[str, Any]] = {
    "SRC-USDA-FDC-FOUNDATION-2026-04": {
        "source_id": "SRC-USDA-FDC",
        "authority_class": "USDA_PUBLIC_FOOD_COMPOSITION_DATABASE",
        "dataset_name": "FoodData Central Foundation Foods",
        "dataset_version": "04/2026",
        "jurisdiction": "US",
        "license": "CC0 1.0 Universal / public domain",
        "food_identifier_stability": "fdcId",
        "phenylalanine_nutrient_identifier": PHE_NUTRIENT_ID,
        "unit_observed": "g per 100 g in source JSON; normalized to mg per 100 g",
        "basis": "100 g edible portion",
        "food_state_representation": "source food description/data-type state",
        "access_method": "official FDC downloadable JSON",
        "local_availability": "downloaded_to_temp_for_audit_not_committed",
        "provenance_quality": "high for food composition; not clinical guidance",
        "classification": "APPROVED_FOR_PILOT",
    },
    "SRC-USDA-FDC-SR-LEGACY-2018-04": {
        "source_id": "SRC-USDA-FDC",
        "authority_class": "USDA_PUBLIC_FOOD_COMPOSITION_DATABASE",
        "dataset_name": "FoodData Central SR Legacy",
        "dataset_version": "04/2018",
        "jurisdiction": "US",
        "license": "USDA public data / public-domain oriented",
        "food_identifier_stability": "fdcId / NDB-derived identifiers",
        "phenylalanine_nutrient_identifier": PHE_NUTRIENT_ID,
        "unit_observed": "not imported in this pilot",
        "basis": "not imported in this pilot",
        "food_state_representation": "legacy food descriptions",
        "access_method": "official FDC downloadable JSON",
        "local_availability": "download_attempt_incomplete_in_current_run",
        "provenance_quality": "potentially useful but obsolete for primary source precedence",
        "classification": "POTENTIALLY_USABLE_REVIEW_REQUIRED",
    },
    "SRC-RU-CLIN-PKU": {
        "source_id": "SRC-RU-CLIN-PKU",
        "authority_class": "RF_CLINICAL_RECOMMENDATION",
        "dataset_name": "Russian clinical PKU/PAH guidance",
        "dataset_version": None,
        "jurisdiction": "RU",
        "license": None,
        "food_identifier_stability": None,
        "phenylalanine_nutrient_identifier": None,
        "unit_observed": None,
        "basis": None,
        "food_state_representation": None,
        "access_method": "local source registry",
        "local_availability": "registry_only_review_required",
        "provenance_quality": "clinical guidance, not a food composition source",
        "classification": "UNSUITABLE",
    },
}

FOUNDATION_PHE_AUDIT = {
    "foundation_foods_total": 395,
    "foundation_foods_with_phe_nutrient_1217": 53,
    "evaluated_01b2_foods": 15,
    "evaluated_01b2_foods_with_phe": 1,
}

# Source value measured from official FDC Foundation 04/2026 JSON.
PHE_SOURCE_VALUES: dict[str, dict[str, Any]] = {
    "chicken_egg": {
        "source_value": 0.66,
        "source_unit": "g",
        "canonical_value_mg": 660.0,
        "basis_amount": 100.0,
        "basis_unit": "g",
        "source_nutrient_id": PHE_NUTRIENT_ID,
        "source_nutrient_name": PHE_NUTRIENT_NAME,
    }
}


@dataclass(frozen=True)
class PhePilotFact:
    nutrient_fact: FoodNutrientFact
    source_value: float
    source_unit: str
    source_basis_amount: float
    source_basis_unit: str

    def to_record(self) -> dict[str, Any]:
        record = self.nutrient_fact.to_record()
        record.update(
            {
                "source_value": self.source_value,
                "source_unit": self.source_unit,
                "source_basis_amount": self.source_basis_amount,
                "source_basis_unit": self.source_basis_unit,
                "canonical_internal_unit": "mg",
                "canonical_internal_basis": "100 g",
            }
        )
        return record


def normalize_phe_to_mg(value: float, unit: str) -> float:
    normalized = unit.strip().lower()
    if normalized == "mg":
        return float(value)
    if normalized == "g":
        return float(value) * 1000.0
    raise ValueError(f"unsupported phenylalanine unit: {unit}")


def phe_fact_for_food(canonical_food_key: str) -> PhePilotFact | None:
    source = PHE_SOURCE_VALUES.get(canonical_food_key)
    if not source:
        return None
    by_nutrient = facts_by_nutrient(canonical_food_key)
    fact = by_nutrient.get("phenylalanine_mg")
    if fact is None:
        return None
    return PhePilotFact(
        nutrient_fact=fact,
        source_value=source["source_value"],
        source_unit=source["source_unit"],
        source_basis_amount=source["basis_amount"],
        source_basis_unit=source["basis_unit"],
    )


def protein_to_phe_estimate(*_args: Any, **_kwargs: Any) -> None:
    raise RuntimeError("protein_to_phe_estimation_is_forbidden")


def food_phe_match_record(canonical_food_key: str) -> dict[str, Any]:
    external = AUTHORITATIVE_FOOD_MATCHES.get(canonical_food_key)
    fact = phe_fact_for_food(canonical_food_key)
    if external and fact:
        status: PheFoodMatchStatus = (
            "EXACT"
            if external.match_confidence == "HIGH"
            else "HIGH_CONFIDENCE_CURATED"
        )
        reason = "authoritative Foundation food match has nutrient 1217"
    elif external:
        status = "REVIEW_REQUIRED"
        reason = "authoritative food identity exists but no accepted Phe nutrient fact in Foundation pilot"
    else:
        status = "UNMATCHED"
        reason = "no accepted authoritative food identity"
    return {
        "canonical_food_key": canonical_food_key,
        "external_source": FDC_FOUNDATION_SOURCE["source_id"] if external else None,
        "external_food_id": external.external_food_id if external else None,
        "external_food_name": external.external_food_name if external else None,
        "food_state": external.food_state if external else None,
        "match_status": status,
        "phe_available": fact is not None,
        "reason": reason,
        "phe_fact": fact.to_record() if fact else None,
    }


def ingredient_phe_record(row: dict[str, Any]) -> dict[str, Any]:
    name = str(row.get("name") or row.get("ingredient_name") or "")
    match = dry_run_food_match(name)
    external = resolve_authoritative_food_match(match)
    canonical = match.canonical_food_key
    fact = phe_fact_for_food(canonical or "")
    quantity = _quantity_to_grams(row.get("quantity"), row.get("unit"))
    state_status = "MATCHED"
    if external and match.food_state != external.food_state and external.food_state != "unknown":
        state_status = "MISMATCH"
    contribution = None
    contribution_status = "NO_PHE_FACT"
    if fact and state_status == "MISMATCH":
        contribution_status = "FOOD_STATE_MISMATCH"
    elif fact and quantity["grams"] is None:
        contribution_status = "PHE_FACT_AVAILABLE_BUT_QUANTITY_UNRESOLVED"
    elif fact and quantity["grams"] is not None:
        contribution = fact.nutrient_fact.contribution_for_grams(float(quantity["grams"]))
        contribution_status = "PHE_CONTRIBUTION_COMPUTED"
    elif match.status != "matched":
        contribution_status = "FOOD_IDENTITY_GAP"
    return {
        "recipe_id": int(row["recipe_id"]) if row.get("recipe_id") is not None else None,
        "ingredient_row_id": int(row["id"]) if row.get("id") is not None else None,
        "ingredient_name": name,
        "canonical_food_key": canonical,
        "food_match_status": match.status,
        "external_food_id": external.external_food_id if external else None,
        "food_state": external.food_state if external else match.food_state,
        "food_state_validation": state_status,
        "phe_fact_available": fact is not None,
        "phe_fact": fact.to_record() if fact else None,
        "quantity": quantity,
        "phe_mg_contribution": contribution,
        "contribution_status": contribution_status,
        "safety_fact_generated": False,
    }


def _quantity_to_grams(quantity: Any, unit: Any) -> dict[str, Any]:
    from app.services.nutrition.authoritative_food_nutrient_pilot import (
        convert_quantity_to_fact_basis,
    )

    result = convert_quantity_to_fact_basis(quantity, unit)
    return result


def simulate_recipe_phe(
    ingredient_rows: list[dict[str, Any]],
    recipes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    ingredient_records = [ingredient_phe_record(row) for row in ingredient_rows]
    by_recipe: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in ingredient_records:
        if record["recipe_id"] is not None:
            by_recipe[record["recipe_id"]].append(record)
    recipe_meta = {int(row["id"]): row for row in (recipes or [])}
    recipe_records: list[dict[str, Any]] = []
    recipe_ids = set(by_recipe)
    recipe_ids.update(recipe_meta)
    for recipe_id in sorted(recipe_ids):
        rows = by_recipe.get(recipe_id, [])
        computed_rows = [row for row in rows if row["phe_mg_contribution"] is not None]
        unresolved_rows = [row for row in rows if row["phe_mg_contribution"] is None]
        if rows and not unresolved_rows:
            status: RecipePheStatus = "FULLY_PHE_COMPUTABLE"
        elif computed_rows:
            status = "PARTIALLY_PHE_COMPUTABLE"
        else:
            status = "NOT_PHE_COMPUTABLE"
        total = sum(float(row["phe_mg_contribution"]) for row in computed_rows)
        servings = _canonical_servings(recipe_meta.get(recipe_id))
        per_serving = total / servings if status == "FULLY_PHE_COMPUTABLE" and servings else None
        recipe_records.append(
            {
                "recipe_id": recipe_id,
                "status": status,
                "ingredient_rows": len(rows),
                "computed_rows": len(computed_rows),
                "unresolved_rows": len(unresolved_rows),
                "total_phe_mg": total if computed_rows else None,
                "servings": servings,
                "per_serving_phe_mg": per_serving,
                "per_serving_authoritative": per_serving is not None,
                "gap_reasons": sorted({_gap_reason(row) for row in unresolved_rows}),
            }
        )
    metrics = {
        "ingredient_rows_benefiting": sum(1 for row in ingredient_records if row["phe_fact_available"]),
        "rows_with_phe_and_usable_quantity": sum(
            1 for row in ingredient_records if row["contribution_status"] == "PHE_CONTRIBUTION_COMPUTED"
        ),
        "rows_with_phe_and_unresolved_quantity": sum(
            1 for row in ingredient_records if row["contribution_status"] == "PHE_FACT_AVAILABLE_BUT_QUANTITY_UNRESOLVED"
        ),
        "rows_missing_phe_fact": sum(
            1 for row in ingredient_records if row["contribution_status"] == "NO_PHE_FACT"
        ),
        "rows_unmatched_identity": sum(
            1 for row in ingredient_records if row["contribution_status"] == "FOOD_IDENTITY_GAP"
        ),
        "food_state_mismatches": sum(
            1 for row in ingredient_records if row["food_state_validation"] == "MISMATCH"
        ),
        "fully_phe_computable_recipes": sum(
            1 for row in recipe_records if row["status"] == "FULLY_PHE_COMPUTABLE"
        ),
        "partially_phe_computable_recipes": sum(
            1 for row in recipe_records if row["status"] == "PARTIALLY_PHE_COMPUTABLE"
        ),
        "not_phe_computable_recipes": sum(
            1 for row in recipe_records if row["status"] == "NOT_PHE_COMPUTABLE"
        ),
        "per_serving_phe_computable_recipes": sum(
            1 for row in recipe_records if row["per_serving_authoritative"]
        ),
    }
    return {
        "ingredient_records": ingredient_records,
        "recipe_records": recipe_records,
        "metrics": metrics,
        "gap_register": gap_register(ingredient_records, recipe_records),
    }


def _canonical_servings(recipe: dict[str, Any] | None) -> float | None:
    if not recipe:
        return None
    raw = recipe.get("servings")
    try:
        servings = float(raw)
    except (TypeError, ValueError):
        return None
    return servings if servings >= 1 else None


def _gap_reason(row: dict[str, Any]) -> str:
    status = row["contribution_status"]
    if status == "FOOD_IDENTITY_GAP":
        return "FOOD_IDENTITY_GAP"
    if status == "NO_PHE_FACT":
        return "AUTHORITATIVE_PHE_SOURCE_GAP"
    if status == "FOOD_STATE_MISMATCH":
        return "FOOD_STATE_GAP"
    if status == "PHE_FACT_AVAILABLE_BUT_QUANTITY_UNRESOLVED":
        return "QUANTITY_UNIT_GAP"
    return "OTHER"


def gap_register(
    ingredient_records: list[dict[str, Any]],
    recipe_records: list[dict[str, Any]],
) -> dict[str, Any]:
    counter: Counter[str] = Counter()
    for row in ingredient_records:
        if row["phe_mg_contribution"] is None:
            counter[_gap_reason(row)] += 1
    serving_gap = sum(
        1
        for row in recipe_records
        if row["status"] == "FULLY_PHE_COMPUTABLE" and not row["per_serving_authoritative"]
    )
    if serving_gap:
        counter["SERVING_GAP"] += serving_gap
    remediation = {
        "FOOD_IDENTITY_GAP": "extend 01B1 deterministic identity mappings or require manual review",
        "AUTHORITATIVE_PHE_SOURCE_GAP": "extend authoritative amino-acid source coverage; do not use protein proxy",
        "FOOD_STATE_GAP": "add explicit state-specific food mapping or keep review-required",
        "QUANTITY_UNIT_GAP": "add sourced food-specific mass conversions or require authoring cleanup",
        "SERVING_GAP": "require canonical serving count before per-serving claim",
        "PRODUCT_LABEL_GAP": "requires product ingredient/label evidence, especially aspartame",
        "COMPOSITE_RECIPE_GAP": "requires decomposition into component foods",
        "SOURCE_REVIEW_REQUIRED": "close source authority before promotion",
        "OTHER": "manual review",
    }
    return {
        "summary": [
            {"gap": key, "count": count, "next_remediation": remediation.get(key, "manual review")}
            for key, count in sorted(counter.items())
        ]
    }


def protein_phe_ratio_audit(canonical_food_keys: list[str]) -> dict[str, Any]:
    ratios = []
    for key in canonical_food_keys:
        facts = facts_by_nutrient(key)
        phe = facts.get("phenylalanine_mg")
        protein = facts.get("protein_g")
        if phe and phe.value is not None and protein and protein.value:
            ratios.append(
                {
                    "canonical_food_key": key,
                    "phe_mg_per_100g": phe.value,
                    "protein_g_per_100g": protein.value,
                    "phe_mg_per_protein_g": phe.value / protein.value,
                }
            )
    values = [row["phe_mg_per_protein_g"] for row in ratios]
    return {
        "count": len(values),
        "ratios": ratios,
        "range": [min(values), max(values)] if values else None,
        "median": median(values) if values else None,
        "variation": (max(values) - min(values)) if len(values) > 1 else None,
        "interpretation": (
            "insufficient_sample_for_universal_coefficient"
            if len(values) < 3
            else "descriptive_only_not_for_imputation"
        ),
        "used_for_imputation": False,
    }


__all__ = [
    "FOUNDATION_PHE_AUDIT",
    "PHE_NUTRIENT_ID",
    "PHE_SOURCE_VALUES",
    "SOURCE_INVENTORY",
    "food_phe_match_record",
    "ingredient_phe_record",
    "normalize_phe_to_mg",
    "phe_fact_for_food",
    "protein_phe_ratio_audit",
    "protein_to_phe_estimate",
    "simulate_recipe_phe",
]
