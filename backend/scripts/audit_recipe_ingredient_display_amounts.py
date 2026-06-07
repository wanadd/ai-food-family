#!/usr/bin/env python3
"""Read-only audit: do ingredient display amounts wrongly show "шт"?

Compares recipe_ingredients rows against the recipes.ingredients JSONB and the
honest formatter, flagging amounts like "по вкусу шт", "800 г шт", etc.

    python backend/scripts/audit_recipe_ingredient_display_amounts.py --dry-run

Reports: reports/recipe_ingredient_display_amounts_audit.md / .json
Never writes the DB.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.services.ingredient_format import (  # noqa: E402
    format_ingredient_amount,
    sanitize_amount_text,
)

DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
REPORTS = ROOT / "reports"
OUT_MD = REPORTS / "recipe_ingredient_display_amounts_audit.md"
OUT_JSON = REPORTS / "recipe_ingredient_display_amounts_audit.json"

SUSPICIOUS = re.compile(
    r"(по вкусу|немного|щепотк\w*|\bг\b|\bкг\b|\bмл\b|\bл\b|ст\.л\.|ч\.л\.|зубчик|стакан|пучок)\s+шт\b",
    re.IGNORECASE,
)


def _load_json(value):
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return None
    return None


def collect(engine) -> dict:
    with engine.connect() as conn:
        rows = list(
            conn.execute(
                text(
                    "SELECT recipe_id, name, quantity, unit, quantity_mode, "
                    "is_to_taste, quantity_text FROM recipe_ingredients"
                )
            ).mappings()
        )
        recipes = {
            r["id"]: r["ingredients"]
            for r in conn.execute(
                text("SELECT id, ingredients FROM recipes")
            ).mappings()
        }

    unit_dist: Counter = Counter()
    row_count = 0
    for r in rows:
        row_count += 1
        unit_dist[(r["unit"] or "").strip() or "<empty>"] += 1

    jsonb_amount_dist: Counter = Counter()
    suspicious_jsonb: list[dict] = []
    for rid, raw in recipes.items():
        data = _load_json(raw) or []
        for item in data:
            if not isinstance(item, dict):
                continue
            amount = str(item.get("amount", "")).strip()
            jsonb_amount_dist[_amount_shape(amount)] += 1
            if SUSPICIOUS.search(amount):
                suspicious_jsonb.append(
                    {"recipe_id": rid, "name": item.get("name", ""), "amount": amount,
                     "fixed": sanitize_amount_text(amount)}
                )

    # Mismatches: row -> formatter says X, but unit shows "шт" wrongly.
    fixed_examples: list[dict] = []
    rows_unit_not_sht = sum(
        1 for r in rows if (r["unit"] or "").strip().lower() not in {"шт", "шт.", ""}
    )
    for r in rows[:5000]:
        before = f"{r['quantity']} {r['unit']}".strip()
        after = format_ingredient_amount(
            r["quantity"], r["unit"],
            quantity_mode=r["quantity_mode"],
            is_to_taste_flag=bool(r["is_to_taste"]),
            quantity_text=r["quantity_text"],
        )
        if before != after and len(fixed_examples) < 40:
            fixed_examples.append(
                {"recipe_id": r["recipe_id"], "name": r["name"],
                 "before": before, "after": after}
            )

    recipe_problem_counter: Counter = Counter()
    for ex in suspicious_jsonb:
        recipe_problem_counter[ex["recipe_id"]] += 1

    return {
        "recipe_ingredient_rows": row_count,
        "rows_unit_distribution": dict(unit_dist.most_common()),
        "rows_unit_not_sht": rows_unit_not_sht,
        "jsonb_amount_shapes": dict(jsonb_amount_dist.most_common()),
        "suspicious_jsonb_count": len(suspicious_jsonb),
        "suspicious_jsonb_examples": suspicious_jsonb[:40],
        "top_problem_recipes": recipe_problem_counter.most_common(20),
        "formatter_before_after_examples": fixed_examples,
    }


def _amount_shape(amount: str) -> str:
    if not amount:
        return "<empty>"
    if SUSPICIOUS.search(amount):
        return "<suspicious_шт>"
    if re.search(r"\bшт\b", amount, re.IGNORECASE):
        return "<has_шт>"
    return "<ok>"


def render_md(rep: dict) -> str:
    lines: list[str] = []
    a = lines.append
    a("# PLANAM V1 — Ingredient display amounts audit (read-only)")
    a("")
    a(f"- recipe_ingredients rows: **{rep['recipe_ingredient_rows']}**")
    a(f"- rows с unit != шт/пусто: **{rep['rows_unit_not_sht']}**")
    a(f"- подозрительных JSONB amount («… шт»): **{rep['suspicious_jsonb_count']}**")
    a("")
    a("## Распределение unit в recipe_ingredients")
    a("")
    a("| unit | строк |")
    a("|------|-------|")
    for unit, cnt in rep["rows_unit_distribution"].items():
        a(f"| {unit} | {cnt} |")
    a("")
    a("## Формы JSONB amount")
    a("")
    a("| форма | кол-во |")
    a("|-------|--------|")
    for shape, cnt in rep["jsonb_amount_shapes"].items():
        a(f"| {shape} | {cnt} |")
    a("")
    if rep["suspicious_jsonb_examples"]:
        a("## Подозрительные JSONB amount (before → after)")
        a("")
        a("| recipe_id | ингредиент | было | станет |")
        a("|-----------|-----------|------|--------|")
        for ex in rep["suspicious_jsonb_examples"]:
            a(f"| {ex['recipe_id']} | {ex['name']} | {ex['amount']} | {ex['fixed']} |")
        a("")
    if rep["formatter_before_after_examples"]:
        a("## recipe_ingredients: formatter before → after")
        a("")
        a("| recipe_id | ингредиент | было | станет |")
        a("|-----------|-----------|------|--------|")
        for ex in rep["formatter_before_after_examples"]:
            a(f"| {ex['recipe_id']} | {ex['name']} | {ex['before']} | {ex['after']} |")
        a("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingredient display amounts audit (read-only)")
    parser.add_argument(
        "--database-url", default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    )
    parser.add_argument("--dry-run", action="store_true", help="(default) read-only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    engine = create_engine(args.database_url)
    rep = collect(engine)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_md(rep), encoding="utf-8")
    OUT_JSON.write_text(
        json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"rows={rep['recipe_ingredient_rows']} "
        f"unit_not_sht={rep['rows_unit_not_sht']} "
        f"suspicious_jsonb={rep['suspicious_jsonb_count']}"
    )
    print(f"MD:   {OUT_MD}")
    print(f"JSON: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
