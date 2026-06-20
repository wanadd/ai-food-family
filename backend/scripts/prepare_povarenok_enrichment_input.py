#!/usr/bin/env python3
"""Prepare Povarenok candidate JSONL for future AI enrichment.

This script does not call AI, import recipes, or write to the database.

Run from the repository root:
    python backend/scripts/prepare_povarenok_enrichment_input.py --input exports/povarenok_candidates_100.jsonl
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = ROOT / "exports" / "povarenok_candidates_100.jsonl"
DEFAULT_OUTPUT_PATH = ROOT / "exports" / "povarenok_enrichment_input_100.jsonl"
DEFAULT_REPORT_PATH = ROOT / "reports" / "povarenok_enrichment_prep_report.md"
DEFAULT_SAMPLE_SIZE = 20

EXPECTED_OUTPUT_SCHEMA = {
    "title": "string",
    "description": "string",
    "meal_type": ["breakfast", "lunch", "dinner", "snack"],
    "category": [
        "soup",
        "main",
        "salad",
        "dessert",
        "quick",
        "kids",
        "drink",
        "event",
        "bbq",
    ],
    "cuisine": "string|null",
    "difficulty": ["easy", "medium", "hard"],
    "prep_time_minutes": "integer|null",
    "cooking_time_minutes": "integer|null",
    "servings": "integer|null",
    "steps": ["string"],
    "tags": ["string"],
    "allergens": ["string"],
    "restrictions": ["string"],
    "suitable_for_children": "boolean",
    "suitable_for_sport": "boolean",
    "suitable_for_event": "boolean",
    "is_drink": "boolean",
    "is_alcoholic": "boolean",
    "calories_per_serving": "number|null",
    "protein_g": "number|null",
    "fat_g": "number|null",
    "carbs_g": "number|null",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare Povarenok candidate JSONL for AI enrichment input"
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to selected Povarenok candidates JSONL",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to enrichment input JSONL",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown preparation report",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Number of prepared examples to include in the report",
    )
    return parser.parse_args()


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, list):
        return not value
    text = str(value).strip()
    return not text or text.lower() in {"nan", "none", "null", "[]", "{}"}


def clean_ingredient(ingredient: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(ingredient.get("name") or "").strip(),
        "quantity": ingredient.get("quantity"),
        "unit": ingredient.get("unit"),
        "raw": ingredient.get("raw"),
    }


def build_enrichment_input(record: dict[str, Any]) -> dict[str, Any]:
    ingredients = [
        clean_ingredient(ingredient)
        for ingredient in record.get("ingredients") or []
        if isinstance(ingredient, dict) and not is_empty(ingredient.get("name"))
    ]
    return {
        "source": record.get("source") or "povarenok",
        "source_url": record.get("source_url"),
        "title": str(record.get("title") or "").strip(),
        "ingredients": ingredients,
        "expected_output_schema": EXPECTED_OUTPUT_SCHEMA,
    }


def validate_record(record: dict[str, Any]) -> str | None:
    if is_empty(record.get("title")):
        return "empty_title"
    ingredients = record.get("ingredients")
    if not isinstance(ingredients, list) or not ingredients:
        return "empty_ingredients"
    valid_ingredients = [
        ingredient
        for ingredient in ingredients
        if isinstance(ingredient, dict) and not is_empty(ingredient.get("name"))
    ]
    if not valid_ingredients:
        return "empty_ingredient_names"
    return None


def build_report(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    total_read: int,
    prepared: int,
    skipped: int,
    skip_reasons: Counter[str],
    samples: list[dict[str, Any]],
) -> str:
    lines = [
        "# Povarenok Enrichment Prep Report",
        "",
        "## Source",
        "",
        f"- Input: `{input_path}`",
        f"- Output: `{output_path}`",
        f"- Report: `{report_path}`",
        "",
        "## Summary",
        "",
        f"- Total read: `{total_read}`",
        f"- Prepared: `{prepared}`",
        f"- Skipped: `{skipped}`",
        "",
        "## Skip Reasons",
        "",
    ]

    if skip_reasons:
        for reason, count in skip_reasons.most_common():
            lines.append(f"- {reason}: `{count}`")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Prepared Examples", ""])
    if samples:
        for index, sample in enumerate(samples, start=1):
            lines.append(f"### Example {index}")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(sample, ensure_ascii=False))
            lines.append("```")
            lines.append("")
    else:
        lines.append("No prepared examples.")

    return "\n".join(lines).rstrip() + "\n"


def prepare_enrichment_input(args: argparse.Namespace) -> tuple[int, Path, Path]:
    if args.sample_size < 1:
        raise SystemExit("--sample-size must be at least 1")

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    total_read = 0
    prepared = 0
    skipped = 0
    skip_reasons: Counter[str] = Counter()
    samples: list[dict[str, Any]] = []

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", encoding="utf-8") as source, output_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as target:
        for line in source:
            if not line.strip():
                continue
            total_read += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                skip_reasons["invalid_json"] += 1
                continue

            reason = validate_record(record)
            if reason is not None:
                skipped += 1
                skip_reasons[reason] += 1
                continue

            enrichment_input = build_enrichment_input(record)
            target.write(json.dumps(enrichment_input, ensure_ascii=False) + "\n")
            prepared += 1
            if len(samples) < args.sample_size:
                samples.append(enrichment_input)

    report = build_report(
        input_path=input_path,
        output_path=output_path,
        report_path=report_path,
        total_read=total_read,
        prepared=prepared,
        skipped=skipped,
        skip_reasons=skip_reasons,
        samples=samples,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return prepared, output_path, report_path


def main() -> int:
    args = parse_args()
    prepared, output_path, report_path = prepare_enrichment_input(args)
    print(f"Prepared {prepared} enrichment inputs")
    print(f"JSONL written to: {output_path}")
    print(f"Report written to: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
