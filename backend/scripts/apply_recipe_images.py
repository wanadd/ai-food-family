#!/usr/bin/env python3
"""Apply recipe image URLs to the database from processed image folders.

Maps one master-derived set to:
  hero_image_url  -> hero.webp
  image_url       -> card_800.webp
  thumbnail_url   -> thumb_400.webp

Run from the repository root:
    python backend/scripts/apply_recipe_images.py --manifest data/recipe_image_manifest.json --dry-run
    python backend/scripts/apply_recipe_images.py --recipe-id 42 --base-url https://cdn.planam.ru/recipes/42 --commit

Requires DATABASE_URL.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))

CDN_BASE_DEFAULT = "https://cdn.planam.ru/recipes"
LOCAL_BASE_DEFAULT = "/recipe-images"


def normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def urls_from_base(base_url: str) -> dict[str, str]:
    base = base_url.rstrip("/")
    return {
        "hero_image_url": f"{base}/hero.webp",
        "image_url": f"{base}/card_800.webp",
        "thumbnail_url": f"{base}/thumb_400.webp",
    }


def urls_from_local_recipe_id(recipe_id: int, *, public_base: str) -> dict[str, str]:
    base = f"{public_base.rstrip('/')}/{recipe_id}"
    return {
        "hero_image_url": f"{base}/hero.webp",
        "image_url": f"{base}/card_800.webp",
        "thumbnail_url": f"{base}/thumb_400.webp",
    }


def verify_files_exist(recipe_id: int, images_root: Path) -> bool:
    folder = images_root / str(recipe_id)
    required = ("hero.webp", "card_800.webp", "thumb_400.webp")
    return folder.is_dir() and all((folder / name).is_file() for name in required)


def load_manifest(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "recipes" in data:
        items = data["recipes"]
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError("Manifest must be a list or {recipes: [...]}")
    if not isinstance(items, list):
        raise ValueError("Manifest recipes must be a list")
    return items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply recipe image URLs to DB")
    parser.add_argument(
        "--manifest",
        help="JSON manifest with recipe_id and optional base_url/title",
    )
    parser.add_argument("--recipe-id", type=int, help="Single recipe ID")
    parser.add_argument(
        "--base-url",
        help="CDN base URL for single recipe (e.g. https://cdn.planam.ru/recipes/42)",
    )
    parser.add_argument(
        "--images-root",
        default=str(ROOT / "apps" / "web" / "public" / "recipe-images"),
        help="Local images root for file existence check",
    )
    parser.add_argument(
        "--cdn-base",
        default=CDN_BASE_DEFAULT,
        help="CDN prefix when manifest omits base_url",
    )
    parser.add_argument(
        "--local-base",
        default=LOCAL_BASE_DEFAULT,
        help="Public URL prefix for local serving",
    )
    parser.add_argument(
        "--require-files",
        action="store_true",
        help="Skip entries when local WebP files are missing",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--commit", action="store_true")
    return parser.parse_args()


def resolve_entries(args: argparse.Namespace) -> list[dict]:
    entries: list[dict] = []
    if args.manifest:
        manifest_path = Path(args.manifest).resolve()
        if not manifest_path.exists():
            raise SystemExit(f"Manifest not found: {manifest_path}")
        for raw in load_manifest(manifest_path):
            if not isinstance(raw, dict):
                continue
            recipe_id = raw.get("recipe_id")
            if recipe_id is None:
                continue
            base_url = raw.get("base_url")
            if not base_url:
                base_url = f"{args.cdn_base.rstrip('/')}/{int(recipe_id)}"
            entries.append(
                {
                    "recipe_id": int(recipe_id),
                    "title": raw.get("title"),
                    "base_url": str(base_url),
                }
            )
    elif args.recipe_id is not None:
        base_url = args.base_url
        if not base_url:
            base_url = f"{args.cdn_base.rstrip('/')}/{args.recipe_id}"
        entries.append(
            {
                "recipe_id": args.recipe_id,
                "title": None,
                "base_url": base_url,
            }
        )
    else:
        raise SystemExit("Provide --manifest or --recipe-id")
    return entries


def apply_entries(entries: list[dict], *, dry_run: bool, args: argparse.Namespace) -> int:
    from app.database import SessionLocal
    from app.models.recipe import Recipe

    images_root = Path(args.images_root).resolve()
    db = SessionLocal()
    updated = 0
    skipped = 0
    failed = 0
    try:
        for entry in entries:
            recipe_id = entry["recipe_id"]
            if args.require_files and not verify_files_exist(recipe_id, images_root):
                skipped += 1
                print(f"SKIP #{recipe_id}: missing local WebP files")
                continue

            recipe = db.get(Recipe, recipe_id)
            if recipe is None and entry.get("title"):
                title_key = normalize_title(str(entry["title"]))
                recipe = (
                    db.query(Recipe)
                    .filter(Recipe.normalized_title == title_key)
                    .first()
                )
            if recipe is None:
                failed += 1
                print(f"FAIL #{recipe_id}: recipe not found in DB")
                continue

            urls = urls_from_base(entry["base_url"])
            label = recipe.title
            if dry_run:
                print(f"DRY-RUN UPDATE #{recipe.id}: {label}")
                print(f"  hero: {urls['hero_image_url']}")
                print(f"  card: {urls['image_url']}")
                print(f"  thumb: {urls['thumbnail_url']}")
            else:
                recipe.hero_image_url = urls["hero_image_url"]
                recipe.image_url = urls["image_url"]
                recipe.thumbnail_url = urls["thumbnail_url"]
                db.commit()
                print(f"UPDATE #{recipe.id}: {label}")
            updated += 1

        print(f"Summary: updated={updated}, skipped={skipped}, failed={failed}")
        return 1 if failed else 0
    finally:
        db.close()


def main() -> int:
    args = parse_args()
    entries = resolve_entries(args)
    if not entries:
        print("No entries to apply", file=sys.stderr)
        return 2
    return apply_entries(entries, dry_run=not args.commit, args=args)


if __name__ == "__main__":
    raise SystemExit(main())
