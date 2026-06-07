#!/usr/bin/env python3
"""Recipe-level nutrition summary calculator (pure, no DB).

Aggregates per-ingredient KБЖУ (from nutrition_data.py) into a recipe summary
with an honest confidence label. Implements the PLANAM nutrition principle:

* exact quantities + facts -> show confidently;
* approximate -> mark "примерно";
* not enough data -> "требует уточнения", never invent numbers.

Used by backend/scripts/calculate_recipe_nutrition_summary.py.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from canonical_products import resolve_product  # noqa: E402
from nutrition_data import compute_row_nutrition  # noqa: E402

NUTRITION_SOURCE = "planam_v1_nutrition_facts"
DEFAULT_SERVING_SIZE_TEXT = "1 порция"

# meal_type / category -> safe fallback servings when recipe.servings is missing.
SINGLE_SERVING_MEALS = {"breakfast", "snack", "drink", "cocktail", "smoothie", "tea", "coffee"}
MULTI_SERVING_MEALS = {"lunch", "dinner"}
MULTI_SERVING_CATEGORIES = {"soup", "main", "salad", "event", "bbq"}


def resolve_servings(servings: int | float | None, meal_type: str, category: str) -> float | None:
    """Use recipe.servings when present; otherwise a conservative fallback or None."""
    if servings and servings >= 1:
        return float(servings)
    mt = (meal_type or "").strip().lower()
    cat = (category or "").strip().lower()
    if mt in SINGLE_SERVING_MEALS:
        return 1.0
    if mt in MULTI_SERVING_MEALS or cat in MULTI_SERVING_CATEGORIES:
        return 4.0
    return None  # do not invent portions


def _round(value: float, digits: int = 1) -> float:
    return round(float(value), digits)


def classify_confidence(coverage: float, counts: dict) -> str:
    used = counts["used_ingredients"]
    countable = counts["countable_ingredients"]
    exact = counts["exact_ingredients"]
    unavailable = counts["unavailable_ingredients"]
    if countable == 0 or used == 0:
        return "unavailable"
    if coverage < 0.40:
        return "unavailable"
    exact_share = exact / used if used else 0.0
    if coverage >= 0.90 and unavailable == 0 and exact_share >= 0.5:
        return "exact"
    if coverage >= 0.70 and unavailable <= 1:
        return "estimated"
    return "low_confidence"


def _review_reason(confidence: str, coverage: float, counts: dict) -> str | None:
    if confidence == "unavailable":
        return "insufficient_data"
    if coverage < 0.70:
        return "low_coverage"
    if counts["unavailable_ingredients"] > 0:
        return "unavailable_ingredient"
    if counts["needs_review_ingredients"] > 0:
        return "needs_review_ingredients"
    return None


@dataclass
class RecipeNutritionSummary:
    recipe_id: int
    title: str
    total: dict | None
    per_serving: dict | None
    servings: float | None
    serving_size_text: str | None
    confidence: str
    coverage: dict
    needs_review: bool
    review_reason: str | None
    source: str = NUTRITION_SOURCE

    def to_dict(self) -> dict:
        return {
            "recipe_id": self.recipe_id,
            "title": self.title,
            "total": self.total,
            "per_serving": self.per_serving,
            "servings": self.servings,
            "serving_size_text": self.serving_size_text,
            "confidence": self.confidence,
            "coverage": self.coverage,
            "needs_review": self.needs_review,
            "review_reason": self.review_reason,
            "source": self.source,
        }


def calculate_recipe_nutrition(
    *,
    recipe_id: int,
    title: str,
    servings: int | float | None,
    meal_type: str,
    category: str,
    ingredients: list[dict],
) -> RecipeNutritionSummary:
    """Aggregate ingredient KБЖУ into a recipe summary.

    Each ingredient dict: {name, quantity, unit, category, is_to_taste, needs_review}.
    """
    totals = {"kcal": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    counts = {
        "total_ingredients": 0,
        "used_ingredients": 0,
        "exact_ingredients": 0,
        "estimated_ingredients": 0,
        "low_confidence_ingredients": 0,
        "unavailable_ingredients": 0,
        "to_taste_ingredients": 0,
        "needs_review_ingredients": 0,
        "generic_ingredients": 0,
    }

    for ing in ingredients:
        counts["total_ingredients"] += 1
        name = ing.get("name", "")
        is_to_taste = bool(ing.get("is_to_taste"))
        needs_review = bool(ing.get("needs_review"))
        generic = resolve_product(name).generic
        if is_to_taste:
            counts["to_taste_ingredients"] += 1
        if needs_review:
            counts["needs_review_ingredients"] += 1
        if generic:
            counts["generic_ingredients"] += 1

        rn = compute_row_nutrition(
            name,
            ing.get("quantity", ""),
            ing.get("unit", ""),
            category=ing.get("category", "other"),
            generic=generic,
            is_to_taste=is_to_taste,
        )
        counts[f"{rn.precision}_ingredients"] += 1
        if rn.grams is not None:
            counts["used_ingredients"] += 1
            totals["kcal"] += rn.kcal
            totals["protein"] += rn.protein
            totals["fat"] += rn.fat
            totals["carbs"] += rn.carbs

    countable = counts["total_ingredients"] - counts["to_taste_ingredients"]
    counts["countable_ingredients"] = countable
    coverage_pct = counts["used_ingredients"] / countable if countable else 0.0
    counts["coverage_pct"] = _round(coverage_pct * 100, 1)

    confidence = classify_confidence(coverage_pct, counts)
    review_reason = _review_reason(confidence, coverage_pct, counts)
    needs_review = confidence in {"low_confidence", "unavailable"}

    resolved_servings = resolve_servings(servings, meal_type, category)

    if confidence == "unavailable":
        # Not enough data — never surface invented numbers.
        return RecipeNutritionSummary(
            recipe_id=recipe_id,
            title=title,
            total=None,
            per_serving=None,
            servings=resolved_servings,
            serving_size_text=DEFAULT_SERVING_SIZE_TEXT if resolved_servings else None,
            confidence=confidence,
            coverage=counts,
            needs_review=True,
            review_reason=review_reason,
        )

    total = {k: _round(v) for k, v in totals.items()}
    per_serving = None
    serving_size_text = None
    if resolved_servings and resolved_servings >= 1:
        per_serving = {k: _round(v / resolved_servings) for k, v in totals.items()}
        serving_size_text = DEFAULT_SERVING_SIZE_TEXT

    return RecipeNutritionSummary(
        recipe_id=recipe_id,
        title=title,
        total=total,
        per_serving=per_serving,
        servings=resolved_servings,
        serving_size_text=serving_size_text,
        confidence=confidence,
        coverage=counts,
        needs_review=needs_review,
        review_reason=review_reason,
    )
