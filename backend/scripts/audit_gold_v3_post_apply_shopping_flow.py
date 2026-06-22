"""Shopping flow audit for upgraded Gold V3 recipe ingredients (read-only)."""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_gold_v3_post_apply_common import (  # noqa: E402
    duplicate_unit_issues,
    extract_upgraded_recipe_ids,
    fetch_recipe_rows,
    has_user_facing_garbage,
    import_sqlalchemy,
    ingredient_category_safe,
    ingredient_name,
    now,
    redact_url,
    write_json,
)


REPORT_JSON = ROOT / "reports" / "SPRINT_1_3M_SHOPPING_FLOW.json"
REPORT_MD = ROOT / "reports" / "SPRINT_1_3M_SHOPPING_FLOW.md"


def shopping_item_from_ingredient(ingredient: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": ingredient_name(ingredient),
        "quantity": ingredient.get("quantity"),
        "unit": ingredient.get("unit"),
        "quantity_text": ingredient.get("quantity_text"),
        "category": ingredient.get("category"),
    }


def evaluate_ingredient(ingredient: dict[str, Any]) -> list[str]:
    blockers = []
    name = ingredient_name(ingredient)
    if not name:
        blockers.append("empty_ingredient_name")
    unit = str(ingredient.get("unit") or "").strip()
    if not unit:
        blockers.append("missing_unit")
    quantity = ingredient.get("quantity")
    if quantity is None and not str(ingredient.get("quantity_text") or "").strip():
        blockers.append("missing_amount")
    blockers.extend(duplicate_unit_issues(ingredient))
    garbage = has_user_facing_garbage(json.dumps(shopping_item_from_ingredient(ingredient), ensure_ascii=False))
    if garbage:
        blockers.append(f"user_facing_garbage:{','.join(garbage)}")
    if not ingredient_category_safe(ingredient):
        blockers.append("unknown_category")
    return blockers


def evaluate_shopping_flow(
    rows: list[dict[str, Any]],
    ingredients_by_id: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    items = []
    hard_fail = 0
    category_counter: Counter[str] = Counter()
    ingredient_total = 0

    for row in rows:
        recipe_id = int(row["id"])
        ingredients = ingredients_by_id.get(recipe_id) or []
        recipe_blockers = []
        ingredient_items = []
        if not ingredients:
            recipe_blockers.append("no_ingredients")
        for ingredient in ingredients:
            ingredient_total += 1
            blockers = evaluate_ingredient(ingredient)
            category_counter[str(ingredient.get("category") or "missing")] += 1
            if blockers:
                recipe_blockers.extend(blockers)
            ingredient_items.append(
                {
                    "name": ingredient_name(ingredient),
                    "blockers": blockers,
                    "shopping_item": shopping_item_from_ingredient(ingredient),
                }
            )
        if recipe_blockers:
            hard_fail += 1
        items.append(
            {
                "id": recipe_id,
                "title": row.get("display_title") or row.get("title"),
                "ingredient_count": len(ingredients),
                "blockers": sorted(set(recipe_blockers)),
                "ingredients": ingredient_items,
            }
        )

    return {
        "generated_at": now(),
        "records": len(rows),
        "ingredient_total": ingredient_total,
        "passed": hard_fail == 0,
        "hard_fail": hard_fail,
        "category_distribution": dict(category_counter),
        "items": items,
        "top_blockers": sorted({blocker for item in items for blocker in item["blockers"]}),
    }


def build_report() -> dict[str, Any]:
    database_url = os.environ.get("DATABASE_URL")
    if import_sqlalchemy() is None:
        return {
            "generated_at": now(),
            "ok": False,
            "db_available": False,
            "hard_fail": 1,
            "error": "sqlalchemy_unavailable",
            "items": [],
        }
    recipe_ids = extract_upgraded_recipe_ids().get("recipe_ids") or []
    try:
        rows, ingredients_by_id, _ = fetch_recipe_rows(recipe_ids, database_url)
    except Exception as exc:
        return {
            "generated_at": now(),
            "ok": False,
            "db_available": False,
            "hard_fail": 1,
            "error": repr(exc),
            "items": [],
        }
    report = evaluate_shopping_flow(rows, ingredients_by_id)
    report["ok"] = report["passed"]
    report["db_available"] = True
    report["database_url"] = redact_url(database_url or "")
    return report


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3M Shopping Flow",
        "",
        f"Generated: `{report['generated_at']}`",
        f"passed: `{report.get('passed')}`",
        f"hard_fail: `{report.get('hard_fail')}`",
        f"ingredient_total: `{report.get('ingredient_total')}`",
        "",
        "## Category distribution",
        "",
    ]
    for category, count in sorted((report.get("category_distribution") or {}).items()):
        lines.append(f"- `{category}`: {count}")
    blocked = [item for item in report.get("items") or [] if item.get("blockers")]
    if blocked:
        lines.extend(["", "## Blocked recipes", ""])
        for item in blocked[:20]:
            lines.append(f"- {item['id']} {item['title']}: {item['blockers']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(render(report), encoding="utf-8")
    print(f"Wrote {REPORT_MD}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
