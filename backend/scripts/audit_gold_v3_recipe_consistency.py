"""Read-only recipe consistency audit for 40 Gold V3 recipes."""

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
API_ROOT = ROOT / "apps" / "api"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if (API_ROOT / "app").is_dir() and str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from audit_gold_v3_nutrition_realism import GOLD_V3_IDS  # noqa: E402
from audit_gold_v3_post_apply_common import (  # noqa: E402
    fetch_recipe_rows,
    has_source_leakage,
    has_user_facing_garbage,
    import_sqlalchemy,
    now,
    redact_url,
    title_garbage,
    write_json,
)

from app.services.recipes.step_display import public_recipe_steps  # noqa: E402
from app.services.recipes.title_display import public_recipe_title  # noqa: E402


REPORT_JSON = ROOT / "reports" / "SPRINT_1_6_RECIPE_CONSISTENCY_AUDIT.json"
REPORT_MD = ROOT / "reports" / "SPRINT_1_6_RECIPE_CONSISTENCY_AUDIT.md"
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"

MAIN_INGREDIENT_HINTS: dict[str, tuple[str, ...]] = {
    "омлет": ("яйц",),
    "овсян": ("овсян", "хлоп"),
    "творож": ("творог",),
    "авокадо": ("авокадо",),
    "банан": ("банан",),
    "рис": ("рис",),
    "индейк": ("индейк",),
    "куриц": ("куриц", "курин", "кури"),
    "греч": ("греч",),
    "фасол": ("фасол",),
    "кревет": ("кревет",),
    "свини": ("свини", "свин"),
    "лосос": ("лосос", "рыб"),
    "перлов": ("перлов",),
    "салат": ("салат", "зелень", "огур", "помид"),
}
BAD_TITLE_TERMS = ("без свинины", "high protein", "pro weight loss", "pre-workout", "post-workout")


def normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def ingredient_names(ingredients: list[dict[str, Any]]) -> list[str]:
    return [normalize(item.get("name")) for item in ingredients if normalize(item.get("name"))]


def step_texts(steps: list[dict[str, Any]]) -> list[str]:
    return [normalize(item.get("text")) for item in steps if normalize(item.get("text"))]


def display_step_texts(
    recipe_id: int,
    steps: list[dict[str, Any]],
    ingredients: list[dict[str, Any]],
) -> list[str]:
    raw_steps = [str(item.get("text") or "") for item in steps if str(item.get("text") or "").strip()]
    return [normalize(step) for step in public_recipe_steps(recipe_id, raw_steps, ingredients) if normalize(step)]


def title_main_terms(title: str) -> list[str]:
    lowered = normalize(title)
    return [term for term in MAIN_INGREDIENT_HINTS if term in lowered]


def evaluate_recipe_consistency(
    row: dict[str, Any],
    ingredients: list[dict[str, Any]],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    recipe_id = int(row["id"])
    raw_title = str(row.get("display_title") or row.get("title") or "").strip()
    title = public_recipe_title(raw_title, recipe_id=recipe_id)
    title_l = normalize(title)
    description = normalize(row.get("description"))
    ing_names = ingredient_names(ingredients)
    raw_step_values = step_texts(steps)
    step_values = display_step_texts(recipe_id, steps, ingredients)
    ingredient_blob = " ".join(ing_names)
    step_blob = " ".join(step_values)
    all_text = " ".join([title_l, description, ingredient_blob, step_blob, json.dumps(row.get("tags") or [], ensure_ascii=False)]).lower()
    hard_fail: list[str] = []
    warnings: list[str] = []

    if not title:
        hard_fail.append("title_empty")
    for term in BAD_TITLE_TERMS:
        if term in title_l:
            hard_fail.append(f"bad_title_term:{term}")
    title_issues = title_garbage(title)
    if title_issues:
        hard_fail.append(f"title_garbage:{','.join(title_issues)}")
    if has_source_leakage(all_text):
        hard_fail.append("source_leakage")
    if has_user_facing_garbage(all_text):
        hard_fail.append("user_facing_garbage")
    if "{" in all_text or "}" in all_text or "[" in all_text or "]" in all_text:
        # Tags are JSON in DB, so only user-facing fields should drive this check.
        user_text = " ".join([title_l, description, ingredient_blob, step_blob])
        if "{" in user_text or "}" in user_text or "[" in user_text or "]" in user_text:
            hard_fail.append("raw_json_user_facing")

    if len(ing_names) < 3:
        hard_fail.append("ingredients_lt_3")
    if len(step_values) < 3:
        hard_fail.append("steps_lt_3")

    title_terms = title_main_terms(title)
    for term in title_terms:
        hints = MAIN_INGREDIENT_HINTS[term]
        if not any(hint in ingredient_blob for hint in hints):
            hard_fail.append(f"title_main_ingredient_missing:{term}")

    important_ingredients = [
        name
        for name in ing_names
        if not any(skip in name for skip in ("соль", "перец", "вода", "масло", "специи", "зелень"))
    ][:6]
    missing_in_steps = [
        name
        for name in important_ingredients
        if name and name.split()[0] not in step_blob
    ]
    if len(missing_in_steps) >= max(2, len(important_ingredients) // 2):
        warnings.append(f"important_ingredients_not_referenced_in_steps:{missing_in_steps[:4]}")

    absent_refs = []
    referenced_ingredient_aliases = {
        "индейк": ("индейк",),
        "куриц": ("куриц", "курин", "куриное", "куриный", "куриная"),
        "кревет": ("кревет",),
        "рыб": ("рыб", "лосос", "треск", "тунец"),
        "лосос": ("лосос", "рыб"),
        "свини": ("свини", "свин"),
        "рис": ("рис",),
        "греч": ("греч",),
        "перлов": ("перлов",),
        "фасол": ("фасол",),
        "яйц": ("яйц",),
    }
    for word, aliases in referenced_ingredient_aliases.items():
        if word in step_blob and not any(alias in ingredient_blob or alias in title_l for alias in aliases):
            absent_refs.append(word)
    if absent_refs:
        hard_fail.append(f"steps_reference_absent_ingredient:{sorted(set(absent_refs))}")

    method_words = ("вар", "запек", "туш", "обжар", "жар", "смеш", "нареж", "довед")
    if not any(word in step_blob for word in method_words):
        warnings.append("cooking_method_unclear")
    if row.get("hero_image_url") and not row.get("image_url"):
        warnings.append("partial_image_urls")

    return {
        "recipe_id": recipe_id,
        "title": title,
        "raw_title": raw_title,
        "title_display_clean": title == public_recipe_title(title, recipe_id=recipe_id),
        "ingredient_count": len(ing_names),
        "step_count": len(step_values),
        "raw_steps_changed": raw_step_values != step_values,
        "hard_fail": sorted(set(hard_fail)),
        "warnings": sorted(set(warnings)),
        "ok": not hard_fail,
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
        evaluate_recipe_consistency(
            row,
            ingredients_by_id.get(int(row["id"])) or [],
            steps_by_id.get(int(row["id"])) or [],
        )
        for row in rows
    ]
    hard_fail = len(missing_ids) + sum(1 for item in items if item["hard_fail"])
    warnings = sum(len(item["warnings"]) for item in items)
    issue_counts: dict[str, int] = {}
    for item in items:
        for issue in [*item["hard_fail"], *item["warnings"]]:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
    return {
        "generated_at": now(),
        "ok": hard_fail == 0,
        "db_available": True,
        "database_url": redact_url(database_url),
        "recipe_ids": GOLD_V3_IDS,
        "recipes_checked": len(items),
        "missing_ids": missing_ids,
        "hard_fail": hard_fail,
        "warnings": warnings,
        "top_issues": sorted(issue_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20],
        "items": items,
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.6 Recipe Consistency Audit",
        "",
        f"Generated: `{report.get('generated_at')}`",
        f"OK: `{report.get('ok')}`",
        f"DB available: `{report.get('db_available')}`",
        f"recipes_checked: `{report.get('recipes_checked')}`",
        f"missing_ids: `{report.get('missing_ids')}`",
        f"hard_fail: `{report.get('hard_fail')}`",
        f"warnings: `{report.get('warnings')}`",
        "",
        "## Top Issues",
        "",
    ]
    for issue, count in report.get("top_issues") or []:
        lines.append(f"- `{issue}`: `{count}`")
    lines.extend(["", "## Recipes", ""])
    for item in report.get("items") or []:
        lines.append(
            f"- `{item['recipe_id']}` {item['title']} — hard_fail: `{item['hard_fail']}`, "
            f"warnings: `{item['warnings']}`"
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
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON}")
    return 0 if report.get("db_available") else 1


if __name__ == "__main__":
    raise SystemExit(main())
