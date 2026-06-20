#!/usr/bin/env python3
"""Group ingredients for the shopping list (read-only report).

Groups by shopping_priority + category, hides `hidden`, and marks `to_taste`
/ low / optional as non-mandatory. Does NOT change shopping list logic — only
prepares/inspects the data. Reuses Row/load_rows from calculate_nutrition.

    python backend/scripts/generate_shopping_list_groups.py

Report: reports/shopping_list_groups.md / .json
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
OUT_MD = REPORTS / "shopping_list_groups.md"
OUT_JSON = REPORTS / "shopping_list_groups.json"

MANDATORY = {"normal"}
NON_MANDATORY = {"low", "optional"}
HIDDEN = {"hidden"}


def _priority(row: Row) -> str:
    return row.shopping_priority or "normal"


def build_summary(rows: list[Row]) -> dict:
    priority = Counter(_priority(r) for r in rows)
    by_category = Counter(r.category for r in rows)
    mandatory = sum(1 for r in rows if _priority(r) in MANDATORY and not r.is_to_taste)
    non_mandatory = sum(1 for r in rows if _priority(r) in NON_MANDATORY or r.is_to_taste)
    hidden = sum(1 for r in rows if _priority(r) in HIDDEN)
    return {
        "ingredients": len(rows),
        "priority_counts": dict(priority),
        "category_counts": dict(by_category.most_common()),
        "mandatory": mandatory,
        "non_mandatory": non_mandatory,
        "hidden": hidden,
        "to_taste": sum(1 for r in rows if r.is_to_taste),
    }


def build_recipe_groups(rows: list[Row]) -> dict[int, dict]:
    """Per recipe: category -> {mandatory[], optional[], hidden[]}."""
    by_recipe: dict[int, dict] = defaultdict(
        lambda: {"title": "", "categories": defaultdict(lambda: {"mandatory": [], "optional": [], "hidden": []})}
    )
    for row in rows:
        bucket = by_recipe[row.recipe_id]
        bucket["title"] = row.title
        prio = _priority(row)
        item = {"name": row.name, "quantity": row.quantity, "unit": row.unit, "priority": prio}
        cats = bucket["categories"][row.category]
        if prio in HIDDEN:
            cats["hidden"].append(item)
        elif prio in NON_MANDATORY or row.is_to_taste:
            cats["optional"].append(item)
        else:
            cats["mandatory"].append(item)
    # convert defaultdicts to plain dicts
    out: dict[int, dict] = {}
    for rid, bucket in by_recipe.items():
        out[rid] = {
            "title": bucket["title"],
            "categories": {cat: dict(v) for cat, v in bucket["categories"].items()},
        }
    return out


def render_md(summary: dict, groups: dict[int, dict], started_at: str) -> str:
    lines: list[str] = []
    a = lines.append
    a("# PLANAM V1 — Shopping list grouping")
    a("")
    a(f"**Запуск:** {started_at}")
    a(f"**Ингредиентов:** {summary['ingredients']}")
    a("")
    a("## Priority")
    a("")
    a("| priority | строк |")
    a("|----------|-------|")
    for key in ("normal", "low", "optional", "hidden"):
        a(f"| {key} | {summary['priority_counts'].get(key, 0)} |")
    a("")
    a(f"- обязательных к покупке: **{summary['mandatory']}**")
    a(f"- необязательных (low/optional/to_taste): **{summary['non_mandatory']}**")
    a(f"- скрытых (hidden): **{summary['hidden']}**")
    a("")
    a("## По категориям")
    a("")
    a("| категория | строк |")
    a("|-----------|-------|")
    for cat, count in summary["category_counts"].items():
        a(f"| {cat} | {count} |")
    a("")
    a("## Пример группировки рецепта")
    a("")
    if groups:
        rid = sorted(groups)[0]
        bucket = groups[rid]
        a(f"### recipe_id={rid} — {bucket['title']}")
        a("")
        for cat, lists in bucket["categories"].items():
            a(f"**{cat}**")
            for item in lists["mandatory"]:
                a(f"- [ ] {item['name']} — {item['quantity']} {item['unit']}")
            for item in lists["optional"]:
                a(f"- _(опц.)_ {item['name']} — {item['quantity']} {item['unit']}")
            for item in lists["hidden"]:
                a(f"- ~~{item['name']}~~ (скрыт)")
            a("")
    return "\n".join(lines)


def write_reports(rows: list[Row], started_at: str) -> dict:
    summary = build_summary(rows)
    groups = build_recipe_groups(rows)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_md(summary, groups, started_at), encoding="utf-8")
    OUT_JSON.write_text(
        json.dumps(
            {"started_at": started_at, "summary": summary, "recipe_groups": groups},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Shopping list grouping (read-only)")
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
    summary = write_reports(rows, started_at)
    print(f"ingredients={summary['ingredients']} mandatory={summary['mandatory']} hidden={summary['hidden']}")
    print(f"MD:   {OUT_MD}")
    print(f"JSON: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
