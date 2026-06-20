#!/usr/bin/env python3
"""Build a read-only steps enrichment batch for holiday and kids weak recipes.

The script uses the current recipes table and the same remediation categories as
the weak steps audit. It writes export/report files only; it does not update the
database and does not call AI.

Usage:
    python backend/scripts/build_holiday_kids_steps_batch.py
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

from audit_recipe_steps_quality import (
    DEFAULT_DATABASE_URL,
    ROOT,
    RecipeStepsRow,
    audit_recipe,
    normalize_steps,
    readable_text,
)
from audit_weak_steps_remediation import remediation_category


DEFAULT_OUTPUT_PATH = ROOT / "exports" / "holiday_kids_steps_batch_12.json"
DEFAULT_REPORT_PATH = ROOT / "reports" / "holiday_kids_steps_batch_12.md"
TARGET_CATEGORIES = {"B": "holiday", "C": "kids"}
EXPECTED_COUNT = 12


@dataclass(frozen=True)
class RecipeBatchRow:
    id: int
    title: str
    description: str
    ingredients: list[Any]
    steps: list[str]
    category: str
    meal_type: str
    tags: list[str]
    is_drink: bool
    is_alcoholic: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build holiday/kids steps batch")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to JSON batch export",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown batch report",
    )
    return parser.parse_args()


def normalize_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def row_to_recipe(row: Any) -> RecipeBatchRow:
    return RecipeBatchRow(
        id=int(row["id"]),
        title=readable_text(row.get("title")),
        description=readable_text(row.get("description")),
        ingredients=normalize_list(row.get("ingredients")),
        steps=normalize_steps(row.get("steps")),
        category=readable_text(row.get("category")),
        meal_type=readable_text(row.get("meal_type")),
        tags=[readable_text(item) for item in normalize_list(row.get("tags"))],
        is_drink=bool(row.get("is_drink")),
        is_alcoholic=bool(row.get("is_alcoholic")),
    )


def load_recipes_sqlalchemy(database_url: str) -> list[RecipeBatchRow]:
    engine = create_engine(database_url)
    query = text(
        """
        SELECT
            id,
            title,
            description,
            ingredients,
            steps,
            category,
            meal_type,
            tags,
            is_drink,
            is_alcoholic
        FROM recipes
        ORDER BY id
        """
    )
    with engine.connect() as conn:
        rows = list(conn.execute(query).mappings())
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


def load_recipes_docker() -> list[RecipeBatchRow]:
    sql = """
        SELECT COALESCE(json_agg(row_to_json(t) ORDER BY id), '[]'::json)
        FROM (
            SELECT
                id,
                title,
                description,
                ingredients,
                steps,
                category,
                meal_type,
                tags,
                is_drink,
                is_alcoholic
            FROM recipes
            ORDER BY id
        ) AS t;
        """
    return [row_to_recipe(row) for row in docker_psql_json(sql)]


def select_batch(recipes: list[RecipeBatchRow]) -> list[tuple[str, RecipeBatchRow]]:
    selected: list[tuple[str, RecipeBatchRow]] = []
    for recipe in recipes:
        quality = audit_recipe(RecipeStepsRow(id=recipe.id, title=recipe.title, steps=recipe.steps))
        if quality.group != "B":
            continue
        category_key = remediation_category(recipe)
        if category_key in TARGET_CATEGORIES:
            selected.append((TARGET_CATEGORIES[category_key], recipe))
    selected.sort(key=lambda item: (0 if item[0] == "holiday" else 1, item[1].id))
    return selected


def export_record(recipe: RecipeBatchRow) -> dict[str, Any]:
    return {
        "id": recipe.id,
        "title": recipe.title,
        "description": recipe.description,
        "ingredients": recipe.ingredients,
        "steps": recipe.steps,
        "category": recipe.category,
    }


def build_report(selected: list[tuple[str, RecipeBatchRow]], output_path: Path, connection_note: str) -> str:
    holiday = [recipe for group, recipe in selected if group == "holiday"]
    kids = [recipe for group, recipe in selected if group == "kids"]
    lines = [
        "# Holiday & Kids Steps Batch",
        "",
        "Scope: read-only export for steps enrichment. No database changes, recipe updates, commits, or AI calls were performed.",
        "",
        "## Summary",
        "",
        f"- Export: `{output_path}`",
        f"- Total records: `{len(selected)}`",
        f"- Holiday count: `{len(holiday)}`",
        f"- Kids count: `{len(kids)}`",
        f"- Expected records: `{EXPECTED_COUNT}`",
        f"- Database read method: `{connection_note}`",
        "",
        "## IDs",
        "",
        "- " + ", ".join(str(recipe.id) for _group, recipe in selected),
        "",
        "## Titles",
        "",
    ]
    for group, recipe in selected:
        lines.append(f"- `{recipe.id}` {recipe.title} ({group})")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
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

    selected = select_batch(recipes)
    output_records = [export_record(recipe) for _group, recipe in selected]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output_records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = build_report(selected, output_path, connection_note)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    holiday_count = sum(group == "holiday" for group, _recipe in selected)
    kids_count = sum(group == "kids" for group, _recipe in selected)
    print(f"Total records: {len(selected)}")
    print(f"Holiday count: {holiday_count}")
    print(f"Kids count: {kids_count}")
    print(f"IDs: {', '.join(str(recipe.id) for _group, recipe in selected)}")
    print(f"Wrote export: {output_path}")
    print(f"Wrote report: {report_path}")
    return 0 if len(selected) == EXPECTED_COUNT else 1


if __name__ == "__main__":
    raise SystemExit(main())
