"""Dry-run/apply guarded Gold V3 nutrition corrections."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import bindparam, create_engine, inspect, text


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_gold_v3_nutrition_correction_manifest import (  # noqa: E402
    DEFAULT_MANIFEST,
    EXPECTED_IDS,
    load_manifest,
    validate_manifest,
)


DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
REPORT_MD = ROOT / "reports" / "SPRINT_1_7_NUTRITION_APPLY_DRY_RUN.md"
REPORT_JSON = ROOT / "reports" / "SPRINT_1_7_NUTRITION_APPLY_DRY_RUN.json"
APPLY_MD = ROOT / "reports" / "SPRINT_1_7_NUTRITION_APPLY_RESULT.md"
APPLY_JSON = ROOT / "reports" / "SPRINT_1_7_NUTRITION_APPLY_RESULT.json"
ENV_GUARD = "PLANAM_ALLOW_GOLD_V3_NUTRITION_APPLY"

TARGET_FIELDS = [
    "calories_per_serving",
    "protein_g",
    "fat_g",
    "carbs_g",
    "nutrition_kcal_total",
    "nutrition_protein_total",
    "nutrition_fat_total",
    "nutrition_carbs_total",
    "nutrition_kcal_per_serving",
    "nutrition_protein_per_serving",
    "nutrition_fat_per_serving",
    "nutrition_carbs_per_serving",
    "nutrition_servings",
    "nutrition_serving_size_text",
    "nutrition_confidence",
    "nutrition_coverage_json",
    "nutrition_source",
    "nutrition_needs_review",
    "nutrition_review_reason",
    "recipe_yield_amount",
    "recipe_yield_unit",
    "serving_size_amount",
    "serving_size_unit",
    "estimated_servings",
    "yield_type",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def plan_id_for(data: dict[str, Any]) -> str:
    payload = {
        "schema_version": data.get("schema_version"),
        "recipe_ids": EXPECTED_IDS,
        "target_fields": TARGET_FIELDS,
        "values": [
            {
                "recipe_id": item["recipe_id"],
                "nutrition_per_serving": item["nutrition_per_serving"],
                "nutrition_cooked_total": item["nutrition_cooked_total"],
                "servings": item["servings"],
                "serving_weight_g": item["serving_weight_g"],
                "nutrition_confidence": item["nutrition_confidence"],
                "nutrition_basis": item["nutrition_basis"],
            }
            for item in sorted(data.get("recipes") or [], key=lambda x: int(x["recipe_id"]))
        ],
    }
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return f"gold-v3-nutrition-{digest}"


def values_for_recipe(item: dict[str, Any]) -> dict[str, Any]:
    per = item["nutrition_per_serving"]
    total = item["nutrition_cooked_total"]
    coverage = {
        "basis": item["nutrition_basis"],
        "confidence": item["nutrition_confidence"],
        "serving_weight_g": item["serving_weight_g"],
        "cooking_method": item["cooking_method"],
        "yield_notes": item["yield_notes"],
        "ingredients_basis": item.get("ingredients_basis") or [],
        "rationale": item.get("rationale"),
        "source": "gold_v3_nutrition_correction_manifest.v1",
    }
    return {
        "calories_per_serving": per["kcal"],
        "protein_g": per["protein_g"],
        "fat_g": per["fat_g"],
        "carbs_g": per["carbs_g"],
        "nutrition_kcal_total": total["kcal"],
        "nutrition_protein_total": total["protein_g"],
        "nutrition_fat_total": total["fat_g"],
        "nutrition_carbs_total": total["carbs_g"],
        "nutrition_kcal_per_serving": per["kcal"],
        "nutrition_protein_per_serving": per["protein_g"],
        "nutrition_fat_per_serving": per["fat_g"],
        "nutrition_carbs_per_serving": per["carbs_g"],
        "nutrition_servings": item["servings"],
        "nutrition_serving_size_text": f"{item['serving_weight_g']} г готового блюда",
        "nutrition_confidence": item["nutrition_confidence"],
        "nutrition_coverage_json": coverage,
        "nutrition_source": "gold_v3_correction_manifest",
        "nutrition_needs_review": False,
        "nutrition_review_reason": None,
        "recipe_yield_amount": round(float(item["serving_weight_g"]) * float(item["servings"]), 1),
        "recipe_yield_unit": "g",
        "serving_size_amount": item["serving_weight_g"],
        "serving_size_unit": "g",
        "estimated_servings": item["servings"],
        "yield_type": "cooked_weight",
    }


def engine_for(database_url: str | None = None):
    return create_engine(database_url or os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL), pool_pre_ping=True)


def existing_columns(engine: Any) -> set[str]:
    return {col["name"] for col in inspect(engine).get_columns("recipes")}


def fetch_existing(conn: Any, ids: list[int]) -> dict[int, dict[str, Any]]:
    query = text(f"SELECT id, {', '.join(TARGET_FIELDS)} FROM recipes WHERE id IN :ids ORDER BY id").bindparams(
        bindparam("ids", expanding=True)
    )
    rows = conn.execute(query, {"ids": ids})
    return {int(row._mapping["id"]): dict(row._mapping) for row in rows}


def build_report(manifest_path: Path, *, apply: bool = False, confirm_plan_id: str | None = None, database_url: str | None = None) -> dict[str, Any]:
    data = load_manifest(manifest_path)
    validation = validate_manifest(data)
    plan_id = plan_id_for(data)
    guard_blockers: list[str] = []
    unsafe: list[str] = []
    if not validation["ok"]:
        guard_blockers.append("manifest_invalid")
    ids = [int(item["recipe_id"]) for item in data.get("recipes") or []]
    if ids != EXPECTED_IDS:
        guard_blockers.append("target_ids_not_exact")
    if apply:
        if os.environ.get(ENV_GUARD) != "YES":
            guard_blockers.append("env_guard_missing")
        if confirm_plan_id != plan_id:
            guard_blockers.append("confirm_plan_id_mismatch")

    engine = engine_for(database_url)
    columns = existing_columns(engine)
    missing_fields = [field for field in TARGET_FIELDS if field not in columns]
    if missing_fields:
        guard_blockers.append(f"missing_db_fields:{missing_fields}")
    selected_fields = [field for field in TARGET_FIELDS if field in columns]
    if set(selected_fields) != set(TARGET_FIELDS):
        unsafe.append("unknown_or_missing_db_fields")

    with engine.connect() as conn:
        existing = fetch_existing(conn, ids) if not missing_fields else {}
    missing_recipes = [rid for rid in ids if rid not in existing]
    if missing_recipes:
        guard_blockers.append(f"missing_recipes:{missing_recipes}")

    desired_by_id = {int(item["recipe_id"]): values_for_recipe(item) for item in data.get("recipes") or []}
    unchanged = 0
    would_update = 0
    operation_cards = []
    for rid in ids:
        current = existing.get(rid) or {}
        desired = desired_by_id.get(rid) or {}
        changed = {
            field: {"old": current.get(field), "new": desired.get(field)}
            for field in selected_fields
            if current.get(field) != desired.get(field)
        }
        if changed:
            would_update += 1
        else:
            unchanged += 1
        operation_cards.append({"recipe_id": rid, "changed_fields": sorted(changed), "changed_count": len(changed)})

    report = {
        "generated_at": now(),
        "mode": "apply" if apply else "dry-run",
        "plan_id": plan_id,
        "recipe_count": len(ids),
        "target_ids": ids,
        "changed_field_names": selected_fields,
        "db_writes": 0,
        "apply_executed": False,
        "guard_blockers": guard_blockers,
        "unsafe_operation_count": len(unsafe),
        "unsafe_operations": unsafe,
        "missing_recipe_count": len(missing_recipes),
        "missing_recipe_ids": missing_recipes,
        "unchanged_recipe_count": unchanged,
        "would_update_count": would_update,
        "rollback_manifest_path": None,
        "recommendation": "ready_for_guarded_apply" if not guard_blockers and not unsafe and would_update > 0 else "blocked",
        "field_mapping": selected_fields,
        "operation_cards": operation_cards,
    }
    if apply and not guard_blockers and not unsafe:
        report.update(apply_updates(engine, data, existing, desired_by_id, plan_id, selected_fields))
    return report


def apply_updates(engine: Any, data: dict[str, Any], existing: dict[int, dict[str, Any]], desired_by_id: dict[int, dict[str, Any]], plan_id: str, fields: list[str]) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = ROOT / "backups" / f"gold_v3_nutrition_apply_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    rollback_path = backup_dir / "rollback_manifest.json"
    rollback = {
        "created_at": now(),
        "plan_id": plan_id,
        "recipe_ids": EXPECTED_IDS,
        "fields": fields,
        "recipes": [
            {
                "recipe_id": rid,
                "previous": {field: existing[rid].get(field) for field in fields},
                "new": {field: desired_by_id[rid].get(field) for field in fields},
            }
            for rid in EXPECTED_IDS
        ],
    }
    rollback_path.write_text(json.dumps(rollback, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    is_pg = engine.dialect.name == "postgresql"
    assignments = ", ".join(
        f"{field} = CAST(:{field} AS jsonb)" if field == "nutrition_coverage_json" and is_pg else f"{field} = :{field}"
        for field in fields
    )
    db_writes = 0
    with engine.begin() as conn:
        for rid in EXPECTED_IDS:
            params = {"id": rid, **desired_by_id[rid]}
            if isinstance(params.get("nutrition_coverage_json"), dict):
                params["nutrition_coverage_json"] = json.dumps(params["nutrition_coverage_json"], ensure_ascii=False)
            result = conn.execute(text(f"UPDATE recipes SET {assignments} WHERE id = :id"), params)
            db_writes += int(result.rowcount or 0)
    return {
        "db_writes": db_writes,
        "apply_executed": True,
        "rollback_manifest_path": str(rollback_path),
        "recommendation": "apply_completed",
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.7 Gold V3 Nutrition Apply",
        "",
        f"Generated: `{report['generated_at']}`",
        f"mode: `{report['mode']}`",
        f"plan_id: `{report['plan_id']}`",
        f"recipe_count: `{report['recipe_count']}`",
        f"changed_field_names: `{report['changed_field_names']}`",
        f"db_writes: `{report['db_writes']}`",
        f"apply_executed: `{report['apply_executed']}`",
        f"guard_blockers: `{report['guard_blockers']}`",
        f"unsafe_operation_count: `{report['unsafe_operation_count']}`",
        f"missing_recipe_count: `{report['missing_recipe_count']}`",
        f"unchanged_recipe_count: `{report['unchanged_recipe_count']}`",
        f"would_update_count: `{report['would_update_count']}`",
        f"rollback_manifest_path: `{report['rollback_manifest_path']}`",
        f"recommendation: `{report['recommendation']}`",
    ]
    return "\n".join(lines) + "\n"


def write_report(report: dict[str, Any]) -> None:
    md = APPLY_MD if report["apply_executed"] else REPORT_MD
    js = APPLY_JSON if report["apply_executed"] else REPORT_JSON
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(render(report), encoding="utf-8")
    js.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-plan-id")
    parser.add_argument("--database-url")
    args = parser.parse_args()
    report = build_report(args.manifest, apply=args.apply, confirm_plan_id=args.confirm_plan_id, database_url=args.database_url)
    write_report(report)
    for key in ("plan_id", "recipe_count", "db_writes", "apply_executed", "guard_blockers", "unsafe_operation_count", "would_update_count", "rollback_manifest_path", "recommendation"):
        print(f"{key}={report.get(key)}")
    return 0 if not report["guard_blockers"] and report["unsafe_operation_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
