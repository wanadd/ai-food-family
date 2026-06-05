#!/usr/bin/env python3
"""Audit recipe catalog quality in PostgreSQL.

Run from the repository root:
    python backend/scripts/audit_recipe_catalog.py
    python backend/scripts/audit_recipe_catalog.py --fix-meal-types --fix-titles
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.services.recipes.title_normalize import (  # noqa: E402
    ALLOWED_CATALOG_MEAL_TYPES,
    EXTENDED_MEAL_TYPES,
    catalog_meal_type,
    display_title_from,
    normalize_title,
)

DEFAULT_REPORT_PATH = ROOT / "reports" / "recipe_catalog_quality.md"
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
ALLOWED_SOURCE_TYPES = frozenset({"manual", "import", "seed"})
SUSPICIOUS_WORDS = (
    "алкогол",
    "настойк",
    "ликер",
    "ликёр",
    "водк",
    "вино",
    "самогон",
)
DESSERT_PATTERNS = (
    r"\bторт",
    r"\bпирожн",
    r"\bдесерт",
    r"\bкекс",
)
PRESERVE_PATTERNS = (
    r"на зиму",
    r"\bзаготов",
    r"\bконсерв",
    r"\bмарин",
    r"\bсолень",
    r"\bваренье",
)
PRIORITY_PATTERNS = (
    r"\bсуп",
    r"\bкаша",
    r"\bкуриц",
    r"\bкотлет",
    r"\bсалат",
    r"\bзапеканк",
)


@dataclass
class AuditStats:
    total: int = 0
    empty_titles: list[int] = field(default_factory=list)
    long_titles: list[tuple[int, str]] = field(default_factory=list)
    suspicious_titles: list[tuple[int, str]] = field(default_factory=list)
    duplicate_groups: dict[str, list[int]] = field(default_factory=dict)
    no_ingredients: list[int] = field(default_factory=list)
    no_steps: list[int] = field(default_factory=list)
    invalid_meal_type: list[tuple[int, str]] = field(default_factory=list)
    non_catalog_meal_type: list[tuple[int, str]] = field(default_factory=list)
    invalid_source_type: list[tuple[int, str]] = field(default_factory=list)
    alcohol_related: list[tuple[int, str]] = field(default_factory=list)
    dessert_not_priority: list[tuple[int, str]] = field(default_factory=list)
    preserve_related: list[tuple[int, str]] = field(default_factory=list)
    few_ingredients: list[tuple[int, int]] = field(default_factory=list)
    many_ingredients: list[tuple[int, int]] = field(default_factory=list)
    missing_normalized_title: list[int] = field(default_factory=list)
    missing_original_title: list[int] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit recipe catalog quality")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
    )
    parser.add_argument("--output", default=str(DEFAULT_REPORT_PATH))
    parser.add_argument(
        "--fix-meal-types",
        action="store_true",
        help="Map meal_type values to breakfast/lunch/dinner/snack",
    )
    parser.add_argument(
        "--fix-titles",
        action="store_true",
        help="Backfill original_title, normalized_title, display_title",
    )
    return parser.parse_args()


def matches_any(text_value: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text_value, flags=re.IGNORECASE) for pattern in patterns)


def is_priority_meal(title: str) -> bool:
    return matches_any(title.lower(), PRIORITY_PATTERNS)


def load_rows(database_url: str) -> list[dict[str, Any]]:
    engine = create_engine(database_url)
    query = text(
        """
        SELECT
            r.id,
            r.title,
            r.original_title,
            r.normalized_title,
            r.display_title,
            r.meal_type,
            r.source_type,
            r.is_active,
            COALESCE(ing.cnt, 0) AS ingredient_count,
            COALESCE(st.cnt, 0) AS step_count
        FROM recipes r
        LEFT JOIN (
            SELECT recipe_id, COUNT(*) AS cnt
            FROM recipe_ingredients
            GROUP BY recipe_id
        ) ing ON ing.recipe_id = r.id
        LEFT JOIN (
            SELECT recipe_id, COUNT(*) AS cnt
            FROM recipe_steps
            GROUP BY recipe_id
        ) st ON st.recipe_id = r.id
        ORDER BY r.id
        """
    )
    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(query).mappings()]


def audit_rows(rows: list[dict[str, Any]]) -> AuditStats:
    stats = AuditStats(total=len(rows))
    by_normalized: dict[str, list[int]] = defaultdict(list)

    for row in rows:
        recipe_id = int(row["id"])
        title = str(row.get("title") or "").strip()
        meal_type = str(row.get("meal_type") or "").strip().lower()
        source_type = str(row.get("source_type") or "").strip().lower()
        ingredient_count = int(row.get("ingredient_count") or 0)
        step_count = int(row.get("step_count") or 0)
        normalized = str(row.get("normalized_title") or "").strip() or normalize_title(title)

        if not title:
            stats.empty_titles.append(recipe_id)
        if len(title) > 200:
            stats.long_titles.append((recipe_id, title))
        if re.search(r"[{}<>\[\]@#$%^*_+=~`]", title):
            stats.suspicious_titles.append((recipe_id, title))

        if not row.get("original_title"):
            stats.missing_original_title.append(recipe_id)
        if not row.get("normalized_title"):
            stats.missing_normalized_title.append(recipe_id)

        by_normalized[normalized].append(recipe_id)

        if ingredient_count == 0:
            stats.no_ingredients.append(recipe_id)
        if step_count == 0:
            stats.no_steps.append(recipe_id)
        if ingredient_count < 3:
            stats.few_ingredients.append((recipe_id, ingredient_count))
        if ingredient_count > 25:
            stats.many_ingredients.append((recipe_id, ingredient_count))

        if meal_type and meal_type not in EXTENDED_MEAL_TYPES:
            stats.invalid_meal_type.append((recipe_id, meal_type))
        if meal_type and meal_type not in ALLOWED_CATALOG_MEAL_TYPES:
            stats.non_catalog_meal_type.append((recipe_id, meal_type))

        if source_type and source_type not in ALLOWED_SOURCE_TYPES:
            stats.invalid_source_type.append((recipe_id, source_type))

        combined = f"{title} {normalized}".lower()
        if any(word in combined for word in SUSPICIOUS_WORDS):
            stats.alcohol_related.append((recipe_id, title))
        if matches_any(title, PRESERVE_PATTERNS):
            stats.preserve_related.append((recipe_id, title))
        if matches_any(title, DESSERT_PATTERNS) and not is_priority_meal(title):
            stats.dessert_not_priority.append((recipe_id, title))

    stats.duplicate_groups = {
        key: ids for key, ids in by_normalized.items() if len(ids) > 1
    }
    return stats


def apply_fixes(database_url: str, *, fix_meal_types: bool, fix_titles: bool) -> None:
    if not fix_meal_types and not fix_titles:
        return

    engine = create_engine(database_url)
    rows = load_rows(database_url)
    with engine.begin() as conn:
        for row in rows:
            recipe_id = int(row["id"])
            title = str(row.get("title") or "").strip()
            updates: dict[str, Any] = {}

            if fix_titles:
                updates["original_title"] = row.get("original_title") or title
                updates["normalized_title"] = row.get("normalized_title") or normalize_title(
                    title
                )
                updates["display_title"] = row.get("display_title") or display_title_from(title)

            if fix_meal_types:
                current = str(row.get("meal_type") or "lunch")
                mapped = catalog_meal_type(current)
                if mapped != current:
                    updates["meal_type"] = mapped

            if not updates:
                continue

            set_clause = ", ".join(f"{key} = :{key}" for key in updates)
            conn.execute(
                text(f"UPDATE recipes SET {set_clause} WHERE id = :id"),
                {"id": recipe_id, **updates},
            )


def render_report(stats: AuditStats, *, output_path: Path, database_url: str) -> str:
    lines = [
        "# Recipe Catalog Quality Audit",
        "",
        "## Source",
        "",
        f"- Database: `{database_url}`",
        f"- Report: `{output_path}`",
        "",
        "## Summary",
        "",
        f"- Total recipes: `{stats.total}`",
        f"- Empty titles: `{len(stats.empty_titles)}`",
        f"- Long titles (>200): `{len(stats.long_titles)}`",
        f"- Suspicious titles: `{len(stats.suspicious_titles)}`",
        f"- Duplicate normalized titles: `{len(stats.duplicate_groups)}` groups",
        f"- Without ingredients: `{len(stats.no_ingredients)}`",
        f"- Without steps: `{len(stats.no_steps)}`",
        f"- Invalid meal_type: `{len(stats.invalid_meal_type)}`",
        f"- Non-catalog meal_type: `{len(stats.non_catalog_meal_type)}`",
        f"- Invalid source_type: `{len(stats.invalid_source_type)}`",
        f"- Alcohol-related titles: `{len(stats.alcohol_related)}`",
        f"- Dessert not priority: `{len(stats.dessert_not_priority)}`",
        f"- Preserve/winter titles: `{len(stats.preserve_related)}`",
        f"- Few ingredients (<3): `{len(stats.few_ingredients)}`",
        f"- Many ingredients (>25): `{len(stats.many_ingredients)}`",
        f"- Missing original_title: `{len(stats.missing_original_title)}`",
        f"- Missing normalized_title: `{len(stats.missing_normalized_title)}`",
        "",
    ]

    def section(title: str, items: list[Any], limit: int = 15) -> None:
        lines.append(f"## {title}")
        lines.append("")
        if not items:
            lines.append("- none")
        else:
            for item in items[:limit]:
                lines.append(f"- {item}")
            if len(items) > limit:
                lines.append(f"- … and {len(items) - limit} more")
        lines.append("")

    section("Duplicate Groups (normalized title)", list(stats.duplicate_groups.items()))
    section("Non-catalog meal_type", stats.non_catalog_meal_type)
    section("Alcohol-related", stats.alcohol_related)
    section("Dessert not priority", stats.dessert_not_priority)
    section("Preserve/winter", stats.preserve_related)
    section("Few ingredients", stats.few_ingredients)
    section("Many ingredients", stats.many_ingredients)
    section("No steps", stats.no_steps)
    section("No ingredients", stats.no_ingredients)

    meal_counter = Counter(
        str(row.get("meal_type") or "") for row in load_rows(database_url)
    )
    lines.extend(["## meal_type distribution", ""])
    for meal_type, count in meal_counter.most_common():
        lines.append(f"- {meal_type or '(empty)'}: `{count}`")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    apply_fixes(
        args.database_url,
        fix_meal_types=args.fix_meal_types,
        fix_titles=args.fix_titles,
    )

    rows = load_rows(args.database_url)
    stats = audit_rows(rows)
    report = render_report(stats, output_path=output_path, database_url=args.database_url)
    output_path.write_text(report, encoding="utf-8")
    print(f"Audited {stats.total} recipes")
    print(f"Report written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
