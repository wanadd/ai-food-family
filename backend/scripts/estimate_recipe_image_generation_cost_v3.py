#!/usr/bin/env python3
"""Stage IMG: cost estimate for Gold V3 recipe image generation (no API calls)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _image_paths import ensure_app_on_path, find_repo_file, recipe_images_dir  # noqa: E402

ensure_app_on_path()

from app.recipes.image_generation_config import (  # noqa: E402
    DEFAULT_ALLOWLIST_IDS,
    get_settings,
    api_key_status,
)
from app.recipes.recipe_gold_v3_image_pipeline import (  # noqa: E402
    IdNotAllowedError,
    ImagePipelineError,
    load_created_ids_from_report,
    parse_ids_csv,
    plan_image_generation,
)

DEFAULT_CREATED_IDS = find_repo_file("reports", "recipe_gold_v3_stage_r_created_ids.json")
DEFAULT_MD_REPORT = find_repo_file("reports", "recipe_image_generation_cost_estimate_v3.md")
DEFAULT_JSON_REPORT = find_repo_file("reports", "recipe_image_generation_cost_estimate_v3.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Estimate Gold V3 recipe image generation cost")
    parser.add_argument(
        "--ids",
        help="Comma-separated recipe IDs (explicit override of default allowlist guard)",
    )
    parser.add_argument(
        "--created-ids-report",
        type=Path,
        default=DEFAULT_CREATED_IDS,
        help="Stage R created IDs JSON (default IDs from report when --ids omitted)",
    )
    parser.add_argument("--report-md", type=Path, default=DEFAULT_MD_REPORT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--dry-run", action="store_true", default=True, help="Always no-op (default)")
    return parser.parse_args()


def resolve_recipe_ids(args: argparse.Namespace) -> tuple[list[int], bool]:
    if args.ids:
        return parse_ids_csv(args.ids), True
    if args.created_ids_report.exists():
        return load_created_ids_from_report(args.created_ids_report), False
    return list(DEFAULT_ALLOWLIST_IDS), False


def build_md_report(plan: dict, settings: dict, key_status: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Recipe Image Generation Cost Estimate (Gold V3)",
        "",
        f"**Generated:** {now}",
        f"**Style version:** `{plan.get('style_version')}`",
        f"**Provider:** `{settings['provider']}`",
        f"**Model:** `{settings['model']}`",
        f"**Size:** `{settings['size']}`",
        f"**Quality:** `{settings['quality']}`",
        f"**API key env:** `{key_status['env_name']}` (configured: `{key_status['configured']}`)",
        f"**Cost per image (est.):** `${plan.get('cost_per_image_usd')}`",
        "",
        "## Summary",
        "",
        f"- Recipe IDs: `{plan.get('recipe_ids')}`",
        f"- Would generate: `{plan.get('to_generate_count')}`",
        f"- Would skip (existing): `{plan.get('to_skip_count')}`",
        f"- Failed checks: `{plan.get('failed_count')}`",
        f"- Estimated total USD: **`${plan.get('estimated_cost_usd')}`**",
        f"- Idempotent full skip: `{plan.get('idempotent_full_skip')}`",
        f"- Plan OK: **`{'PASS' if plan.get('ok') else 'FAIL'}`**",
        "",
        "## Per recipe",
        "",
    ]
    for row in plan.get("targets") or []:
        lines.append(f"- `{json.dumps(row, ensure_ascii=False)}`")
    lines.extend(["", "## Errors", ""])
    errors = plan.get("errors_by_code") or {}
    if errors:
        for code, count in sorted(errors.items()):
            lines.append(f"- {code}: `{count}`")
    else:
        lines.append("- none")
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
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: invalid IDs input: {exc}", file=sys.stderr)
        return 1

    from app.database import SessionLocal

    session = SessionLocal()
    try:
        plan = plan_image_generation(
            session,
            recipe_ids,
            images_dir=recipe_images_dir(),
            force=False,
            explicit_ids=explicit_ids,
        )
    except (ImagePipelineError, IdNotAllowedError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()

    settings = get_settings(dry_run=True).as_dict()
    key_status = api_key_status()
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "settings": settings,
        "api_key_status": key_status,
        "plan": {
            k: v
            for k, v in plan.items()
            if k not in {"to_generate", "to_skip", "failed"}
        },
        "targets": plan.get("targets"),
    }

    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report_md.write_text(build_md_report(plan, settings, key_status), encoding="utf-8")

    print(
        f"ids={recipe_ids} would_generate={plan['to_generate_count']} "
        f"would_skip={plan['to_skip_count']} estimated_usd={plan['estimated_cost_usd']} "
        f"recommendation={'PASS' if plan['ok'] else 'FAIL'}"
    )
    print(f"report_md={args.report_md}")
    print(f"report_json={args.report_json}")
    return 0 if plan.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
