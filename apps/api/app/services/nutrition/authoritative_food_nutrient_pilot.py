"""Controlled authoritative nutrient pilot for P0-DATA-FOUNDATION-01B2.

The pilot is intentionally fixture-backed and dry-run only. It does not write
``FoodMatch`` rows, does not persist nutrient facts, and does not generate
allergen, gluten-free, or medical safety facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from app.services.nutrition.food_identity_foundation import (
    classify_quantity,
    dry_run_food_match,
    normalize_ingredient_name,
)
from app.services.nutrition.recipe_nutrition_provenance import (
    FoodMatch,
    FoodNutrientFact,
)

PilotSelectionStatus = Literal[
    "PILOT_ACCEPTED",
    "PILOT_REJECTED_AMBIGUOUS",
    "PILOT_REJECTED_STATE_UNKNOWN",
    "PILOT_REJECTED_COMPOSITE",
    "PILOT_REJECTED_PRODUCT_SPECIFIC",
    "REVIEW_REQUIRED",
]

FDC_FOUNDATION_SOURCE = {
    "source_id": "SRC-USDA-FDC",
    "source_data_type": "Foundation",
    "source_version": "FoodData Central Foundation Foods 04/2026",
    "download_url": "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_json_2026-04-30.zip",
    "download_page": "https://fdc.nal.usda.gov/download-datasets/",
    "license": "CC0 1.0 Universal / public domain",
    "retrieved_or_imported_at": "2026-09-21T00:00:00+03:00",
}

MACRO_NUTRIENTS = ("energy_kcal", "protein_g", "fat_g", "carbohydrate_g")
AUDIT_NUTRIENTS = (
    "energy_kcal",
    "protein_g",
    "fat_g",
    "carbohydrate_g",
    "fiber_g",
    "sodium_mg",
    "phenylalanine_mg",
    "potassium_mg",
    "phosphorus_mg",
)


@dataclass(frozen=True)
class AuthoritativeFoodMatch:
    canonical_food_key: str
    external_food_id: int
    external_food_name: str
    food_state: str
    match_method: str
    match_confidence: str
    review_status: str
    selection_status: PilotSelectionStatus = "PILOT_ACCEPTED"
    review_notes: str | None = None

    def to_food_match(self, normalized_ingredient_name: str) -> FoodMatch:
        return FoodMatch(
            normalized_ingredient_name=normalized_ingredient_name,
            original_ingredient_text=normalized_ingredient_name,
            status="matched",
            canonical_food_key=self.canonical_food_key,
            source_id=FDC_FOUNDATION_SOURCE["source_id"],
            source_record_locator=f"fdc:{self.external_food_id}",
            source_food_name=self.external_food_name,
            food_state=self.food_state,
            match_method=self.match_method,
            match_confidence=self.match_confidence,
            review_reason=self.review_notes,
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "canonical_food_key": self.canonical_food_key,
            "external_source": FDC_FOUNDATION_SOURCE["source_id"],
            "external_food_id": self.external_food_id,
            "external_food_name": self.external_food_name,
            "food_state": self.food_state,
            "match_method": self.match_method,
            "match_confidence": self.match_confidence,
            "source_version": FDC_FOUNDATION_SOURCE["source_version"],
            "source_data_type": FDC_FOUNDATION_SOURCE["source_data_type"],
            "retrieved_or_imported_at": FDC_FOUNDATION_SOURCE["retrieved_or_imported_at"],
            "review_status": self.review_status,
            "selection_status": self.selection_status,
            "review_notes": self.review_notes,
        }


PILOT_SELECTION: dict[str, dict[str, str]] = {
    "banana": {"status": "PILOT_ACCEPTED", "reason": "raw ripe banana has a specific Foundation record"},
    "buckwheat_groats": {"status": "PILOT_ACCEPTED", "reason": "raw whole-grain buckwheat record is compatible with dry buckwheat groats pilot"},
    "potato": {"status": "REVIEW_REQUIRED", "reason": "Foundation record specifies russet without skin while recipe identity does not specify variety or peel state"},
    "shrimp": {"status": "PILOT_ACCEPTED", "reason": "raw shrimp has a specific Foundation record"},
    "chicken_fillet": {"status": "PILOT_ACCEPTED", "reason": "raw boneless skinless chicken breast is compatible with fillet identity"},
    "lemon": {"status": "REVIEW_REQUIRED", "reason": "no reliable Foundation whole lemon match found in pilot source"},
    "onion": {"status": "PILOT_ACCEPTED", "reason": "yellow raw onion selected as reviewed representative for onion bulb"},
    "olive_oil": {"status": "REVIEW_REQUIRED", "reason": "Foundation olive oil record lacks complete macro nutrient facts in the downloaded pilot source"},
    "carrot": {"status": "PILOT_ACCEPTED", "reason": "mature raw carrot has a specific Foundation record"},
    "cucumber": {"status": "PILOT_ACCEPTED", "reason": "raw cucumber with peel has a specific Foundation record"},
    "parsley": {"status": "REVIEW_REQUIRED", "reason": "no reliable Foundation parsley match found in pilot source"},
    "tomato": {"status": "REVIEW_REQUIRED", "reason": "Foundation records are variety-specific and recipe identity does not specify variety"},
    "rice": {"status": "PILOT_ACCEPTED", "reason": "white long-grain raw rice selected as reviewed pilot representative"},
    "sugar": {"status": "PILOT_ACCEPTED", "reason": "granulated sugar has a specific Foundation record"},
    "salt": {"status": "PILOT_ACCEPTED", "reason": "iodized table salt has a specific Foundation record"},
    "cod": {"status": "PILOT_ACCEPTED", "reason": "raw Atlantic cod has a specific Foundation record"},
    "dill": {"status": "REVIEW_REQUIRED", "reason": "only pickle/dill product record found, not dill herb"},
    "oat_flakes": {"status": "PILOT_ACCEPTED", "reason": "old-fashioned rolled oats has a specific Foundation record"},
    "garlic": {"status": "PILOT_ACCEPTED", "reason": "raw garlic has a specific Foundation record"},
    "spinach": {"status": "PILOT_ACCEPTED", "reason": "mature spinach selected as reviewed pilot representative"},
    "apple": {"status": "REVIEW_REQUIRED", "reason": "Foundation records are cultivar-specific and recipe identity does not specify cultivar"},
    "chicken_egg": {"status": "PILOT_ACCEPTED", "reason": "large whole egg has a specific Foundation record"},
}

AUTHORITATIVE_FOOD_MATCHES: dict[str, AuthoritativeFoodMatch] = {
    "banana": AuthoritativeFoodMatch("banana", 1105314, "Bananas, ripe and slightly ripe, raw", "raw", "FDC_EXACT_REVIEWED", "HIGH", "accepted"),
    "buckwheat_groats": AuthoritativeFoodMatch("buckwheat_groats", 2512378, "Buckwheat, whole grain", "raw", "FDC_EXACT_REVIEWED", "HIGH", "accepted"),
    "shrimp": AuthoritativeFoodMatch("shrimp", 2684443, "Crustaceans, shrimp, farm raised, raw", "raw", "FDC_EXACT_REVIEWED", "HIGH", "accepted"),
    "chicken_fillet": AuthoritativeFoodMatch("chicken_fillet", 2646170, "Chicken, breast, boneless, skinless, raw", "raw", "FDC_EXACT_REVIEWED", "HIGH", "accepted"),
    "onion": AuthoritativeFoodMatch("onion", 790646, "Onions, yellow, raw", "raw", "FDC_REVIEWED_REPRESENTATIVE", "REVIEWED", "accepted"),
    "carrot": AuthoritativeFoodMatch("carrot", 2258586, "Carrots, mature, raw", "raw", "FDC_EXACT_REVIEWED", "HIGH", "accepted"),
    "cucumber": AuthoritativeFoodMatch("cucumber", 2346406, "Cucumber, with peel, raw", "raw", "FDC_EXACT_REVIEWED", "HIGH", "accepted"),
    "rice": AuthoritativeFoodMatch("rice", 2512381, "Rice, white, long grain, unenriched, raw", "raw", "FDC_REVIEWED_REPRESENTATIVE", "REVIEWED", "accepted"),
    "sugar": AuthoritativeFoodMatch("sugar", 746784, "Sugars, granulated", "unknown", "FDC_EXACT_REVIEWED", "HIGH", "accepted"),
    "salt": AuthoritativeFoodMatch("salt", 746775, "Salt, table, iodized", "unknown", "FDC_EXACT_REVIEWED", "HIGH", "accepted"),
    "cod": AuthoritativeFoodMatch("cod", 2684444, "Fish, cod, Atlantic, wild caught, raw", "raw", "FDC_EXACT_REVIEWED", "HIGH", "accepted"),
    "oat_flakes": AuthoritativeFoodMatch("oat_flakes", 2346396, "Oats, whole grain, rolled, old fashioned", "raw", "FDC_EXACT_REVIEWED", "HIGH", "accepted"),
    "garlic": AuthoritativeFoodMatch("garlic", 1104647, "Garlic, raw", "raw", "FDC_EXACT_REVIEWED", "HIGH", "accepted"),
    "spinach": AuthoritativeFoodMatch("spinach", 1999633, "Spinach, mature", "raw", "FDC_REVIEWED_REPRESENTATIVE", "REVIEWED", "accepted"),
    "chicken_egg": AuthoritativeFoodMatch("chicken_egg", 748967, "Eggs, Grade A, Large, egg whole", "raw", "FDC_EXACT_REVIEWED", "HIGH", "accepted"),
}

NUTRIENT_FACT_FIXTURE: dict[str, dict[str, dict[str, Any]]] = {
    "banana": {
        "energy_kcal": {"value": 97.0, "unit": "kcal", "source_nutrient_id": "1008", "source_nutrient_name": "Energy"},
        "protein_g": {"value": 0.74, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 0.29, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 23.0, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "fiber_g": {"value": 1.7, "unit": "g", "source_nutrient_id": "1079", "source_nutrient_name": "Fiber, total dietary"},
        "sodium_mg": {"value": 0.0, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 326.0, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 22.0, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
    },
    "buckwheat_groats": {
        "energy_kcal": {"value": 332.0, "unit": "kcal", "source_nutrient_id": "2048", "source_nutrient_name": "Energy (Atwater Specific Factors)"},
        "protein_g": {"value": 11.1, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 3.04, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 71.1, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "fiber_g": {"value": 4.05, "unit": "g", "source_nutrient_id": "1079", "source_nutrient_name": "Fiber, total dietary"},
        "sodium_mg": {"value": 0.0, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 414.0, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 374.0, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
    },
    "shrimp": {
        "energy_kcal": {"value": 72.0, "unit": "kcal", "source_nutrient_id": "2048", "source_nutrient_name": "Energy (Atwater Specific Factors)"},
        "protein_g": {"value": 15.6, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 0.801, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 0.485, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "sodium_mg": {"value": 475.0, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 146.0, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 191.0, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
    },
    "chicken_fillet": {
        "energy_kcal": {"value": 112.0, "unit": "kcal", "source_nutrient_id": "2048", "source_nutrient_name": "Energy (Atwater Specific Factors)"},
        "protein_g": {"value": 22.5, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 1.93, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 0.0, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "sodium_mg": {"value": 65.8, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 330.0, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 215.0, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
    },
    "onion": {
        "energy_kcal": {"value": 38.0, "unit": "kcal", "source_nutrient_id": "1008", "source_nutrient_name": "Energy"},
        "protein_g": {"value": 0.83, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 0.05, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 8.61, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "fiber_g": {"value": 1.9, "unit": "g", "source_nutrient_id": "1079", "source_nutrient_name": "Fiber, total dietary"},
        "sodium_mg": {"value": 1.0, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 182.0, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 34.0, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
    },
    "carrot": {
        "energy_kcal": {"value": 42.0, "unit": "kcal", "source_nutrient_id": "2048", "source_nutrient_name": "Energy (Atwater Specific Factors)"},
        "protein_g": {"value": 0.941, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 0.351, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 10.3, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "fiber_g": {"value": 3.1, "unit": "g", "source_nutrient_id": "1079", "source_nutrient_name": "Fiber, total dietary"},
        "sodium_mg": {"value": 86.6, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 280.0, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 39.8, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
    },
    "cucumber": {
        "energy_kcal": {"value": 17.0, "unit": "kcal", "source_nutrient_id": "2048", "source_nutrient_name": "Energy (Atwater Specific Factors)"},
        "protein_g": {"value": 0.625, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 0.178, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 2.95, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "sodium_mg": {"value": 1.52, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 170.0, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 23.2, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
    },
    "rice": {
        "energy_kcal": {"value": 357.0, "unit": "kcal", "source_nutrient_id": "2048", "source_nutrient_name": "Energy (Atwater Specific Factors)"},
        "protein_g": {"value": 7.04, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 1.03, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 80.3, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "fiber_g": {"value": 0.149, "unit": "g", "source_nutrient_id": "1079", "source_nutrient_name": "Fiber, total dietary"},
        "sodium_mg": {"value": 0.462, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 82.3, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 108.0, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
    },
    "sugar": {
        "energy_kcal": {"value": 385.0, "unit": "kcal", "source_nutrient_id": "1008", "source_nutrient_name": "Energy"},
        "protein_g": {"value": 0.0, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 0.32, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 99.6, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "sodium_mg": {"value": 1.0, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 2.0, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 0.0, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
    },
    "salt": {
        "sodium_mg": {"value": 38700.0, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 2.0, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 0.0, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
    },
    "cod": {
        "energy_kcal": {"value": 74.0, "unit": "kcal", "source_nutrient_id": "2048", "source_nutrient_name": "Energy (Atwater Specific Factors)"},
        "protein_g": {"value": 16.1, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 0.668, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 0.0, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "sodium_mg": {"value": 299.0, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 245.0, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 224.0, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
    },
    "oat_flakes": {
        "energy_kcal": {"value": 379.0, "unit": "kcal", "source_nutrient_id": "2048", "source_nutrient_name": "Energy (Atwater Specific Factors)"},
        "protein_g": {"value": 13.5, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 5.89, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 68.7, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "sodium_mg": {"value": 0.668, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 350.0, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 387.0, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
    },
    "garlic": {
        "energy_kcal": {"value": 143.0, "unit": "kcal", "source_nutrient_id": "1008", "source_nutrient_name": "Energy"},
        "protein_g": {"value": 6.62, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 0.38, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 28.2, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "fiber_g": {"value": 2.7, "unit": "g", "source_nutrient_id": "1079", "source_nutrient_name": "Fiber, total dietary"},
    },
    "spinach": {
        "energy_kcal": {"value": 22.0, "unit": "kcal", "source_nutrient_id": "2048", "source_nutrient_name": "Energy (Atwater Specific Factors)"},
        "protein_g": {"value": 2.91, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 0.604, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 2.64, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "fiber_g": {"value": 1.59, "unit": "g", "source_nutrient_id": "1079", "source_nutrient_name": "Fiber, total dietary"},
        "sodium_mg": {"value": 107.0, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 460.0, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 40.6, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
    },
    "chicken_egg": {
        "energy_kcal": {"value": 148.0, "unit": "kcal", "source_nutrient_id": "1008", "source_nutrient_name": "Energy"},
        "protein_g": {"value": 12.4, "unit": "g", "source_nutrient_id": "1003", "source_nutrient_name": "Protein"},
        "fat_g": {"value": 9.96, "unit": "g", "source_nutrient_id": "1004", "source_nutrient_name": "Total lipid (fat)"},
        "carbohydrate_g": {"value": 0.96, "unit": "g", "source_nutrient_id": "1005", "source_nutrient_name": "Carbohydrate, by difference"},
        "fiber_g": {"value": 0.0, "unit": "g", "source_nutrient_id": "1079", "source_nutrient_name": "Fiber, total dietary"},
        "sodium_mg": {"value": 129.0, "unit": "mg", "source_nutrient_id": "1093", "source_nutrient_name": "Sodium, Na"},
        "potassium_mg": {"value": 132.0, "unit": "mg", "source_nutrient_id": "1092", "source_nutrient_name": "Potassium, K"},
        "phosphorus_mg": {"value": 184.0, "unit": "mg", "source_nutrient_id": "1091", "source_nutrient_name": "Phosphorus, P"},
        "phenylalanine_mg": {"value": 660.0, "unit": "mg", "source_nutrient_id": "1217", "source_nutrient_name": "Phenylalanine"},
    },
}


def resolve_authoritative_food_match(match: FoodMatch) -> AuthoritativeFoodMatch | None:
    if match.status != "matched" or not match.canonical_food_key:
        return None
    external = AUTHORITATIVE_FOOD_MATCHES.get(match.canonical_food_key)
    if external is None:
        return None
    if match.food_state != external.food_state and external.food_state != "unknown":
        return None
    return external


def nutrient_facts_for_food(canonical_food_key: str) -> list[FoodNutrientFact]:
    external = AUTHORITATIVE_FOOD_MATCHES.get(canonical_food_key)
    if external is None:
        return []
    retrieved = datetime.fromisoformat(FDC_FOUNDATION_SOURCE["retrieved_or_imported_at"])
    facts: list[FoodNutrientFact] = []
    for nutrient_key, payload in NUTRIENT_FACT_FIXTURE.get(canonical_food_key, {}).items():
        facts.append(
            FoodNutrientFact(
                canonical_food_key=canonical_food_key,
                nutrient_key=nutrient_key,
                value=payload["value"],
                unit=payload["unit"],
                basis_amount=100.0,
                basis_unit="g",
                source_id=FDC_FOUNDATION_SOURCE["source_id"],
                source_record_locator=f"fdc:{external.external_food_id}",
                source_version=FDC_FOUNDATION_SOURCE["source_version"],
                source_data_type=FDC_FOUNDATION_SOURCE["source_data_type"],
                fdc_id=external.external_food_id,
                food_state=external.food_state,
                provenance_status="external_verified",
                source_food_name=external.external_food_name,
                source_nutrient_id=payload["source_nutrient_id"],
                source_nutrient_name=payload["source_nutrient_name"],
                match_method=external.match_method,
                match_confidence=external.match_confidence,
                review_status=external.review_status,
                review_notes=external.review_notes,
                retrieved_or_imported_at=retrieved.astimezone(timezone.utc),
            )
        )
    return facts


def facts_by_nutrient(canonical_food_key: str) -> dict[str, FoodNutrientFact]:
    return {fact.nutrient_key: fact for fact in nutrient_facts_for_food(canonical_food_key)}


def has_complete_macro_facts(canonical_food_key: str) -> bool:
    by_key = facts_by_nutrient(canonical_food_key)
    return all(by_key.get(key) and by_key[key].value is not None for key in MACRO_NUTRIENTS)


def convert_quantity_to_fact_basis(quantity: str | None, unit: str | None) -> dict[str, Any]:
    plan = classify_quantity(quantity, unit)
    if plan.computability != "EXACT_MASS_COMPUTABLE" or plan.canonical_unit != "г":
        return {
            **plan.to_dict(),
            "basis_conversion_status": "UNRESOLVED_WITHOUT_MASS",
            "grams": None,
        }
    return {
        **plan.to_dict(),
        "basis_conversion_status": "MASS_CONVERTED",
        "grams": plan.canonical_amount,
    }


def ingredient_pilot_record(row: dict[str, Any]) -> dict[str, Any]:
    name = row.get("name") or row.get("ingredient_name") or row.get("normalized_ingredient")
    match = dry_run_food_match(str(name or ""))
    external = resolve_authoritative_food_match(match)
    quantity = convert_quantity_to_fact_basis(row.get("quantity"), row.get("unit"))
    facts = facts_by_nutrient(match.canonical_food_key or "")
    macro_ready = external is not None and all(
        facts.get(key) and facts[key].value is not None for key in MACRO_NUTRIENTS
    )
    amount_ready = quantity["basis_conversion_status"] == "MASS_CONVERTED"
    contributions: dict[str, float | None] = {}
    if macro_ready and amount_ready:
        grams = float(quantity["grams"])
        for key in MACRO_NUTRIENTS:
            contributions[key] = facts[key].contribution_for_grams(grams)
    return {
        "recipe_id": row.get("recipe_id"),
        "ingredient_row_id": row.get("id"),
        "normalized_ingredient": normalize_ingredient_name(str(name or "")),
        "canonical_food_key": match.canonical_food_key,
        "food_match_status": match.status,
        "authoritative_match_status": "MATCHED" if external else "UNMATCHED_AUTHORITATIVE_SOURCE",
        "external_food_id": external.external_food_id if external else None,
        "food_state": external.food_state if external else match.food_state,
        "quantity": quantity,
        "has_authoritative_macro_facts": macro_ready,
        "amount_convertible_to_100g_basis": amount_ready,
        "authoritatively_computable": macro_ready and amount_ready,
        "missing_macro_nutrients": [
            key for key in MACRO_NUTRIENTS if not facts.get(key) or facts[key].value is None
        ],
        "macro_contributions": contributions,
        "safety_facts_generated": False,
    }


def simulate_recipe_computability(ingredient_rows: list[dict[str, Any]]) -> dict[str, Any]:
    ingredient_records = [ingredient_pilot_record(row) for row in ingredient_rows]
    by_recipe: dict[Any, list[dict[str, Any]]] = {}
    for record in ingredient_records:
        by_recipe.setdefault(record["recipe_id"], []).append(record)
    recipe_records: list[dict[str, Any]] = []
    for recipe_id, rows in sorted(by_recipe.items(), key=lambda item: str(item[0])):
        has_any = any(row["authoritatively_computable"] for row in rows)
        full = bool(rows) and all(row["authoritatively_computable"] for row in rows)
        recipe_records.append(
            {
                "recipe_id": recipe_id,
                "ingredient_rows": len(rows),
                "authoritative_contribution_rows": sum(
                    1 for row in rows if row["authoritatively_computable"]
                ),
                "has_authoritative_contribution": has_any,
                "fully_authoritative_macro_computable": full,
                "partially_computable": has_any and not full,
                "incomplete": not full,
            }
        )
    return {
        "ingredient_records": ingredient_records,
        "recipe_records": recipe_records,
        "metrics": {
            "ingredient_rows_with_authoritative_food_match": sum(
                1 for row in ingredient_records if row["authoritative_match_status"] == "MATCHED"
            ),
            "ingredient_rows_with_authoritative_macro_facts": sum(
                1 for row in ingredient_records if row["has_authoritative_macro_facts"]
            ),
            "ingredient_rows_convertible_to_fact_basis": sum(
                1 for row in ingredient_records if row["amount_convertible_to_100g_basis"]
            ),
            "ingredient_rows_usable_authoritative_macros": sum(
                1 for row in ingredient_records if row["authoritatively_computable"]
            ),
            "recipes_with_authoritative_contribution": sum(
                1 for row in recipe_records if row["has_authoritative_contribution"]
            ),
            "recipes_fully_authoritative_macro_computable": sum(
                1 for row in recipe_records if row["fully_authoritative_macro_computable"]
            ),
            "recipes_partially_computable": sum(1 for row in recipe_records if row["partially_computable"]),
            "recipes_not_computable": sum(1 for row in recipe_records if not row["has_authoritative_contribution"]),
        },
    }


def validate_no_safety_fact_generation(records: list[dict[str, Any]]) -> bool:
    return all(record.get("safety_facts_generated") is False for record in records)
