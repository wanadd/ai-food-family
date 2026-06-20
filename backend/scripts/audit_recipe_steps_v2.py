#!/usr/bin/env python3
"""Read-only V2 audit for recipe cooking steps.

Compares the existing steps quality classification with a more permissive V2
classification that treats sufficiently detailed recipes as good even when old
heuristics marked them weak. It does not update recipes or call AI.

Usage:
    python backend/scripts/audit_recipe_steps_v2.py
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from audit_recipe_steps_quality import (
    DEFAULT_DATABASE_URL,
    GROUPS,
    ROOT,
    RecipeStepsRow,
    StepQualityResult,
    audit_recipe,
    find_placeholder_matches,
    fmt_inline,
    format_steps,
    load_recipes_docker,
    load_recipes_sqlalchemy,
    normalize_text,
)


DEFAULT_REPORT_PATH = ROOT / "reports" / "recipe_steps_audit_v2.md"

COOKING_VERBS = (
    "нарежьте",
    "обжарьте",
    "отварите",
    "запекайте",
    "тушите",
    "смешайте",
    "добавьте",
    "взбейте",
    "выложите",
    "разогрейте",
)


@dataclass(frozen=True)
class StepQualityV2Result:
    recipe: RecipeStepsRow
    old: StepQualityResult
    group: str
    reasons: list[str]
    steps_count: int
    action_word_count: int
    cooking_verb_count: int
    cooking_verbs: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit recipe steps quality V2")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown recipe steps V2 audit report",
    )
    return parser.parse_args()


def count_cooking_verbs(steps: list[str]) -> tuple[int, list[str]]:
    text_value = " ".join(normalize_text(step) for step in steps)
    found = [verb for verb in COOKING_VERBS if normalize_text(verb) in text_value]
    return len(found), found


def audit_recipe_v2(recipe: RecipeStepsRow, old: StepQualityResult) -> StepQualityV2Result:
    steps_count = len(recipe.steps)
    cooking_verb_count, cooking_verbs = count_cooking_verbs(recipe.steps)
    placeholder_matches = find_placeholder_matches(recipe.steps)
    reasons: list[str] = []

    if steps_count == 0:
        group = "D"
        reasons.append("missing_steps")
    elif placeholder_matches:
        group = "C"
        reasons.append("placeholder_phrases:" + ", ".join(placeholder_matches))
    elif steps_count >= 6:
        group = "A"
        reasons.append("steps_count>=6")
    elif old.action_word_count >= 4:
        group = "A"
        reasons.append("action_words>=4")
    elif cooking_verb_count >= 3:
        group = "A"
        reasons.append("cooking_verbs>=3:" + ", ".join(cooking_verbs))
    else:
        group = "B"
        if steps_count <= 3:
            reasons.append("steps_count<=3")
        if old.avg_step_length < 35:
            reasons.append("avg_step_length<35")
        if old.action_word_count:
            reasons.append(f"action_words={old.action_word_count}")
        if cooking_verb_count:
            reasons.append(f"cooking_verbs={cooking_verb_count}")

    return StepQualityV2Result(
        recipe=recipe,
        old=old,
        group=group,
        reasons=reasons,
        steps_count=steps_count,
        action_word_count=old.action_word_count,
        cooking_verb_count=cooking_verb_count,
        cooking_verbs=cooking_verbs,
    )


def count_groups(results: list[StepQualityResult | StepQualityV2Result]) -> dict[str, int]:
    counts = {group_name: 0 for group_name in GROUPS.values()}
    for result in results:
        counts[GROUPS[result.group]] += 1
    return counts


def build_report(
    old_results: list[StepQualityResult],
    new_results: list[StepQualityV2Result],
    connection_note: str,
) -> str:
    old_counts = count_groups(old_results)
    new_counts = count_groups(new_results)
    promoted = [
        result
        for result in new_results
        if result.old.group == "B" and result.group == "A"
    ]
    promoted.sort(key=lambda result: (result.recipe.id, result.recipe.title))

    lines = [
        "# Recipe Steps Audit V2",
        "",
        "Scope: read-only comparison of old recipe steps audit rules and V2 classification. No database changes, recipe updates, commits, or AI calls were performed.",
        "",
        "## Summary",
        "",
        f"- Total recipes: `{len(new_results)}`",
        f"- Old good count: `{old_counts['good_steps']}`",
        f"- Old weak count: `{old_counts['weak_steps']}`",
        f"- New good count: `{new_counts['good_steps']}`",
        f"- New weak count: `{new_counts['weak_steps']}`",
        f"- Placeholder steps count: `{new_counts['placeholder_steps']}`",
        f"- Missing steps count: `{new_counts['missing_steps']}`",
        f"- weak -> good: `{len(promoted)}`",
        f"- Database read method: `{connection_note}`",
        "",
        "## V2 Rules",
        "",
        "- GOOD if `steps_count >= 6`.",
        "- GOOD if old audit `action_words >= 4`.",
        "- GOOD if at least 3 different cooking verbs are present: `нарежьте`, `обжарьте`, `отварите`, `запекайте`, `тушите`, `смешайте`, `добавьте`, `взбейте`, `выложите`, `разогрейте`.",
        "- `no_specific_actions` no longer automatically makes a recipe weak.",
        "- Placeholder and missing steps remain problem groups.",
        "",
        "## Weak To Good",
        "",
        "| ID | Title | Steps count | Action words | Cooking verbs | V2 reason | Steps |",
        "| ---: | --- | ---: | ---: | --- | --- | --- |",
    ]
    if not promoted:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    for result in promoted:
        lines.append(
            f"| {result.recipe.id} | {fmt_inline(result.recipe.title)} | "
            f"{result.steps_count} | {result.action_word_count} | "
            f"{fmt_inline(', '.join(result.cooking_verbs) or 'n/a')} | "
            f"{fmt_inline('; '.join(result.reasons) or 'n/a')} | "
            f"{format_steps(result.recipe.steps)} |"
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

    old_results = [audit_recipe(recipe) for recipe in recipes]
    old_by_id = {result.recipe.id: result for result in old_results}
    new_results = [audit_recipe_v2(recipe, old_by_id[recipe.id]) for recipe in recipes]

    report = build_report(old_results, new_results, connection_note)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    old_counts = count_groups(old_results)
    new_counts = count_groups(new_results)
    print(f"Total recipes: {len(new_results)}")
    print(f"Old good count: {old_counts['good_steps']}")
    print(f"Old weak count: {old_counts['weak_steps']}")
    print(f"New good count: {new_counts['good_steps']}")
    print(f"New weak count: {new_counts['weak_steps']}")
    print(
        "Weak -> good: "
        f"{sum(1 for result in new_results if result.old.group == 'B' and result.group == 'A')}"
    )
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
