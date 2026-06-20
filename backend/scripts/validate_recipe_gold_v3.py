#!/usr/bin/env python3
"""Validate Recipe Gold V3 JSONL fixtures (no DB writes)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_gold_v3_validation import validate_recipe_gold_v3  # noqa: E402

DEFAULT_INPUT = ROOT / "exports" / "recipe_gold_v3_validation_samples.jsonl"
DEFAULT_REPORT = ROOT / "reports" / "recipe_gold_v3_validation_report.md"


def load_jsonl(path: Path) -> list[dict]:
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


def build_report(
    *,
    input_path: Path,
    report_path: Path,
    results: list[tuple[dict, object]],
    dry_run: bool,
) -> str:
    branch, commit = git_meta()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    valid = sum(1 for _, r in results if r.ok)
    invalid = len(results) - valid
    error_codes: Counter[str] = Counter()
    warning_codes: Counter[str] = Counter()
    scores: list[int] = []

    for _, result in results:
        scores.append(result.score)
        for issue in result.errors:
            error_codes[issue.code] += 1
        for issue in result.warnings:
            warning_codes[issue.code] += 1

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    lines = [
        "# Recipe Gold V3 Validation Report",
        "",
        f"**Generated:** {now}",
        f"**Branch:** `{branch}`",
        f"**Commit:** `{commit}`",
        f"**Mode:** `{'dry-run' if dry_run else 'apply'}`",
        "",
        "## Summary",
        "",
        f"- Input: `{input_path}`",
        f"- Records: `{len(results)}`",
        f"- Valid: `{valid}`",
        f"- Invalid: `{invalid}`",
        f"- Average score: `{avg_score}`",
        "",
        "## Errors by code",
        "",
    ]
    if error_codes:
        for code, count in error_codes.most_common():
            lines.append(f"- {code}: `{count}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Warnings by code", ""])
    if warning_codes:
        for code, count in warning_codes.most_common():
            lines.append(f"- {code}: `{count}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Per-record", ""])
    for idx, (raw, result) in enumerate(results, start=1):
        title = raw.get("title", "?")
        status = "VALID" if result.ok else "INVALID"
        lines.append(f"### {idx}. {title} — {status} (score {result.score})")
        if result.errors:
            for issue in result.errors:
                lines.append(f"- ERROR `{issue.code}`: {issue.message}")
        if result.warnings:
            for issue in result.warnings:
                lines.append(f"- WARN `{issue.code}`: {issue.message}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Recipe Gold V3 JSONL")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--fail-on-error", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    recipes = load_jsonl(args.input)
    results: list[tuple[dict, object]] = []
    for raw in recipes:
        result = validate_recipe_gold_v3(raw)
        results.append((raw, result))

    valid = sum(1 for _, r in results if r.ok)
    invalid = len(results) - valid
    avg_score = round(
        sum(r.score for _, r in results) / len(results),
        1,
    ) if results else 0

    print(f"records={len(results)} valid={valid} invalid={invalid} avg_score={avg_score}")

    report_md = build_report(
        input_path=args.input,
        report_path=args.report,
        results=results,
        dry_run=args.dry_run,
    )

    if not args.dry_run:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report_md, encoding="utf-8")
        print(f"report_written={args.report}")
    else:
        # dry-run still writes report per Stage E spec (local artifact only)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report_md, encoding="utf-8")
        print(f"report_written={args.report} (dry-run, no DB)")

    if args.fail_on_error and invalid:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
