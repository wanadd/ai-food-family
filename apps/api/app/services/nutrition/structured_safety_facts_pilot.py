"""Structured allergen and celiac dry-run pilot for P0-DATA-FOUNDATION-01B3.

The pilot reuses P0-D ``AllergenFact`` semantics. It does not persist facts,
does not mark recipes safe, and does not infer negative allergen facts from
missing positives.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Literal

from app.nutrition.allergen_ontology import (
    ALLERGEN_CONCEPTS,
    GLUTEN_CONCEPTS,
    AllergenFact,
    aggregate_allergen_facts,
)
from app.services.nutrition.food_identity_foundation import (
    dry_run_food_match,
    normalize_ingredient_name,
    safety_sensitive_flags,
)

PilotSafetyClass = Literal[
    "IDENTITY_SUITABLE",
    "NEEDS_PRODUCT_LABEL",
    "NEEDS_COMPOSITION",
    "AMBIGUOUS_IDENTITY",
    "REVIEW_REQUIRED",
]
RecipeAllergenAuditStatus = Literal[
    "STRUCTURED_POSITIVE_FACTS_AVAILABLE",
    "PARTIAL_STRUCTURED_COVERAGE",
    "UNKNOWN_DUE_TO_UNMAPPED_INGREDIENT",
    "UNKNOWN_DUE_TO_PRODUCT_COMPOSITION",
    "NO_STRUCTURED_SAFETY_EVIDENCE",
]
CeliacAuditStatus = Literal[
    "KNOWN_GLUTEN_SOURCE_PRESENT",
    "PARTIAL_GLUTEN_EVIDENCE",
    "NATURALLY_GF_INGREDIENT_SET_BUT_NOT_VERIFIED",
    "VERIFIED_GF",
    "UNKNOWN",
]

SOURCE_STRATEGY = {
    "intrinsic_curated_identity": {
        "source_id": "SRC-PLANAM-SAFETY-POLICY",
        "source_role": "PRIMARY",
        "evidence_type": "curated_intrinsic_food_identity",
        "verification_status": "curated_reviewed",
        "scope": "GENERIC_FOOD_IDENTITY",
    },
    "label_required": {
        "source_id": "SRC-RU-TR-022",
        "source_role": "PRIMARY",
        "evidence_type": "product_label_required",
        "verification_status": "requires_product_label",
        "scope": "PACKAGED_PRODUCT_IDENTITY",
    },
    "clinical_review_required": {
        "source_id": "SRC-RU-CLIN-FOOD-ALLERGY",
        "source_role": "PRIMARY",
        "evidence_type": "clinical_interpretation_review_required",
        "verification_status": "REVIEW_REQUIRED",
        "scope": "CLINICAL_CONTEXT",
    },
}


@dataclass(frozen=True)
class StructuredSafetyFact:
    canonical_food_key: str
    concept_id: str
    relation_type: str
    provenance_status: str
    source_id: str
    source_role: str
    evidence_type: str
    verification_status: str
    scope: str
    source_record_locator: str
    confidence: str = "high"
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.concept_id not in ALLERGEN_CONCEPTS:
            raise ValueError(f"unsupported allergen concept: {self.concept_id}")

    @property
    def fact_class(self) -> str:
        return "gluten_source" if self.concept_id in GLUTEN_CONCEPTS else "allergen"

    def to_allergen_fact(self, *, ingredient_id: int | None = None, ingredient_name: str | None = None) -> AllergenFact:
        return AllergenFact(
            concept_id=self.concept_id,
            relation_type=self.relation_type,
            provenance_status=self.provenance_status,
            confidence=self.confidence,
            source_id=self.source_id,
            source_record_locator=self.source_record_locator,
            ingredient_id=ingredient_id,
            ingredient_name=ingredient_name,
            evidence_notes=self.notes,
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "canonical_food_key": self.canonical_food_key,
            "fact_class": self.fact_class,
            "concept_id": self.concept_id,
            "relation_type": self.relation_type,
            "provenance_status": self.provenance_status,
            "confidence": self.confidence,
            "source_id": self.source_id,
            "source_role": self.source_role,
            "evidence_type": self.evidence_type,
            "verification_status": self.verification_status,
            "scope": self.scope,
            "source_record_locator": self.source_record_locator,
            "notes": self.notes,
        }


def _intrinsic_fact(food: str, concept: str, *, notes: str | None = None) -> StructuredSafetyFact:
    src = SOURCE_STRATEGY["intrinsic_curated_identity"]
    return StructuredSafetyFact(
        canonical_food_key=food,
        concept_id=concept,
        relation_type="contains",
        provenance_status="curated_reviewed",
        source_id=src["source_id"],
        source_role=src["source_role"],
        evidence_type=src["evidence_type"],
        verification_status=src["verification_status"],
        scope=src["scope"],
        source_record_locator=f"planam_01b3_intrinsic_food:{food}:{concept}",
        notes=notes,
    )


CURATED_INTRINSIC_FACTS: dict[str, tuple[StructuredSafetyFact, ...]] = {
    "peanut": (_intrinsic_fact("peanut", "peanut"),),
    "milk": (_intrinsic_fact("milk", "milk_protein", notes="Milk protein allergen; not lactose intolerance."),),
    "butter": (_intrinsic_fact("butter", "milk_protein", notes="Dairy identity; product label still needed for formulation/cross-contact."),),
    "yogurt": (_intrinsic_fact("yogurt", "milk_protein"),),
    "cottage_cheese": (_intrinsic_fact("cottage_cheese", "milk_protein"),),
    "chicken_egg": (_intrinsic_fact("chicken_egg", "egg"),),
    "cod": (_intrinsic_fact("cod", "fish"),),
    "shrimp": (_intrinsic_fact("shrimp", "crustacean"),),
    "tofu": (_intrinsic_fact("tofu", "soy", notes="Generic tofu supports soy identity; product label still needed for additives/cross-contact."),),
    "wheat_flour": (_intrinsic_fact("wheat_flour", "wheat", notes="Gluten-source cereal derivative."),),
    "barley_groats": (_intrinsic_fact("barley_groats", "barley", notes="Gluten-source cereal."),),
    "rye_flour": (_intrinsic_fact("rye_flour", "rye", notes="Gluten-source cereal derivative."),),
}

NATURALLY_GF_CANDIDATE_FOODS = frozenset(
    {
        "banana",
        "buckwheat_groats",
        "carrot",
        "chicken_egg",
        "chicken_fillet",
        "cod",
        "cucumber",
        "garlic",
        "onion",
        "rice",
        "salt",
        "shrimp",
        "spinach",
        "sugar",
    }
)
PRODUCT_LABEL_REQUIRED_FOODS = frozenset(
    {
        "butter",
        "cottage_cheese",
        "milk",
        "olive_oil",
        "sour_cream",
        "tofu",
        "yogurt",
    }
)
COMPOSITION_REQUIRED_NAMES = frozenset(
    {
        "бекон",
        "ветчина",
        "колбаса",
        "крабовые палочки",
        "майонез",
        "приправа",
        "соус",
        "специи",
        "смесь перцев",
    }
)
GLUTEN_SOURCE_NAME_MAP = {
    "мука пшеничная": "wheat_flour",
    "хлеб": "wheat_flour",
    "хлебцы": "wheat_flour",
    "макаронные изделия": "wheat_flour",
    "крупа перловая": "barley_groats",
}
MANUAL_CANONICAL_ALIASES = {
    **GLUTEN_SOURCE_NAME_MAP,
    "молоко": "milk",
    "масло сливочное": "butter",
    "йогурт": "yogurt",
    "творог": "cottage_cheese",
    "тофу": "tofu",
    "арахис": "peanut",
}


def canonical_food_for_safety(name: str) -> str | None:
    normalized = normalize_ingredient_name(name)
    if normalized in MANUAL_CANONICAL_ALIASES:
        return MANUAL_CANONICAL_ALIASES[normalized]
    match = dry_run_food_match(normalized)
    return match.canonical_food_key if match.status == "matched" else None


def structured_facts_for_food(canonical_food_key: str | None) -> tuple[StructuredSafetyFact, ...]:
    if not canonical_food_key:
        return ()
    return CURATED_INTRINSIC_FACTS.get(canonical_food_key, ())


def classify_pilot_food(name: str) -> dict[str, Any]:
    normalized = normalize_ingredient_name(name)
    canonical = canonical_food_for_safety(normalized)
    if normalized in COMPOSITION_REQUIRED_NAMES:
        status: PilotSafetyClass = "NEEDS_COMPOSITION"
        reason = "composite_or_packaged_food_requires_composition_or_label"
    elif canonical in PRODUCT_LABEL_REQUIRED_FOODS:
        status = "NEEDS_PRODUCT_LABEL"
        reason = "generic identity cannot prove label, formulation, may-contain, or cross-contact facts"
    elif canonical and structured_facts_for_food(canonical):
        status = "IDENTITY_SUITABLE"
        reason = "curated intrinsic positive relation exists"
    elif canonical in NATURALLY_GF_CANDIDATE_FOODS:
        status = "IDENTITY_SUITABLE"
        reason = "identity suitable for naturally-GF candidate only; not verified GF"
    elif dry_run_food_match(normalized).status == "ambiguous":
        status = "AMBIGUOUS_IDENTITY"
        reason = "generic ingredient requires disambiguation"
    else:
        status = "REVIEW_REQUIRED"
        reason = "no accepted structured safety fact mapping"
    return {
        "normalized_ingredient": normalized,
        "canonical_food_key": canonical,
        "pilot_classification": status,
        "reason": reason,
        "safety_sensitive_flags": list(safety_sensitive_flags(normalized)),
        "structured_fact_count": len(structured_facts_for_food(canonical)),
        "naturally_gf_candidate": canonical in NATURALLY_GF_CANDIDATE_FOODS,
        "verified_gf_product": False,
    }


def ingredient_safety_record(row: dict[str, Any]) -> dict[str, Any]:
    name = str(row.get("name") or row.get("normalized_ingredient") or "")
    pilot = classify_pilot_food(name)
    facts = [
        fact.to_allergen_fact(
            ingredient_id=int(row["id"]) if row.get("id") is not None else None,
            ingredient_name=name,
        ).to_dict()
        for fact in structured_facts_for_food(pilot["canonical_food_key"])
    ]
    gluten_facts = [fact for fact in facts if fact["concept_id"] in GLUTEN_CONCEPTS]
    return {
        "recipe_id": int(row["recipe_id"]) if row.get("recipe_id") is not None else None,
        "ingredient_row_id": int(row["id"]) if row.get("id") is not None else None,
        "ingredient_name": name,
        **pilot,
        "allergen_facts": facts,
        "gluten_facts": gluten_facts,
        "has_positive_structured_fact": any(fact["relation_type"] == "contains" for fact in facts),
        "has_gluten_source_fact": any(fact["relation_type"] == "contains" for fact in gluten_facts),
        "requires_product_label": pilot["pilot_classification"] == "NEEDS_PRODUCT_LABEL",
        "requires_composition": pilot["pilot_classification"] == "NEEDS_COMPOSITION",
        "unresolved": pilot["pilot_classification"] in {"AMBIGUOUS_IDENTITY", "REVIEW_REQUIRED", "NEEDS_PRODUCT_LABEL", "NEEDS_COMPOSITION"},
    }


def _recipe_allergen_status(rows: list[dict[str, Any]]) -> RecipeAllergenAuditStatus:
    if any(row["has_positive_structured_fact"] for row in rows):
        return "STRUCTURED_POSITIVE_FACTS_AVAILABLE"
    if any(row["requires_composition"] for row in rows):
        return "UNKNOWN_DUE_TO_PRODUCT_COMPOSITION"
    if any(row["unresolved"] for row in rows):
        return "UNKNOWN_DUE_TO_UNMAPPED_INGREDIENT"
    if any(row["pilot_classification"] == "IDENTITY_SUITABLE" for row in rows):
        return "PARTIAL_STRUCTURED_COVERAGE"
    return "NO_STRUCTURED_SAFETY_EVIDENCE"


def _recipe_celiac_status(rows: list[dict[str, Any]], *, verified_gf: bool = False) -> CeliacAuditStatus:
    if verified_gf:
        return "VERIFIED_GF"
    if any(row["has_gluten_source_fact"] for row in rows):
        return "KNOWN_GLUTEN_SOURCE_PRESENT"
    if rows and all(row["naturally_gf_candidate"] for row in rows):
        return "NATURALLY_GF_INGREDIENT_SET_BUT_NOT_VERIFIED"
    if any(row["naturally_gf_candidate"] or row["has_gluten_source_fact"] for row in rows):
        return "PARTIAL_GLUTEN_EVIDENCE"
    return "UNKNOWN"


def simulate_structured_safety(ingredient_rows: list[dict[str, Any]], recipe_tags: dict[int, list[str]] | None = None) -> dict[str, Any]:
    records = [ingredient_safety_record(row) for row in ingredient_rows]
    by_recipe: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["recipe_id"] is not None:
            by_recipe[record["recipe_id"]].append(record)

    recipe_allergen_records: list[dict[str, Any]] = []
    recipe_celiac_records: list[dict[str, Any]] = []
    legacy_comparisons: list[dict[str, Any]] = []
    for recipe_id, rows in sorted(by_recipe.items()):
        all_facts = [
            AllergenFact(
                concept_id=fact["concept_id"],
                relation_type=fact["relation_type"],
                provenance_status=fact["provenance_status"],
                confidence=fact["confidence"],
                source_id=fact["source_id"],
                source_record_locator=fact["source_record_locator"],
                ingredient_id=fact["ingredient_id"],
                ingredient_name=fact["ingredient_name"],
                evidence_notes=fact["evidence_notes"],
            )
            for row in rows
            for fact in row["allergen_facts"]
        ]
        aggregated = aggregate_allergen_facts(all_facts)
        allergen_status = _recipe_allergen_status(rows)
        celiac_status = _recipe_celiac_status(rows)
        recipe_allergen_records.append(
            {
                "recipe_id": recipe_id,
                "audit_status": allergen_status,
                "aggregated_positive_relations": aggregated,
                "complete_relevant_identity_coverage": all(not row["unresolved"] for row in rows),
                "unresolved_reasons": sorted({row["pilot_classification"] for row in rows if row["unresolved"]}),
                "safe_claim_generated": False,
            }
        )
        tags = [str(tag).lower() for tag in (recipe_tags or {}).get(recipe_id, [])]
        tag_status = "NO_TAG"
        if "gluten_free" in tags or "без глютена" in tags:
            tag_status = (
                "TAG_CONFLICTS_WITH_STRUCTURED_EVIDENCE"
                if celiac_status == "KNOWN_GLUTEN_SOURCE_PRESENT"
                else "TAG_UNVERIFIED"
            )
        recipe_celiac_records.append(
            {
                "recipe_id": recipe_id,
                "celiac_status": celiac_status,
                "known_gluten_concepts": sorted(
                    {fact["concept_id"] for row in rows for fact in row["gluten_facts"]}
                ),
                "naturally_gf_candidate": celiac_status == "NATURALLY_GF_INGREDIENT_SET_BUT_NOT_VERIFIED",
                "verified_gf": celiac_status == "VERIFIED_GF",
                "legacy_tag_status": tag_status,
                "safe_claim_generated": False,
            }
        )
        if tag_status != "NO_TAG" or aggregated:
            legacy_comparisons.append(
                {
                    "recipe_id": recipe_id,
                    "comparison": (
                        "CONFLICTS"
                        if tag_status == "TAG_CONFLICTS_WITH_STRUCTURED_EVIDENCE"
                        else ("STRUCTURED_ONLY" if aggregated and tag_status == "NO_TAG" else "LEGACY_ONLY")
                    ),
                    "legacy_tag_status": tag_status,
                    "structured_concepts": sorted(aggregated.keys()),
                }
            )

    metrics = {
        "ingredient_rows_benefiting_from_structured_safety_facts": sum(
            1 for row in records if row["has_positive_structured_fact"]
        ),
        "ingredient_rows_unresolved": sum(1 for row in records if row["unresolved"]),
        "safety_sensitive_ingredient_rows_unresolved": sum(
            1 for row in records if row["unresolved"] and row["safety_sensitive_flags"]
        ),
        "recipes_with_structured_allergen_facts": sum(
            1 for row in recipe_allergen_records if row["aggregated_positive_relations"]
        ),
        "recipes_with_known_gluten_source": sum(
            1 for row in recipe_celiac_records if row["celiac_status"] == "KNOWN_GLUTEN_SOURCE_PRESENT"
        ),
        "recipes_with_complete_structured_safety_coverage": sum(
            1 for row in recipe_allergen_records if row["complete_relevant_identity_coverage"]
        ),
        "recipes_with_partial_safety_coverage": sum(
            1 for row in recipe_allergen_records if row["audit_status"] in {"STRUCTURED_POSITIVE_FACTS_AVAILABLE", "PARTIAL_STRUCTURED_COVERAGE"} and not row["complete_relevant_identity_coverage"]
        ),
        "recipes_unresolved": sum(
            1 for row in recipe_allergen_records if not row["complete_relevant_identity_coverage"]
        ),
        "naturally_gf_candidate_recipes": sum(
            1 for row in recipe_celiac_records if row["naturally_gf_candidate"]
        ),
        "verified_gf_recipes": sum(1 for row in recipe_celiac_records if row["verified_gf"]),
        "legacy_conflicts": sum(1 for row in legacy_comparisons if row["comparison"] == "CONFLICTS"),
    }
    return {
        "ingredient_records": records,
        "recipe_allergen_records": recipe_allergen_records,
        "recipe_celiac_records": recipe_celiac_records,
        "legacy_comparisons": legacy_comparisons,
        "metrics": metrics,
    }


def product_label_future_contract() -> dict[str, str]:
    return {
        "product_identity": "canonical product id distinct from generic food identity",
        "brand": "declared brand or manufacturer",
        "gtin_or_barcode": "barcode/GTIN when available",
        "ingredient_declaration": "raw label ingredient declaration text",
        "allergen_declaration": "declared allergen statement",
        "may_contain_statement": "declared may-contain/cross-contact text",
        "label_source": "photo, OCR, barcode database, or manual entry",
        "label_image_or_text_provenance": "stable locator to captured source",
        "market_jurisdiction": "market where label applies",
        "captured_at": "timestamp of label capture",
        "verification_status": "unreviewed, product_label, curated_reviewed, rejected",
    }
