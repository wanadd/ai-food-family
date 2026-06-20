#!/usr/bin/env python3
"""Safely apply nutrition backfill updates to recipes.

Default mode is dry-run. Use --commit to write changes.

Run from the repository root:
    python backend/scripts/apply_nutrition_backfill.py --input exports/nutrition_backfill_update_20.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
DEFAULT_INPUT_PATH = ROOT / "exports" / "nutrition_backfill_update_20.json"
DEFAULT_REPORT_PATH = ROOT / "reports" / "nutrition_backfill_apply_20_report.md"
NUTRITION_FIELDS = (
    "calories_per_serving",
    "protein_g",
    "fat_g",
    "carbs_g",
)
UPDATE_FIELDS = (*NUTRITION_FIELDS, "alcohol_percent")


@dataclass(frozen=True)
class UpdateRecord:
    id: int
    calories_per_serving: float
    protein_g: float
    fat_g: float
    carbs_g: float
    alcohol_percent: float | None
    nutrition_confidence: str | None
    nutrition_notes: str


@dataclass(frozen=True)
class CurrentRecipe:
    id: int
    title: str
    calories_per_serving: float | None
    protein_g: float | None
    fat_g: float | None
    carbs_g: float | None
    alcohol_percent: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply nutrition backfill updates")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to nutrition update JSON array",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown apply report",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing. This is the default.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually update recipes in the database.",
    )
    return parser.parse_args()


def non_negative_number(value: Any, field: str) -> float:
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


def parse_update_record(raw: Any, index: int) -> UpdateRecord:
    if not isinstance(raw, dict):
        raise ValueError(f"record_{index}_is_not_object")
    if raw.get("id") is None:
        raise ValueError("missing_id")
    try:
        recipe_id = int(raw["id"])
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_id") from exc

    return UpdateRecord(
        id=recipe_id,
        calories_per_serving=non_negative_number(
            raw.get("calories_per_serving"), "calories_per_serving"
        ),
        protein_g=non_negative_number(raw.get("protein_g"), "protein_g"),
        fat_g=non_negative_number(raw.get("fat_g"), "fat_g"),
        carbs_g=non_negative_number(raw.get("carbs_g"), "carbs_g"),
        alcohol_percent=optional_non_negative_number(
            raw.get("alcohol_percent"), "alcohol_percent"
        ),
        nutrition_confidence=(
            str(raw.get("nutrition_confidence")).strip()
            if raw.get("nutrition_confidence") is not None
            else None
        ),
        nutrition_notes=str(raw.get("nutrition_notes") or "").strip(),
    )


def load_updates(input_path: Path) -> tuple[list[UpdateRecord], list[dict[str, Any]]]:
    with input_path.open("r", encoding="utf-8") as handle:
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
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                    "raw": raw,
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
        alcohol_percent=row.get("alcohol_percent"),
    )


def load_current_sqlalchemy(
    database_url: str,
    ids: list[int],
) -> dict[int, CurrentRecipe]:
    if not ids:
        return {}
    engine = create_engine(database_url)
    query = text(
        """
        SELECT id, title, calories_per_serving, protein_g, fat_g, carbs_g, alcohol_percent
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
            SELECT id, title, calories_per_serving, protein_g, fat_g, carbs_g, alcohol_percent
            FROM recipes
            WHERE id IN ({id_list})
            ORDER BY id
        ) AS t;
        """
    rows = docker_psql_json(sql)
    return {int(row["id"]): row_to_current(row) for row in rows}


def sql_literal_number(value: float | None) -> str:
    return "NULL" if value is None else str(float(value))


def apply_update_sqlalchemy(database_url: str, update: UpdateRecord) -> None:
    engine = create_engine(database_url)
    query = text(
        """
        UPDATE recipes
        SET
            calories_per_serving = :calories_per_serving,
            protein_g = :protein_g,
            fat_g = :fat_g,
            carbs_g = :carbs_g,
            alcohol_percent = :alcohol_percent
        WHERE id = :id
        """
    )
    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "id": update.id,
                "calories_per_serving": update.calories_per_serving,
                "protein_g": update.protein_g,
                "fat_g": update.fat_g,
                "carbs_g": update.carbs_g,
                "alcohol_percent": update.alcohol_percent,
            },
        )


def apply_update_docker(update: UpdateRecord) -> None:
    sql = f"""
        UPDATE recipes
        SET
            calories_per_serving = {sql_literal_number(update.calories_per_serving)},
            protein_g = {sql_literal_number(update.protein_g)},
            fat_g = {sql_literal_number(update.fat_g)},
            carbs_g = {sql_literal_number(update.carbs_g)},
            alcohol_percent = {sql_literal_number(update.alcohol_percent)}
        WHERE id = {update.id};
        """
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
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        sql,
    ]
    subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )


def values_dict(value: CurrentRecipe | UpdateRecord) -> dict[str, Any]:
    return {field: getattr(value, field) for field in UPDATE_FIELDS}


def format_value(value: Any) -> str:
    return "NULL" if value is None else str(value)


def format_change(current: CurrentRecipe, update: UpdateRecord) -> str:
    parts = []
    for field in UPDATE_FIELDS:
        parts.append(
            f"{field}: {format_value(getattr(current, field))} -> "
            f"{format_value(getattr(update, field))}"
        )
    return "; ".join(parts)


def build_report(
    input_path: Path,
    report_path: Path,
    mode: str,
    connection: str,
    results: list[dict[str, Any]],
) -> str:
    updated = sum(item["status"] == "updated" for item in results)
    skipped = sum(item["status"] == "skipped" for item in results)
    failed = sum(item["status"] == "failed" for item in results)
    lines = [
        "# Nutrition Backfill Apply Report",
        "",
        "## Source",
        "",
        f"- Input: `{input_path}`",
        f"- Report: `{report_path}`",
        f"- Mode: `{mode}`",
        f"- DB connection: `{connection}`",
        "",
        "## Summary",
        "",
        f"- Updated: `{updated}`",
        f"- Skipped: `{skipped}`",
        f"- Failed: `{failed}`",
        "",
        "## Records",
        "",
    ]
    if not results:
        lines.append("- `n/a`")
    for item in results:
        recipe_id = item.get("id")
        title = item.get("title") or "n/a"
        lines.append(f"### Recipe #{recipe_id}: {title}")
        lines.append("")
        lines.append(f"- Status: `{item['status']}`")
        if item.get("error"):
            lines.append(f"- Error: `{item['error']}`")
        if item.get("current") is not None:
            lines.append("- Current:")
            lines.append("```json")
            lines.append(json.dumps(item["current"], ensure_ascii=False, indent=2))
            lines.append("```")
        if item.get("new") is not None:
            lines.append("- New:")
            lines.append("```json")
            lines.append(json.dumps(item["new"], ensure_ascii=False, indent=2))
            lines.append("```")
        if item.get("nutrition_confidence") or item.get("nutrition_notes"):
            lines.append(
                f"- Confidence/notes not written to DB: "
                f"{item.get('nutrition_confidence') or 'n/a'}; "
                f"{item.get('nutrition_notes') or ''}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    if args.dry_run and args.commit:
        raise SystemExit("Use either --dry-run or --commit, not both")

    mode = "commit" if args.commit else "dry-run"
    updates, results = load_updates(input_path)
    ids = [update.id for update in updates]

    try:
        current_by_id = load_current_sqlalchemy(args.database_url, ids)
        connection = "sqlalchemy"
    except SQLAlchemyError as exc:
        print(
            "SQLAlchemy connection failed, falling back to docker compose psql: "
            f"{exc.__class__.__name__}"
        )
        current_by_id = load_current_docker(ids)
        connection = "docker compose psql"

    for update in updates:
        current = current_by_id.get(update.id)
        if current is None:
            result = {
                "id": update.id,
                "title": None,
                "status": "failed",
                "error": "recipe_not_found",
                "current": None,
                "new": values_dict(update),
                "nutrition_confidence": update.nutrition_confidence,
                "nutrition_notes": update.nutrition_notes,
            }
            results.append(result)
            print(f"FAILED #{update.id}: recipe_not_found")
            continue

        print(f"#{update.id} {current.title}")
        print(f"  {format_change(current, update)}")

        result = {
            "id": update.id,
            "title": current.title,
            "status": "skipped",
            "error": None,
            "current": values_dict(current),
            "new": values_dict(update),
            "nutrition_confidence": update.nutrition_confidence,
            "nutrition_notes": update.nutrition_notes,
        }

        if args.commit:
            try:
                if connection == "sqlalchemy":
                    apply_update_sqlalchemy(args.database_url, update)
                else:
                    apply_update_docker(update)
                result["status"] = "updated"
            except Exception as exc:
                result["status"] = "failed"
                result["error"] = f"{type(exc).__name__}: {exc}"
                print(f"FAILED #{update.id}: {type(exc).__name__}: {exc}")

        results.append(result)

    report = build_report(
        input_path=input_path,
        report_path=report_path,
        mode=mode,
        connection=connection,
        results=results,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    updated = sum(item["status"] == "updated" for item in results)
    skipped = sum(item["status"] == "skipped" for item in results)
    failed = sum(item["status"] == "failed" for item in results)
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Report written to: {report_path}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
