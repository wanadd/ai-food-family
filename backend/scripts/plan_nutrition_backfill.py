#!/usr/bin/env python3
"""Build a read-only nutrition backfill plan for recipes.

This script prepares JSONL input for a future AI pass. It does not call AI,
write to the database, import recipes, or recalculate nutrition locally.

Run from the repository root:
    python backend/scripts/plan_nutrition_backfill.py
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
DEFAULT_OUTPUT_PATH = ROOT / "exports" / "nutrition_backfill_input.jsonl"
DEFAULT_REPORT_PATH = ROOT / "reports" / "nutrition_backfill_plan.md"

REQUIRED_OUTPUT_SCHEMA = {
    "calories_per_serving": "number",
    "protein_g": "number",
    "fat_g": "number",
    "carbs_g": "number",
    "alcohol_percent": "number|null",
    "confidence": ["low", "medium", "high"],
    "notes": "string",
}


@dataclass(frozen=True)
class RecipeNutritionRow:
    id: int
    title: str
    description: str
    ingredients: list[Any]
    calories_per_serving: float | None
    protein_g: float | None
    fat_g: float | None
    carbs_g: float | None
    is_alcoholic: bool
    alcohol_percent: float | None
    source_type: str | None

    @property
    def missing_nutrition_fields(self) -> list[str]:
        fields = [
            ("calories_per_serving", self.calories_per_serving),
            ("protein_g", self.protein_g),
            ("fat_g", self.fat_g),
            ("carbs_g", self.carbs_g),
        ]
        return [name for name, value in fields if value is None]

    @property
    def needs_alcohol_percent(self) -> bool:
        return self.is_alcoholic and self.alcohol_percent is None

    @property
    def needs_backfill(self) -> bool:
        return bool(self.missing_nutrition_fields) or self.needs_alcohol_percent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan nutrition backfill")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to JSONL nutrition backfill input",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown nutrition backfill plan",
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


def load_recipes(database_url: str) -> list[RecipeNutritionRow]:
    engine = create_engine(database_url)
    query = text(
        """
        SELECT
            id,
            title,
            description,
            ingredients,
            calories_per_serving,
            protein_g,
            fat_g,
            carbs_g,
            is_alcoholic,
            alcohol_percent,
            source_type
        FROM recipes
        ORDER BY id
        """
    )
    with engine.connect() as conn:
        rows = list(conn.execute(query).mappings())
    return rows_to_recipes(rows)


def load_recipes_via_docker() -> list[RecipeNutritionRow]:
    sql = """
        SELECT COALESCE(json_agg(row_to_json(t) ORDER BY id), '[]'::json)
        FROM (
            SELECT
                id,
                title,
                description,
                ingredients,
                calories_per_serving,
                protein_g,
                fat_g,
                carbs_g,
                is_alcoholic,
                alcohol_percent,
                source_type
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


def rows_to_recipes(rows: Any) -> list[RecipeNutritionRow]:
    recipes: list[RecipeNutritionRow] = []
    for row in rows:
        recipes.append(
            RecipeNutritionRow(
                id=int(row["id"]),
                title=readable_text(row["title"]),
                description=readable_text(row["description"]),
                ingredients=normalize_ingredients(row.get("ingredients")),
                calories_per_serving=row.get("calories_per_serving"),
                protein_g=row.get("protein_g"),
                fat_g=row.get("fat_g"),
                carbs_g=row.get("carbs_g"),
                is_alcoholic=bool(row.get("is_alcoholic")),
                alcohol_percent=row.get("alcohol_percent"),
                source_type=row.get("source_type"),
            )
        )
    return recipes


def build_backfill_record(recipe: RecipeNutritionRow) -> dict[str, Any]:
    return {
        "id": recipe.id,
        "title": recipe.title,
        "description": recipe.description,
        "ingredients": recipe.ingredients,
        "current": {
            "calories_per_serving": recipe.calories_per_serving,
            "protein_g": recipe.protein_g,
            "fat_g": recipe.fat_g,
            "carbs_g": recipe.carbs_g,
        },
        "is_alcoholic": recipe.is_alcoholic,
        "current_alcohol_percent": recipe.alcohol_percent,
        "required_output_schema": REQUIRED_OUTPUT_SCHEMA,
        "rules": {
            "missing_macros": "Return 0, not null, for missing protein_g/fat_g/carbs_g.",
            "missing_calories": "Return 0, not null, if calories are unknown.",
            "non_alcoholic": "Return alcohol_percent=null for non-alcoholic recipes.",
            "alcoholic": "Estimate alcohol_percent for alcoholic recipes.",
        },
    }


def write_jsonl(path: Path, recipes: list[RecipeNutritionRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for recipe in recipes:
            handle.write(
                json.dumps(build_backfill_record(recipe), ensure_ascii=False) + "\n"
            )


def build_report(
    all_recipes: list[RecipeNutritionRow],
    target_recipes: list[RecipeNutritionRow],
    output_path: Path,
) -> str:
    missing_counts = {
        "calories_per_serving": sum(
            recipe.calories_per_serving is None for recipe in all_recipes
        ),
        "protein_g": sum(recipe.protein_g is None for recipe in all_recipes),
        "fat_g": sum(recipe.fat_g is None for recipe in all_recipes),
        "carbs_g": sum(recipe.carbs_g is None for recipe in all_recipes),
    }
    all_nutrition_null = sum(
        recipe.calories_per_serving is None
        and recipe.protein_g is None
        and recipe.fat_g is None
        and recipe.carbs_g is None
        for recipe in all_recipes
    )
    alcohol_missing = [
        recipe for recipe in all_recipes if recipe.needs_alcohol_percent
    ]

    lines = [
        "# Nutrition Backfill Plan",
        "",
        "## Summary",
        "",
        f"- Total recipes: `{len(all_recipes)}`",
        f"- Recipes selected for backfill: `{len(target_recipes)}`",
        f"- Recipes with all four nutrition fields NULL: `{all_nutrition_null}`",
        f"- Alcoholic recipes missing alcohol_percent: `{len(alcohol_missing)}`",
        f"- JSONL output: `{output_path}`",
        "- Mode: `read-only plan`",
        "",
        "## Missing Field Counts",
        "",
        "| Field | Missing |",
        "|---|---:|",
    ]
    for field, count in missing_counts.items():
        lines.append(f"| {field} | {count} |")

    lines.extend(
        [
            "",
            "## Output Rules",
            "",
            "- If protein/fat/carbs are unavailable, AI must return `0`, not `null`.",
            "- If calories are unavailable, AI must return `0`, not `null`.",
            "- If recipe is not alcoholic, AI must return `alcohol_percent=null`.",
            "- If recipe is alcoholic, AI must estimate `alcohol_percent`.",
            "",
            "## Selected Recipes",
            "",
        ]
    )

    if not target_recipes:
        lines.append("- `n/a`")
    else:
        for recipe in target_recipes:
            missing = ", ".join(recipe.missing_nutrition_fields) or "none"
            alcohol_note = (
                ", needs alcohol_percent"
                if recipe.needs_alcohol_percent
                else ""
            )
            lines.append(
                f"- `#{recipe.id}` {recipe.title} "
                f"(missing: {missing}{alcohol_note}, source_type={recipe.source_type or 'n/a'})"
            )

    lines.extend(["", "## JSONL Example", ""])
    if target_recipes:
        lines.append("```json")
        lines.append(json.dumps(build_backfill_record(target_recipes[0]), ensure_ascii=False))
        lines.append("```")
    else:
        lines.append("- `n/a`")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()

    try:
        recipes = load_recipes(args.database_url)
        connection_note = "sqlalchemy"
    except SQLAlchemyError as exc:
        print(
            "SQLAlchemy connection failed, falling back to docker compose psql: "
            f"{exc.__class__.__name__}"
        )
        recipes = load_recipes_via_docker()
        connection_note = "docker compose psql"
    target_recipes = [recipe for recipe in recipes if recipe.needs_backfill]
    write_jsonl(output_path, target_recipes)

    report = build_report(recipes, target_recipes, output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"Total recipes: {len(recipes)}")
    print(f"Selected for backfill: {len(target_recipes)}")
    print(f"Read connection: {connection_note}")
    print(
        "Alcoholic missing alcohol_percent: "
        f"{sum(recipe.needs_alcohol_percent for recipe in recipes)}"
    )
    print(f"JSONL written to: {output_path}")
    print(f"Report written to: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
