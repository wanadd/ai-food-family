#!/usr/bin/env python3
"""Stage R: Gold V3 importer dry-run CLI (no DB writes)."""

from __future__ import annotations

import argparse
import json
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
    load_gold_v3_jsonl,
    plan_import_gold_v3_batch,
)

DEFAULT_INPUT = ROOT / "exports" / "recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl"
DEFAULT_QUALITY_REPORT = ROOT / "reports" / "recipe_gold_v3_stage_gh_quality_gate_report.gpt4o_mini.md"
DEFAULT_REPORT = ROOT / "reports" / "recipe_gold_v3_stage_r_importer_dry_run_report.md"

EM_DASH = "\u2014"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gold V3 importer dry-run")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--quality-report", type=Path, default=DEFAULT_QUALITY_REPORT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--allow-write", action="store_true", default=False)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


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


def build_report_md(args: argparse.Namespace, result: dict, quality_ok: bool) -> str:
    branch, commit = git_meta()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ms = result.get("mapping_summary") or {}

    lines = [
        f"# Recipe Gold V3 {EM_DASH} Stage R Importer Dry-Run Report",
        "",
        f"**Generated:** {now}",
        f"**Branch:** `{branch}`",
        f"**Commit:** `{commit}`",
        f"**Input:** `{args.input}`",
        f"**Quality report:** `{args.quality_report}`",
        f"**Quality report PASS:** `{quality_ok}`",
        f"**Mode:** `dry-run`",
        "",
        "## Safety",
        "",
        f"- DB write disabled: `{not args.allow_write}`",
        "- Image generation disabled: `true`",
        "- Safe reset disabled: `true`",
        "- Production DB unchanged: `true`",
        "",
        "## Summary",
        "",
        f"- Records: `{result.get('records', 0)}`",
        f"- Valid (validator): `{result.get('valid', 0)}`",
        f"- Would create: `{result.get('would_create', 0)}`",
        f"- Would update: `{result.get('would_update', 0)}`",
        f"- Would skip: `{result.get('would_skip', 0)}`",
        f"- Importer dry-run: **`{'PASS' if result.get('ok') else 'FAIL'}`**",
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
        "",
        "## Errors by code",
        "",
    ]

    errors = result.get("errors_by_code") or {}
    if errors:
        for code, count in sorted(errors.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"- {code}: `{count}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Warnings by code", ""])
    warnings = result.get("warnings_by_code") or {}
    if warnings:
        for code, count in sorted(warnings.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"- {code}: `{count}`")
    else:
        lines.append("- none")

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

    lines.extend(
        [
            "",
            "## UI compatibility notes",
            "",
            "- Recipe card KBJU uses `calories_per_serving`, `protein_g`, `fat_g`, `carbs_g` "
            f"{EM_DASH} mapped from Gold V3 nutrition_per_serving.",
            "- Recipe detail also exposes `sugar_g`, `fiber_g`; `salt_g` stored in `nutrition_coverage_json` (no dedicated column).",
            "- Shopping list merge uses ingredient `name` (= shopping_name) and `amount` (= display_amount).",
            "",
            "## Next step",
            "",
            f"- Stage R apply/import only after explicit approval (not implemented in this dry-run).",
            "",
            "## Not done",
            "",
        ]
    )
    for item in result.get("not_done") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    if not args.dry_run and not args.allow_write:
        print("ERROR: refuse non-dry-run without --allow-write", file=sys.stderr)
        return 1

    if not args.dry_run:
        print("ERROR: real import not implemented in Stage R", file=sys.stderr)
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

    session = None
    if args.allow_write:
        print("ERROR: --allow-write without apply implementation blocked", file=sys.stderr)
        return 1

    result = plan_import_gold_v3_batch(
        recipes,
        session=session,
        dry_run=True,
        require_quality_pass=True,
        quality_gate_ok=quality_ok,
    )

    report_text = build_report_md(args, result, quality_ok)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report_text, encoding="utf-8")

    print(
        f"records={result['records']} would_create={result['would_create']} "
        f"recommendation={'PASS' if result['ok'] else 'FAIL'}"
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
