#!/usr/bin/env python3
"""Archive placeholder/demo/legacy recipes after V1 catalog import.

Sets is_active=False for seed and catalog placeholder recipes. Does not delete rows.

Run from the repository root:
    python backend/scripts/archive_placeholder_recipes.py --dry-run
    python backend/scripts/archive_placeholder_recipes.py --commit
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))


def normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def placeholder_titles() -> set[str]:
    from app.data.recipe_catalog_seed import CATALOG_RECIPES
    from app.data.recipe_seed import SEED_RECIPES

    titles: set[str] = set()
    for item in SEED_RECIPES:
        titles.add(normalize_title(str(item["title"])))
    for item in CATALOG_RECIPES:
        titles.add(normalize_title(str(item["title"])))
    return titles


def archive_placeholders(*, dry_run: bool) -> int:
    from app.database import SessionLocal
    from app.models.recipe import Recipe

    titles = placeholder_titles()
    db = SessionLocal()
    archived = 0
    skipped = 0
    try:
        rows = (
            db.query(Recipe)
            .filter(Recipe.is_active.is_(True))
            .filter(Recipe.source_type != "v1_import")
            .all()
        )
        for recipe in rows:
            title_key = normalize_title(recipe.title)
            should_archive = title_key in titles or recipe.source_type == "seed"
            if not should_archive:
                skipped += 1
                continue
            if dry_run:
                print(f"DRY-RUN ARCHIVE: {recipe.title} (source_type={recipe.source_type})")
            else:
                recipe.is_active = False
                print(f"ARCHIVE: {recipe.title} (source_type={recipe.source_type})")
            archived += 1
        if not dry_run:
            db.commit()
        print(f"Summary: archived={archived}, skipped={skipped}")
        return 0
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive placeholder PlanAm recipes")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--commit", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return archive_placeholders(dry_run=not args.commit)


if __name__ == "__main__":
    raise SystemExit(main())
