#!/usr/bin/env python3
"""Repair recipe image assignments mis-applied to archived manual recipes.

Background: the pilot runner once trusted the pilot JSON ``recipe_id`` (a batch
index 1..10) as a DB primary key. That assigned hero/card/thumb URLs to archived
``manual`` recipes (id 1..10) instead of the active ``v1_import`` recipes.

This script:
  1. Reads reports/planam_v1_recipe_image_pilot_results.json
  2. For each entry, resolves the correct active v1_import recipe BY TITLE
  3. Moves hero_image_url / image_url / thumbnail_url onto the correct recipe
  4. Clears those URLs on the wrong (archived manual) recipes id 1..10

Usage (from repo root):
    python backend/scripts/repair_recipe_image_assignments.py --dry-run
    python backend/scripts/repair_recipe_image_assignments.py --commit

Requires DATABASE_URL.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "backend" / "scripts"
API_ROOT = ROOT / "apps" / "api"
for _path in (str(SCRIPTS_DIR), str(API_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from recipe_id_resolver import (  # noqa: E402
    RecipeResolutionError,
    resolve_v1_recipe_id_by_title,
)

DEFAULT_RESULTS = ROOT / "reports" / "planam_v1_recipe_image_pilot_results.json"
LOCAL_URL_BASE = "/recipe-images"
WRONG_MANUAL_IDS = list(range(1, 11))  # archived manual recipes id 1..10


def urls_for_recipe_id(recipe_id: int) -> dict[str, str]:
    base = f"{LOCAL_URL_BASE}/{recipe_id}"
    return {
        "hero_image_url": f"{base}/hero.webp",
        "image_url": f"{base}/card_800.webp",
        "thumbnail_url": f"{base}/thumb_400.webp",
    }


def load_results(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    results = data.get("results") if isinstance(data, dict) else data
    if not isinstance(results, list):
        raise SystemExit("Results JSON must contain a 'results' list")
    return [r for r in results if isinstance(r, dict) and r.get("title")]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repair mis-assigned recipe images")
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--commit", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entries = load_results(Path(args.results).resolve())

    from app.database import SessionLocal
    from app.models.recipe import Recipe

    db = SessionLocal()
    moved = 0
    failed = 0
    correct_ids: set[int] = set()
    try:
        print(f"{'OLD_ID':>7} {'NEW_ID':>7}  TITLE")
        print("-" * 60)
        for entry in entries:
            title = str(entry.get("title") or "")
            old_id = entry.get("recipe_id")
            try:
                new_id = resolve_v1_recipe_id_by_title(db, Recipe, title)
            except RecipeResolutionError as exc:
                failed += 1
                print(f"{str(old_id):>7} {'ERR':>7}  {title}  -> {exc}")
                continue

            correct_ids.add(new_id)
            print(f"{str(old_id):>7} {new_id:>7}  {title}")

            if args.commit:
                target = db.get(Recipe, new_id)
                urls = urls_for_recipe_id(new_id)
                target.hero_image_url = urls["hero_image_url"]
                target.image_url = urls["image_url"]
                target.thumbnail_url = urls["thumbnail_url"]
            moved += 1

        # Clear URLs on archived manual recipes id 1..10 that were not, in fact,
        # legitimately assigned a correct id by the resolver.
        cleared = 0
        for wrong_id in WRONG_MANUAL_IDS:
            if wrong_id in correct_ids:
                continue
            recipe = db.get(Recipe, wrong_id)
            if recipe is None:
                continue
            if any(
                getattr(recipe, attr)
                for attr in ("hero_image_url", "image_url", "thumbnail_url")
            ):
                print(f"CLEAR  #{wrong_id}: {recipe.title!r} (source_type={recipe.source_type})")
                cleared += 1
                if args.commit:
                    recipe.hero_image_url = None
                    recipe.image_url = None
                    recipe.thumbnail_url = None

        if args.commit:
            db.commit()
            print(f"\nCOMMIT: moved={moved} cleared={cleared} failed={failed}")
        else:
            print(f"\nDRY-RUN: would move={moved} clear={cleared} failed={failed}")
        return 1 if failed else 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
