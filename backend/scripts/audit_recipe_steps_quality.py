"""Read-only quality audit for recipe cooking steps.

Checks all recipes for missing, placeholder, or weak cooking steps and writes a
Markdown report. It does not update recipes or call AI.

Usage:
    python backend/scripts/audit_recipe_steps_quality.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
DEFAULT_REPORT_PATH = ROOT / "reports" / "recipe_steps_quality_audit.md"

PLACEHOLDER_PHRASES = (
    "подготовьте продукты",
    "приготовьте по классическому рецепту",
    "подавайте тёплым",
    "подавайте теплым",
    "по классическому рецепту",
)
ACTION_WORDS = (
    "нарежьте",
    "обжарьте",
    "варите",
    "тушите",
    "запекайте",
    "смешайте",
    "добавьте",
    "перемешайте",
    "доведите",
    "очистите",
)
MIN_AVG_STEP_LENGTH = 35
WEAK_STEP_COUNT_THRESHOLD = 3

GROUPS = {
    "A": "good_steps",
    "B": "weak_steps",
    "C": "placeholder_steps",
    "D": "missing_steps",
}
GROUP_SEVERITY = {"D": 0, "C": 1, "B": 2, "A": 3}


@dataclass(frozen=True)
class RecipeStepsRow:
    id: int
    title: str
    steps: list[str]


@dataclass(frozen=True)
class StepQualityResult:
    recipe: RecipeStepsRow
    group: str
    reasons: list[str]
    steps_count: int
    avg_step_length: float
    action_word_count: int
    placeholder_matches: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit recipe steps quality")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown recipe steps quality audit report",
    )
    return parser.parse_args()


def readable_text(value: Any) -> str:
    text_value = str(value or "").strip()
    if not any(marker in text_value for marker in ("Р", "С", "Ð", "Ñ")):
        return text_value
    try:
        repaired = text_value.encode("cp1251").decode("utf-8")
    except UnicodeError:
        return text_value
    return repaired or text_value


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", readable_text(value).lower().replace("ё", "е")).strip()


def normalize_steps(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    steps = [readable_text(step) for step in value]
    return [step for step in steps if step]


def row_to_recipe(row: Any) -> RecipeStepsRow:
    return RecipeStepsRow(
        id=int(row["id"]),
        title=readable_text(row["title"]),
        steps=normalize_steps(row.get("steps")),
    )


def load_recipes_sqlalchemy(database_url: str) -> list[RecipeStepsRow]:
    engine = create_engine(database_url)
    query = text(
        """
        SELECT id, title, steps
        FROM recipes
        ORDER BY id
        """
    )
    with engine.connect() as conn:
        rows = list(conn.execute(query).mappings())
    return [row_to_recipe(row) for row in rows]


def docker_psql_json(sql: str) -> Any:
    cmd = [
        "docker",
        "compose",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        "aifood",
        "-d",
        "aifood",
        "-t",
        "-A",
        "-c",
        sql,
    ]
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return json.loads(result.stdout.strip() or "[]")


def load_recipes_docker() -> list[RecipeStepsRow]:
    sql = """
        SELECT COALESCE(json_agg(row_to_json(t) ORDER BY id), '[]'::json)
        FROM (
            SELECT id, title, steps
            FROM recipes
            ORDER BY id
        ) AS t;
        """
    return [row_to_recipe(row) for row in docker_psql_json(sql)]


def count_action_words(steps: list[str]) -> int:
    text_value = " ".join(normalize_text(step) for step in steps)
    return sum(1 for word in ACTION_WORDS if word in text_value)


def find_placeholder_matches(steps: list[str]) -> list[str]:
    text_value = " ".join(normalize_text(step) for step in steps)
    return [phrase for phrase in PLACEHOLDER_PHRASES if phrase.replace("ё", "е") in text_value]


def average_step_length(steps: list[str]) -> float:
    if not steps:
        return 0.0
    return sum(len(step.strip()) for step in steps) / len(steps)


def audit_recipe(recipe: RecipeStepsRow) -> StepQualityResult:
    steps_count = len(recipe.steps)
    avg_length = average_step_length(recipe.steps)
    action_count = count_action_words(recipe.steps)
    placeholder_matches = find_placeholder_matches(recipe.steps)
    reasons: list[str] = []

    if steps_count == 0:
        reasons.append("missing_steps")
        group = "D"
    else:
        if steps_count <= WEAK_STEP_COUNT_THRESHOLD:
            reasons.append("steps_count<=3")
        if placeholder_matches:
            reasons.append("placeholder_phrases:" + ", ".join(placeholder_matches))
        if avg_length < MIN_AVG_STEP_LENGTH:
            reasons.append(f"avg_step_length<{MIN_AVG_STEP_LENGTH}")
        if action_count == 0:
            reasons.append("no_specific_actions")

        if placeholder_matches:
            group = "C"
        elif reasons:
            group = "B"
        else:
            group = "A"

    return StepQualityResult(
        recipe=recipe,
        group=group,
        reasons=reasons,
        steps_count=steps_count,
        avg_step_length=avg_length,
        action_word_count=action_count,
        placeholder_matches=placeholder_matches,
    )


def fmt_inline(value: str) -> str:
    return value.replace("|", "\\|")


def format_steps(steps: list[str]) -> str:
    if not steps:
        return "`n/a`"
    return "<br>".join(
        f"{index}. {fmt_inline(step)}" for index, step in enumerate(steps, start=1)
    )


def build_report(results: list[StepQualityResult], connection_note: str) -> str:
    counts = {group_name: 0 for group_name in GROUPS.values()}
    for result in results:
        counts[GROUPS[result.group]] += 1

    problematic = [result for result in results if result.group != "A"]
    problematic.sort(
        key=lambda result: (
            GROUP_SEVERITY[result.group],
            result.steps_count,
            result.avg_step_length,
            result.recipe.id,
        )
    )
    top_problematic = problematic[:100]

    lines = [
        "# Recipe Steps Quality Audit",
        "",
        "Scope: read-only audit of recipe preparation steps. No database changes, recipe updates, migrations, commits, or AI calls were performed.",
        "",
        "## Summary",
        "",
        f"- Total recipes: `{len(results)}`",
        f"- good_steps count: `{counts['good_steps']}`",
        f"- weak_steps count: `{counts['weak_steps']}`",
        f"- placeholder_steps count: `{counts['placeholder_steps']}`",
        f"- missing_steps count: `{counts['missing_steps']}`",
        f"- Database read method: `{connection_note}`",
        "",
        "## Rules",
        "",
        f"- Weak step count: `steps count <= {WEAK_STEP_COUNT_THRESHOLD}`",
        f"- Short average step length: `< {MIN_AVG_STEP_LENGTH}` characters",
        "- Placeholder phrase match: `Подготовьте продукты`, `Приготовьте по классическому рецепту`, `Подавайте тёплым`, `Подавайте теплым`, `по классическому рецепту`",
        "- Specific action words: `нарежьте`, `обжарьте`, `варите`, `тушите`, `запекайте`, `смешайте`, `добавьте`, `перемешайте`, `доведите`, `очистите`",
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
            "## Top 100 Problem Recipes",
            "",
            "| ID | Title | Group | Steps count | Avg step length | Action words | Reason | Steps |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    if not top_problematic:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    for result in top_problematic:
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
    for group_name in ("good_steps", "weak_steps", "placeholder_steps", "missing_steps"):
        print(f"{group_name}: {counts[group_name]}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
