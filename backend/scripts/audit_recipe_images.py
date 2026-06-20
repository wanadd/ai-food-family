#!/usr/bin/env python3
"""Read-only audit of recipe image URLs vs files on disk.

Reports recipes whose DB image URLs point to missing files, and image folders
on disk that no active recipe references. Never modifies the DB or files.

Usage (repo root or inside the api container):
    python backend/scripts/audit_recipe_images.py
    RECIPE_IMAGES_DIR=/app/public/recipe-images python backend/scripts/audit_recipe_images.py

Requires DATABASE_URL.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _image_paths import (  # noqa: E402
    ensure_app_on_path,
    recipe_images_dir,
    recipe_images_public_url,
)

REQUIRED_FILES = ("hero.webp", "card_800.webp", "thumb_400.webp")


def _url_to_local(url: str, public_base: str, images_root: Path) -> Path | None:
    if not url:
        return None
    prefix = public_base + "/"
    if not url.startswith(prefix):
        return None
    rel = url[len(prefix):]  # e.g. "75/hero.webp"
    return images_root / rel


def main() -> int:
    ensure_app_on_path()
    from app.database import SessionLocal
    from app.models.recipe import Recipe

    images_root = recipe_images_dir()
    public_base = recipe_images_public_url()
    print(f"images_root = {images_root}")
    print(f"public_url  = {public_base}")
    print("-" * 60)

    db = SessionLocal()
    missing_files = 0
    with_images = 0
    referenced_ids: set[str] = set()
    try:
        recipes = (
            db.query(Recipe)
            .filter(Recipe.is_active.is_(True))
            .filter(
                (Recipe.hero_image_url.isnot(None))
                | (Recipe.image_url.isnot(None))
                | (Recipe.thumbnail_url.isnot(None))
            )
            .all()
        )
        for recipe in recipes:
            with_images += 1
            urls = [
                recipe.hero_image_url,
                recipe.image_url,
                recipe.thumbnail_url,
            ]
            for url in urls:
                local = _url_to_local(url or "", public_base, images_root)
                if local is None:
                    continue
                referenced_ids.add(local.parent.name)
                if not local.is_file():
                    missing_files += 1
                    print(f"MISSING #{recipe.id} {recipe.title!r}: {url} -> {local}")

        # Folders on disk not referenced by any active recipe.
        orphans = 0
        if images_root.is_dir():
            for folder in sorted(images_root.iterdir()):
                if folder.is_dir() and folder.name not in referenced_ids:
                    if any((folder / name).is_file() for name in REQUIRED_FILES):
                        orphans += 1
                        print(f"ORPHAN folder {folder.name} (not referenced by active recipe)")

        print("-" * 60)
        print(
            f"active recipes with image URLs: {with_images}; "
            f"missing files: {missing_files}; orphan folders: {orphans}"
        )
        return 1 if missing_files else 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
