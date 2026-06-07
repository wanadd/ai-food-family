#!/usr/bin/env python3
"""Estimate KБЖУ per ingredient row + per recipe (read-only report).

Uses nutrition_data.py (facts per 100 g + unit conversion). Never writes the DB
on its own — the orchestrator (nutrition_shopping_photo_pipeline.py) owns the
safe-only commit. Shared `Row` + `load_rows` are reused by the other scripts.

    python backend/scripts/calculate_nutrition.py

Report: reports/nutrition_estimate.md / .json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from canonical_products import resolve_product  # noqa: E402
from nutrition_data import RowNutrition, compute_row_nutrition  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
REPORTS = ROOT / "reports"
OUT_MD = REPORTS / "nutrition_estimate.md"
OUT_JSON = REPORTS / "nutrition_estimate.json"


@dataclass
class Row:
    id: int
    recipe_id: int
    title: str
    servings: int
    name: str
    quantity: str
    unit: str
    category: str
    notes: str | None
    is_to_taste: bool
    generic: bool
    nutrition_precision: str | None
    shopping_priority: str | None
    photo_visibility: str | None


def _b(v) -> bool:
    return bool(v) if v is not None else False


def load_rows(engine, source_type: str = "v1_import") -> list[Row]:
    query = text(
        """
        SELECT ri.id, ri.recipe_id, r.title, r.servings, ri.name, ri.quantity,
               ri.unit, ri.category, ri.notes, ri.is_to_taste, ri.nutrition_precision,
               ri.shopping_priority, ri.photo_visibility
        FROM recipe_ingredients ri
        JOIN recipes r ON r.id = ri.recipe_id
        WHERE r.is_active = TRUE AND r.source_type = :source_type
        ORDER BY ri.recipe_id, ri.id
        """
    )
    rows: list[Row] = []
    with engine.connect() as conn:
        for m in conn.execute(query, {"source_type": source_type}).mappings():
            product = resolve_product(m["name"] or "")
            rows.append(
                Row(
                    id=m["id"],
                    recipe_id=m["recipe_id"],
                    title=m["title"] or "",
                    servings=int(m["servings"] or 4),
                    name=m["name"] or "",
                    quantity=m["quantity"] or "",
                    unit=m["unit"] or "",
                    category=m["category"] or "other",
                    notes=m["notes"],
                    is_to_taste=_b(m["is_to_taste"]),
                    generic=product.generic,
                    nutrition_precision=m["nutrition_precision"],
                    shopping_priority=m["shopping_priority"],
                    photo_visibility=m["photo_visibility"],
                )
            )
    return rows


def nutrition_for(row: Row) -> RowNutrition:
    return compute_row_nutrition(
        row.name,
        row.quantity,
        row.unit,
        category=row.category,
        generic=row.generic,
        is_to_taste=row.is_to_taste,
    )


@dataclass
class RecipeNutrition:
    recipe_id: int
    title: str
    servings: int
    kcal: float
    protein: float
    fat: float
    carbs: float
    rows_total: int
    rows_with_grams: int
    estimable: bool

    @property
    def per_serving_kcal(self) -> float:
        return round(self.kcal / max(1, self.servings), 1)


def aggregate_by_recipe(rows: list[Row]) -> list[RecipeNutrition]:
    by_id: dict[int, dict] = {}
    for row in rows:
        n = nutrition_for(row)
        agg = by_id.setdefault(
            row.recipe_id,
            {
                "title": row.title,
                "servings": row.servings,
                "kcal": 0.0,
                "protein": 0.0,
                "fat": 0.0,
                "carbs": 0.0,
                "rows_total": 0,
                "rows_with_grams": 0,
                "blocking": 0,  # non-to_taste, non-generic rows we still can't quantify
            },
        )
        agg["rows_total"] += 1
        if n.grams is not None:
            agg["rows_with_grams"] += 1
            agg["kcal"] += n.kcal
            agg["protein"] += n.protein
            agg["fat"] += n.fat
            agg["carbs"] += n.carbs
        elif not row.is_to_taste and not row.generic:
            agg["blocking"] += 1

    result: list[RecipeNutrition] = []
    for rid, agg in by_id.items():
        result.append(
            RecipeNutrition(
                recipe_id=rid,
                title=agg["title"],
                servings=agg["servings"],
                kcal=round(agg["kcal"], 1),
                protein=round(agg["protein"], 1),
                fat=round(agg["fat"], 1),
                carbs=round(agg["carbs"], 1),
                rows_total=agg["rows_total"],
                rows_with_grams=agg["rows_with_grams"],
                estimable=agg["blocking"] == 0,
            )
        )
    result.sort(key=lambda r: r.recipe_id)
    return result


def summarize(rows: list[Row], recipes: list[RecipeNutrition]) -> dict:
    precision = Counter(nutrition_for(r).precision for r in rows)
    return {
        "ingredients": len(rows),
        "recipes": len(recipes),
        "precision_counts": dict(precision),
        "recipes_estimable": sum(1 for r in recipes if r.estimable),
        "recipes_need_manual": sum(1 for r in recipes if not r.estimable),
    }


def render_md(summary: dict, recipes: list[RecipeNutrition], started_at: str) -> str:
    lines: list[str] = []
    a = lines.append
    a("# PLANAM V1 — Nutrition estimate (KБЖУ)")
    a("")
    a(f"**Запуск:** {started_at}")
    a(f"**Ингредиентов:** {summary['ingredients']} · **рецептов:** {summary['recipes']}")
    a("")
    a("## Precision (per ingredient)")
    a("")
    a("| precision | строк |")
    a("|-----------|-------|")
    for key in ("exact", "estimated", "low_confidence", "unavailable"):
        a(f"| {key} | {summary['precision_counts'].get(key, 0)} |")
    a("")
    a(f"- рецептов можно считать: **{summary['recipes_estimable']}**")
    a(f"- рецептов нужна ручная правка: **{summary['recipes_need_manual']}**")
    a("")
    a("## Per-recipe estimate (первые 40)")
    a("")
    a("| recipe_id | рецепт | ккал | б | ж | у | ккал/порц | покрытие | estimable |")
    a("|-----------|--------|------|---|---|---|-----------|----------|-----------|")
    for r in recipes[:40]:
        cov = f"{r.rows_with_grams}/{r.rows_total}"
        a(
            f"| {r.recipe_id} | {r.title} | {r.kcal} | {r.protein} | {r.fat} | "
            f"{r.carbs} | {r.per_serving_kcal} | {cov} | {'да' if r.estimable else 'нет'} |"
        )
    a("")
    return "\n".join(lines)


def write_reports(rows: list[Row], recipes: list[RecipeNutrition], started_at: str) -> None:
    summary = summarize(rows, recipes)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_md(summary, recipes, started_at), encoding="utf-8")
    OUT_JSON.write_text(
        json.dumps(
            {
                "started_at": started_at,
                "summary": summary,
                "recipes": [
                    {
                        "recipe_id": r.recipe_id,
                        "title": r.title,
                        "servings": r.servings,
                        "kcal": r.kcal,
                        "protein": r.protein,
                        "fat": r.fat,
                        "carbs": r.carbs,
                        "per_serving_kcal": r.per_serving_kcal,
                        "coverage": f"{r.rows_with_grams}/{r.rows_total}",
                        "estimable": r.estimable,
                    }
                    for r in recipes
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Estimate nutrition (read-only)")
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
    recipes = aggregate_by_recipe(rows)
    write_reports(rows, recipes, started_at)
    print(f"ingredients={len(rows)} recipes={len(recipes)}")
    print(f"MD:   {OUT_MD}")
    print(f"JSON: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
