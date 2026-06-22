"""Validate Gold V3 upgraded-30 recipe image assets (local, prod storage, public URLs)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from gold_v3_upgraded_30_photo_common import (  # noqa: E402
    EXPECTED_UPGRADE_IDS,
    EXPECTED_WIDTHS,
    MANIFEST_PATH,
    MAX_FILE_BYTES,
    MIN_FILE_BYTES,
    REQUIRED_FILES,
    load_manifest,
    manifest_recipe_ids,
    recipe_manifest_by_id,
    validate_manifest_ids,
)

REPORT_JSON = ROOT / "reports" / "SPRINT_1_5_IMAGE_ASSET_VALIDATION.json"
REPORT_MD = ROOT / "reports" / "SPRINT_1_5_IMAGE_ASSET_VALIDATION.md"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def inspect_image_file(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_file(),
        "size_bytes": None,
        "format": None,
        "width": None,
        "height": None,
        "ok": False,
        "issues": [],
    }
    if not path.is_file():
        result["issues"].append("missing_file")
        return result
    size = path.stat().st_size
    result["size_bytes"] = size
    if size < MIN_FILE_BYTES:
        result["issues"].append("file_too_small")
    if size > MAX_FILE_BYTES:
        result["issues"].append("file_too_large")
    try:
        from PIL import Image
    except Exception as exc:
        result["issues"].append(f"pillow_unavailable:{exc}")
        result["ok"] = not result["issues"]
        return result
    try:
        with Image.open(path) as image:
            result["format"] = (image.format or "").upper()
            result["width"] = int(image.width)
            result["height"] = int(image.height)
    except Exception as exc:
        result["issues"].append(f"image_read_failed:{exc}")
        return result
    if result["format"] != "WEBP":
        result["issues"].append("not_webp")
    min_w, max_w = EXPECTED_WIDTHS.get(path.name, (1, 10_000))
    width = int(result["width"] or 0)
    if width < min_w or width > max_w:
        result["issues"].append(f"width_out_of_range:{width}")
    result["ok"] = not result["issues"]
    return result


def check_public_url(public_base_url: str, recipe_id: int, filename: str, timeout: float) -> dict[str, Any]:
    url = f"{public_base_url.rstrip('/')}/recipe-images/{recipe_id}/{filename}"
    row: dict[str, Any] = {"url": url, "ok": False, "status": None, "error": None}
    try:
        request = Request(url, method="HEAD", headers={"User-Agent": "planam-gold-v3-image-validate/1.0"})
        with urlopen(request, timeout=timeout) as response:
            row["status"] = int(response.status)
            row["ok"] = 200 <= row["status"] < 400
    except HTTPError as exc:
        row["status"] = int(exc.code)
    except (URLError, TimeoutError, OSError) as exc:
        row["error"] = str(exc)
    return row


def validate(
    *,
    manifest: dict[str, Any],
    image_root: Path | None,
    public_base_url: str | None,
    public_timeout: float,
    strict_extra_ids: bool,
) -> dict[str, Any]:
    manifest_errors = validate_manifest_ids(manifest)
    by_id = recipe_manifest_by_id(manifest)
    items: list[dict[str, Any]] = []
    missing_assets = 0
    public_failures = 0

    for recipe_id in EXPECTED_UPGRADE_IDS:
        recipe = by_id.get(recipe_id) or {"id": recipe_id}
        row: dict[str, Any] = {
            "id": recipe_id,
            "title": recipe.get("display_title") or recipe.get("title") or "",
            "files": {},
            "public_urls": {},
            "ok": True,
            "issues": [],
        }
        for filename in REQUIRED_FILES:
            file_result: dict[str, Any] = {"local": None, "public": None}
            if image_root is not None:
                local_path = image_root / str(recipe_id) / filename
                local = inspect_image_file(local_path)
                file_result["local"] = local
                if not local["ok"]:
                    row["ok"] = False
                    row["issues"].append(f"missing_or_invalid:{filename}")
            if public_base_url:
                public = check_public_url(public_base_url, recipe_id, filename, public_timeout)
                file_result["public"] = public
                if not public["ok"]:
                    row["ok"] = False
                    public_failures += 1
                    row["issues"].append(f"public_url_failed:{filename}")
            row["files"][filename] = file_result
        if image_root is not None and any(
            not (row["files"][filename]["local"] or {}).get("ok") for filename in REQUIRED_FILES
        ):
            missing_assets += 1
        items.append(row)

    extra_ids: list[int] = []
    if image_root is not None and image_root.is_dir():
        for child in image_root.iterdir():
            if not child.is_dir():
                continue
            try:
                recipe_id = int(child.name)
            except ValueError:
                continue
            if recipe_id not in EXPECTED_UPGRADE_IDS:
                extra_ids.append(recipe_id)
        extra_ids.sort()

    errors = list(manifest_errors)
    if strict_extra_ids and extra_ids:
        errors.append(f"unexpected_recipe_dirs:{extra_ids}")
    if image_root is None and public_base_url is None:
        errors.append("no_validation_mode_selected")

    complete = sum(
        1
        for item in items
        if image_root is not None
        and all((item["files"][filename]["local"] or {}).get("ok") for filename in REQUIRED_FILES)
    )
    ok = not errors and all(item["ok"] for item in items if image_root is not None or public_base_url)

    return {
        "generated_at": now(),
        "ok": ok,
        "manifest_path": str(MANIFEST_PATH),
        "recipe_ids": manifest_recipe_ids(manifest),
        "image_root": str(image_root) if image_root else None,
        "public_base_url": public_base_url,
        "recipes_checked": len(items),
        "complete_triplets": complete,
        "missing_asset_count": missing_assets,
        "public_url_fail_count": public_failures,
        "extra_ids": extra_ids,
        "strict_extra_ids": strict_extra_ids,
        "errors": errors,
        "items": items,
        "image_generation_run": False,
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.5 Image Asset Validation",
        "",
        f"Generated: `{report['generated_at']}`",
        f"ok: `{report.get('ok')}`",
        f"recipes_checked: `{report.get('recipes_checked')}`",
        f"complete_triplets: `{report.get('complete_triplets')}`",
        f"missing_asset_count: `{report.get('missing_asset_count')}`",
        f"public_url_fail_count: `{report.get('public_url_fail_count')}`",
        f"image_root: `{report.get('image_root')}`",
        f"public_base_url: `{report.get('public_base_url')}`",
        "",
    ]
    if report.get("errors"):
        lines.extend(["## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
        lines.append("")
    blocked = [item for item in report.get("items") or [] if not item.get("ok")]
    if blocked:
        lines.extend(["## Failed items", ""])
        for item in blocked[:30]:
            lines.append(f"- {item['id']} {item.get('title')}: {item.get('issues')}")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--image-root", type=Path, default=None)
    parser.add_argument("--public-base-url", default=None)
    parser.add_argument("--public-timeout", type=float, default=8.0)
    parser.add_argument("--strict-extra-ids", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = load_manifest(args.manifest)
    image_root = args.image_root.resolve() if args.image_root else None
    report = validate(
        manifest=manifest,
        image_root=image_root,
        public_base_url=args.public_base_url,
        public_timeout=args.public_timeout,
        strict_extra_ids=args.strict_extra_ids,
    )
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render(report), encoding="utf-8")
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
