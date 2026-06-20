#!/usr/bin/env python3
"""Streaming analyzer for the RecipeNLG CSV dataset.

Run from the repository root:
    python backend/scripts/analyze_recipe_dataset.py --input path/to/full_dataset.csv
    python backend/scripts/analyze_recipe_dataset.py --input path/to/full_dataset.csv --sample-size 20
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_PATH = ROOT / "reports" / "dataset_analysis.md"
DEFAULT_CHUNK_SIZE = 50_000
DEFAULT_SAMPLE_SIZE = 10

TITLE_COLUMNS = ("title", "name")
INSTRUCTION_COLUMNS = ("directions", "instructions", "steps", "method")
INGREDIENT_COLUMNS = ("ingredients", "ingredient", "ner")
STEP_COLUMNS = ("directions", "instructions", "steps")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a large RecipeNLG CSV dataset without importing recipes"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the RecipeNLG CSV file",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Number of sample records to include in the report",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help="Rows per CSV chunk while streaming the dataset",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to the Markdown report",
    )
    return parser.parse_args()


def import_pandas() -> Any:
    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit(
            "pandas is required for chunked CSV analysis. Install it and run again."
        ) from exc
    return pd


def normalize_column_lookup(columns: list[str]) -> dict[str, str]:
    return {column.strip().lower(): column for column in columns}


def find_column(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    lookup = normalize_column_lookup(columns)
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


def is_empty_series(series: Any) -> Any:
    text = series.fillna("").astype(str).str.strip()
    lowered = text.str.lower()
    return (text == "") | lowered.isin({"nan", "none", "null", "[]", "{}"})


def average_text_length(series: Any) -> tuple[int, int]:
    non_empty = series[~is_empty_series(series)].fillna("").astype(str)
    if non_empty.empty:
        return 0, 0
    lengths = non_empty.str.len()
    return int(lengths.sum()), int(lengths.count())


def shorten(value: Any, limit: int = 220) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def parse_list_like(value: Any) -> list[str]:
    text = str(value).strip()
    if not text:
        return []

    for loader in (ast.literal_eval, json.loads):
        try:
            parsed = loader(text)
        except Exception:
            continue
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
        if isinstance(parsed, str) and parsed.strip():
            return [parsed.strip()]

    if "|" in text:
        return [part.strip() for part in text.split("|") if part.strip()]
    if ";" in text:
        return [part.strip() for part in text.split(";") if part.strip()]
    return [text]


def add_first_examples(
    examples: OrderedDict[str, list[str]],
    name: str,
    value: Any,
    limit: int,
) -> None:
    if len(examples[name]) >= limit:
        return
    parsed = parse_list_like(value)
    for item in parsed:
        if len(examples[name]) >= limit:
            break
        examples[name].append(item)


def record_to_markdown(record: dict[str, Any], index: int) -> str:
    lines = [f"### Sample {index}"]
    for key, value in record.items():
        lines.append(f"- **{key}**: {shorten(value)}")
    return "\n".join(lines)


def build_report(
    input_path: Path,
    output_path: Path,
    total_rows: int,
    columns: list[str],
    empty_counts: dict[str, int],
    samples: list[dict[str, Any]],
    title_average: float | None,
    instruction_average: float | None,
    ingredient_examples: list[str],
    step_examples: list[str],
    chunk_size: int,
) -> str:
    lines = [
        "# RecipeNLG Dataset Analysis",
        "",
        "## Source",
        "",
        f"- Input: `{input_path}`",
        f"- Report: `{output_path}`",
        f"- Chunk size: `{chunk_size}` rows",
        "",
        "## Summary",
        "",
        f"- Total rows: `{total_rows}`",
        f"- Columns: `{len(columns)}`",
        "",
        "## Columns",
        "",
    ]

    for column in columns:
        empty = empty_counts.get(column, 0)
        filled = total_rows - empty
        filled_percent = (filled / total_rows * 100) if total_rows else 0
        lines.append(
            f"- `{column}`: filled `{filled_percent:.2f}%`, empty `{empty}`"
        )

    lines.extend(
        [
            "",
            "## Text Lengths",
            "",
            "- Average title length: "
            + (f"`{title_average:.2f}` characters" if title_average is not None else "`n/a`"),
            "- Average instruction length: "
            + (
                f"`{instruction_average:.2f}` characters"
                if instruction_average is not None
                else "`n/a`"
            ),
            "",
            "## Ingredient Examples",
            "",
        ]
    )

    if ingredient_examples:
        lines.extend(f"- {shorten(item, 180)}" for item in ingredient_examples[:10])
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Cooking Step Examples", ""])
    if step_examples:
        lines.extend(f"- {shorten(item, 220)}" for item in step_examples[:10])
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Sample Records", ""])
    if samples:
        for index, record in enumerate(samples, start=1):
            lines.append(record_to_markdown(record, index))
            lines.append("")
    else:
        lines.append("No records found.")

    return "\n".join(lines).rstrip() + "\n"


def analyze_dataset(args: argparse.Namespace) -> tuple[int, Path]:
    if args.sample_size < 1:
        raise SystemExit("--sample-size must be at least 1")
    if args.chunk_size < 1:
        raise SystemExit("--chunk-size must be at least 1")

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    pd = import_pandas()

    total_rows = 0
    columns: list[str] = []
    empty_counts: dict[str, int] = {}
    samples: list[dict[str, Any]] = []
    title_length_sum = 0
    title_length_count = 0
    instruction_length_sum = 0
    instruction_length_count = 0
    ingredient_examples: OrderedDict[str, list[str]] = OrderedDict([("items", [])])
    step_examples: OrderedDict[str, list[str]] = OrderedDict([("items", [])])

    reader = pd.read_csv(
        input_path,
        chunksize=args.chunk_size,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    )

    for chunk_index, chunk in enumerate(reader, start=1):
        if not columns:
            columns = [str(column) for column in chunk.columns]
            empty_counts = {column: 0 for column in columns}

        chunk_rows = len(chunk)
        total_rows += chunk_rows

        for column in columns:
            empty_counts[column] += int(is_empty_series(chunk[column]).sum())

        if len(samples) < args.sample_size:
            remaining = args.sample_size - len(samples)
            sample_chunk = chunk.head(remaining)
            samples.extend(sample_chunk.to_dict(orient="records"))

        title_column = find_column(columns, TITLE_COLUMNS)
        if title_column:
            length_sum, length_count = average_text_length(chunk[title_column])
            title_length_sum += length_sum
            title_length_count += length_count

        instruction_column = find_column(columns, INSTRUCTION_COLUMNS)
        if instruction_column:
            length_sum, length_count = average_text_length(chunk[instruction_column])
            instruction_length_sum += length_sum
            instruction_length_count += length_count

        ingredient_column = find_column(columns, INGREDIENT_COLUMNS)
        if ingredient_column and len(ingredient_examples["items"]) < 10:
            for value in chunk[ingredient_column]:
                add_first_examples(ingredient_examples, "items", value, 10)
                if len(ingredient_examples["items"]) >= 10:
                    break

        step_column = find_column(columns, STEP_COLUMNS)
        if step_column and len(step_examples["items"]) < 10:
            for value in chunk[step_column]:
                add_first_examples(step_examples, "items", value, 10)
                if len(step_examples["items"]) >= 10:
                    break

        print(f"Processed chunk {chunk_index}: {total_rows} rows", file=sys.stderr)

    title_average = (
        title_length_sum / title_length_count if title_length_count else None
    )
    instruction_average = (
        instruction_length_sum / instruction_length_count
        if instruction_length_count
        else None
    )

    report = build_report(
        input_path=input_path,
        output_path=output_path,
        total_rows=total_rows,
        columns=columns,
        empty_counts=empty_counts,
        samples=samples,
        title_average=title_average,
        instruction_average=instruction_average,
        ingredient_examples=ingredient_examples["items"],
        step_examples=step_examples["items"],
        chunk_size=args.chunk_size,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return total_rows, output_path


def main() -> int:
    args = parse_args()
    total_rows, output_path = analyze_dataset(args)
    print(f"Analyzed {total_rows} rows")
    print(f"Report written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
