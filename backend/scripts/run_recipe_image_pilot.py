#!/usr/bin/env python3
"""PlanAm V1 recipe image pilot runner.

Pilot only — 1 master image per recipe, then crop to hero/card/thumb and write
URLs to the DB. Designed for a small batch (default 10) from the pilot file.

Examples (run from the repository root):
    # Dry-run: no API calls, no files, no DB writes
    python backend/scripts/run_recipe_image_pilot.py \
        --pilot-file data/planam_v1_image_pilot_batch.json --limit 10 --dry-run

    # Single recipe, commit
    python backend/scripts/run_recipe_image_pilot.py --recipe-id 1 --commit

    # Batch of 10, commit
    python backend/scripts/run_recipe_image_pilot.py \
        --pilot-file data/planam_v1_image_pilot_batch.json --limit 10 --commit

Environment:
    PLANAM_IMAGE_OPENAI_API_KEY  dedicated image key (preferred)
    OPENAI_API_KEY               fallback only
    DATABASE_URL                 required for --commit
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "backend" / "scripts"
API_ROOT = ROOT / "apps" / "api"
for path in (str(SCRIPTS_DIR), str(API_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from apply_recipe_images import urls_from_local_recipe_id  # noqa: E402
from openai_recipe_image_client import (  # noqa: E402
    DEFAULT_MODEL,
    DEFAULT_QUALITY,
    DEFAULT_SIZE,
    estimate_cost,
    generate_master_image,
    is_image_pipeline_configured,
)
from process_recipe_images import process_master  # noqa: E402
from recipe_id_resolver import (  # noqa: E402
    RecipeResolutionError,
    resolve_v1_recipe_id_by_title,
)
from recipe_image_utils import build_master_prompt  # noqa: E402

DEFAULT_PILOT_FILE = ROOT / "data" / "planam_v1_image_pilot_batch.json"
DEFAULT_OUTPUT_ROOT = ROOT / "apps" / "web" / "public" / "recipe-images"
DEFAULT_RESULTS_PATH = ROOT / "reports" / "planam_v1_recipe_image_pilot_results.json"
LOCAL_URL_BASE = "/recipe-images"


def normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the recipe image pilot")
    parser.add_argument(
        "--pilot-file",
        default=str(DEFAULT_PILOT_FILE),
        help="Pilot batch JSON (list of recipe entries with master_prompt)",
    )
    parser.add_argument("--recipe-id", type=int, help="Run a single pilot entry by recipe_id")
    parser.add_argument("--limit", type=int, default=10, help="Max recipes in batch mode")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--size", default=DEFAULT_SIZE)
    parser.add_argument("--quality", default=DEFAULT_QUALITY, choices=["low", "medium", "high"])
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Root folder for generated images",
    )
    parser.add_argument(
        "--results",
        default=str(DEFAULT_RESULTS_PATH),
        help="Path for the pilot results JSON",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="No API, no files, no DB")
    mode.add_argument("--commit", action="store_true", help="Generate, crop, write DB")
    return parser.parse_args()


def load_pilot_entries(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Pilot file must be a JSON array")
    return [item for item in data if isinstance(item, dict)]


def select_entries(args: argparse.Namespace) -> list[dict[str, Any]]:
    entries = load_pilot_entries(Path(args.pilot_file).resolve())
    if args.recipe_id is not None:
        chosen = [e for e in entries if e.get("recipe_id") == args.recipe_id]
        if not chosen:
            raise SystemExit(f"recipe_id {args.recipe_id} not found in pilot file")
        return chosen[:1]
    return entries[: max(args.limit, 1)]


def resolve_prompt(entry: dict[str, Any]) -> str:
    prompt = str(entry.get("master_prompt") or "").strip()
    if prompt:
        return prompt
    return build_master_prompt(entry)


def resolve_db_recipe(entry: dict[str, Any]):
    """Resolve the real DB recipe by TITLE only (commit mode).

    The pilot JSON ``recipe_id`` is a batch index (1..N) and must never be used
    as a DB primary key — that bug assigned images to archived manual recipes.
    """
    from app.database import SessionLocal
    from app.models.recipe import Recipe

    db = SessionLocal()
    try:
        recipe_id = resolve_v1_recipe_id_by_title(db, Recipe, entry.get("title", ""))
        recipe = db.get(Recipe, recipe_id)
        return {"id": recipe.id, "title": recipe.title}
    finally:
        db.close()


def apply_urls_to_db(recipe_id: int, urls: dict[str, str]) -> None:
    from app.database import SessionLocal
    from app.models.recipe import Recipe

    db = SessionLocal()
    try:
        recipe = db.get(Recipe, recipe_id)
        if recipe is None:
            raise SystemExit(f"recipe id {recipe_id} disappeared before apply")
        recipe.hero_image_url = urls["hero_image_url"]
        recipe.image_url = urls["image_url"]
        recipe.thumbnail_url = urls["thumbnail_url"]
        db.commit()
    finally:
        db.close()


def run_dry_run(entries: list[dict[str, Any]], args: argparse.Namespace) -> int:
    print(f"DRY-RUN: {len(entries)} recipe(s); no API, no files, no DB")
    total_cost = 0.0
    for index, entry in enumerate(entries, start=1):
        cost = estimate_cost(args.size, args.quality, None)
        total_cost += cost
        batch_index = entry.get("recipe_id")
        title = entry.get("title", "")
        prompt = resolve_prompt(entry)
        print(f"\n[{index}] batch_index={batch_index} title={title!r}")
        print(f"    model={args.model} size={args.size} quality={args.quality}")
        print(f"    est_cost=${cost:.4f}")
        print("    db_id: resolved at --commit by TITLE (v1_import, is_active)")
        print(f"    prompt_preview={prompt[:90]!r}...")
    print(f"\nDRY-RUN total estimated cost: ${total_cost:.4f}")
    return 0


def run_commit(entries: list[dict[str, Any]], args: argparse.Namespace) -> int:
    if not is_image_pipeline_configured():
        raise SystemExit(
            "No image API key. Set PLANAM_IMAGE_OPENAI_API_KEY (or OPENAI_API_KEY)."
        )
    output_root = Path(args.output_root).resolve()
    results: list[dict[str, Any]] = []
    total_cost = 0.0
    failures = 0

    for index, entry in enumerate(entries, start=1):
        title = str(entry.get("title") or "")
        try:
            db_recipe = resolve_db_recipe(entry)
        except RecipeResolutionError as exc:
            failures += 1
            print(f"[{index}] SKIP: {exc}", file=sys.stderr)
            results.append(
                {
                    "recipe_id": None,
                    "title": title,
                    "status": "no_db_match",
                    "error": str(exc),
                    "approved": False,
                }
            )
            continue

        real_id = db_recipe["id"]
        recipe_dir = output_root / str(real_id)
        master_path = recipe_dir / "master.png"
        prompt = resolve_prompt(entry)
        started = time.monotonic()
        try:
            gen = generate_master_image(
                prompt=prompt,
                master_path=master_path,
                recipe_id=real_id,
                title=title,
                model=args.model,
                size=args.size,
                quality=args.quality,
            )
            process_master(master_path, recipe_dir, save_master_copy=True)
            urls = urls_from_local_recipe_id(real_id, public_base=LOCAL_URL_BASE)
            apply_urls_to_db(real_id, urls)
            duration = time.monotonic() - started
            total_cost += gen.estimated_cost_usd
            print(
                f"[{index}] OK recipe_id={real_id} title={title!r} "
                f"cost~${gen.estimated_cost_usd:.4f} {duration:.1f}s"
            )
            results.append(
                {
                    "recipe_id": real_id,
                    "title": title,
                    "prompt": prompt,
                    "status": "final_ready",
                    "duration_s": round(duration, 2),
                    "cost_usd": round(gen.estimated_cost_usd, 4),
                    "model": gen.model,
                    "size": gen.size,
                    "quality": gen.quality,
                    "usage": gen.usage,
                    "urls": urls,
                    "quality_score": None,
                    "approved": None,
                }
            )
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"[{index}] FAIL {title!r}: {exc}", file=sys.stderr)
            results.append(
                {
                    "recipe_id": real_id,
                    "title": title,
                    "status": "failed",
                    "error": str(exc),
                    "approved": False,
                }
            )

    results_path = Path(args.results).resolve()
    results_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "generated": len([r for r in results if r.get("status") == "final_ready"]),
        "failed": failures,
        "total_cost_usd": round(total_cost, 4),
        "model": args.model,
        "size": args.size,
        "quality": args.quality,
        "results": results,
    }
    results_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"\nPilot complete: generated={summary['generated']} failed={failures} "
        f"total_cost~${total_cost:.4f}"
    )
    print(f"Results: {results_path}")
    return 1 if failures else 0


def main() -> int:
    args = parse_args()
    os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))
    entries = select_entries(args)
    if args.dry_run:
        return run_dry_run(entries, args)
    return run_commit(entries, args)


if __name__ == "__main__":
    raise SystemExit(main())
