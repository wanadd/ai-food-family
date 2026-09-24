from __future__ import annotations

from dataclasses import dataclass
from typing import Any

AUTHORITATIVE_SOURCE_TIERS = {"REGULATORY", "AUTHORITATIVE_DATASET", "PRODUCT_LABEL", "CLINICAL_GUIDANCE"}
ALLERGEN_RELATIONS = {"CONTAINS", "MAY_CONTAIN", "CROSS_CONTACT", "UNKNOWN", "ABSENT_VERIFIED"}
VERIFIED_REVIEW_STATUS = "REVIEWED_ACCEPTED"


@dataclass(frozen=True)
class SourceProvenance:
    source_code: str | None
    authority_tier: str | None
    source_version: str | None
    source_record_locator: str | None
    review_status: str | None = None
    confidence: str | None = None

    @property
    def is_source_backed(self) -> bool:
        return bool(
            self.source_code
            and self.authority_tier in AUTHORITATIVE_SOURCE_TIERS
            and self.source_version
            and self.source_record_locator
        )


@dataclass(frozen=True)
class CompositionInput:
    food_identity_key: str
    nutrient_key: str
    value: float | None
    unit: str
    basis_amount: float
    basis_unit: str
    food_state: str
    provenance: SourceProvenance
    derivation: str = "SOURCE_REPORTED"


def can_create_authoritative_composition_fact(input_fact: CompositionInput) -> bool:
    if input_fact.value is None:
        return False
    if input_fact.basis_amount <= 0:
        return False
    if input_fact.derivation != "SOURCE_REPORTED":
        return False
    return input_fact.provenance.is_source_backed


def missing_nutrient_value(input_fact: CompositionInput) -> str:
    return "UNKNOWN" if input_fact.value is None else "KNOWN_PRESENT"


def can_use_protein_as_authoritative_phe(nutrient_key: str, derivation: str) -> bool:
    if nutrient_key.lower() != "phenylalanine_mg":
        return True
    return derivation == "SOURCE_REPORTED"


def resolve_conflicting_values(values: list[CompositionInput]) -> dict[str, Any]:
    distinct = {(item.value, item.unit, item.basis_amount, item.basis_unit, item.food_state) for item in values}
    if len(distinct) <= 1:
        return {"status": "NO_CONFLICT", "averaged": False}
    return {"status": "CONFLICT_RETAINED", "averaged": False, "source_count": len(values)}


def ai_match_review_status(match_method: str, proposed_status: str) -> str:
    if match_method.upper() in {"AI", "AI_SUGGESTED", "FUZZY_AI"}:
        return "NEEDS_REVIEW"
    return proposed_status


def allergen_absence_status(relation: str | None, provenance: SourceProvenance | None) -> str:
    if relation is None:
        return "UNKNOWN"
    normalized = relation.upper()
    if normalized == "ABSENT_VERIFIED" and provenance and provenance.is_source_backed:
        return "ABSENT_VERIFIED"
    if normalized == "ABSENT_VERIFIED":
        return "UNKNOWN"
    if normalized in ALLERGEN_RELATIONS:
        return normalized
    return "UNKNOWN"


def verified_gf_status(food_identity_key: str, product_label_fact: dict[str, Any] | None) -> str:
    if food_identity_key.lower() == "oats" and not product_label_fact:
        return "UNKNOWN"
    if not product_label_fact:
        return "UNKNOWN"
    if product_label_fact.get("fact_type") != "gluten_free_claim":
        return "UNKNOWN"
    if product_label_fact.get("knowledge_state") != "KNOWN_PRESENT":
        return "UNKNOWN"
    provenance = product_label_fact.get("provenance")
    if not isinstance(provenance, SourceProvenance) or not provenance.is_source_backed:
        return "UNKNOWN"
    return "VERIFIED_GF"


def pasteurization_status(food_identity_key: str, product_label_fact: dict[str, Any] | None) -> str:
    if food_identity_key.lower() == "milk" and not product_label_fact:
        return "UNKNOWN"
    if not product_label_fact:
        return "UNKNOWN"
    if product_label_fact.get("fact_type") != "pasteurization":
        return "UNKNOWN"
    if product_label_fact.get("knowledge_state") != "KNOWN_PRESENT":
        return "UNKNOWN"
    provenance = product_label_fact.get("provenance")
    if not isinstance(provenance, SourceProvenance) or not provenance.is_source_backed:
        return "UNKNOWN"
    return "PASTEURIZED"


def recipe_instruction_proves_actual_cooking(_instruction: str) -> bool:
    return False
