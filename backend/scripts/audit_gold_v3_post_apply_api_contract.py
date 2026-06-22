"""Post-apply API contract audit for upgraded Gold V3 recipes (read-only)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_gold_v3_post_apply_common import (  # noqa: E402
    count_json_array,
    extract_upgraded_recipe_ids,
    fetch_recipe_rows,
    has_source_leakage,
    has_user_facing_garbage,
    image_field_safe,
    import_sqlalchemy,
    nutrition_complete,
    now,
    parse_json_value,
    redact_url,
    row_diets,
    row_tags,
    recipe_text_blob,
    servings_safe,
    time_fields_safe,
    title_garbage,
    write_json,
)


REPORT_JSON = ROOT / "reports" / "SPRINT_1_3M_POST_APPLY_API_CONTRACT.json"
REPORT_MD = ROOT / "reports" / "SPRINT_1_3M_POST_APPLY_API_CONTRACT.md"
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"


def api_visible_payload(row: dict[str, Any], ingredients: list[dict[str, Any]], steps: list[dict[str, Any]]) -> dict[str, Any]:
    ingredient_names = [str(item.get("name") or "") for item in ingredients]
    step_texts = [str(item.get("text") or "") for item in steps]
    return {
        "id": row.get("id"),
        "title": row.get("display_title") or row.get("title"),
        "display_title": row.get("display_title"),
        "description": row.get("description") or "",
        "meal_type": row.get("meal_type"),
        "servings": row.get("servings"),
        "cooking_time_minutes": row.get("cooking_time_minutes"),
        "prep_time_minutes": row.get("prep_time_minutes"),
        "hero_image_url": row.get("hero_image_url"),
        "image_url": row.get("image_url"),
        "thumbnail_url": row.get("thumbnail_url"),
        "ingredients": ingredient_names,
        "steps": step_texts,
        "tags": row_tags(row.get("tags")),
        "diets": row_diets(row.get("diets")),
        "nutrition": {
            "kcal": row.get("calories_per_serving") or row.get("nutrition_kcal_per_serving"),
            "protein_g": row.get("protein_g") or row.get("nutrition_protein_per_serving"),
            "fat_g": row.get("fat_g") or row.get("nutrition_fat_per_serving"),
            "carbs_g": row.get("carbs_g") or row.get("nutrition_carbs_per_serving"),
        },
    }


def evaluate_recipe(
    row: dict[str, Any],
    ingredients: list[dict[str, Any]],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    recipe_id = int(row["id"])
    blockers: list[str] = []
    warnings: list[str] = []

    title = str(row.get("display_title") or row.get("title") or "").strip()
    description = str(row.get("description") or "").strip()
    if not title:
        blockers.append("title_empty")
    if not description:
        warnings.append("description_empty")
    if not row.get("meal_type"):
        blockers.append("meal_type_missing")
    if not servings_safe(row):
        blockers.append("servings_invalid")
    if not time_fields_safe(row):
        blockers.append("time_fields_invalid")
    if not nutrition_complete(row):
        blockers.append("nutrition_incomplete")

    ingredient_count = len(ingredients) or count_json_array(row.get("ingredients"))
    step_count = len(steps) or count_json_array(row.get("steps"))
    if ingredient_count < 3:
        blockers.append("ingredients_lt_3")
    if step_count < 3:
        blockers.append("steps_lt_3")

    for field in ("tags", "diets", "ingredients", "steps", "nutrition_coverage_json"):
        _, error = parse_json_value(row.get(field))
        if error:
            blockers.append(f"{field}_json_invalid")

    for field in ("hero_image_url", "image_url", "thumbnail_url"):
        if not image_field_safe(row.get(field)):
            blockers.append(f"image_field_unsafe:{field}")

    blob = recipe_text_blob(row, ingredients, steps)
    leakage = has_source_leakage(blob)
    if leakage:
        blockers.append(f"source_leakage:{','.join(leakage)}")
    if row.get("source_url"):
        warnings.append("source_url_db_present")
    garbage = has_user_facing_garbage(blob)
    if garbage:
        blockers.append(f"user_facing_garbage:{','.join(garbage)}")
    title_issues = title_garbage(title)
    if title_issues:
        blockers.append(f"title_garbage:{','.join(title_issues)}")

    payload = api_visible_payload(row, ingredients, steps)
    payload_text = json.dumps(payload, ensure_ascii=False).lower()
    if "source_url" in payload_text or "original_url" in payload_text:
        blockers.append("api_payload_source_leakage")

    return {
        "id": recipe_id,
        "title": title,
        "meal_type": row.get("meal_type"),
        "ingredient_count": ingredient_count,
        "step_count": step_count,
        "nutrition_complete": nutrition_complete(row),
        "blockers": blockers,
        "warnings": warnings,
        "ok": not blockers,
    }


def build_report() -> dict[str, Any]:
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    if import_sqlalchemy() is None:
        return {
            "generated_at": now(),
            "ok": False,
            "db_available": False,
            "hard_fail": 1,
            "warnings_count": 0,
            "error": "sqlalchemy_unavailable",
            "database_url": redact_url(database_url),
            "recipes": [],
        }

    id_report = extract_upgraded_recipe_ids()
    recipe_ids = id_report.get("recipe_ids") or []
    try:
        rows, ingredients_by_id, steps_by_id = fetch_recipe_rows(recipe_ids, database_url)
    except Exception as exc:
        return {
            "generated_at": now(),
            "ok": False,
            "db_available": False,
            "hard_fail": 1,
            "warnings_count": 0,
            "error": repr(exc),
            "database_url": redact_url(database_url),
            "recipe_ids": recipe_ids,
            "recipes": [],
        }

    found_ids = {int(row["id"]) for row in rows}
    missing_ids = [recipe_id for recipe_id in recipe_ids if recipe_id not in found_ids]
    items = []
    hard_fail = len(missing_ids)
    warnings_count = 0
    if missing_ids:
        hard_fail += 1
    for row in rows:
        recipe_id = int(row["id"])
        item = evaluate_recipe(row, ingredients_by_id.get(recipe_id) or [], steps_by_id.get(recipe_id) or [])
        warnings_count += len(item["warnings"])
        if item["blockers"]:
            hard_fail += 1
        items.append(item)

    return {
        "generated_at": now(),
        "ok": hard_fail == 0,
        "db_available": True,
        "database_url": redact_url(database_url),
        "plan_id": id_report.get("computed_plan_id"),
        "recipe_ids": recipe_ids,
        "missing_ids": missing_ids,
        "hard_fail": hard_fail,
        "warnings_count": warnings_count,
        "recipes": items,
        "top_blockers": sorted(
            {
                blocker
                for item in items
                for blocker in item["blockers"]
            }
        ),
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3M Post-Apply API Contract",
        "",
        f"Generated: `{report['generated_at']}`",
        f"OK: `{report.get('ok')}`",
        f"hard_fail: `{report.get('hard_fail')}`",
        f"warnings_count: `{report.get('warnings_count')}`",
        f"DB available: `{report.get('db_available')}`",
        f"missing_ids: `{report.get('missing_ids')}`",
        "",
        "| id | title | ingredients | steps | nutrition | ok | blockers |",
        "| --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for item in report.get("recipes") or []:
        title = str(item.get("title") or "").replace("|", "\\|")
        lines.append(
            f"| {item['id']} | {title} | {item['ingredient_count']} | {item['step_count']} | "
            f"{item['nutrition_complete']} | {item['ok']} | {item['blockers']} |"
        )
    if report.get("top_blockers"):
        lines.extend(["", "## Top blockers", ""])
        lines.extend(f"- {blocker}" for blocker in report["top_blockers"])
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(render(report), encoding="utf-8")
    print(f"Wrote {REPORT_MD}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
