"""Verify Gold V3 pilot seed, local assets, external image roots, and public URLs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = ROOT / "data" / "recipe_v2" / "gold_v3_pilot_10_seed.json"
PUBLIC_IMAGES = ROOT / "apps" / "web" / "public" / "recipe-images"
REPORTS = ROOT / "reports"
REPORT = REPORTS / "SPRINT_1_3C_GOLD_V3_ASSET_VERIFY.md"
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


def expected_urls(recipe_id: int) -> dict[str, str]:
    return {
        "hero_image_url": f"/recipe-images/{recipe_id}/hero.webp",
        "image_url": f"/recipe-images/{recipe_id}/card_800.webp",
        "thumbnail_url": f"/recipe-images/{recipe_id}/thumb_400.webp",
    }


def file_rows(root: Path) -> tuple[list[dict[str, Any]], bool]:
    rows = []
    for recipe_id in PILOT_IDS:
        files = {}
        for name in REQUIRED_FILES:
            path = root / str(recipe_id) / name
            files[name] = path.exists()
        rows.append({"id": recipe_id, **files})
    ok = all(all(row[name] for name in REQUIRED_FILES) for row in rows)
    return rows, ok


def public_url_rows(public_base_url: str, timeout: float) -> tuple[list[dict[str, Any]], bool]:
    base = public_base_url.rstrip("/")
    rows = []
    for recipe_id in PILOT_IDS:
        row: dict[str, Any] = {"id": recipe_id}
        for name in REQUIRED_FILES:
            url = f"{base}/recipe-images/{recipe_id}/{name}"
            status: int | None = None
            error: str | None = None
            try:
                req = Request(url, method="HEAD", headers={"User-Agent": "planam-gold-v3-asset-verify/1.0"})
                with urlopen(req, timeout=timeout) as response:
                    status = int(response.status)
            except HTTPError as exc:
                status = int(exc.code)
            except URLError as exc:
                error = str(exc.reason)
            except Exception as exc:
                error = repr(exc)
            row[name] = status == 200
            row[f"{name}_status"] = status
            if error:
                row[f"{name}_error"] = error
        rows.append(row)
    ok = all(all(row[name] for name in REQUIRED_FILES) for row in rows)
    return rows, ok


def forbidden_staged_files() -> list[str]:
    return [
        path
        for path in staged_files()
        if "backups/" in path
        or path.startswith("reports/")
        or path.endswith("master.png")
        or path.endswith("master.webp")
        or path.endswith(".tar.gz")
        or path.endswith(".csv")
    ]


def verify(
    *,
    include_db: bool,
    image_root: Path | None,
    public_base_url: str | None,
    public_timeout: float,
) -> tuple[dict[str, Any], list[str]]:
    recipes, errors = load_recipes()
    seed_ids = sorted(recipe.get("id") for recipe in recipes if isinstance(recipe.get("id"), int))
    if seed_ids != PILOT_IDS:
        errors.append(f"Seed IDs must be {PILOT_IDS}, got {seed_ids}.")
    by_id = {recipe.get("id"): recipe for recipe in recipes}
    for recipe_id in PILOT_IDS:
        recipe = by_id.get(recipe_id)
        if recipe is None:
            errors.append(f"Missing seed recipe {recipe_id}.")
            continue
        for field, expected in expected_urls(recipe_id).items():
            if recipe.get(field) != expected:
                errors.append(f"Recipe {recipe_id}: {field} must be {expected}.")

    local_rows, local_ok = file_rows(PUBLIC_IMAGES)
    image_root_rows: list[dict[str, Any]] = []
    image_root_ok: bool | None = None
    if image_root is not None:
        image_root_rows, image_root_ok = file_rows(image_root)
    public_url_rows_data: list[dict[str, Any]] = []
    public_url_ok: bool | None = None
    if public_base_url:
        public_url_rows_data, public_url_ok = public_url_rows(public_base_url, public_timeout)

    forbidden = forbidden_staged_files()
    if forbidden:
        errors.append(f"Forbidden staged files: {forbidden}")

    mode_results = [local_ok]
    if image_root_ok is not None:
        mode_results.append(image_root_ok)
    if public_url_ok is not None:
        mode_results.append(public_url_ok)
    storage_ok = any(mode_results)
    if not storage_ok:
        errors.append("No asset storage mode passed.")

    result: dict[str, Any] = {
        "generated_at": now(),
        "seed_exists": SEED_PATH.exists(),
        "seed_count": len(recipes),
        "seed_ids": seed_ids,
        "local_repo_root": str(PUBLIC_IMAGES),
        "local_repo_rows": local_rows,
        "local_repo_ok": local_ok,
        "image_root": str(image_root) if image_root else None,
        "image_root_rows": image_root_rows,
        "image_root_ok": image_root_ok,
        "public_base_url": public_base_url,
        "public_url_rows": public_url_rows_data,
        "public_url_ok": public_url_ok,
        "staged_forbidden_files": forbidden,
        "overall_ok": not errors,
    }
    if include_db:
        result["db"] = db_check()
        db = result["db"]
        if db.get("available") and (db.get("count") != 10 or not db.get("all_image_urls_present")):
            errors.append(f"DB check failed: {db}")
            result["overall_ok"] = False
    return result, errors


def render_rows(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| id | hero.webp | card_800.webp | thumb_400.webp |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['hero.webp']} | {row['card_800.webp']} | {row['thumb_400.webp']} |"
        )
    return lines


def render(result: dict[str, Any], errors: list[str]) -> str:
    lines = [
        "# Sprint 1.3C Gold V3 Asset Verify",
        "",
        f"Generated: `{result['generated_at']}`",
        f"OK: `{not errors}`",
        f"Seed exists: `{result['seed_exists']}`",
        f"Seed count: `{result['seed_count']}`",
        f"Seed IDs: `{result['seed_ids']}`",
        f"local_repo_ok: `{result['local_repo_ok']}`",
        f"image_root_ok: `{result['image_root_ok']}`",
        f"public_url_ok: `{result['public_url_ok']}`",
        f"overall OK: `{not errors}`",
        f"Forbidden staged files: `{result['staged_forbidden_files']}`",
        "",
        "## Local Repo",
        "",
        f"Root: `{result['local_repo_root']}`",
        "",
    ]
    lines.extend(render_rows(result["local_repo_rows"]))
    if result.get("image_root") is not None:
        lines.extend(["", "## Image Root", "", f"Root: `{result['image_root']}`", ""])
        lines.extend(render_rows(result["image_root_rows"]))
    if result.get("public_base_url"):
        lines.extend(["", "## Public URL", "", f"Base URL: `{result['public_base_url']}`", ""])
        lines.extend(render_rows(result["public_url_rows"]))
    if "db" in result:
        lines.extend(["", "## DB", "", f"`{result['db']}`"])
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in errors)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", action="store_true", help="Also verify DB rows and image URLs.")
    parser.add_argument("--image-root", type=Path, default=None, help="External recipe image root.")
    parser.add_argument("--public-base-url", default=None, help="Public site base URL, e.g. https://planam.ru.")
    parser.add_argument("--public-timeout", type=float, default=5.0)
    args = parser.parse_args()
    REPORTS.mkdir(exist_ok=True)
    result, errors = verify(
        include_db=args.db,
        image_root=args.image_root,
        public_base_url=args.public_base_url,
        public_timeout=args.public_timeout,
    )
    REPORT.write_text(render(result, errors), encoding="utf-8")
    print(f"Wrote {REPORT}")
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
