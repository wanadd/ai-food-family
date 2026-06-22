"""Guarded controlled apply for Gold V3 upgrades of existing recipes.

Dry-run is the default. Real apply is implemented for a later manual operator
step and is guarded by backup/drift checks, a matching plan id, and an explicit
environment variable.
"""

from __future__ import annotations

import argparse
import hashlib
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

from dry_run_gold_v3_controlled_upgrade_apply import (  # noqa: E402
    EXPECTED_MAX_RECIPE_ID,
    EXPECTED_RECIPES_TOTAL,
    EXPECTED_UPGRADE_IDS,
    INPUT,
    backup_status,
    build_report as build_controlled_dry_run,
    candidate_by_recipe_id,
    candidate_records,
    has_source_leakage,
    inspect_db_state,
)


REPORT_DRY_MD = ROOT / "reports" / "SPRINT_1_3J_GOLD_V3_CONTROLLED_APPLY_DRY_RUN.md"
REPORT_DRY_JSON = ROOT / "reports" / "SPRINT_1_3J_GOLD_V3_CONTROLLED_APPLY_DRY_RUN.json"
REPORT_APPLY_MD = ROOT / "reports" / "SPRINT_1_3J_GOLD_V3_CONTROLLED_APPLY_RESULT.md"
REPORT_APPLY_JSON = ROOT / "reports" / "SPRINT_1_3J_GOLD_V3_CONTROLLED_APPLY_RESULT.json"
ALLOW_ENV = "PLANAM_ALLOW_GOLD_V3_UPGRADE_APPLY"
ALLOW_ENV_VALUE = "YES"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def plan_id_for(controlled_report: dict[str, Any]) -> str:
    payload = {
        "backup_id": (controlled_report.get("backup") or {}).get("manifest_backup_id"),
        "backup_path": (controlled_report.get("backup") or {}).get("backup_path"),
        "planned_recipe_ids": controlled_report.get("planned_recipe_ids"),
        "operation_cards": [
            {
                "recipe_id": card.get("recipe_id"),
                "operation": card.get("operation"),
                "candidate_title": card.get("candidate_title"),
                "future_child_rows": card.get("future_child_rows"),
            }
            for card in controlled_report.get("operation_cards") or []
        ],
    }
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return f"gold-v3-upgrade-{digest[:16]}"


def build_apply_preview(controlled_report: dict[str, Any]) -> dict[str, Any]:
    cards = controlled_report.get("operation_cards") or []
    expected_ingredient_replacements = sum(
        int((card.get("future_child_rows") or {}).get("recipe_ingredients") or 0) for card in cards
    )
    expected_step_replacements = sum(
        int((card.get("future_child_rows") or {}).get("recipe_steps") or 0) for card in cards
    )
    return {
        "expected_recipe_updates": len(cards),
        "expected_ingredient_replacements": expected_ingredient_replacements,
        "expected_step_replacements": expected_step_replacements,
        "preserve": [
            "recipe ids",
            "created_at",
            "existing image urls unless candidate has approved image urls",
            "recipe_explanations",
            "recipe_favorites",
            "recipe_history",
            "menu/planned meal references",
            "shopping references",
        ],
        "replace": ["recipe fields", "recipe_ingredients rows for planned ids", "recipe_steps rows for planned ids"],
        "transaction_steps": [
            "acquire advisory lock",
            "re-run backup verification",
            "re-run rollback manifest verification",
            "re-run drift check",
            "re-run relation safety check",
            "update existing recipe rows",
            "replace child rows only for planned ids",
            "verify recipe count and max id",
            "commit only if every check passes",
        ],
    }


def relation_safety_passed(controlled_report: dict[str, Any]) -> bool:
    relation = controlled_report.get("relation_safety") or {}
    return bool(relation.get("relation_check_available")) and relation.get("relation_policy") == "preserve_untouched"


def apply_guard_blockers(
    controlled_report: dict[str, Any],
    *,
    backup_path: Path | None,
    confirm_plan_id: str | None,
    env: dict[str, str] | None = None,
) -> list[str]:
    env = env if env is not None else os.environ
    blockers: list[str] = []
    backup = controlled_report.get("backup") or {}
    if backup_path is None:
        blockers.append("backup_path_missing")
    if not backup.get("exists"):
        blockers.append("backup_missing")
    if not backup.get("rollback_manifest_parsed"):
        blockers.append("rollback_manifest_missing")
    if not backup.get("verify_ok"):
        blockers.append("backup_verification_failed")
    if not backup.get("rollback_dry_run_possible"):
        blockers.append("rollback_dry_run_failed")
    if controlled_report.get("drift_detected"):
        blockers.append("drift_detected")
    if not relation_safety_passed(controlled_report):
        blockers.append("relation_safety_failed")
    if controlled_report.get("planned_recipe_ids") != EXPECTED_UPGRADE_IDS:
        blockers.append("planned_id_set_mismatch")
    if len(controlled_report.get("operation_cards") or []) != 30:
        blockers.append("operation_cards_not_30")
    if controlled_report.get("import_new_recipe") != 0:
        blockers.append("import_new_recipe_present")
    if controlled_report.get("simulated_insert_ids"):
        blockers.append("simulated_insert_ids_present")
    if controlled_report.get("db", {}).get("recipes_total") != EXPECTED_RECIPES_TOTAL:
        blockers.append("recipes_total_drift")
    if controlled_report.get("db", {}).get("current_max_id") != EXPECTED_MAX_RECIPE_ID:
        blockers.append("max_recipe_id_drift")

    generated_plan_id = controlled_report.get("plan_id") or plan_id_for(controlled_report)
    if not confirm_plan_id:
        blockers.append("confirm_plan_id_missing")
    elif confirm_plan_id != generated_plan_id:
        blockers.append("confirm_plan_id_mismatch")
    if env.get(ALLOW_ENV) != ALLOW_ENV_VALUE:
        blockers.append("apply_env_var_missing")
    return sorted(set(blockers))


def build_report(
    *,
    backup_path: Path | None,
    apply: bool = False,
    confirm_plan_id: str | None = None,
    db_state: dict[str, Any] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    env: dict[str, str] | None = None,
    write_reports: bool = True,
) -> dict[str, Any]:
    candidates = candidates if candidates is not None else candidate_records()
    controlled = build_controlled_dry_run(
        backup_path=backup_path,
        db_state=db_state,
        candidates=candidates,
        write_reports=False,
    )
    plan_id = plan_id_for(controlled)
    controlled["plan_id"] = plan_id
    preview = build_apply_preview(controlled)
    guard_blockers = apply_guard_blockers(
        controlled,
        backup_path=backup_path,
        confirm_plan_id=confirm_plan_id,
        env=env,
    )
    report = {
        "generated_at": now(),
        "mode": "apply" if apply else "dry_run",
        "dry_run": not apply,
        "apply": bool(apply),
        "apply_supported": True,
        "apply_executed": False,
        "db_writes": 0,
        "plan_id": plan_id,
        "confirm_plan_id": confirm_plan_id,
        "input": str(INPUT.relative_to(ROOT)),
        "backup_path": str(backup_path) if backup_path else None,
        "backup_verified": bool((controlled.get("backup") or {}).get("verify_ok")),
        "rollback_manifest_verified": bool((controlled.get("backup") or {}).get("rollback_manifest_parsed")),
        "rollback_dry_run_possible": bool((controlled.get("backup") or {}).get("rollback_dry_run_possible")),
        "db_available": bool(controlled.get("db_available")),
        "drift_detected": bool(controlled.get("drift_detected")),
        "relation_safety_passed": relation_safety_passed(controlled),
        "operation_cards": controlled.get("operation_cards") or [],
        "operation_card_count": len(controlled.get("operation_cards") or []),
        "planned_recipe_ids": controlled.get("planned_recipe_ids") or [],
        "import_new_recipe": controlled.get("import_new_recipe"),
        "simulated_insert_ids": controlled.get("simulated_insert_ids") or [],
        "apply_preview": preview,
        "safety_guards": {
            "env_var_required": f"{ALLOW_ENV}={ALLOW_ENV_VALUE}",
            "confirm_plan_id_required": True,
            "guard_blockers": guard_blockers,
        },
        "controlled_dry_run_summary": {
            "recipes_total": (controlled.get("db") or {}).get("recipes_total"),
            "current_max_id": (controlled.get("db") or {}).get("current_max_id"),
            "future_apply_blocked": controlled.get("future_apply_blocked"),
            "future_apply_blockers": controlled.get("future_apply_blockers") or [],
            "recommendation": controlled.get("recommendation"),
        },
        "recommendation": "ready_for_manual_operator_controlled_apply" if not guard_blockers else "fix_controlled_apply_guard_blockers",
    }
    if has_source_leakage(report):
        raise RuntimeError("controlled apply report contains source leakage")
    if write_reports:
        write_report(report, apply=False)
    return report


def candidate_payload(record: dict[str, Any], current_recipe: dict[str, Any] | None = None) -> dict[str, Any]:
    current_recipe = current_recipe or {}
    nutrition = record.get("nutrition_per_serving") or {}
    tags = sorted(set(list(record.get("tags") or []) + ["gold_v3", "recipe_schema_v3", "upgraded_from_legacy"]))
    return {
        "title": record.get("title"),
        "display_title": record.get("display_title") or record.get("title"),
        "normalized_title": record.get("normalized_title"),
        "description": record.get("description") or "",
        "meal_type": record.get("meal_type"),
        "category": record.get("category") or "main",
        "difficulty": record.get("difficulty") or "easy",
        "cooking_time_minutes": record.get("cook_time_minutes") or record.get("cooking_time_minutes") or 30,
        "prep_time_minutes": record.get("prep_time_minutes") or 0,
        "servings": record.get("servings") or 4,
        "calories_per_serving": nutrition.get("kcal"),
        "protein_g": nutrition.get("protein_g"),
        "fat_g": nutrition.get("fat_g"),
        "carbs_g": nutrition.get("carbs_g"),
        "fiber_g": nutrition.get("fiber_g"),
        "sugar_g": nutrition.get("sugar_g"),
        "nutrition_kcal_per_serving": nutrition.get("kcal"),
        "nutrition_protein_per_serving": nutrition.get("protein_g"),
        "nutrition_fat_per_serving": nutrition.get("fat_g"),
        "nutrition_carbs_per_serving": nutrition.get("carbs_g"),
        "nutrition_servings": float(record.get("servings") or 4),
        "nutrition_source": "gold_v3_controlled_upgrade",
        "nutrition_confidence": "estimated",
        "nutrition_coverage_json": {
            "fiber_g": nutrition.get("fiber_g"),
            "salt_g": nutrition.get("salt_g"),
            "sugar_g": nutrition.get("sugar_g"),
        },
        "source_type": "import",
        "source_url": None,
        "is_active": True,
        "diets": record.get("diet_tags") or [],
        "tags": tags,
        "ingredients": [
            {
                "name": ingredient.get("display_name") or ingredient.get("name"),
                "amount": ingredient.get("display_amount") or display_amount(ingredient),
                "is_optional": bool(ingredient.get("is_optional")),
            }
            for ingredient in record.get("ingredients") or []
        ],
        "steps": [step.get("text") if isinstance(step, dict) else str(step) for step in record.get("steps") or []],
        "hero_image_url": current_recipe.get("hero_image_url"),
        "image_url": current_recipe.get("image_url"),
        "thumbnail_url": current_recipe.get("thumbnail_url"),
    }


def display_amount(ingredient: dict[str, Any]) -> str:
    amount = ingredient.get("amount")
    unit = ingredient.get("unit")
    if amount is None:
        return str(unit or "").strip()
    return f"{amount} {unit or ''}".strip()


def ingredient_payloads(record: dict[str, Any]) -> list[dict[str, Any]]:
    payloads = []
    for ingredient in record.get("ingredients") or []:
        payloads.append(
            {
                "name": ingredient.get("display_name") or ingredient.get("name"),
                "quantity": str(ingredient.get("amount") if ingredient.get("amount") is not None else "1"),
                "unit": ingredient.get("unit") or "шт",
                "category": ingredient.get("shopping_category_slug") or ingredient.get("pantry_category_slug") or "other",
                "is_optional": bool(ingredient.get("is_optional")),
                "quantity_text": ingredient.get("display_amount") or display_amount(ingredient),
                "is_to_taste": False,
                "needs_review": False,
            }
        )
    return payloads


def step_payloads(record: dict[str, Any]) -> list[dict[str, Any]]:
    payloads = []
    for index, step in enumerate(record.get("steps") or [], start=1):
        if isinstance(step, dict):
            text_value = step.get("text")
            step_number = step.get("step_number") or index
        else:
            text_value = str(step)
            step_number = index
        payloads.append({"step_number": int(step_number), "text": str(text_value or "").strip()})
    return [payload for payload in payloads if payload["text"]]


def filter_columns(payload: dict[str, Any], columns: set[str]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key in columns}


def execute_update(conn: Any, text: Any, table: str, payload: dict[str, Any], key_name: str, key_value: Any) -> None:
    columns = sorted(payload)
    assignments = ", ".join(f"{column} = :{column}" for column in columns)
    params = dict(payload)
    params[key_name] = key_value
    conn.execute(text(f"update {table} set {assignments} where {key_name} = :{key_name}"), params)


def execute_insert(conn: Any, text: Any, table: str, payload: dict[str, Any]) -> None:
    columns = sorted(payload)
    conn.execute(
        text(f"insert into {table} ({', '.join(columns)}) values ({', '.join(':' + column for column in columns)})"),
        payload,
    )


def apply_transaction(
    *,
    conn: Any,
    text: Any,
    inspector: Any,
    candidates: list[dict[str, Any]],
    controlled_report: dict[str, Any],
) -> dict[str, Any]:
    recipe_columns = {column["name"] for column in inspector.get_columns("recipes")}
    ingredient_columns = {column["name"] for column in inspector.get_columns("recipe_ingredients")}
    step_columns = {column["name"] for column in inspector.get_columns("recipe_steps")}
    records_by_recipe_id = candidate_by_recipe_id(candidates)
    current_rows = (controlled_report.get("db") or {}).get("recipes_by_id") or {}

    conn.execute(text("select pg_advisory_xact_lock(1303001)"))
    recipes_updated = 0
    ingredients_inserted = 0
    steps_inserted = 0
    for recipe_id in EXPECTED_UPGRADE_IDS:
        record = records_by_recipe_id[recipe_id]
        recipe_payload = candidate_payload(record, current_rows.get(recipe_id))
        recipe_payload.pop("hero_image_url", None) if "hero_image_url" not in recipe_columns else None
        recipe_payload.pop("image_url", None) if "image_url" not in recipe_columns else None
        recipe_payload.pop("thumbnail_url", None) if "thumbnail_url" not in recipe_columns else None
        execute_update(conn, text, "recipes", filter_columns(recipe_payload, recipe_columns - {"id", "created_at"}), "id", recipe_id)
        conn.execute(text("delete from recipe_ingredients where recipe_id = :recipe_id"), {"recipe_id": recipe_id})
        conn.execute(text("delete from recipe_steps where recipe_id = :recipe_id"), {"recipe_id": recipe_id})
        for ingredient in ingredient_payloads(record):
            payload = filter_columns({"recipe_id": recipe_id, **ingredient}, ingredient_columns)
            execute_insert(conn, text, "recipe_ingredients", payload)
            ingredients_inserted += 1
        for step in step_payloads(record):
            payload = filter_columns({"recipe_id": recipe_id, **step}, step_columns)
            execute_insert(conn, text, "recipe_steps", payload)
            steps_inserted += 1
        recipes_updated += 1
    return {
        "recipes_updated": recipes_updated,
        "ingredients_inserted": ingredients_inserted,
        "steps_inserted": steps_inserted,
        "recipe_ids_preserved": EXPECTED_UPGRADE_IDS,
    }


def verify_post_apply(conn: Any, text: Any) -> dict[str, Any]:
    recipes_total = int(conn.execute(text("select count(*) from recipes")).scalar_one())
    max_recipe_id = int(conn.execute(text("select coalesce(max(id), 0) from recipes")).scalar_one())
    planned_count = int(
        conn.execute(text("select count(*) from recipes where id = any(:ids)"), {"ids": EXPECTED_UPGRADE_IDS}).scalar_one()
    )
    ingredient_recipe_count = int(
        conn.execute(
            text("select count(distinct recipe_id) from recipe_ingredients where recipe_id = any(:ids)"),
            {"ids": EXPECTED_UPGRADE_IDS},
        ).scalar_one()
    )
    step_recipe_count = int(
        conn.execute(
            text("select count(distinct recipe_id) from recipe_steps where recipe_id = any(:ids)"),
            {"ids": EXPECTED_UPGRADE_IDS},
        ).scalar_one()
    )
    ok = (
        recipes_total == EXPECTED_RECIPES_TOTAL
        and max_recipe_id == EXPECTED_MAX_RECIPE_ID
        and planned_count == 30
        and ingredient_recipe_count == 30
        and step_recipe_count == 30
    )
    return {
        "ok": ok,
        "recipes_total": recipes_total,
        "max_recipe_id": max_recipe_id,
        "planned_count": planned_count,
        "ingredient_recipe_count": ingredient_recipe_count,
        "step_recipe_count": step_recipe_count,
    }


def execute_apply(
    *,
    backup_path: Path,
    confirm_plan_id: str | None,
    candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    from sqlalchemy import create_engine, inspect, text

    candidates = candidates if candidates is not None else candidate_records()
    pre_report = build_report(
        backup_path=backup_path,
        apply=True,
        confirm_plan_id=confirm_plan_id,
        candidates=candidates,
        write_reports=False,
    )
    guard_blockers = pre_report["safety_guards"]["guard_blockers"]
    if guard_blockers:
        pre_report["apply_executed"] = False
        pre_report["apply_refused"] = True
        pre_report["db_writes"] = 0
        pre_report["recommendation"] = "apply_refused_by_safety_guards"
        write_report(pre_report, apply=True)
        return pre_report

    database_url = os.getenv("DATABASE_URL") or "postgresql://aifood:aifood@localhost:5432/aifood"
    engine = create_engine(database_url, future=True)
    try:
        with engine.begin() as conn:
            inspector = inspect(conn)
            live_state = inspect_db_state(EXPECTED_UPGRADE_IDS, database_url=database_url)
            live_report = build_report(
                backup_path=backup_path,
                apply=True,
                confirm_plan_id=confirm_plan_id,
                db_state=live_state,
                candidates=candidates,
                write_reports=False,
            )
            live_blockers = live_report["safety_guards"]["guard_blockers"]
            if live_blockers:
                raise RuntimeError("apply guard failed inside transaction: " + ", ".join(live_blockers))
            result = apply_transaction(conn=conn, text=text, inspector=inspector, candidates=candidates, controlled_report=live_report)
            post = verify_post_apply(conn, text)
            if not post["ok"]:
                raise RuntimeError("post apply verification failed")
            live_report.update(
                {
                    "apply_executed": True,
                    "db_writes": result["recipes_updated"] + result["ingredients_inserted"] + result["steps_inserted"],
                    "apply_result": result,
                    "post_apply_verification": post,
                    "recommendation": "controlled_apply_completed_verify_prod",
                }
            )
            write_report(live_report, apply=True)
            return live_report
    except Exception as exc:
        failure = dict(pre_report)
        failure.update(
            {
                "apply_executed": False,
                "apply_failed": True,
                "db_writes": 0,
                "error": f"{type(exc).__name__}: {exc}",
                "recommendation": "controlled_apply_failed_transaction_rolled_back",
            }
        )
        write_report(failure, apply=True)
        return failure


def write_report(report: dict[str, Any], *, apply: bool) -> None:
    json_path = REPORT_APPLY_JSON if apply else REPORT_DRY_JSON
    md_path = REPORT_APPLY_MD if apply else REPORT_DRY_MD
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render(report), encoding="utf-8")


def render(report: dict[str, Any]) -> str:
    preview = report.get("apply_preview") or {}
    guards = report.get("safety_guards") or {}
    lines = [
        "# Sprint 1.3J Gold V3 Controlled Apply Dry-Run" if not report.get("apply") else "# Sprint 1.3J Gold V3 Controlled Apply Result",
        "",
        f"Generated: `{report['generated_at']}`",
        f"mode: `{report['mode']}`",
        f"plan_id: `{report['plan_id']}`",
        f"backup_path: `{report['backup_path']}`",
        f"backup_verified: `{report['backup_verified']}`",
        f"rollback_manifest_verified: `{report['rollback_manifest_verified']}`",
        f"rollback_dry_run_possible: `{report['rollback_dry_run_possible']}`",
        f"db_available: `{report['db_available']}`",
        f"drift_detected: `{report['drift_detected']}`",
        f"relation_safety_passed: `{report['relation_safety_passed']}`",
        f"operation_cards: `{report['operation_card_count']}`",
        f"apply_supported: `{report['apply_supported']}`",
        f"apply_executed: `{report['apply_executed']}`",
        f"db_writes: `{report['db_writes']}`",
        f"guard_blockers: `{guards.get('guard_blockers')}`",
        f"recommendation: `{report['recommendation']}`",
        "",
        "## Apply Preview",
        "",
        f"expected_recipe_updates: `{preview.get('expected_recipe_updates')}`",
        f"expected_ingredient_replacements: `{preview.get('expected_ingredient_replacements')}`",
        f"expected_step_replacements: `{preview.get('expected_step_replacements')}`",
        f"planned_recipe_ids: `{report.get('planned_recipe_ids')}`",
        f"import_new_recipe: `{report.get('import_new_recipe')}`",
        f"simulated_insert_ids: `{report.get('simulated_insert_ids')}`",
        "",
        "## Safety Guards",
        "",
        f"env_var_required: `{guards.get('env_var_required')}`",
        f"confirm_plan_id_required: `{guards.get('confirm_plan_id_required')}`",
        "",
        "## Operation Cards",
        "",
    ]
    for card in report.get("operation_cards") or []:
        lines.append(
            f"- recipe `{card.get('recipe_id')}`: current=`{card.get('current_title')}`, "
            f"candidate=`{card.get('candidate_title')}`, writes_now=`{card.get('db_writes_executed_now')}`"
        )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-path")
    parser.add_argument("--confirm-plan-id")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    backup_path = Path(args.backup_path) if args.backup_path else None
    if args.apply:
        if backup_path is None:
            print("Apply refused: --backup-path is required.", file=sys.stderr)
            return 2
        result = execute_apply(backup_path=backup_path, confirm_plan_id=args.confirm_plan_id)
        if result.get("apply_refused") or result.get("apply_failed"):
            blockers = (result.get("safety_guards") or {}).get("guard_blockers") or [result.get("error")]
            print("Apply refused: " + ", ".join(str(item) for item in blockers), file=sys.stderr)
            return 2
        print(f"Wrote {REPORT_APPLY_MD}")
        return 0

    report = build_report(backup_path=backup_path, apply=False)
    write_report(report, apply=False)
    print(f"Wrote {REPORT_DRY_MD}")
    return 0 if report["operation_card_count"] == 30 else 1


if __name__ == "__main__":
    raise SystemExit(main())
