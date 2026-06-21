"""Verify Gold V3 pilot seed and local WebP assets."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = ROOT / "data" / "recipe_v2" / "gold_v3_pilot_10_seed.json"
PUBLIC_IMAGES = ROOT / "apps" / "web" / "public" / "recipe-images"
REPORTS = ROOT / "reports"
REPORT = REPORTS / "SPRINT_1_3B_GOLD_V3_PILOT_ASSET_VERIFY.md"
PILOT_IDS = list(range(256, 266))
REQUIRED_FILES = ("hero.webp", "card_800.webp", "thumb_400.webp")
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_recipes() -> tuple[list[dict[str, Any]], list[str]]:
    if not SEED_PATH.exists():
        return [], [f"Seed file missing: {SEED_PATH}"]
    try:
        data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [f"Seed JSON is invalid: {exc}"]
    recipes = data.get("recipes") if isinstance(data, dict) else data
    if not isinstance(recipes, list):
        return [], ["Seed must be a list or an object with a recipes list."]
    return recipes, []


def staged_files() -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
        )
    except Exception:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def db_check() -> dict[str, Any]:
    try:
        from sqlalchemy import create_engine, text
    except Exception as exc:
        return {"available": False, "error": f"sqlalchemy import failed: {exc}"}
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            rows = [
                dict(row._mapping)
                for row in conn.execute(
                    text(
                        """
                        SELECT id, title, hero_image_url, image_url, thumbnail_url, tags
                        FROM recipes
                        WHERE id = ANY(:ids)
                        ORDER BY id
                        """
                    ),
                    {"ids": PILOT_IDS},
                )
            ]
        return {
            "available": True,
            "count": len(rows),
            "ids": [row["id"] for row in rows],
            "all_image_urls_present": all(
                row.get("hero_image_url") and row.get("image_url") and row.get("thumbnail_url")
                for row in rows
            ),
        }
    except Exception as exc:
        return {"available": False, "error": repr(exc)}


def verify(include_db: bool) -> tuple[dict[str, Any], list[str]]:
    recipes, errors = load_recipes()
    seed_ids = sorted(recipe.get("id") for recipe in recipes if isinstance(recipe.get("id"), int))
    if seed_ids != PILOT_IDS:
        errors.append(f"Seed IDs must be {PILOT_IDS}, got {seed_ids}.")
    by_id = {recipe.get("id"): recipe for recipe in recipes}
    image_rows = []
    for recipe_id in PILOT_IDS:
        recipe = by_id.get(recipe_id)
        if recipe is None:
            errors.append(f"Missing seed recipe {recipe_id}.")
            continue
        expected_urls = {
            "hero_image_url": f"/recipe-images/{recipe_id}/hero.webp",
            "image_url": f"/recipe-images/{recipe_id}/card_800.webp",
            "thumbnail_url": f"/recipe-images/{recipe_id}/thumb_400.webp",
        }
        for field, expected in expected_urls.items():
            if recipe.get(field) != expected:
                errors.append(f"Recipe {recipe_id}: {field} must be {expected}.")
        files = {}
        for name in REQUIRED_FILES:
            path = PUBLIC_IMAGES / str(recipe_id) / name
            files[name] = path.exists()
            if not path.exists():
                errors.append(f"Missing image file: {path}")
        image_rows.append({"id": recipe_id, **files})

    staged = staged_files()
    forbidden = [
        path
        for path in staged
        if "backups/" in path
        or path.startswith("reports/")
        or path.endswith("master.png")
        or path.endswith("master.webp")
        or path.endswith(".tar.gz")
        or path.endswith(".csv")
    ]
    if forbidden:
        errors.append(f"Forbidden staged files: {forbidden}")

    result: dict[str, Any] = {
        "generated_at": now(),
        "seed_exists": SEED_PATH.exists(),
        "seed_count": len(recipes),
        "seed_ids": seed_ids,
        "image_rows": image_rows,
        "staged_forbidden_files": forbidden,
    }
    if include_db:
        result["db"] = db_check()
        db = result["db"]
        if db.get("available") and (db.get("count") != 10 or not db.get("all_image_urls_present")):
            errors.append(f"DB check failed: {db}")
    return result, errors


def render(result: dict[str, Any], errors: list[str]) -> str:
    lines = [
        "# Sprint 1.3B Gold V3 Pilot Asset Verify",
        "",
        f"Generated: `{result['generated_at']}`",
        f"OK: `{not errors}`",
        f"Seed exists: `{result['seed_exists']}`",
        f"Seed count: `{result['seed_count']}`",
        f"Seed IDs: `{result['seed_ids']}`",
        f"Forbidden staged files: `{result['staged_forbidden_files']}`",
        "",
        "## Images",
        "",
        "| id | hero.webp | card_800.webp | thumb_400.webp |",
        "| --- | --- | --- | --- |",
    ]
    for row in result["image_rows"]:
        lines.append(
            f"| {row['id']} | {row['hero.webp']} | {row['card_800.webp']} | {row['thumb_400.webp']} |"
        )
    if "db" in result:
        lines.extend(["", "## DB", "", f"`{result['db']}`"])
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in errors)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", action="store_true", help="Also verify DB rows and image URLs.")
    args = parser.parse_args()
    REPORTS.mkdir(exist_ok=True)
    result, errors = verify(args.db)
    REPORT.write_text(render(result, errors), encoding="utf-8")
    print(f"Wrote {REPORT}")
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
