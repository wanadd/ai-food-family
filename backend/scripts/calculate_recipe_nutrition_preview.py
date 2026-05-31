#!/usr/bin/env python3
"""Preview recipe nutrition calculation from ingredient amounts.

This is a read-only MVP calculator. It reads recipes, normalizes ingredient
amounts, applies a small seed nutrition reference, and writes a Markdown report.
It does not update recipes, import data, or create migrations.

Run from the repository root:
    python backend/scripts/calculate_recipe_nutrition_preview.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from normalize_ingredient_amounts import normalize_amount, readable_text


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
DEFAULT_REFERENCE_PATH = ROOT / "backend" / "data" / "nutrition_reference_seed.json"
DEFAULT_REPORT_PATH = ROOT / "reports" / "recipe_nutrition_calculation_preview.md"


@dataclass(frozen=True)
class RecipeRow:
    id: int
    title: str
    servings: int | None
    ingredients: list[Any]


@dataclass(frozen=True)
class NutritionReference:
    canonical_name: str
    calories_per_100g: float
    protein_g_per_100g: float
    fat_g_per_100g: float
    carbs_g_per_100g: float
    default_unit_grams: dict[str, float]


@dataclass(frozen=True)
class IngredientCalculation:
    name: str
    amount: str
    canonical_name: str | None
    grams: float | None
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float
    status: str
    reason: str


@dataclass(frozen=True)
class RecipeCalculation:
    recipe: RecipeRow
    ingredients: list[IngredientCalculation]
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float
    calculated_count: int
    skipped_count: int
    missing_count: int
    unmeasured_count: int

    @property
    def is_fully_calculated(self) -> bool:
        return self.missing_count == 0 and self.unmeasured_count == 0

    @property
    def is_partially_calculated(self) -> bool:
        return self.calculated_count > 0 and not self.is_fully_calculated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview recipe nutrition calculation from ingredient amounts"
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--reference",
        default=str(DEFAULT_REFERENCE_PATH),
        help="Path to nutrition reference seed JSON",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown calculation preview report",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=10,
        help="Number of calculated recipe examples to show in the report",
    )
    return parser.parse_args()


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_name(value: Any) -> str:
    text_value = readable_text(value).lower().replace("ё", "е")
    text_value = re.sub(r"[^0-9a-zа-я]+", " ", text_value, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text_value).strip()


def number_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_reference(path: Path) -> dict[str, NutritionReference]:
    raw_items = json.loads(path.read_text(encoding="utf-8"))
    aliases: dict[str, NutritionReference] = {}
    for raw in raw_items:
        reference = NutritionReference(
            canonical_name=str(raw["canonical_name"]),
            calories_per_100g=float(raw["calories_per_100g"]),
            protein_g_per_100g=float(raw["protein_g_per_100g"]),
            fat_g_per_100g=float(raw["fat_g_per_100g"]),
            carbs_g_per_100g=float(raw["carbs_g_per_100g"]),
            default_unit_grams={
                str(unit): float(grams)
                for unit, grams in (raw.get("default_unit_grams") or {}).items()
            },
        )
        names = [raw["canonical_name"], *(raw.get("aliases") or [])]
        for name in names:
            normalized = normalize_name(name)
            if normalized:
                aliases[normalized] = reference
    return aliases


def rows_to_recipes(rows: Any) -> list[RecipeRow]:
    recipes: list[RecipeRow] = []
    for row in rows:
        ingredients = row.get("ingredients")
        recipes.append(
            RecipeRow(
                id=int(row["id"]),
                title=readable_text(row["title"]),
                servings=int(row["servings"]) if row.get("servings") else None,
                ingredients=ingredients if isinstance(ingredients, list) else [],
            )
        )
    return recipes


def load_recipes(database_url: str) -> list[RecipeRow]:
    engine = create_engine(database_url)
    query = text(
        """
        SELECT id, title, servings, ingredients
        FROM recipes
        ORDER BY id
        """
    )
    with engine.connect() as conn:
        rows = list(conn.execute(query).mappings())
    return rows_to_recipes(rows)


def load_recipes_via_docker() -> list[RecipeRow]:
    sql = """
        SELECT COALESCE(json_agg(row_to_json(t) ORDER BY id), '[]'::json)
        FROM (
            SELECT id, title, servings, ingredients
            FROM recipes
            ORDER BY id
        ) AS t;
        """
    cmd = [
        "docker",
        "compose",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        "aifood",
        "-d",
        "aifood",
        "-t",
        "-A",
        "-c",
        sql,
    ]
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    rows = json.loads(result.stdout.strip() or "[]")
    return rows_to_recipes(rows)


def ingredient_name(ingredient: Any) -> str:
    if isinstance(ingredient, dict):
        return readable_text(ingredient.get("name"))
    return readable_text(ingredient)


def ingredient_amount(ingredient: Any) -> str:
    if not isinstance(ingredient, dict):
        return ""
    raw_amount = ingredient.get("amount")
    if raw_amount:
        return clean_text(raw_amount)
    quantity = clean_text(ingredient.get("quantity"))
    unit = clean_text(ingredient.get("unit"))
    return f"{quantity} {unit}".strip()


def grams_for_unit(
    quantity: float,
    unit: str,
    reference: NutritionReference,
) -> tuple[float | None, str | None]:
    if unit == "g":
        return quantity, None
    if unit == "ml":
        multiplier = reference.default_unit_grams.get("ml", 1.0)
        return quantity * multiplier, None
    multiplier = reference.default_unit_grams.get(unit)
    if multiplier is None:
        return None, f"missing_unit_conversion:{unit}"
    return quantity * multiplier, None


def calculate_ingredient(
    ingredient: Any,
    reference_by_alias: dict[str, NutritionReference],
) -> IngredientCalculation:
    name = ingredient_name(ingredient)
    amount = ingredient_amount(ingredient)
    normalized = normalize_amount(amount)
    reference = reference_by_alias.get(normalize_name(name))

    if normalized.amount_type == "to_taste":
        return IngredientCalculation(
            name=name,
            amount=amount,
            canonical_name=reference.canonical_name if reference else None,
            grams=None,
            calories=0,
            protein_g=0,
            fat_g=0,
            carbs_g=0,
            status="skipped",
            reason="to_taste",
        )

    if not normalized.success or normalized.quantity is None or normalized.unit is None:
        return IngredientCalculation(
            name=name,
            amount=amount,
            canonical_name=reference.canonical_name if reference else None,
            grams=None,
            calories=0,
            protein_g=0,
            fat_g=0,
            carbs_g=0,
            status="unmeasured",
            reason=normalized.reason,
        )

    if reference is None:
        return IngredientCalculation(
            name=name,
            amount=amount,
            canonical_name=None,
            grams=None,
            calories=0,
            protein_g=0,
            fat_g=0,
            carbs_g=0,
            status="missing_reference",
            reason="missing_reference",
        )

    grams, reason = grams_for_unit(normalized.quantity, normalized.unit, reference)
    if grams is None:
        return IngredientCalculation(
            name=name,
            amount=amount,
            canonical_name=reference.canonical_name,
            grams=None,
            calories=0,
            protein_g=0,
            fat_g=0,
            carbs_g=0,
            status="unmeasured",
            reason=reason or "missing_unit_conversion",
        )

    factor = grams / 100
    return IngredientCalculation(
        name=name,
        amount=amount,
        canonical_name=reference.canonical_name,
        grams=grams,
        calories=reference.calories_per_100g * factor,
        protein_g=reference.protein_g_per_100g * factor,
        fat_g=reference.fat_g_per_100g * factor,
        carbs_g=reference.carbs_g_per_100g * factor,
        status="calculated",
        reason="calculated",
    )


def calculate_recipe(
    recipe: RecipeRow,
    reference_by_alias: dict[str, NutritionReference],
) -> RecipeCalculation:
    ingredients = [
        calculate_ingredient(ingredient, reference_by_alias)
        for ingredient in recipe.ingredients
    ]
    return RecipeCalculation(
        recipe=recipe,
        ingredients=ingredients,
        calories=sum(item.calories for item in ingredients),
        protein_g=sum(item.protein_g for item in ingredients),
        fat_g=sum(item.fat_g for item in ingredients),
        carbs_g=sum(item.carbs_g for item in ingredients),
        calculated_count=sum(item.status == "calculated" for item in ingredients),
        skipped_count=sum(item.status == "skipped" for item in ingredients),
        missing_count=sum(item.status == "missing_reference" for item in ingredients),
        unmeasured_count=sum(item.status == "unmeasured" for item in ingredients),
    )


def round_nutrition(value: float) -> float:
    return round(value, 1)


def per_serving_line(calculation: RecipeCalculation) -> str:
    servings = calculation.recipe.servings
    if servings and servings > 0:
        return (
            f"per serving ({servings}): "
            f"{round_nutrition(calculation.calories / servings)} kcal, "
            f"P {round_nutrition(calculation.protein_g / servings)}g, "
            f"F {round_nutrition(calculation.fat_g / servings)}g, "
            f"C {round_nutrition(calculation.carbs_g / servings)}g"
        )
    return (
        "whole recipe, servings missing: "
        f"{round_nutrition(calculation.calories)} kcal, "
        f"P {round_nutrition(calculation.protein_g)}g, "
        f"F {round_nutrition(calculation.fat_g)}g, "
        f"C {round_nutrition(calculation.carbs_g)}g"
    )


def build_report(
    calculations: list[RecipeCalculation],
    reference_path: Path,
    sample_size: int,
    connection_note: str,
) -> str:
    fully = [item for item in calculations if item.is_fully_calculated]
    partially = [item for item in calculations if item.is_partially_calculated]
    coverage = (len(fully) / len(calculations) * 100) if calculations else 0
    missing_reference_counts: Counter[str] = Counter()
    unmeasured_counts: Counter[str] = Counter()
    for calculation in calculations:
        for ingredient in calculation.ingredients:
            if ingredient.status == "missing_reference":
                missing_reference_counts[normalize_name(ingredient.name)] += 1
            elif ingredient.status == "unmeasured":
                key = f"{normalize_name(ingredient.name)} [{ingredient.reason}]"
                unmeasured_counts[key] += 1

    lines = [
        "# Recipe Nutrition Calculation Preview",
        "",
        "Scope: read-only nutrition calculation preview from normalized ingredient amounts. No database changes, recipe updates, imports, or migrations were performed.",
        "",
        "## Summary",
        "",
        f"- Read connection: `{connection_note}`",
        f"- Reference seed: `{reference_path}`",
        f"- Total recipes checked: `{len(calculations)}`",
        f"- Recipes fully calculated: `{len(fully)}`",
        f"- Recipes partially calculated: `{len(partially)}`",
        f"- Fully calculated coverage: `{coverage:.1f}%`",
        f"- Missing reference ingredients: `{sum(missing_reference_counts.values())}`",
        f"- Unmeasured ingredients: `{sum(unmeasured_counts.values())}`",
        "",
        "## Top Missing Ingredients",
        "",
    ]
    if missing_reference_counts:
        for name, count in missing_reference_counts.most_common(30):
            lines.append(f"- `{name}`: `{count}`")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Top Unmeasured Ingredients", ""])
    if unmeasured_counts:
        for name, count in unmeasured_counts.most_common(30):
            lines.append(f"- `{name}`: `{count}`")
    else:
        lines.append("- `n/a`")

    lines.extend(["", f"## Calculated Recipe Examples ({sample_size})", ""])
    examples = [item for item in calculations if item.calculated_count > 0][
        :sample_size
    ]
    if not examples:
        lines.append("- `n/a`")
    for calculation in examples:
        recipe = calculation.recipe
        status = (
            "full"
            if calculation.is_fully_calculated
            else f"partial, missing={calculation.missing_count}, unmeasured={calculation.unmeasured_count}"
        )
        lines.extend(
            [
                f"### #{recipe.id} {recipe.title}",
                "",
                f"- Status: `{status}`",
                f"- Ingredients calculated: `{calculation.calculated_count}`",
                f"- Ingredients skipped/to_taste: `{calculation.skipped_count}`",
                f"- Total recipe: `{round_nutrition(calculation.calories)}` kcal, "
                f"`{round_nutrition(calculation.protein_g)}`g protein, "
                f"`{round_nutrition(calculation.fat_g)}`g fat, "
                f"`{round_nutrition(calculation.carbs_g)}`g carbs",
                f"- {per_serving_line(calculation)}",
                "",
            ]
        )
        shown = 0
        for ingredient in calculation.ingredients:
            if ingredient.status != "calculated":
                continue
            lines.append(
                f"  - {ingredient.name}: `{round_nutrition(ingredient.grams or 0)}`g as "
                f"`{ingredient.canonical_name}` -> "
                f"`{round_nutrition(ingredient.calories)}` kcal"
            )
            shown += 1
            if shown >= 5:
                break
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    reference_path = Path(args.reference).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    if args.sample_size < 1:
        raise SystemExit("--sample-size must be at least 1")

    reference_by_alias = load_reference(reference_path)
    try:
        recipes = load_recipes(args.database_url)
        connection_note = "SQLAlchemy"
    except SQLAlchemyError as exc:
        print(
            "SQLAlchemy connection failed, falling back to docker compose psql: "
            f"{exc.__class__.__name__}"
        )
        recipes = load_recipes_via_docker()
        connection_note = "docker compose psql"

    calculations = [
        calculate_recipe(recipe, reference_by_alias)
        for recipe in recipes
    ]
    report = build_report(
        calculations=calculations,
        reference_path=reference_path,
        sample_size=args.sample_size,
        connection_note=connection_note,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    fully_count = sum(item.is_fully_calculated for item in calculations)
    partial_count = sum(item.is_partially_calculated for item in calculations)
    missing_count = sum(
        item.status == "missing_reference"
        for calculation in calculations
        for item in calculation.ingredients
    )
    print(f"Read connection: {connection_note}")
    print(f"Total recipes checked: {len(calculations)}")
    print(f"Recipes fully calculated: {fully_count}")
    print(f"Recipes partially calculated: {partial_count}")
    print(f"Missing reference ingredients: {missing_count}")
    print(f"Report written to: {report_path}")


if __name__ == "__main__":
    main()
