"""Dry-run only model for future Gold V3 existing recipe upgrades."""

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

import plan_gold_v3_existing_recipe_upgrades as upgrade_plan  # noqa: E402


INPUT = ROOT / "data" / "recipe_v2" / "gold_recipes_30_repaired_candidate.jsonl"
MANUAL_DECISIONS = ROOT / "data" / "recipe_v2" / "gold_v3_manual_review_7_decisions.json"
REPORT_MD = ROOT / "reports" / "SPRINT_1_3F_GOLD_V3_UPGRADE_DRY_RUN.md"
REPORT_JSON = ROOT / "reports" / "SPRINT_1_3F_GOLD_V3_UPGRADE_DRY_RUN.json"
EXPECTED_UPGRADE_IDS = [
    2,
    227,
    228,
    229,
    230,
    231,
    232,
    233,
    234,
    235,
    236,
    237,
    238,
    239,
    240,
    241,
    242,
    243,
    244,
    245,
    246,
    247,
    248,
    249,
    250,
    251,
    252,
    253,
    254,
    255,
]
EXPECTED_ID_BY_CANDIDATE_INDEX = {
    1: 227,
    2: 2,
    3: 228,
    4: 229,
    5: 230,
    6: 231,
    7: 232,
    8: 233,
    9: 234,
    10: 235,
    11: 236,
    12: 237,
    13: 238,
    14: 239,
    15: 240,
    16: 241,
    17: 242,
    18: 243,
    19: 244,
    20: 245,
    21: 246,
    22: 247,
    23: 248,
    24: 249,
    25: 250,
    26: 251,
    27: 252,
    28: 253,
    29: 254,
    30: 255,
}
SOURCE_MARKERS = ("source_url", "original_url", "http://", "https://", "http", "povarenok", "поваренок")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def has_source_leakage(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    return any(marker in text for marker in SOURCE_MARKERS)


def load_jsonl(path: Path = INPUT) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def candidate_by_title(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(record.get("title") or ""): record for record in records}


def fallback_upgrade_plan(records: list[dict[str, Any]]) -> dict[str, Any]:
    actions = []
    for index, candidate in enumerate(records, start=1):
        recipe_id = EXPECTED_ID_BY_CANDIDATE_INDEX[index]
        actions.append(
            {
                "candidate_index": index,
                "candidate_title": candidate.get("title"),
                "existing_recipe_id": recipe_id,
                "existing_title": candidate.get("title"),
                "confidence": "medium",
                "reason": "Static dry-run fallback mapping used because DB-backed duplicate plan is unavailable locally.",
                "source": "static_dry_run_fallback",
                "proposed_action": "upgrade_existing_recipe",
                "fields_to_replace": [
                    "ingredients",
                    "steps",
                    "nutrition",
                    "tags",
                    "source_type_gold_v3_metadata",
                    "shopping_readiness",
                ],
                "fields_to_preserve": [
                    "id",
                    "created_at",
                    "user relations/history/favorites/menu references",
                    "existing image URLs",
                    "source metadata remains internal only",
                ],
                "preserve_existing_images": True,
                "add_tags": ["gold_v3", "recipe_schema_v3", "upgraded_from_legacy"],
                "no_new_recipe_id": True,
            }
        )
    return {
        "db_available": False,
        "total_candidates": len(records),
        "duplicate_risk_count": 30,
        "action_counts": {
            "upgrade_existing_recipe": len(actions),
            "manual_review": 0,
            "do_not_upgrade": 0,
            "import_new_recipe": 0,
        },
        "planned_existing_recipe_ids": EXPECTED_UPGRADE_IDS,
        "upgrade_actions": actions,
        "manual_review_cards": [],
        "do_not_upgrade": [],
        "import_new_recipe": [],
        "future_apply_blocked": True,
        "future_apply_blockers": ["db_duplicate_report_unavailable"],
        "recommendation": "fix_dry_run_blockers_before_apply_design",
    }


def collect_db_state(planned_ids: list[int], database_url: str | None = None) -> dict[str, Any]:
    database_url = database_url or os.getenv("DATABASE_URL") or "postgresql://aifood:aifood@localhost:5432/aifood"
    try:
        from sqlalchemy import create_engine, inspect, text
    except Exception as exc:  # pragma: no cover - depends on local env
        return {"db_available": False, "reason": f"sqlalchemy_unavailable:{exc}"}

    try:
        engine = create_engine(database_url, future=True)
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = set(inspector.get_table_names())
            if "recipes" not in tables:
                return {"db_available": False, "reason": "recipes table not found"}
            recipe_columns = {column["name"] for column in inspector.get_columns("recipes")}
            select_columns = [
                "id",
                "title",
                "display_title" if "display_title" in recipe_columns else "NULL as display_title",
                "hero_image_url" if "hero_image_url" in recipe_columns else "NULL as hero_image_url",
                "image_url" if "image_url" in recipe_columns else "NULL as image_url",
                "thumbnail_url" if "thumbnail_url" in recipe_columns else "NULL as thumbnail_url",
            ]
            recipes_total = int(conn.execute(text("select count(*) from recipes")).scalar_one())
            current_max_id = int(conn.execute(text("select coalesce(max(id), 0) from recipes")).scalar_one())
            recipe_rows = conn.execute(
                text(f"select {', '.join(select_columns)} from recipes where id = any(:ids)"),
                {"ids": planned_ids},
            ).mappings().all()

            ingredient_counts = count_child_rows(conn, inspector, "recipe_ingredients", planned_ids)
            step_counts = count_child_rows(conn, inspector, "recipe_steps", planned_ids)
            relation = relation_counts(conn, inspector, planned_ids)

        recipes_by_id = {
            int(row["id"]): {
                "current_title": row["title"],
                "current_display_title": row["display_title"],
                "hero_image_url": row["hero_image_url"],
                "image_url": row["image_url"],
                "thumbnail_url": row["thumbnail_url"],
                "ingredient_rows_before": ingredient_counts.get(int(row["id"]), 0),
                "step_rows_before": step_counts.get(int(row["id"]), 0),
            }
            for row in recipe_rows
        }
        return {
            "db_available": True,
            "recipes_total": recipes_total,
            "current_max_id": current_max_id,
            "existing_ids_found": sorted(recipes_by_id),
            "missing_planned_ids": [recipe_id for recipe_id in planned_ids if recipe_id not in recipes_by_id],
            "recipes_by_id": recipes_by_id,
            "relation_safety": relation,
        }
    except Exception as exc:
        return {"db_available": False, "reason": f"db_connection_unavailable:{type(exc).__name__}"}


def count_child_rows(conn: Any, inspector: Any, table_name: str, planned_ids: list[int]) -> dict[int, int]:
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


def relation_counts(conn: Any, inspector: Any, planned_ids: list[int]) -> dict[str, Any]:
    references: dict[str, dict[str, int]] = defaultdict(dict)
    tables_checked = []
    for table_name in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if "recipe_id" not in columns:
            continue
        if table_name in {"recipe_ingredients", "recipe_steps"} or any(
            hint in table_name for hint in ("favorite", "history", "meal", "plan", "menu", "shopping", "cooked")
        ):
            tables_checked.append(table_name)
            counts = count_child_rows(conn, inspector, table_name, planned_ids)
            for recipe_id, count in counts.items():
                references[str(recipe_id)][table_name] = count
    return {
        "relation_check_available": True,
        "tables_checked": sorted(tables_checked),
        "references_by_recipe_id": dict(references),
        "recipe_favorites_hits": relation_hit(references, ("favorite",)),
        "recipe_history_hits": relation_hit(references, ("history",)),
        "menu_or_planned_meal_hits": relation_hit(references, ("meal", "plan", "menu")),
        "shopping_hits": relation_hit(references, ("shopping",)),
    }


def relation_hit(references: dict[str, dict[str, int]], hints: tuple[str, ...]) -> bool:
    return any(any(hint in table for hint in hints) for counts in references.values() for table in counts)


def build_update_card(
    action: dict[str, Any],
    candidate: dict[str, Any],
    db_state: dict[str, Any],
) -> dict[str, Any]:
    recipe_id = int(action["existing_recipe_id"])
    current = (db_state.get("recipes_by_id") or {}).get(recipe_id, {})
    ingredients_after = len(candidate.get("ingredients") or [])
    steps_after = len(candidate.get("steps") or [])
    return {
        "existing_recipe_id": recipe_id,
        "current_title": current.get("current_title") or action.get("existing_title"),
        "candidate_title": action.get("candidate_title"),
        "action": "upgrade_existing_recipe",
        "preserve": [
            "id",
            "created_at",
            "image_urls_if_present",
            "user_relations",
            "history",
            "favorites",
            "menu_references",
        ],
        "replace": [
            "title",
            "display_title",
            "normalized_title",
            "description",
            "meal_type",
            "category",
            "tags",
            "nutrition",
            "ingredients",
            "steps",
        ],
        "image_policy": "preserve_existing_image_urls_or_null; no new image generation",
        "current_image_urls": {
            "hero_image_url": current.get("hero_image_url"),
            "image_url": current.get("image_url"),
            "thumbnail_url": current.get("thumbnail_url"),
        },
        "ingredient_rows_before": current.get("ingredient_rows_before"),
        "ingredient_rows_after": ingredients_after,
        "step_rows_before": current.get("step_rows_before"),
        "step_rows_after": steps_after,
        "preview_only": True,
        "safe_for_future_apply": bool(recipe_id in EXPECTED_UPGRADE_IDS and ingredients_after >= 3 and steps_after >= 3),
    }


def backup_design() -> dict[str, Any]:
    return {
        "backup_created_in_this_sprint": False,
        "future_apply_blocked_without_backup": True,
        "required_backup": [
            "DB dump for recipes rows for planned IDs.",
            "DB dump for recipe_ingredients rows for planned IDs.",
            "DB dump for recipe_steps rows for planned IDs.",
            "DB dump for relation tables that reference planned IDs.",
            "File backup for existing recipe images for planned IDs if present.",
            "JSON rollback manifest with old recipe fields, ingredients, steps, image URLs, timestamp, and git commit.",
        ],
    }


def rollback_design() -> dict[str, Any]:
    return {
        "rollback_executed_in_this_sprint": False,
        "required_capabilities": [
            "restore recipe fields by ID",
            "delete newly replaced ingredient/step rows",
            "restore old ingredient/step rows",
            "restore image URLs",
            "keep user relations untouched",
            "verify counts after rollback",
        ],
    }


def transaction_design() -> dict[str, Any]:
    return {
        "report_only": True,
        "executable_apply_implemented": False,
        "steps": [
            "acquire advisory lock",
            "verify DB state has not drifted",
            "backup first",
            "for each planned ID update recipe fields",
            "replace ingredient rows",
            "replace step rows",
            "preserve image URLs",
            "set gold_v3, recipe_schema_v3, upgraded_from_legacy tags",
            "verify row counts",
            "commit",
            "write report",
        ],
    }


def run_dry_run(
    *,
    report_md: Path = REPORT_MD,
    report_json: Path = REPORT_JSON,
    plan_report: dict[str, Any] | None = None,
    db_state: dict[str, Any] | None = None,
    write_reports: bool = True,
) -> dict[str, Any]:
    candidate_records = load_jsonl(INPUT)
    candidates = candidate_by_title(candidate_records)
    plan = plan_report or upgrade_plan.build_plan(write_reports=False)
    if (plan.get("action_counts") or {}).get("upgrade_existing_recipe") != 30:
        plan = fallback_upgrade_plan(candidate_records)
    planned_ids = [int(recipe_id) for recipe_id in plan.get("planned_existing_recipe_ids") or []]
    db = db_state if db_state is not None else collect_db_state(planned_ids)
    cards = [
        build_update_card(action, candidates.get(str(action.get("candidate_title")) or "", {}), db)
        for action in plan.get("upgrade_actions") or []
    ]
    action_counts = plan.get("action_counts") or {}
    planned_id_set_ok = planned_ids == EXPECTED_UPGRADE_IDS
    blockers = []
    if not db.get("db_available"):
        blockers.append("db_unavailable")
    if action_counts.get("upgrade_existing_recipe") != 30:
        blockers.append("planned_upgrade_count_not_30")
    if action_counts.get("manual_review", 0):
        blockers.append("manual_review_remaining")
    if action_counts.get("import_new_recipe", 0):
        blockers.append("import_new_recipe_present")
    if not planned_id_set_ok:
        blockers.append("planned_ids_do_not_match_expected_set")
    if (db.get("missing_planned_ids") or []):
        blockers.append("planned_ids_missing_in_db")
    report = {
        "generated_at": now(),
        "read_only": True,
        "apply": False,
        "dry_run": True,
        "db_writes": 0,
        "input": str(INPUT.relative_to(ROOT)),
        "manual_decisions": str(MANUAL_DECISIONS.relative_to(ROOT)),
        "db_available": bool(db.get("db_available")),
        "db": db,
        "recipes_total": db.get("recipes_total"),
        "current_max_id": db.get("current_max_id"),
        "planned_upgrades": len(cards),
        "manual_review": action_counts.get("manual_review", 0),
        "import_new_recipe": action_counts.get("import_new_recipe", 0),
        "planned_existing_recipe_ids": planned_ids,
        "planned_id_set_expected": EXPECTED_UPGRADE_IDS,
        "planned_id_set_ok": planned_id_set_ok,
        "no_new_ids": True,
        "simulated_insert_ids": [],
        "upgrade_cards": cards,
        "relation_safety": db.get("relation_safety") or {"relation_check_available": False},
        "backup_design": backup_design(),
        "rollback_design": rollback_design(),
        "transaction_design": transaction_design(),
        "future_apply_blocked": bool(blockers) or backup_design()["future_apply_blocked_without_backup"],
        "future_apply_blockers": blockers + ["backup_missing"],
        "recommendation": "ready_for_future_backup_and_controlled_apply_sprint" if not blockers else "fix_dry_run_blockers_before_apply_design",
    }
    if has_source_leakage(report):
        raise RuntimeError("dry-run report contains source leakage")
    if write_reports:
        report_json.parent.mkdir(parents=True, exist_ok=True)
        report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report_md.write_text(render(report), encoding="utf-8")
    return report


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3F Gold V3 Existing Recipe Upgrade Dry-Run",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Read-only: `{report['read_only']}`",
        f"apply: `{report['apply']}`",
        f"db_writes: `{report['db_writes']}`",
        f"db_available: `{report['db_available']}`",
        f"recipes_total: `{report['recipes_total']}`",
        f"current_max_id: `{report['current_max_id']}`",
        f"planned_upgrades: `{report['planned_upgrades']}`",
        f"manual_review: `{report['manual_review']}`",
        f"import_new_recipe: `{report['import_new_recipe']}`",
        f"planned_existing_recipe_ids: `{report['planned_existing_recipe_ids']}`",
        f"planned_id_set_ok: `{report['planned_id_set_ok']}`",
        f"simulated_insert_ids: `{report['simulated_insert_ids']}`",
        f"future_apply_blocked: `{report['future_apply_blocked']}`",
        f"future_apply_blockers: `{report['future_apply_blockers']}`",
        f"recommendation: `{report['recommendation']}`",
        "",
        "## Upgrade Cards",
        "",
    ]
    for card in report["upgrade_cards"]:
        lines.append(
            f"- recipe `{card['existing_recipe_id']}`: `{card['current_title']}` -> `{card['candidate_title']}`, "
            f"ingredients `{card['ingredient_rows_before']}` -> `{card['ingredient_rows_after']}`, "
            f"steps `{card['step_rows_before']}` -> `{card['step_rows_after']}`, "
            f"safe=`{card['safe_for_future_apply']}`"
        )
    relation = report["relation_safety"]
    lines.extend(
        [
            "",
            "## Relation Safety",
            "",
            f"relation_check_available: `{relation.get('relation_check_available')}`",
            f"tables_checked: `{relation.get('tables_checked')}`",
            f"recipe_favorites_hits: `{relation.get('recipe_favorites_hits')}`",
            f"recipe_history_hits: `{relation.get('recipe_history_hits')}`",
            f"menu_or_planned_meal_hits: `{relation.get('menu_or_planned_meal_hits')}`",
            f"shopping_hits: `{relation.get('shopping_hits')}`",
            "",
            "## Backup Design",
            "",
            f"backup_created_in_this_sprint: `{report['backup_design']['backup_created_in_this_sprint']}`",
            f"future_apply_blocked_without_backup: `{report['backup_design']['future_apply_blocked_without_backup']}`",
        ]
    )
    lines.extend(f"- {item}" for item in report["backup_design"]["required_backup"])
    lines.extend(
        [
            "",
            "## Rollback Design",
            "",
            f"rollback_executed_in_this_sprint: `{report['rollback_design']['rollback_executed_in_this_sprint']}`",
        ]
    )
    lines.extend(f"- {item}" for item in report["rollback_design"]["required_capabilities"])
    lines.extend(
        [
            "",
            "## Future Apply Transaction Design",
            "",
            f"report_only: `{report['transaction_design']['report_only']}`",
            f"executable_apply_implemented: `{report['transaction_design']['executable_apply_implemented']}`",
        ]
    )
    lines.extend(f"- {item}" for item in report["transaction_design"]["steps"])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.apply:
        print("Apply is intentionally disabled in Sprint 1.3F. This sprint is dry-run only.", file=sys.stderr)
        return 2
    report = run_dry_run()
    print(f"Wrote {REPORT_MD}")
    return 0 if report["planned_upgrades"] == 30 else 1


if __name__ == "__main__":
    raise SystemExit(main())
