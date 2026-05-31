#!/usr/bin/env python3
"""Safely apply calculated nutrition updates to recipes.

Default mode is dry-run. Use --commit to write the allowed nutrition fields.

Run from the repository root:
    python backend/scripts/apply_calculated_nutrition_updates.py --dry-run
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
DEFAULT_INPUT_PATH = ROOT / "exports" / "calculated_nutrition_updates_safe.json"
DEFAULT_REPORT_PATH = ROOT / "reports" / "calculated_nutrition_apply_report.md"
UPDATE_FIELDS = (
    "calories_per_serving",
    "protein_g",
    "fat_g",
    "carbs_g",
    "alcohol_percent",
)


@dataclass(frozen=True)
class UpdateRecord:
    id: int
    title: str
    calories_per_serving: float
    protein_g: float
    fat_g: float
    carbs_g: float
    alcohol_percent: float | None
    source: str


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
    parser = argparse.ArgumentParser(description="Apply calculated nutrition updates")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to calculated nutrition update JSON array",
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
        alcohol_percent=optional_non_negative_number(
            raw.get("alcohol_percent"), "alcohol_percent"
        ),
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
                    "status": "failed",
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


def sql_number(value: float | None) -> str:
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
            calories_per_serving = {sql_number(update.calories_per_serving)},
            protein_g = {sql_number(update.protein_g)},
            fat_g = {sql_number(update.fat_g)},
            carbs_g = {sql_number(update.carbs_g)},
            alcohol_percent = {sql_number(update.alcohol_percent)}
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


def values_for(update: UpdateRecord) -> dict[str, float | None]:
    return {field: getattr(update, field) for field in UPDATE_FIELDS}


def values_current(current: CurrentRecipe) -> dict[str, float | None]:
    return {field: getattr(current, field) for field in UPDATE_FIELDS}


def build_report(
    mode: str,
    input_path: Path,
    connection_note: str,
    results: list[dict[str, Any]],
    parse_failures: list[dict[str, Any]],
) -> str:
    updated = sum(item["status"] == "updated" for item in results)
    skipped = sum(item["status"] == "skipped" for item in results)
    failed = sum(item["status"] == "failed" for item in results) + len(parse_failures)
    suspicious = [
        item
        for item in results
        if item.get("status") != "failed"
        and item.get("new", {}).get("calories_per_serving", 0) < 5
    ]
    lines = [
        "# Calculated Nutrition Apply Report",
        "",
        "Scope: safe apply pipeline for calculated nutrition updates. Dry-run mode does not write to the database.",
        "",
        "## Summary",
        "",
        f"- Mode: `{mode}`",
        f"- Read/apply connection: `{connection_note}`",
        f"- Input: `{input_path}`",
        f"- Updated: `{updated}`",
        f"- Skipped: `{skipped}`",
        f"- Failed: `{failed}`",
        f"- Suspicious low-calorie updates (<5 kcal): `{len(suspicious)}`",
        "",
        "## Changes",
        "",
    ]
    for item in results[:80]:
        if item["status"] == "failed":
            lines.append(
                f"- `#{item.get('id')}` {item.get('title')}: failed `{item.get('error')}`"
            )
            continue
        lines.append(
            f"- `#{item['id']}` {item['title']}: `{item['status']}` "
            f"current={json.dumps(item['current'], ensure_ascii=False)} -> "
            f"new={json.dumps(item['new'], ensure_ascii=False)}"
        )

    lines.extend(["", "## Suspicious Updates For Manual Review", ""])
    if not suspicious:
        lines.append("- `n/a`")
    for item in suspicious[:50]:
        lines.append(
            f"- `#{item['id']}` {item['title']}: "
            f"current={json.dumps(item['current'], ensure_ascii=False)} -> "
            f"new={json.dumps(item['new'], ensure_ascii=False)}"
        )

    lines.extend(["", "## Parse Failures", ""])
    if not parse_failures:
        lines.append("- `n/a`")
    for failure in parse_failures[:50]:
        lines.append(
            f"- `#{failure.get('id')}` {failure.get('title')}: `{failure.get('error')}`"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    commit = bool(args.commit)
    mode = "commit" if commit else "dry-run"

    updates, parse_failures = load_updates(input_path)
    ids = [update.id for update in updates]
    try:
        current_by_id = load_current_sqlalchemy(args.database_url, ids)
        connection_note = "SQLAlchemy"
        apply_func = lambda update: apply_update_sqlalchemy(args.database_url, update)
    except SQLAlchemyError as exc:
        print(
            "SQLAlchemy connection failed, falling back to docker compose psql: "
            f"{exc.__class__.__name__}"
        )
        current_by_id = load_current_docker(ids)
        connection_note = "docker compose psql"
        apply_func = apply_update_docker

    results: list[dict[str, Any]] = []
    for update in updates:
        try:
            current = current_by_id.get(update.id)
            if current is None:
                raise ValueError("recipe_not_found")
            current_values = values_current(current)
            new_values = values_for(update)
            status = "skipped" if current_values == new_values else "updated"
            if commit and status == "updated":
                apply_func(update)
            results.append(
                {
                    "id": update.id,
                    "title": current.title or update.title,
                    "status": status,
                    "current": current_values,
                    "new": new_values,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "id": update.id,
                    "title": update.title,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                    "current": None,
                    "new": values_for(update),
                }
            )

    report = build_report(
        mode=mode,
        input_path=input_path,
        connection_note=connection_note,
        results=results,
        parse_failures=parse_failures,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    updated = sum(item["status"] == "updated" for item in results)
    skipped = sum(item["status"] == "skipped" for item in results)
    failed = sum(item["status"] == "failed" for item in results) + len(parse_failures)
    print(f"Mode: {mode}")
    print(f"Connection: {connection_note}")
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Report written to: {report_path}")


if __name__ == "__main__":
    main()
