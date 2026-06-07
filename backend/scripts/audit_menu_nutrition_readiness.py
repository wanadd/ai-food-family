#!/usr/bin/env python3
"""Read-only audit: can the selected menus be turned into day/week KБЖУ?

Cross-references planned menu slots (family_menu_selections.menu_data JSON) with
recipe-level nutrition (recipes.nutrition_*). Never writes the DB.

    python backend/scripts/audit_menu_nutrition_readiness.py --dry-run
    python backend/scripts/audit_menu_nutrition_readiness.py --date 2026-06-07
    python backend/scripts/audit_menu_nutrition_readiness.py --week-start 2026-06-03

Reports: reports/menu_nutrition_readiness.md / .json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
REPORTS = ROOT / "reports"
OUT_MD = REPORTS / "menu_nutrition_readiness.md"
OUT_JSON = REPORTS / "menu_nutrition_readiness.json"

USABLE = {"exact", "estimated", "low_confidence"}


def _load_json(value):
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return None
    return None


def _iter_slots(menu_data: dict):
    """Yield (date_iso, meal_type, recipe_id) for filled slots."""
    if not isinstance(menu_data, dict):
        return
    days = menu_data.get("days")
    if isinstance(days, list) and days:
        for day in days:
            if not isinstance(day, dict):
                continue
            date_iso = day.get("date_iso")
            for meal in day.get("meals", []) or []:
                if isinstance(meal, dict) and meal.get("recipe_id"):
                    yield date_iso, meal.get("meal_type"), meal.get("recipe_id")
    else:
        for meal in menu_data.get("meals", []) or []:
            if isinstance(meal, dict) and meal.get("recipe_id"):
                yield None, meal.get("meal_type"), meal.get("recipe_id")


def classify_day(counts: dict) -> str:
    total = counts["total"]
    calc = counts["calculated"]
    if total == 0 or calc == 0:
        return "unavailable"
    coverage = calc / total
    if coverage < 0.40:
        return "unavailable"
    if coverage >= 0.90 and counts["unavailable"] == 0 and counts["exact"] / calc >= 0.8:
        return "exact"
    if coverage >= 0.70 and counts["unavailable"] <= 1:
        return "estimated"
    return "low_confidence"


def collect(engine, *, on_date: str | None, week_start: str | None) -> dict:
    wanted_dates: set[str] | None = None
    if on_date:
        wanted_dates = {on_date}
    elif week_start:
        start = date.fromisoformat(week_start)
        wanted_dates = {(start + timedelta(days=i)).isoformat() for i in range(7)}

    with engine.connect() as conn:
        selections = list(
            conn.execute(text("SELECT id, user_id, family_id, menu_data FROM family_menu_selections")).mappings()
        )
        recipe_rows = {
            r["id"]: {"confidence": r["nutrition_confidence"], "kcal": r["nutrition_kcal_per_serving"]}
            for r in conn.execute(
                text("SELECT id, nutrition_confidence, nutrition_kcal_per_serving FROM recipes")
            ).mappings()
        }

    total_items = 0
    with_recipe = 0
    with_nutrition = 0
    unavailable = 0
    low_conf = 0
    missing_recipe_ids: Counter = Counter()
    # day key = (selection_id, date_iso)
    day_counts: dict[tuple, dict] = {}

    for sel in selections:
        menu = _load_json(sel["menu_data"])
        for date_iso, _meal_type, recipe_id in _iter_slots(menu):
            if wanted_dates is not None and date_iso not in wanted_dates:
                continue
            total_items += 1
            with_recipe += 1
            rec = recipe_rows.get(recipe_id)
            key = (sel["id"], date_iso or "flat")
            dc = day_counts.setdefault(
                key, {"total": 0, "calculated": 0, "exact": 0, "unavailable": 0}
            )
            dc["total"] += 1
            conf = rec["confidence"] if rec else None
            kcal = rec["kcal"] if rec else None
            if rec and conf in USABLE and kcal is not None:
                with_nutrition += 1
                dc["calculated"] += 1
                if conf == "exact":
                    dc["exact"] += 1
                if conf == "low_confidence":
                    low_conf += 1
            else:
                unavailable += 1
                dc["unavailable"] += 1
                if rec is None:
                    missing_recipe_ids[recipe_id] += 1

    days_computable = sum(1 for c in day_counts.values() if classify_day(c) != "unavailable")
    days_not = len(day_counts) - days_computable

    return {
        "selections": len(selections),
        "menu_items": total_items,
        "with_recipe_id": with_recipe,
        "with_nutrition_summary": with_nutrition,
        "unavailable_items": unavailable,
        "low_confidence_items": low_conf,
        "days_total": len(day_counts),
        "days_computable": days_computable,
        "days_not_computable": days_not,
        "top_missing_recipe_ids": missing_recipe_ids.most_common(20),
    }


def render_md(rep: dict, scope_label: str) -> str:
    lines: list[str] = []
    a = lines.append
    a("# PLANAM V1 — Menu nutrition readiness (read-only audit)")
    a("")
    a(f"**Область:** {scope_label}")
    a("")
    a("| метрика | значение |")
    a("|---------|----------|")
    a(f"| selections | {rep['selections']} |")
    a(f"| menu items | {rep['menu_items']} |")
    a(f"| с recipe_id | {rep['with_recipe_id']} |")
    a(f"| с nutrition summary (usable) | {rep['with_nutrition_summary']} |")
    a(f"| unavailable | {rep['unavailable_items']} |")
    a(f"| low_confidence | {rep['low_confidence_items']} |")
    a(f"| дней всего | {rep['days_total']} |")
    a(f"| дней можно посчитать | {rep['days_computable']} |")
    a(f"| дней нельзя посчитать | {rep['days_not_computable']} |")
    a("")
    if rep["top_missing_recipe_ids"]:
        a("## Топ проблем: recipe_id без nutrition (или отсутствуют)")
        a("")
        a("| recipe_id | слотов |")
        a("|-----------|--------|")
        for rid, cnt in rep["top_missing_recipe_ids"]:
            a(f"| {rid} | {cnt} |")
        a("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Menu nutrition readiness audit (read-only)")
    parser.add_argument(
        "--database-url", default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    )
    parser.add_argument("--date", default=None)
    parser.add_argument("--week-start", default=None)
    parser.add_argument("--dry-run", action="store_true", help="(default) read-only, all dates")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    engine = create_engine(args.database_url)
    rep = collect(engine, on_date=args.date, week_start=args.week_start)
    scope_label = (
        f"date={args.date}" if args.date
        else f"week-start={args.week_start}" if args.week_start
        else "все даты (dry-run)"
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_md(rep, scope_label), encoding="utf-8")
    OUT_JSON.write_text(
        json.dumps({"scope": scope_label, **rep}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"selections={rep['selections']} items={rep['menu_items']} "
        f"with_nutrition={rep['with_nutrition_summary']} "
        f"days_computable={rep['days_computable']}/{rep['days_total']}"
    )
    print(f"MD:   {OUT_MD}")
    print(f"JSON: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
