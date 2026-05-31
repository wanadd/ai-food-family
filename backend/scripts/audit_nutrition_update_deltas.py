"""Audit calculated nutrition update deltas without changing the database.

Compares the safe calculated nutrition update export against current recipes
nutrition values and writes a Markdown report.

Usage:
    python backend/scripts/audit_nutrition_update_deltas.py
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:  # pragma: no cover - docker fallback handles local script runs.
    create_engine = None
    text = None

    class SQLAlchemyError(Exception):
        pass


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
DEFAULT_INPUT_PATH = ROOT / "exports" / "calculated_nutrition_updates_safe.json"
DEFAULT_REPORT_PATH = ROOT / "reports" / "nutrition_update_delta_audit.md"

NUTRITION_FIELDS = (
    "calories_per_serving",
    "protein_g",
    "fat_g",
    "carbs_g",
)
SUSPICIOUS_MULTIPLIERS = {
    "calories_per_serving": 2.5,
    "protein_g": 3.0,
    "fat_g": 3.0,
    "carbs_g": 3.0,
}


@dataclass(frozen=True)
class UpdateRecord:
    id: int
    title: str
    calories_per_serving: float
    protein_g: float
    fat_g: float
    carbs_g: float
    source: str


@dataclass(frozen=True)
class CurrentRecipe:
    id: int
    title: str
    calories_per_serving: float | None
    protein_g: float | None
    fat_g: float | None
    carbs_g: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit nutrition update deltas")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to calculated nutrition update JSON array",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown delta audit report",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    return parser.parse_args()


def non_negative_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field}_is_boolean")
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field}_is_not_number")
    number = float(value)
    if number < 0:
        raise ValueError(f"{field}_is_negative")
    return number


def parse_update_record(raw: Any, index: int) -> UpdateRecord:
    if not isinstance(raw, dict):
        raise ValueError(f"record_{index}_is_not_object")
    try:
        recipe_id = int(raw["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid_id") from exc
    source = str(raw.get("source") or "").strip()
    if source != "ingredient_engine_v2":
        raise ValueError("invalid_source")
    return UpdateRecord(
        id=recipe_id,
        title=str(raw.get("title") or "").strip(),
        calories_per_serving=non_negative_number(
            raw.get("calories_per_serving"), "calories_per_serving"
        ),
        protein_g=non_negative_number(raw.get("protein_g"), "protein_g"),
        fat_g=non_negative_number(raw.get("fat_g"), "fat_g"),
        carbs_g=non_negative_number(raw.get("carbs_g"), "carbs_g"),
        source=source,
    )


def load_updates(path: Path) -> tuple[list[UpdateRecord], list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as handle:
        raw_updates = json.load(handle)
    if not isinstance(raw_updates, list):
        raise SystemExit("Input must be a JSON array")

    updates: list[UpdateRecord] = []
    failures: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for index, raw in enumerate(raw_updates, start=1):
        try:
            update = parse_update_record(raw, index)
            if update.id in seen_ids:
                raise ValueError("duplicate_id")
            seen_ids.add(update.id)
            updates.append(update)
        except Exception as exc:
            failures.append(
                {
                    "id": raw.get("id") if isinstance(raw, dict) else None,
                    "title": raw.get("title") if isinstance(raw, dict) else "",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    return updates, failures


def row_to_current(row: Any) -> CurrentRecipe:
    return CurrentRecipe(
        id=int(row["id"]),
        title=str(row.get("title") or ""),
        calories_per_serving=row.get("calories_per_serving"),
        protein_g=row.get("protein_g"),
        fat_g=row.get("fat_g"),
        carbs_g=row.get("carbs_g"),
    )


def load_current_sqlalchemy(
    database_url: str,
    ids: list[int],
) -> dict[int, CurrentRecipe]:
    if not ids:
        return {}
    if create_engine is None or text is None:
        raise SQLAlchemyError("sqlalchemy_not_installed")
    engine = create_engine(database_url)
    query = text(
        """
        SELECT id, title, calories_per_serving, protein_g, fat_g, carbs_g
        FROM recipes
        WHERE id = ANY(:ids)
        ORDER BY id
        """
    )
    with engine.connect() as conn:
        rows = list(conn.execute(query, {"ids": ids}).mappings())
    return {int(row["id"]): row_to_current(row) for row in rows}


def docker_psql_json(sql: str) -> Any:
    cmd = [
        "docker",
        "compose",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        "aifood",
        "-d",
        "aifood",
        "-t",
        "-A",
        "-c",
        sql,
    ]
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return json.loads(result.stdout.strip() or "[]")


def load_current_docker(ids: list[int]) -> dict[int, CurrentRecipe]:
    if not ids:
        return {}
    id_list = ", ".join(str(recipe_id) for recipe_id in ids)
    sql = f"""
        SELECT COALESCE(json_agg(row_to_json(t) ORDER BY id), '[]'::json)
        FROM (
            SELECT id, title, calories_per_serving, protein_g, fat_g, carbs_g
            FROM recipes
            WHERE id IN ({id_list})
            ORDER BY id
        ) AS t;
        """
    rows = docker_psql_json(sql)
    return {int(row["id"]): row_to_current(row) for row in rows}


def percent_delta(current: float | None, new: float) -> float | None:
    if current is None or current == 0:
        return None
    return abs(new - current) / abs(current) * 100


def fold_change(current: float | None, new: float) -> float | None:
    if current is None:
        return None
    if current == 0 and new == 0:
        return 1.0
    if current == 0 or new == 0:
        return float("inf")
    return max(abs(current), abs(new)) / min(abs(current), abs(new))


def fmt_number(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    if value == float("inf"):
        return "inf"
    return f"{value:.1f}"


def fmt_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f}%"


def fmt_title(value: str) -> str:
    return value.replace("|", "\\|")


def analyze_updates(
    updates: list[UpdateRecord],
    current_by_id: dict[int, CurrentRecipe],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for update in updates:
        current = current_by_id.get(update.id)
        if current is None:
            missing.append(
                {
                    "id": update.id,
                    "title": update.title,
                    "error": "recipe_not_found",
                }
            )
            continue

        deltas: dict[str, dict[str, float | None]] = {}
        suspicious_fields: list[str] = []
        for field in NUTRITION_FIELDS:
            current_value = getattr(current, field)
            new_value = getattr(update, field)
            absolute = None if current_value is None else abs(new_value - current_value)
            percent = percent_delta(current_value, new_value)
            multiplier = fold_change(current_value, new_value)
            threshold = SUSPICIOUS_MULTIPLIERS[field]
            if multiplier is not None and multiplier > threshold:
                suspicious_fields.append(field)
            deltas[field] = {
                "current": current_value,
                "new": new_value,
                "absolute": absolute,
                "percent": percent,
                "multiplier": multiplier,
            }

        results.append(
            {
                "id": update.id,
                "title": current.title or update.title,
                "deltas": deltas,
                "suspicious_fields": suspicious_fields,
                "suspicious": bool(suspicious_fields),
            }
        )
    return results, missing


def biggest_calorie_deltas(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        results,
        key=lambda item: item["deltas"]["calories_per_serving"]["absolute"] or 0,
        reverse=True,
    )[:30]


def biggest_macro_deltas(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    macro_rows: list[dict[str, Any]] = []
    for item in results:
        for field in ("protein_g", "fat_g", "carbs_g"):
            delta = item["deltas"][field]
            macro_rows.append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "field": field,
                    "delta": delta,
                    "suspicious": field in item["suspicious_fields"],
                }
            )
    return sorted(
        macro_rows,
        key=lambda item: item["delta"]["absolute"] or 0,
        reverse=True,
    )[:30]


def build_report(
    input_path: Path,
    connection_note: str,
    total_safe_records: int,
    results: list[dict[str, Any]],
    parse_failures: list[dict[str, Any]],
    missing: list[dict[str, Any]],
) -> str:
    suspicious = [item for item in results if item["suspicious"]]
    suspicious_counts = {
        field: sum(field in item["suspicious_fields"] for item in results)
        for field in NUTRITION_FIELDS
    }
    lines = [
        "# Nutrition Update Delta Audit",
        "",
        "Scope: read-only delta audit for calculated nutrition updates. No database changes, recipe updates, imports, migrations, or apply --commit were performed.",
        "",
        "## Summary",
        "",
        f"- Input: `{input_path.relative_to(ROOT) if input_path.is_relative_to(ROOT) else input_path}`",
        f"- Database read method: `{connection_note}`",
        f"- Total safe records: `{total_safe_records}`",
        f"- Suspicious by delta: `{len(suspicious)}`",
        f"- Missing recipes: `{len(missing)}`",
        f"- Parse failures: `{len(parse_failures)}`",
        "",
        "## Suspicious Thresholds",
        "",
        "- calories_per_serving: changed more than `2.5x`",
        "- protein_g: changed more than `3x`",
        "- fat_g: changed more than `3x`",
        "- carbs_g: changed more than `3x`",
        "",
        "## Suspicious By Field",
        "",
        "| Field | Suspicious records |",
        "| --- | ---: |",
    ]
    for field in NUTRITION_FIELDS:
        lines.append(f"| {field} | {suspicious_counts[field]} |")

    lines.extend(
        [
            "",
            "## Suspicious By Delta",
            "",
            "| ID | Title | Fields | Max fold-change |",
            "| ---: | --- | --- | ---: |",
        ]
    )
    if not suspicious:
        lines.append("| n/a | n/a | n/a | n/a |")
    for item in sorted(
        suspicious,
        key=lambda row: max(
            row["deltas"][field]["multiplier"] or 0
            for field in row["suspicious_fields"]
        ),
        reverse=True,
    ):
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
            "## Top 30 Biggest Calorie Deltas",
            "",
            "| ID | Title | Current | New | Abs delta | Percent delta | Fold-change | Suspicious |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for item in biggest_calorie_deltas(results):
        delta = item["deltas"]["calories_per_serving"]
        lines.append(
            f"| {item['id']} | {fmt_title(item['title'])} | "
            f"{fmt_number(delta['current'])} | {fmt_number(delta['new'])} | "
            f"{fmt_number(delta['absolute'])} | {fmt_percent(delta['percent'])} | "
            f"{fmt_number(delta['multiplier'])}x | "
            f"{'yes' if 'calories_per_serving' in item['suspicious_fields'] else 'no'} |"
        )

    lines.extend(
        [
            "",
            "## Top 30 Biggest Macro Deltas",
            "",
            "| ID | Title | Field | Current | New | Abs delta | Percent delta | Fold-change | Suspicious |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for item in biggest_macro_deltas(results):
        delta = item["delta"]
        lines.append(
            f"| {item['id']} | {fmt_title(item['title'])} | {item['field']} | "
            f"{fmt_number(delta['current'])} | {fmt_number(delta['new'])} | "
            f"{fmt_number(delta['absolute'])} | {fmt_percent(delta['percent'])} | "
            f"{fmt_number(delta['multiplier'])}x | "
            f"{'yes' if item['suspicious'] else 'no'} |"
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
    report_path = Path(args.report).expanduser().resolve()

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
    report = build_report(
        input_path=input_path,
        connection_note=connection_note,
        total_safe_records=len(updates),
        results=results,
        parse_failures=parse_failures,
        missing=missing,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"Total safe records: {len(updates)}")
    print(f"Suspicious by delta: {sum(item['suspicious'] for item in results)}")
    print(f"Missing recipes: {len(missing)}")
    print(f"Parse failures: {len(parse_failures)}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()
