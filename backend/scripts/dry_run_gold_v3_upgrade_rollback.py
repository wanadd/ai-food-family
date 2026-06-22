"""Read-only rollback dry-run for future Gold V3 existing recipe upgrades."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from dry_run_gold_v3_existing_recipe_upgrades import EXPECTED_UPGRADE_IDS  # noqa: E402


MANIFEST_SCHEMA = ROOT / "data" / "recipe_v2" / "gold_v3_upgrade_backup_manifest_schema.json"
REPORT_MD = ROOT / "reports" / "SPRINT_1_3G_GOLD_V3_ROLLBACK_DRY_RUN.md"
REPORT_JSON = ROOT / "reports" / "SPRINT_1_3G_GOLD_V3_ROLLBACK_DRY_RUN.json"
SOURCE_MARKERS = ("source_url", "original_url", "http://", "https://", "http", "povarenok", "поваренок")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def has_source_leakage(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    return any(marker in text for marker in SOURCE_MARKERS)


def expected_inputs() -> list[str]:
    return ["recipes.jsonl", "recipe_ingredients.jsonl", "recipe_steps.jsonl", "rollback_manifest.json"]


def rollback_operations() -> list[str]:
    return [
        "restore recipes fields by ID",
        "delete current ingredient rows for planned IDs",
        "restore old ingredient rows",
        "delete current step rows for planned IDs",
        "restore old step rows",
        "restore image URLs",
        "preserve relation tables untouched",
    ]


def verification_plan() -> list[str]:
    return [
        "recipe count unchanged",
        "max ID unchanged",
        "30 recipe IDs exist",
        "ingredient counts match backup",
        "step counts match backup",
        "relation counts unchanged",
    ]


def inspect_db_available() -> dict[str, Any]:
    try:
        import dry_run_gold_v3_upgrade_backup as backup

        state = backup.inspect_db(EXPECTED_UPGRADE_IDS)
        return {
            "db_available": bool(state.get("db_available")),
            "relation_check_available": bool((state.get("relation_tables") or {}) or state.get("db_available")),
            "reason": state.get("reason"),
        }
    except Exception as exc:
        return {"db_available": False, "relation_check_available": False, "reason": f"db_check_failed:{type(exc).__name__}"}


def build_report(
    *,
    future_backup_path: Path | None = None,
    db_state: dict[str, Any] | None = None,
    write_reports: bool = True,
) -> dict[str, Any]:
    db_state = db_state if db_state is not None else inspect_db_available()
    manifest_exists = bool(future_backup_path and (future_backup_path / "manifest.json").exists())
    backup_missing = not bool(future_backup_path and future_backup_path.exists())
    blockers = []
    if backup_missing:
        blockers.append("backup_missing")
    if not manifest_exists:
        blockers.append("manifest_missing")
    if not db_state.get("db_available"):
        blockers.append("db_unavailable")
    if not db_state.get("relation_check_available"):
        blockers.append("relation_tables_unchecked")
    report = {
        "generated_at": now(),
        "read_only": True,
        "apply": False,
        "db_writes": 0,
        "planned_recipe_ids": EXPECTED_UPGRADE_IDS,
        "backup_manifest_schema": str(MANIFEST_SCHEMA.relative_to(ROOT)),
        "future_backup_path": str(future_backup_path) if future_backup_path else None,
        "backup_missing": backup_missing,
        "manifest_status": "present" if manifest_exists else "missing",
        "db_available": bool(db_state.get("db_available")),
        "relation_check_available": bool(db_state.get("relation_check_available")),
        "expected_inputs": expected_inputs(),
        "planned_rollback_operations": rollback_operations(),
        "verification_after_future_rollback": verification_plan(),
        "blockers": blockers,
        "recommendation": "ready_for_future_real_backup_artifact_sprint" if blockers == ["backup_missing", "manifest_missing"] else "fix_rollback_dry_run_blockers",
    }
    if has_source_leakage(report):
        raise RuntimeError("rollback dry-run report contains source leakage")
    if write_reports:
        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        REPORT_MD.write_text(render(report), encoding="utf-8")
    return report


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3G Gold V3 Rollback Dry-Run",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Read-only: `{report['read_only']}`",
        f"apply: `{report['apply']}`",
        f"db_writes: `{report['db_writes']}`",
        f"backup_missing: `{report['backup_missing']}`",
        f"manifest_status: `{report['manifest_status']}`",
        f"db_available: `{report['db_available']}`",
        f"relation_check_available: `{report['relation_check_available']}`",
        f"blockers: `{report['blockers']}`",
        f"recommendation: `{report['recommendation']}`",
        "",
        "## Expected Inputs",
        "",
    ]
    lines.extend(f"- {item}" for item in report["expected_inputs"])
    lines.extend(["", "## Planned Rollback Operations", ""])
    lines.extend(f"- {item}" for item in report["planned_rollback_operations"])
    lines.extend(["", "## Verification After Future Rollback", ""])
    lines.extend(f"- {item}" for item in report["verification_after_future_rollback"])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.apply:
        print("Apply is intentionally disabled in Sprint 1.3G. Rollback execution is not part of this sprint.", file=sys.stderr)
        return 2
    report = build_report(future_backup_path=Path(args.backup_path) if args.backup_path else None)
    print(f"Wrote {REPORT_MD}")
    return 0 if len(report["planned_recipe_ids"]) == 30 else 1


if __name__ == "__main__":
    raise SystemExit(main())
