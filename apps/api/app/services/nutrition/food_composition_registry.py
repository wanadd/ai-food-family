"""Food-composition source registry for recipe nutrition provenance."""

from __future__ import annotations

FOOD_COMPOSITION_SOURCE_REGISTRY: dict[str, dict[str, object]] = {
    "SRC-RU-FIC-FOODCOMP": {
        "domain": "recipe_nutrition",
        "authority": "FIC nutrition and biotechnology food-composition database",
        "role": "PRIMARY_RU",
        "jurisdiction": "RU",
        "reference_edition": "2024",
        "status": "preferred_when_reliable_match_exists",
        "record_locator_policy": "Use source_record_locator when no stable machine ID is exposed.",
    },
    "SRC-USDA-FDC": {
        "domain": "recipe_nutrition",
        "authority": "USDA FoodData Central",
        "role": "INTERNATIONAL_FALLBACK_REFERENCE",
        "jurisdiction": "US",
        "verified_releases": {
            "Foundation": "04/2026",
            "FNDDS": "10/2024 (2021-2023)",
            "Branded_download": "04/2026",
            "SR Legacy": "04/2018 final",
        },
        "status": "fallback_reference_preserve_fdc_id_and_data_type",
    },
    "SRC-USDA-SR-LEGACY": {
        "domain": "recipe_nutrition",
        "authority": "USDA",
        "role": "OBSOLETE_FOR_PRIMARY",
        "final_release": "04/2018",
        "status": "legacy_historical_only",
    },
    "SRC-PLANAM-V1-NUTRITION-FACTS": {
        "domain": "recipe_nutrition",
        "authority": "PLANAM internal",
        "role": "INTERNAL_LEGACY_UNSOURCED",
        "runtime_label": "planam_v1_nutrition_facts",
        "status": "compatibility_only_unsourced",
    },
}

FOOD_COMPOSITION_SOURCE_PRECEDENCE: tuple[str, ...] = (
    "SRC-RU-FIC-FOODCOMP",
    "SRC-USDA-FDC",
    "manual_reviewed_external",
    "SRC-PLANAM-V1-NUTRITION-FACTS",
    "unavailable",
)

OBSOLETE_FOR_PRIMARY_SOURCE_IDS = frozenset({"SRC-USDA-SR-LEGACY"})
