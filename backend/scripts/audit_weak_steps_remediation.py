#!/usr/bin/env python3
"""Read-only remediation audit for recipes classified as weak_steps.

The script reads current recipes, reuses the existing steps quality rules, and
groups weak recipes into practical remediation buckets. It does not update the
database and does not call AI.

Usage:
    python backend/scripts/audit_weak_steps_remediation.py
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


DEFAULT_REPORT_PATH = ROOT / "reports" / "weak_steps_remediation_plan.md"

CATEGORIES = {
    "A": {
        "name": "Beverage recipes",
        "description": "лимонады, морсы, смузи, коктейли, кофе, чай",
    },
    "B": {
        "name": "Holiday recipes",
        "description": "праздничные блюда",
    },
    "C": {
        "name": "Kids recipes",
        "description": "детские блюда",
    },
    "D": {
        "name": "Real recipes with only 2-3 steps",
        "description": "реальные рецепты, где шаги слишком сжаты",
    },
    "E": {
        "name": "Real recipes with good steps but false-positive audit",
        "description": "рецепты, попавшие в weak_steps из-за эвристик качества",
    },
}

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
)
HOLIDAY_KEYWORDS = (
    "празднич",
    "новогод",
    "рождествен",
    "пасх",
    "день рождения",
    "юбилей",
    "торт",
    "кулич",
)
KIDS_KEYWORDS = (
    "детск",
    "детям",
    "ребен",
    "ребён",
    "малыш",
    "школь",
)


@dataclass(frozen=True)
class RecipeMetaRow:
    id: int
    title: str
    steps: list[str]
    category: str
    meal_type: str
    tags: list[str]
    is_drink: bool
    is_alcoholic: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit weak steps remediation groups")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown weak steps remediation report",
    )
    return parser.parse_args()


def normalize_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [readable_text(item) for item in value if readable_text(item)]
    return []


def row_to_recipe(row: Any) -> RecipeMetaRow:
    return RecipeMetaRow(
        id=int(row["id"]),
        title=readable_text(row.get("title")),
        steps=normalize_steps(row.get("steps")),
        category=readable_text(row.get("category")),
        meal_type=readable_text(row.get("meal_type")),
        tags=normalize_tags(row.get("tags")),
        is_drink=bool(row.get("is_drink")),
        is_alcoholic=bool(row.get("is_alcoholic")),
    )


def load_recipes_sqlalchemy(database_url: str) -> list[RecipeMetaRow]:
    engine = create_engine(database_url)
    query = text(
        """
        SELECT
            id,
            title,
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


def load_recipes_docker() -> list[RecipeMetaRow]:
    sql = """
        SELECT COALESCE(json_agg(row_to_json(t) ORDER BY id), '[]'::json)
        FROM (
            SELECT
                id,
                title,
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


def combined_text(recipe: RecipeMetaRow) -> str:
    values = [recipe.title, recipe.category, recipe.meal_type, *recipe.tags]
    return " ".join(normalize_text(value) for value in values if value)


def contains_any(text_value: str, keywords: tuple[str, ...]) -> bool:
    for keyword in keywords:
        if keyword == "морс":
            pattern = r"(?<![а-яa-z0-9])морс(а|ы|ом|ов|овый|овая|овое|овые)?(?![а-яa-z0-9])"
        else:
            pattern = rf"(?<![а-яa-z0-9]){re.escape(keyword)}[а-яa-z]*(?![а-яa-z0-9])"
        if re.search(pattern, text_value):
            return True
    return False


def remediation_category(recipe: RecipeMetaRow) -> str:
    text_value = combined_text(recipe)
    if (
        recipe.is_drink
        or recipe.is_alcoholic
        or recipe.category == "drink"
        or recipe.meal_type in {"drink", "smoothie", "protein_shake", "coffee", "tea", "cocktail"}
        or contains_any(text_value, BEVERAGE_KEYWORDS)
    ):
        return "A"
    if recipe.category == "event" or contains_any(text_value, HOLIDAY_KEYWORDS):
        return "B"
    if contains_any(text_value, KIDS_KEYWORDS):
        return "C"
    if 2 <= len(recipe.steps) <= 3:
        return "D"
    return "E"


def audit_weak_recipes(recipes: list[RecipeMetaRow]) -> dict[str, list[tuple[RecipeMetaRow, Any]]]:
    groups: dict[str, list[tuple[RecipeMetaRow, Any]]] = {key: [] for key in CATEGORIES}
    for recipe in recipes:
        quality = audit_recipe(RecipeStepsRow(id=recipe.id, title=recipe.title, steps=recipe.steps))
        if quality.group != "B":
            continue
        groups[remediation_category(recipe)].append((recipe, quality))
    for records in groups.values():
        records.sort(key=lambda item: (item[0].id, item[0].title))
    return groups


def build_report(
    recipes: list[RecipeMetaRow],
    groups: dict[str, list[tuple[RecipeMetaRow, Any]]],
    connection_note: str,
) -> str:
    weak_total = sum(len(records) for records in groups.values())
    lines = [
        "# Weak Steps Remediation Plan",
        "",
        "Scope: read-only audit of current `recipes` weak_steps records. No database changes, recipe updates, commits, or AI calls were performed.",
        "",
        "## Summary",
        "",
        f"- Total recipes scanned: `{len(recipes)}`",
        f"- Total weak_steps: `{weak_total}`",
        f"- Database read method: `{connection_note}`",
        "",
        "## Category Counts",
        "",
        "| Category | Name | Count |",
        "| --- | --- | ---: |",
    ]
    for category, meta in CATEGORIES.items():
        lines.append(f"| {category} | {meta['name']} | {len(groups[category])} |")

    for category, meta in CATEGORIES.items():
        lines.extend(
            [
                "",
                f"## {category}. {meta['name']}",
                "",
                f"{meta['description']}.",
                "",
                "| ID | Title | Steps count | Steps |",
                "| ---: | --- | ---: | --- |",
            ]
        )
        records = groups[category]
        if not records:
            lines.append("| n/a | n/a | n/a | n/a |")
            continue
        for recipe, _quality in records:
            lines.append(
                f"| {recipe.id} | {fmt_inline(recipe.title)} | "
                f"{len(recipe.steps)} | {format_steps(recipe.steps)} |"
            )

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

    groups = audit_weak_recipes(recipes)
    report = build_report(recipes, groups, connection_note)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"Total recipes scanned: {len(recipes)}")
    print(f"Total weak_steps: {sum(len(records) for records in groups.values())}")
    for category, meta in CATEGORIES.items():
        print(f"{category}. {meta['name']}: {len(groups[category])}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
