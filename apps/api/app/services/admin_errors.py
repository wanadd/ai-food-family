"""Append-only error log for admin dashboard (MVP)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


def _log_path() -> Path:
    root = Path(settings.backup_root).resolve()
    if not root.is_absolute():
        root = Path("/app") / root
    log_dir = root.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "admin_errors.jsonl"


def record_error(*, path: str, status_code: int, detail: str | None = None) -> None:
    try:
        entry = {
            "at": datetime.now(timezone.utc).isoformat(),
            "path": path[:500],
            "status_code": status_code,
            "detail": (detail or "")[:2000],
        }
        with _log_path().open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.exception("Failed to write admin error log")


def count_errors_since(hours: int = 24) -> int:
    path = _log_path()
    if not path.is_file():
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    count = 0
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                at = datetime.fromisoformat(entry["at"].replace("Z", "+00:00"))
                if at >= cutoff:
                    count += 1
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    except OSError:
        logger.exception("Failed to read admin error log")
    return count
