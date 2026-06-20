#!/usr/bin/env python3
"""Convert Povarenok CSV rows to PlanAm-compatible raw JSONL.

Run from the repository root:
    python backend/scripts/convert_povarenok.py --input C:\\path\\to\\povarenok.csv
    python backend/scripts/convert_povarenok.py --input C:\\path\\to\\povarenok.csv --limit 100 --dry-run
"""

from __future__ import annotations

import argparse
import ast
import json
import random
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = Path(
    r"C:\Users\boss\Desktop\рецепты\povarenok_recipes_2021_06_16.csv"
)
DEFAULT_OUTPUT_PATH = ROOT / "exports" / "povarenok_planam_raw.jsonl"
DEFAULT_REPORT_PATH = ROOT / "reports" / "povarenok_conversion_report.md"
DEFAULT_CHUNK_SIZE = 50_000
DEFAULT_SAMPLE_SIZE = 20
RANDOM_SEED = 20210616

ENCODING_CANDIDATES = ("utf-8", "utf-8-sig", "cp1251", "windows-1251", "latin1")
MOJIBAKE_MARKERS = ("Ð", "Ñ", "Р", "С", "Ã", "Â")
REQUIRED_COLUMNS = ("url", "name", "ingredients")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Povarenok CSV to PlanAm raw JSONL without importing"
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to the Povarenok CSV file",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to the output JSONL file",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of converted recipes to write",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Number of converted JSONL examples to include in the report",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help="Rows per CSV chunk while streaming the dataset",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to the Markdown conversion report",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze and report without writing the JSONL export",
    )
    return parser.parse_args()


def import_pandas() -> Any:
    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit(
            "pandas is required for chunked CSV conversion. Install it and run again."
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


def normalize_name(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def is_empty(value: Any) -> bool:
    text = str(value).strip()
    if not text:
        return True
    return text.lower() in {"nan", "none", "null", "[]", "{}"}


def parse_ingredients_dict(value: Any) -> dict[str, Any] | None:
    if is_empty(value):
        return None
    try:
        parsed = ast.literal_eval(str(value))
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def parse_quantity_and_unit(value: Any) -> tuple[str | None, str | None, str | None]:
    if value is None:
        return None, None, None

    raw = str(value).strip()
    if not raw or raw.lower() in {"nan", "none", "null"}:
        return None, None, raw if raw else None

    match = re.match(
        r"^\s*(?P<quantity>\d+(?:[,.]\d+)?\s*-\s*\d+(?:[,.]\d+)?|\d+\s*[/\\]\s*\d+|\d+(?:[,.]\d+)?)"
        r"\s*(?P<unit>[^\d\s].*)?\s*$",
        raw,
    )
    if not match:
        return None, None, raw

    quantity = (
        re.sub(r"\s+", "", match.group("quantity"))
        .replace(",", ".")
        .replace("\\", "/")
    )
    unit = match.group("unit")
    unit = re.sub(r"\s+", " ", unit).strip() if unit else None
    return quantity, unit, raw


def convert_ingredients(value: Any) -> tuple[list[dict[str, Any]] | None, int, int]:
    source = parse_ingredients_dict(value)
    if not source:
        return None, 0, 0

    ingredients: list[dict[str, Any]] = []
    parsed_count = 0
    unparsed_count = 0
    for name, amount in source.items():
        ingredient_name = str(name).strip()
        if not ingredient_name:
            continue

        quantity, unit, raw = parse_quantity_and_unit(amount)
        if quantity is None:
            unparsed_count += 1
        else:
            parsed_count += 1

        ingredients.append(
            {
                "name": ingredient_name,
                "quantity": quantity,
                "unit": unit,
                "raw": raw,
            }
        )

    if not ingredients:
        return None, parsed_count, unparsed_count
    return ingredients, parsed_count, unparsed_count


def update_reservoir(
    reservoir: list[dict[str, Any]],
    record: dict[str, Any],
    seen_records: int,
    sample_size: int,
    rng: random.Random,
) -> None:
    if sample_size <= 0:
        return
    if len(reservoir) < sample_size:
        reservoir.append(record)
        return
    index = rng.randint(0, seen_records - 1)
    if index < sample_size:
        reservoir[index] = record


def shorten(value: Any, limit: int = 500) -> str:
    text = json.dumps(value, ensure_ascii=False)
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def build_record(row: dict[str, Any], ingredients: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source": "povarenok",
        "source_url": str(row["url"]).strip(),
        "title": str(row["name"]).strip(),
        "ingredients": ingredients,
        "steps": [],
    }


def build_report(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    encoding: str,
    dry_run: bool,
    total_rows: int,
    converted: int,
    skipped: int,
    duplicates: int,
    ingredients_parsed: int,
    ingredients_unparsed: int,
    samples: list[dict[str, Any]],
) -> str:
    lines = [
        "# Povarenok Conversion Report",
        "",
        "## Source",
        "",
        f"- Input: `{input_path}`",
        f"- Output: `{output_path}`",
        f"- Report: `{report_path}`",
        f"- Dry run: `{dry_run}`",
        f"- Detected encoding: `{encoding}`",
        f"- Encoding candidates: `{', '.join(ENCODING_CANDIDATES)}`",
        "",
        "## Summary",
        "",
        f"- Total rows: `{total_rows}`",
        f"- Converted: `{converted}`",
        f"- Skipped: `{skipped}`",
        f"- Duplicates: `{duplicates}`",
        f"- Ingredients parsed: `{ingredients_parsed}`",
        f"- Ingredients unparsed: `{ingredients_unparsed}`",
        "",
        "## JSONL Examples",
        "",
    ]

    if samples:
        for index, sample in enumerate(samples, start=1):
            lines.append(f"### Example {index}")
            lines.append("")
            lines.append("```json")
            lines.append(shorten(sample))
            lines.append("```")
            lines.append("")
    else:
        lines.append("No converted records.")

    return "\n".join(lines).rstrip() + "\n"


def validate_columns(columns: list[str]) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise SystemExit(f"Missing required columns: {', '.join(missing)}")


def convert_dataset(args: argparse.Namespace) -> tuple[int, Path, Path]:
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    if args.sample_size < 1:
        raise SystemExit("--sample-size must be at least 1")
    if args.chunk_size < 1:
        raise SystemExit("--chunk-size must be at least 1")

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    pd = import_pandas()
    rng = random.Random(RANDOM_SEED)
    encoding = detect_encoding(input_path)

    total_rows = 0
    converted = 0
    skipped = 0
    duplicates = 0
    ingredients_parsed = 0
    ingredients_unparsed = 0
    seen_names: set[str] = set()
    samples: list[dict[str, Any]] = []

    output_handle = None
    if not args.dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_handle = output_path.open("w", encoding="utf-8", newline="\n")

    try:
        reader = pd.read_csv(
            input_path,
            chunksize=args.chunk_size,
            dtype=str,
            keep_default_na=False,
            encoding=encoding,
            low_memory=False,
        )

        for chunk_index, chunk in enumerate(reader, start=1):
            columns = [str(column) for column in chunk.columns]
            validate_columns(columns)

            for row in chunk.to_dict(orient="records"):
                total_rows += 1
                name = row.get("name")
                ingredients_value = row.get("ingredients")

                if is_empty(name) or is_empty(ingredients_value):
                    skipped += 1
                    continue

                normalized = normalize_name(name)
                if normalized in seen_names:
                    duplicates += 1
                    skipped += 1
                    continue
                seen_names.add(normalized)

                ingredients, parsed_count, unparsed_count = convert_ingredients(
                    ingredients_value
                )
                if ingredients is None:
                    skipped += 1
                    continue

                record = build_record(row, ingredients)
                converted += 1
                ingredients_parsed += parsed_count
                ingredients_unparsed += unparsed_count

                update_reservoir(samples, record, converted, args.sample_size, rng)

                if output_handle is not None:
                    output_handle.write(json.dumps(record, ensure_ascii=False) + "\n")

                if args.limit is not None and converted >= args.limit:
                    raise StopIteration

            print(
                f"Processed chunk {chunk_index}: rows={total_rows}, converted={converted}",
                file=sys.stderr,
            )
    except StopIteration:
        pass
    finally:
        if output_handle is not None:
            output_handle.close()

    report = build_report(
        input_path=input_path,
        output_path=output_path,
        report_path=report_path,
        encoding=encoding,
        dry_run=args.dry_run,
        total_rows=total_rows,
        converted=converted,
        skipped=skipped,
        duplicates=duplicates,
        ingredients_parsed=ingredients_parsed,
        ingredients_unparsed=ingredients_unparsed,
        samples=samples,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return converted, output_path, report_path


def main() -> int:
    args = parse_args()
    converted, output_path, report_path = convert_dataset(args)
    print(f"Converted {converted} recipes")
    if args.dry_run:
        print("Dry run: JSONL export was not written")
    else:
        print(f"JSONL written to: {output_path}")
    print(f"Report written to: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
