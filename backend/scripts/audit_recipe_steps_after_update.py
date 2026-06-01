#!/usr/bin/env python3
"""Read-only audit for recipe steps quality after an apply run.

This script only reads recipes and writes a Markdown report. It does not update
the database and does not call AI.

Usage:
    python backend/scripts/audit_recipe_steps_after_update.py
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from audit_recipe_steps_quality import (
    DEFAULT_DATABASE_URL,
    GROUPS,
    GROUP_SEVERITY,
    audit_recipe,
    fmt_inline,
    format_steps,
    load_recipes_docker,
    load_recipes_sqlalchemy,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_PATH = ROOT / "reports" / "recipe_steps_after_update_audit.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit recipe steps after update")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown after-update audit report",
    )
    return parser.parse_args()


def build_report(results, connection_note: str) -> str:
    counts = {group_name: 0 for group_name in GROUPS.values()}
    for result in results:
        counts[GROUPS[result.group]] += 1

    remaining_problematic = [result for result in results if result.group != "A"]
    remaining_problematic.sort(
        key=lambda result: (
            GROUP_SEVERITY[result.group],
            result.steps_count,
            result.avg_step_length,
            result.recipe.id,
        )
    )

    lines = [
        "# Recipe Steps After Update Audit",
        "",
        "Scope: read-only audit of recipe preparation steps after the safe apply pipeline. No database changes, recipe updates, commits, or AI calls were performed by this audit.",
        "",
        "## Summary",
        "",
        f"- Total recipes: `{len(results)}`",
        f"- Placeholder steps remaining: `{counts['placeholder_steps']}`",
        f"- Full/good steps: `{counts['good_steps']}`",
        f"- Weak steps remaining: `{counts['weak_steps']}`",
        f"- Missing steps remaining: `{counts['missing_steps']}`",
        f"- Database read method: `{connection_note}`",
        "",
        "## Group Counts",
        "",
        "| Group | Name | Count |",
        "| --- | --- | ---: |",
    ]
    for group, name in GROUPS.items():
        lines.append(f"| {group} | {name} | {counts[name]} |")

    lines.extend(
        [
            "",
            "## Remaining Problem Recipes",
            "",
            "| ID | Title | Group | Steps count | Avg step length | Action words | Reason | Steps |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    if not remaining_problematic:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    for result in remaining_problematic[:100]:
        reason = "; ".join(result.reasons) if result.reasons else "n/a"
        lines.append(
            f"| {result.recipe.id} | {fmt_inline(result.recipe.title)} | "
            f"{result.group}: {GROUPS[result.group]} | {result.steps_count} | "
            f"{result.avg_step_length:.1f} | {result.action_word_count} | "
            f"{fmt_inline(reason)} | {format_steps(result.recipe.steps)} |"
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    report_path = Path(args.report).expanduser().resolve()
    try:
        recipes = load_recipes_sqlalchemy(args.database_url)
        connection_note = "SQLAlchemy"
    except SQLAlchemyError as exc:
        print(
            "SQLAlchemy connection failed, falling back to docker compose psql: "
            f"{exc.__class__.__name__}"
        )
        recipes = load_recipes_docker()
        connection_note = "docker compose psql"

    results = [audit_recipe(recipe) for recipe in recipes]
    report = build_report(results, connection_note)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    counts = {group_name: 0 for group_name in GROUPS.values()}
    for result in results:
        counts[GROUPS[result.group]] += 1
    print(f"Total recipes: {len(results)}")
    print(f"Placeholder steps remaining: {counts['placeholder_steps']}")
    print(f"Full/good steps: {counts['good_steps']}")
    print(f"Weak steps remaining: {counts['weak_steps']}")
    print(f"Missing steps remaining: {counts['missing_steps']}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
