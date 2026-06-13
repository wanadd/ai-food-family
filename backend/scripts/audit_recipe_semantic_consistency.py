#!/usr/bin/env python3
"""Audit semantic consistency between recipe text and ingredients/steps."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _image_paths import ensure_app_on_path  # noqa: E402

API_ROOT = ensure_app_on_path()

from app.recipes.recipe_gold_v3_semantic_consistency import check_semantic_consistency  # noqa: E402
from app.services.recipe_storage import get_structured_ingredients, get_structured_steps  # noqa: E402

DEFAULT_REPORT_PATH = ROOT / "reports" / "recipe_semantic_consistency_audit.md"


def _recipe_to_gate_payload(recipe: Any) -> dict[str, Any]:
    ingredients = get_structured_ingredients(recipe)
    steps = [{"text": text} for text in get_structured_steps(recipe)]
    return {
        "title": recipe.title,
        "display_title": recipe.display_title,
        "description": recipe.description,
        "ingredients": ingredients,
        "steps": steps,
    }


def audit_recipes(recipes: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for recipe in recipes:
        findings = check_semantic_consistency(_recipe_to_gate_payload(recipe))
        if not findings:
            continue
        rows.append(
            {
                "id": recipe.id,
                "title": recipe.title,
                "display_title": recipe.display_title,
                "findings": findings,
            }
        )
    return rows


def render_report(rows: list[dict[str, Any]], *, total: int) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Recipe semantic consistency audit",
        "",
        f"**Generated:** {now}",
        f"**Recipes scanned:** {total}",
        f"**Failures:** {len(rows)}",
        "",
    ]
    if not rows:
        lines.extend(["All scanned recipes passed semantic consistency checks.", ""])
        return "\n".join(lines)

    for row in rows:
        lines.append(f"## Recipe #{row['id']}: {row['title']}")
        if row.get("display_title"):
            lines.append(f"- display_title: {row['display_title']}")
        for finding in row["findings"]:
            lines.append(
                f"- **{finding['code']}** ({finding['severity']}): {finding['message']}"
            )
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit recipe semantic text vs ingredients")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="PostgreSQL/SQLite URL (defaults to DATABASE_URL)",
    )
    parser.add_argument("--output", default=str(DEFAULT_REPORT_PATH))
    parser.add_argument(
        "--recipe-ids",
        default="",
        help="Comma-separated recipe ids (default: all active catalog-ready)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL required", file=sys.stderr)
        return 1

    from sqlalchemy import select

    from app.database import SessionLocal
    from app.models.recipe import Recipe
    from app.services.recipes.catalog_ready import is_catalog_ready_recipe

    session = SessionLocal()
    try:
        query = select(Recipe).where(Recipe.is_active.is_(True))
        if args.recipe_ids.strip():
            ids = [int(x.strip()) for x in args.recipe_ids.split(",") if x.strip()]
            query = query.where(Recipe.id.in_(ids))
        recipes = list(session.scalars(query).all())
        if not args.recipe_ids.strip():
            recipes = [r for r in recipes if is_catalog_ready_recipe(r)]
        rows = audit_recipes(recipes)
    finally:
        session.close()

    report = render_report(rows, total=len(recipes))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(f"Wrote {output} ({len(rows)} failures / {len(recipes)} recipes)")
    return 1 if rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
