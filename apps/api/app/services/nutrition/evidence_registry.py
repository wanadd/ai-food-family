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

ALLERGEN_SAFETY_EVIDENCE_REGISTRY: dict[str, dict[str, str | None]] = {
    "EV-AL-001": {
        "domain": "allergen_safety",
        "description": "Typed profile safety entries enforce allergy/intolerance separation.",
        "source_id": "SRC-NIAID-FOOD-ALLERGY",
        "source_version": "selected_research_2026_09_09",
        "calculation_method": "typed_safety_profile_v1",
        "status": "match",
    },
    "EV-AL-002": {
        "domain": "allergen_safety",
        "description": "Milk-protein allergy and lactose intolerance are separate concepts.",
        "source_id": "SRC-NIAID-FOOD-ALLERGY",
        "source_version": "selected_research_2026_09_09",
        "calculation_method": "typed_safety_profile_v1",
        "status": "match",
    },
    "EV-AL-003": {
        "domain": "allergen_safety",
        "description": "Peanut/tree-nut and fish/crustacean/mollusc remain distinct canonical concepts.",
        "source_id": "SRC-RU-TR-022",
        "source_version": "selected_research_2026_09_09",
        "calculation_method": "allergen_ontology_v1",
        "status": "match",
    },
    "EV-AL-004": {
        "domain": "allergen_safety",
        "description": "Allergen relation types are modeled and consumed by deterministic safety.",
        "source_id": "SRC-CODEX-CXS1",
        "source_version": "selected_research_2026_09_09",
        "calculation_method": "allergen_relation_v1",
        "status": "strong_partial_foundation",
    },
    "EV-AL-006": {
        "domain": "celiac_safety",
        "description": "Keyword and bare gluten_free tags cannot certify celiac safety.",
        "source_id": "SRC-NIDDK-CELIAC",
        "source_version": "selected_research_2026_09_09",
        "calculation_method": "celiac_gf_decision_v1",
        "status": "match",
    },
    "EV-AL-007": {
        "domain": "celiac_safety",
        "description": "Verified gluten-free status requires acceptable structured provenance.",
        "source_id": "SRC-NIDDK-CELIAC",
        "source_version": "selected_research_2026_09_09",
        "calculation_method": "celiac_gf_decision_v1",
        "status": "strong_partial_foundation",
    },
    "EV-AL-008": {
        "domain": "allergen_safety",
        "description": "Typed profile identity survives account and virtual menu context paths.",
        "source_id": None,
        "source_version": None,
        "calculation_method": "typed_profile_context_bridge_v1",
        "status": "strong_partial_foundation",
    },
}

MEDICAL_SAFETY_EVIDENCE_REGISTRY: dict[str, dict[str, str | None]] = {
    "EV-MD-001": {"domain": "medical_safety", "description": "Typed person-scoped medical context and deterministic escalation.", "source_id": "SRC-HANDOFF-RU-FOOD-SAFETY-CORE", "source_version": "selected_research_2026_09_09", "calculation_method": "typed_medical_context_decision_v1", "status": "match"},
    "EV-MD-002": {"domain": "medical_safety", "description": "PAH/PKU requires individualized phenylalanine target and specialist plan.", "source_id": "SRC-NCBI-PAH-2025", "source_version": "selected_research_2026_09_09", "calculation_method": "pku_phe_escalation_v1", "status": "strong_partial_foundation"},
    "EV-MD-003": {"domain": "medical_safety", "description": "Diabetes nutrition context is individualized; general targets are not treatment macros.", "source_id": "SRC-ADA-2026", "source_version": "selected_research_2026_09_09", "calculation_method": "diabetes_mnt_context_v1", "status": "strong_partial_foundation"},
    "EV-MD-004": {"domain": "medical_safety", "description": "CKD stage and clinician targets are required; no inferred stage or generic macros.", "source_id": "SRC-KDIGO-CKD-2024", "source_version": "selected_research_2026_09_09", "calculation_method": "ckd_context_escalation_v1", "status": "strong_partial_foundation"},
    "EV-MD-005": {"domain": "medical_safety", "description": "Adult sodium target preserves sodium and salt units and does not invent child adjustment.", "source_id": "SRC-WHO-SODIUM", "source_version": "selected_research_2026_09_09", "calculation_method": "sodium_target_v1", "status": "strong_partial_foundation"},
    "EV-MD-006": {"domain": "medical_safety", "description": "Pregnancy decisions require structured pasteurization and food-state/process facts.", "source_id": "SRC-CDC-PREGNANCY-FOOD-SAFETY", "source_version": "selected_research_2026_09_09", "calculation_method": "pregnancy_food_state_v1", "status": "strong_partial_foundation"},
}
