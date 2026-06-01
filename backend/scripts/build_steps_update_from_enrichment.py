#!/usr/bin/env python3
"""Build final recipe steps update JSON from enrichment JSONL files.

Reads successful steps enrichment JSONL artifacts, validates the merged result,
and writes an update JSON plus a Markdown report. It does not read or write the
database.

Usage:
    python backend/scripts/build_steps_update_from_enrichment.py
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUTS = [
    ROOT / "exports" / "placeholder_recipe_steps_enriched_16.jsonl",
    ROOT / "exports" / "placeholder_recipe_steps_enriched_retry_2.jsonl",
]
DEFAULT_OUTPUT_PATH = ROOT / "exports" / "placeholder_recipe_steps_update_16.json"
DEFAULT_REPORT_PATH = ROOT / "reports" / "placeholder_recipe_steps_update_report.md"
EXPECTED_COUNT = 16
SOURCE = "steps_enrichment_v1"
FORBIDDEN_PHRASES = (
    "Подготовьте продукты",
    "Приготовьте по классическому рецепту",
    "Подавайте тёплым",
    "Подавайте теплым",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build recipe steps update JSON")
    parser.add_argument(
        "--input",
        action="append",
        default=None,
        help="Input enrichment JSONL path. Can be passed multiple times.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to output update JSON",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown report",
    )
    return parser.parse_args()


def normalize_text(value: Any) -> str:
    text_value = str(value or "").lower().replace("ё", "е")
    text_value = re.sub(r"\s+", " ", text_value)
    return text_value.strip()


def strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    if not path.exists():
        failures.append({"path": str(path), "line": None, "error": "input_not_found"})
        return records, failures
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                parsed = json.loads(strip_json_fence(line))
            except Exception as exc:
                failures.append(
                    {
                        "path": str(path),
                        "line": line_number,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            if not isinstance(parsed, dict):
                failures.append(
                    {
                        "path": str(path),
                        "line": line_number,
                        "error": "record_is_not_object",
                    }
                )
                continue
            parsed["_source_path"] = str(path)
            parsed["_source_line"] = line_number
            records.append(parsed)
    return records, failures


def validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        int(record.get("id"))
    except (TypeError, ValueError):
        errors.append("invalid_id")
    title = str(record.get("title") or "").strip()
    if not title:
        errors.append("missing_title")
    steps = record.get("steps")
    if not isinstance(steps, list):
        errors.append("steps_is_not_list")
        return errors
    normalized_steps = [str(step or "").strip() for step in steps if str(step or "").strip()]
    if len(normalized_steps) != len(steps):
        errors.append("blank_step")
    if not 5 <= len(normalized_steps) <= 9:
        errors.append("steps_count_not_5_to_9")
    all_steps = normalize_text(" ".join(normalized_steps))
    for phrase in FORBIDDEN_PHRASES:
        if normalize_text(phrase) in all_steps:
            errors.append(f"forbidden_phrase:{phrase}")
    return errors


def build_update_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(record["id"]),
        "title": str(record["title"]).strip(),
        "steps": [str(step).strip() for step in record["steps"]],
        "source": SOURCE,
    }


def fmt_inline(value: str) -> str:
    return value.replace("|", "\\|")


def build_report(
    input_paths: list[Path],
    output_path: Path,
    records: list[dict[str, Any]],
    read_failures: list[dict[str, Any]],
    invalid_records: list[dict[str, Any]],
    duplicate_ids: list[int],
    update_records: list[dict[str, Any]],
    wrote_output: bool,
) -> str:
    lines = [
        "# Placeholder Recipe Steps Update Report",
        "",
        "Scope: build update JSON from steps enrichment outputs. No database changes and no apply/import were performed.",
        "",
        "## Inputs",
        "",
    ]
    for path in input_paths:
        lines.append(f"- `{path}`")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Total input records: `{len(records)}`",
            f"- Unique records: `{len({int(record['id']) for record in records if str(record.get('id')).isdigit()})}`",
            f"- Expected records: `{EXPECTED_COUNT}`",
            f"- Invalid records: `{len(invalid_records) + len(read_failures)}`",
            f"- Duplicate IDs: `{len(duplicate_ids)}`",
            f"- Output: `{output_path}`",
            f"- Output written: `{wrote_output}`",
            "",
            "## Examples",
            "",
        ]
    )
    if update_records:
        for record in update_records[:5]:
            lines.append(f"### #{record['id']} {record['title']}")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(record, ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Invalid Records", ""])
    if not invalid_records and not read_failures:
        lines.append("- `n/a`")
    for failure in read_failures:
        lines.append(
            f"- `{failure.get('path')}` line `{failure.get('line')}`: `{failure.get('error')}`"
        )
    for item in invalid_records:
        record = item.get("record") or {}
        lines.append(
            f"- `#{record.get('id')}` {record.get('title')}: "
            f"`{', '.join(item.get('errors') or [])}`"
        )

    lines.extend(["", "## Duplicate IDs", ""])
    if not duplicate_ids:
        lines.append("- `n/a`")
    else:
        for recipe_id in duplicate_ids:
            lines.append(f"- `{recipe_id}`")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    input_paths = [
        Path(path).expanduser().resolve()
        for path in (args.input if args.input else DEFAULT_INPUTS)
    ]
    output_path = Path(args.output).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()

    records: list[dict[str, Any]] = []
    read_failures: list[dict[str, Any]] = []
    for path in input_paths:
        path_records, path_failures = load_jsonl(path)
        records.extend(path_records)
        read_failures.extend(path_failures)

    invalid_records: list[dict[str, Any]] = []
    for record in records:
        errors = validate_record(record)
        if errors:
            invalid_records.append({"record": record, "errors": errors})

    id_counts: Counter[int] = Counter()
    for record in records:
        try:
            id_counts[int(record.get("id"))] += 1
        except (TypeError, ValueError):
            continue
    duplicate_ids = sorted(recipe_id for recipe_id, count in id_counts.items() if count > 1)

    valid_records = [
        record
        for record in records
        if not any(item["record"] is record for item in invalid_records)
    ]
    update_records = sorted(
        [build_update_record(record) for record in valid_records],
        key=lambda item: item["id"],
    )

    can_write = (
        len(records) == EXPECTED_COUNT
        and len(update_records) == EXPECTED_COUNT
        and not read_failures
        and not invalid_records
        and not duplicate_ids
    )
    if can_write:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(update_records, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    report = build_report(
        input_paths=input_paths,
        output_path=output_path,
        records=records,
        read_failures=read_failures,
        invalid_records=invalid_records,
        duplicate_ids=duplicate_ids,
        update_records=update_records,
        wrote_output=can_write,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"Total input records: {len(records)}")
    print(f"Unique records: {len(id_counts)}")
    print(f"Invalid records: {len(invalid_records) + len(read_failures)}")
    print(f"Duplicate IDs: {len(duplicate_ids)}")
    print(f"Output written: {can_write}")
    print(f"Wrote report: {report_path}")
    if can_write:
        print(f"Wrote output: {output_path}")
    return 0 if can_write else 1


if __name__ == "__main__":
    raise SystemExit(main())
