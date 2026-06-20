#!/usr/bin/env python3
"""Stage IMG: generate and attach hero images for Gold V3 recipe batch."""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _image_paths import (  # noqa: E402
    ensure_app_on_path,
    find_repo_file,
    recipe_images_dir,
    recipe_images_public_url,
)
from apply_recipe_images import urls_from_local_recipe_id  # noqa: E402
from openai_recipe_image_client import (  # noqa: E402
    DEFAULT_MODEL,
    DEFAULT_QUALITY,
    DEFAULT_SIZE,
    ImageGenerationError,
    generate_master_image,
    is_image_pipeline_configured,
)
from process_recipe_images import process_master  # noqa: E402

ensure_app_on_path()

from app.recipes.image_generation_config import (  # noqa: E402
    DEFAULT_ALLOWLIST_IDS,
    MASTER_FILENAME,
    PROMPT_VERSION,
    api_key_status,
    get_settings,
)
from app.recipes.recipe_gold_v3_image_pipeline import (  # noqa: E402
    IdNotAllowedError,
    ImagePipelineError,
    RecipeImageTarget,
    apply_image_urls_to_recipe,
    build_master_prompt,
    check_apply_guards,
    load_created_ids_from_report,
    parse_ids_csv,
    plan_image_generation,
    recipe_to_prompt_dict,
)

DEFAULT_CREATED_IDS = find_repo_file("reports", "recipe_gold_v3_stage_r_created_ids.json")
DEFAULT_MD_REPORT = find_repo_file("reports", "recipe_image_generation_actual_cost_v3.md")
DEFAULT_JSON_REPORT = find_repo_file("reports", "recipe_image_generation_actual_cost_v3.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Gold V3 recipe images")
    parser.add_argument(
        "--ids",
        help="Comma-separated recipe IDs (explicit override of default allowlist guard)",
    )
    parser.add_argument(
        "--created-ids-report",
        type=Path,
        default=DEFAULT_CREATED_IDS,
        help="Stage R created IDs JSON",
    )
    parser.add_argument("--report-md", type=Path, default=DEFAULT_MD_REPORT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--force", action="store_true", help="Regenerate even when hero exists")
    parser.add_argument(
        "--max-cost-usd",
        type=float,
        default=None,
        help="Required for --apply — abort if estimated cost exceeds this cap",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", default=True, help="Default: plan only")
    mode.add_argument("--apply", action="store_true", help="Real generation + DB update")
    return parser.parse_args()


def resolve_recipe_ids(args: argparse.Namespace) -> tuple[list[int], bool]:
    if args.ids:
        return parse_ids_csv(args.ids), True
    if args.created_ids_report.exists():
        return load_created_ids_from_report(args.created_ids_report), False
    return list(DEFAULT_ALLOWLIST_IDS), False


def build_md_report(result: dict, settings: dict, key_status: dict, *, apply_mode: bool) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    title = "Actual" if apply_mode else "Dry-Run"
    lines = [
        f"# Recipe Image Generation {title} Report (Gold V3)",
        "",
        f"**Generated:** {now}",
        f"**Mode:** `{'apply' if apply_mode else 'dry-run'}`",
        f"**Style version:** `{PROMPT_VERSION}`",
        f"**Provider:** `{settings['provider']}`",
        f"**Model:** `{settings['model']}`",
        f"**API key env:** `{key_status['env_name']}` (configured: `{key_status['configured']}`)",
        "",
        "## Summary",
        "",
        f"- Recipe IDs: `{result.get('recipe_ids')}`",
        f"- Generated: `{result.get('generated_count', 0)}`",
        f"- Skipped: `{result.get('skipped_count', 0)}`",
        f"- Failed: `{result.get('failed_count', 0)}`",
        f"- Estimated cost USD: `${result.get('estimated_cost_usd', 0)}`",
        f"- Actual cost USD: `${result.get('actual_cost_usd', 0)}`",
        f"- Max cost USD cap: `{result.get('max_cost_usd')}`",
        f"- Idempotent full skip: `{result.get('idempotent_full_skip')}`",
        f"- Recommendation: **`{'PASS' if result.get('ok') else 'FAIL'}`**",
        "",
        "## Per recipe",
        "",
    ]
    for row in result.get("results") or []:
        lines.append(f"- `{json.dumps(row, ensure_ascii=False)}`")
    lines.extend(["", "## Errors", ""])
    errors = result.get("errors_by_code") or {}
    if errors:
        for code, count in sorted(errors.items()):
            lines.append(f"- {code}: `{count}`")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def run_generation_for_target(
    target: RecipeImageTarget,
    *,
    session: Any,
    images_root: Path,
    public_base: str,
    model: str,
    size: str,
    quality: str,
) -> dict[str, Any]:
    from app.models.recipe import Recipe

    recipe = session.get(Recipe, target.recipe_id)
    if recipe is None:
        return {
            "recipe_id": target.recipe_id,
            "title": target.title,
            "status": "failed",
            "error": "recipe_not_found",
        }

    out_dir = images_root / str(target.recipe_id)
    master_path = out_dir / MASTER_FILENAME
    prompt = target.master_prompt or build_master_prompt(recipe_to_prompt_dict(recipe))

    gen = generate_master_image(
        prompt=prompt,
        master_path=master_path,
        recipe_id=target.recipe_id,
        title=target.title,
        model=model,
        size=size,
        quality=quality,
        prompt_version=PROMPT_VERSION,
    )
    process_master(master_path, out_dir)
    urls = urls_from_local_recipe_id(target.recipe_id, public_base=public_base)
    apply_image_urls_to_recipe(session, target.recipe_id, urls)

    return {
        "recipe_id": target.recipe_id,
        "title": target.title,
        "status": "generated",
        "master_path": str(gen.master_path),
        "hero_url": urls["hero_image_url"],
        "estimated_cost_usd": gen.estimated_cost_usd,
        "duration_s": gen.duration_s,
    }


def main() -> int:
    args = parse_args()
    apply_mode = bool(args.apply)
    os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL required", file=sys.stderr)
        return 1

    if apply_mode and args.max_cost_usd is None:
        print("ERROR: --apply requires --max-cost-usd", file=sys.stderr)
        return 1

    try:
        recipe_ids, explicit_ids = resolve_recipe_ids(args)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: invalid IDs input: {exc}", file=sys.stderr)
        return 1

    images_root = recipe_images_dir()
    public_base = recipe_images_public_url()
    key_status = api_key_status()
    settings = get_settings(dry_run=not apply_mode, generation_enabled=apply_mode).as_dict()

    from app.database import SessionLocal

    session = SessionLocal()
    try:
        plan = plan_image_generation(
            session,
            recipe_ids,
            images_dir=images_root,
            force=args.force,
            explicit_ids=explicit_ids,
        )
    except (ImagePipelineError, IdNotAllowedError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()

    guard_ok, guard_code = check_apply_guards(
        apply_mode=apply_mode,
        max_cost_usd=args.max_cost_usd,
        estimated_cost_usd=float(plan.get("estimated_cost_usd") or 0),
        api_configured=key_status["configured"],
    )
    if apply_mode and not guard_ok:
        print(f"ERROR: apply guard failed: {guard_code}", file=sys.stderr)
        return 1

    result_rows: list[dict[str, Any]] = []
    actual_cost = 0.0
    generated_count = 0
    skipped_count = plan.get("to_skip_count", 0)
    failed_count = plan.get("failed_count", 0)

    if apply_mode:
        session = SessionLocal()
        try:
            for target in plan.get("to_skip") or []:
                result_rows.append(
                    {
                        "recipe_id": target.recipe_id,
                        "title": target.title,
                        "status": "skipped",
                        "reason": target.skip_reason,
                    }
                )
            for target in plan.get("failed") or []:
                result_rows.append(
                    {
                        "recipe_id": target.recipe_id,
                        "title": target.title,
                        "status": "failed",
                        "reason": target.skip_reason,
                    }
                )
            for target in plan.get("to_generate") or []:
                try:
                    row = run_generation_for_target(
                        target,
                        session=session,
                        images_root=images_root,
                        public_base=public_base,
                        model=DEFAULT_MODEL,
                        size=DEFAULT_SIZE,
                        quality=DEFAULT_QUALITY,
                    )
                    if row["status"] == "generated":
                        generated_count += 1
                        actual_cost += float(row.get("estimated_cost_usd") or 0)
                    else:
                        failed_count += 1
                    result_rows.append(row)
                except (ImageGenerationError, ImagePipelineError, Exception) as exc:
                    session.rollback()
                    failed_count += 1
                    result_rows.append(
                        {
                            "recipe_id": target.recipe_id,
                            "title": target.title,
                            "status": "failed",
                            "error": str(exc),
                            "traceback": traceback.format_exc(limit=3),
                        }
                    )
        finally:
            session.close()
    else:
        for row in plan.get("targets") or []:
            result_rows.append({**row, "mode": "dry-run"})
        if not is_image_pipeline_configured() and plan.get("to_generate_count", 0) > 0:
            print(
                f"NOTE: API key not configured ({key_status['env_name']}); "
                "dry-run only — no external calls",
            )

    ok = bool(plan.get("ok"))
    if apply_mode:
        ok = failed_count == 0 and (generated_count + skipped_count) == len(recipe_ids)

    result = {
        "ok": ok,
        "mode": "apply" if apply_mode else "dry-run",
        "recipe_ids": recipe_ids,
        "generated_count": generated_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "estimated_cost_usd": plan.get("estimated_cost_usd"),
        "actual_cost_usd": round(actual_cost, 4),
        "max_cost_usd": args.max_cost_usd,
        "idempotent_full_skip": plan.get("idempotent_full_skip"),
        "errors_by_code": plan.get("errors_by_code"),
        "warnings_by_code": plan.get("warnings_by_code"),
        "results": result_rows,
        "settings": settings,
        "api_key_status": key_status,
    }

    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report_md.write_text(
        build_md_report(result, settings, key_status, apply_mode=apply_mode),
        encoding="utf-8",
    )

    print(
        f"mode={'apply' if apply_mode else 'dry-run'} "
        f"would_generate={plan['to_generate_count']} "
        f"skipped={skipped_count} failed={failed_count} "
        f"estimated_usd={plan['estimated_cost_usd']} "
        f"actual_usd={result['actual_cost_usd']} "
        f"idempotent_full_skip={plan.get('idempotent_full_skip')} "
        f"recommendation={'PASS' if ok else 'FAIL'}"
    )
    print(f"report_md={args.report_md}")
    print(f"report_json={args.report_json}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
