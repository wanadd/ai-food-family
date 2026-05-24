"""Admin error logging to database (and legacy file fallback)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.admin import AdminErrorLog

logger = logging.getLogger(__name__)


def _log_path() -> Path:
    root = Path(settings.backup_root).resolve()
    if not root.is_absolute():
        root = Path("/app") / root
    log_dir = root.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "admin_errors.jsonl"


def record_error(
    *,
    path: str,
    status_code: int,
    detail: str | None = None,
    error_type: str = "backend",
    user_id: int | None = None,
    family_id: int | None = None,
    stack: str | None = None,
) -> None:
    message = (detail or "")[:4000]
    try:
        db = SessionLocal()
        try:
            db.add(
                AdminErrorLog(
                    error_type=error_type,
                    user_id=user_id,
                    family_id=family_id,
                    endpoint=path[:500],
                    message=message,
                    stack=stack[:8000] if stack else None,
                    status=status_code,
                )
            )
            db.commit()
        finally:
            db.close()
    except Exception:
        logger.exception("Failed to write admin error log to database")

    try:
        entry = {
            "at": datetime.now(timezone.utc).isoformat(),
            "path": path[:500],
            "status_code": status_code,
            "detail": message[:2000],
        }
        with _log_path().open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.exception("Failed to write admin error log file")


def count_errors_since(hours: int = 24, db: Session | None = None) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    if db is not None:
        return (
            db.query(func.count(AdminErrorLog.id))
            .filter(AdminErrorLog.created_at >= cutoff)
            .scalar()
            or 0
        )
    session = SessionLocal()
    try:
        return count_errors_since(hours, db=session)
    finally:
        session.close()


def list_errors(db: Session, *, limit: int = 100, offset: int = 0) -> list[dict]:
    rows = (
        db.query(AdminErrorLog)
        .order_by(AdminErrorLog.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "error_type": row.error_type,
            "user_id": row.user_id,
            "family_id": row.family_id,
            "endpoint": row.endpoint,
            "message": row.message,
            "status": row.status,
            "created_at": row.created_at,
        }
        for row in rows
    ]
