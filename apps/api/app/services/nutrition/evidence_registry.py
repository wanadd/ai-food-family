"""Machine-readable evidence registry references for nutrition and safety.

The source-closure records below are provenance metadata only. They must not
change P0-D/P0-E safety semantics or imply recipe/ingredient data coverage.
"""

from __future__ import annotations

from typing import Any

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

SOURCE_AUTHORITY_CLASSES = frozenset(
    {
        "RF_EAEU_REGULATION",
        "RF_SANITARY_RULE",
        "RF_GUIDANCE",
        "RF_CLINICAL_RECOMMENDATION",
        "INTERNATIONAL_GUIDANCE",
        "INTERNATIONAL_CLINICAL_GUIDANCE",
        "PLANAM_POLICY",
        "INTERNAL_LEGACY",
    }
)

SOURCE_APPLICABILITY = frozenset(
    {
        "LABEL_FACTS",
        "SPECIALIZED_FOOD_LABELING",
        "PUBLIC_CATERING_REFERENCE",
        "INSTITUTIONAL_REFERENCE",
        "HOUSEHOLD_REFERENCE",
        "CLINICAL_CONTEXT",
        "PRODUCT_POLICY",
        "DATA_COVERAGE_REQUIRED",
        "NOT_DIRECT_HOUSEHOLD_LAW",
    }
)

SOURCE_ROLES = frozenset(
    {
        "PRIMARY",
        "SECONDARY",
        "SUPPLEMENTARY",
        "NOT_NEEDED",
        "REVIEW_REQUIRED",
    }
)

SOURCE_RELATIONSHIPS = frozenset(
    {"SAME_SOURCE", "ALIAS", "SUPERSEDED", "DISTINCT_SOURCE", "UNKNOWN"}
)

SOURCE_VERIFICATION_STATUSES = frozenset(
    {"VERIFIED", "REVIEW_REQUIRED", "SUPERSEDED", "LEGACY_UNSOURCED"}
)

CANONICAL_SOURCE_REGISTRY: dict[str, dict[str, Any]] = {
    "SRC-RU-MR-0253-21": {
        "title": "MR 2.3.1.0253-21 physiological requirements",
        "authority": "Rospotrebnadzor",
        "authority_class": "RF_GUIDANCE",
        "jurisdiction": "RU",
        "source_class": "methodological_recommendation",
        "status": "VERIFIED",
        "version": "MR-2.3.1.0253-21@2021-07-22",
        "effective_date": "2021-07-22",
        "accessed_at": None,
        "official_locator": None,
        "scope": "physiological-needs macro and energy targets",
        "consumer_context": "household_reference",
        "applicability": ["HOUSEHOLD_REFERENCE"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "verified_from_committed_dataset",
        "notes": "Official guidance for scoped PLANAM baseline targets; not statutory household intake law.",
    },
    "SRC-RU-TR-022": {
        "title": "TR TS 022/2011 Food products in terms of labeling",
        "authority": "EAEU",
        "authority_class": "RF_EAEU_REGULATION",
        "jurisdiction": "EAEU",
        "source_class": "technical_regulation",
        "status": "VERIFIED",
        "version": "TR-TS-022-2011",
        "effective_date": None,
        "accessed_at": None,
        "official_locator": None,
        "scope": "food label facts and declared ingredients/allergens",
        "consumer_context": "product_label_facts",
        "applicability": ["LABEL_FACTS", "NOT_DIRECT_HOUSEHOLD_LAW"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "verified_from_local_source_pack",
        "notes": "Mandatory labeling layer. It supports structured label-derived facts but is not a complete clinical allergy or celiac decision standard.",
    },
    "SRC-EAEU-TR-027": {
        "title": "TR TS 027/2012 Specialized food products",
        "authority": "EAEU",
        "authority_class": "RF_EAEU_REGULATION",
        "jurisdiction": "EAEU",
        "source_class": "technical_regulation",
        "status": "VERIFIED",
        "version": "TR-TS-027-2012",
        "effective_date": None,
        "accessed_at": None,
        "official_locator": None,
        "scope": "specialized and dietetic food labeling",
        "consumer_context": "specialized_food_label_facts",
        "applicability": ["SPECIALIZED_FOOD_LABELING", "NOT_DIRECT_HOUSEHOLD_LAW"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "verified_from_local_source_pack",
        "notes": "Gluten threshold belongs to specialized-food scope and is not universalized to every home-prepared dish.",
    },
    "SRC-RU-SANPIN-4282-26": {
        "title": "SanPiN 2.3/2.4.4282-26 public catering sanitary requirements",
        "authority": "Rospotrebnadzor",
        "authority_class": "RF_SANITARY_RULE",
        "jurisdiction": "RU",
        "source_class": "sanitary_rule",
        "status": "VERIFIED",
        "version": "SanPiN-2.3/2.4.4282-26",
        "effective_date": "2026-09-01",
        "accessed_at": None,
        "official_locator": None,
        "scope": "public catering service activity",
        "consumer_context": "public_catering_reference",
        "applicability": ["PUBLIC_CATERING_REFERENCE", "NOT_DIRECT_HOUSEHOLD_LAW"],
        "supersedes": ["SRC-RU-SANPIN-3590-20"],
        "superseded_by": [],
        "review_status": "verified_from_local_currentness_pack",
        "notes": "Current from 2026-09-01; not direct household law.",
    },
    "SRC-RU-SANPIN-3590-20": {
        "title": "SanPiN 2.3/2.4.3590-20 public catering sanitary requirements",
        "authority": "Rospotrebnadzor",
        "authority_class": "RF_SANITARY_RULE",
        "jurisdiction": "RU",
        "source_class": "sanitary_rule",
        "status": "SUPERSEDED",
        "version": "SanPiN-2.3/2.4.3590-20",
        "effective_date": None,
        "accessed_at": None,
        "official_locator": None,
        "scope": "public catering service activity",
        "consumer_context": "public_catering_reference",
        "applicability": ["PUBLIC_CATERING_REFERENCE", "NOT_DIRECT_HOUSEHOLD_LAW"],
        "supersedes": [],
        "superseded_by": ["SRC-RU-SANPIN-4282-26"],
        "review_status": "superseded_by_local_currentness_pack",
        "notes": "Superseded effective 2026-08-31.",
    },
    "SRC-RU-CLIN-FOOD-ALLERGY": {
        "title": "Russian Ministry of Health clinical recommendation for food allergy",
        "authority": "Ministry of Health of the Russian Federation",
        "authority_class": "RF_CLINICAL_RECOMMENDATION",
        "jurisdiction": "RU",
        "source_class": "clinical_recommendation",
        "status": "REVIEW_REQUIRED",
        "version": None,
        "effective_date": None,
        "accessed_at": None,
        "official_locator": None,
        "scope": "clinical food allergy concepts and management",
        "consumer_context": "clinical_context",
        "applicability": ["CLINICAL_CONTEXT"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "exact_official_locator_and_version_required",
        "notes": "Preferred Russian-context clinical authority, but exact official record was not verified in local evidence.",
    },
    "SRC-RU-CLIN-CELIAC": {
        "title": "Russian Ministry of Health clinical recommendation for celiac disease",
        "authority": "Ministry of Health of the Russian Federation",
        "authority_class": "RF_CLINICAL_RECOMMENDATION",
        "jurisdiction": "RU",
        "source_class": "clinical_recommendation",
        "status": "REVIEW_REQUIRED",
        "version": None,
        "effective_date": None,
        "accessed_at": None,
        "official_locator": None,
        "scope": "clinical celiac disease and gluten avoidance",
        "consumer_context": "clinical_context",
        "applicability": ["CLINICAL_CONTEXT"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "exact_official_locator_and_version_required",
        "notes": "Preferred Russian-context clinical authority, but exact official record was not verified in local evidence.",
    },
    "SRC-RU-CLIN-PKU": {
        "title": "Russian Ministry of Health clinical recommendation for phenylketonuria/hyperphenylalaninemia",
        "authority": "Ministry of Health of the Russian Federation",
        "authority_class": "RF_CLINICAL_RECOMMENDATION",
        "jurisdiction": "RU",
        "source_class": "clinical_recommendation",
        "status": "REVIEW_REQUIRED",
        "version": None,
        "effective_date": None,
        "accessed_at": None,
        "official_locator": None,
        "scope": "clinical PKU/PAH nutrition management",
        "consumer_context": "clinical_context",
        "applicability": ["CLINICAL_CONTEXT"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "exact_official_locator_and_version_required",
        "notes": "Preferred Russian-context clinical authority, but exact official record was not verified in local evidence.",
    },
    "SRC-RU-CLIN-CKD": {
        "title": "Russian Ministry of Health clinical recommendation for chronic kidney disease",
        "authority": "Ministry of Health of the Russian Federation",
        "authority_class": "RF_CLINICAL_RECOMMENDATION",
        "jurisdiction": "RU",
        "source_class": "clinical_recommendation",
        "status": "REVIEW_REQUIRED",
        "version": None,
        "effective_date": None,
        "accessed_at": None,
        "official_locator": None,
        "scope": "clinical CKD nutrition context",
        "consumer_context": "clinical_context",
        "applicability": ["CLINICAL_CONTEXT"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "exact_official_locator_and_version_required",
        "notes": "Preferred Russian-context clinical authority, but exact official record was not verified in local evidence.",
    },
    "SRC-RU-CLIN-DIABETES": {
        "title": "Russian Ministry of Health clinical recommendation for diabetes",
        "authority": "Ministry of Health of the Russian Federation",
        "authority_class": "RF_CLINICAL_RECOMMENDATION",
        "jurisdiction": "RU",
        "source_class": "clinical_recommendation",
        "status": "REVIEW_REQUIRED",
        "version": None,
        "effective_date": None,
        "accessed_at": None,
        "official_locator": None,
        "scope": "clinical diabetes medical nutrition therapy context",
        "consumer_context": "clinical_context",
        "applicability": ["CLINICAL_CONTEXT"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "exact_official_locator_and_version_required",
        "notes": "Preferred Russian-context clinical authority, but exact official record was not verified in local evidence.",
    },
    "SRC-RU-CLIN-PREGNANCY-FOOD-SAFETY": {
        "title": "Russian clinical/public-health source for pregnancy food safety",
        "authority": "Russian official clinical or public-health authority",
        "authority_class": "RF_CLINICAL_RECOMMENDATION",
        "jurisdiction": "RU",
        "source_class": "clinical_or_public_health_guidance",
        "status": "REVIEW_REQUIRED",
        "version": None,
        "effective_date": None,
        "accessed_at": None,
        "official_locator": None,
        "scope": "pregnancy food safety and process-state risks",
        "consumer_context": "clinical_context",
        "applicability": ["CLINICAL_CONTEXT"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "exact_official_locator_and_version_required",
        "notes": "Preferred Russian-context authority, but exact official record was not verified in local evidence.",
    },
    "SRC-NIAID-FOOD-ALLERGY": {
        "title": "NIAID-sponsored food allergy guidelines",
        "authority": "NIAID",
        "authority_class": "INTERNATIONAL_CLINICAL_GUIDANCE",
        "jurisdiction": "US",
        "source_class": "clinical_guideline",
        "status": "REVIEW_REQUIRED",
        "version": "selected_research_2026_09_09",
        "effective_date": None,
        "accessed_at": "2026-09-20",
        "official_locator": "https://www.niaid.nih.gov/diseases-conditions/food-allergy-guidelines-faq",
        "scope": "food allergy concepts and management",
        "consumer_context": "clinical_context",
        "applicability": ["CLINICAL_CONTEXT"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "exact_claim_mapping_required",
        "notes": "Retained as supplementary international guidance; Russian/EAEU authority precedes it where adequate.",
    },
    "SRC-NIDDK-CELIAC": {
        "title": "NIDDK celiac disease diet and nutrition guidance",
        "authority": "NIDDK",
        "authority_class": "INTERNATIONAL_CLINICAL_GUIDANCE",
        "jurisdiction": "US",
        "source_class": "public_health_guidance",
        "status": "REVIEW_REQUIRED",
        "version": "selected_research_2026_09_09",
        "effective_date": None,
        "accessed_at": "2026-09-20",
        "official_locator": "https://www.niddk.nih.gov/health-information/digestive-diseases/celiac-disease/eating-diet-nutrition",
        "scope": "celiac gluten avoidance, label checking, and cross-contact",
        "consumer_context": "clinical_context",
        "applicability": ["CLINICAL_CONTEXT"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "exact_claim_mapping_required",
        "notes": "Retained as supplementary international guidance for claims not closed by Russian/EAEU sources.",
    },
    "SRC-CODEX-CXS1": {
        "title": "Codex CXS 1 General Standard for the Labelling of Prepackaged Foods",
        "authority": "Codex Alimentarius",
        "authority_class": "INTERNATIONAL_GUIDANCE",
        "jurisdiction": "GLOBAL",
        "source_class": "standard",
        "status": "REVIEW_REQUIRED",
        "version": None,
        "effective_date": None,
        "accessed_at": None,
        "official_locator": None,
        "scope": "prepackaged food labeling concepts",
        "consumer_context": "product_label_facts",
        "applicability": ["LABEL_FACTS"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "local_alias_to_src_codex_0002_requires_locator",
        "notes": "Existing runtime id retained; alias relation to SRC-CODEX-0002 is explicit.",
    },
    "SRC-NCBI-PAH-2025": {
        "title": "International PAH/PKU clinical evidence package",
        "authority": "NCBI/PubMed-indexed literature",
        "authority_class": "INTERNATIONAL_CLINICAL_GUIDANCE",
        "jurisdiction": "GLOBAL",
        "source_class": "clinical_literature",
        "status": "REVIEW_REQUIRED",
        "version": "selected_research_2026_09_09",
        "effective_date": None,
        "accessed_at": None,
        "official_locator": None,
        "scope": "PKU/PAH nutrition management concepts",
        "consumer_context": "clinical_context",
        "applicability": ["CLINICAL_CONTEXT", "DATA_COVERAGE_REQUIRED"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "exact_article_or_guideline_locator_required",
        "notes": "Supplementary only until Russian official clinical source and exact international locator are closed.",
    },
    "SRC-KDIGO-CKD-2024": {
        "title": "KDIGO 2024 CKD guideline",
        "authority": "KDIGO",
        "authority_class": "INTERNATIONAL_CLINICAL_GUIDANCE",
        "jurisdiction": "GLOBAL",
        "source_class": "clinical_guideline",
        "status": "REVIEW_REQUIRED",
        "version": "2024",
        "effective_date": None,
        "accessed_at": "2026-09-20",
        "official_locator": "https://kdigo.org/guidelines/ckd-evaluation-and-management/",
        "scope": "CKD clinical management and nutrition context",
        "consumer_context": "clinical_context",
        "applicability": ["CLINICAL_CONTEXT"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "exact_claim_mapping_required",
        "notes": "Supplementary until Russian official clinical source is closed for the exact claim.",
    },
    "SRC-ADA-2026": {
        "title": "ADA Standards of Care in Diabetes 2026",
        "authority": "American Diabetes Association",
        "authority_class": "INTERNATIONAL_CLINICAL_GUIDANCE",
        "jurisdiction": "US",
        "source_class": "clinical_guideline",
        "status": "REVIEW_REQUIRED",
        "version": "2026",
        "effective_date": None,
        "accessed_at": "2026-09-20",
        "official_locator": "https://professional.diabetes.org/standards-of-care",
        "scope": "diabetes care and individualized medical nutrition therapy",
        "consumer_context": "clinical_context",
        "applicability": ["CLINICAL_CONTEXT"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "exact_claim_mapping_required",
        "notes": "Supplementary until Russian official clinical source is closed for the exact claim.",
    },
    "SRC-CDC-PREGNANCY-FOOD-SAFETY": {
        "title": "CDC pregnancy food safety guidance",
        "authority": "CDC",
        "authority_class": "INTERNATIONAL_GUIDANCE",
        "jurisdiction": "US",
        "source_class": "public_health_guidance",
        "status": "REVIEW_REQUIRED",
        "version": "selected_research_2026_09_09",
        "effective_date": None,
        "accessed_at": "2026-09-20",
        "official_locator": "https://www.cdc.gov/food-safety/foods/pregnant-women.html",
        "scope": "pregnancy food safety and high-risk process states",
        "consumer_context": "clinical_context",
        "applicability": ["CLINICAL_CONTEXT", "DATA_COVERAGE_REQUIRED"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "exact_claim_mapping_required",
        "notes": "Supplementary until Russian official source is closed for the exact claim.",
    },
    "SRC-WHO-SODIUM": {
        "title": "WHO guideline: sodium intake for adults and children",
        "authority": "WHO",
        "authority_class": "INTERNATIONAL_GUIDANCE",
        "jurisdiction": "GLOBAL",
        "source_class": "guideline",
        "status": "VERIFIED",
        "version": "2012",
        "effective_date": "2012-12-25",
        "accessed_at": "2026-09-20",
        "official_locator": "https://www.who.int/publications/i/item/9789241504836",
        "scope": "sodium and salt intake guidance",
        "consumer_context": "public_health_reference",
        "applicability": ["HOUSEHOLD_REFERENCE"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "verified_with_official_locator",
        "notes": "Same source as legacy registry seed SRC-WHO-0005; adult target is source-backed, child resolver remains review-required.",
    },
    "SRC-PLANAM-SAFETY-POLICY": {
        "title": "PLANAM conservative deterministic safety policy",
        "authority": "PLANAM",
        "authority_class": "PLANAM_POLICY",
        "jurisdiction": "INTERNAL",
        "source_class": "product_policy",
        "status": "VERIFIED",
        "version": "p0_safety_policy_v1",
        "effective_date": None,
        "accessed_at": None,
        "official_locator": None,
        "scope": "product safety invariants for uncertainty, AI, and family aggregation",
        "consumer_context": "product_policy",
        "applicability": ["PRODUCT_POLICY"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "internal_policy",
        "notes": "Supports UNKNOWN != SAFE and AI cannot override deterministic safety; it is not presented as law.",
    },
    "SRC-PLANAM-V1-NUTRITION-FACTS": {
        "title": "PLANAM v1 internal legacy nutrition facts",
        "authority": "PLANAM",
        "authority_class": "INTERNAL_LEGACY",
        "jurisdiction": "INTERNAL",
        "source_class": "internal_legacy_unsourced",
        "status": "LEGACY_UNSOURCED",
        "version": "planam_v1",
        "effective_date": None,
        "accessed_at": None,
        "official_locator": None,
        "scope": "legacy hard-coded nutrition facts",
        "consumer_context": "legacy_fallback",
        "applicability": ["DATA_COVERAGE_REQUIRED"],
        "supersedes": [],
        "superseded_by": [],
        "review_status": "legacy_unsourced",
        "notes": "Retained only so legacy facts stay labeled and cannot masquerade as verified external evidence.",
    },
}

SOURCE_ALIAS_MATRIX: list[dict[str, Any]] = [
    {
        "existing_source_id": "SRC-WHO-0005",
        "canonical_source_id": "SRC-WHO-SODIUM",
        "relationship": "SAME_SOURCE",
        "migration_needed": False,
        "runtime_compatibility_needed": True,
        "reason": "Runtime uses SRC-WHO-SODIUM; prior source registry seed uses SRC-WHO-0005 for the same WHO sodium guidance.",
    },
    {
        "existing_source_id": "SRC-CODEX-0002",
        "canonical_source_id": "SRC-CODEX-CXS1",
        "relationship": "ALIAS",
        "migration_needed": False,
        "runtime_compatibility_needed": True,
        "reason": "Runtime uses a Codex CXS1 id; prior registry seed uses generic Codex labeling id.",
    },
    {
        "existing_source_id": "SRC-RU-0001",
        "canonical_source_id": "SRC-RU-MR-0253-21",
        "relationship": "ALIAS",
        "migration_needed": False,
        "runtime_compatibility_needed": True,
        "reason": "Runtime uses descriptive MR id; source seed used numeric RU id.",
    },
    {
        "existing_source_id": "SRC-RU-0009",
        "canonical_source_id": "SRC-RU-SANPIN-3590-20",
        "relationship": "ALIAS",
        "migration_needed": False,
        "runtime_compatibility_needed": False,
        "reason": "Both identify superseded SanPiN 2.3/2.4.3590-20 evidence.",
    },
    {
        "existing_source_id": "SRC-RU-0012",
        "canonical_source_id": "SRC-RU-SANPIN-4282-26",
        "relationship": "ALIAS",
        "migration_needed": False,
        "runtime_compatibility_needed": False,
        "reason": "Both identify current SanPiN 2.3/2.4.4282-26 evidence.",
    },
    {
        "existing_source_id": "SRC-HANDOFF-RU-FOOD-SAFETY-CORE",
        "canonical_source_id": "SRC-PLANAM-SAFETY-POLICY",
        "relationship": "ALIAS",
        "migration_needed": False,
        "runtime_compatibility_needed": True,
        "reason": "Existing medical safety registry uses a handoff source id for internal conservative product policy.",
    },
]

RULE_SOURCE_TRACEABILITY: dict[str, list[dict[str, Any]]] = {
    "V2-AL-001": [
        {
            "claim": "Typed profile safety entries keep allergy, intolerance, medical condition, diet, preference, and legacy kinds distinct.",
            "source_id": "SRC-RU-CLIN-FOOD-ALLERGY",
            "source_role": "PRIMARY",
            "authority_class": "RF_CLINICAL_RECOMMENDATION",
            "scope": "clinical food allergy concepts",
            "applicability": "CLINICAL_CONTEXT",
            "version": None,
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-AL-001",
            "runtime_path": "app.nutrition.allergen_ontology.TypedSafetyEntry",
            "notes": "Preferred Russian clinical source identity requires official locator/version closure.",
        },
        {
            "claim": "International guidance remains supplementary for food allergy concept separation.",
            "source_id": "SRC-NIAID-FOOD-ALLERGY",
            "source_role": "SUPPLEMENTARY",
            "authority_class": "INTERNATIONAL_CLINICAL_GUIDANCE",
            "scope": "food allergy concepts",
            "applicability": "CLINICAL_CONTEXT",
            "version": "selected_research_2026_09_09",
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-AL-001",
            "runtime_path": "app.nutrition.allergen_ontology.TypedSafetyEntry",
            "notes": "Retained; not promoted over Russian source for Russian product context.",
        },
    ],
    "V2-AL-002": [
        {
            "claim": "Peanut/tree nut and fish/crustacean/mollusc concepts remain distinct.",
            "source_id": "SRC-RU-TR-022",
            "source_role": "PRIMARY",
            "authority_class": "RF_EAEU_REGULATION",
            "scope": "label-derived ingredient/allergen facts",
            "applicability": "LABEL_FACTS",
            "version": "TR-TS-022-2011",
            "verification_status": "VERIFIED",
            "engine_mapping": "EV-AL-003",
            "runtime_path": "app.nutrition.allergen_ontology.ALLERGEN_CONCEPTS",
            "notes": "Supports product label fact categories; clinical allergy decision still needs clinical authority.",
        },
        {
            "claim": "Clinical allergen distinctions remain review-required until Russian clinical source is closed.",
            "source_id": "SRC-RU-CLIN-FOOD-ALLERGY",
            "source_role": "PRIMARY",
            "authority_class": "RF_CLINICAL_RECOMMENDATION",
            "scope": "clinical food allergy concepts",
            "applicability": "CLINICAL_CONTEXT",
            "version": None,
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-AL-003",
            "runtime_path": "app.nutrition.allergen_ontology.ALLERGEN_CONCEPTS",
            "notes": "Does not weaken existing concept separation.",
        },
    ],
    "V2-AL-003": [
        {
            "claim": "contains, may_contain, cross_contact, and unknown are preserved as relation types.",
            "source_id": "SRC-RU-TR-022",
            "source_role": "PRIMARY",
            "authority_class": "RF_EAEU_REGULATION",
            "scope": "structured product label facts",
            "applicability": "LABEL_FACTS",
            "version": "TR-TS-022-2011",
            "verification_status": "VERIFIED",
            "engine_mapping": "EV-AL-004",
            "runtime_path": "app.nutrition.allergen_ontology.AllergenFact",
            "notes": "Regulatory label facts support structured provenance; cross-contact semantics remain conservative product/clinical handling.",
        },
        {
            "claim": "Conservative handling of may/cross/unknown is product policy when label facts are incomplete.",
            "source_id": "SRC-PLANAM-SAFETY-POLICY",
            "source_role": "PRIMARY",
            "authority_class": "PLANAM_POLICY",
            "scope": "uncertainty handling",
            "applicability": "PRODUCT_POLICY",
            "version": "p0_safety_policy_v1",
            "verification_status": "VERIFIED",
            "engine_mapping": "EV-AL-004",
            "runtime_path": "app.nutrition.restriction_safety",
            "notes": "Policy is not represented as law.",
        },
    ],
    "V2-AL-004": [
        {
            "claim": "Celiac is a medical condition and gluten-free safety cannot be certified by keyword/tag/AI-only evidence.",
            "source_id": "SRC-RU-CLIN-CELIAC",
            "source_role": "PRIMARY",
            "authority_class": "RF_CLINICAL_RECOMMENDATION",
            "scope": "clinical celiac disease",
            "applicability": "CLINICAL_CONTEXT",
            "version": None,
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-AL-006",
            "runtime_path": "app.nutrition.allergen_ontology.decide_celiac_gluten_free",
            "notes": "Exact official Russian source requires closure.",
        },
        {
            "claim": "NIDDK celiac guidance is retained for gluten avoidance, label checking, and cross-contact concepts.",
            "source_id": "SRC-NIDDK-CELIAC",
            "source_role": "SUPPLEMENTARY",
            "authority_class": "INTERNATIONAL_CLINICAL_GUIDANCE",
            "scope": "celiac diet and cross-contact",
            "applicability": "CLINICAL_CONTEXT",
            "version": "selected_research_2026_09_09",
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-AL-006",
            "runtime_path": "app.nutrition.allergen_ontology.decide_celiac_gluten_free",
            "notes": "Supplementary source is retained, not silently removed.",
        },
        {
            "claim": "TR TS 027 gluten threshold is scoped to specialized foods only.",
            "source_id": "SRC-EAEU-TR-027",
            "source_role": "SECONDARY",
            "authority_class": "RF_EAEU_REGULATION",
            "scope": "specialized-food labeling",
            "applicability": "SPECIALIZED_FOOD_LABELING",
            "version": "TR-TS-027-2012",
            "verification_status": "VERIFIED",
            "engine_mapping": "EV-AL-007",
            "runtime_path": "app.nutrition.allergen_ontology.decide_celiac_gluten_free",
            "notes": "Not generalized to every home-prepared dish.",
        },
        {
            "claim": "Codex labeling concepts remain supplementary for prepackaged gluten-free/label claims.",
            "source_id": "SRC-CODEX-CXS1",
            "source_role": "SUPPLEMENTARY",
            "authority_class": "INTERNATIONAL_GUIDANCE",
            "scope": "prepackaged food labeling concepts",
            "applicability": "LABEL_FACTS",
            "version": None,
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-AL-007",
            "runtime_path": "app.nutrition.allergen_ontology.decide_celiac_gluten_free",
            "notes": "Retained with explicit role; not used as a universal home-prepared dish rule.",
        },
    ],
    "V2-AL-006": [
        {
            "claim": "Structured allergen/gluten fact coverage is required before deterministic decisions can be evidence-complete.",
            "source_id": "SRC-PLANAM-SAFETY-POLICY",
            "source_role": "PRIMARY",
            "authority_class": "PLANAM_POLICY",
            "scope": "data coverage requirement",
            "applicability": "DATA_COVERAGE_REQUIRED",
            "version": "p0_safety_policy_v1",
            "verification_status": "VERIFIED",
            "engine_mapping": "EV-AL-006",
            "runtime_path": "app.nutrition.allergen_ontology.collect_recipe_allergen_facts",
            "notes": "No data backfill in this stage.",
        }
    ],
    "V2-MD-001": [
        {
            "claim": "Medical context must be explicit typed person-scoped data; free text and AI cannot diagnose.",
            "source_id": "SRC-PLANAM-SAFETY-POLICY",
            "source_role": "PRIMARY",
            "authority_class": "PLANAM_POLICY",
            "scope": "diagnostic inference boundary",
            "applicability": "PRODUCT_POLICY",
            "version": "p0_safety_policy_v1",
            "verification_status": "VERIFIED",
            "engine_mapping": "EV-MD-001",
            "runtime_path": "app.nutrition.medical_safety.normalize_medical_context_entries",
            "notes": "Internal safety boundary; not fabricated as statute.",
        }
    ],
    "V2-MD-002": [
        {
            "claim": "PKU/PAH requires individualized specialist phenylalanine target/plan and recipe phenylalanine/aspartame facts.",
            "source_id": "SRC-RU-CLIN-PKU",
            "source_role": "PRIMARY",
            "authority_class": "RF_CLINICAL_RECOMMENDATION",
            "scope": "PKU/PAH clinical nutrition",
            "applicability": "CLINICAL_CONTEXT",
            "version": None,
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-MD-002",
            "runtime_path": "app.nutrition.medical_safety.evaluate_medical_safety",
            "notes": "Russian clinical source identity remains open.",
        },
        {
            "claim": "International PAH/PKU evidence remains supplementary until exact locator is closed.",
            "source_id": "SRC-NCBI-PAH-2025",
            "source_role": "SUPPLEMENTARY",
            "authority_class": "INTERNATIONAL_CLINICAL_GUIDANCE",
            "scope": "PKU/PAH evidence",
            "applicability": "CLINICAL_CONTEXT",
            "version": "selected_research_2026_09_09",
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-MD-002",
            "runtime_path": "app.nutrition.medical_safety.evaluate_medical_safety",
            "notes": "Does not invent phenylalanine targets.",
        },
    ],
    "V2-MD-003": [
        {
            "claim": "CKD requires clinician targets/stage and must not infer generic disease macros.",
            "source_id": "SRC-RU-CLIN-CKD",
            "source_role": "PRIMARY",
            "authority_class": "RF_CLINICAL_RECOMMENDATION",
            "scope": "CKD clinical nutrition context",
            "applicability": "CLINICAL_CONTEXT",
            "version": None,
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-MD-004",
            "runtime_path": "app.nutrition.medical_safety.evaluate_medical_safety",
            "notes": "Russian clinical source identity remains open.",
        },
        {
            "claim": "KDIGO remains supplementary for CKD clinical context.",
            "source_id": "SRC-KDIGO-CKD-2024",
            "source_role": "SUPPLEMENTARY",
            "authority_class": "INTERNATIONAL_CLINICAL_GUIDANCE",
            "scope": "CKD clinical guideline",
            "applicability": "CLINICAL_CONTEXT",
            "version": "2024",
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-MD-004",
            "runtime_path": "app.nutrition.medical_safety.evaluate_medical_safety",
            "notes": "Retained, but no universal macro prescription is introduced.",
        },
    ],
    "V2-MD-004": [
        {
            "claim": "Diabetes nutrition context requires individualized MNT and must not impose universal fixed macros.",
            "source_id": "SRC-RU-CLIN-DIABETES",
            "source_role": "PRIMARY",
            "authority_class": "RF_CLINICAL_RECOMMENDATION",
            "scope": "diabetes clinical nutrition context",
            "applicability": "CLINICAL_CONTEXT",
            "version": None,
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-MD-003",
            "runtime_path": "app.nutrition.medical_safety.evaluate_medical_safety",
            "notes": "Russian clinical source identity remains open.",
        },
        {
            "claim": "ADA remains supplementary for individualized medical nutrition therapy context.",
            "source_id": "SRC-ADA-2026",
            "source_role": "SUPPLEMENTARY",
            "authority_class": "INTERNATIONAL_CLINICAL_GUIDANCE",
            "scope": "diabetes clinical guideline",
            "applicability": "CLINICAL_CONTEXT",
            "version": "2026",
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-MD-003",
            "runtime_path": "app.nutrition.medical_safety.evaluate_medical_safety",
            "notes": "Retained, but no universal fixed macro target is introduced.",
        },
    ],
    "V2-MD-005": [
        {
            "claim": "Adult sodium target preserves sodium and salt units; child adjustment is not invented.",
            "source_id": "SRC-WHO-SODIUM",
            "source_role": "PRIMARY",
            "authority_class": "INTERNATIONAL_GUIDANCE",
            "scope": "public-health sodium/salt intake guidance",
            "applicability": "HOUSEHOLD_REFERENCE",
            "version": "2012",
            "verification_status": "VERIFIED",
            "engine_mapping": "EV-MD-005",
            "runtime_path": "app.nutrition.medical_safety.resolve_sodium_target",
            "notes": "SRC-WHO-0005 is an alias for this runtime source id.",
        }
    ],
    "V2-MD-006": [
        {
            "claim": "Pregnancy safety requires structured pasteurization, raw/undercooked, and process-state facts.",
            "source_id": "SRC-RU-CLIN-PREGNANCY-FOOD-SAFETY",
            "source_role": "PRIMARY",
            "authority_class": "RF_CLINICAL_RECOMMENDATION",
            "scope": "pregnancy food safety",
            "applicability": "CLINICAL_CONTEXT",
            "version": None,
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-MD-006",
            "runtime_path": "app.nutrition.medical_safety.evaluate_medical_safety",
            "notes": "Russian official source identity remains open.",
        },
        {
            "claim": "CDC remains supplementary for pregnancy food safety process-state concepts.",
            "source_id": "SRC-CDC-PREGNANCY-FOOD-SAFETY",
            "source_role": "SUPPLEMENTARY",
            "authority_class": "INTERNATIONAL_GUIDANCE",
            "scope": "pregnancy food safety",
            "applicability": "CLINICAL_CONTEXT",
            "version": "selected_research_2026_09_09",
            "verification_status": "REVIEW_REQUIRED",
            "engine_mapping": "EV-MD-006",
            "runtime_path": "app.nutrition.medical_safety.evaluate_medical_safety",
            "notes": "Retained, no data backfill performed.",
        },
    ],
    "V2-MD-007": [
        {
            "claim": "Medical safety facts must be populated before runtime safety can be evidence-complete.",
            "source_id": "SRC-PLANAM-SAFETY-POLICY",
            "source_role": "PRIMARY",
            "authority_class": "PLANAM_POLICY",
            "scope": "data coverage requirement",
            "applicability": "DATA_COVERAGE_REQUIRED",
            "version": "p0_safety_policy_v1",
            "verification_status": "VERIFIED",
            "engine_mapping": "EV-MD-007",
            "runtime_path": "app.nutrition.medical_safety._fact",
            "notes": "No mass data update or backfill in this stage.",
        }
    ],
    "V2-XD-001": [
        {
            "claim": "Deterministic safety must exist before and after AI and AI cannot override it.",
            "source_id": "SRC-PLANAM-SAFETY-POLICY",
            "source_role": "PRIMARY",
            "authority_class": "PLANAM_POLICY",
            "scope": "AI safety boundary",
            "applicability": "PRODUCT_POLICY",
            "version": "p0_safety_policy_v1",
            "verification_status": "VERIFIED",
            "engine_mapping": "menu safety filter",
            "runtime_path": "app.services.menu_restriction_safety",
            "notes": "Product policy, not law.",
        }
    ],
    "V2-XD-002": [
        {
            "claim": "Legacy keyword-only paths must not become canonical source-backed evidence decisions.",
            "source_id": "SRC-PLANAM-SAFETY-POLICY",
            "source_role": "PRIMARY",
            "authority_class": "PLANAM_POLICY",
            "scope": "legacy compatibility boundary",
            "applicability": "PRODUCT_POLICY",
            "version": "p0_safety_policy_v1",
            "verification_status": "VERIFIED",
            "engine_mapping": "legacy safety bridges",
            "runtime_path": "app.nutrition.allergen_ontology.legacy_bridge_entries",
            "notes": "Legacy bridges stay reviewable.",
        }
    ],
}


def resolve_source_id(source_id: str | None) -> str | None:
    """Resolve known aliases while preserving runtime compatibility."""
    if source_id is None:
        return None
    if source_id in CANONICAL_SOURCE_REGISTRY:
        return source_id
    for alias in SOURCE_ALIAS_MATRIX:
        if alias["existing_source_id"] == source_id:
            return alias["canonical_source_id"]
    return source_id


def all_evidence_rule_records() -> dict[str, dict[str, str | None]]:
    records: dict[str, dict[str, str | None]] = {}
    for registry in (
        NUTRITION_TARGET_EVIDENCE_REGISTRY,
        RECIPE_NUTRITION_EVIDENCE_REGISTRY,
        ALLERGEN_SAFETY_EVIDENCE_REGISTRY,
        MEDICAL_SAFETY_EVIDENCE_REGISTRY,
    ):
        records.update(registry)
    return records


def validate_source_authority_registry() -> list[str]:
    """Return source-closure integrity errors without mutating runtime state."""
    errors: list[str] = []
    source_ids = set(CANONICAL_SOURCE_REGISTRY)
    if len(source_ids) != len(CANONICAL_SOURCE_REGISTRY):
        errors.append("duplicate source_id")

    for source_id, source in CANONICAL_SOURCE_REGISTRY.items():
        if source.get("authority_class") not in SOURCE_AUTHORITY_CLASSES:
            errors.append(f"{source_id}: invalid authority_class")
        if source.get("status") not in SOURCE_VERIFICATION_STATUSES:
            errors.append(f"{source_id}: invalid status")
        for applicability in source.get("applicability", []):
            if applicability not in SOURCE_APPLICABILITY:
                errors.append(f"{source_id}: invalid applicability {applicability}")
        if source.get("status") == "REVIEW_REQUIRED" and (
            source.get("review_status") or ""
        ).startswith("verified"):
            errors.append(f"{source_id}: review-required source marked verified")
        for superseded_by in source.get("superseded_by", []):
            if superseded_by == source_id:
                errors.append(f"{source_id}: source supersedes itself")
            if superseded_by not in source_ids:
                errors.append(f"{source_id}: missing superseded_by target {superseded_by}")
        for supersedes in source.get("supersedes", []):
            if supersedes == source_id:
                errors.append(f"{source_id}: source supersedes itself")
            if supersedes not in source_ids:
                errors.append(f"{source_id}: missing supersedes target {supersedes}")
        if (
            "PUBLIC_CATERING_REFERENCE" in source.get("applicability", [])
            and "HOUSEHOLD_REFERENCE" in source.get("applicability", [])
        ):
            errors.append(f"{source_id}: public-catering source marked household")

    for alias in SOURCE_ALIAS_MATRIX:
        if alias.get("relationship") not in SOURCE_RELATIONSHIPS:
            errors.append(f"{alias.get('existing_source_id')}: invalid alias relationship")
        target = alias.get("canonical_source_id")
        if target not in source_ids:
            errors.append(f"{alias.get('existing_source_id')}: alias target missing")

    for rule_id, claims in RULE_SOURCE_TRACEABILITY.items():
        for claim in claims:
            source_id = claim.get("source_id")
            if source_id not in source_ids:
                errors.append(f"{rule_id}: missing source {source_id}")
            if claim.get("source_role") not in SOURCE_ROLES:
                errors.append(f"{rule_id}: invalid source_role")
            if claim.get("authority_class") not in SOURCE_AUTHORITY_CLASSES:
                errors.append(f"{rule_id}: invalid authority_class")
            if claim.get("applicability") not in SOURCE_APPLICABILITY:
                errors.append(f"{rule_id}: invalid applicability")
            if (
                claim.get("verification_status") == "VERIFIED"
                and CANONICAL_SOURCE_REGISTRY[source_id]["status"] == "REVIEW_REQUIRED"
            ):
                errors.append(f"{rule_id}: REVIEW_REQUIRED source used as VERIFIED")
    return errors


__all__ = [
    "ALLERGEN_SAFETY_EVIDENCE_REGISTRY",
    "CANONICAL_SOURCE_REGISTRY",
    "MEDICAL_SAFETY_EVIDENCE_REGISTRY",
    "NUTRITION_TARGET_EVIDENCE_REGISTRY",
    "NUTRITION_TARGET_SOURCE_REGISTRY",
    "RECIPE_NUTRITION_EVIDENCE_REGISTRY",
    "RULE_SOURCE_TRACEABILITY",
    "SOURCE_ALIAS_MATRIX",
    "SOURCE_APPLICABILITY",
    "SOURCE_AUTHORITY_CLASSES",
    "SOURCE_RELATIONSHIPS",
    "SOURCE_ROLES",
    "SOURCE_VERIFICATION_STATUSES",
    "all_evidence_rule_records",
    "resolve_source_id",
    "validate_source_authority_registry",
]
