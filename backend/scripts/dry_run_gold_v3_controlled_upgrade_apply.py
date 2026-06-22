"""Dry-run only gate for a future controlled Gold V3 upgrade apply."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from dry_run_gold_v3_existing_recipe_upgrades import (  # noqa: E402
    EXPECTED_ID_BY_CANDIDATE_INDEX,
    EXPECTED_UPGRADE_IDS,
)
import dry_run_gold_v3_upgrade_rollback as rollback_dry_run  # noqa: E402
import verify_gold_v3_upgrade_backup_artifacts as backup_verify  # noqa: E402


INPUT = ROOT / "data" / "recipe_v2" / "gold_recipes_30_repaired_candidate.jsonl"
REPORT_MD = ROOT / "reports" / "SPRINT_1_3I_GOLD_V3_CONTROLLED_UPGRADE_APPLY_DRY_RUN.md"
REPORT_JSON = ROOT / "reports" / "SPRINT_1_3I_GOLD_V3_CONTROLLED_UPGRADE_APPLY_DRY_RUN.json"
EXPECTED_RECIPES_TOTAL = 263
EXPECTED_MAX_RECIPE_ID = 265
SOURCE_MARKERS = ("source_url", "original_url", "http://", "https://", "http", "povarenok", "поваренок")
DRIFT_FIELDS = ("title", "display_title", "normalized_title")
PRESERVE_FIELDS = [
    "id",
    "created_at",
    "image_urls",
    "user_relations",
    "favorites",
    "history",
    "menu_references",
]
UPDATE_RECIPE_FIELDS = [
    "title",
    "display_title",
    "normalized_title",
    "description",
    "meal_type",
    "category",
    "tags",
    "nutrition",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def has_source_leakage(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    return any(marker in text for marker in SOURCE_MARKERS)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_records(path: Path = INPUT) -> list[dict[str, Any]]:
    return load_jsonl(path)


def candidate_by_recipe_id(records: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for record in records:
        index = int(record.get("candidate_index") or 0)
        recipe_id = EXPECTED_ID_BY_CANDIDATE_INDEX.get(index)
        if recipe_id is not None:
            result[recipe_id] = record
    return result


def backup_status(backup_path: Path | None) -> dict[str, Any]:
    if backup_path is None:
        return {
            "backup_path_required": True,
            "backup_path": None,
            "exists": False,
            "manifest_parsed": False,
            "rollback_manifest_parsed": False,
            "recipes_count": 0,
            "recipe_ingredients_count": 0,
            "recipe_steps_count": 0,
            "recipe_ids": [],
            "recipe_ids_ok": False,
            "verify_ok": False,
            "rollback_dry_run_possible": False,
            "blockers": ["backup_path_missing"],
        }

    blockers: list[str] = []
    backup_path = backup_path.resolve()
    if not backup_path.exists():
        return {
            "backup_path_required": True,
            "backup_path": str(backup_path),
            "exists": False,
            "manifest_parsed": False,
            "rollback_manifest_parsed": False,
            "recipes_count": 0,
            "recipe_ingredients_count": 0,
            "recipe_steps_count": 0,
            "recipe_ids": [],
            "recipe_ids_ok": False,
            "verify_ok": False,
            "rollback_dry_run_possible": False,
            "blockers": ["backup_missing"],
        }

    manifest_path = backup_path / "manifest.json"
    rollback_manifest_path = backup_path / "rollback_manifest.json"
    recipes_path = backup_path / "recipes.jsonl"
    ingredients_path = backup_path / "recipe_ingredients.jsonl"
    steps_path = backup_path / "recipe_steps.jsonl"

    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    rollback_manifest = read_json(rollback_manifest_path) if rollback_manifest_path.exists() else {}
    recipes = load_jsonl(recipes_path) if recipes_path.exists() else []
    ingredients = load_jsonl(ingredients_path) if ingredients_path.exists() else []
    steps = load_jsonl(steps_path) if steps_path.exists() else []
    recipe_ids = sorted(int(row["id"]) for row in recipes if row.get("id") is not None)

    expected_ingredient_count = int(
        ((manifest.get("tables") or {}).get("recipe_ingredients") or {}).get("row_count")
        or (rollback_manifest.get("db_counts") or {}).get("recipe_ingredients")
        or 123
    )
    expected_step_count = int(
        ((manifest.get("tables") or {}).get("recipe_steps") or {}).get("row_count")
        or (rollback_manifest.get("db_counts") or {}).get("recipe_steps")
        or 58
    )

    if not manifest:
        blockers.append("manifest_missing_or_invalid")
    if not rollback_manifest:
        blockers.append("rollback_manifest_missing_or_invalid")
    if len(recipes) != 30:
        blockers.append("recipes_count_not_30")
    if len(ingredients) != expected_ingredient_count:
        blockers.append("recipe_ingredients_count_mismatch")
    if len(steps) != expected_step_count:
        blockers.append("recipe_steps_count_mismatch")
    if recipe_ids != EXPECTED_UPGRADE_IDS:
        blockers.append("recipe_ids_mismatch")

    verify_report = backup_verify.verify(backup_path, write_reports=False)
    rollback_report = rollback_dry_run.build_report(
        future_backup_path=backup_path,
        db_state={"db_available": True, "relation_check_available": True},
        write_reports=False,
    )
    if not verify_report.get("ok"):
        blockers.append("backup_verify_failed")
    if rollback_report.get("blockers"):
        blockers.append("rollback_dry_run_with_backup_failed")

    return {
        "backup_path_required": True,
        "backup_path": str(backup_path),
        "exists": True,
        "manifest_parsed": bool(manifest),
        "rollback_manifest_parsed": bool(rollback_manifest),
        "manifest_backup_id": manifest.get("backup_id"),
        "rollback_manifest_upgrade_apply_allowed": rollback_manifest.get("upgrade_apply_allowed"),
        "recipes_count": len(recipes),
        "recipe_ingredients_count": len(ingredients),
        "recipe_steps_count": len(steps),
        "expected_recipe_ingredients_count": expected_ingredient_count,
        "expected_recipe_steps_count": expected_step_count,
        "recipe_ids": recipe_ids,
        "recipe_ids_ok": recipe_ids == EXPECTED_UPGRADE_IDS,
        "verify_ok": bool(verify_report.get("ok")),
        "verify_blockers": verify_report.get("blockers") or [],
        "rollback_dry_run_possible": not rollback_report.get("blockers"),
        "rollback_dry_run_blockers": rollback_report.get("blockers") or [],
        "blockers": blockers,
    }


def backup_rows(backup_path: Path | None) -> dict[str, Any]:
    if backup_path is None or not backup_path.exists():
        return {"recipes": {}, "ingredients_count_by_recipe_id": {}, "steps_count_by_recipe_id": {}}
    recipes = {int(row["id"]): row for row in load_jsonl(backup_path / "recipes.jsonl")}
    ingredients = load_jsonl(backup_path / "recipe_ingredients.jsonl")
    steps = load_jsonl(backup_path / "recipe_steps.jsonl")
    return {
        "recipes": recipes,
        "ingredients_count_by_recipe_id": count_by_recipe_id(ingredients),
        "steps_count_by_recipe_id": count_by_recipe_id(steps),
    }


def count_by_recipe_id(rows: list[dict[str, Any]]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for row in rows:
        recipe_id = row.get("recipe_id")
        if recipe_id is not None:
            counts[int(recipe_id)] = counts.get(int(recipe_id), 0) + 1
    return counts


def connect_db(database_url: str | None = None):
    from sqlalchemy import create_engine

    database_url = database_url or os.getenv("DATABASE_URL") or "postgresql://aifood:aifood@localhost:5432/aifood"
    return create_engine(database_url, future=True)


def inspect_db_state(planned_ids: list[int] | None = None, database_url: str | None = None) -> dict[str, Any]:
    planned_ids = planned_ids or EXPECTED_UPGRADE_IDS
    try:
        from sqlalchemy import inspect, text
    except Exception as exc:  # pragma: no cover - depends on local env
        return {"db_available": False, "reason": f"sqlalchemy_unavailable:{type(exc).__name__}"}

    try:
        engine = connect_db(database_url)
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = set(inspector.get_table_names())
            if "recipes" not in tables:
                return {"db_available": False, "reason": "recipes_table_missing"}
            recipes_total = int(conn.execute(text("select count(*) from recipes")).scalar_one())
            current_max_id = int(conn.execute(text("select coalesce(max(id), 0) from recipes")).scalar_one())
            recipe_rows = [
                dict(row)
                for row in conn.execute(
                    text("select * from recipes where id = any(:ids) order by id"),
                    {"ids": planned_ids},
                ).mappings().all()
            ]
            ingredient_counts = child_counts(conn, inspector, "recipe_ingredients", planned_ids)
            step_counts = child_counts(conn, inspector, "recipe_steps", planned_ids)
            relation = relation_safety(conn, inspector, planned_ids)
    except Exception as exc:
        return {"db_available": False, "reason": f"db_connection_unavailable:{type(exc).__name__}"}

    public_rows = {
        int(row["id"]): public_recipe_row(row, ingredient_counts, step_counts)
        for row in recipe_rows
    }
    existing_ids = sorted(public_rows)
    return {
        "db_available": True,
        "recipes_total": recipes_total,
        "current_max_id": current_max_id,
        "planned_recipe_ids": planned_ids,
        "recipes_rows_for_planned_ids": len(public_rows),
        "existing_ids_found": existing_ids,
        "missing_planned_ids": [recipe_id for recipe_id in planned_ids if recipe_id not in public_rows],
        "recipes_by_id": public_rows,
        "recipe_ingredients_count": sum(ingredient_counts.values()),
        "recipe_steps_count": sum(step_counts.values()),
        "ingredient_counts_by_recipe_id": ingredient_counts,
        "step_counts_by_recipe_id": step_counts,
        "relation_safety": relation,
    }


def public_recipe_row(row: dict[str, Any], ingredient_counts: dict[int, int], step_counts: dict[int, int]) -> dict[str, Any]:
    recipe_id = int(row["id"])
    return {
        "id": recipe_id,
        "title": row.get("title"),
        "display_title": row.get("display_title"),
        "normalized_title": row.get("normalized_title"),
        "meal_type": row.get("meal_type"),
        "category": row.get("category"),
        "source_type": row.get("source_type"),
        "has_images": bool(row.get("hero_image_url") or row.get("image_url") or row.get("thumbnail_url")),
        "ingredient_count": ingredient_counts.get(recipe_id, 0),
        "step_count": step_counts.get(recipe_id, 0),
    }


def child_counts(conn: Any, inspector: Any, table_name: str, planned_ids: list[int]) -> dict[int, int]:
    from sqlalchemy import text

    if table_name not in set(inspector.get_table_names()):
        return {}
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if "recipe_id" not in columns:
        return {}
    rows = conn.execute(
        text(f"select recipe_id, count(*) as count from {table_name} where recipe_id = any(:ids) group by recipe_id"),
        {"ids": planned_ids},
    ).mappings().all()
    return {int(row["recipe_id"]): int(row["count"]) for row in rows}


def relation_safety(conn: Any, inspector: Any, planned_ids: list[int]) -> dict[str, Any]:
    tables = set(inspector.get_table_names())
    relation_tables: dict[str, dict[str, Any]] = {}
    table_hints = ("favorite", "history", "meal", "plan", "menu", "shopping", "checkin", "consumption", "explanation")
    for table_name in sorted(tables):
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if "recipe_id" not in columns:
            continue
        if table_name in {"recipe_ingredients", "recipe_steps"} or not any(hint in table_name for hint in table_hints):
            continue
        counts = child_counts(conn, inspector, table_name, planned_ids)
        relation_tables[table_name] = {
            "rows": sum(counts.values()),
            "policy": "preserve_untouched",
            "backup_required": bool(sum(counts.values())),
        }
    return summarize_relation_tables(relation_tables)


def summarize_relation_tables(relation_tables: dict[str, dict[str, Any]]) -> dict[str, Any]:
    def hit(*hints: str) -> bool:
        return any(meta.get("rows", 0) > 0 and any(hint in table for hint in hints) for table, meta in relation_tables.items())

    return {
        "relation_check_available": True,
        "relation_tables": relation_tables,
        "recipe_explanations_preserve_only": (relation_tables.get("recipe_explanations") or {}).get("policy") == "preserve_untouched",
        "recipe_explanations_hits": int((relation_tables.get("recipe_explanations") or {}).get("rows", 0)),
        "favorite_hits": hit("favorite"),
        "history_hits": hit("history"),
        "menu_or_planned_meal_hits": hit("meal", "plan", "menu"),
        "shopping_hits": hit("shopping"),
        "relation_policy": "preserve_untouched",
    }


def drift_report(db_state: dict[str, Any], backups: dict[str, Any]) -> dict[str, Any]:
    if not db_state.get("db_available"):
        return {"drift_detected": True, "drift_rows": [], "reason": "db_unavailable"}
    current_rows = db_state.get("recipes_by_id") or {}
    backup_recipe_rows = backups.get("recipes") or {}
    drift_rows = []
    for recipe_id in EXPECTED_UPGRADE_IDS:
        current = current_rows.get(recipe_id)
        backup = backup_recipe_rows.get(recipe_id)
        if not current or not backup:
            drift_rows.append({"recipe_id": recipe_id, "fields": ["row_missing"]})
            continue
        fields = []
        for field in DRIFT_FIELDS:
            if current.get(field) != backup.get(field):
                fields.append({"field": field, "backup": backup.get(field), "current": current.get(field)})
        if fields:
            drift_rows.append({"recipe_id": recipe_id, "fields": fields})
    return {"drift_detected": bool(drift_rows), "drift_rows": drift_rows}


def build_operation_cards(
    records_by_recipe_id: dict[int, dict[str, Any]],
    db_state: dict[str, Any],
    backups: dict[str, Any],
) -> list[dict[str, Any]]:
    current_rows = db_state.get("recipes_by_id") or {}
    backup_recipe_rows = backups.get("recipes") or {}
    cards = []
    for recipe_id in EXPECTED_UPGRADE_IDS:
        candidate = records_by_recipe_id.get(recipe_id, {})
        current = current_rows.get(recipe_id, {})
        backup = backup_recipe_rows.get(recipe_id, {})
        cards.append(
            {
                "recipe_id": recipe_id,
                "operation": "upgrade_existing_recipe",
                "db_writes_planned_future": True,
                "db_writes_executed_now": False,
                "preserve": PRESERVE_FIELDS,
                "update_recipe_fields": UPDATE_RECIPE_FIELDS,
                "replace_child_rows_future": ["recipe_ingredients", "recipe_steps"],
                "relation_policy": "preserve_untouched",
                "rollback_available": bool(backup),
                "safe_for_future_apply": bool(current and backup and candidate),
                "current_title": current.get("title"),
                "backup_title": backup.get("title"),
                "candidate_title": candidate.get("title"),
                "current_child_rows": {
                    "recipe_ingredients": current.get("ingredient_count"),
                    "recipe_steps": current.get("step_count"),
                },
                "future_child_rows": {
                    "recipe_ingredients": len(candidate.get("ingredients") or []),
                    "recipe_steps": len(candidate.get("steps") or []),
                },
                "fields_preserved_from_db": ["id", "created_at", "hero_image_url", "image_url", "thumbnail_url"],
                "preview_only_not_executable": True,
            }
        )
    return cards


def future_apply_gate(blockers: list[str]) -> dict[str, Any]:
    return {
        "real_apply_available": False,
        "apply_command_supported": False,
        "future_apply_blocked": bool(blockers),
        "future_apply_blockers": blockers,
        "allowed_only_if": [
            "backup artifacts verified",
            "rollback dry-run with backup passed",
            "controlled apply dry-run passed",
            "DB drift check passed",
            "relation safety passed",
            "operator explicitly starts a separate future sprint",
            "script version implements explicit --apply only in that later sprint",
            "pre-apply DB no-mutation baseline is recorded immediately before apply",
        ],
        "recommendation": "ready_for_controlled_upgrade_apply_sprint" if not blockers else "fix_controlled_apply_dry_run_blockers",
    }


def build_report(
    *,
    backup_path: Path | None = None,
    db_state: dict[str, Any] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    write_reports: bool = True,
) -> dict[str, Any]:
    candidates = candidates if candidates is not None else candidate_records()
    records_by_recipe_id = candidate_by_recipe_id(candidates)
    backup = backup_status(backup_path)
    backups = backup_rows(backup_path)
    db = db_state if db_state is not None else inspect_db_state(EXPECTED_UPGRADE_IDS)
    drift = drift_report(db, backups)
    operation_cards = build_operation_cards(records_by_recipe_id, db, backups)

    blockers: list[str] = []
    blockers.extend(backup.get("blockers") or [])
    if not db.get("db_available"):
        blockers.append("db_unavailable")
    if db.get("db_available"):
        if db.get("recipes_total") != EXPECTED_RECIPES_TOTAL:
            blockers.append("recipes_total_drift")
        if db.get("current_max_id") != EXPECTED_MAX_RECIPE_ID:
            blockers.append("max_recipe_id_drift")
        if db.get("missing_planned_ids"):
            blockers.append("planned_recipe_ids_missing")
        if db.get("recipes_rows_for_planned_ids") != 30:
            blockers.append("planned_recipe_rows_not_30")
    if drift.get("drift_detected"):
        blockers.append("drift_detected")
    relation = db.get("relation_safety") or {"relation_check_available": False, "relation_policy": "preserve_untouched"}
    if not relation.get("relation_check_available"):
        blockers.append("relation_check_unavailable")

    gate = future_apply_gate(sorted(set(blockers)))
    report = {
        "generated_at": now(),
        "read_only": True,
        "dry_run": True,
        "apply": False,
        "db_writes": 0,
        "real_apply_available": gate["real_apply_available"],
        "apply_command_supported": gate["apply_command_supported"],
        "input": str(INPUT.relative_to(ROOT)),
        "backup": backup,
        "db_available": bool(db.get("db_available")),
        "db": db,
        "db_expectations": {
            "recipes_total": EXPECTED_RECIPES_TOTAL,
            "max_recipe_id": EXPECTED_MAX_RECIPE_ID,
        },
        "planned_recipe_ids": EXPECTED_UPGRADE_IDS,
        "operation_cards": operation_cards,
        "operation_card_count": len(operation_cards),
        "import_new_recipe": 0,
        "simulated_insert_ids": [],
        "drift": drift,
        "drift_detected": bool(drift.get("drift_detected")),
        "relation_safety": relation,
        "future_apply_gate": gate,
        "future_apply_blocked": gate["future_apply_blocked"],
        "future_apply_blockers": gate["future_apply_blockers"],
        "recommendation": gate["recommendation"],
    }
    if has_source_leakage(report):
        raise RuntimeError("controlled upgrade apply dry-run report contains source leakage")
    if write_reports:
        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        REPORT_MD.write_text(render(report), encoding="utf-8")
    return report


def render(report: dict[str, Any]) -> str:
    backup = report["backup"]
    db = report["db"]
    gate = report["future_apply_gate"]
    lines = [
        "# Sprint 1.3I Gold V3 Controlled Upgrade Apply Dry-Run",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Read-only: `{report['read_only']}`",
        f"apply: `{report['apply']}`",
        f"db_writes: `{report['db_writes']}`",
        f"db_available: `{report['db_available']}`",
        f"recipes_total: `{db.get('recipes_total')}`",
        f"current_max_id: `{db.get('current_max_id')}`",
        f"operation_cards: `{report['operation_card_count']}`",
        f"drift_detected: `{report['drift_detected']}`",
        f"import_new_recipe: `{report['import_new_recipe']}`",
        f"simulated_insert_ids: `{report['simulated_insert_ids']}`",
        f"real_apply_available: `{report['real_apply_available']}`",
        f"apply_command_supported: `{report['apply_command_supported']}`",
        f"future_apply_blocked: `{report['future_apply_blocked']}`",
        f"future_apply_blockers: `{report['future_apply_blockers']}`",
        f"recommendation: `{report['recommendation']}`",
        "",
        "## Backup Preconditions",
        "",
        f"backup_path: `{backup.get('backup_path')}`",
        f"exists: `{backup.get('exists')}`",
        f"manifest_parsed: `{backup.get('manifest_parsed')}`",
        f"rollback_manifest_parsed: `{backup.get('rollback_manifest_parsed')}`",
        f"recipes_count: `{backup.get('recipes_count')}`",
        f"recipe_ingredients_count: `{backup.get('recipe_ingredients_count')}`",
        f"recipe_steps_count: `{backup.get('recipe_steps_count')}`",
        f"recipe_ids_ok: `{backup.get('recipe_ids_ok')}`",
        f"verify_ok: `{backup.get('verify_ok')}`",
        f"rollback_dry_run_possible: `{backup.get('rollback_dry_run_possible')}`",
        f"backup_blockers: `{backup.get('blockers')}`",
        "",
        "## Drift Check",
        "",
        f"drift_detected: `{report['drift_detected']}`",
    ]
    for row in report["drift"].get("drift_rows") or []:
        lines.append(f"- recipe `{row['recipe_id']}` fields: `{row['fields']}`")
    lines.extend(
        [
            "",
            "## Operation Cards",
            "",
        ]
    )
    for card in report["operation_cards"]:
        lines.append(
            f"- recipe `{card['recipe_id']}`: `{card['operation']}`, "
            f"current=`{card['current_title']}`, candidate=`{card['candidate_title']}`, "
            f"writes_now=`{card['db_writes_executed_now']}`, rollback=`{card['rollback_available']}`"
        )
    relation = report["relation_safety"]
    lines.extend(
        [
            "",
            "## Relation Safety",
            "",
            f"relation_check_available: `{relation.get('relation_check_available')}`",
            f"relation_policy: `{relation.get('relation_policy')}`",
            f"recipe_explanations_hits: `{relation.get('recipe_explanations_hits')}`",
            f"recipe_explanations_preserve_only: `{relation.get('recipe_explanations_preserve_only')}`",
            f"favorite_hits: `{relation.get('favorite_hits')}`",
            f"history_hits: `{relation.get('history_hits')}`",
            f"menu_or_planned_meal_hits: `{relation.get('menu_or_planned_meal_hits')}`",
            f"shopping_hits: `{relation.get('shopping_hits')}`",
            "",
            "## Future Apply Gate",
            "",
            f"real_apply_available: `{gate['real_apply_available']}`",
            f"apply_command_supported: `{gate['apply_command_supported']}`",
            f"future_apply_blocked: `{gate['future_apply_blocked']}`",
            f"recommendation: `{gate['recommendation']}`",
        ]
    )
    lines.extend(f"- {item}" for item in gate["allowed_only_if"])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--backup-path")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.apply:
        print(
            "Apply is intentionally disabled in Sprint 1.3I. This sprint is controlled apply dry-run only.",
            file=sys.stderr,
        )
        return 2
    report = build_report(backup_path=Path(args.backup_path) if args.backup_path else None)
    print(f"Wrote {REPORT_MD}")
    return 0 if report["operation_card_count"] == 30 else 1


if __name__ == "__main__":
    raise SystemExit(main())
