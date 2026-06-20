#!/usr/bin/env python3
"""Read-only readiness report (shopping list / nutrition / photo prompt).

Reads the ingredient quality columns populated by
migrate_to_taste_ingredients.py and summarizes how ready the catalog is for the
next pipelines. Never writes to the DB.

    python backend/scripts/report_recipe_readiness.py

Reports:
  reports/recipe_readiness_after_to_taste.md
  reports/recipe_readiness_after_to_taste.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
REPORTS = ROOT / "reports"
OUT_MD = REPORTS / "recipe_readiness_after_to_taste.md"
OUT_JSON = REPORTS / "recipe_readiness_after_to_taste.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recipe readiness report")
    parser.add_argument(
        "--database-url", default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    )
    parser.add_argument("--source-type", default="v1_import")
    return parser.parse_args()


def load_rows(engine, source_type: str) -> list[dict]:
    query = text(
        """
        SELECT ri.recipe_id, ri.name, ri.category, ri.quantity_mode, ri.is_to_taste,
               ri.nutrition_precision, ri.shopping_priority, ri.photo_visibility,
               ri.needs_review, ri.needs_review_reason
        FROM recipe_ingredients ri
        JOIN recipes r ON r.id = ri.recipe_id
        WHERE r.is_active = TRUE AND r.source_type = :source_type
        ORDER BY ri.recipe_id, ri.id
        """
    )
    with engine.connect() as conn:
        return [dict(m) for m in conn.execute(query, {"source_type": source_type}).mappings()]


def _b(v) -> bool:
    return bool(v) if v is not None else False


def build_report(rows: list[dict]) -> dict:
    total = len(rows) or 1
    shopping = Counter(r.get("shopping_priority") or "unset" for r in rows)
    nutrition = Counter(r.get("nutrition_precision") or "unset" for r in rows)
    photo = Counter(r.get("photo_visibility") or "unset" for r in rows)
    generic = sum(1 for r in rows if (r.get("needs_review_reason") == "generic"))
    to_taste = sum(1 for r in rows if _b(r.get("is_to_taste")))

    # per-recipe photo readiness
    by_recipe_visible: dict[int, int] = {}
    by_recipe_unsafe: dict[int, int] = {}
    for r in rows:
        rid = r["recipe_id"]
        by_recipe_visible.setdefault(rid, 0)
        by_recipe_unsafe.setdefault(rid, 0)
        if r.get("photo_visibility") in {"visible", "optional"}:
            by_recipe_visible[rid] += 1
        if r.get("photo_visibility") == "unsafe":
            by_recipe_unsafe[rid] += 1
    recipes = len(by_recipe_visible) or 1
    recipes_ready = sum(1 for c in by_recipe_visible.values() if c >= 2)

    # per-recipe nutrition: countable if no unavailable and at least mostly exact/estimated
    by_recipe_unavailable: dict[int, int] = {}
    for r in rows:
        rid = r["recipe_id"]
        by_recipe_unavailable.setdefault(rid, 0)
        if r.get("nutrition_precision") in {"low_confidence", "unavailable"}:
            by_recipe_unavailable[rid] += 1
    recipes_estimable = sum(1 for c in by_recipe_unavailable.values() if c == 0)
    recipes_need_manual = recipes - recipes_estimable

    skip_reasons = Counter(
        r.get("needs_review_reason") for r in rows if r.get("needs_review_reason")
    )

    return {
        "total_ingredients": len(rows),
        "recipes": len(by_recipe_visible),
        "shopping_list_readiness": {
            "normal": shopping.get("normal", 0),
            "low": shopping.get("low", 0),
            "optional": shopping.get("optional", 0),
            "hidden": shopping.get("hidden", 0),
            "unset": shopping.get("unset", 0),
            "generic": generic,
            "to_taste": to_taste,
        },
        "nutrition_readiness": {
            "exact": nutrition.get("exact", 0),
            "estimated": nutrition.get("estimated", 0),
            "low_confidence": nutrition.get("low_confidence", 0),
            "unavailable": nutrition.get("unavailable", 0),
            "unset": nutrition.get("unset", 0),
            "recipes_estimable": recipes_estimable,
            "recipes_need_manual": recipes_need_manual,
        },
        "photo_prompt_readiness": {
            "visible": photo.get("visible", 0),
            "optional": photo.get("optional", 0),
            "hidden": photo.get("hidden", 0),
            "unsafe": photo.get("unsafe", 0),
            "unset": photo.get("unset", 0),
            "recipes_ready": recipes_ready,
            "recipes_not_ready": recipes - recipes_ready,
            "top_skip_reasons": dict(skip_reasons.most_common(8)),
        },
    }


def render_md(rep: dict, started_at: str) -> str:
    lines: list[str] = []
    a = lines.append
    s = rep["shopping_list_readiness"]
    n = rep["nutrition_readiness"]
    p = rep["photo_prompt_readiness"]
    a("# PLANAM V1 — Recipe readiness after to_taste")
    a("")
    a(f"**Запуск:** {started_at}")
    a(f"**Всего ингредиентов:** {rep['total_ingredients']} · **рецептов:** {rep['recipes']}")
    a("")
    a("## Shopping list readiness")
    a("")
    a("| priority | строк |")
    a("|----------|-------|")
    a(f"| normal | {s['normal']} |")
    a(f"| low | {s['low']} |")
    a(f"| optional | {s['optional']} |")
    a(f"| hidden | {s['hidden']} |")
    a(f"| (не размечено) | {s['unset']} |")
    a("")
    a(f"- generic: **{s['generic']}** · to_taste: **{s['to_taste']}**")
    a("")
    a("## Nutrition readiness")
    a("")
    a("| precision | строк |")
    a("|-----------|-------|")
    a(f"| exact | {n['exact']} |")
    a(f"| estimated | {n['estimated']} |")
    a(f"| low_confidence | {n['low_confidence']} |")
    a(f"| unavailable | {n['unavailable']} |")
    a(f"| (не размечено) | {n['unset']} |")
    a("")
    a(f"- рецептов можно считать приблизительно: **{n['recipes_estimable']}**")
    a(f"- рецептов нельзя без ручной правки: **{n['recipes_need_manual']}**")
    a("")
    a("## Photo prompt readiness")
    a("")
    a("| visibility | строк |")
    a("|------------|-------|")
    a(f"| visible | {p['visible']} |")
    a(f"| optional | {p['optional']} |")
    a(f"| hidden | {p['hidden']} |")
    a(f"| unsafe | {p['unsafe']} |")
    a(f"| (не размечено) | {p['unset']} |")
    a("")
    a(f"- рецептов готовы к prompt (>=2 видимых): **{p['recipes_ready']}**")
    a(f"- рецептов не готовы: **{p['recipes_not_ready']}**")
    a(f"- visible ingredients: **{p['visible']}** · hidden: **{p['hidden']}** · unsafe: **{p['unsafe']}**")
    a("")
    a("### Top skip reasons")
    a("")
    if p["top_skip_reasons"]:
        a("| reason | строк |")
        a("|--------|-------|")
        for reason, count in p["top_skip_reasons"].items():
            a(f"| {reason} | {count} |")
    else:
        a("_Нет._")
    a("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    engine = create_engine(args.database_url)
    rows = load_rows(engine, args.source_type)
    rep = build_report(rows)

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_md(rep, started_at), encoding="utf-8")
    OUT_JSON.write_text(
        json.dumps({"started_at": started_at, "source_type": args.source_type, **rep}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"ingredients={rep['total_ingredients']} recipes={rep['recipes']}")
    print(f"MD:   {OUT_MD}")
    print(f"JSON: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
