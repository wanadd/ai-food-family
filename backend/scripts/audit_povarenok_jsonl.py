#!/usr/bin/env python3
"""Audit Povarenok PlanAm raw JSONL before enrichment and import.

Run from the repository root:
    python backend/scripts/audit_povarenok_jsonl.py --input exports/povarenok_planam_raw.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = ROOT / "exports" / "povarenok_planam_raw.jsonl"
DEFAULT_REPORT_PATH = ROOT / "reports" / "povarenok_jsonl_quality.md"
DEFAULT_SAMPLE_SIZE = 20
RANDOM_SEED = 20210616

ALCOHOL_PATTERNS = (
    r"\bалкогол",
    r"\bводк",
    r"\bвино\b",
    r"\bвинн",
    r"\bконьяк",
    r"\bром\b",
    r"\bликер",
    r"\bликёр",
    r"\bпиво\b",
    r"\bспирт",
    r"\bнастойк",
    r"\bналивк",
    r"\bсамогон",
)
WINTER_PATTERNS = (
    r"на зиму",
    r"\bзаготов",
    r"\bконсерв",
    r"\bмарин",
    r"\bсолень",
    r"\bваренье",
    r"\bджем\b",
    r"\bкомпот",
    r"\bзакатк",
)
DESSERT_PATTERNS = (
    r"\bторт",
    r"\bпирожн",
    r"\bдесерт",
    r"\bкекс",
    r"\bпечень",
    r"\bпирог",
    r"\bбулоч",
    r"\bконфет",
    r"\bморожен",
    r"\bсуфле",
    r"\bшоколад",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Povarenok raw JSONL without importing recipes"
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to the Povarenok PlanAm raw JSONL file",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Number of suspicious examples to include per category",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to the Markdown quality report",
    )
    return parser.parse_args()


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, list):
        return len(value) == 0
    text = str(value).strip()
    if not text:
        return True
    return text.lower() in {"nan", "none", "null", "[]", "{}"}


def matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def ingredient_names_text(ingredients: list[Any]) -> str:
    names = []
    for ingredient in ingredients:
        if isinstance(ingredient, dict):
            names.append(str(ingredient.get("name") or ""))
    return " ".join(names)


def update_sample(
    samples: list[dict[str, Any]],
    record: dict[str, Any],
    seen: int,
    sample_size: int,
    rng: random.Random,
) -> None:
    if sample_size <= 0:
        return
    sample = {
        "title": record.get("title"),
        "source_url": record.get("source_url"),
        "ingredient_count": len(record.get("ingredients") or []),
    }
    if len(samples) < sample_size:
        samples.append(sample)
        return
    index = rng.randint(0, seen - 1)
    if index < sample_size:
        samples[index] = sample


def format_sample(sample: dict[str, Any]) -> str:
    title = sample.get("title") or "<empty title>"
    count = sample.get("ingredient_count")
    url = sample.get("source_url") or ""
    return f"- {title} | ingredients: `{count}` | {url}"


def build_report(
    input_path: Path,
    output_path: Path,
    total_records: int,
    invalid_json: int,
    empty_titles: int,
    empty_ingredients: int,
    ingredient_total: int,
    min_ingredients: int | None,
    max_ingredients: int | None,
    top_ingredients: list[tuple[str, int]],
    top_units: list[tuple[str, int]],
    quantity_null: int,
    unit_null: int,
    suspicious_counts: dict[str, int],
    suspicious_samples: dict[str, list[dict[str, Any]]],
) -> str:
    average_ingredients = (
        ingredient_total / total_records if total_records else None
    )
    lines = [
        "# Povarenok JSONL Quality Audit",
        "",
        "## Source",
        "",
        f"- Input: `{input_path}`",
        f"- Report: `{output_path}`",
        "",
        "## Summary",
        "",
        f"- Records: `{total_records}`",
        f"- Invalid JSON lines: `{invalid_json}`",
        f"- Empty title: `{empty_titles}`",
        f"- Empty ingredients: `{empty_ingredients}`",
        "- Average ingredients: "
        + (
            f"`{average_ingredients:.2f}`"
            if average_ingredients is not None
            else "`n/a`"
        ),
        "- Min ingredients: "
        + (f"`{min_ingredients}`" if min_ingredients is not None else "`n/a`"),
        "- Max ingredients: "
        + (f"`{max_ingredients}`" if max_ingredients is not None else "`n/a`"),
        f"- Ingredients with quantity=null: `{quantity_null}`",
        f"- Ingredients with unit=null: `{unit_null}`",
        "",
        "## Suspicious Recipes",
        "",
    ]

    labels = {
        "alcohol": "Alcohol",
        "winter": "Winter preserves",
        "desserts": "Cakes and desserts",
        "less_than_3_ingredients": "Less than 3 ingredients",
        "more_than_25_ingredients": "More than 25 ingredients",
    }
    for key, label in labels.items():
        lines.append(f"- {label}: `{suspicious_counts.get(key, 0)}`")

    lines.extend(["", "## Top 200 Ingredients", ""])
    if top_ingredients:
        for name, count in top_ingredients:
            lines.append(f"- {name}: `{count}`")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Top 200 Units", ""])
    if top_units:
        for unit, count in top_units:
            lines.append(f"- {unit}: `{count}`")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Suspicious Samples", ""])
    for key, label in labels.items():
        lines.append(f"### {label}")
        samples = suspicious_samples.get(key, [])
        if samples:
            lines.extend(format_sample(sample) for sample in samples)
        else:
            lines.append("- `n/a`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def audit_jsonl(args: argparse.Namespace) -> tuple[int, Path]:
    if args.sample_size < 1:
        raise SystemExit("--sample-size must be at least 1")

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    rng = random.Random(RANDOM_SEED)
    total_records = 0
    invalid_json = 0
    empty_titles = 0
    empty_ingredients = 0
    ingredient_total = 0
    min_ingredients: int | None = None
    max_ingredients: int | None = None
    ingredient_counter: Counter[str] = Counter()
    unit_counter: Counter[str] = Counter()
    quantity_null = 0
    unit_null = 0
    suspicious_counts = {
        "alcohol": 0,
        "winter": 0,
        "desserts": 0,
        "less_than_3_ingredients": 0,
        "more_than_25_ingredients": 0,
    }
    suspicious_samples: dict[str, list[dict[str, Any]]] = {
        key: [] for key in suspicious_counts
    }

    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                invalid_json += 1
                continue

            total_records += 1
            title = record.get("title")
            ingredients = record.get("ingredients")
            if is_empty(title):
                empty_titles += 1
            if not isinstance(ingredients, list) or not ingredients:
                empty_ingredients += 1
                ingredients = []

            ingredient_count = len(ingredients)
            ingredient_total += ingredient_count
            min_ingredients = (
                ingredient_count
                if min_ingredients is None
                else min(min_ingredients, ingredient_count)
            )
            max_ingredients = (
                ingredient_count
                if max_ingredients is None
                else max(max_ingredients, ingredient_count)
            )

            for ingredient in ingredients:
                if not isinstance(ingredient, dict):
                    continue
                name = normalize_text(ingredient.get("name"))
                unit = normalize_text(ingredient.get("unit"))
                if name:
                    ingredient_counter[name] += 1
                if unit:
                    unit_counter[unit] += 1
                if ingredient.get("quantity") is None:
                    quantity_null += 1
                if ingredient.get("unit") is None:
                    unit_null += 1

            combined_text = f"{normalize_text(title)} {normalize_text(ingredient_names_text(ingredients))}"
            flags = {
                "alcohol": matches_any(combined_text, ALCOHOL_PATTERNS),
                "winter": matches_any(combined_text, WINTER_PATTERNS),
                "desserts": matches_any(combined_text, DESSERT_PATTERNS),
                "less_than_3_ingredients": ingredient_count < 3,
                "more_than_25_ingredients": ingredient_count > 25,
            }
            for key, matched in flags.items():
                if matched:
                    suspicious_counts[key] += 1
                    update_sample(
                        suspicious_samples[key],
                        record,
                        suspicious_counts[key],
                        args.sample_size,
                        rng,
                    )

            if line_number % 50_000 == 0:
                print(f"Processed {line_number} lines", file=sys.stderr)

    report = build_report(
        input_path=input_path,
        output_path=output_path,
        total_records=total_records,
        invalid_json=invalid_json,
        empty_titles=empty_titles,
        empty_ingredients=empty_ingredients,
        ingredient_total=ingredient_total,
        min_ingredients=min_ingredients,
        max_ingredients=max_ingredients,
        top_ingredients=ingredient_counter.most_common(200),
        top_units=unit_counter.most_common(200),
        quantity_null=quantity_null,
        unit_null=unit_null,
        suspicious_counts=suspicious_counts,
        suspicious_samples=suspicious_samples,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return total_records, output_path


def main() -> int:
    args = parse_args()
    total_records, output_path = audit_jsonl(args)
    print(f"Audited {total_records} JSONL records")
    print(f"Report written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
