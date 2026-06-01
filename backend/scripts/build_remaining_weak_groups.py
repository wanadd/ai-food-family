#!/usr/bin/env python3
"""Build final groups for remaining V2 weak recipe steps.

Reads current recipes, applies the V2 steps audit, groups the remaining weak
recipes, and exports real food recipes for a future enrichment batch. It does
not update the database and does not call AI.

Usage:
    python backend/scripts/build_remaining_weak_groups.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
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
    fmt_inline,
    format_steps,
    normalize_steps,
    normalize_text,
    readable_text,
)
from audit_recipe_steps_v2 import audit_recipe_v2


DEFAULT_REPORT_PATH = ROOT / "reports" / "remaining_weak_groups.md"
DEFAULT_EXPORT_PATH = ROOT / "exports" / "remaining_real_recipe_steps_batch.json"

BEVERAGE_KEYWORDS = (
    "лимонад",
    "морс",
    "компот",
    "смузи",
    "коктей",
    "кофе",
    "капучино",
    "латте",
    "чай",
    "напит",
    "мохито",
    "пунш",
    "какао",
    "фреш",
    "изотоник",
    "глинтвейн",
    "эль",
)

GROUPS = {
    "A": "Beverage recipes",
    "B": "Real food recipes",
    "C": "Other",
}


@dataclass(frozen=True)
class RecipeFullRow:
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
    parser = argparse.ArgumentParser(description="Build remaining weak recipe groups")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown remaining weak groups report",
    )
    parser.add_argument(
        "--export",
        default=str(DEFAULT_EXPORT_PATH),
        help="Path to JSON export for real food recipes",
    )
    return parser.parse_args()


def normalize_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def normalize_tags(value: Any) -> list[str]:
    return [readable_text(item) for item in normalize_list(value) if readable_text(item)]


def row_to_recipe(row: Any) -> RecipeFullRow:
    return RecipeFullRow(
        id=int(row["id"]),
        title=readable_text(row.get("title")),
        description=readable_text(row.get("description")),
        ingredients=normalize_list(row.get("ingredients")),
        steps=normalize_steps(row.get("steps")),
        category=readable_text(row.get("category")),
        meal_type=readable_text(row.get("meal_type")),
        tags=normalize_tags(row.get("tags")),
        is_drink=bool(row.get("is_drink")),
        is_alcoholic=bool(row.get("is_alcoholic")),
    )


def load_recipes_sqlalchemy(database_url: str) -> list[RecipeFullRow]:
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


def load_recipes_docker() -> list[RecipeFullRow]:
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


def combined_text(recipe: RecipeFullRow) -> str:
    values = [recipe.title, recipe.category, recipe.meal_type, *recipe.tags]
    return " ".join(normalize_text(value) for value in values if value)


def contains_keyword(text_value: str, keyword: str) -> bool:
    if keyword == "морс":
        pattern = r"(?<![а-яa-z0-9])морс(а|ы|ом|ов|овый|овая|овое|ые)?(?![а-яa-z0-9])"
    else:
        pattern = rf"(?<![а-яa-z0-9]){re.escape(keyword)}[а-яa-z]*(?![а-яa-z0-9])"
    return bool(re.search(pattern, text_value))


def is_beverage(recipe: RecipeFullRow) -> bool:
    text_value = combined_text(recipe)
    return (
        recipe.is_drink
        or recipe.is_alcoholic
        or recipe.category == "drink"
        or recipe.meal_type
        in {"drink", "smoothie", "protein_shake", "coffee", "tea", "cocktail"}
        or any(contains_keyword(text_value, keyword) for keyword in BEVERAGE_KEYWORDS)
    )


def is_other(recipe: RecipeFullRow) -> bool:
    title = normalize_text(recipe.title)
    category = normalize_text(recipe.category)
    if category in {"event"}:
        return True
    return "основной продукт" in title or "ассорти" in title


def group_for(recipe: RecipeFullRow) -> str:
    if is_beverage(recipe):
        return "A"
    if is_other(recipe):
        return "C"
    return "B"


def recipe_steps_row(recipe: RecipeFullRow) -> RecipeStepsRow:
    return RecipeStepsRow(id=recipe.id, title=recipe.title, steps=recipe.steps)


def remaining_weak_groups(
    recipes: list[RecipeFullRow],
) -> dict[str, list[tuple[RecipeFullRow, Any]]]:
    groups: dict[str, list[tuple[RecipeFullRow, Any]]] = {key: [] for key in GROUPS}
    for recipe in recipes:
        base = recipe_steps_row(recipe)
        old = audit_recipe(base)
        new = audit_recipe_v2(base, old)
        if new.group != "B":
            continue
        groups[group_for(recipe)].append((recipe, new))
    for records in groups.values():
        records.sort(key=lambda item: (item[0].id, item[0].title))
    return groups


def export_record(recipe: RecipeFullRow) -> dict[str, Any]:
    return {
        "id": recipe.id,
        "title": recipe.title,
        "description": recipe.description,
        "ingredients": recipe.ingredients,
        "steps": recipe.steps,
        "category": recipe.category,
    }


def build_report(
    recipes: list[RecipeFullRow],
    groups: dict[str, list[tuple[RecipeFullRow, Any]]],
    export_path: Path,
    connection_note: str,
) -> str:
    total_weak = sum(len(records) for records in groups.values())
    lines = [
        "# Remaining Weak Groups",
        "",
        "Scope: read-only classification of remaining V2 weak recipe steps. No database changes, recipe updates, commits, or AI calls were performed.",
        "",
        "## Summary",
        "",
        f"- Total recipes scanned: `{len(recipes)}`",
        f"- Remaining weak count: `{total_weak}`",
        f"- Beverage count: `{len(groups['A'])}`",
        f"- Real recipe count: `{len(groups['B'])}`",
        f"- Other count: `{len(groups['C'])}`",
        f"- Real recipe export: `{export_path}`",
        f"- Database read method: `{connection_note}`",
    ]

    for group, name in GROUPS.items():
        lines.extend(
            [
                "",
                f"## {group}. {name}",
                "",
                "| ID | Title | Steps count | Steps |",
                "| ---: | --- | ---: | --- |",
            ]
        )
        records = groups[group]
        if not records:
            lines.append("| n/a | n/a | n/a | n/a |")
            continue
        for recipe, result in records:
            lines.append(
                f"| {recipe.id} | {fmt_inline(recipe.title)} | "
                f"{result.steps_count} | {format_steps(recipe.steps)} |"
            )

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    report_path = Path(args.report).expanduser().resolve()
    export_path = Path(args.export).expanduser().resolve()
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

    groups = remaining_weak_groups(recipes)
    export_records = [export_record(recipe) for recipe, _result in groups["B"]]
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(
        json.dumps(export_records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = build_report(recipes, groups, export_path, connection_note)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"Remaining weak count: {sum(len(records) for records in groups.values())}")
    print(f"Beverage count: {len(groups['A'])}")
    print(f"Real recipe count: {len(groups['B'])}")
    print(f"Other count: {len(groups['C'])}")
    print(f"Wrote export: {export_path}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
