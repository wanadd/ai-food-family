#!/usr/bin/env python3
"""Stage G/H: Gold V3 batch originality + quality gate CLI (no DB import)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_gold_v3_quality_gate import evaluate_recipe_gold_v3_quality_gate  # noqa: E402

DEFAULT_INPUT = ROOT / "exports" / "recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl"
DEFAULT_SIGNALS = ROOT / "exports" / "povarenok_culinary_signals_v3_100.jsonl"
DEFAULT_REPORT = ROOT / "reports" / "recipe_gold_v3_stage_gh_quality_gate_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gold V3 batch quality gate")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--signals", type=Path, default=DEFAULT_SIGNALS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-score", type=int, default=85)
    parser.add_argument("--avg-score", type=float, default=90.0)
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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


def build_report_md(args: argparse.Namespace, result: dict) -> str:
    branch, commit = git_meta()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    s = result["summary"]

    lines = [
        "# Recipe Gold V3 \u2014 Stage G/H Quality Gate Report",
        "",
        f"**Generated:** {now}",
        f"**Branch:** `{branch}`",
        f"**Commit:** `{commit}`",
        f"**Input:** `{args.input}`",
        f"**Signals:** `{args.signals}`",
        f"**Mode:** `{'dry-run' if args.dry_run else 'apply'}`",
        "",
        "## Summary",
        "",
        f"- Records: `{s['records']}`",
        f"- Valid (validator): `{s['valid']}`",
        f"- Invalid: `{s['invalid']}`",
        f"- Avg score: `{s['avg_score']}`",
        f"- Min score threshold: `{s['min_score_threshold']}`",
        f"- Avg score threshold: `{s['avg_score_threshold']}`",
        f"- Originality: `{s['originality']}`",
        f"- Duplicate check: `{s['duplicate_check']}`",
        f"- Diversity: `{s['diversity']}`",
        f"- Quality gate: **`{s['quality_gate']}`**",
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

    lines.extend(["", "## Per recipe", ""])
    for row in result.get("per_recipe") or []:
        lines.append(f"- `{json.dumps(row, ensure_ascii=False)}`")

    lines.extend(["", "## Pairwise similarity findings", ""])
    pairwise = result.get("pairwise") or []
    if pairwise:
        for row in pairwise:
            lines.append(f"- `{json.dumps(row, ensure_ascii=False)}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Signal similarity findings", ""])
    signal_findings = result.get("signal_findings") or []
    if signal_findings:
        for row in signal_findings:
            lines.append(f"- `{json.dumps(row, ensure_ascii=False)}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Diversity", ""])
    div = result.get("diversity") or {}
    lines.append(f"- Categories: `{json.dumps(div.get('categories', {}), ensure_ascii=False)}`")
    lines.append(f"- Meal types: `{json.dumps(div.get('meal_types', {}), ensure_ascii=False)}`")
    lines.append(
        f"- Main ingredient families: `{json.dumps(div.get('main_ingredient_families', {}), ensure_ascii=False)}`"
    )
    lines.append(f"- Category overconcentration: `{div.get('category_overconcentration', False)}`")
    lines.append(f"- Meal type overconcentration: `{div.get('meal_type_overconcentration', False)}`")
    lines.append(
        f"- Main ingredient overconcentration: `{div.get('main_ingredient_overconcentration', False)}`"
    )

    lines.extend(["", "## Production recommendation", ""])
    if result["recommendation"] == "PASS":
        lines.append("- **PASS** \u2014 ready for Stage R importer dry-run")
    else:
        lines.append("- **FAIL** \u2014 fix generation/prompt/postprocess before importer")

    lines.extend(
        [
            "",
            "## Not done",
            "",
            "- DB import",
            "- Image generation",
            "- Safe reset",
            "- Production DB changes",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    recipes = load_jsonl(args.input)
    signals = load_jsonl(args.signals) if args.signals else []

    if not recipes:
        print(f"ERROR: no recipes in {args.input}", file=sys.stderr)
        return 1

    result = evaluate_recipe_gold_v3_quality_gate(
        recipes,
        signals or None,
        min_score=args.min_score,
        avg_score=args.avg_score,
        fail_on_warning=args.fail_on_warning,
    )

    report_text = build_report_md(args, result)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report_text, encoding="utf-8")

    s = result["summary"]
    print(
        f"records={s['records']} recommendation={result['recommendation']} "
        f"avg_score={s['avg_score']}"
    )
    return 0 if result["recommendation"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
