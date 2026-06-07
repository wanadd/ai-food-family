#!/usr/bin/env python3
"""Evaluate photo prompt readiness per recipe (read-only report).

A recipe is "ready" when it has >= 2 visible/optional ingredients. Classifies
photo_visibility (visible / optional / hidden / unsafe). Does NOT generate
prompts or images. Reuses Row/load_rows from calculate_nutrition.

    python backend/scripts/evaluate_photo_prompt_readiness.py

Report: reports/photo_prompt_readiness.md / .json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from calculate_nutrition import Row, load_rows  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
REPORTS = ROOT / "reports"
OUT_MD = REPORTS / "photo_prompt_readiness.md"
OUT_JSON = REPORTS / "photo_prompt_readiness.json"

MIN_VISIBLE = 2
SHOWN = {"visible", "optional"}


def _vis(row: Row) -> str:
    return row.photo_visibility or "visible"


def evaluate(rows: list[Row]) -> dict:
    visible_by_recipe: dict[int, list[str]] = defaultdict(list)
    title_by_recipe: dict[int, str] = {}
    vis_counts = Counter(_vis(r) for r in rows)
    for row in rows:
        title_by_recipe[row.recipe_id] = row.title
        if _vis(row) in SHOWN:
            visible_by_recipe[row.recipe_id].append(row.name)

    recipes: list[dict] = []
    all_recipe_ids = {r.recipe_id for r in rows}
    for rid in sorted(all_recipe_ids):
        names = visible_by_recipe.get(rid, [])
        recipes.append(
            {
                "recipe_id": rid,
                "title": title_by_recipe.get(rid, ""),
                "visible_count": len(names),
                "ready": len(names) >= MIN_VISIBLE,
                "visible_ingredients": names[:8],
            }
        )

    ready = sum(1 for r in recipes if r["ready"])
    return {
        "recipes": len(recipes),
        "recipes_ready": ready,
        "recipes_not_ready": len(recipes) - ready,
        "visibility_counts": {
            "visible": vis_counts.get("visible", 0),
            "optional": vis_counts.get("optional", 0),
            "hidden": vis_counts.get("hidden", 0),
            "unsafe": vis_counts.get("unsafe", 0),
        },
        "recipe_list": recipes,
    }


def render_md(rep: dict, started_at: str) -> str:
    lines: list[str] = []
    a = lines.append
    v = rep["visibility_counts"]
    a("# PLANAM V1 — Photo prompt readiness")
    a("")
    a(f"**Запуск:** {started_at}")
    a(f"**Рецептов:** {rep['recipes']}")
    a("")
    a("## Visibility (per ingredient)")
    a("")
    a("| visibility | строк |")
    a("|------------|-------|")
    a(f"| visible | {v['visible']} |")
    a(f"| optional | {v['optional']} |")
    a(f"| hidden | {v['hidden']} |")
    a(f"| unsafe | {v['unsafe']} |")
    a("")
    a(f"- рецептов готовы к prompt (>= {MIN_VISIBLE} видимых): **{rep['recipes_ready']}**")
    a(f"- рецептов не готовы: **{rep['recipes_not_ready']}**")
    a("")
    a("## Рецепты не готовы (первые 30)")
    a("")
    not_ready = [r for r in rep["recipe_list"] if not r["ready"]][:30]
    if not_ready:
        a("| recipe_id | рецепт | видимых |")
        a("|-----------|--------|---------|")
        for r in not_ready:
            a(f"| {r['recipe_id']} | {r['title']} | {r['visible_count']} |")
    else:
        a("_Все рецепты готовы._")
    a("")
    return "\n".join(lines)


def write_reports(rows: list[Row], started_at: str) -> dict:
    rep = evaluate(rows)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_md(rep, started_at), encoding="utf-8")
    OUT_JSON.write_text(
        json.dumps({"started_at": started_at, **rep}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return rep


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Photo prompt readiness (read-only)")
    parser.add_argument(
        "--database-url", default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    )
    parser.add_argument("--source-type", default="v1_import")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    engine = create_engine(args.database_url)
    rows = load_rows(engine, args.source_type)
    rep = write_reports(rows, started_at)
    print(f"recipes={rep['recipes']} ready={rep['recipes_ready']} not_ready={rep['recipes_not_ready']}")
    print(f"MD:   {OUT_MD}")
    print(f"JSON: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
