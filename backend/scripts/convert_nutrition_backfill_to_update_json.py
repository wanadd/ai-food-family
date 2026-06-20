#!/usr/bin/env python3
"""Convert nutrition backfill JSONL to a validated update JSON file.

This script does not write to the database or import data.

Run from the repository root:
    python backend/scripts/convert_nutrition_backfill_to_update_json.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = ROOT / "exports" / "nutrition_backfill_20.jsonl"
DEFAULT_OUTPUT_PATH = ROOT / "exports" / "nutrition_backfill_update_20.json"
DEFAULT_REPORT_PATH = ROOT / "reports" / "nutrition_backfill_update_20_report.md"
ALLOWED_CONFIDENCE = {"low", "medium", "high"}
NUTRITION_FIELDS = (
    "calories_per_serving",
    "protein_g",
    "fat_g",
    "carbs_g",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert nutrition backfill JSONL to update JSON"
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to nutrition backfill JSONL",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to update JSON array",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown conversion report",
    )
    return parser.parse_args()


def number_or_error(value: Any, field: str) -> float:
    if value is None:
        raise ValueError(f"{field}_is_null")
    if isinstance(value, bool):
        raise ValueError(f"{field}_is_boolean")
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field}_is_not_number")
    number = float(value)
    if number < 0:
        raise ValueError(f"{field}_is_negative")
    return number


def optional_non_negative_number(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field}_is_boolean")
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field}_is_not_number")
    number = float(value)
    if number < 0:
        raise ValueError(f"{field}_is_negative")
    return number


def normalize_confidence(value: Any) -> str:
    confidence = str(value or "").strip().lower()
    if confidence not in ALLOWED_CONFIDENCE:
        raise ValueError("invalid_confidence")
    return confidence


def convert_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("id") is None:
        raise ValueError("missing_id")
    try:
        recipe_id = int(record["id"])
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_id") from exc

    backfill = record.get("backfill")
    if not isinstance(backfill, dict):
        raise ValueError("missing_backfill")

    converted: dict[str, Any] = {"id": recipe_id}
    for field in NUTRITION_FIELDS:
        converted[field] = number_or_error(backfill.get(field), field)

    converted["alcohol_percent"] = optional_non_negative_number(
        backfill.get("alcohol_percent"),
        "alcohol_percent",
    )
    converted["nutrition_confidence"] = normalize_confidence(
        backfill.get("confidence")
    )
    converted["nutrition_notes"] = str(backfill.get("notes") or "").strip()
    return converted


def read_and_convert(input_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    updates: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    total_read = 0

    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            total_read += 1
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("record_is_not_object")
                updates.append(convert_record(record))
            except Exception as exc:
                errors.append(
                    {
                        "line": line_number,
                        "error": f"{type(exc).__name__}: {exc}",
                        "raw": line.strip(),
                    }
                )

    return updates, errors, total_read


def build_report(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    total_read: int,
    updates: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> str:
    lines = [
        "# Nutrition Backfill Update Conversion Report",
        "",
        "## Source",
        "",
        f"- Input: `{input_path}`",
        f"- Output: `{output_path}`",
        f"- Report: `{report_path}`",
        "",
        "## Summary",
        "",
        f"- Total JSONL records read: `{total_read}`",
        f"- Valid update records: `{len(updates)}`",
        f"- Invalid records: `{len(errors)}`",
        "- Mode: `file conversion only; database unchanged`",
        "",
        "## Validation Rules",
        "",
        "- KБЖУ fields must be present, numeric, and `>= 0`.",
        "- `nutrition_confidence` must be `low`, `medium`, or `high`.",
        "- `alcohol_percent` must be `null` or numeric `>= 0`.",
        "",
        "## Errors",
        "",
    ]
    if errors:
        for item in errors[:100]:
            lines.append(f"- Line `{item['line']}`: {item['error']}")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Examples", ""])
    if updates:
        for index, update in enumerate(updates[:5], start=1):
            lines.append(f"### Example {index}")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(update, ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")
    else:
        lines.append("- `n/a`")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    updates, errors, total_read = read_and_convert(input_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(updates, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = build_report(
        input_path=input_path,
        output_path=output_path,
        report_path=report_path,
        total_read=total_read,
        updates=updates,
        errors=errors,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"Total JSONL records read: {total_read}")
    print(f"Valid update records: {len(updates)}")
    print(f"Invalid records: {len(errors)}")
    print(f"Update JSON written to: {output_path}")
    print(f"Report written to: {report_path}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
