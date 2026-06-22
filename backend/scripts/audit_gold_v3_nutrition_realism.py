"""Read-only nutrition realism audit for 40 Gold V3 recipes."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(os.environ.get("PLANAM_ROOT") or Path(__file__).resolve().parents[2])
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_gold_v3_post_apply_common import (  # noqa: E402
    fetch_recipe_rows,
    import_sqlalchemy,
    now,
    redact_url,
    write_json,
)


REPORT_JSON = ROOT / "reports" / "SPRINT_1_6_NUTRITION_REALISM_AUDIT.json"
REPORT_MD = ROOT / "reports" / "SPRINT_1_6_NUTRITION_REALISM_AUDIT.md"
PLAN_MD = ROOT / "reports" / "SPRINT_1_6_NUTRITION_CORRECTION_PLAN.md"
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
UPGRADED_IDS = [2, *range(227, 256)]
PILOT_IDS = list(range(256, 266))
GOLD_V3_IDS = [*UPGRADED_IDS, *PILOT_IDS]

SALAD_PROTEIN_WORDS = ("салат", "тунец", "индейк", "куриц", "рыб", "лосось", "кревет")
GRAIN_WORDS = ("паста", "рис", "греч", "перлов", "булгур", "овсян", "лапша", "макарон")
OMELET_WORDS = ("омлет", "яйц")
SOUP_WORDS = ("суп", "борщ", "похлеб")
STEW_WORDS = ("туш", "рагу")
SNACK_WORDS = ("перекус", "смузи", "боул", "батончик", "десерт")


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def nutrition_for(row: dict[str, Any]) -> dict[str, float | None]:
    return {
        "kcal": _num(row.get("nutrition_kcal_per_serving")) or _num(row.get("calories_per_serving")),
        "protein": _num(row.get("nutrition_protein_per_serving")) or _num(row.get("protein_g")),
        "fat": _num(row.get("nutrition_fat_per_serving")) or _num(row.get("fat_g")),
        "carbs": _num(row.get("nutrition_carbs_per_serving")) or _num(row.get("carbs_g")),
    }


def serving_count_for(row: dict[str, Any]) -> float | None:
    return _num(row.get("nutrition_servings")) or _num(row.get("estimated_servings")) or _num(row.get("servings"))


def text_blob(row: dict[str, Any], ingredients: list[dict[str, Any]], steps: list[dict[str, Any]]) -> str:
    parts = [
        row.get("title"),
        row.get("display_title"),
        row.get("description"),
        row.get("meal_type"),
        row.get("category"),
        " ".join(str(item.get("name") or "") for item in ingredients),
        " ".join(str(item.get("text") or "") for item in steps),
    ]
    return re.sub(r"\s+", " ", " ".join(str(part or "") for part in parts).lower())


def has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def has_soup_term(text: str) -> bool:
    return has_any(text, SOUP_WORDS) or re.search(r"\bщи\b", text) is not None


def evaluate_nutrition_realism(
    row: dict[str, Any],
    ingredients: list[dict[str, Any]],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    values = nutrition_for(row)
    servings = serving_count_for(row)
    title = str(row.get("display_title") or row.get("title") or "").strip()
    meal_type = str(row.get("meal_type") or "").lower()
    category = str(row.get("category") or "").lower()
    blob = text_blob(row, ingredients, steps)
    flags: list[str] = []

    missing = [key for key, value in values.items() if value is None]
    if missing:
        flags.append(f"nutrition_missing:{','.join(missing)}")
    if servings is None or servings <= 0:
        flags.append("serving_count_missing_or_invalid")

    kcal = values["kcal"]
    protein = values["protein"]
    fat = values["fat"]
    carbs = values["carbs"]

    if kcal is not None and meal_type in {"breakfast", "lunch", "dinner"} and kcal < 80:
        flags.append("kcal_lt_80_full_meal")
    if kcal is not None and kcal > 1200 and meal_type != "snack":
        flags.append("kcal_gt_1200_single_serving")
    if protein is not None and protein > 100:
        flags.append("protein_gt_100g")
    if fat is not None and fat > 80:
        flags.append("fat_gt_80g")
    if carbs is not None and carbs > 180:
        flags.append("carbs_gt_180g")
    if kcal is not None and meal_type == "snack" and "дет" in blob and kcal > 600:
        flags.append("children_snack_gt_600_kcal")
    if has_any(blob, SALAD_PROTEIN_WORDS) and "салат" in blob and protein is not None and protein < 8:
        flags.append("protein_salad_protein_too_low")
    if has_any(blob, GRAIN_WORDS) and carbs is not None and carbs < 15:
        flags.append("grain_dish_carbs_too_low")
    if has_any(blob, OMELET_WORDS):
        if protein is not None and protein < 8:
            flags.append("omelet_protein_too_low")
        if fat is not None and fat < 5:
            flags.append("omelet_fat_too_low")

    if not row.get("nutrition_coverage_json"):
        flags.append("no_nutrition_coverage_metadata")
    if not row.get("nutrition_serving_size_text") and not row.get("serving_size_amount"):
        flags.append("no_portion_basis")
    if has_any(blob, GRAIN_WORDS) and not row.get("yield_type"):
        flags.append("dry_grain_yield_unknown")
    if ("масло" in blob or "жар" in blob or "обжар" in blob) and not row.get("nutrition_coverage_json"):
        flags.append("oil_or_frying_basis_unclear")
    if has_soup_term(blob) and not row.get("yield_type"):
        flags.append("soup_or_stew_yield_unknown")
    elif has_any(blob, STEW_WORDS) and not row.get("yield_type"):
        flags.append("braise_or_stew_yield_unknown")

    hard_markers = [flag for flag in flags if flag.startswith("nutrition_missing") or flag == "serving_count_missing_or_invalid"]
    outlier_markers = [
        flag
        for flag in flags
        if flag
        in {
            "kcal_lt_80_full_meal",
            "kcal_gt_1200_single_serving",
            "protein_gt_100g",
            "fat_gt_80g",
            "carbs_gt_180g",
        }
    ]
    if hard_markers:
        proposed_action = "missing_data"
        confidence = "low"
    elif outlier_markers:
        proposed_action = "needs_recalc"
        confidence = "low"
    elif any("too_low" in flag or flag.endswith("_unknown") for flag in flags):
        proposed_action = "needs_recalc"
        confidence = "medium"
    elif any(flag.startswith("no_") or flag.endswith("_unclear") for flag in flags):
        proposed_action = "needs_manual_review"
        confidence = "medium"
    else:
        proposed_action = "ok"
        confidence = "high"

    if len(ingredients) < 3 or len(steps) < 3:
        flags.append("insufficient_recipe_structure_for_nutrition_estimate")
        if proposed_action == "ok":
            proposed_action = "needs_manual_review"
            confidence = "medium"

    return {
        "recipe_id": int(row["id"]),
        "title": title,
        "kcal": values["kcal"],
        "protein": values["protein"],
        "fat": values["fat"],
        "carbs": values["carbs"],
        "serving_count": servings,
        "confidence": confidence,
        "flags": sorted(set(flags)),
        "proposed_action": proposed_action,
        "meal_type": meal_type,
        "category": category,
        "ingredient_count": len(ingredients),
        "step_count": len(steps),
    }


def build_report(database_url: str | None = None) -> dict[str, Any]:
    database_url = database_url or os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    if import_sqlalchemy() is None:
        return {
            "generated_at": now(),
            "ok": False,
            "db_available": False,
            "database_url": redact_url(database_url),
            "error": "sqlalchemy_unavailable",
            "recipes_checked": 0,
            "items": [],
        }
    try:
        rows, ingredients_by_id, steps_by_id = fetch_recipe_rows(GOLD_V3_IDS, database_url)
    except Exception as exc:
        return {
            "generated_at": now(),
            "ok": False,
            "db_available": False,
            "database_url": redact_url(database_url),
            "error": repr(exc),
            "recipes_checked": 0,
            "items": [],
        }

    found_ids = {int(row["id"]) for row in rows}
    missing_ids = [recipe_id for recipe_id in GOLD_V3_IDS if recipe_id not in found_ids]
    items = [
        evaluate_nutrition_realism(
            row,
            ingredients_by_id.get(int(row["id"])) or [],
            steps_by_id.get(int(row["id"])) or [],
        )
        for row in rows
    ]
    counts = {
        "ok": sum(1 for item in items if item["proposed_action"] == "ok"),
        "needs_review": sum(1 for item in items if item["proposed_action"] == "needs_manual_review"),
        "needs_recalc": sum(1 for item in items if item["proposed_action"] == "needs_recalc"),
        "missing_data": sum(1 for item in items if item["proposed_action"] == "missing_data"),
        "hard_blockers": len(missing_ids) + sum(1 for item in items if item["proposed_action"] == "missing_data"),
    }
    flag_counts: dict[str, int] = {}
    for item in items:
        for flag in item["flags"]:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
    return {
        "generated_at": now(),
        "ok": not missing_ids and counts["hard_blockers"] == 0,
        "db_available": True,
        "database_url": redact_url(database_url),
        "recipe_ids": GOLD_V3_IDS,
        "recipes_checked": len(items),
        "missing_ids": missing_ids,
        "summary": counts,
        "top_issues": sorted(flag_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20],
        "items": items,
    }


def render(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    lines = [
        "# Sprint 1.6 Nutrition Realism Audit",
        "",
        f"Generated: `{report.get('generated_at')}`",
        f"OK: `{report.get('ok')}`",
        f"DB available: `{report.get('db_available')}`",
        f"recipes_checked: `{report.get('recipes_checked')}`",
        f"missing_ids: `{report.get('missing_ids')}`",
        "",
        "## Summary",
        "",
        f"- ok: `{summary.get('ok', 0)}`",
        f"- needs_review: `{summary.get('needs_review', 0)}`",
        f"- needs_recalc: `{summary.get('needs_recalc', 0)}`",
        f"- missing_data: `{summary.get('missing_data', 0)}`",
        f"- hard_blockers: `{summary.get('hard_blockers', 0)}`",
        "",
        "## Top Issues",
        "",
    ]
    for flag, count in report.get("top_issues") or []:
        lines.append(f"- `{flag}`: `{count}`")
    lines.extend(["", "## Recipes", ""])
    for item in report.get("items") or []:
        lines.append(
            f"- `{item['recipe_id']}` {item['title']} — action: `{item['proposed_action']}`, "
            f"confidence: `{item['confidence']}`, kcal/protein/fat/carbs: "
            f"`{item['kcal']}/{item['protein']}/{item['fat']}/{item['carbs']}`, flags: `{item['flags']}`"
        )
    return "\n".join(lines) + "\n"


def render_correction_plan(report: dict[str, Any]) -> str:
    actionable = [
        item
        for item in report.get("items") or []
        if item.get("proposed_action") in {"needs_recalc", "needs_manual_review", "missing_data"}
    ]
    lines = [
        "# Sprint 1.6 Nutrition Correction Plan",
        "",
        f"Generated: `{report.get('generated_at')}`",
        "",
        "## Scope",
        "",
        "- Gold V3 upgraded IDs: `2, 227-255`",
        "- Gold V3 pilot IDs: `256-265`",
        "- Planning only. No DB mutation, apply, rollback, import, recipe generation, or photo generation.",
        "",
        "## Recipes Needing Follow-Up",
        "",
    ]
    for item in actionable:
        lines.append(
            f"- `{item['recipe_id']}` {item['title']} — `{item['proposed_action']}`; "
            f"flags: `{item['flags']}`"
        )
    if not actionable:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Proposed Recalculation Model",
            "",
            "- raw ingredient nutrition by ingredient amount and edible portion",
            "- cooking method adjustment for oil/frying/baking/boiling",
            "- recipe yield factor and final cooked total",
            "- per-serving result from cooked total divided by verified serving count",
            "- confidence level based on ingredient coverage and portion basis",
            "",
            "## Candidate Fields For Future Sprint",
            "",
            "- `nutrition_raw_total_json`",
            "- `nutrition_cooked_total_json`",
            "- `nutrition_per_serving_json`",
            "- `nutrition_confidence`",
            "- `yield_factor`",
            "- `serving_weight_g`",
            "- `nutrition_basis`",
            "",
            "## Future Guarded Update Requirement",
            "",
            "- dry-run first with exact expected IDs",
            "- update nutrition fields only",
            "- no unrelated recipe fields",
            "- rollback manifest before apply",
            "- post-apply API/menu/shopping QA",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()
    report = build_report(args.database_url)
    write_json(REPORT_JSON, report)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(render(report), encoding="utf-8")
    PLAN_MD.write_text(render_correction_plan(report), encoding="utf-8")
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON}")
    print(f"Wrote {PLAN_MD}")
    return 0 if report.get("db_available") else 1


if __name__ == "__main__":
    raise SystemExit(main())
