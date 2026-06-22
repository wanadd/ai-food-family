"""Read-only backup scope dry-run for future Gold V3 existing recipe upgrades."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from dry_run_gold_v3_existing_recipe_upgrades import EXPECTED_UPGRADE_IDS  # noqa: E402


REPORT_MD = ROOT / "reports" / "SPRINT_1_3G_GOLD_V3_BACKUP_DRY_RUN.md"
REPORT_JSON = ROOT / "reports" / "SPRINT_1_3G_GOLD_V3_BACKUP_DRY_RUN.json"
MANIFEST_SCHEMA = ROOT / "data" / "recipe_v2" / "gold_v3_upgrade_backup_manifest_schema.json"
SOURCE_MARKERS = ("source_url", "original_url", "http://", "https://", "http", "povarenok", "поваренок")
RECIPE_FIELDS = (
    "id",
    "title",
    "display_title",
    "normalized_title",
    "description",
    "source_type",
    "meal_type",
    "category",
    "tags",
    "calories_per_serving",
    "protein_g",
    "fat_g",
    "carbs_g",
    "hero_image_url",
    "image_url",
    "thumbnail_url",
    "created_at",
    "updated_at",
)
RELATION_TABLE_CANDIDATES = (
    "recipe_favorites",
    "recipe_history",
    "meal_checkins",
    "meal_consumption_logs",
    "recipe_explanations",
)
RELATION_HINTS = ("meal_plan", "planned_meal", "menu", "shopping")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def has_source_leakage(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    return any(marker in text for marker in SOURCE_MARKERS)


def public_columns(columns: list[str]) -> list[str]:
    return [
        column
        for column in columns
        if not any(marker in column.lower() for marker in SOURCE_MARKERS)
    ]


def safe_db_error(exc: Exception) -> str:
    return f"db_connection_unavailable:{type(exc).__name__}"


def row_counts(conn: Any, table_name: str, planned_ids: list[int]) -> tuple[int, dict[str, int]]:
    from sqlalchemy import text

    rows = conn.execute(
        text(f"select recipe_id, count(*) as count from {table_name} where recipe_id = any(:ids) group by recipe_id"),
        {"ids": planned_ids},
    ).mappings().all()
    by_id = {str(row["recipe_id"]): int(row["count"]) for row in rows}
    return sum(by_id.values()), by_id


def inspect_relation_table(conn: Any, inspector: Any, table_name: str, planned_ids: list[int]) -> dict[str, Any]:
    if table_name not in set(inspector.get_table_names()):
        return {
            "table_exists": False,
            "recipe_id_column_detected": False,
            "hits_by_recipe_id": {},
            "backup_required": False,
            "mutation_policy": "preserve untouched; no delete; no update",
        }
    columns = [column["name"] for column in inspector.get_columns(table_name)]
    recipe_id_column_detected = "recipe_id" in columns
    hits_by_recipe_id: dict[str, int] = {}
    if recipe_id_column_detected:
        _total, hits_by_recipe_id = row_counts(conn, table_name, planned_ids)
    return {
        "table_exists": True,
        "recipe_id_column_detected": recipe_id_column_detected,
        "columns_detected": public_columns(columns),
        "hits_by_recipe_id": hits_by_recipe_id,
        "backup_required": bool(hits_by_recipe_id),
        "mutation_policy": "preserve untouched; no delete; no update",
    }


def inspect_db(planned_ids: list[int], database_url: str | None = None) -> dict[str, Any]:
    database_url = database_url or os.getenv("DATABASE_URL") or "postgresql://aifood:aifood@localhost:5432/aifood"
    try:
        from sqlalchemy import create_engine, inspect, text
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"db_available": False, "reason": f"sqlalchemy_unavailable:{type(exc).__name__}"}

    try:
        engine = create_engine(database_url, future=True)
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = set(inspector.get_table_names())
            if "recipes" not in tables:
                return {"db_available": False, "reason": "recipes table not found"}

            recipes_total = int(conn.execute(text("select count(*) from recipes")).scalar_one())
            current_max_id = int(conn.execute(text("select coalesce(max(id), 0) from recipes")).scalar_one())
            recipe_columns = [column["name"] for column in inspector.get_columns("recipes")]
            existing_recipe_fields = [field for field in RECIPE_FIELDS if field in recipe_columns]
            recipe_rows = conn.execute(
                text("select id from recipes where id = any(:ids)"),
                {"ids": planned_ids},
            ).mappings().all()
            recipe_ids_found = sorted(int(row["id"]) for row in recipe_rows)

            child_tables = {}
            for table_name in ("recipe_ingredients", "recipe_steps"):
                if table_name in tables:
                    columns = [column["name"] for column in inspector.get_columns(table_name)]
                    if "recipe_id" in columns:
                        total, by_id = row_counts(conn, table_name, planned_ids)
                    else:
                        total, by_id = 0, {}
                    child_tables[table_name] = {
                        "table_exists": True,
                        "columns_detected": public_columns(columns),
                        "row_count_total": total,
                        "row_count_by_recipe_id": by_id,
                        "backup_required": True,
                    }
                else:
                    child_tables[table_name] = {
                        "table_exists": False,
                        "columns_detected": [],
                        "row_count_total": 0,
                        "row_count_by_recipe_id": {},
                        "backup_required": True,
                    }

            relation_tables = {}
            relation_names = set(RELATION_TABLE_CANDIDATES)
            relation_names.update(
                table_name
                for table_name in tables
                if any(hint in table_name for hint in RELATION_HINTS)
            )
            for table_name in sorted(relation_names):
                relation_tables[table_name] = inspect_relation_table(conn, inspector, table_name, planned_ids)

        return {
            "db_available": True,
            "recipes_total": recipes_total,
            "current_max_id": current_max_id,
            "planned_recipe_ids": planned_ids,
            "recipe_ids_found": recipe_ids_found,
                "missing_recipe_ids": [recipe_id for recipe_id in planned_ids if recipe_id not in recipe_ids_found],
            "recipes": {
                "table_exists": True,
                "columns_detected": public_columns(recipe_columns),
                "backup_fields": existing_recipe_fields,
                "row_count": len(recipe_ids_found),
                "backup_required": True,
            },
            "child_tables": child_tables,
            "relation_tables": relation_tables,
        }
    except Exception as exc:
        return {"db_available": False, "reason": safe_db_error(exc)}


def backup_path_design() -> dict[str, Any]:
    return {
        "server_future_path": "/var/www/ai-food-family/backups/gold_v3_upgrade_<timestamp>/",
        "local_future_path": "C:\\Projects\\ai-food-family\\backups\\gold_v3_upgrade_<timestamp>\\",
        "required_future_files": [
            "MANIFEST.md",
            "manifest.json",
            "recipes.jsonl",
            "recipe_ingredients.jsonl",
            "recipe_steps.jsonl",
            "relation_tables/*.jsonl",
            "recipe-images.tar.gz if images exist for planned IDs",
            "rollback_manifest.json",
            "verification_report.md",
        ],
        "created_in_this_sprint": False,
    }


def build_report(db_state: dict[str, Any] | None = None, write_reports: bool = True) -> dict[str, Any]:
    db_state = db_state if db_state is not None else inspect_db(EXPECTED_UPGRADE_IDS)
    blockers = []
    if not db_state.get("db_available"):
        blockers.append("db_unavailable")
    if db_state.get("missing_recipe_ids"):
        blockers.append("planned_recipe_ids_missing")
    report = {
        "generated_at": now(),
        "read_only": True,
        "apply": False,
        "db_writes": 0,
        "planned_recipe_ids": EXPECTED_UPGRADE_IDS,
        "planned_recipe_id_count": len(EXPECTED_UPGRADE_IDS),
        "db_available": bool(db_state.get("db_available")),
        "db": db_state,
        "recipes_rows": (db_state.get("recipes") or {}).get("row_count"),
        "ingredient_rows": ((db_state.get("child_tables") or {}).get("recipe_ingredients") or {}).get("row_count_total"),
        "step_rows": ((db_state.get("child_tables") or {}).get("recipe_steps") or {}).get("row_count_total"),
        "backup_path_design": backup_path_design(),
        "backup_manifest_schema": str(MANIFEST_SCHEMA.relative_to(ROOT)),
        "blockers": blockers,
        "recommendation": "ready_for_future_real_backup_artifact_sprint" if not blockers else "fix_backup_dry_run_blockers",
    }
    if has_source_leakage(report):
        raise RuntimeError("backup dry-run report contains source leakage")
    if write_reports:
        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        REPORT_MD.write_text(render(report), encoding="utf-8")
    return report


def render(report: dict[str, Any]) -> str:
    db = report["db"]
    lines = [
        "# Sprint 1.3G Gold V3 Backup Dry-Run",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Read-only: `{report['read_only']}`",
        f"apply: `{report['apply']}`",
        f"db_writes: `{report['db_writes']}`",
        f"db_available: `{report['db_available']}`",
        f"planned_recipe_id_count: `{report['planned_recipe_id_count']}`",
        f"recipes_rows: `{report['recipes_rows']}`",
        f"ingredient_rows: `{report['ingredient_rows']}`",
        f"step_rows: `{report['step_rows']}`",
        f"blockers: `{report['blockers']}`",
        f"recommendation: `{report['recommendation']}`",
        "",
        "## Main Recipe Rows",
        "",
        f"backup_required: `{(db.get('recipes') or {}).get('backup_required')}`",
        f"fields: `{(db.get('recipes') or {}).get('backup_fields')}`",
        "",
        "## Child Rows",
        "",
    ]
    for table_name, table in (db.get("child_tables") or {}).items():
        lines.append(f"- {table_name}: rows=`{table.get('row_count_total')}`, backup_required=`{table.get('backup_required')}`")
    lines.extend(["", "## Relation Tables", ""])
    for table_name, table in (db.get("relation_tables") or {}).items():
        lines.append(
            f"- {table_name}: exists=`{table.get('table_exists')}`, recipe_id_column=`{table.get('recipe_id_column_detected')}`, "
            f"hits=`{sum((table.get('hits_by_recipe_id') or {}).values())}`, backup_required=`{table.get('backup_required')}`, "
            f"policy=`{table.get('mutation_policy')}`"
        )
    lines.extend(["", "## Backup Artifact Path Design", ""])
    lines.append(f"server_future_path: `{report['backup_path_design']['server_future_path']}`")
    lines.append(f"local_future_path: `{report['backup_path_design']['local_future_path']}`")
    lines.extend(f"- {item}" for item in report["backup_path_design"]["required_future_files"])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.apply:
        print("Apply is intentionally disabled in Sprint 1.3G. This sprint is backup/rollback dry-run only.", file=sys.stderr)
        return 2
    report = build_report()
    print(f"Wrote {REPORT_MD}")
    return 0 if report["planned_recipe_id_count"] == 30 else 1


if __name__ == "__main__":
    raise SystemExit(main())
