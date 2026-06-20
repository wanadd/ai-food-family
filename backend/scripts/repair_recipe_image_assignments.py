#!/usr/bin/env python3
"""Repair recipe image assignments mis-applied to archived manual recipes.

Background: the pilot runner once trusted the pilot JSON ``recipe_id`` (a batch
index 1..10) as a DB primary key. That generated image files into folders named
by that index AND assigned hero/card/thumb URLs to archived ``manual`` recipes
(id 1..10) instead of the active ``v1_import`` recipes.

After the DB-only repair, URLs pointed to ``/recipe-images/{correct_id}/`` while
the actual files still lived in ``/recipe-images/{old_id}/`` — causing 404s.

This script fixes BOTH layers:
  1. Reads reports/planam_v1_recipe_image_pilot_results.json
  2. Resolves the correct active v1_import recipe BY TITLE (single source of truth)
  3. Relocates image files  {old_id} -> {correct_id}  on disk
  4. Sets hero/card/thumb URLs on the correct recipe ONLY if files exist there
     (otherwise clears them so the UI falls back instead of 404-ing)
  5. Clears URLs on the wrong (archived manual) recipes

Usage (from repo root):
    python backend/scripts/repair_recipe_image_assignments.py --dry-run
    python backend/scripts/repair_recipe_image_assignments.py --commit

Requires DATABASE_URL.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _image_paths import (  # noqa: E402
    find_repo_file,
    recipe_images_dir,
    recipe_images_public_url,
)
from recipe_id_resolver import (  # noqa: E402
    RecipeResolutionError,
    resolve_v1_recipe_id_by_title,
)

DEFAULT_RESULTS = find_repo_file(
    "reports", "planam_v1_recipe_image_pilot_results.json"
)
WRONG_MANUAL_IDS = list(range(1, 11))  # archived manual recipes id 1..10
REQUIRED_FILES = ("hero.webp", "card_800.webp", "thumb_400.webp")


def urls_for_recipe_id(recipe_id: int) -> dict[str, str]:
    base = f"{recipe_images_public_url()}/{recipe_id}"
    return {
        "hero_image_url": f"{base}/hero.webp",
        "image_url": f"{base}/card_800.webp",
        "thumbnail_url": f"{base}/thumb_400.webp",
    }


def has_required_files(folder: Path) -> bool:
    return folder.is_dir() and all((folder / name).is_file() for name in REQUIRED_FILES)


def relocate_image_folder(
    old_id: int, new_id: int, images_root: Path, *, dry_run: bool
) -> str:
    """Move generated image files from ``old_id`` folder to ``new_id`` folder.

    Returns an action label:
      - ``dst_ready``  : target already has all required files (nothing to do)
      - ``would_move`` : dry-run; a move is needed
      - ``moved``      : files moved into place
      - ``missing``    : no usable source files found (URL must be cleared)
    """
    src = images_root / str(old_id)
    dst = images_root / str(new_id)

    if has_required_files(dst):
        return "dst_ready"
    if not (src.is_dir() and any(src.iterdir())):
        return "missing"
    if dry_run:
        return "would_move"

    dst.mkdir(parents=True, exist_ok=True)
    for item in list(src.iterdir()):
        if item.is_file():
            target = dst / item.name
            if target.exists():
                target.unlink()
            shutil.move(str(item), str(target))
    try:
        if src.is_dir() and not any(src.iterdir()):
            src.rmdir()
    except OSError:
        pass
    return "moved" if has_required_files(dst) else "missing"


def load_results(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    results = data.get("results") if isinstance(data, dict) else data
    if not isinstance(results, list):
        raise SystemExit("Results JSON must contain a 'results' list")
    return [r for r in results if isinstance(r, dict) and r.get("title")]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repair mis-assigned recipe images")
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument("--images-root", default=str(recipe_images_dir()))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--commit", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entries = load_results(Path(args.results).resolve())
    images_root = Path(args.images_root).resolve()

    from _image_paths import ensure_app_on_path

    ensure_app_on_path()
    from app.database import SessionLocal
    from app.models.recipe import Recipe

    db = SessionLocal()
    moved = 0
    failed = 0
    correct_ids: set[int] = set()
    old_ids: set[int] = set()
    try:
        print(f"{'OLD_ID':>7} {'NEW_ID':>7}  {'FILES':<10} TITLE")
        print("-" * 70)
        for entry in entries:
            title = str(entry.get("title") or "")
            old_id = entry.get("recipe_id")
            try:
                new_id = resolve_v1_recipe_id_by_title(db, Recipe, title)
            except RecipeResolutionError as exc:
                failed += 1
                print(f"{str(old_id):>7} {'ERR':>7}  {'-':<10} {title}  -> {exc}")
                continue

            if isinstance(old_id, int):
                old_ids.add(old_id)
            correct_ids.add(new_id)

            action = "skip"
            if isinstance(old_id, int):
                action = relocate_image_folder(
                    old_id, new_id, images_root, dry_run=not args.commit
                )
            files_ok = action in ("dst_ready", "would_move", "moved")
            print(f"{str(old_id):>7} {new_id:>7}  {action:<10} {title}")

            if args.commit:
                target = db.get(Recipe, new_id)
                if target is None:
                    failed += 1
                    print(f"        WARN: recipe id {new_id} not in DB")
                    continue
                if files_ok:
                    urls = urls_for_recipe_id(new_id)
                    target.hero_image_url = urls["hero_image_url"]
                    target.image_url = urls["image_url"]
                    target.thumbnail_url = urls["thumbnail_url"]
                else:
                    # No files to back the URL — clear to avoid a 404.
                    target.hero_image_url = None
                    target.image_url = None
                    target.thumbnail_url = None
                    failed += 1
            if files_ok:
                moved += 1

        # Clear URLs on archived manual recipes (results old_ids + 1..10 range)
        # that did not legitimately resolve to themselves.
        cleared = 0
        for wrong_id in sorted(set(WRONG_MANUAL_IDS) | old_ids):
            if wrong_id in correct_ids:
                continue
            recipe = db.get(Recipe, wrong_id)
            if recipe is None:
                continue
            if any(
                getattr(recipe, attr)
                for attr in ("hero_image_url", "image_url", "thumbnail_url")
            ):
                print(
                    f"CLEAR  #{wrong_id}: {recipe.title!r} "
                    f"(source_type={recipe.source_type})"
                )
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
