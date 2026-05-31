"""Read-only strategy audit for beverage nutrition gaps.

The script inspects beverage recipes 32-58, groups them by beverage type, and
writes a strategy report. It does not create update JSON or change the database.

Usage:
    python backend/scripts/audit_beverage_nutrition_strategy.py
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
DEFAULT_REPORT_PATH = ROOT / "reports" / "beverage_nutrition_strategy.md"
BEVERAGE_IDS = list(range(32, 59))

GROUPS = {
    "A": {
        "name": "Water-based drinks",
        "description": "лимонады, морсы, компоты, изотоники, фруктовые пунши",
        "strategy": "beverage rules",
        "auto_without_gpt": "partial",
        "auto_note": "Can estimate protein/fat as 0 and carbs from current calories for simple sugar/fruit drinks, but ingredient-specific macros need enrichment because source ingredients are placeholders.",
    },
    "B": {
        "name": "Smoothies",
        "description": "fruit/green/oat smoothies",
        "strategy": "AI enrichment",
        "auto_without_gpt": "no",
        "auto_note": "Smoothies need actual fruit/dairy/oat composition; placeholder `Основа напитка` is not enough for reliable protein/fat/carbs.",
    },
    "C": {
        "name": "Protein shakes",
        "description": "protein shakes and post-workout cocktails",
        "strategy": "AI enrichment",
        "auto_without_gpt": "no",
        "auto_note": "Protein shakes require protein powder amount/type and liquid base; current placeholder hides the macro driver.",
    },
    "D": {
        "name": "Coffee & tea",
        "description": "coffee, latte/cappuccino, tea",
        "strategy": "beverage rules",
        "auto_without_gpt": "partial",
        "auto_note": "Plain tea can be rule-based; milk coffee needs milk/sugar assumptions or enrichment to avoid wrong macros.",
    },
    "E": {
        "name": "Non-alcohol cocktails",
        "description": "non-alcohol cocktails and festive lemonades",
        "strategy": "beverage rules + AI enrichment",
        "auto_without_gpt": "partial",
        "auto_note": "Rules can handle alcohol=0 and rough sugar calories; recipe-specific mixers, syrups, and fruit need enrichment.",
    },
    "F": {
        "name": "Alcohol cocktails",
        "description": "alcoholic cocktails",
        "strategy": "beverage rules + alcohol_percent",
        "auto_without_gpt": "partial",
        "auto_note": "Can estimate with beverage/alcohol rules only after ABV and mixer assumptions are known; missing alcohol_percent blocks safe automatic fill.",
    },
}


@dataclass(frozen=True)
class BeverageRow:
    id: int
    title: str
    calories_per_serving: float | None
    ingredients: list[Any]
    servings: int | None
    category: str
    meal_type: str
    is_drink: bool
    is_alcoholic: bool
    alcohol_percent: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit beverage nutrition strategy")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown beverage strategy report",
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
    amount = ingredient.get("amount")
    if amount:
        return readable_text(amount)
    quantity = readable_text(ingredient.get("quantity"))
    unit = readable_text(ingredient.get("unit"))
    return f"{quantity} {unit}".strip()


def ingredient_line(ingredient: Any) -> str:
    name = ingredient_name(ingredient)
    amount = ingredient_amount(ingredient)
    return f"{name} ({amount})" if amount else name


def row_to_beverage(row: Any) -> BeverageRow:
    return BeverageRow(
        id=int(row["id"]),
        title=readable_text(row["title"]),
        calories_per_serving=row.get("calories_per_serving"),
        ingredients=normalize_ingredients(row.get("ingredients")),
        servings=int(row["servings"]) if row.get("servings") else None,
        category=readable_text(row.get("category")),
        meal_type=readable_text(row.get("meal_type")),
        is_drink=bool(row.get("is_drink")),
        is_alcoholic=bool(row.get("is_alcoholic")),
        alcohol_percent=row.get("alcohol_percent"),
    )


def load_beverages_sqlalchemy(database_url: str) -> list[BeverageRow]:
    engine = create_engine(database_url)
    query = text(
        """
        SELECT
            id,
            title,
            calories_per_serving,
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
        rows = list(conn.execute(query, {"ids": BEVERAGE_IDS}).mappings())
    return [row_to_beverage(row) for row in rows]


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


def load_beverages_docker() -> list[BeverageRow]:
    id_list = ", ".join(str(recipe_id) for recipe_id in BEVERAGE_IDS)
    sql = f"""
        SELECT COALESCE(json_agg(row_to_json(t) ORDER BY id), '[]'::json)
        FROM (
            SELECT
                id,
                title,
                calories_per_serving,
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
    return [row_to_beverage(row) for row in docker_psql_json(sql)]


def has_placeholder_ingredients(beverage: BeverageRow) -> bool:
    names = {normalize_text(ingredient_name(item)) for item in beverage.ingredients}
    return "основа напитка" in names or "основной продукт" in names


def group_for(beverage: BeverageRow) -> str:
    title = normalize_text(beverage.title)
    meal_type = normalize_text(beverage.meal_type)
    if beverage.is_alcoholic:
        return "F"
    if meal_type == "protein_shake" or "протеин" in title or "после тренировки" in title:
        return "C"
    if meal_type == "smoothie" or "смузи" in title:
        return "B"
    if meal_type in {"coffee", "tea"} or "кофе" in title or "латте" in title or "капучино" in title or "чай" in title or "какао" in title:
        return "D"
    if meal_type == "cocktail" or "мохито" in title or "коктей" in title or "эль" in title:
        return "E"
    return "A"


def fmt_value(value: float | int | None) -> str:
    return "NULL" if value is None else f"{float(value):.1f}"


def fmt_inline(value: str) -> str:
    return value.replace("|", "\\|")


def ingredients_text(beverage: BeverageRow) -> str:
    if not beverage.ingredients:
        return "n/a"
    return "; ".join(ingredient_line(item) for item in beverage.ingredients)


def build_report(beverages: list[BeverageRow], connection_note: str) -> str:
    found_ids = {item.id for item in beverages}
    missing_ids = [recipe_id for recipe_id in BEVERAGE_IDS if recipe_id not in found_ids]
    grouped: dict[str, list[BeverageRow]] = {key: [] for key in GROUPS}
    for beverage in beverages:
        grouped[group_for(beverage)].append(beverage)

    placeholder_count = sum(has_placeholder_ingredients(item) for item in beverages)
    lines = [
        "# Beverage Nutrition Strategy",
        "",
        "Scope: read-only strategy audit for beverage recipes 32-58. No database changes, update JSON files, migrations, or commits were performed.",
        "",
        "## Summary",
        "",
        f"- Requested beverage IDs: `{len(BEVERAGE_IDS)}`",
        f"- Beverages found: `{len(beverages)}`",
        f"- Missing requested IDs in DB: `{len(missing_ids)}`",
        f"- Database read method: `{connection_note}`",
        f"- Beverages with placeholder ingredient `Основа напитка`: `{placeholder_count}`",
        "- Key finding: current ingredient lists are placeholders, so the normal ingredient engine cannot calculate reliable BЖУ without enrichment.",
        "",
        "## Group Strategy",
        "",
        "| Group | Name | Count | Proposed method | Auto BЖУ without GPT? | Note |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for key, meta in GROUPS.items():
        lines.append(
            f"| {key} | {meta['name']} | {len(grouped[key])} | "
            f"{meta['strategy']} | {meta['auto_without_gpt']} | {fmt_inline(meta['auto_note'])} |"
        )

    lines.extend(
        [
            "",
            "## Beverage Index",
            "",
            "| ID | Title | Current calories | Ingredients | Servings | Category | Meal type | Group |",
            "| ---: | --- | ---: | --- | ---: | --- | --- | --- |",
        ]
    )
    for beverage in beverages:
        group = group_for(beverage)
        lines.append(
            f"| {beverage.id} | {fmt_inline(beverage.title)} | "
            f"{fmt_value(beverage.calories_per_serving)} | "
            f"{fmt_inline(ingredients_text(beverage))} | "
            f"{beverage.servings if beverage.servings is not None else 'NULL'} | "
            f"{fmt_inline(beverage.category)} | {fmt_inline(beverage.meal_type)} | "
            f"{group}: {GROUPS[group]['name']} |"
        )

    for key, meta in GROUPS.items():
        lines.extend(["", f"## Group {key}: {meta['name']}", "", f"Description: {meta['description']}", f"Proposed method: {meta['strategy']}", f"Auto BЖУ without GPT: {meta['auto_without_gpt']}", f"Strategy note: {meta['auto_note']}", ""])
        if not grouped[key]:
            lines.append("- `n/a`")
            continue
        lines.extend(
            [
                "| ID | Title | Current calories | Ingredients | Servings | Category | Meal type |",
                "| ---: | --- | ---: | --- | ---: | --- | --- |",
            ]
        )
        for beverage in grouped[key]:
            lines.append(
                f"| {beverage.id} | {fmt_inline(beverage.title)} | "
                f"{fmt_value(beverage.calories_per_serving)} | "
                f"{fmt_inline(ingredients_text(beverage))} | "
                f"{beverage.servings if beverage.servings is not None else 'NULL'} | "
                f"{fmt_inline(beverage.category)} | {fmt_inline(beverage.meal_type)} |"
            )

    lines.extend(["", "## Automatic Calculation Without GPT", ""])
    lines.extend(
        [
            "| Group | Can calculate BЖУ for whole group without GPT? | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for key, meta in GROUPS.items():
        lines.append(f"| {key}: {meta['name']} | {meta['auto_without_gpt']} | {fmt_inline(meta['auto_note'])} |")

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
        beverages = load_beverages_sqlalchemy(args.database_url)
        connection_note = "SQLAlchemy"
    except SQLAlchemyError as exc:
        print(
            "SQLAlchemy connection failed, falling back to docker compose psql: "
            f"{exc.__class__.__name__}"
        )
        beverages = load_beverages_docker()
        connection_note = "docker compose psql"

    report = build_report(beverages, connection_note)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    grouped_counts = {key: 0 for key in GROUPS}
    for beverage in beverages:
        grouped_counts[group_for(beverage)] += 1
    print(f"Requested beverage IDs: {len(BEVERAGE_IDS)}")
    print(f"Beverages found: {len(beverages)}")
    for key, count in grouped_counts.items():
        print(f"Group {key} ({GROUPS[key]['name']}): {count}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
