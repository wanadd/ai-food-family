"""Machine-readable evidence registry references for nutrition targets."""

from __future__ import annotations

NUTRITION_TARGET_EVIDENCE_REGISTRY: dict[str, dict[str, str | None]] = {
    "EV-NT-001": {
        "domain": "nutrition_targets",
        "description": "MR 2.3.1.0253-21 table lookup for baseline nutrition targets.",
        "source_id": "SRC-RU-MR-0253-21",
        "source_version": "MR-2.3.1.0253-21@2021-07-22",
        "calculation_method": "mr_2_3_1_0253_21_table_lookup_v1",
        "status": "active",
    }
}

NUTRITION_TARGET_SOURCE_REGISTRY: dict[str, dict[str, str | None]] = {
    "SRC-RU-MR-0253-21": {
        "domain": "nutrition_targets",
        "description": "MR 2.3.1.0253-21 source record for baseline macro targets.",
        "version": "MR-2.3.1.0253-21@2021-07-22",
        "dataset_id": "PLANAM-MR-0253-21-MACRO-TARGETS-v1",
        "status": "verified_for_P0_A2",
    }
}

RECIPE_NUTRITION_EVIDENCE_REGISTRY: dict[str, dict[str, str | None]] = {
    "EV-RN-002": {
        "domain": "recipe_nutrition",
        "description": "Canonical nutrient facts require per-fact source provenance.",
        "source_id": None,
        "source_version": None,
        "calculation_method": "food_nutrient_fact_provenance_contract_v1",
        "status": "strong_partial_foundation",
    },
    "EV-RN-003": {
        "domain": "recipe_nutrition",
        "description": "PLANAM v1 hard-coded facts are internal legacy unsourced, not external evidence.",
        "source_id": "SRC-PLANAM-V1-NUTRITION-FACTS",
        "source_version": "planam_v1",
        "calculation_method": "planam_v1_internal_legacy_macro_sum_v1",
        "status": "match",
    },
}
