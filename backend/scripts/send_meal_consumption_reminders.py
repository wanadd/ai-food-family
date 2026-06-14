#!/usr/bin/env python3
"""Run meal consumption reminder job (Phase 3A).

Safe manual/dry-run entry point — does not start a background loop.

Usage (local):
    cd C:\\Projects\\ai-food-family
    $env:PYTHONPATH="apps/api"
    python backend/scripts/send_meal_consumption_reminders.py --dry-run

    python backend/scripts/send_meal_consumption_reminders.py --now 2026-06-10T16:00:00+03:00
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql://aifood:aifood@localhost:5432/aifood")

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.services.meal_consumption_reminders import (  # noqa: E402
    send_due_meal_consumption_reminders,
)


def _parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


async def _run(*, dry_run: bool, now: datetime, limit: int | None) -> dict[str, int]:
    db = SessionLocal()
    try:
        counts = await send_due_meal_consumption_reminders(
            db,
            now,
            dry_run=dry_run,
            limit=limit,
            force=dry_run,
        )
        db.commit()
        return counts
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Send meal consumption reminders")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log candidates without sending Telegram messages",
    )
    parser.add_argument(
        "--now",
        default=None,
        help="ISO datetime for simulated current time (UTC if no offset)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max reminders to process in one run",
    )
    args = parser.parse_args()

    if not settings.meal_consumption_reminders_enabled and not args.dry_run:
        print(
            "MEAL_CONSUMPTION_REMINDERS_ENABLED=false — use --dry-run or enable flag",
            file=sys.stderr,
        )
        return 2

    now = _parse_now(args.now)
    dry_run = args.dry_run or settings.meal_consumption_reminders_dry_run
    counts = asyncio.run(_run(dry_run=dry_run, now=now, limit=args.limit))
    print(json.dumps(counts, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
