#!/usr/bin/env python3
"""Read-only duplicate audit for recipes.

Run from the repository root:
    python backend/scripts/audit_recipe_duplicates.py
"""

from __future__ import annotations

import argparse
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_PATH = ROOT / "reports" / "recipe_duplicates_audit.md"
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
SIMILARITY_THRESHOLD = 0.86


@dataclass(frozen=True)
class RecipeRow:
    id: int
    title: str
    normalized_title: str
    source_type: str | None
    source_url: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit duplicate recipe titles")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown duplicate audit report",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=SIMILARITY_THRESHOLD,
        help="Title similarity threshold for potential duplicates",
    )
    return parser.parse_args()


def normalize_title(value: str) -> str:
    text_value = value.lower()
    text_value = text_value.replace("ё", "е")
    text_value = re.sub(r"[\"'«»„“”‘’`´]", "", text_value)
    text_value = re.sub(r"[^0-9a-zа-я\s]+", " ", text_value)
    text_value = re.sub(r"\s+", " ", text_value).strip()
    return text_value


def load_recipes(database_url: str) -> list[RecipeRow]:
    engine = create_engine(database_url)
    query = text(
        """
        SELECT id, title, source_type, source_url
        FROM recipes
        ORDER BY id
        """
    )
    rows: list[RecipeRow] = []
    with engine.connect() as conn:
        for row in conn.execute(query).mappings():
            title = str(row["title"] or "").strip()
            rows.append(
                RecipeRow(
                    id=int(row["id"]),
                    title=title,
                    normalized_title=normalize_title(title),
                    source_type=row.get("source_type"),
                    source_url=row.get("source_url"),
                )
            )
    return rows


def exact_duplicate_groups(recipes: list[RecipeRow]) -> list[list[RecipeRow]]:
    by_title: dict[str, list[RecipeRow]] = defaultdict(list)
    for recipe in recipes:
        if recipe.normalized_title:
            by_title[recipe.normalized_title].append(recipe)
    return [items for items in by_title.values() if len(items) > 1]


def title_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right).ratio()


def potential_duplicate_groups(
    recipes: list[RecipeRow],
    threshold: float,
) -> tuple[list[list[RecipeRow]], list[tuple[RecipeRow, RecipeRow, float]]]:
    parent = {recipe.id: recipe.id for recipe in recipes}

    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    pairs: list[tuple[RecipeRow, RecipeRow, float]] = []
    for index, left in enumerate(recipes):
        if not left.normalized_title:
            continue
        for right in recipes[index + 1 :]:
            if not right.normalized_title:
                continue
            if left.normalized_title == right.normalized_title:
                continue
            score = title_similarity(left.normalized_title, right.normalized_title)
            if score >= threshold:
                pairs.append((left, right, score))
                union(left.id, right.id)

    grouped: dict[int, list[RecipeRow]] = defaultdict(list)
    ids_with_pairs = {recipe.id for pair in pairs for recipe in pair[:2]}
    for recipe in recipes:
        if recipe.id in ids_with_pairs:
            grouped[find(recipe.id)].append(recipe)

    groups = [items for items in grouped.values() if len(items) > 1]
    groups.sort(key=lambda items: (-len(items), min(item.id for item in items)))
    pairs.sort(key=lambda item: (-item[2], item[0].id, item[1].id))
    return groups, pairs


def recipe_line(recipe: RecipeRow) -> str:
    source = f", source_type={recipe.source_type}" if recipe.source_type else ""
    return f"- #{recipe.id}: {recipe.title}{source}"


def build_report(
    recipes: list[RecipeRow],
    exact_groups: list[list[RecipeRow]],
    potential_groups: list[list[RecipeRow]],
    potential_pairs: list[tuple[RecipeRow, RecipeRow, float]],
    threshold: float,
) -> str:
    lines = [
        "# Recipe Duplicate Audit",
        "",
        "## Summary",
        "",
        f"- Total recipes: `{len(recipes)}`",
        f"- Exact duplicate groups: `{len(exact_groups)}`",
        f"- Potential duplicate groups: `{len(potential_groups)}`",
        f"- Similarity threshold: `{threshold:.2f}`",
        "",
        "## Exact Duplicate Groups",
        "",
    ]

    if exact_groups:
        for index, group in enumerate(exact_groups, start=1):
            lines.append(f"### Exact Group {index}: `{group[0].normalized_title}`")
            lines.extend(recipe_line(recipe) for recipe in group)
            lines.append("")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Potential Duplicate Groups", ""])
    if potential_groups:
        for index, group in enumerate(potential_groups[:50], start=1):
            lines.append(f"### Potential Group {index}")
            lines.extend(recipe_line(recipe) for recipe in group)
            lines.append("")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Similar Title Examples", ""])
    if potential_pairs:
        for left, right, score in potential_pairs[:100]:
            lines.append(
                f"- `{score:.3f}` #{left.id} {left.title} <-> "
                f"#{right.id} {right.title}"
            )
    else:
        lines.append("- `n/a`")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    recipes = load_recipes(args.database_url)
    exact_groups = exact_duplicate_groups(recipes)
    potential_groups, potential_pairs = potential_duplicate_groups(
        recipes,
        args.similarity_threshold,
    )
    report = build_report(
        recipes,
        exact_groups,
        potential_groups,
        potential_pairs,
        args.similarity_threshold,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Total recipes: {len(recipes)}")
    print(f"Exact duplicate groups: {len(exact_groups)}")
    print(f"Potential duplicate groups: {len(potential_groups)}")
    print(f"Report written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
