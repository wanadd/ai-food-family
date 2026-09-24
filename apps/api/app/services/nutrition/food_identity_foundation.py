"""Deterministic food identity and unit normalization foundation.

This module creates dry-run plans only. It does not write ``FoodMatch`` rows,
does not attach nutrient facts, and does not generate allergen, gluten-free, or
medical safety facts.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Literal

from app.nutrition.allergen_ontology import ALLERGEN_CONCEPTS
from app.services.nutrition.recipe_nutrition_provenance import FoodMatch

NormalizationClass = Literal[
    "CANONICAL_CANDIDATE",
    "SYNONYM",
    "VARIANT",
    "TOO_GENERIC",
    "COMPOSITE",
    "PREPARATION_EMBEDDED",
    "BRAND_OR_PRODUCT",
    "AMBIGUOUS",
    "INVALID_OR_NOISE",
    "MANUAL_REVIEW",
]
UnitClass = Literal[
    "MASS_CONVERTIBLE",
    "VOLUME_CONVERTIBLE",
    "COUNT",
    "HOUSEHOLD_MEASURE",
    "QUALITATIVE",
    "UNKNOWN",
]
QuantityComputability = Literal[
    "EXACT_MASS_COMPUTABLE",
    "EXACT_VOLUME_COMPUTABLE",
    "COUNT_WITHOUT_MASS",
    "HOUSEHOLD_MEASURE_WITHOUT_CONVERSION",
    "QUALITATIVE_AMOUNT",
    "MISSING_QUANTITY",
    "UNKNOWN_UNIT",
]
MatchStatus = Literal["matched", "ambiguous", "unmatched", "manual_review_required"]
MatchMethod = Literal[
    "EXACT_CANONICAL",
    "EXACT_ALIAS",
    "NORMALIZED_ALIAS",
    "CURATED_MAPPING",
    "REVIEW_CANDIDATE",
    "UNMATCHED",
]
Confidence = Literal["EXACT", "HIGH", "REVIEW_REQUIRED", "UNMATCHED"]
Readiness = Literal[
    "READY_FOR_AUTHORITATIVE_MATCH",
    "NEEDS_DISAMBIGUATION",
    "NEEDS_RECIPE_AUTHORING_FIX",
    "NEEDS_PRODUCT_LABEL",
    "UNSUPPORTED",
]

MATCH_PROVENANCE = "planam_p0_data_foundation_01b1_curated_v1"

_PUNCT_RE = re.compile(r"[\"'«»“”„.,;:!?()\[\]{}]+")
_SPACE_RE = re.compile(r"\s+")

UNIT_ALIASES: dict[str, tuple[str, UnitClass, float | None]] = {
    "г": ("г", "MASS_CONVERTIBLE", 1.0),
    "гр": ("г", "MASS_CONVERTIBLE", 1.0),
    "гр.": ("г", "MASS_CONVERTIBLE", 1.0),
    "грамм": ("г", "MASS_CONVERTIBLE", 1.0),
    "грамма": ("г", "MASS_CONVERTIBLE", 1.0),
    "граммов": ("г", "MASS_CONVERTIBLE", 1.0),
    "кг": ("г", "MASS_CONVERTIBLE", 1000.0),
    "килограмм": ("г", "MASS_CONVERTIBLE", 1000.0),
    "килограмма": ("г", "MASS_CONVERTIBLE", 1000.0),
    "килограммов": ("г", "MASS_CONVERTIBLE", 1000.0),
    "мл": ("мл", "VOLUME_CONVERTIBLE", 1.0),
    "миллилитр": ("мл", "VOLUME_CONVERTIBLE", 1.0),
    "миллилитра": ("мл", "VOLUME_CONVERTIBLE", 1.0),
    "миллилитров": ("мл", "VOLUME_CONVERTIBLE", 1.0),
    "л": ("мл", "VOLUME_CONVERTIBLE", 1000.0),
    "литр": ("мл", "VOLUME_CONVERTIBLE", 1000.0),
    "литра": ("мл", "VOLUME_CONVERTIBLE", 1000.0),
    "литров": ("мл", "VOLUME_CONVERTIBLE", 1000.0),
    "шт": ("шт", "COUNT", None),
    "шт.": ("шт", "COUNT", None),
    "штука": ("шт", "COUNT", None),
    "штуки": ("шт", "COUNT", None),
    "штук": ("шт", "COUNT", None),
    "pc": ("шт", "COUNT", None),
    "pcs": ("шт", "COUNT", None),
    "ст.л.": ("ст.л.", "HOUSEHOLD_MEASURE", None),
    "ст. л.": ("ст.л.", "HOUSEHOLD_MEASURE", None),
    "ст л": ("ст.л.", "HOUSEHOLD_MEASURE", None),
    "стак.": ("стакан", "HOUSEHOLD_MEASURE", None),
    "стакан": ("стакан", "HOUSEHOLD_MEASURE", None),
    "ч.л.": ("ч.л.", "HOUSEHOLD_MEASURE", None),
    "ч. л.": ("ч.л.", "HOUSEHOLD_MEASURE", None),
    "ч л": ("ч.л.", "HOUSEHOLD_MEASURE", None),
    "зуб.": ("зубчик", "HOUSEHOLD_MEASURE", None),
    "зубчик": ("зубчик", "HOUSEHOLD_MEASURE", None),
    "пуч.": ("пучок", "HOUSEHOLD_MEASURE", None),
    "пучок": ("пучок", "HOUSEHOLD_MEASURE", None),
    "щепот.": ("щепотка", "QUALITATIVE", None),
    "щепотка": ("щепотка", "QUALITATIVE", None),
    "по вкусу": ("по вкусу", "QUALITATIVE", None),
    "немного": ("немного", "QUALITATIVE", None),
}

GENERIC_NAMES = {
    "лук",
    "перец",
    "сыр",
    "масло",
    "зелень",
    "специи",
    "фарш",
    "рыба",
    "мясо",
    "орехи",
    "мука",
    "соус",
    "приправа",
}
COMPOSITE_MARKERS = ("смесь", "набор", "ассорти", "овощи для", "смесь перцев")
PREPARATION_MARKERS = (
    "варен",
    "отвар",
    "жарен",
    "запеч",
    "копчен",
    "марин",
    "консерв",
    "солен",
    "заморож",
)
PRODUCT_MARKERS = ("колбас", "сосиск", "ветчина", "бекон", "крабовые палочки", "майонез")

CANONICAL_FOODS: dict[str, dict[str, str]] = {
    "рис": {"canonical_food_key": "rice", "source_food_name": "рис", "food_state": "raw"},
    "гречка": {"canonical_food_key": "buckwheat_groats", "source_food_name": "крупа гречневая", "food_state": "raw"},
    "крупа гречневая": {"canonical_food_key": "buckwheat_groats", "source_food_name": "крупа гречневая", "food_state": "raw"},
    "овсяные хлопья": {"canonical_food_key": "oat_flakes", "source_food_name": "хлопья овсяные", "food_state": "raw"},
    "хлопья овсяные": {"canonical_food_key": "oat_flakes", "source_food_name": "хлопья овсяные", "food_state": "raw"},
    "молоко": {"canonical_food_key": "milk", "source_food_name": "молоко", "food_state": "unknown"},
    "яйцо": {"canonical_food_key": "chicken_egg", "source_food_name": "яйцо куриное", "food_state": "raw"},
    "яйца": {"canonical_food_key": "chicken_egg", "source_food_name": "яйцо куриное", "food_state": "raw"},
    "яйцо куриное": {"canonical_food_key": "chicken_egg", "source_food_name": "яйцо куриное", "food_state": "raw"},
    "куриное филе": {"canonical_food_key": "chicken_fillet", "source_food_name": "филе куриное", "food_state": "raw"},
    "филе куриное": {"canonical_food_key": "chicken_fillet", "source_food_name": "филе куриное", "food_state": "raw"},
    "морковь": {"canonical_food_key": "carrot", "source_food_name": "морковь", "food_state": "raw"},
    "картофель": {"canonical_food_key": "potato", "source_food_name": "картофель", "food_state": "raw"},
    "лук репчатый": {"canonical_food_key": "onion", "source_food_name": "лук репчатый", "food_state": "raw"},
    "чеснок": {"canonical_food_key": "garlic", "source_food_name": "чеснок", "food_state": "raw"},
    "помидор": {"canonical_food_key": "tomato", "source_food_name": "помидор", "food_state": "raw"},
    "помидоры": {"canonical_food_key": "tomato", "source_food_name": "помидор", "food_state": "raw"},
    "огурец": {"canonical_food_key": "cucumber", "source_food_name": "огурец", "food_state": "raw"},
    "банан": {"canonical_food_key": "banana", "source_food_name": "банан", "food_state": "raw"},
    "яблоко": {"canonical_food_key": "apple", "source_food_name": "яблоко", "food_state": "raw"},
    "лимон": {"canonical_food_key": "lemon", "source_food_name": "лимон", "food_state": "raw"},
    "творог": {"canonical_food_key": "cottage_cheese", "source_food_name": "творог", "food_state": "unknown"},
    "сметана": {"canonical_food_key": "sour_cream", "source_food_name": "сметана", "food_state": "unknown"},
    "йогурт": {"canonical_food_key": "yogurt", "source_food_name": "йогурт", "food_state": "unknown"},
    "масло оливковое": {"canonical_food_key": "olive_oil", "source_food_name": "масло оливковое", "food_state": "unknown"},
    "оливковое масло": {"canonical_food_key": "olive_oil", "source_food_name": "масло оливковое", "food_state": "unknown"},
    "масло сливочное": {"canonical_food_key": "butter", "source_food_name": "масло сливочное", "food_state": "unknown"},
    "сахар": {"canonical_food_key": "sugar", "source_food_name": "сахар", "food_state": "unknown"},
    "соль": {"canonical_food_key": "salt", "source_food_name": "соль", "food_state": "unknown"},
    "укроп": {"canonical_food_key": "dill", "source_food_name": "укроп", "food_state": "raw"},
    "петрушка": {"canonical_food_key": "parsley", "source_food_name": "петрушка", "food_state": "raw"},
    "шпинат": {"canonical_food_key": "spinach", "source_food_name": "шпинат", "food_state": "raw"},
    "треска": {"canonical_food_key": "cod", "source_food_name": "треска", "food_state": "raw"},
    "креветки": {"canonical_food_key": "shrimp", "source_food_name": "креветки", "food_state": "raw"},
    "арахис": {"canonical_food_key": "peanut", "source_food_name": "арахис", "food_state": "raw"},
    "тофу": {"canonical_food_key": "tofu", "source_food_name": "тофу", "food_state": "unknown"},
}

ALIASES: dict[str, str] = {
    "овсянка": "овсяные хлопья",
    "рис белый": "рис",
    "курица": "куриное филе",
    "куриная грудка": "куриное филе",
    "филе трески": "треска",
    "масло растительное": "масло оливковое",
    "мед": "мёд",
    "мёд": "мед",
}

SAFETY_SENSITIVE_MARKERS: dict[str, tuple[str, ...]] = {
    "milk_dairy": ("молоко", "сыр", "творог", "йогурт", "сметана", "сливки", "масло сливочное"),
    "nuts_peanut": ("орех", "арахис", "миндаль", "фундук", "кешью"),
    "fish_shellfish": ("рыба", "треска", "лосось", "тунец", "кревет", "краб", "мидии", "кальмар"),
    "egg": ("яйцо", "яйца"),
    "soy": ("соя", "соев", "тофу"),
    "gluten_grain": ("пшениц", "мука", "хлеб", "макарон", "паста", "лаваш", "перлов", "ячмен", "рожь"),
    "mixed_or_processed": ("соус", "колбас", "сосиск", "ветчина", "бекон", "крабовые палочки", "смесь", "специи", "приправа"),
}


@dataclass(frozen=True)
class NormalizedUnit:
    raw_unit: str | None
    canonical_unit: str | None
    unit_class: UnitClass
    multiplier_to_canonical: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_unit": self.raw_unit,
            "canonical_unit": self.canonical_unit,
            "unit_class": self.unit_class,
            "multiplier_to_canonical": self.multiplier_to_canonical,
        }


@dataclass(frozen=True)
class QuantityPlan:
    quantity: str | None
    unit: NormalizedUnit
    computability: QuantityComputability
    canonical_amount: float | None = None
    canonical_unit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "quantity": self.quantity,
            "unit": self.unit.to_dict(),
            "computability": self.computability,
            "canonical_amount": self.canonical_amount,
            "canonical_unit": self.canonical_unit,
        }


def normalize_ingredient_name(value: str | None) -> str:
    text = str(value or "").casefold().replace("ё", "е").strip()
    text = _PUNCT_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def normalize_unit_for_nutrition(value: str | None) -> NormalizedUnit:
    raw = (value or "").strip()
    key = raw.casefold()
    if not key:
        return NormalizedUnit(raw, None, "UNKNOWN", None)
    if key in UNIT_ALIASES:
        canon, unit_class, multiplier = UNIT_ALIASES[key]
        return NormalizedUnit(raw, canon, unit_class, multiplier)
    return NormalizedUnit(raw, key, "UNKNOWN", None)


def _parse_quantity(value: str | None) -> float | None:
    text = str(value or "").strip().replace(",", ".")
    if not text:
        return None
    if "/" in text:
        parts = text.split("/", 1)
        try:
            return float(parts[0]) / float(parts[1])
        except Exception:
            return None
    try:
        return float(text)
    except Exception:
        return None


def classify_quantity(quantity: str | None, unit: str | None) -> QuantityPlan:
    unit_plan = normalize_unit_for_nutrition(unit)
    raw_quantity = str(quantity or "").strip()
    if not raw_quantity:
        return QuantityPlan(quantity, unit_plan, "MISSING_QUANTITY")
    if raw_quantity.casefold() in {"по вкусу", "немного"}:
        return QuantityPlan(quantity, unit_plan, "QUALITATIVE_AMOUNT")
    amount = _parse_quantity(raw_quantity)
    if amount is None:
        return QuantityPlan(quantity, unit_plan, "MISSING_QUANTITY")
    if unit_plan.unit_class == "MASS_CONVERTIBLE" and unit_plan.multiplier_to_canonical:
        return QuantityPlan(
            quantity,
            unit_plan,
            "EXACT_MASS_COMPUTABLE",
            amount * unit_plan.multiplier_to_canonical,
            unit_plan.canonical_unit,
        )
    if unit_plan.unit_class == "VOLUME_CONVERTIBLE" and unit_plan.multiplier_to_canonical:
        return QuantityPlan(
            quantity,
            unit_plan,
            "EXACT_VOLUME_COMPUTABLE",
            amount * unit_plan.multiplier_to_canonical,
            unit_plan.canonical_unit,
        )
    if unit_plan.unit_class == "COUNT":
        return QuantityPlan(quantity, unit_plan, "COUNT_WITHOUT_MASS")
    if unit_plan.unit_class == "HOUSEHOLD_MEASURE":
        return QuantityPlan(quantity, unit_plan, "HOUSEHOLD_MEASURE_WITHOUT_CONVERSION")
    if unit_plan.unit_class == "QUALITATIVE":
        return QuantityPlan(quantity, unit_plan, "QUALITATIVE_AMOUNT")
    return QuantityPlan(quantity, unit_plan, "UNKNOWN_UNIT")


def classify_normalized_ingredient(name: str) -> NormalizationClass:
    normalized = normalize_ingredient_name(name)
    if not normalized:
        return "INVALID_OR_NOISE"
    if normalized in GENERIC_NAMES:
        return "TOO_GENERIC"
    if any(marker in normalized for marker in COMPOSITE_MARKERS):
        return "COMPOSITE"
    if any(marker in normalized for marker in PRODUCT_MARKERS):
        return "BRAND_OR_PRODUCT"
    if any(marker in normalized for marker in PREPARATION_MARKERS):
        return "PREPARATION_EMBEDDED"
    if normalized in ALIASES:
        return "SYNONYM"
    if normalized in CANONICAL_FOODS:
        return "CANONICAL_CANDIDATE"
    if len(normalized.split()) >= 4:
        return "MANUAL_REVIEW"
    return "VARIANT"


def safety_sensitive_flags(name: str) -> tuple[str, ...]:
    normalized = normalize_ingredient_name(name)
    flags = [
        flag
        for flag, markers in SAFETY_SENSITIVE_MARKERS.items()
        if any(marker in normalized for marker in markers)
    ]
    if normalized in ALLERGEN_CONCEPTS:
        flags.append("implemented_allergen_concept")
    return tuple(sorted(set(flags)))


def dry_run_food_match(raw_name: str, *, fuzzy_candidate: str | None = None) -> FoodMatch:
    normalized = normalize_ingredient_name(raw_name)
    if normalized in GENERIC_NAMES:
        return FoodMatch(
            normalized_ingredient_name=normalized,
            original_ingredient_text=raw_name,
            status="ambiguous",
            match_method="candidate_only",
            match_confidence="REVIEW_REQUIRED",
            review_reason="generic_ingredient_requires_disambiguation",
        )
    if normalized in CANONICAL_FOODS:
        food = CANONICAL_FOODS[normalized]
        return FoodMatch(
            normalized_ingredient_name=normalized,
            original_ingredient_text=raw_name,
            status="matched",
            canonical_food_key=food["canonical_food_key"],
            source_id="SRC-PLANAM-FOOD-IDENTITY-CURATED",
            source_record_locator=f"{MATCH_PROVENANCE}:{food['canonical_food_key']}",
            source_food_name=food["source_food_name"],
            food_state=food["food_state"],
            match_method="EXACT_CANONICAL",
            match_confidence="EXACT",
        )
    alias_target = ALIASES.get(normalized)
    if alias_target and alias_target in CANONICAL_FOODS:
        food = CANONICAL_FOODS[alias_target]
        return FoodMatch(
            normalized_ingredient_name=normalized,
            original_ingredient_text=raw_name,
            status="matched",
            canonical_food_key=food["canonical_food_key"],
            source_id="SRC-PLANAM-FOOD-IDENTITY-CURATED",
            source_record_locator=f"{MATCH_PROVENANCE}:{normalized}->{food['canonical_food_key']}",
            source_food_name=food["source_food_name"],
            food_state=food["food_state"],
            match_method="EXACT_ALIAS",
            match_confidence="HIGH",
        )
    if fuzzy_candidate:
        return FoodMatch(
            normalized_ingredient_name=normalized,
            original_ingredient_text=raw_name,
            status="manual_review_required",
            canonical_food_key=None,
            match_method="REVIEW_CANDIDATE",
            match_confidence="REVIEW_REQUIRED",
            review_reason=f"fuzzy_candidate_not_verified:{fuzzy_candidate}",
        )
    return FoodMatch(
        normalized_ingredient_name=normalized,
        original_ingredient_text=raw_name,
        status="unmatched",
        match_method="UNMATCHED",
        match_confidence="UNMATCHED",
        review_reason="no_deterministic_mapping",
    )


def authoritative_match_readiness(name: str, match: FoodMatch) -> Readiness:
    normalized = normalize_ingredient_name(name)
    if match.status == "matched" and match.canonical_food_key:
        if safety_sensitive_flags(normalized) and match.food_state == "unknown":
            return "NEEDS_PRODUCT_LABEL"
        return "READY_FOR_AUTHORITATIVE_MATCH"
    if match.status == "ambiguous":
        return "NEEDS_DISAMBIGUATION"
    if classify_normalized_ingredient(normalized) in {"PREPARATION_EMBEDDED", "COMPOSITE"}:
        return "NEEDS_RECIPE_AUTHORING_FIX"
    if classify_normalized_ingredient(normalized) == "BRAND_OR_PRODUCT":
        return "NEEDS_PRODUCT_LABEL"
    return "UNSUPPORTED"


def match_plan_record(name: str, *, affected_recipe_count: int = 0, affected_row_count: int = 0) -> dict[str, Any]:
    match = dry_run_food_match(name)
    flags = safety_sensitive_flags(name)
    return {
        "normalized_ingredient": normalize_ingredient_name(name),
        "candidate_canonical_food": match.canonical_food_key,
        "match_status": match.status,
        "match_method": match.match_method,
        "confidence": match.match_confidence,
        "reason": match.review_reason or "deterministic_curated_mapping",
        "manual_review_required": match.status != "matched" or bool(flags),
        "safety_sensitive_flags": list(flags),
        "authoritative_match_readiness": authoritative_match_readiness(name, match),
        "affected_recipe_count": affected_recipe_count,
        "affected_ingredient_row_count": affected_row_count,
        "food_match": match.to_record(),
    }
