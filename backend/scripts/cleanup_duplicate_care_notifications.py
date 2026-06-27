#!/usr/bin/env python3
"""Find and cancel duplicate care_notifications from the last 24 hours.

Dry-run by default. Apply with --apply only after reviewing stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlalchemy import create_engine, text


def _dedup_key(row: dict) -> tuple:
    payload = row.get("payload")
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            payload = {}
    if not isinstance(payload, dict):
        payload = {}
    web_path = payload.get("web_app_path") or ""
    semantic = row.get("semantic_key") or ""
    return (
        row.get("user_id"),
        row.get("family_id"),
        row.get("type"),
        row.get("message") or "",
        semantic or web_path,
    )


def _pick_winner(rows: list[dict]) -> dict:
    """Prefer sent, then earliest pending/sent, else earliest created."""

    def sort_key(r: dict) -> tuple:
        status = (r.get("status") or "").lower()
        sent_rank = 0 if status == "sent" else 1
        created = r.get("created_at")
        return (sent_rank, created or datetime.min.replace(tzinfo=timezone.utc))

    return sorted(rows, key=sort_key)[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Cancel duplicate rows")
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    engine = create_engine(url)

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, user_id, family_id, type, message, status, semantic_key,
                       payload, created_at, sent_at
                FROM care_notifications
                WHERE created_at >= :since
                  AND status IN ('pending', 'sent')
                ORDER BY created_at ASC
                """
            ),
            {"since": since},
        ).mappings().all()

        grouped: dict[tuple, list[dict]] = defaultdict(list)
        for row in rows:
            grouped[_dedup_key(dict(row))].append(dict(row))

        duplicates_found = 0
        notifications_changed = 0
        events_changed = 0
        affected_users: set[int] = set()

        for key, group in grouped.items():
            if len(group) <= 1:
                continue
            duplicates_found += len(group) - 1
            winner = _pick_winner(group)
            losers = [r for r in group if r["id"] != winner["id"]]

            for loser in losers:
                affected_users.add(int(loser["user_id"]))
                print(
                    f"duplicate id={loser['id']} user={loser['user_id']} "
                    f"type={loser['type']} status={loser['status']} "
                    f"keep id={winner['id']}"
                )
                if not args.apply:
                    continue

                conn.execute(
                    text(
                        """
                        UPDATE care_notifications
                        SET status = 'cancelled'
                        WHERE id = :id AND status IN ('pending', 'sent')
                        """
                    ),
                    {"id": loser["id"]},
                )
                notifications_changed += 1

                ev = conn.execute(
                    text(
                        """
                        UPDATE care_events
                        SET payload = COALESCE(payload, '{}'::jsonb) ||
                            '{"dedup_cancelled": true}'::jsonb
                        WHERE event_type LIKE 'care_%'
                          AND payload->>'notification_id' = :nid
                        """
                    ),
                    {"nid": str(loser["id"])},
                )
                events_changed += ev.rowcount or 0

        if args.apply:
            conn.commit()

    print(
        json.dumps(
            {
                "duplicates_found": duplicates_found,
                "notifications_changed": notifications_changed,
                "events_changed": events_changed,
                "affected_users": sorted(affected_users),
                "mode": "apply" if args.apply else "dry-run",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
