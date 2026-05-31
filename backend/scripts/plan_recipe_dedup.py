#!/usr/bin/env python3
"""Build a read-only recipe deduplication plan.

Run from the repository root:
    python backend/scripts/plan_recipe_dedup.py
"""

from __future__ import annotations

import argparse
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_PATH = ROOT / "reports" / "recipe_dedup_plan.md"
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"


@dataclass(frozen=True)
class RecipeRow:
    id: int
    title: str
    normalized_title: str
    description: str
    steps_count: int
    ingredients_count: int
    source_type: str | None
    source_url: str | None

    @property
    def description_length(self) -> int:
        return len(self.description.strip())


@dataclass(frozen=True)
class DedupGroup:
    normalized_title: str
    main_recipe: RecipeRow
    duplicate_recipes: list[RecipeRow]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan recipe deduplication")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown deduplication plan",
    )
    return parser.parse_args()


def normalize_title(value: str) -> str:
    text_value = value.lower().replace("ё", "е")
    text_value = re.sub(r"[\"'«»„“”‘’`´]", "", text_value)
    text_value = re.sub(r"[^0-9a-zа-я\s]+", " ", text_value)
    text_value = re.sub(r"\s+", " ", text_value).strip()
    return text_value


def count_json_list(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def load_recipes(database_url: str) -> list[RecipeRow]:
    engine = create_engine(database_url)
    query = text(
        """
        SELECT id, title, description, steps, ingredients, source_type, source_url
        FROM recipes
        ORDER BY id
        """
    )
    rows: list[RecipeRow] = []
    with engine.connect() as conn:
        for row in conn.execute(query).mappings():
            title = str(row["title"] or "").strip()
            description = str(row["description"] or "").strip()
            rows.append(
                RecipeRow(
                    id=int(row["id"]),
                    title=title,
                    normalized_title=normalize_title(title),
                    description=description,
                    steps_count=count_json_list(row.get("steps")),
                    ingredients_count=count_json_list(row.get("ingredients")),
                    source_type=row.get("source_type"),
                    source_url=row.get("source_url"),
                )
            )
    return rows


def main_sort_key(recipe: RecipeRow) -> tuple[int, int, int]:
    return (-recipe.description_length, -recipe.steps_count, recipe.id)


def build_dedup_plan(recipes: list[RecipeRow]) -> list[DedupGroup]:
    by_title: dict[str, list[RecipeRow]] = defaultdict(list)
    for recipe in recipes:
        if recipe.normalized_title:
            by_title[recipe.normalized_title].append(recipe)

    groups: list[DedupGroup] = []
    for normalized_title, group in by_title.items():
        if len(group) < 2:
            continue
        sorted_group = sorted(group, key=main_sort_key)
        groups.append(
            DedupGroup(
                normalized_title=normalized_title,
                main_recipe=sorted_group[0],
                duplicate_recipes=sorted_group[1:],
            )
        )
    groups.sort(key=lambda group: group.main_recipe.id)
    return groups


def recipe_summary(recipe: RecipeRow) -> str:
    return (
        f"#{recipe.id}: {recipe.title} "
        f"(description={recipe.description_length} chars, "
        f"steps={recipe.steps_count}, ingredients={recipe.ingredients_count}, "
        f"source_type={recipe.source_type or 'n/a'})"
    )


def build_report(recipes: list[RecipeRow], groups: list[DedupGroup]) -> str:
    lines = [
        "# Recipe Deduplication Plan",
        "",
        "## Summary",
        "",
        f"- Total recipes: `{len(recipes)}`",
        f"- Duplicate groups: `{len(groups)}`",
        "- Mode: `read-only plan`",
        "",
        "## Selection Rules",
        "",
        "1. Keep recipe with longer description.",
        "2. If tied, keep recipe with more steps.",
        "3. If tied, keep recipe with smaller id.",
        "",
        "## Duplicate Groups",
        "",
    ]

    if not groups:
        lines.append("- `n/a`")
        return "\n".join(lines).rstrip() + "\n"

    for index, group in enumerate(groups, start=1):
        main = group.main_recipe
        lines.extend(
            [
                f"### Group {index}: `{group.normalized_title}`",
                "",
                "#### Main Recipe",
                "",
                f"- {recipe_summary(main)}",
                "",
                "#### Duplicate Recipes",
                "",
            ]
        )
        lines.extend(f"- {recipe_summary(recipe)}" for recipe in group.duplicate_recipes)
        duplicate_ids = ", ".join(str(recipe.id) for recipe in group.duplicate_recipes)
        lines.extend(
            [
                "",
                "#### What Will Be Preserved",
                "",
                f"- Main recipe `#{main.id}` keeps its title, description, steps, ingredients, metadata, ratings and relations.",
                "- No data will be changed by this plan.",
                "",
                "#### What Could Be Merged Later",
                "",
                f"- Potential duplicate recipe ids: `{duplicate_ids}`",
                "- Candidate merge data: source URLs, tags, allergens, restrictions, ratings/favorites/history, and any richer ingredients or steps.",
                "- Final merge/delete requires a separate explicit command and should preserve foreign-key references.",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    recipes = load_recipes(args.database_url)
    groups = build_dedup_plan(recipes)
    report = build_report(recipes, groups)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Total recipes: {len(recipes)}")
    print(f"Duplicate groups: {len(groups)}")
    print(f"Report written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
