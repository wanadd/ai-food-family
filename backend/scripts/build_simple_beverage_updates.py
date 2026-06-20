"""Build rule-based nutrition updates for simple beverage recipes.

This is a read-only builder. It reads selected simple beverage recipes from the
database, derives macros from current calories, and writes JSON/report artifacts.
It does not update the database.

Rule:
    protein_g = 0
    fat_g = 0
    carbs_g = round(calories_per_serving / 4, 1)
    alcohol_percent = null

Usage:
    python backend/scripts/build_simple_beverage_updates.py
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
DEFAULT_OUTPUT_PATH = ROOT / "exports" / "simple_beverage_nutrition_updates.json"
DEFAULT_REPORT_PATH = ROOT / "reports" / "simple_beverage_nutrition_updates_report.md"
SIMPLE_BEVERAGE_IDS = [32, 33, 34, 35, 36, 44, 49, 52]
SOURCE = "simple_beverage_rules_v1"


@dataclass(frozen=True)
class BeverageRow:
    id: int
    title: str
    calories_per_serving: float
    protein_g: float | None
    fat_g: float | None
    carbs_g: float | None
    alcohol_percent: float | None
    ingredients: list[Any]
    servings: int | None
    category: str
    meal_type: str
    is_drink: bool
    is_alcoholic: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build simple beverage nutrition updates")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to output JSON update array",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown report",
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


def normalize_ingredients(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def row_to_beverage(row: Any) -> BeverageRow:
    calories = row.get("calories_per_serving")
    if calories is None:
        raise ValueError(f"recipe_{row.get('id')}_missing_calories_per_serving")
    return BeverageRow(
        id=int(row["id"]),
        title=readable_text(row["title"]),
        calories_per_serving=float(calories),
        protein_g=row.get("protein_g"),
        fat_g=row.get("fat_g"),
        carbs_g=row.get("carbs_g"),
        alcohol_percent=row.get("alcohol_percent"),
        ingredients=normalize_ingredients(row.get("ingredients")),
        servings=int(row["servings"]) if row.get("servings") else None,
        category=readable_text(row.get("category")),
        meal_type=readable_text(row.get("meal_type")),
        is_drink=bool(row.get("is_drink")),
        is_alcoholic=bool(row.get("is_alcoholic")),
    )


def load_beverages_sqlalchemy(database_url: str) -> list[BeverageRow]:
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
            alcohol_percent,
            ingredients,
            servings,
            category,
            meal_type,
            is_drink,
            is_alcoholic
        FROM recipes
        WHERE id = ANY(:ids)
        ORDER BY id
        """
    )
    with engine.connect() as conn:
        rows = list(conn.execute(query, {"ids": SIMPLE_BEVERAGE_IDS}).mappings())
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
    id_list = ", ".join(str(recipe_id) for recipe_id in SIMPLE_BEVERAGE_IDS)
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
                alcohol_percent,
                ingredients,
                servings,
                category,
                meal_type,
                is_drink,
                is_alcoholic
            FROM recipes
            WHERE id IN ({id_list})
            ORDER BY id
        ) AS t;
        """
    return [row_to_beverage(row) for row in docker_psql_json(sql)]


def build_update(beverage: BeverageRow) -> dict[str, Any]:
    return {
        "id": beverage.id,
        "title": beverage.title,
        "calories_per_serving": round(beverage.calories_per_serving, 1),
        "protein_g": 0,
        "fat_g": 0,
        "carbs_g": round(beverage.calories_per_serving / 4, 1),
        "alcohol_percent": None,
        "source": SOURCE,
    }


def fmt_value(value: float | int | None) -> str:
    return "NULL" if value is None else f"{float(value):.1f}"


def fmt_kbju(values: dict[str, Any] | BeverageRow) -> str:
    if isinstance(values, BeverageRow):
        calories = values.calories_per_serving
        protein = values.protein_g
        fat = values.fat_g
        carbs = values.carbs_g
    else:
        calories = values["calories_per_serving"]
        protein = values["protein_g"]
        fat = values["fat_g"]
        carbs = values["carbs_g"]
    return (
        f"{fmt_value(calories)} / {fmt_value(protein)} / "
        f"{fmt_value(fat)} / {fmt_value(carbs)}"
    )


def fmt_inline(value: str) -> str:
    return value.replace("|", "\\|")


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


def ingredients_text(beverage: BeverageRow) -> str:
    parts = []
    for ingredient in beverage.ingredients:
        name = ingredient_name(ingredient)
        amount = ingredient_amount(ingredient)
        parts.append(f"{name} ({amount})" if amount else name)
    return "; ".join(parts) if parts else "n/a"


def build_report(
    beverages: list[BeverageRow],
    records: list[dict[str, Any]],
    output_path: Path,
    connection_note: str,
    missing_ids: list[int],
) -> str:
    record_by_id = {int(record["id"]): record for record in records}
    lines = [
        "# Simple Beverage Nutrition Updates Report",
        "",
        "Scope: read-only rule-based update build for simple beverage recipes. No database changes, migrations, or apply --commit were performed.",
        "",
        "## Summary",
        "",
        f"- Database read method: `{connection_note}`",
        f"- Requested IDs: `{', '.join(str(item) for item in SIMPLE_BEVERAGE_IDS)}`",
        f"- Records written: `{len(records)}`",
        f"- Missing requested IDs: `{len(missing_ids)}`",
        f"- Output JSON: `{output_path.relative_to(ROOT)}`",
        f"- Source marker: `{SOURCE}`",
        "- Rule: `protein_g=0`, `fat_g=0`, `carbs_g=round(calories_per_serving / 4, 1)`, `alcohol_percent=null`.",
        "- Scope guard: smoothies, protein shakes, milk coffee, and alcohol are excluded.",
        "",
        "## Current To New",
        "",
        "| ID | Title | Current KБЖУ | New KБЖУ | Ingredients | Servings | Category | Meal type | Reason why safe |",
        "| ---: | --- | ---: | ---: | --- | ---: | --- | --- | --- |",
    ]
    for beverage in beverages:
        record = record_by_id[beverage.id]
        lines.append(
            f"| {beverage.id} | {fmt_inline(beverage.title)} | {fmt_kbju(beverage)} | "
            f"{fmt_kbju(record)} | {fmt_inline(ingredients_text(beverage))} | "
            f"{beverage.servings if beverage.servings is not None else 'NULL'} | "
            f"{fmt_inline(beverage.category)} | {fmt_inline(beverage.meal_type)} | "
            "simple non-alcohol placeholder beverage; current calories retained and carbs derived by 4 kcal/g |"
        )

    lines.extend(["", "## Missing Requested IDs", ""])
    if not missing_ids:
        lines.append("- `n/a`")
    else:
        lines.extend(f"- `{recipe_id}`" for recipe_id in missing_ids)

    lines.extend(
        [
            "",
            "## Dry Run",
            "",
            "- Command: `python backend/scripts/apply_calculated_nutrition_updates.py --input exports/simple_beverage_nutrition_updates.json --dry-run`",
            "- Result: pending until dry-run is executed.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
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

    found_ids = {beverage.id for beverage in beverages}
    missing_ids = [recipe_id for recipe_id in SIMPLE_BEVERAGE_IDS if recipe_id not in found_ids]
    records = [build_update(beverage) for beverage in beverages]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = build_report(beverages, records, output_path, connection_note, missing_ids)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"Records written: {len(records)}")
    print(f"Missing requested IDs: {len(missing_ids)}")
    print(f"Wrote JSON: {output_path}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
