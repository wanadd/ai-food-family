"""Read-only audit for remaining recipes with incomplete nutrition data.

This script reads a fixed set of remaining recipe IDs, groups them by the
recommended follow-up strategy, and writes a Markdown report. It does not update
the database.

Usage:
    python backend/scripts/audit_remaining_nutrition_gaps.py
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
DEFAULT_REPORT_PATH = ROOT / "reports" / "remaining_nutrition_gap_audit.md"

REMAINING_IDS = [
    22,
    24,
    27,
    *range(32, 59),
    *range(59, 75),
]

NUTRITION_FIELDS = (
    "calories_per_serving",
    "protein_g",
    "fat_g",
    "carbs_g",
)

GROUP_STRATEGIES = {
    "A": (
        "normal_recipe_partial_missing",
        "Use ingredient engine. If ingredient coverage is incomplete, enrich or normalize only the missing ingredient aliases/units before applying automatically.",
    ),
    "B": (
        "beverage_or_drink",
        "Use beverage-specific rules or GPT-4.1 fallback. Drinks often need liquid volume, dilution, sweetener, caffeine, and serving-size handling.",
    ),
    "C": (
        "placeholder_recipe",
        "Manual review / AI enrichment / do not apply automatically. Placeholder ingredients are not enough for reliable nutrition math.",
    ),
    "D": (
        "alcohol",
        "Add alcohol_percent and use beverage rules. Alcoholic recipes need ABV-aware calories and should not be treated as ordinary food.",
    ),
}

DRINK_MEAL_TYPES = {
    "drink",
    "cocktail",
    "smoothie",
    "protein_shake",
    "tea",
    "coffee",
}
DRINK_CATEGORIES = {"drink", "beverage", "cocktail", "smoothie"}
DRINK_TITLE_KEYWORDS = (
    "напит",
    "смузи",
    "чай",
    "кофе",
    "коктей",
    "лимонад",
    "морс",
    "компот",
    "квас",
)
ALCOHOL_TITLE_KEYWORDS = (
    "алког",
    "вино",
    "пиво",
    "ром",
    "водк",
    "джин",
    "ликер",
    "ликёр",
    "шампан",
    "глинтвейн",
)
PLACEHOLDER_INGREDIENTS = {
    "основа напитка",
    "основной продукт",
    "ингредиенты по вкусу",
}
NON_REAL_INGREDIENTS = {
    "вода",
    "соль",
    "специи",
    "приправа",
    "перец черный",
    "лист лавровый",
}


@dataclass(frozen=True)
class RecipeGapRow:
    id: int
    title: str
    calories_per_serving: float | None
    protein_g: float | None
    fat_g: float | None
    carbs_g: float | None
    ingredients: list[Any]
    servings: int | None
    category: str
    meal_type: str
    is_drink: bool
    is_alcoholic: bool
    alcohol_percent: float | None

    @property
    def missing_nutrition_fields(self) -> list[str]:
        return [field for field in NUTRITION_FIELDS if getattr(self, field) is None]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit remaining nutrition gaps")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown remaining nutrition gap audit report",
    )
    return parser.parse_args()


def readable_text(value: Any) -> str:
    text_value = str(value or "").strip()
    if not any(marker in text_value for marker in ("Р", "С", "Ð", "Ñ")):
        return text_value
    try:
        repaired = text_value.encode("cp1251").decode("utf-8")
    except UnicodeError:
        return text_value
    return repaired or text_value


def normalize_text(value: Any) -> str:
    return readable_text(value).lower().replace("ё", "е").strip()


def normalize_ingredients(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def ingredient_name(ingredient: Any) -> str:
    if isinstance(ingredient, dict):
        return readable_text(ingredient.get("name"))
    return readable_text(ingredient)


def ingredient_amount(ingredient: Any) -> str:
    if not isinstance(ingredient, dict):
        return ""
    raw_amount = ingredient.get("amount")
    if raw_amount:
        return readable_text(raw_amount)
    quantity = readable_text(ingredient.get("quantity"))
    unit = readable_text(ingredient.get("unit"))
    return f"{quantity} {unit}".strip()


def ingredient_line(ingredient: Any) -> str:
    name = ingredient_name(ingredient)
    amount = ingredient_amount(ingredient)
    return f"{name} ({amount})" if amount else name


def row_to_recipe(row: Any) -> RecipeGapRow:
    return RecipeGapRow(
        id=int(row["id"]),
        title=readable_text(row["title"]),
        calories_per_serving=row.get("calories_per_serving"),
        protein_g=row.get("protein_g"),
        fat_g=row.get("fat_g"),
        carbs_g=row.get("carbs_g"),
        ingredients=normalize_ingredients(row.get("ingredients")),
        servings=int(row["servings"]) if row.get("servings") else None,
        category=readable_text(row.get("category")),
        meal_type=readable_text(row.get("meal_type")),
        is_drink=bool(row.get("is_drink")),
        is_alcoholic=bool(row.get("is_alcoholic")),
        alcohol_percent=row.get("alcohol_percent"),
    )


def load_recipes_sqlalchemy(database_url: str) -> list[RecipeGapRow]:
    engine = create_engine(database_url)
    query = text(
        """
        SELECT
            id,
            title,
            calories_per_serving,
            protein_g,
            fat_g,
            carbs_g,
            ingredients,
            servings,
            category,
            meal_type,
            is_drink,
            is_alcoholic,
            alcohol_percent
        FROM recipes
        WHERE id = ANY(:ids)
        ORDER BY id
        """
    )
    with engine.connect() as conn:
        rows = list(conn.execute(query, {"ids": REMAINING_IDS}).mappings())
    return [row_to_recipe(row) for row in rows]


def docker_psql_json(sql: str) -> Any:
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
    return json.loads(result.stdout.strip() or "[]")


def load_recipes_docker() -> list[RecipeGapRow]:
    id_list = ", ".join(str(recipe_id) for recipe_id in REMAINING_IDS)
    sql = f"""
        SELECT COALESCE(json_agg(row_to_json(t) ORDER BY id), '[]'::json)
        FROM (
            SELECT
                id,
                title,
                calories_per_serving,
                protein_g,
                fat_g,
                carbs_g,
                ingredients,
                servings,
                category,
                meal_type,
                is_drink,
                is_alcoholic,
                alcohol_percent
            FROM recipes
            WHERE id IN ({id_list})
            ORDER BY id
        ) AS t;
        """
    return [row_to_recipe(row) for row in docker_psql_json(sql)]


def is_placeholder_recipe(recipe: RecipeGapRow) -> bool:
    if not recipe.ingredients:
        return True
    names = [normalize_text(ingredient_name(item)) for item in recipe.ingredients]
    if any(name in PLACEHOLDER_INGREDIENTS for name in names):
        return True
    real_names = [
        name
        for name in names
        if name and name not in NON_REAL_INGREDIENTS and name not in PLACEHOLDER_INGREDIENTS
    ]
    return not real_names


def is_alcohol(recipe: RecipeGapRow) -> bool:
    haystack = f"{recipe.title} {recipe.category} {recipe.meal_type}"
    normalized = normalize_text(haystack)
    if "безалког" in normalized and not recipe.is_alcoholic:
        return False
    return recipe.is_alcoholic or any(keyword in normalized for keyword in ALCOHOL_TITLE_KEYWORDS)


def is_beverage_or_drink(recipe: RecipeGapRow) -> bool:
    haystack = f"{recipe.title} {recipe.category} {recipe.meal_type}"
    normalized = normalize_text(haystack)
    return (
        recipe.is_drink
        or normalize_text(recipe.meal_type) in DRINK_MEAL_TYPES
        or normalize_text(recipe.category) in DRINK_CATEGORIES
        or any(keyword in normalized for keyword in DRINK_TITLE_KEYWORDS)
    )


def group_for(recipe: RecipeGapRow) -> str:
    if is_alcohol(recipe):
        return "D"
    if is_beverage_or_drink(recipe):
        return "B"
    if is_placeholder_recipe(recipe):
        return "C"
    return "A"


def fmt_value(value: float | int | None) -> str:
    return "NULL" if value is None else f"{float(value):.1f}"


def fmt_kbju(recipe: RecipeGapRow) -> str:
    return (
        f"{fmt_value(recipe.calories_per_serving)} / "
        f"{fmt_value(recipe.protein_g)} / "
        f"{fmt_value(recipe.fat_g)} / "
        f"{fmt_value(recipe.carbs_g)}"
    )


def fmt_inline(value: str) -> str:
    return value.replace("|", "\\|")


def recipe_detail_lines(recipe: RecipeGapRow) -> list[str]:
    ingredients = recipe.ingredients
    lines = [
        f"### #{recipe.id} {recipe.title}",
        "",
        f"- id: `{recipe.id}`",
        f"- title: `{recipe.title}`",
        f"- current КБЖУ: `{fmt_kbju(recipe)}`",
        f"- missing fields: `{', '.join(recipe.missing_nutrition_fields) or 'none'}`",
        f"- servings: `{recipe.servings if recipe.servings is not None else 'NULL'}`",
        f"- category: `{recipe.category}`",
        f"- meal_type: `{recipe.meal_type}`",
        f"- is_drink: `{recipe.is_drink}`",
        f"- is_alcoholic: `{recipe.is_alcoholic}`",
        f"- alcohol_percent: `{fmt_value(recipe.alcohol_percent)}`",
        "- ingredients:",
    ]
    if not ingredients:
        lines.append("  - `n/a`")
    else:
        for ingredient in ingredients:
            lines.append(f"  - {ingredient_line(ingredient)}")
    return lines


def build_report(recipes: list[RecipeGapRow], connection_note: str) -> str:
    found_ids = {recipe.id for recipe in recipes}
    missing_ids = [recipe_id for recipe_id in REMAINING_IDS if recipe_id not in found_ids]
    grouped: dict[str, list[RecipeGapRow]] = {key: [] for key in GROUP_STRATEGIES}
    for recipe in recipes:
        grouped[group_for(recipe)].append(recipe)

    lines = [
        "# Remaining Nutrition Gap Audit",
        "",
        "Scope: read-only audit for remaining recipes with incomplete nutrition data. No database changes, recipe updates, imports, migrations, or apply --commit were performed.",
        "",
        "## Summary",
        "",
        f"- Requested IDs: `{len(REMAINING_IDS)}`",
        f"- Recipes found: `{len(recipes)}`",
        f"- Missing requested IDs in DB: `{len(missing_ids)}`",
        f"- Database read method: `{connection_note}`",
        "- Current КБЖУ tuple format: `calories_per_serving / protein_g / fat_g / carbs_g`",
        "",
        "## Group Counts",
        "",
        "| Group | Name | Count | Strategy |",
        "| --- | --- | ---: | --- |",
    ]
    for key, (name, strategy) in GROUP_STRATEGIES.items():
        lines.append(f"| {key} | {name} | {len(grouped[key])} | {fmt_inline(strategy)} |")

    lines.extend(
        [
            "",
            "## Quick Index",
            "",
            "| ID | Title | Current КБЖУ | Missing fields | Servings | Category | Meal type | Group |",
            "| ---: | --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for recipe in recipes:
        group = group_for(recipe)
        group_name = GROUP_STRATEGIES[group][0]
        lines.append(
            f"| {recipe.id} | {fmt_inline(recipe.title)} | {fmt_kbju(recipe)} | "
            f"{', '.join(recipe.missing_nutrition_fields) or 'none'} | "
            f"{recipe.servings if recipe.servings is not None else 'NULL'} | "
            f"{fmt_inline(recipe.category)} | {fmt_inline(recipe.meal_type)} | "
            f"{group}: {group_name} |"
        )

    for key, (name, strategy) in GROUP_STRATEGIES.items():
        lines.extend(["", f"## Group {key}: {name}", "", f"Strategy: {strategy}", ""])
        if not grouped[key]:
            lines.append("- `n/a`")
            continue
        for recipe in grouped[key]:
            lines.extend(recipe_detail_lines(recipe))
            lines.append("")

    lines.extend(["", "## Missing Requested IDs", ""])
    if not missing_ids:
        lines.append("- `n/a`")
    else:
        lines.extend(f"- `{recipe_id}`" for recipe_id in missing_ids)

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    report_path = Path(args.report).expanduser().resolve()
    try:
        recipes = load_recipes_sqlalchemy(args.database_url)
        connection_note = "SQLAlchemy"
    except SQLAlchemyError as exc:
        print(
            "SQLAlchemy connection failed, falling back to docker compose psql: "
            f"{exc.__class__.__name__}"
        )
        recipes = load_recipes_docker()
        connection_note = "docker compose psql"

    report = build_report(recipes, connection_note)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    grouped_counts = {key: 0 for key in GROUP_STRATEGIES}
    for recipe in recipes:
        grouped_counts[group_for(recipe)] += 1
    print(f"Requested IDs: {len(REMAINING_IDS)}")
    print(f"Recipes found: {len(recipes)}")
    for key, count in grouped_counts.items():
        print(f"Group {key} ({GROUP_STRATEGIES[key][0]}): {count}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
