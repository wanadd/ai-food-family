"""Database backups for admin panel and deploy scripts."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from app.config import settings

logger = logging.getLogger(__name__)

BACKUP_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$")


def backup_root() -> Path:
    root = Path(settings.backup_root)
    if not root.is_absolute():
        root = Path("/app") / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def _timestamp_folder() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")


def _find_env_file() -> Path | None:
    candidates = [
        Path("/app/.env"),
        Path("/app") / ".." / ".env",
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
    ]
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file():
            return resolved
    return None


def _parse_database_url(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": parsed.username or "",
        "password": parsed.password or "",
        "dbname": (parsed.path or "/").lstrip("/"),
    }


def create_backup() -> dict[str, str]:
    folder_name = _timestamp_folder()
    target = backup_root() / folder_name
    target.mkdir(parents=True, exist_ok=False)

    db_params = _parse_database_url(settings.database_url)
    dump_path = target / "database.sql"

    env = os.environ.copy()
    if db_params["password"]:
        env["PGPASSWORD"] = db_params["password"]

    cmd = [
        "pg_dump",
        "-h",
        db_params["host"],
        "-p",
        db_params["port"],
        "-U",
        db_params["user"],
        "-d",
        db_params["dbname"],
        "--no-owner",
        "--no-acl",
        "-f",
        str(dump_path),
    ]

    try:
        subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        shutil.rmtree(target, ignore_errors=True)
        raise RuntimeError(
            "pg_dump не найден. Установите postgresql-client или запустите scripts/backup.sh на хосте."
        ) from exc
    except subprocess.CalledProcessError as exc:
        shutil.rmtree(target, ignore_errors=True)
        stderr = (exc.stderr or "").strip()
        raise RuntimeError(f"pg_dump failed: {stderr or exc}") from exc

    env_src = _find_env_file()
    if env_src is not None:
        shutil.copy2(env_src, target / "env.backup")

    (target / "timestamp.txt").write_text(
        datetime.now(timezone.utc).isoformat(),
        encoding="utf-8",
    )

    size_bytes = sum(f.stat().st_size for f in target.rglob("*") if f.is_file())
    logger.info("Backup created at %s (%s bytes)", target, size_bytes)

    return {
        "id": folder_name,
        "path": str(target),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "size_bytes": str(size_bytes),
    }


def list_backups() -> list[dict[str, str | int]]:
    root = backup_root()
    items: list[dict[str, str | int]] = []
    if not root.is_dir():
        return items

    for entry in sorted(root.iterdir(), reverse=True):
        if not entry.is_dir() or not BACKUP_NAME_RE.match(entry.name):
            continue
        ts_file = entry / "timestamp.txt"
        created_at = ts_file.read_text(encoding="utf-8").strip() if ts_file.is_file() else entry.name
        size_bytes = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
        has_db = (entry / "database.sql").is_file()
        has_env = (entry / "env.backup").is_file()
        items.append(
            {
                "id": entry.name,
                "path": str(entry),
                "created_at": created_at,
                "size_bytes": size_bytes,
                "has_database": has_db,
                "has_env": has_env,
            }
        )
    return items
