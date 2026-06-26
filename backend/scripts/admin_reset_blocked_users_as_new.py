#!/usr/bin/env python3
"""Reset blocked users as new — dry-run by default, --apply to execute.

Removes blocked non-admin users and all their data so Telegram re-login
creates a fresh account with 7-day trial.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.user import User
from app.services.user_data_purge import hard_delete_user_row, purge_user_data, snapshot_user_for_backup


def _admin_ids() -> set[int]:
    return settings.admin_telegram_id_set()


def _blocked_users(db: Session) -> list[User]:
    admin_ids = _admin_ids()
    q = db.query(User).filter(User.is_blocked.is_(True))
    if admin_ids:
        q = q.filter(User.telegram_id.notin_(admin_ids))
    return q.order_by(User.id).all()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Execute deletions")
    parser.add_argument(
        "--backup-dir",
        default=str(ROOT / "backups"),
        help="Directory for JSON backup before apply",
    )
    args = parser.parse_args()

    engine = create_engine(os.environ["DATABASE_URL"])
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    users = _blocked_users(db)
    print(f"Blocked users to reset: {len(users)}")
    for user in users:
        print(
            f"  id={user.id} tg={user.telegram_id} "
            f"name={user.first_name!r} deleted={user.is_deleted}"
        )

    if not users:
        print("Nothing to do.")
        return 0

    if not args.apply:
        print("Dry-run only. Pass --apply to execute.")
        return 0

    backup_dir = Path(args.backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"blocked_users_reset_{stamp}.json"
    backup_path.write_text(
        json.dumps([snapshot_user_for_backup(u) for u in users], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Backup written: {backup_path}")

    for user in users:
        purge_user_data(db, user.id, include_subscriptions=True)
        hard_delete_user_row(db, user.id)
    db.commit()

    remaining = db.query(User).filter(User.is_blocked.is_(True)).count()
    print(f"Apply complete. blocked_users_remaining={remaining}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
