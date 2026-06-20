#!/usr/bin/env python3
"""Pre-import backup + lightweight DB snapshot for Gold V3 Stage R."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

DEFAULT_SNAPSHOT_REPORT = ROOT / "reports" / "recipe_gold_v3_pre_import_db_snapshot.md"
DEFAULT_BACKUP_ROOT = ROOT / "backups" / "recipe_gold_v3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backup DB before Gold V3 import")
    parser.add_argument("--backup-dir", type=Path, default=None)
    parser.add_argument("--snapshot-report", type=Path, default=DEFAULT_SNAPSHOT_REPORT)
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", ""))
    return parser.parse_args()


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _redact_db_url(db_url: str) -> str:
    if "@" in db_url:
        return db_url.split("@", 1)[1]
    if db_url.startswith("sqlite"):
        return "sqlite"
    return "local"


def backup_sqlite(db_url: str, dest: Path) -> Path:
    path_part = db_url.replace("sqlite:///", "")
    src = Path(path_part).resolve()
    if not src.exists():
        raise SystemExit(f"sqlite file not found: {src}")
    out = dest / "database.sqlite"
    shutil.copy2(src, out)
    return out


def backup_postgres(db_url: str, dest: Path) -> Path:
    out = dest / "database.sql"
    cmd = [
        "pg_dump",
        db_url,
        "--no-owner",
        "--no-acl",
        "--table=recipes",
        "--table=recipe_ingredients",
        "--table=recipe_steps",
        "--table=recipe_tags",
        "--table=recipe_allergens",
        "--table=recipe_restrictions",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise SystemExit("pg_dump not found; install postgresql-client") from exc
    if proc.returncode != 0:
        raise SystemExit(f"pg_dump failed: {proc.stderr or proc.stdout}")
    out.write_text(proc.stdout, encoding="utf-8")
    return out


def write_snapshot_report(path: Path, snapshot: dict, backup_path: Path, db_url: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Recipe Gold V3 — Pre-Import DB Snapshot",
        "",
        f"**Generated:** {now}",
        f"**Backup path:** `{backup_path}`",
        f"**Database:** `{_redact_db_url(db_url)}`",
        "",
        "## Counts (before import)",
        "",
        f"- recipes total: `{snapshot.get('recipes_total', 0)}`",
        f"- recipe_ingredients total: `{snapshot.get('recipe_ingredients_total', 0)}`",
        f"- gold_v3 tag count: `{snapshot.get('gold_v3_count', 0)}`",
        f"- generated_original source_type count: `{snapshot.get('generated_original_count', 0)}`",
        f"- max recipe id: `{snapshot.get('max_recipe_id', 0)}`",
        "",
        "## Safety",
        "",
        "- Safe reset: not run",
        "- Old recipe updates: not run",
        "- Old recipe deletes: not run",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    db_url = (args.database_url or "").strip()
    if not db_url:
        print("ERROR: set DATABASE_URL or --database-url", file=sys.stderr)
        return 2

    os.environ["DATABASE_URL"] = db_url
    from app.database import SessionLocal  # noqa: E402
    from app.recipes.recipe_gold_v3_importer import collect_db_snapshot  # noqa: E402

    stamp = _stamp()
    dest = args.backup_dir or (DEFAULT_BACKUP_ROOT / stamp)
    dest.mkdir(parents=True, exist_ok=True)

    if db_url.startswith("sqlite"):
        backup_path = backup_sqlite(db_url, dest)
    elif db_url.startswith("postgres"):
        backup_path = backup_postgres(db_url, dest)
    else:
        print(f"ERROR: unsupported DATABASE_URL scheme", file=sys.stderr)
        return 2

    session = SessionLocal()
    try:
        snapshot = collect_db_snapshot(session)
    finally:
        session.close()

    manifest = dest / "manifest.md"
    manifest.write_text(
        f"# Gold V3 pre-import backup\n\n- stamp: `{stamp}`\n- backup: `{backup_path}`\n",
        encoding="utf-8",
    )
    write_snapshot_report(args.snapshot_report, snapshot, backup_path, db_url)
    print(f"backup={backup_path}")
    print(f"snapshot={args.snapshot_report}")
    print(f"recipes_total={snapshot['recipes_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
