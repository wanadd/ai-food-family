"""Guarded DB image URL update for Gold V3 upgraded recipes 2, 227-255.

Dry-run is the default. Apply requires env guard, matching plan id, and existing assets.
"""

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
API_ROOT = ROOT / "apps" / "api"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if (API_ROOT / "app").is_dir() and str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
elif (ROOT / "app").is_dir() and str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gold_v3_upgraded_30_photo_common import (  # noqa: E402
    EXPECTED_UPGRADE_IDS,
    FILE_BY_URL_FIELD,
    IMAGE_URL_FIELDS,
    MANIFEST_PATH,
    REQUIRED_FILES,
    SCRIPT_VERSION,
    expected_public_urls,
    load_manifest,
    manifest_recipe_ids,
    plan_id_for,
    recipe_manifest_by_id,
    validate_manifest_ids,
)
from validate_gold_v3_upgraded_30_images import validate as validate_assets  # noqa: E402

REPORT_DRY_JSON = ROOT / "reports" / "SPRINT_1_5_IMAGE_URL_APPLY_DRY_RUN.json"
REPORT_DRY_MD = ROOT / "reports" / "SPRINT_1_5_IMAGE_URL_APPLY_DRY_RUN.md"
REPORT_APPLY_JSON = ROOT / "reports" / "SPRINT_1_5_IMAGE_URL_APPLY_RESULT.json"
REPORT_APPLY_MD = ROOT / "reports" / "SPRINT_1_5_IMAGE_URL_APPLY_RESULT.md"
ALLOW_ENV = "PLANAM_ALLOW_GOLD_V3_IMAGE_URL_APPLY"
ALLOW_ENV_VALUE = "YES"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact_url(url: str) -> str:
    if "@" not in url or "://" not in url:
        return url
    scheme = url.split("://", 1)[0]
    return f"{scheme}://***:***@{url.split('@', 1)[1]}"


def import_sqlalchemy():
    try:
        from sqlalchemy import create_engine, text
    except Exception as exc:
        raise RuntimeError(f"sqlalchemy_unavailable:{exc}") from exc
    return create_engine, text


def inspect_db_state(database_url: str) -> dict[str, Any]:
    create_engine, text = import_sqlalchemy()
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        recipe_count = conn.execute(text("select count(*) from recipes")).scalar_one()
        max_id = conn.execute(text("select coalesce(max(id), 0) from recipes")).scalar_one()
        rows = [
            dict(row._mapping)
            for row in conn.execute(
                text(
                    """
                    SELECT id, hero_image_url, image_url, thumbnail_url
                    FROM recipes
                    WHERE id = ANY(:ids)
                    ORDER BY id
                    """
                ),
                {"ids": EXPECTED_UPGRADE_IDS},
            )
        ]
    return {
        "recipe_count": int(recipe_count),
        "max_recipe_id": int(max_id),
        "rows_by_id": {int(row["id"]): row for row in rows},
    }


def build_operation_cards(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = recipe_manifest_by_id(manifest)
    cards: list[dict[str, Any]] = []
    for recipe_id in EXPECTED_UPGRADE_IDS:
        recipe = by_id.get(recipe_id) or {}
        urls = expected_public_urls(recipe_id, recipe)
        cards.append(
            {
                "recipe_id": recipe_id,
                "title": recipe.get("display_title") or recipe.get("title") or "",
                "operation": "update_image_urls_only",
                "fields": list(IMAGE_URL_FIELDS),
                "current_urls": None,
                "target_urls": urls,
                "unsafe_operations": [],
            }
        )
    return cards


def guard_blockers(
    *,
    apply: bool,
    confirm_plan_id: str | None,
    expected_plan_id: str,
    asset_report: dict[str, Any],
    unexpected_recipe_ids: list[int] | None = None,
) -> list[str]:
    blockers: list[str] = []
    if not apply:
        return blockers
    if os.environ.get(ALLOW_ENV) != ALLOW_ENV_VALUE:
        blockers.append(f"missing_env:{ALLOW_ENV}={ALLOW_ENV_VALUE}")
    if not confirm_plan_id:
        blockers.append("missing_confirm_plan_id")
    elif confirm_plan_id != expected_plan_id:
        blockers.append("confirm_plan_id_mismatch")
    if int(asset_report.get("missing_asset_count") or 0) > 0:
        blockers.append("missing_assets")
    if int(asset_report.get("public_url_fail_count") or 0) > 0:
        blockers.append("public_url_failures")
    if unexpected_recipe_ids:
        blockers.append(f"unexpected_recipe_ids:{unexpected_recipe_ids}")
    return blockers


def build_report(
    *,
    apply: bool,
    manifest_path: Path,
    image_root: Path,
    public_base_url: str | None,
    confirm_plan_id: str | None,
    unexpected_recipe_ids: list[int] | None = None,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    manifest_errors = validate_manifest_ids(manifest)
    plan_id = plan_id_for(manifest)
    asset_report = validate_assets(
        manifest=manifest,
        image_root=image_root,
        public_base_url=public_base_url,
        public_timeout=8.0,
        strict_extra_ids=False,
    )
    cards = build_operation_cards(manifest)
    unsafe_count = sum(len(card.get("unsafe_operations") or []) for card in cards)
    blockers = list(manifest_errors)
    blockers.extend(
        guard_blockers(
            apply=apply,
            confirm_plan_id=confirm_plan_id,
            expected_plan_id=plan_id,
            asset_report=asset_report,
            unexpected_recipe_ids=unexpected_recipe_ids,
        )
    )
    database_url = os.environ.get("DATABASE_URL", "")
    db_before: dict[str, Any] | None = None
    if database_url:
        try:
            db_before = inspect_db_state(database_url)
            for card in cards:
                current = (db_before.get("rows_by_id") or {}).get(card["recipe_id"]) or {}
                card["current_urls"] = {
                    field: current.get(field) for field in IMAGE_URL_FIELDS
                }
        except Exception as exc:
            blockers.append(f"db_inspect_failed:{exc}")
    recommendation = "ready_for_guarded_apply" if apply and not blockers else "dry_run_only"
    if int(asset_report.get("missing_asset_count") or 0) > 0:
        recommendation = "produce_images_before_apply"
    if manifest_errors:
        recommendation = "fix_manifest_before_apply"
    return {
        "generated_at": now(),
        "mode": "apply" if apply else "dry-run",
        "plan_id": plan_id,
        "script_version": SCRIPT_VERSION,
        "manifest_path": str(manifest_path),
        "recipe_count": len(EXPECTED_UPGRADE_IDS),
        "expected_update_ids": EXPECTED_UPGRADE_IDS,
        "operation_cards": cards,
        "operation_card_count": len(cards),
        "db_writes": 0,
        "apply_executed": False,
        "apply_refused": bool(apply and blockers),
        "missing_asset_count": int(asset_report.get("missing_asset_count") or 0),
        "public_url_fail_count": int(asset_report.get("public_url_fail_count") or 0),
        "unsafe_operation_count": unsafe_count,
        "safety_guards": {
            "env_var_required": f"{ALLOW_ENV}={ALLOW_ENV_VALUE}",
            "confirm_plan_id_required": True,
            "guard_blockers": blockers,
        },
        "asset_validation": {
            "ok": asset_report.get("ok"),
            "complete_triplets": asset_report.get("complete_triplets"),
            "missing_asset_count": asset_report.get("missing_asset_count"),
            "public_url_fail_count": asset_report.get("public_url_fail_count"),
        },
        "database_url": redact_url(database_url),
        "db_before": db_before,
        "db_after": None,
        "import_new_recipe": False,
        "recipe_generation_run": False,
        "photo_generation_run": False,
        "recommendation": recommendation,
    }


def execute_apply(report: dict[str, Any]) -> dict[str, Any]:
    blockers = (report.get("safety_guards") or {}).get("guard_blockers") or []
    if blockers:
        report["apply_refused"] = True
        report["recommendation"] = "apply_refused"
        return report

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        report["apply_refused"] = True
        report["error"] = "DATABASE_URL missing"
        return report

    create_engine, text = import_sqlalchemy()
    engine = create_engine(database_url, pool_pre_ping=True)
    db_before = inspect_db_state(database_url)
    writes = 0
    try:
        with engine.begin() as conn:
            for card in report.get("operation_cards") or []:
                recipe_id = int(card["recipe_id"])
                if recipe_id not in EXPECTED_UPGRADE_IDS:
                    raise RuntimeError(f"unexpected_recipe_id:{recipe_id}")
                target = card.get("target_urls") or {}
                result = conn.execute(
                    text(
                        """
                        UPDATE recipes
                        SET hero_image_url = :hero_image_url,
                            image_url = :image_url,
                            thumbnail_url = :thumbnail_url,
                            updated_at = NOW()
                        WHERE id = :recipe_id
                        """
                    ),
                    {
                        "recipe_id": recipe_id,
                        "hero_image_url": target["hero_image_url"],
                        "image_url": target["image_url"],
                        "thumbnail_url": target["thumbnail_url"],
                    },
                )
                writes += int(result.rowcount or 0)
                card["db_writes_executed_now"] = int(result.rowcount or 0)
        db_after = inspect_db_state(database_url)
        report["db_writes"] = writes
        report["apply_executed"] = True
        report["apply_refused"] = False
        report["db_before"] = db_before
        report["db_after"] = db_after
        report["recipe_count_unchanged"] = db_before["recipe_count"] == db_after["recipe_count"]
        report["max_recipe_id_unchanged"] = db_before["max_recipe_id"] == db_after["max_recipe_id"]
        report["recommendation"] = "apply_completed"
        return report
    except Exception as exc:
        report["apply_executed"] = False
        report["apply_failed"] = True
        report["error"] = repr(exc)
        report["recommendation"] = "apply_failed_rolled_back"
        return report


def render(report: dict[str, Any]) -> str:
    guards = report.get("safety_guards") or {}
    lines = [
        "# Sprint 1.5 Gold V3 Image URL Apply",
        "",
        f"Generated: `{report['generated_at']}`",
        f"mode: `{report['mode']}`",
        f"plan_id: `{report['plan_id']}`",
        f"recipe_count: `{report['recipe_count']}`",
        f"missing_asset_count: `{report['missing_asset_count']}`",
        f"public_url_fail_count: `{report['public_url_fail_count']}`",
        f"unsafe_operation_count: `{report['unsafe_operation_count']}`",
        f"db_writes: `{report['db_writes']}`",
        f"apply_executed: `{report['apply_executed']}`",
        f"recommendation: `{report['recommendation']}`",
        f"guard_blockers: `{guards.get('guard_blockers')}`",
        "",
        "## Expected update IDs",
        "",
        ", ".join(str(recipe_id) for recipe_id in report.get("expected_update_ids") or []),
        "",
    ]
    return "\n".join(lines) + "\n"


def write_report(report: dict[str, Any], *, apply: bool) -> None:
    if apply:
        REPORT_APPLY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        REPORT_APPLY_MD.write_text(render(report), encoding="utf-8")
    else:
        REPORT_DRY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        REPORT_DRY_MD.write_text(render(report), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Validate and plan only (default).")
    parser.add_argument("--apply", action="store_true", help="Execute guarded DB image URL update.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--image-root", type=Path, required=True)
    parser.add_argument("--public-base-url", default=None)
    parser.add_argument("--confirm-plan-id")
    parser.add_argument("--unexpected-recipe-id", type=int, action="append", default=[])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.apply and args.dry_run:
        print("Use either --dry-run or --apply, not both.", file=sys.stderr)
        return 2
    apply = bool(args.apply)
    image_root = args.image_root.resolve()
    report = build_report(
        apply=apply,
        manifest_path=args.manifest,
        image_root=image_root,
        public_base_url=args.public_base_url,
        confirm_plan_id=args.confirm_plan_id,
        unexpected_recipe_ids=args.unexpected_recipe_id or None,
    )
    if apply:
        report = execute_apply(report)
    write_report(report, apply=apply)
    print(f"Wrote {REPORT_APPLY_MD if apply else REPORT_DRY_MD}")
    if apply and (report.get("apply_refused") or report.get("apply_failed")):
        blockers = (report.get("safety_guards") or {}).get("guard_blockers") or [report.get("error")]
        print("Apply refused: " + ", ".join(str(item) for item in blockers if item), file=sys.stderr)
        return 2
    return 0 if report.get("mode") == "dry-run" or report.get("apply_executed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
