#!/usr/bin/env python3
"""Export calculated recipe nutrition updates without writing to the database.

Uses the ingredient nutrition engine preview and writes a JSON update batch plus
a Markdown audit report. It does not update recipes or create migrations.

Run from the repository root:
    python backend/scripts/export_calculated_nutrition_updates.py
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from calculate_recipe_nutrition_preview import (
    DEFAULT_DATABASE_URL,
    DEFAULT_REFERENCE_PATH,
    ROOT,
    calculate_recipe,
    load_recipes,
    load_recipes_via_docker,
    load_reference,
    normalize_name,
    round_nutrition,
)


DEFAULT_OUTPUT_PATH = ROOT / "exports" / "calculated_nutrition_updates_174.json"
DEFAULT_SAFE_OUTPUT_PATH = ROOT / "exports" / "calculated_nutrition_updates_safe.json"
DEFAULT_SUSPICIOUS_OUTPUT_PATH = (
    ROOT / "exports" / "calculated_nutrition_updates_suspicious.json"
)
DEFAULT_REPORT_PATH = ROOT / "reports" / "calculated_nutrition_updates_report.md"
SOURCE = "ingredient_engine_v2"
PLACEHOLDER_INGREDIENTS = {"основа напитка", "основной продукт"}
NON_REAL_INGREDIENTS = {
    *PLACEHOLDER_INGREDIENTS,
    "вода",
    "соль",
    "специи",
    "приправа",
    "перец черный",
    "лист лавровый",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export calculated nutrition updates as a JSON batch"
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--reference",
        default=str(DEFAULT_REFERENCE_PATH),
        help="Path to nutrition reference seed JSON",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to legacy full output JSON update array",
    )
    parser.add_argument(
        "--safe-output",
        default=str(DEFAULT_SAFE_OUTPUT_PATH),
        help="Path to safe output JSON update array",
    )
    parser.add_argument(
        "--suspicious-output",
        default=str(DEFAULT_SUSPICIOUS_OUTPUT_PATH),
        help="Path to suspicious output JSON update array",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown export report",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=20,
        help="Number of examples to show in the report",
    )
    return parser.parse_args()


def calculated_per_serving(total: float, servings: int | None) -> float:
    divisor = servings if servings and servings > 0 else 1
    return round_nutrition(total / divisor)


def build_update_record(calculation: Any) -> dict[str, Any]:
    recipe = calculation.recipe
    return {
        "id": recipe.id,
        "title": recipe.title,
        "calories_per_serving": calculated_per_serving(
            calculation.calories, recipe.servings
        ),
        "protein_g": calculated_per_serving(calculation.protein_g, recipe.servings),
        "fat_g": calculated_per_serving(calculation.fat_g, recipe.servings),
        "carbs_g": calculated_per_serving(calculation.carbs_g, recipe.servings),
        "alcohol_percent": None,
        "source": SOURCE,
    }


def quality_gate_reasons(record: dict[str, Any], calculation: Any) -> list[str]:
    reasons: list[str] = []
    calories = record["calories_per_serving"]
    protein = record["protein_g"]
    fat = record["fat_g"]
    carbs = record["carbs_g"]

    if calories == 0 and protein == 0 and fat == 0 and carbs == 0:
        reasons.append("all_zero")
    if calories < 5:
        reasons.append("low_calorie")
    if calories > 1500:
        reasons.append("extreme_calorie")
    if protein > 120 or fat > 150 or carbs > 250:
        reasons.append("extreme_macro")

    ingredient_names = [
        normalize_name(item.name)
        for item in calculation.ingredients
        if normalize_name(item.name)
    ]
    placeholder_ingredients = [
        name for name in ingredient_names if name in PLACEHOLDER_INGREDIENTS
    ]
    real_ingredients = [name for name in ingredient_names if name not in NON_REAL_INGREDIENTS]
    if placeholder_ingredients:
        reasons.append("placeholder_ingredients")
    if not real_ingredients:
        reasons.append("missing_real_ingredients")

    return list(dict.fromkeys(reasons))


def build_report(
    total_recipes: int,
    all_records: list[dict[str, Any]],
    safe_records: list[dict[str, Any]],
    suspicious_records: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    output_path: Path,
    safe_output_path: Path,
    suspicious_output_path: Path,
    sample_size: int,
    connection_note: str,
) -> str:
    reason_counts: Counter[str] = Counter()
    for record in suspicious_records:
        reason_counts.update(record.get("suspicious_reasons") or [])

    lines = [
        "# Calculated Nutrition Updates Export",
        "",
        "Scope: read-only export from ingredient nutrition engine v2 with a safety gate. No database changes, recipe updates, imports, or migrations were performed.",
        "",
        "## Summary",
        "",
        f"- Read connection: `{connection_note}`",
        f"- Total recipes: `{total_recipes}`",
        f"- Exported records: `{len(all_records)}`",
        f"- Safe records: `{len(safe_records)}`",
        f"- Suspicious records: `{len(suspicious_records)}`",
        f"- Failed: `{len(failures)}`",
        f"- Legacy full output: `{output_path}`",
        f"- Safe output: `{safe_output_path}`",
        f"- Suspicious output: `{suspicious_output_path}`",
        f"- Source: `{SOURCE}`",
        "",
        "## Reasons Breakdown",
        "",
    ]
    if not reason_counts:
        lines.append("- `n/a`")
    for reason, count in reason_counts.most_common():
        lines.append(f"- `{reason}`: `{count}`")

    lines.extend(
        [
            "",
            f"## First {sample_size} Safe Examples",
            "",
        ]
    )
    if not safe_records:
        lines.append("- `n/a`")
    for record in safe_records[:sample_size]:
        lines.append(
            f"- `#{record['id']}` {record['title']}: "
            f"{record['calories_per_serving']} kcal, "
            f"P {record['protein_g']}g, "
            f"F {record['fat_g']}g, "
            f"C {record['carbs_g']}g"
        )

    lines.extend(
        [
            "",
            f"## Top {sample_size} Suspicious Examples",
            "",
        ]
    )
    if not suspicious_records:
        lines.append("- `n/a`")
    for record in suspicious_records[:sample_size]:
        reasons = ", ".join(record.get("suspicious_reasons") or [])
        lines.append(
            f"- `#{record['id']}` {record['title']}: `{reasons}`; "
            f"{record['calories_per_serving']} kcal, "
            f"P {record['protein_g']}g, "
            f"F {record['fat_g']}g, "
            f"C {record['carbs_g']}g"
        )

    lines.extend(
        [
            "",
        f"## First {sample_size} Examples",
        "",
        ]
    )
    if not all_records:
        lines.append("- `n/a`")
    for record in all_records[:sample_size]:
        lines.append(
            f"- `#{record['id']}` {record['title']}: "
            f"{record['calories_per_serving']} kcal, "
            f"P {record['protein_g']}g, "
            f"F {record['fat_g']}g, "
            f"C {record['carbs_g']}g"
        )

    lines.extend(["", "## Failed Records", ""])
    if not failures:
        lines.append("- `n/a`")
    for failure in failures[:50]:
        lines.append(
            f"- `#{failure.get('id')}` {failure.get('title')}: `{failure.get('error')}`"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    if args.sample_size < 1:
        raise SystemExit("--sample-size must be at least 1")

    reference_path = Path(args.reference).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    safe_output_path = Path(args.safe_output).expanduser().resolve()
    suspicious_output_path = Path(args.suspicious_output).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()

    reference_by_alias = load_reference(reference_path)
    try:
        recipes = load_recipes(args.database_url)
        connection_note = "SQLAlchemy"
    except SQLAlchemyError as exc:
        print(
            "SQLAlchemy connection failed, falling back to docker compose psql: "
            f"{exc.__class__.__name__}"
        )
        recipes = load_recipes_via_docker()
        connection_note = "docker compose psql"

    records: list[dict[str, Any]] = []
    safe_records: list[dict[str, Any]] = []
    suspicious_records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for recipe in recipes:
        try:
            calculation = calculate_recipe(recipe, reference_by_alias)
            if not calculation.is_fully_calculated:
                raise ValueError(
                    "recipe_not_fully_calculated:"
                    f"missing={calculation.missing_count},"
                    f"unmeasured={calculation.unmeasured_count}"
                )
            record = build_update_record(calculation)
            reasons = quality_gate_reasons(record, calculation)
            records.append(record)
            if reasons:
                suspicious_record = dict(record)
                suspicious_record["suspicious_reasons"] = reasons
                suspicious_records.append(suspicious_record)
            else:
                safe_records.append(record)
        except Exception as exc:
            failures.append(
                {
                    "id": recipe.id,
                    "title": recipe.title,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    safe_output_path.parent.mkdir(parents=True, exist_ok=True)
    safe_output_path.write_text(
        json.dumps(safe_records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    suspicious_output_path.parent.mkdir(parents=True, exist_ok=True)
    suspicious_output_path.write_text(
        json.dumps(suspicious_records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = build_report(
        total_recipes=len(recipes),
        all_records=records,
        safe_records=safe_records,
        suspicious_records=suspicious_records,
        failures=failures,
        output_path=output_path,
        safe_output_path=safe_output_path,
        suspicious_output_path=suspicious_output_path,
        sample_size=args.sample_size,
        connection_note=connection_note,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"Read connection: {connection_note}")
    print(f"Total recipes: {len(recipes)}")
    print(f"Exported records: {len(records)}")
    print(f"Safe records: {len(safe_records)}")
    print(f"Suspicious records: {len(suspicious_records)}")
    print(f"Failed: {len(failures)}")
    print(f"Output written to: {output_path}")
    print(f"Safe output written to: {safe_output_path}")
    print(f"Suspicious output written to: {suspicious_output_path}")
    print(f"Report written to: {report_path}")


if __name__ == "__main__":
    main()
