#!/usr/bin/env python3
"""Stage R: Gold V3 importer CLI — dry-run and safe apply import."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_gold_v3_importer import (  # noqa: E402
    apply_import_gold_v3_batch,
    load_gold_v3_jsonl,
    plan_import_gold_v3_batch,
)

DEFAULT_INPUT = ROOT / "exports" / "recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl"
DEFAULT_QUALITY_REPORT = ROOT / "reports" / "recipe_gold_v3_stage_gh_quality_gate_report.gpt4o_mini.md"
DEFAULT_REPORT = ROOT / "reports" / "recipe_gold_v3_stage_r_importer_dry_run_report.md"
DEFAULT_APPLY_REPORT = ROOT / "reports" / "recipe_gold_v3_stage_r_apply_import_report.md"

EM_DASH = "\u2014"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gold V3 importer dry-run / apply")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--quality-report", type=Path, default=DEFAULT_QUALITY_REPORT)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--apply", action="store_true", default=False)
    parser.add_argument("--allow-write", action="store_true", default=False)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--expected-count",
        type=int,
        default=None,
        metavar="N",
        help="Safety guard: required for --apply; optional for --dry-run",
    )
    return parser.parse_args()


def validate_expected_count_guard(
    *,
    apply_mode: bool,
    expected_count: int | None,
    actual_count: int,
) -> tuple[bool, str | None]:
    if apply_mode and expected_count is None:
        return False, "expected_count_required_for_apply"
    if expected_count is not None and actual_count != expected_count:
        return False, "expected_count_mismatch"
    return True, None


def guard_failure_result(
    *,
    actual_count: int,
    expected_count: int | None,
    error_code: str,
) -> dict:
    return {
        "ok": False,
        "records": actual_count,
        "expected_count": expected_count,
        "actual_count": actual_count,
        "errors_by_code": {error_code: 1},
        "warnings_by_code": {},
        "not_done": [
            "DB import write",
            "safe reset",
            "old recipe updates",
            "old recipe deletes",
        ],
    }


def git_meta() -> tuple[str, str]:
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=ROOT, text=True
        ).strip()
        commit = subprocess.check_output(
            ["git", "log", "-1", "--oneline"], cwd=ROOT, text=True
        ).strip()
        return branch, commit
    except Exception:
        return "unknown", "unknown"


def quality_report_passes(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if re.search(r"Quality gate:\s*\*\*`PASS`\*\*", text, re.I):
        return True
    if re.search(r"Quality gate:\s*\*\*PASS\*\*", text, re.I):
        return True
    if re.search(r"quality gate:\s*PASS", text, re.I):
        return True
    return False


def build_report_md(
    args: argparse.Namespace,
    result: dict,
    quality_ok: bool,
    *,
    mode: str,
) -> str:
    branch, commit = git_meta()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ms = result.get("mapping_summary") or {}
    title = (
        "Stage R Importer Dry-Run Report"
        if mode == "dry-run"
        else "Stage R Apply Import Report"
    )

    lines = [
        f"# Recipe Gold V3 {EM_DASH} {title}",
        "",
        f"**Generated:** {now}",
        f"**Branch:** `{branch}`",
        f"**Commit:** `{commit}`",
        f"**Input:** `{args.input}`",
        f"**Quality report:** `{args.quality_report}`",
        f"**Quality report PASS:** `{quality_ok}`",
        f"**Mode:** `{mode}`",
        "",
        "## Safety",
        "",
        f"- DB write disabled: `{mode == 'dry-run'}`",
        "- Safe reset disabled: `true`",
        "- Old recipe updates: `false`",
        "- Old recipe deletes: `false`",
        f"- Expected count: `{args.expected_count if args.expected_count is not None else 'n/a'}`",
        f"- Actual count: `{result.get('actual_count', result.get('records', 0))}`",
        f"- Idempotent full skip: `{result.get('idempotent_full_skip', False)}`",
        "",
        "## Summary",
        "",
    ]

    if mode == "dry-run":
        lines.extend(
            [
                f"- Records: `{result.get('records', 0)}`",
                f"- Valid (validator): `{result.get('valid', 0)}`",
                f"- Would create: `{result.get('would_create', 0)}`",
                f"- Would update: `{result.get('would_update', 0)}`",
                f"- Would skip: `{result.get('would_skip', 0)}`",
                f"- Importer dry-run: **`{'PASS' if result.get('ok') else 'FAIL'}`**",
            ]
        )
        if ms:
            lines.extend(
                [
                    "",
                    "## Mapping summary",
                    "",
                    f"- Recipe fields: `{json.dumps(ms.get('recipe_fields', []), ensure_ascii=False)}`",
                    f"- Nutrition legacy UI: `{json.dumps(ms.get('nutrition_fields', {}).get('legacy_ui', []))}`",
                    f"- Nutrition summary columns: `{json.dumps(ms.get('nutrition_fields', {}).get('summary_columns', []))}`",
                    f"- Nutrition extras: `{json.dumps(ms.get('nutrition_fields', {}).get('extras', []))}`",
                    f"- UI primary: `{ms.get('nutrition_fields', {}).get('ui_primary', '')}`",
                    f"- Ingredient JSONB: `{ms.get('ingredient_fields', {}).get('jsonb', '')}`",
                    f"- Ingredient rows plan: `{ms.get('ingredient_fields', {}).get('rows_plan', '')}`",
                    f"- Shopping fields: `{json.dumps(ms.get('shopping_fields', []), ensure_ascii=False)}`",
                ]
            )
        lines.extend(["", "## Per recipe plan", ""])
        for row in result.get("per_recipe") or []:
            lines.append(f"- `{json.dumps(row, ensure_ascii=False)}`")
        lines.extend(["", "## DB duplicate findings", ""])
        db_dupes = result.get("db_duplicate_findings") or []
        if db_dupes:
            for row in db_dupes:
                lines.append(f"- `{json.dumps(row, ensure_ascii=False)}`")
        else:
            lines.append("- none (no session or no duplicates)")
    else:
        lines.extend(
            [
                f"- Records: `{result.get('records', 0)}`",
                f"- Created: `{result.get('created_count', 0)}`",
                f"- Skipped (idempotent): `{result.get('skipped_count', 0)}`",
                f"- Idempotent full skip: `{result.get('idempotent_full_skip', False)}`",
                f"- Old recipes touched: `{result.get('old_recipes_touched', 0)}`",
                f"- Apply import: **`{'PASS' if result.get('ok') else 'FAIL'}`**",
            ]
        )
        before = result.get("before_snapshot") or {}
        after = result.get("after_snapshot") or {}
        lines.extend(
            [
                "",
                "## Before / after counts",
                "",
                f"- recipes before: `{before.get('recipes_total', 'n/a')}`",
                f"- recipes after: `{after.get('recipes_total', 'n/a')}`",
                f"- recipe_ingredients before: `{before.get('recipe_ingredients_total', 'n/a')}`",
                f"- recipe_ingredients after: `{after.get('recipe_ingredients_total', 'n/a')}`",
                f"- max recipe id before: `{before.get('max_recipe_id', 'n/a')}`",
                f"- max recipe id after: `{after.get('max_recipe_id', 'n/a')}`",
                "",
                "## Created recipe IDs",
                "",
            ]
        )
        created = result.get("created") or []
        if created:
            for row in created:
                lines.append(f"- `{row.get('id')}` {EM_DASH} {row.get('title')}")
        else:
            lines.append("- none")

    lines.extend(["", "## Errors by code", ""])
    errors = result.get("errors_by_code") or {}
    if errors:
        for code, count in sorted(errors.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"- {code}: `{count}`")
    else:
        lines.append("- none")

    if mode == "dry-run":
        lines.extend(["", "## Warnings by code", ""])
        warnings = result.get("warnings_by_code") or {}
        if warnings:
            for code, count in sorted(warnings.items(), key=lambda x: (-x[1], x[0])):
                lines.append(f"- {code}: `{count}`")
        else:
            lines.append("- none")
        lines.extend(
            [
                "",
                "## UI compatibility notes",
                "",
                "- Recipe card KBJU uses `calories_per_serving`, `protein_g`, `fat_g`, `carbs_g` "
                f"{EM_DASH} mapped from Gold V3 nutrition_per_serving.",
                "- Recipe detail also exposes `sugar_g`, `fiber_g`; `salt_g` stored in `nutrition_coverage_json`.",
                "- Shopping list merge uses ingredient `name` (= shopping_name) and `amount` (= display_amount).",
            ]
        )

    lines.extend(["", "## Not done", ""])
    for item in result.get("not_done") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    apply_mode = args.apply or (not args.dry_run)

    if apply_mode and not args.allow_write:
        print("ERROR: refuse apply without --allow-write", file=sys.stderr)
        return 1

    quality_ok = quality_report_passes(args.quality_report)
    if not quality_ok:
        print(f"ERROR: quality report does not indicate PASS: {args.quality_report}", file=sys.stderr)
        return 1

    if not args.input.exists():
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        return 1

    try:
        loaded = load_gold_v3_jsonl(args.input)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    recipes = [row["recipe"] for row in loaded]
    if args.limit is not None:
        recipes = recipes[: args.limit]

    actual_count = len(recipes)
    report_path = args.report or (DEFAULT_APPLY_REPORT if apply_mode else DEFAULT_REPORT)

    guard_ok, guard_error = validate_expected_count_guard(
        apply_mode=apply_mode,
        expected_count=args.expected_count,
        actual_count=actual_count,
    )
    if not guard_ok:
        assert guard_error is not None
        print(
            f"ERROR: {guard_error} (expected={args.expected_count} actual={actual_count})",
            file=sys.stderr,
        )
        result = guard_failure_result(
            actual_count=actual_count,
            expected_count=args.expected_count,
            error_code=guard_error,
        )
        mode = "apply" if apply_mode else "dry-run"
        report_text = build_report_md(args, result, quality_ok, mode=mode)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_text, encoding="utf-8")
        print(f"report={report_path}")
        return 1

    if apply_mode:
        os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))
        if not os.environ.get("DATABASE_URL"):
            print("ERROR: DATABASE_URL required for --apply", file=sys.stderr)
            return 1
        from app.database import SessionLocal  # noqa: E402

        session = SessionLocal()
        try:
            result = apply_import_gold_v3_batch(
                recipes,
                session=session,
                require_quality_pass=True,
                quality_gate_ok=quality_ok,
            )
            result["expected_count"] = args.expected_count
            result["actual_count"] = actual_count
            result["not_done"] = [
                "safe reset",
                "old recipe updates",
                "old recipe deletes",
            ]
        finally:
            session.close()
        mode = "apply"
        print(
            f"created={result.get('created_count', 0)} "
            f"skipped={result.get('skipped_count', 0)} "
            f"recommendation={'PASS' if result.get('ok') else 'FAIL'}"
        )
    else:
        session = None
        db_url = os.environ.get("DATABASE_URL", "").strip()
        if db_url:
            from app.database import SessionLocal  # noqa: E402

            session = SessionLocal()
        try:
            result = plan_import_gold_v3_batch(
                recipes,
                session=session,
                dry_run=True,
                require_quality_pass=True,
                quality_gate_ok=quality_ok,
            )
            result["expected_count"] = args.expected_count
            result["actual_count"] = actual_count
        finally:
            if session is not None:
                session.close()
        mode = "dry-run"
        print(
            f"records={result['records']} would_create={result['would_create']} "
            f"would_skip={result['would_skip']} "
            f"idempotent_full_skip={result.get('idempotent_full_skip', False)} "
            f"recommendation={'PASS' if result['ok'] else 'FAIL'}"
        )

    report_text = build_report_md(args, result, quality_ok, mode=mode)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8")
    print(f"report={report_path}")

    if apply_mode and result.get("created"):
        created_path = ROOT / "reports" / "recipe_gold_v3_stage_r_created_ids.json"
        created_path.parent.mkdir(parents=True, exist_ok=True)
        created_path.write_text(
            json.dumps({"created": result["created"]}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"created_ids={created_path}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
