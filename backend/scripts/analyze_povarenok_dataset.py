#!/usr/bin/env python3
"""Streaming auditor for a Povarenok CSV dataset.

Run from the repository root:
    python backend/scripts/analyze_povarenok_dataset.py --input C:\\path\\to\\povarenok.csv
    python backend/scripts/analyze_povarenok_dataset.py --input C:\\path\\to\\povarenok.csv --sample-size 20
"""

from __future__ import annotations

import argparse
import ast
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = Path(
    r"C:\Users\boss\Desktop\рецепты\povarenok_recipes_2021_06_16.csv"
)
DEFAULT_REPORT_PATH = ROOT / "reports" / "povarenok_analysis.md"
DEFAULT_CHUNK_SIZE = 50_000
DEFAULT_SAMPLE_SIZE = 20
RANDOM_SEED = 20210616
ENCODING_CANDIDATES = ("utf-8", "utf-8-sig", "cp1251", "windows-1251", "latin1")
MOJIBAKE_MARKERS = ("Ð", "Ñ", "Р", "С", "Ã", "Â")

TITLE_COLUMNS = ("name", "title", "recipe_name", "название")
CATEGORY_COLUMNS = ("category", "categories", "rubric", "tags", "категория")
PHOTO_COLUMNS = ("photo", "image", "image_url", "img", "picture", "фото")
INGREDIENT_COLUMNS = ("ingredients", "ingredient", "ингредиенты")
STEP_COLUMNS = ("steps", "directions", "instructions", "method", "cooking", "шаги")
TIME_COLUMNS = ("time", "cook_time", "cooking_time", "duration", "время")
RATING_COLUMNS = ("rating", "rate", "stars", "рейтинг")
CALORIE_COLUMNS = ("calories", "kcal", "kkal", "energy", "калории", "ккал")
PROTEIN_COLUMNS = ("protein", "proteins", "белки")
FAT_COLUMNS = ("fat", "fats", "жиры")
CARB_COLUMNS = ("carbohydrates", "carbs", "углеводы")
KBJU_COLUMNS = CALORIE_COLUMNS + PROTEIN_COLUMNS + FAT_COLUMNS + CARB_COLUMNS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a Povarenok CSV dataset without importing recipes"
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to the Povarenok CSV file",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Number of random recipes to include for manual audit",
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


def score_decoded_text(text: str) -> int:
    cyrillic = sum(1 for char in text if "а" <= char.lower() <= "я" or char in "ёЁ")
    mojibake = sum(text.count(marker) for marker in MOJIBAKE_MARKERS)
    controls = sum(
        1
        for char in text
        if ord(char) < 32 and char not in {"\r", "\n", "\t"}
    )
    replacement = text.count("\ufffd")
    return cyrillic * 4 - mojibake * 8 - controls * 20 - replacement * 50


def detect_encoding(input_path: Path) -> str:
    sample = input_path.read_bytes()[:256_000]
    scored: list[tuple[int, int, str]] = []
    for index, encoding in enumerate(ENCODING_CANDIDATES):
        try:
            text = sample.decode(encoding)
        except UnicodeDecodeError:
            continue
        scored.append((score_decoded_text(text), -index, encoding))

    if not scored:
        raise SystemExit(
            "Could not decode input with supported encodings: "
            + ", ".join(ENCODING_CANDIDATES)
        )

    scored.sort(reverse=True)
    best_encoding = scored[0][2]
    if best_encoding == "utf-8-sig" and not sample.startswith(b"\xef\xbb\xbf"):
        return "utf-8"
    return best_encoding


def normalize_column_name(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def find_columns(columns: list[str], candidates: tuple[str, ...]) -> list[str]:
    normalized_candidates = {normalize_column_name(candidate) for candidate in candidates}
    return [
        column
        for column in columns
        if normalize_column_name(column) in normalized_candidates
    ]


def find_column(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    matches = find_columns(columns, candidates)
    return matches[0] if matches else None


def is_empty_value(value: Any) -> bool:
    text = str(value).strip()
    if not text:
        return True
    return text.lower() in {"nan", "none", "null", "[]", "{}", "нет", "n/a"}


def is_empty_series(series: Any) -> Any:
    text = series.fillna("").astype(str).str.strip()
    lowered = text.str.lower()
    return (text == "") | lowered.isin({"nan", "none", "null", "[]", "{}", "нет", "n/a"})


def normalize_title(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def parse_structured_value(value: Any) -> Any:
    text = str(value).strip()
    if not text:
        return None
    for loader in (ast.literal_eval, json.loads):
        try:
            return loader(text)
        except Exception:
            continue
    return text


def split_text_items(value: Any) -> list[str]:
    parsed = parse_structured_value(value)
    if parsed is None:
        return []
    if isinstance(parsed, dict):
        return [str(key).strip() for key in parsed if str(key).strip()]
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]

    text = str(parsed).strip()
    if not text:
        return []
    for separator in ("|", ";", "\n"):
        if separator in text:
            return [part.strip() for part in text.split(separator) if part.strip()]
    return [text]


def count_ingredients(value: Any) -> int:
    return len(split_text_items(value))


def update_reservoir(
    reservoir: list[dict[str, Any]],
    row: dict[str, Any],
    seen_rows: int,
    sample_size: int,
    rng: random.Random,
) -> None:
    if sample_size <= 0:
        return
    if len(reservoir) < sample_size:
        reservoir.append(row)
        return
    index = rng.randint(0, seen_rows - 1)
    if index < sample_size:
        reservoir[index] = row


def shorten(value: Any, limit: int = 240) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def presence_line(label: str, present_rows: int, total_rows: int, columns: list[str]) -> str:
    percent = (present_rows / total_rows * 100) if total_rows else 0
    if not columns:
        return f"- {label}: column not found"
    return (
        f"- {label}: `{present_rows}` rows (`{percent:.2f}%`), "
        f"columns: `{', '.join(columns)}`"
    )


def record_to_markdown(record: dict[str, Any], index: int) -> str:
    lines = [f"### Recipe {index}"]
    for key, value in record.items():
        lines.append(f"- **{key}**: {shorten(value)}")
    return "\n".join(lines)


def build_report(
    input_path: Path,
    output_path: Path,
    encoding: str,
    total_rows: int,
    columns: list[str],
    empty_counts: dict[str, int],
    duplicate_title_groups: int,
    duplicate_title_rows: int,
    feature_presence: dict[str, int],
    feature_columns: dict[str, list[str]],
    top_categories: list[tuple[str, int]],
    average_ingredients: float | None,
    samples: list[dict[str, Any]],
    chunk_size: int,
) -> str:
    lines = [
        "# Povarenok Dataset Analysis",
        "",
        "## Source",
        "",
        f"- Input: `{input_path}`",
        f"- Report: `{output_path}`",
        f"- Detected encoding: `{encoding}`",
        f"- Encoding candidates: `{', '.join(ENCODING_CANDIDATES)}`",
        f"- Chunk size: `{chunk_size}` rows",
        "",
        "## Summary",
        "",
        f"- Recipes: `{total_rows}`",
        f"- Columns: `{len(columns)}`",
        f"- Duplicate title groups: `{duplicate_title_groups}`",
        f"- Duplicate recipe rows by title: `{duplicate_title_rows}`",
        "- Average ingredient count: "
        + (
            f"`{average_ingredients:.2f}`"
            if average_ingredients is not None
            else "`n/a`"
        ),
        "",
        "## Columns Fill Rate",
        "",
    ]

    for column in columns:
        empty = empty_counts.get(column, 0)
        filled = total_rows - empty
        filled_percent = (filled / total_rows * 100) if total_rows else 0
        lines.append(
            f"- `{column}`: filled `{filled_percent:.2f}%`, empty `{empty}`"
        )

    lines.extend(["", "## Feature Presence", ""])
    labels = {
        "categories": "Categories",
        "photos": "Photos",
        "ingredients": "Ingredients",
        "steps": "Cooking steps",
        "time": "Cooking time",
        "ratings": "Ratings",
        "kbju": "KBJU",
    }
    for key, label in labels.items():
        lines.append(
            presence_line(
                label,
                feature_presence.get(key, 0),
                total_rows,
                feature_columns.get(key, []),
            )
        )

    lines.extend(["", "## Top Categories", ""])
    if top_categories:
        for category, count in top_categories:
            lines.append(f"- {category}: `{count}`")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Random Recipes For Manual Audit", ""])
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
    rng = random.Random(RANDOM_SEED)
    encoding = detect_encoding(input_path)

    total_rows = 0
    columns: list[str] = []
    empty_counts: dict[str, int] = {}
    title_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    feature_presence = {
        "categories": 0,
        "photos": 0,
        "ingredients": 0,
        "steps": 0,
        "time": 0,
        "ratings": 0,
        "kbju": 0,
    }
    feature_columns: dict[str, list[str]] = {key: [] for key in feature_presence}
    ingredient_count_sum = 0
    ingredient_count_rows = 0
    samples: list[dict[str, Any]] = []

    reader = pd.read_csv(
        input_path,
        chunksize=args.chunk_size,
        dtype=str,
        keep_default_na=False,
        encoding=encoding,
        low_memory=False,
    )

    for chunk_index, chunk in enumerate(reader, start=1):
        if not columns:
            columns = [str(column) for column in chunk.columns]
            empty_counts = {column: 0 for column in columns}
            feature_columns["categories"] = find_columns(columns, CATEGORY_COLUMNS)
            feature_columns["photos"] = find_columns(columns, PHOTO_COLUMNS)
            feature_columns["ingredients"] = find_columns(columns, INGREDIENT_COLUMNS)
            feature_columns["steps"] = find_columns(columns, STEP_COLUMNS)
            feature_columns["time"] = find_columns(columns, TIME_COLUMNS)
            feature_columns["ratings"] = find_columns(columns, RATING_COLUMNS)
            feature_columns["kbju"] = find_columns(columns, KBJU_COLUMNS)

        rows_before_chunk = total_rows
        chunk_rows = len(chunk)
        total_rows += chunk_rows

        for column in columns:
            empty_counts[column] += int(is_empty_series(chunk[column]).sum())

        title_column = find_column(columns, TITLE_COLUMNS)
        if title_column:
            for title in chunk[title_column]:
                normalized = normalize_title(title)
                if normalized:
                    title_counts[normalized] += 1

        for key, matched_columns in feature_columns.items():
            if not matched_columns:
                continue
            non_empty_any = None
            for column in matched_columns:
                column_non_empty = ~is_empty_series(chunk[column])
                non_empty_any = (
                    column_non_empty
                    if non_empty_any is None
                    else non_empty_any | column_non_empty
                )
            feature_presence[key] += int(non_empty_any.sum()) if non_empty_any is not None else 0

        category_columns = feature_columns["categories"]
        if category_columns:
            for column in category_columns:
                for value in chunk[column]:
                    for category in split_text_items(value):
                        category_counts[category] += 1

        ingredient_column = find_column(columns, INGREDIENT_COLUMNS)
        if ingredient_column:
            for value in chunk[ingredient_column]:
                count = count_ingredients(value)
                if count:
                    ingredient_count_sum += count
                    ingredient_count_rows += 1

        for offset, row in enumerate(chunk.to_dict(orient="records"), start=1):
            update_reservoir(
                samples,
                row,
                rows_before_chunk + offset,
                args.sample_size,
                rng,
            )

        print(f"Processed chunk {chunk_index}: {total_rows} rows", file=sys.stderr)

    duplicate_title_groups = sum(1 for count in title_counts.values() if count > 1)
    duplicate_title_rows = sum(count - 1 for count in title_counts.values() if count > 1)
    average_ingredients = (
        ingredient_count_sum / ingredient_count_rows if ingredient_count_rows else None
    )

    report = build_report(
        input_path=input_path,
        output_path=output_path,
        encoding=encoding,
        total_rows=total_rows,
        columns=columns,
        empty_counts=empty_counts,
        duplicate_title_groups=duplicate_title_groups,
        duplicate_title_rows=duplicate_title_rows,
        feature_presence=feature_presence,
        feature_columns=feature_columns,
        top_categories=category_counts.most_common(20),
        average_ingredients=average_ingredients,
        samples=samples,
        chunk_size=args.chunk_size,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return total_rows, output_path


def main() -> int:
    args = parse_args()
    total_rows, output_path = analyze_dataset(args)
    print(f"Analyzed {total_rows} recipes")
    print(f"Report written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
