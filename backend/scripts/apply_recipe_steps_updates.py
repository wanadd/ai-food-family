#!/usr/bin/env python3
"""Safely apply recipe steps updates.

Default mode is dry-run. Use --commit to update only the recipes.steps field.

Usage:
    python backend/scripts/apply_recipe_steps_updates.py --dry-run
    python backend/scripts/apply_recipe_steps_updates.py --commit
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
DEFAULT_INPUT_PATH = ROOT / "exports" / "placeholder_recipe_steps_update_16.json"
DEFAULT_REPORT_PATH = ROOT / "reports" / "recipe_steps_apply_report.md"
ALLOWED_SOURCES = {
    "steps_enrichment_v1",
    "steps_enrichment_holiday_kids_v1",
}


@dataclass(frozen=True)
class StepsUpdate:
    id: int
    title: str
    steps: list[str]
    source: str


@dataclass(frozen=True)
class CurrentRecipe:
    id: int
    title: str
    steps: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply recipe steps updates")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to recipe steps update JSON array",
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
        help="Actually update recipes.steps in the database.",
    )
    return parser.parse_args()


def normalize_steps(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("steps_is_not_list")
    steps = [str(step or "").strip() for step in value]
    steps = [step for step in steps if step]
    if len(steps) < 5:
        raise ValueError("steps_count_less_than_5")
    return steps


def parse_update_record(raw: Any, index: int) -> StepsUpdate:
    if not isinstance(raw, dict):
        raise ValueError(f"record_{index}_is_not_object")
    try:
        recipe_id = int(raw["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid_id") from exc
    source = str(raw.get("source") or "").strip()
    if source not in ALLOWED_SOURCES:
        raise ValueError("invalid_source")
    return StepsUpdate(
        id=recipe_id,
        title=str(raw.get("title") or "").strip(),
        steps=normalize_steps(raw.get("steps")),
        source=source,
    )


def load_updates(path: Path) -> tuple[list[StepsUpdate], list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as handle:
        raw_updates = json.load(handle)
    if not isinstance(raw_updates, list):
        raise SystemExit("Input must be a JSON array")
    updates: list[StepsUpdate] = []
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
    steps = row.get("steps")
    return CurrentRecipe(
        id=int(row["id"]),
        title=str(row.get("title") or ""),
        steps=steps if isinstance(steps, list) else [],
    )


def load_current_sqlalchemy(database_url: str, ids: list[int]) -> dict[int, CurrentRecipe]:
    if not ids:
        return {}
    engine = create_engine(database_url)
    query = text(
        """
        SELECT id, title, steps
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
            SELECT id, title, steps
            FROM recipes
            WHERE id IN ({id_list})
            ORDER BY id
        ) AS t;
        """
    return {int(row["id"]): row_to_current(row) for row in docker_psql_json(sql)}


def apply_update_sqlalchemy(database_url: str, update: StepsUpdate) -> None:
    engine = create_engine(database_url)
    query = text(
        """
        UPDATE recipes
        SET steps = CAST(:steps AS jsonb)
        WHERE id = :id
        """
    )
    with engine.begin() as conn:
        conn.execute(query, {"id": update.id, "steps": json.dumps(update.steps, ensure_ascii=False)})


def apply_update_docker(update: StepsUpdate) -> None:
    sql = """
        UPDATE recipes
        SET steps = $json$%s$json$::jsonb
        WHERE id = %s;
        """ % (json.dumps(update.steps, ensure_ascii=False), update.id)
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


def build_report(
    mode: str,
    input_path: Path,
    connection_note: str,
    results: list[dict[str, Any]],
    parse_failures: list[dict[str, Any]],
) -> str:
    updated = sum(item["status"] == "updated" for item in results)
    would_update = sum(item["status"] == "would_update" for item in results)
    skipped = sum(item["status"] == "skipped" for item in results)
    failed = sum(item["status"] == "failed" for item in results) + len(parse_failures)
    lines = [
        "# Recipe Steps Apply Report",
        "",
        "Scope: safe apply pipeline for recipe steps updates. Only `recipes.steps` is eligible for update. Dry-run mode does not write to the database.",
        "",
        "## Summary",
        "",
        f"- Mode: `{mode}`",
        f"- Read/apply connection: `{connection_note}`",
        f"- Input: `{input_path}`",
        f"- Would update: `{would_update}`",
        f"- Updated: `{updated}`",
        f"- Skipped: `{skipped}`",
        f"- Failed: `{failed}`",
        "",
        "## Changes",
        "",
    ]
    for item in results:
        if item["status"] == "failed":
            lines.append(
                f"- `#{item.get('id')}` {item.get('title')}: failed `{item.get('error')}`"
            )
            continue
        lines.append(
            f"- `#{item['id']}` {item['title']}: `{item['status']}` "
            f"current_steps={len(item['current_steps'])} -> new_steps={len(item['new_steps'])}"
        )
    lines.extend(["", "## Parse Failures", ""])
    if not parse_failures:
        lines.append("- `n/a`")
    for failure in parse_failures[:50]:
        lines.append(
            f"- `#{failure.get('id')}` {failure.get('title')}: `{failure.get('error')}`"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
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
            if update.steps == current.steps:
                status = "skipped"
            else:
                status = "updated" if commit else "would_update"
                if commit:
                    apply_func(update)
            results.append(
                {
                    "id": update.id,
                    "title": current.title or update.title,
                    "status": status,
                    "current_steps": current.steps,
                    "new_steps": update.steps,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "id": update.id,
                    "title": update.title,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                    "current_steps": None,
                    "new_steps": update.steps,
                }
            )

    report = build_report(mode, input_path, connection_note, results, parse_failures)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    would_update = sum(item["status"] == "would_update" for item in results)
    updated = sum(item["status"] == "updated" for item in results)
    skipped = sum(item["status"] == "skipped" for item in results)
    failed = sum(item["status"] == "failed" for item in results) + len(parse_failures)
    print(f"Mode: {mode}")
    print(f"Connection: {connection_note}")
    if commit:
        print(f"Updated: {updated}")
    else:
        print(f"Would update: {would_update}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Report written to: {report_path}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
