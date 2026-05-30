#!/usr/bin/env python3
"""Build a 10-recipe AI enrichment batch without calling AI.

Run from the repository root:
    python backend/scripts/build_enrichment_batch.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = ROOT / "exports" / "povarenok_enrichment_input_100.jsonl"
DEFAULT_OUTPUT_PATH = ROOT / "exports" / "povarenok_enrichment_batch_10.json"
DEFAULT_REPORT_PATH = ROOT / "reports" / "enrichment_batch_preview.md"
DEFAULT_LIMIT = 10

REQUESTED_FIELDS = [
    "description",
    "meal_type",
    "category",
    "cuisine",
    "difficulty",
    "prep_time_minutes",
    "cooking_time_minutes",
    "servings",
    "steps",
    "tags",
    "allergens",
    "restrictions",
    "suitable_for_children",
    "suitable_for_sport",
    "suitable_for_event",
    "is_drink",
    "is_alcoholic",
    "calories_per_serving",
    "protein_g",
    "fat_g",
    "carbs_g",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a 10-recipe enrichment batch without calling AI"
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to enrichment input JSONL",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to enrichment batch JSON",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown preview report",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Number of recipes to include",
    )
    return parser.parse_args()


def read_first_records(input_path: Path, limit: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            records.append(json.loads(line))
            if len(records) >= limit:
                break
    return records


def compact_recipe(record: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "id": f"povarenok_{index:03d}",
        "source": record.get("source"),
        "source_url": record.get("source_url"),
        "title": record.get("title"),
        "ingredients": record.get("ingredients") or [],
    }


def build_batch(records: list[dict[str, Any]]) -> dict[str, Any]:
    schema = records[0].get("expected_output_schema") if records else {}
    return {
        "task": "enrich_povarenok_recipes",
        "language": "ru",
        "instructions": [
            "Return one enriched object per recipe.",
            "Do not invent ingredients.",
            "Infer missing cooking steps from title and ingredients only when reasonable.",
            "Use null when a numeric value cannot be estimated safely.",
            "Keep is_alcoholic=false unless the recipe clearly contains alcohol.",
        ],
        "requested_fields": REQUESTED_FIELDS,
        "expected_output_schema": schema,
        "recipes": [
            compact_recipe(record, index)
            for index, record in enumerate(records, start=1)
        ],
    }


def build_report(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    batch: dict[str, Any],
    output_size: int,
) -> str:
    recipes = batch.get("recipes") or []
    lines = [
        "# Enrichment Batch Preview",
        "",
        "## Source",
        "",
        f"- Input: `{input_path}`",
        f"- Output: `{output_path}`",
        f"- Report: `{report_path}`",
        f"- Recipes: `{len(recipes)}`",
        f"- JSON size: `{output_size}` bytes",
        "",
        "## Recipes",
        "",
    ]

    for recipe in recipes:
        lines.append(f"- {recipe.get('id')}: {recipe.get('title')}")

    lines.extend(["", "## Example Record", ""])
    if recipes:
        lines.append("```json")
        lines.append(json.dumps(recipes[0], ensure_ascii=False, indent=2))
        lines.append("```")
    else:
        lines.append("No recipes.")

    return "\n".join(lines).rstrip() + "\n"


def build_enrichment_batch(args: argparse.Namespace) -> tuple[int, Path, Path, int]:
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    records = read_first_records(input_path, args.limit)
    if not records:
        raise SystemExit("No records found in input JSONL")

    batch = build_batch(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(batch, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    output_size = output_path.stat().st_size

    report = build_report(
        input_path=input_path,
        output_path=output_path,
        report_path=report_path,
        batch=batch,
        output_size=output_size,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return len(records), output_path, report_path, output_size


def main() -> int:
    args = parse_args()
    count, output_path, report_path, output_size = build_enrichment_batch(args)
    print(f"Prepared {count} recipes")
    print(f"Batch written to: {output_path}")
    print(f"Preview written to: {report_path}")
    print(f"JSON size: {output_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
