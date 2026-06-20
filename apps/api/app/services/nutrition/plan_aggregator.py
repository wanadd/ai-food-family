"""Aggregate recipe-level nutrition into day / week menu summaries.

Reads the already-computed recipes.nutrition_* fields (see
calculate_recipe_nutrition_summary.py) and the selected menu JSON. Pure
aggregation core (no DB) + thin DB-facing helpers, so it's easy to test.

Honest-by-design:
* `unavailable` recipes are NOT counted as 0 — they lower coverage instead;
* `low_confidence` recipes DO contribute to totals but lower the day confidence;
* per-person daily intake uses **1 serving per planned meal** by default (the
  menu item `servings` is a cooking quantity, not a per-person multiplier).
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.progress import NutritionTarget
from app.models.recipe import Recipe
from app.services.app_scope import AppScope

MACROS = ("kcal", "protein", "fat", "carbs")
MEAL_GROUPS = ("breakfast", "lunch", "dinner", "snack")
USABLE_CONFIDENCE = {"exact", "estimated", "low_confidence"}

# Fallback target when the user has no nutrition_targets row (NOT persisted).
FALLBACK_TARGETS: dict[str, int | None] = {
    "kcal": 2200,
    "protein": None,
    "fat": None,
    "carbs": None,
}


# --------------------------- pure aggregation core ---------------------------

def _empty_macros() -> dict[str, float]:
    return {k: 0.0 for k in MACROS}


def _round_macros(macros: dict[str, float]) -> dict[str, int]:
    return {k: int(round(macros.get(k, 0.0))) for k in MACROS}


def _item_contribution(recipe_nut: dict, multiplier: float) -> dict[str, float]:
    return {
        "kcal": (recipe_nut.get("kcal_per_serving") or 0.0) * multiplier,
        "protein": (recipe_nut.get("protein_per_serving") or 0.0) * multiplier,
        "fat": (recipe_nut.get("fat_per_serving") or 0.0) * multiplier,
        "carbs": (recipe_nut.get("carbs_per_serving") or 0.0) * multiplier,
    }


def classify_period(counts: dict) -> str:
    """exact / estimated / low_confidence / unavailable for a day or week."""
    total = counts.get("total_items", 0)
    if total == 0:
        return "unavailable"
    calc = counts.get("calculated_items", 0)
    if calc == 0:
        return "unavailable"
    coverage = calc / total
    if coverage < 0.40:
        return "unavailable"
    exact = counts.get("exact_items", 0)
    low = counts.get("low_confidence_items", 0)
    unavailable = counts.get("unavailable_items", 0)
    exact_share = exact / calc
    low_share = low / calc
    if coverage >= 0.90 and unavailable == 0 and exact_share >= 0.8:
        return "exact"
    if coverage >= 0.70 and unavailable <= 1 and low_share <= 0.5:
        return "estimated"
    return "low_confidence"


def _coverage_pct(counts: dict) -> int:
    total = counts.get("total_items", 0)
    if not total:
        return 0
    return int(round(counts.get("calculated_items", 0) / total * 100))


def _build_warnings(confidence: str, counts: dict) -> list[str]:
    warnings: list[str] = []
    if counts.get("total_items", 0) == 0:
        return warnings  # empty state handled by UI
    unavailable = counts.get("unavailable_items", 0)
    if unavailable > 0:
        warnings.append(f"{unavailable} рецептов без точного КБЖУ")
    if confidence == "estimated":
        warnings.append("часть данных рассчитана приблизительно")
    elif confidence == "low_confidence":
        warnings.append("часть рецептов требует уточнения — КБЖУ рассчитаны приблизительно")
    elif confidence == "unavailable":
        warnings.append("недостаточно данных для расчёта КБЖУ")
    return warnings


def _progress(totals: dict[str, float], targets: dict[str, int | None]) -> dict[str, int | None]:
    progress: dict[str, int | None] = {}
    for key in MACROS:
        target = targets.get(key)
        if target and target > 0:
            progress[f"{key}_pct"] = int(round(totals.get(key, 0.0) / target * 100))
        else:
            progress[f"{key}_pct"] = None
    return progress


def aggregate_day(
    date_iso: str,
    items: list[dict],
    recipe_map: dict[int, dict],
    targets: dict[str, int | None],
) -> dict:
    """Aggregate one day's menu items into a nutrition summary dict.

    item: {recipe_id, meal_type, name, serving_multiplier?}
    recipe_map: recipe_id -> {kcal_per_serving, protein_per_serving, fat_per_serving,
                              carbs_per_serving, confidence}
    """
    totals = _empty_macros()
    counts = {
        "total_items": 0,
        "calculated_items": 0,
        "exact_items": 0,
        "estimated_items": 0,
        "low_confidence_items": 0,
        "unavailable_items": 0,
    }
    meal_blocks: dict[str, dict] = {}

    for item in items:
        counts["total_items"] += 1
        meal_type = item.get("meal_type") or "other"
        group = meal_type if meal_type in MEAL_GROUPS else "other"
        block = meal_blocks.setdefault(
            group,
            {"meal_type": group, "totals": _empty_macros(), "items": [],
             "_counts": dict(counts, total_items=0)},
        )

        recipe_id = item.get("recipe_id")
        recipe_nut = recipe_map.get(recipe_id) if recipe_id is not None else None
        confidence = recipe_nut.get("confidence") if recipe_nut else None
        kcal_ps = recipe_nut.get("kcal_per_serving") if recipe_nut else None
        usable = (
            recipe_nut is not None
            and confidence in USABLE_CONFIDENCE
            and kcal_ps is not None
        )
        multiplier = float(item.get("serving_multiplier") or 1.0)

        item_kcal: float | None = None
        if usable:
            counts["calculated_items"] += 1
            counts[f"{confidence}_items"] += 1
            contrib = _item_contribution(recipe_nut, multiplier)
            item_kcal = contrib["kcal"]
            for k in MACROS:
                totals[k] += contrib[k]
                block["totals"][k] += contrib[k]
        else:
            counts["unavailable_items"] += 1

        block["items"].append(
            {
                "recipe_id": recipe_id,
                "name": item.get("name", ""),
                "kcal": int(round(item_kcal)) if item_kcal is not None else None,
                "confidence": confidence,
            }
        )

    confidence = classify_period(counts)
    ordered_meals = [
        {
            "meal_type": meal_blocks[g]["meal_type"],
            "totals": _round_macros(meal_blocks[g]["totals"]),
            "items": meal_blocks[g]["items"],
        }
        for g in (*MEAL_GROUPS, "other")
        if g in meal_blocks
    ]

    return {
        "date": date_iso,
        "totals": _round_macros(totals),
        "targets": dict(targets),
        "progress": _progress(totals, targets),
        "confidence": confidence,
        "coverage": {**counts, "coverage_pct": _coverage_pct(counts)},
        "meals": ordered_meals,
        "warnings": _build_warnings(confidence, counts),
    }


def aggregate_week(start_iso: str, end_iso: str, day_results: list[dict]) -> dict:
    """Combine per-day results (already aggregated) into a week summary."""
    weekly_total = _empty_macros()
    combined = {
        "total_items": 0,
        "calculated_items": 0,
        "exact_items": 0,
        "estimated_items": 0,
        "low_confidence_items": 0,
        "unavailable_items": 0,
    }
    days_with_data = 0
    days_with_full_calc = 0
    for day in day_results:
        for k in MACROS:
            weekly_total[k] += day["totals"].get(k, 0)
        cov = day["coverage"]
        for key in combined:
            combined[key] += cov.get(key, 0)
        if cov.get("calculated_items", 0) > 0:
            days_with_data += 1
        if day["confidence"] in {"exact", "estimated"}:
            days_with_full_calc += 1

    weekly_average = (
        {k: int(round(weekly_total[k] / days_with_data)) for k in MACROS}
        if days_with_data
        else _round_macros(weekly_total)
    )
    confidence = classify_period(combined)
    warnings: list[str] = []
    low_conf_days = len(day_results) - days_with_full_calc
    if low_conf_days > 0 and day_results:
        warnings.append(f"{low_conf_days} дней рассчитаны приблизительно")
    if combined["unavailable_items"] > 0:
        warnings.append("часть рецептов без точного КБЖУ")

    return {
        "start_date": start_iso,
        "end_date": end_iso,
        "days": day_results,
        "weekly_total": _round_macros(weekly_total),
        "weekly_average": weekly_average,
        "days_with_full_calc": days_with_full_calc,
        "confidence": confidence,
        "warnings": warnings,
    }


# --------------------------- DB-facing helpers ---------------------------

def recipe_nutrition_map(db: Session, recipe_ids: list[int]) -> dict[int, dict]:
    if not recipe_ids:
        return {}
    rows = (
        db.query(
            Recipe.id,
            Recipe.nutrition_kcal_per_serving,
            Recipe.nutrition_protein_per_serving,
            Recipe.nutrition_fat_per_serving,
            Recipe.nutrition_carbs_per_serving,
            Recipe.nutrition_confidence,
        )
        .filter(Recipe.id.in_(set(recipe_ids)))
        .all()
    )
    return {
        row.id: {
            "kcal_per_serving": row.nutrition_kcal_per_serving,
            "protein_per_serving": row.nutrition_protein_per_serving,
            "fat_per_serving": row.nutrition_fat_per_serving,
            "carbs_per_serving": row.nutrition_carbs_per_serving,
            "confidence": row.nutrition_confidence,
        }
        for row in rows
    }


def resolve_targets(db: Session, user_id: int) -> dict[str, int | None]:
    """Read-only goal resolver — never writes a default into the DB."""
    row = (
        db.query(NutritionTarget)
        .filter(NutritionTarget.user_id == user_id)
        .order_by(NutritionTarget.updated_at.desc())
        .first()
    )
    if row is None:
        return dict(FALLBACK_TARGETS)
    return {
        "kcal": row.calories_target,
        "protein": row.protein_target_g,
        "fat": row.fat_target_g,
        "carbs": row.carbs_target_g,
    }


def _menu_items_for_date(db: Session, scope: AppScope, plan_date_iso: str) -> tuple[str, list[dict]]:
    from app.services.menu_recipe_plan import get_plan_for_date  # avoid cycle

    date_iso, items, _menu = get_plan_for_date(db, scope, plan_date=plan_date_iso)
    agg_items = [
        {
            "recipe_id": it.get("recipe_id"),
            "meal_type": it.get("meal_type"),
            "name": it.get("name", ""),
            "serving_multiplier": 1.0,  # one portion per planned meal (per person)
        }
        for it in items
        if it.get("recipe_id") is not None
    ]
    return date_iso, agg_items


def build_day_nutrition(
    db: Session, user_id: int, scope: AppScope, plan_date: str | None
) -> dict:
    target_iso = plan_date or date.today().isoformat()
    date_iso, items = _menu_items_for_date(db, scope, target_iso)
    recipe_ids = [it["recipe_id"] for it in items if it["recipe_id"] is not None]
    rmap = recipe_nutrition_map(db, recipe_ids)
    targets = resolve_targets(db, user_id)
    return aggregate_day(date_iso, items, rmap, targets)


def build_week_nutrition(
    db: Session, user_id: int, scope: AppScope, start_date: str | None
) -> dict:
    start = date.fromisoformat(start_date) if start_date else date.today()
    end = start + timedelta(days=6)
    day_results: list[dict] = []
    # Resolve targets/recipe maps once where possible.
    all_items: list[tuple[str, list[dict]]] = []
    recipe_ids: set[int] = set()
    for i in range(7):
        d_iso = (start + timedelta(days=i)).isoformat()
        date_iso, items = _menu_items_for_date(db, scope, d_iso)
        all_items.append((date_iso, items))
        recipe_ids.update(it["recipe_id"] for it in items if it["recipe_id"] is not None)
    rmap = recipe_nutrition_map(db, list(recipe_ids))
    targets = resolve_targets(db, user_id)
    for date_iso, items in all_items:
        day_results.append(aggregate_day(date_iso, items, rmap, targets))
    return aggregate_week(start.isoformat(), end.isoformat(), day_results)


def shape_nutrition_context(day: dict, week: dict) -> dict:
    """Pure: turn a day + week summary into the nutritionist context dict."""
    targets = day["targets"]
    deltas: dict[str, dict] = {}
    for key in MACROS:
        target = targets.get(key)
        actual = day["totals"].get(key, 0)
        if target and target > 0:
            diff = actual - target
            deltas[key] = {
                "target": target,
                "actual": actual,
                "diff": diff,
                "status": "deficit" if diff < 0 else ("excess" if diff > 0 else "on_target"),
            }

    top_low: list[dict] = []
    for meal in day["meals"]:
        for it in meal["items"]:
            if it["confidence"] in {"low_confidence", "unavailable", None}:
                top_low.append(
                    {"recipe_id": it["recipe_id"], "name": it["name"],
                     "confidence": it["confidence"] or "unavailable"}
                )

    return {
        "date": day["date"],
        "day_totals": day["totals"],
        "week_average": week["weekly_average"],
        "goals": targets,
        "deltas": deltas,
        "confidence": day["confidence"],
        "week_confidence": week["confidence"],
        "warnings": day["warnings"],
        "top_low_confidence_recipes": top_low[:10],
    }


def get_user_nutrition_context(
    db: Session,
    user_id: int,
    scope: AppScope,
    *,
    on_date: str | None = None,
    week_start: str | None = None,
) -> dict:
    """Prepared nutrition context for the AI nutritionist (no LLM here)."""
    day = build_day_nutrition(db, user_id, scope, on_date)
    week = build_week_nutrition(db, user_id, scope, week_start or day["date"])
    return shape_nutrition_context(day, week)
