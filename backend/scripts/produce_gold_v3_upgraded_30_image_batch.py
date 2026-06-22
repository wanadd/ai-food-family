#!/usr/bin/env python3
"""Produce Gold V3 upgraded-30 recipe images from manifest (no DB writes).

Writes WebP derivatives to a staging root, default:
  artifacts/recipe-images/{id}/hero.webp
  artifacts/recipe-images/{id}/card_800.webp
  artifacts/recipe-images/{id}/thumb_400.webp

Examples:
  python backend/scripts/produce_gold_v3_upgraded_30_image_batch.py --dry-run
  python backend/scripts/produce_gold_v3_upgraded_30_image_batch.py --generate --max-cost-usd 3
  python backend/scripts/produce_gold_v3_upgraded_30_image_batch.py --generate --recipe-ids 2,235,254 --overwrite --max-cost-usd 1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
API_ROOT = ROOT / "apps" / "api"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if (API_ROOT / "app").is_dir() and str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
elif (ROOT / "app").is_dir() and str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gold_v3_upgraded_30_photo_common import (  # noqa: E402
    EXPECTED_UPGRADE_IDS,
    MANIFEST_PATH,
    REQUIRED_FILES,
    load_manifest,
    recipe_manifest_by_id,
)
from openai_recipe_image_client import (  # noqa: E402
    DEFAULT_MODEL,
    DEFAULT_QUALITY,
    DEFAULT_SIZE,
    ImageGenerationError,
    generate_master_image,
    is_image_pipeline_configured,
)
from process_recipe_images import process_master  # noqa: E402

from app.recipes.image_generation_config import (  # noqa: E402
    ESTIMATED_COST_PER_IMAGE_USD,
    PROMPT_VERSION,
)
from app.recipes.recipe_gold_v3_image_pipeline import build_master_prompt  # noqa: E402

DEFAULT_OUTPUT_ROOT = ROOT / "artifacts" / "recipe-images"
REPORT_JSON = ROOT / "reports" / "SPRINT_1_5B_IMAGE_PRODUCTION_BATCH.json"
MASTER_FILENAME = "master.png"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def manifest_prompt_dict(recipe: dict[str, Any]) -> dict[str, Any]:
    title = str(recipe.get("display_title") or recipe.get("title") or "").strip()
    meal_type = str(recipe.get("meal_type") or "dinner")
    return {
        "title": title,
        "display_title": title,
        "meal_type": meal_type,
        "category": "main",
        "ingredients": [{"name": name} for name in recipe.get("key_ingredients") or []],
    }


def resolve_prompt(recipe: dict[str, Any]) -> str:
    custom = str(recipe.get("image_prompt") or "").strip()
    built = build_master_prompt(manifest_prompt_dict(recipe))
    if custom and len(custom) < 80:
        return built
    if custom:
        return f"{built}\n\nAdditional style note: {custom}"
    return built


def derivatives_complete(recipe_dir: Path) -> bool:
    return recipe_dir.is_dir() and all((recipe_dir / name).is_file() for name in REQUIRED_FILES)


def parse_recipe_ids(
    manifest: dict[str, Any],
    *,
    recipe_ids_arg: str | None,
    recipe_id_args: list[int],
) -> tuple[list[int] | None, list[str]]:
    """Resolve and validate selective recipe IDs against the manifest."""
    errors: list[str] = []
    if recipe_ids_arg:
        raw_parts = [part.strip() for part in recipe_ids_arg.split(",") if part.strip()]
        try:
            parsed = [int(part) for part in raw_parts]
        except ValueError:
            return None, ["invalid_recipe_ids:not_integers"]
        if not parsed:
            return None, ["invalid_recipe_ids:empty"]
        recipe_id_args = parsed
    if not recipe_id_args:
        return None, []
    seen: set[int] = set()
    duplicates: list[int] = []
    for recipe_id in recipe_id_args:
        if recipe_id in seen:
            duplicates.append(recipe_id)
        seen.add(recipe_id)
    if duplicates:
        errors.append(f"duplicate_recipe_ids:{sorted(set(duplicates))}")
    manifest_ids = {int(recipe["id"]) for recipe in manifest.get("recipes") or []}
    allowed = set(EXPECTED_UPGRADE_IDS)
    unknown = sorted({recipe_id for recipe_id in recipe_id_args if recipe_id not in manifest_ids})
    if unknown:
        errors.append(f"unknown_recipe_ids:{unknown}")
    disallowed = sorted({recipe_id for recipe_id in recipe_id_args if recipe_id not in allowed})
    if disallowed:
        errors.append(f"recipe_ids_not_in_upgrade_set:{disallowed}")
    if errors:
        return None, errors
    return recipe_id_args, []


def plan_batch(
    manifest: dict[str, Any],
    *,
    output_root: Path,
    recipe_ids: list[int] | None,
    skip_existing: bool,
) -> dict[str, Any]:
    by_id = recipe_manifest_by_id(manifest)
    ids = recipe_ids or EXPECTED_UPGRADE_IDS
    to_generate: list[dict[str, Any]] = []
    to_skip: list[dict[str, Any]] = []
    for recipe_id in ids:
        recipe = by_id.get(recipe_id)
        if recipe is None:
            to_skip.append({"id": recipe_id, "reason": "missing_manifest_entry"})
            continue
        out_dir = output_root / str(recipe_id)
        if skip_existing and derivatives_complete(out_dir):
            to_skip.append({"id": recipe_id, "reason": "derivatives_exist"})
            continue
        to_generate.append(
            {
                "id": recipe_id,
                "title": recipe.get("display_title") or recipe.get("title"),
                "prompt_preview": resolve_prompt(recipe)[:160],
            }
        )
    estimated_cost = round(len(to_generate) * ESTIMATED_COST_PER_IMAGE_USD, 4)
    return {
        "recipe_ids": ids,
        "to_generate": to_generate,
        "to_skip": to_skip,
        "to_generate_count": len(to_generate),
        "to_skip_count": len(to_skip),
        "estimated_cost_usd": round(estimated_cost, 4),
        "output_root": str(output_root),
        "api_configured": is_image_pipeline_configured(),
    }


def generate_one(
    recipe: dict[str, Any],
    *,
    output_root: Path,
    model: str,
    size: str,
    quality: str,
) -> dict[str, Any]:
    recipe_id = int(recipe["id"])
    title = str(recipe.get("display_title") or recipe.get("title") or "")
    out_dir = output_root / str(recipe_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    master_path = out_dir / MASTER_FILENAME
    prompt = resolve_prompt(recipe)
    started = time.monotonic()
    gen = generate_master_image(
        prompt=prompt,
        master_path=master_path,
        recipe_id=recipe_id,
        title=title,
        model=model,
        size=size,
        quality=quality,
        prompt_version=PROMPT_VERSION,
    )
    process_master(master_path, out_dir, save_master_copy=False)
    missing = [name for name in REQUIRED_FILES if not (out_dir / name).is_file()]
    if missing:
        raise ImageGenerationError(f"derivatives_missing:{missing}")
    duration = time.monotonic() - started
    return {
        "id": recipe_id,
        "title": title,
        "status": "generated",
        "duration_s": round(duration, 2),
        "estimated_cost_usd": gen.estimated_cost_usd,
        "output_dir": str(out_dir),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--recipe-id", type=int, action="append", default=[], help="Repeatable recipe ID")
    parser.add_argument(
        "--recipe-ids",
        default=None,
        help="Comma-separated recipe IDs from manifest (e.g. 2,235,254)",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--size", default=DEFAULT_SIZE)
    parser.add_argument("--quality", default=DEFAULT_QUALITY)
    parser.add_argument("--max-cost-usd", type=float, default=None)
    parser.add_argument("--skip-existing", action="store_true", default=True)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate even when derivatives exist (alias for --force)",
    )
    parser.add_argument("--force", action="store_true", help="Regenerate even when derivatives exist")
    parser.add_argument("--dry-run", action="store_true", help="Plan only (default)")
    parser.add_argument("--generate", action="store_true", help="Call OpenAI and write WebP files")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.generate and args.dry_run:
        print("Use either --dry-run or --generate, not both.", file=sys.stderr)
        return 2
    generate_mode = bool(args.generate)
    manifest = load_manifest(args.manifest)
    output_root = args.output_root.resolve()
    recipe_ids, id_errors = parse_recipe_ids(
        manifest,
        recipe_ids_arg=args.recipe_ids,
        recipe_id_args=[int(rid) for rid in args.recipe_id],
    )
    if id_errors:
        for err in id_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 2
    overwrite = bool(args.overwrite or args.force)
    skip_existing = args.skip_existing and not overwrite
    plan = plan_batch(manifest, output_root=output_root, recipe_ids=recipe_ids, skip_existing=skip_existing)

    report: dict[str, Any] = {
        "generated_at": now(),
        "mode": "generate" if generate_mode else "dry-run",
        "plan": plan,
        "results": [],
        "generated_count": 0,
        "failed_count": 0,
        "skipped_count": plan["to_skip_count"],
        "actual_cost_usd": 0.0,
        "db_writes": 0,
        "image_generation_run": generate_mode,
    }

    if not generate_mode:
        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        print(f"Wrote {REPORT_JSON}")
        return 0

    if not is_image_pipeline_configured():
        print("ERROR: PLANAM_IMAGE_OPENAI_API_KEY or OPENAI_API_KEY required for --generate", file=sys.stderr)
        return 1
    if args.max_cost_usd is None:
        print("ERROR: --generate requires --max-cost-usd", file=sys.stderr)
        return 1
    if float(plan["estimated_cost_usd"]) > float(args.max_cost_usd):
        print(
            f"ERROR: estimated cost ${plan['estimated_cost_usd']} exceeds cap ${args.max_cost_usd}",
            file=sys.stderr,
        )
        return 1

    by_id = recipe_manifest_by_id(manifest)
    for skip in plan["to_skip"]:
        report["results"].append({**skip, "status": "skipped"})

    for item in plan["to_generate"]:
        recipe_id = int(item["id"])
        recipe = by_id[recipe_id]
        try:
            row = generate_one(
                recipe,
                output_root=output_root,
                model=args.model,
                size=args.size,
                quality=args.quality,
            )
            report["results"].append(row)
            report["generated_count"] += 1
            report["actual_cost_usd"] = round(float(report["actual_cost_usd"]) + float(row["estimated_cost_usd"]), 4)
            print(f"OK {recipe_id} {row['title']!r} ${row['estimated_cost_usd']:.4f}")
        except Exception as exc:  # noqa: BLE001
            report["failed_count"] += 1
            report["results"].append(
                {"id": recipe_id, "title": item.get("title"), "status": "failed", "error": repr(exc)}
            )
            print(f"FAIL {recipe_id}: {exc}", file=sys.stderr)

    report["ok"] = report["failed_count"] == 0 and report["generated_count"] == plan["to_generate_count"]
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_JSON}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
