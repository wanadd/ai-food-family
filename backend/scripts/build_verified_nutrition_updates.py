"""Build verified-safe calculated nutrition updates without changing the database.

Splits calculated_nutrition_updates_safe.json into:
- verified-safe records with no suspicious current-vs-new delta
- delta-suspicious records for manual review

Usage:
    python backend/scripts/build_verified_nutrition_updates.py
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from audit_nutrition_update_deltas import (
    DEFAULT_DATABASE_URL,
    NUTRITION_FIELDS,
    ROOT,
    SUSPICIOUS_MULTIPLIERS,
    analyze_updates,
    fmt_number,
    fmt_percent,
    fmt_title,
    load_current_docker,
    load_current_sqlalchemy,
    load_updates,
)


DEFAULT_INPUT_PATH = ROOT / "exports" / "calculated_nutrition_updates_safe.json"
DEFAULT_VERIFIED_SAFE_OUTPUT_PATH = (
    ROOT / "exports" / "calculated_nutrition_updates_verified_safe.json"
)
DEFAULT_DELTA_SUSPICIOUS_OUTPUT_PATH = (
    ROOT / "exports" / "calculated_nutrition_updates_delta_suspicious.json"
)
DEFAULT_REPORT_PATH = ROOT / "reports" / "verified_nutrition_updates_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build verified nutrition updates")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to calculated nutrition update JSON array",
    )
    parser.add_argument(
        "--verified-safe-output",
        default=str(DEFAULT_VERIFIED_SAFE_OUTPUT_PATH),
        help="Path to verified-safe output JSON array",
    )
    parser.add_argument(
        "--delta-suspicious-output",
        default=str(DEFAULT_DELTA_SUSPICIOUS_OUTPUT_PATH),
        help="Path to delta-suspicious output JSON array",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown verified update report",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    return parser.parse_args()


def load_raw_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        records = json.load(handle)
    if not isinstance(records, list):
        raise SystemExit("Input must be a JSON array")
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise SystemExit(f"Input record {index} must be an object")
    return records


def write_json(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def relative_or_absolute(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def build_report(
    input_path: Path,
    verified_safe_output_path: Path,
    delta_suspicious_output_path: Path,
    connection_note: str,
    results: list[dict[str, Any]],
    verified_safe: list[dict[str, Any]],
    delta_suspicious: list[dict[str, Any]],
    parse_failures: list[dict[str, Any]],
    missing: list[dict[str, Any]],
) -> str:
    suspicious_counts = {
        field: sum(field in item["suspicious_fields"] for item in results)
        for field in NUTRITION_FIELDS
    }
    lines = [
        "# Verified Nutrition Updates Report",
        "",
        "Scope: read-only build of verified nutrition update JSON files. No database changes, recipe updates, imports, migrations, or apply --commit were performed.",
        "",
        "## Summary",
        "",
        f"- Input: `{relative_or_absolute(input_path)}`",
        f"- Database read method: `{connection_note}`",
        f"- Verified-safe output: `{relative_or_absolute(verified_safe_output_path)}`",
        f"- Delta-suspicious output: `{relative_or_absolute(delta_suspicious_output_path)}`",
        f"- Total safe records: `{len(results) + len(missing)}`",
        f"- Verified safe records: `{len(verified_safe)}`",
        f"- Delta suspicious records: `{len(delta_suspicious)}`",
        f"- Missing recipes excluded from verified safe: `{len(missing)}`",
        f"- Parse failures: `{len(parse_failures)}`",
        "",
        "## Exclusion Thresholds",
        "",
        "- calories_per_serving: changed more than `2.5x`",
        "- protein_g: changed more than `3x`",
        "- fat_g: changed more than `3x`",
        "- carbs_g: changed more than `3x`",
        "",
        "## Delta Suspicious By Field",
        "",
        "| Field | Suspicious records | Threshold |",
        "| --- | ---: | ---: |",
    ]
    for field in NUTRITION_FIELDS:
        lines.append(f"| {field} | {suspicious_counts[field]} | {SUSPICIOUS_MULTIPLIERS[field]}x |")

    lines.extend(
        [
            "",
            "## Delta Suspicious Records",
            "",
            "| ID | Title | Fields | Max fold-change |",
            "| ---: | --- | --- | ---: |",
        ]
    )
    if not delta_suspicious:
        lines.append("| n/a | n/a | n/a | n/a |")
    suspicious_by_id = {int(record["id"]): record for record in delta_suspicious}
    for item in sorted(
        (row for row in results if row["suspicious"]),
        key=lambda row: max(
            row["deltas"][field]["multiplier"] or 0
            for field in row["suspicious_fields"]
        ),
        reverse=True,
    ):
        if item["id"] not in suspicious_by_id:
            continue
        max_multiplier = max(
            item["deltas"][field]["multiplier"] or 0
            for field in item["suspicious_fields"]
        )
        lines.append(
            f"| {item['id']} | {fmt_title(item['title'])} | "
            f"{', '.join(item['suspicious_fields'])} | {fmt_number(max_multiplier)}x |"
        )

    lines.extend(
        [
            "",
            "## Top Verified-Safe Calorie Deltas",
            "",
            "| ID | Title | Current | New | Abs delta | Percent delta | Fold-change |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    verified_ids = {int(record["id"]) for record in verified_safe}
    verified_results = [item for item in results if item["id"] in verified_ids]
    for item in sorted(
        verified_results,
        key=lambda row: row["deltas"]["calories_per_serving"]["absolute"] or 0,
        reverse=True,
    )[:30]:
        delta = item["deltas"]["calories_per_serving"]
        lines.append(
            f"| {item['id']} | {fmt_title(item['title'])} | "
            f"{fmt_number(delta['current'])} | {fmt_number(delta['new'])} | "
            f"{fmt_number(delta['absolute'])} | {fmt_percent(delta['percent'])} | "
            f"{fmt_number(delta['multiplier'])}x |"
        )

    lines.extend(["", "## Missing Recipes", ""])
    if not missing:
        lines.append("- `n/a`")
    for item in missing[:50]:
        lines.append(f"- `#{item['id']}` {item['title']}: `{item['error']}`")

    lines.extend(["", "## Parse Failures", ""])
    if not parse_failures:
        lines.append("- `n/a`")
    for item in parse_failures[:50]:
        lines.append(
            f"- `#{item.get('id')}` {item.get('title')}: `{item.get('error')}`"
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    verified_safe_output_path = Path(args.verified_safe_output).expanduser().resolve()
    delta_suspicious_output_path = Path(args.delta_suspicious_output).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()

    raw_records = load_raw_records(input_path)
    raw_by_id = {int(record["id"]): record for record in raw_records if "id" in record}
    updates, parse_failures = load_updates(input_path)
    ids = [update.id for update in updates]

    try:
        current_by_id = load_current_sqlalchemy(args.database_url, ids)
        connection_note = "SQLAlchemy"
    except Exception as exc:
        print(
            "SQLAlchemy connection failed, falling back to docker compose psql: "
            f"{exc.__class__.__name__}"
        )
        current_by_id = load_current_docker(ids)
        connection_note = "docker compose psql"

    results, missing = analyze_updates(updates, current_by_id)
    verified_safe_ids = {
        item["id"] for item in results if not item["suspicious"] and item["id"] in raw_by_id
    }
    delta_suspicious_ids = {
        item["id"] for item in results if item["suspicious"] and item["id"] in raw_by_id
    }
    verified_safe = [
        record for record in raw_records if int(record.get("id", -1)) in verified_safe_ids
    ]
    delta_suspicious = [
        record for record in raw_records if int(record.get("id", -1)) in delta_suspicious_ids
    ]

    write_json(verified_safe_output_path, verified_safe)
    write_json(delta_suspicious_output_path, delta_suspicious)

    report = build_report(
        input_path=input_path,
        verified_safe_output_path=verified_safe_output_path,
        delta_suspicious_output_path=delta_suspicious_output_path,
        connection_note=connection_note,
        results=results,
        verified_safe=verified_safe,
        delta_suspicious=delta_suspicious,
        parse_failures=parse_failures,
        missing=missing,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"Total safe records: {len(updates)}")
    print(f"Verified safe records: {len(verified_safe)}")
    print(f"Delta suspicious records: {len(delta_suspicious)}")
    print(f"Missing recipes excluded from verified safe: {len(missing)}")
    print(f"Parse failures: {len(parse_failures)}")
    print(f"Wrote verified safe: {verified_safe_output_path}")
    print(f"Wrote delta suspicious: {delta_suspicious_output_path}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
