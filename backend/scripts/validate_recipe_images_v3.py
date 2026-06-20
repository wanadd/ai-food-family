#!/usr/bin/env python3
"""Stage IMG: validate Gold V3 recipe images (DB + filesystem + public URL)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _image_paths import (  # noqa: E402
    ensure_app_on_path,
    find_repo_file,
    recipe_images_dir,
    recipe_images_public_url,
)

ensure_app_on_path()

from app.recipes.image_generation_config import DEFAULT_ALLOWLIST_IDS, REQUIRED_DERIVATIVE_FILES
from app.recipes.recipe_gold_v3_image_pipeline import (
    IdNotAllowedError,
    ImagePipelineError,
    derivatives_complete,
    hero_file_path,
    load_created_ids_from_report,
    parse_ids_csv,
    validate_ids_allowed,
)

DEFAULT_CREATED_IDS = find_repo_file("reports", "recipe_gold_v3_stage_r_created_ids.json")
DEFAULT_REPORT = find_repo_file("reports", "recipe_gold_v3_image_availability_report.md")
DEFAULT_PUBLIC_SITE = "https://planam.ru"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Gold V3 recipe image availability")
    parser.add_argument("--ids", help="Comma-separated recipe IDs")
    parser.add_argument("--created-ids-report", type=Path, default=DEFAULT_CREATED_IDS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--public-site",
        default=os.environ.get("PLANAM_PUBLIC_SITE", DEFAULT_PUBLIC_SITE),
        help="Public site base for HTTP checks (default https://planam.ru)",
    )
    parser.add_argument(
        "--skip-http",
        action="store_true",
        help="Skip public URL HTTP checks (filesystem + DB only)",
    )
    return parser.parse_args()


def resolve_recipe_ids(args: argparse.Namespace) -> tuple[list[int], bool]:
    if args.ids:
        return parse_ids_csv(args.ids), True
    if args.created_ids_report.exists():
        return load_created_ids_from_report(args.created_ids_report), False
    return list(DEFAULT_ALLOWLIST_IDS), False


def check_public_url(url: str, timeout: float = 15.0) -> tuple[bool, int | None, str | None]:
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300, resp.status, None
    except urllib.error.HTTPError as exc:
        return False, exc.code, str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, None, str(exc)


def build_report(rows: list[dict], *, public_site: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    passed = sum(1 for r in rows if r.get("ok"))
    lines = [
        "# Recipe Gold V3 Image Availability Report",
        "",
        f"**Generated:** {now}",
        f"**Public site:** `{public_site}`",
        f"**Checked:** `{len(rows)}` recipes",
        f"**PASS:** `{passed}` / `{len(rows)}`",
        f"**Overall:** **`{'PASS' if passed == len(rows) and rows else 'FAIL'}`**",
        "",
        "## Per recipe",
        "",
    ]
    for row in rows:
        lines.append(f"- `{json.dumps(row, ensure_ascii=False)}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL required", file=sys.stderr)
        return 1

    try:
        recipe_ids, explicit_ids = resolve_recipe_ids(args)
        validate_ids_allowed(recipe_ids, explicit_ids=explicit_ids)
    except (ImagePipelineError, IdNotAllowedError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    images_root = recipe_images_dir()
    public_prefix = recipe_images_public_url()
    public_site = args.public_site.rstrip("/")

    from app.database import SessionLocal
    from app.models.recipe import Recipe

    session = SessionLocal()
    rows: list[dict] = []
    try:
        recipes = session.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()
        by_id = {int(r.id): r for r in recipes}
        for rid in recipe_ids:
            recipe = by_id.get(rid)
            row: dict = {"recipe_id": rid, "ok": False}
            if recipe is None:
                row.update({"status": "fail", "error": "recipe_not_found"})
                rows.append(row)
                continue

            hero_url = recipe.hero_image_url
            image_url = recipe.image_url
            thumb_url = recipe.thumbnail_url
            hero_file = hero_file_path(rid, images_root)
            deriv_ok = derivatives_complete(rid, images_root)

            row.update(
                {
                    "title": recipe.title,
                    "hero_image_url": hero_url,
                    "image_url": image_url,
                    "thumbnail_url": thumb_url,
                    "hero_file": str(hero_file),
                    "hero_file_exists": hero_file.is_file(),
                    "derivatives_complete": deriv_ok,
                    "required_files": list(REQUIRED_DERIVATIVE_FILES),
                }
            )

            db_ok = bool(hero_url)
            file_ok = hero_file.is_file() and deriv_ok
            http_ok = None
            http_status = None
            if not args.skip_http and hero_url:
                if hero_url.startswith("/"):
                    check_url = f"{public_site}{hero_url}"
                else:
                    check_url = hero_url
                http_ok, http_status, http_err = check_public_url(check_url)
                row["public_check_url"] = check_url
                row["public_http_ok"] = http_ok
                row["public_http_status"] = http_status
                if http_err:
                    row["public_http_error"] = http_err

            ok = db_ok and file_ok
            if not args.skip_http and hero_url:
                ok = ok and bool(http_ok)
            row["ok"] = ok
            row["status"] = "pass" if ok else "fail"
            if not db_ok:
                row["fail_reason"] = "hero_image_url_missing"
            elif not file_ok:
                row["fail_reason"] = "hero_or_derivatives_missing_on_disk"
            elif not args.skip_http and hero_url and not http_ok:
                row["fail_reason"] = "public_url_not_200"

            rows.append(row)
    finally:
        session.close()

    overall_ok = bool(rows) and all(r.get("ok") for r in rows)
    report_text = build_report(rows, public_site=public_site)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report_text, encoding="utf-8")

    passed = sum(1 for r in rows if r.get("ok"))
    print(
        f"checked={len(rows)} pass={passed} "
        f"recommendation={'PASS' if overall_ok else 'FAIL'}"
    )
    print(f"report={args.report}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
