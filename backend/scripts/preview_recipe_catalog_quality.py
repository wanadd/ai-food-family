#!/usr/bin/env python3
"""Stage Q2: preview default recipe catalog ordering (first 30 rows)."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _image_paths import ensure_app_on_path, find_repo_file  # noqa: E402

ensure_app_on_path()

from app.services.recipes.catalog_sort import sort_recipes_catalog  # noqa: E402
from app.services.recipes.repository import query_recipes  # noqa: E402
from app.services.recipes.types import RecipeListFilters  # noqa: E402

DEFAULT_REPORT = find_repo_file("reports", "recipe_catalog_quality_preview.md")
PREVIEW_LIMIT = 30


def main() -> int:
    os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL required", file=sys.stderr)
        return 1

    from app.database import SessionLocal

    session = SessionLocal()
    try:
        recipes = query_recipes(session, RecipeListFilters())
        recipes = sort_recipes_catalog(recipes)
        preview = recipes[:PREVIEW_LIMIT]
    finally:
        session.close()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Recipe Catalog Quality Preview",
        "",
        f"**Generated:** {now}",
        f"**Sort:** `quality-first` (default GET /recipes)",
        f"**Total active (gold filter):** `{len(recipes)}`",
        f"**Preview rows:** `{len(preview)}`",
        "",
        "## First 30 recipes",
        "",
        "| # | id | title | source_type | hero_image_url |",
        "|---|-----|-------|-------------|----------------|",
    ]
    for idx, recipe in enumerate(preview, start=1):
        hero = recipe.hero_image_url or ""
        if len(hero) > 48:
            hero = hero[:45] + "..."
        title = (recipe.title or "").replace("|", "/")
        lines.append(
            f"| {idx} | {recipe.id} | {title} | {recipe.source_type} | `{hero or '—'}` |"
        )
    lines.append("")

    DEFAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"preview={len(preview)} total={len(recipes)} report={DEFAULT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
