"""Recipe nutrition provenance contracts and pure calculation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from app.services.nutrition.food_composition_registry import (
    OBSOLETE_FOR_PRIMARY_SOURCE_IDS,
)

NUTRIENT_KEYS = (
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
PROVENANCE_STATUSES = frozenset(
    {
        "external_verified",
        "external_imported_unreviewed",
        "manual_reviewed",
        "internal_legacy_unsourced",
        "unavailable",
    }
)
FOOD_MATCH_STATUSES = frozenset(
    {"matched", "ambiguous", "unmatched", "manual_review_required"}
)
FoodState = Literal[
    "raw",
    "cooked",
    "boiled",
    "baked",
    "fried",
    "dried",
    "canned/drained",
    "unknown",
]


@dataclass(frozen=True)
class FoodNutrientFact:
    canonical_food_key: str
    nutrient_key: str
    value: float | None
    unit: str
    basis_amount: float
    basis_unit: str
    source_id: str
    source_record_locator: str | None
    source_version: str | None
    food_state: str = "unknown"
    provenance_status: str = "external_imported_unreviewed"
    source_data_type: str | None = None
    fdc_id: int | None = None
    source_food_name: str | None = None
    source_nutrient_id: str | None = None
    source_nutrient_name: str | None = None
    preparation_method: str | None = None
    match_method: str | None = None
    match_confidence: str | None = None
    review_status: str | None = None
    review_notes: str | None = None
    loss_or_retention_metadata: dict | None = None
    retrieved_or_imported_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if self.nutrient_key not in NUTRIENT_KEYS:
            raise ValueError(f"unsupported nutrient_key: {self.nutrient_key}")
        if self.provenance_status not in PROVENANCE_STATUSES:
            raise ValueError(f"unsupported provenance_status: {self.provenance_status}")
        if self.value is None and self.provenance_status != "unavailable":
            raise ValueError("numeric value is required unless fact is unavailable")
        if self.value is not None and self.source_id == "SRC-PLANAM-V1-NUTRITION-FACTS":
            if self.provenance_status != "internal_legacy_unsourced":
                raise ValueError("PLANAM internal facts must be internal_legacy_unsourced")
        if self.provenance_status == "external_verified":
            if not self.source_id or not self.source_record_locator or not self.source_version:
                raise ValueError("external_verified requires source, locator, and version")
            if self.source_id == "SRC-PLANAM-V1-NUTRITION-FACTS":
                raise ValueError("PLANAM internal facts cannot be external_verified")
        if self.source_id == "SRC-USDA-FDC" and not self.fdc_id:
            raise ValueError("USDA FDC facts require fdc_id")
        if self.source_id == "SRC-USDA-FDC" and not self.source_data_type:
            raise ValueError("USDA FDC facts require data_type")

    @property
    def source_record_id_or_locator(self) -> str | None:
        return str(self.fdc_id) if self.fdc_id is not None else self.source_record_locator

    @property
    def obsolete_for_primary(self) -> bool:
        return (
            self.source_id in OBSOLETE_FOR_PRIMARY_SOURCE_IDS
            or self.source_data_type == "SR Legacy"
        )

    def contribution_for_grams(self, grams: float) -> float | None:
        if self.value is None:
            return None
        if self.basis_unit != "g" or self.basis_amount <= 0:
            return None
        return self.value * grams / self.basis_amount

    def to_record(self) -> dict:
        return {
            "canonical_food_key": self.canonical_food_key,
            "nutrient_key": self.nutrient_key,
            "value": self.value,
            "unit": self.unit,
            "basis_amount": self.basis_amount,
            "basis_unit": self.basis_unit,
            "source_id": self.source_id,
            "source_record_locator": self.source_record_locator,
            "source_record_id_or_locator": self.source_record_id_or_locator,
            "source_version": self.source_version,
            "source_data_type": self.source_data_type,
            "fdc_id": self.fdc_id,
            "food_state": self.food_state,
            "provenance_status": self.provenance_status,
            "source_food_name": self.source_food_name,
            "source_nutrient_id": self.source_nutrient_id,
            "source_nutrient_name": self.source_nutrient_name,
            "preparation_method": self.preparation_method,
            "match_method": self.match_method,
            "match_confidence": self.match_confidence,
            "review_status": self.review_status,
            "review_notes": self.review_notes,
            "retrieved_or_imported_at": self.retrieved_or_imported_at.isoformat(),
        }


@dataclass(frozen=True)
class FoodMatch:
    normalized_ingredient_name: str
    original_ingredient_text: str
    status: str
    canonical_food_key: str | None = None
    source_id: str | None = None
    source_record_locator: str | None = None
    source_food_name: str | None = None
    food_state: str = "unknown"
    match_method: str = "candidate_only"
    match_confidence: str = "none"
    brand: str | None = None
    review_reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in FOOD_MATCH_STATUSES:
            raise ValueError(f"unsupported food match status: {self.status}")
        if self.status == "matched":
            required = (
                self.canonical_food_key,
                self.source_id,
                self.source_record_locator,
                self.source_food_name,
                self.food_state,
                self.match_method,
                self.match_confidence,
            )
            if not all(required):
                raise ValueError("matched food requires canonical identity and provenance")
        if self.match_method == "candidate_only" and self.status == "matched":
            raise ValueError("candidate_only cannot be accepted as a verified match")

    def to_record(self) -> dict:
        return {
            "normalized_ingredient_name": self.normalized_ingredient_name,
            "original_ingredient_text": self.original_ingredient_text,
            "status": self.status,
            "canonical_food_key": self.canonical_food_key,
            "source_id": self.source_id,
            "source_record_locator": self.source_record_locator,
            "source_food_name": self.source_food_name,
            "food_state": self.food_state,
            "match_method": self.match_method,
            "match_confidence": self.match_confidence,
            "brand": self.brand,
            "review_reason": self.review_reason,
        }


@dataclass(frozen=True)
class ResolvedServings:
    servings: float | None
    source: str
    canonical_per_serving: bool


def resolve_servings_with_provenance(
    servings: int | float | None,
    meal_type: str,
    category: str,
) -> ResolvedServings:
    if servings and servings >= 1:
        return ResolvedServings(float(servings), "declared_servings", True)
    mt = (meal_type or "").strip().lower()
    cat = (category or "").strip().lower()
    if mt in {"breakfast", "snack", "drink", "cocktail", "smoothie", "tea", "coffee"}:
        return ResolvedServings(1.0, "legacy_unsourced_serving_estimate", False)
    if mt in {"lunch", "dinner"} or cat in {"soup", "main", "salad", "event", "bbq"}:
        return ResolvedServings(4.0, "legacy_unsourced_serving_estimate", False)
    return ResolvedServings(None, "unresolved", False)


def choose_preferred_fact_group(
    groups: list[list[FoodNutrientFact]],
) -> list[FoodNutrientFact] | None:
    if not groups:
        return None

    def rank(group: list[FoodNutrientFact]) -> tuple[int, int]:
        first = group[0]
        if first.source_id == "SRC-RU-FIC-FOODCOMP" and first.provenance_status in {
            "external_verified",
            "manual_reviewed",
        }:
            return (0, 0)
        if first.source_id == "SRC-USDA-FDC" and not first.obsolete_for_primary:
            return (1, 0)
        if first.provenance_status == "manual_reviewed":
            return (2, 0)
        if first.source_id == "SRC-PLANAM-V1-NUTRITION-FACTS":
            return (3, 0)
        if first.obsolete_for_primary:
            return (4, 0)
        return (5, 0)

    return sorted(groups, key=rank)[0]


def summarize_provenance(
    ingredient_records: list[dict],
    *,
    method: str,
    serving_resolution: ResolvedServings,
) -> dict:
    source_records: list[dict] = []
    source_versions: dict[str, list[str]] = {}
    source_kinds: set[str] = set()
    requires_review = False
    for row in ingredient_records:
        match = row.get("match") or {}
        if match.get("status") != "matched":
            requires_review = True
        for fact in row.get("facts") or []:
            source_id = fact.get("source_id")
            status = fact.get("provenance_status")
            if status:
                source_kinds.add(status)
            if source_id:
                locator = fact.get("source_record_id_or_locator")
                source_records.append(
                    {
                        "source_id": source_id,
                        "source_record_id_or_locator": locator,
                        "source_data_type": fact.get("source_data_type"),
                        "food_state": fact.get("food_state"),
                        "canonical_food_key": fact.get("canonical_food_key"),
                    }
                )
                version = fact.get("source_version")
                if version:
                    source_versions.setdefault(source_id, [])
                    if version not in source_versions[source_id]:
                        source_versions[source_id].append(version)
            if status in {"internal_legacy_unsourced", "unavailable"}:
                requires_review = True
    if not serving_resolution.canonical_per_serving:
        requires_review = True
    if not source_kinds:
        nutrition_source_kind = "unavailable"
    elif source_kinds == {"external_verified"}:
        nutrition_source_kind = "external_verified"
    elif "internal_legacy_unsourced" in source_kinds and len(source_kinds) == 1:
        nutrition_source_kind = "internal_legacy_unsourced"
    else:
        nutrition_source_kind = "mixed"
    return {
        "nutrition_source_kind": nutrition_source_kind,
        "nutrition_source_records": source_records,
        "nutrition_source_versions": source_versions,
        "nutrition_calculation_method": method,
        "serving_source": serving_resolution.source,
        "canonical_per_serving": serving_resolution.canonical_per_serving,
        "needs_review": requires_review,
    }
