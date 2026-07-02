"""Create read-only backup artifacts for future Gold V3 recipe upgrades."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tarfile
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from dry_run_gold_v3_existing_recipe_upgrades import EXPECTED_UPGRADE_IDS  # noqa: E402


REPORT_MD = ROOT / "reports" / "SPRINT_1_3H_GOLD_V3_BACKUP_ARTIFACTS_DRY_RUN.md"
REPORT_JSON = ROOT / "reports" / "SPRINT_1_3H_GOLD_V3_BACKUP_ARTIFACTS_DRY_RUN.json"
SOURCE_MARKERS = ("source_url", "original_url", "http://", "https://", "http", "povarenok", "поваренок")
RELATION_TABLE_CANDIDATES = (
    "recipe_explanations",
    "recipe_favorites",
    "recipe_history",
    "meal_checkins",
    "meal_consumption_logs",
    "family_menu_selections",
    "family_shopping_lists",
    "shopping_categories",
)
RELATION_HINTS = ("meal_plan", "planned_meal", "menu", "shopping")
REQUIRED_BACKUP_FILES = (
    "MANIFEST.md",
    "manifest.json",
    "recipes.jsonl",
    "recipe_ingredients.jsonl",
    "recipe_steps.jsonl",
    "rollback_manifest.json",
    "verification_report.md",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def backup_id() -> str:
    return "gold_v3_upgrade_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def make_unique_backup_dir(root: Path, bid: str) -> Path:
    for index in range(100):
        suffix = "" if index == 0 else f"_{index:02d}"
        candidate = root / f"{bid}{suffix}"
        try:
            candidate.mkdir(parents=True, exist_ok=False)
            return candidate
        except FileExistsError:
            continue
    raise RuntimeError(f"Unable to allocate unique backup directory under {root}")


def git_commit() -> str:
    try:
        import subprocess

        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(json_safe(row), ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def has_source_leakage(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    return any(marker in text for marker in SOURCE_MARKERS)


def public_table_summary(name: str, rows: list[dict[str, Any]], required: bool) -> dict[str, Any]:
    return {"required": required, "row_count": len(rows), "format": "jsonl"}


def connect_db(database_url: str | None = None):
    from sqlalchemy import create_engine

    database_url = database_url or os.getenv("DATABASE_URL") or "postgresql://aifood:aifood@localhost:5432/aifood"
    return create_engine(database_url, future=True)


def select_rows(conn: Any, table_name: str, planned_ids: list[int]) -> list[dict[str, Any]]:
    from sqlalchemy import text

    rows = conn.execute(
        text(f"select * from {table_name} where recipe_id = any(:ids) order by recipe_id"),
        {"ids": planned_ids},
    ).mappings().all()
    return [dict(row) for row in rows]


def collect_backup_data(planned_ids: list[int] | None = None, database_url: str | None = None) -> dict[str, Any]:
    planned_ids = planned_ids or EXPECTED_UPGRADE_IDS
    if planned_ids != EXPECTED_UPGRADE_IDS:
        raise RuntimeError("Planned IDs do not match expected Gold V3 upgrade set.")

    from sqlalchemy import inspect, text

    engine = connect_db(database_url)
    with engine.connect() as conn:
        inspector = inspect(conn)
        tables = set(inspector.get_table_names())
        if "recipes" not in tables:
            raise RuntimeError("recipes table not found")
        recipes = [
            dict(row)
            for row in conn.execute(
                text("select * from recipes where id = any(:ids) order by id"),
                {"ids": planned_ids},
            ).mappings().all()
        ]
        if sorted(int(row["id"]) for row in recipes) != planned_ids:
            raise RuntimeError("Not all planned recipe IDs exist in DB.")

        ingredients = select_rows(conn, "recipe_ingredients", planned_ids) if "recipe_ingredients" in tables else []
        steps = select_rows(conn, "recipe_steps", planned_ids) if "recipe_steps" in tables else []

        relation_table_names = set(RELATION_TABLE_CANDIDATES)
        relation_table_names.update(table for table in tables if any(hint in table for hint in RELATION_HINTS))
        relation_tables: dict[str, dict[str, Any]] = {}
        relation_rows: dict[str, list[dict[str, Any]]] = {}
        for table_name in sorted(relation_table_names):
            if table_name not in tables:
                relation_tables[table_name] = {
                    "exists": False,
                    "recipe_id_column": False,
                    "rows": 0,
                    "policy": "preserve_only_no_delete_no_update",
                }
                continue
            columns = {column["name"] for column in inspector.get_columns(table_name)}
            has_recipe_id = "recipe_id" in columns
            rows = select_rows(conn, table_name, planned_ids) if has_recipe_id else []
            relation_rows[table_name] = rows
            relation_tables[table_name] = {
                "exists": True,
                "recipe_id_column": has_recipe_id,
                "rows": len(rows),
                "policy": "preserve_only_no_delete_no_update",
                "backup_required": bool(rows),
            }

    return {
        "recipe_ids": planned_ids,
        "recipes": recipes,
        "recipe_ingredients": ingredients,
        "recipe_steps": steps,
        "relation_tables": relation_tables,
        "relation_rows": relation_rows,
    }


def image_paths(recipes: list[dict[str, Any]]) -> list[Path]:
    image_root = Path(os.getenv("RECIPE_IMAGES_DIR", str(ROOT / "apps" / "web" / "public" / "recipe-images")))
    paths: list[Path] = []
    for row in recipes:
        for field in ("hero_image_url", "image_url", "thumbnail_url"):
            value = str(row.get(field) or "")
            if not value or "/recipe-images/" not in value:
                continue
            relative = value.split("/recipe-images/", 1)[1]
            candidate = image_root / relative
            if candidate.exists():
                paths.append(candidate)
    return sorted(set(paths))


def manifest(data: dict[str, Any], bid: str, image_count: int) -> dict[str, Any]:
    return {
        "backup_id": bid,
        "git_commit": git_commit(),
        "created_at": now(),
        "recipe_ids": data["recipe_ids"],
        "tables": {
            "recipes": public_table_summary("recipes", data["recipes"], True),
            "recipe_ingredients": public_table_summary("recipe_ingredients", data["recipe_ingredients"], True),
            "recipe_steps": public_table_summary("recipe_steps", data["recipe_steps"], True),
        },
        "relation_tables": data["relation_tables"],
        "image_files": {"count": image_count, "archive": "recipe-images.tar.gz" if image_count else None},
        "rollback_manifest": {"required": True, "format": "json"},
        "upgrade_apply_allowed": False,
    }


def rollback_manifest(data: dict[str, Any], bid: str) -> dict[str, Any]:
    return {
        "backup_id": bid,
        "created_at": now(),
        "git_commit": git_commit(),
        "recipe_ids": data["recipe_ids"],
        "db_counts": {
            "recipes": len(data["recipes"]),
            "recipe_ingredients": len(data["recipe_ingredients"]),
            "recipe_steps": len(data["recipe_steps"]),
        },
        "relation_tables": {
            table: {"rows": meta["rows"], "policy": "preserve_restore_if_needed" if meta["rows"] else "preserve_untouched"}
            for table, meta in data["relation_tables"].items()
        },
        "rollback_operations": [
            "restore recipes by id",
            "replace recipe_ingredients rows for planned ids",
            "replace recipe_steps rows for planned ids",
            "restore image urls",
            "preserve relation tables untouched",
        ],
        "upgrade_apply_allowed": False,
    }


def backup_root() -> Path:
    return Path(os.getenv("BACKUP_ROOT", str(ROOT / "backups")))


def create_backup(data: dict[str, Any], root: Path | None = None) -> Path:
    bid = backup_id()
    root = root or backup_root()
    out_dir = make_unique_backup_dir(root, bid)
    relation_dir = out_dir / "relation_tables"
    relation_dir.mkdir()

    images = image_paths(data["recipes"])
    man = manifest(data, bid, len(images))
    rollback = rollback_manifest(data, bid)

    write_jsonl(out_dir / "recipes.jsonl", data["recipes"])
    write_jsonl(out_dir / "recipe_ingredients.jsonl", data["recipe_ingredients"])
    write_jsonl(out_dir / "recipe_steps.jsonl", data["recipe_steps"])
    for table, rows in data["relation_rows"].items():
        if rows:
            write_jsonl(relation_dir / f"{table}.jsonl", rows)
    (relation_dir / "_metadata.json").write_text(
        json.dumps(json_safe(data["relation_tables"]), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "manifest.json").write_text(
        json.dumps(json_safe(man), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "rollback_manifest.json").write_text(
        json.dumps(json_safe(rollback), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if images:
        with tarfile.open(out_dir / "recipe-images.tar.gz", "w:gz") as tar:
            for path in images:
                tar.add(path, arcname=str(path.relative_to(path.parents[2])))
    write_manifest_md(out_dir / "MANIFEST.md", man)
    write_verification_report(out_dir / "verification_report.md", man, rollback, out_dir)
    return out_dir


def write_manifest_md(path: Path, man: dict[str, Any]) -> None:
    lines = [
        "# Gold V3 Upgrade Backup Manifest",
        "",
        f"backup_id: `{man['backup_id']}`",
        f"created_at: `{man['created_at']}`",
        f"git_commit: `{man['git_commit']}`",
        f"recipe_ids: `{man['recipe_ids']}`",
        f"upgrade_apply_allowed: `{man['upgrade_apply_allowed']}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_verification_report(path: Path, man: dict[str, Any], rollback: dict[str, Any], out_dir: Path) -> None:
    lines = [
        "# Gold V3 Upgrade Backup Verification",
        "",
        f"backup_dir: `{out_dir}`",
        f"recipes: `{man['tables']['recipes']['row_count']}`",
        f"recipe_ingredients: `{man['tables']['recipe_ingredients']['row_count']}`",
        f"recipe_steps: `{man['tables']['recipe_steps']['row_count']}`",
        f"rollback_manifest_upgrade_apply_allowed: `{rollback['upgrade_apply_allowed']}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def public_report(data: dict[str, Any], mode: str, created_dir: Path | None = None) -> dict[str, Any]:
    report = {
        "generated_at": now(),
        "mode": mode,
        "read_only_db": True,
        "db_writes": 0,
        "backup_dir": str(created_dir) if created_dir else None,
        "planned_recipe_ids": data["recipe_ids"],
        "recipes_count": len(data["recipes"]),
        "recipe_ingredients_count": len(data["recipe_ingredients"]),
        "recipe_steps_count": len(data["recipe_steps"]),
        "relation_tables": data["relation_tables"],
        "required_files": list(REQUIRED_BACKUP_FILES) + ["relation_tables/_metadata.json"],
        "upgrade_apply_allowed": False,
        "recommendation": "ready_to_create_backup_artifacts" if mode == "dry_run" else "ready_to_verify_backup_artifacts",
    }
    if has_source_leakage(report):
        raise RuntimeError("public backup report contains source leakage")
    return report


def unavailable_report(reason: str) -> dict[str, Any]:
    return {
        "generated_at": now(),
        "mode": "dry_run",
        "read_only_db": True,
        "db_available": False,
        "db_writes": 0,
        "backup_dir": None,
        "planned_recipe_ids": EXPECTED_UPGRADE_IDS,
        "recipes_count": None,
        "recipe_ingredients_count": None,
        "recipe_steps_count": None,
        "relation_tables": {},
        "required_files": list(REQUIRED_BACKUP_FILES) + ["relation_tables/_metadata.json"],
        "upgrade_apply_allowed": False,
        "blockers": [reason],
        "recommendation": "fix_backup_artifact_blockers",
    }


def write_report(report: dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Sprint 1.3H Gold V3 Backup Artifacts Dry-Run",
        "",
        f"mode: `{report['mode']}`",
        f"db_writes: `{report['db_writes']}`",
        f"db_available: `{report.get('db_available', True)}`",
        f"backup_dir: `{report['backup_dir']}`",
        f"recipes_count: `{report['recipes_count']}`",
        f"recipe_ingredients_count: `{report['recipe_ingredients_count']}`",
        f"recipe_steps_count: `{report['recipe_steps_count']}`",
        f"upgrade_apply_allowed: `{report['upgrade_apply_allowed']}`",
        "",
        "## Relation Tables",
        "",
    ]
    for table, meta in report["relation_tables"].items():
        lines.append(f"- {table}: rows=`{meta['rows']}`, backup_required=`{meta.get('backup_required', False)}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(mode: str = "dry_run", backup_root_path: Path | None = None) -> dict[str, Any]:
    try:
        data = collect_backup_data()
    except Exception as exc:
        if mode == "create_backup":
            raise
        report = unavailable_report(f"db_unavailable:{type(exc).__name__}")
        write_report(report)
        return report
    created_dir = create_backup(data, backup_root_path) if mode == "create_backup" else None
    report = public_report(data, mode, created_dir)
    write_report(report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--create-backup", action="store_true")
    parser.add_argument("--backup-root")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.apply:
        print("Apply is not supported in this script. This script creates backup artifacts only.", file=sys.stderr)
        return 2
    mode = "create_backup" if args.create_backup else "dry_run"
    try:
        report = run(mode, Path(args.backup_root) if args.backup_root else None)
    except Exception as exc:
        print(f"Backup artifact script failed safely: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if report.get("backup_dir"):
        print(f"Created backup dir: {report['backup_dir']}")
    print(f"Wrote {REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
