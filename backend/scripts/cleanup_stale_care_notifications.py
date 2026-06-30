#!/usr/bin/env python3
"""Mark stale invalid pending care_notifications as skipped.

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

from app.services.care_guard import PROACTIVE_CARE_SEMANTIC_KEYS, TYPE_TO_CARE_FLAG


def _json_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    return []


def _enabled_matches(enabled: list[str], notification_type: str) -> bool:
    aliases = {"protein": {"protein", "health"}}.get(
        notification_type, {notification_type}
    )
    return not set(enabled).isdisjoint(aliases)


def _invalid_reasons(row: dict, duplicate_ids: set[int]) -> list[str]:
    reasons: list[str] = []
    notification_type = str(row.get("type") or "")
    enabled = _json_list(row.get("enabled_notification_types"))
    expected_semantic = PROACTIVE_CARE_SEMANTIC_KEYS.get(notification_type)

    if not row.get("notifications_onboarded"):
        reasons.append("notifications_onboarded_off")
    if (row.get("care_mode") or "off") == "off":
        reasons.append("care_mode_off")
    if expected_semantic and row.get("semantic_key") != expected_semantic:
        reasons.append("invalid_semantic_key")
    if notification_type in TYPE_TO_CARE_FLAG:
        if not _enabled_matches(enabled, notification_type):
            reasons.append("type_not_enabled")
        if not row.get(TYPE_TO_CARE_FLAG[notification_type]):
            reasons.append("care_flag_off")
    if int(row["id"]) in duplicate_ids:
        reasons.append("duplicate_pending")
    return reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Mark invalid rows skipped")
    parser.add_argument(
        "--age-minutes",
        type=int,
        default=30,
        help="Only inspect pending rows older than this age",
    )
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1

    before = datetime.now(timezone.utc) - timedelta(minutes=args.age_minutes)
    engine = create_engine(url)
    duplicate_ids: set[int] = set()
    invalid_rows: list[dict] = []

    with engine.connect() as conn:
        rows = [
            dict(row)
            for row in conn.execute(
                text(
                    """
                    SELECT cn.id, cn.user_id, cn.family_id, cn.type, cn.status,
                           cn.semantic_key, cn.payload, cn.created_at,
                           uns.notifications_onboarded, uns.care_mode,
                           uns.enabled_notification_types,
                           cs.water_enabled, cs.protein_enabled, cs.menu_enabled,
                           cs.shopping_enabled, cs.pantry_enabled, cs.progress_enabled,
                           cs.family_enabled
                    FROM care_notifications cn
                    LEFT JOIN user_notification_settings uns ON uns.user_id = cn.user_id
                    LEFT JOIN care_settings cs ON cs.user_id = cn.user_id
                    WHERE cn.status = 'pending'
                      AND cn.created_at < :before
                    ORDER BY cn.user_id, cn.type, cn.semantic_key, cn.created_at, cn.id
                    """
                ),
                {"before": before},
            )
            .mappings()
            .all()
        ]

        grouped: dict[tuple, list[dict]] = defaultdict(list)
        for row in rows:
            key = (
                row.get("user_id"),
                row.get("family_id"),
                row.get("type"),
                row.get("semantic_key"),
                row.get("status"),
            )
            grouped[key].append(row)

        for group in grouped.values():
            if len(group) > 1:
                for row in group[1:]:
                    duplicate_ids.add(int(row["id"]))

        for row in rows:
            reasons = _invalid_reasons(row, duplicate_ids)
            if not reasons:
                continue
            row["reasons"] = reasons
            invalid_rows.append(row)
            print(
                "stale pending id={id} user={user_id} type={type} semantic={semantic_key} "
                "reasons={reasons}".format(**row)
            )
            if args.apply:
                payload = row.get("payload")
                if isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except json.JSONDecodeError:
                        payload = {}
                if not isinstance(payload, dict):
                    payload = {}
                payload = {
                    **payload,
                    "cleanup_reasons": reasons,
                    "cleanup_at": datetime.now(timezone.utc).isoformat(),
                }
                conn.execute(
                    text(
                        """
                        UPDATE care_notifications
                        SET status = 'skipped', payload = CAST(:payload AS JSONB)
                        WHERE id = :id AND status = 'pending'
                        """
                    ),
                    {"id": row["id"], "payload": json.dumps(payload)},
                )

        if args.apply:
            conn.commit()

    print(
        json.dumps(
            {
                "stale_pending_found": len(rows),
                "invalid_pending_found": len(invalid_rows),
                "changed": len(invalid_rows) if args.apply else 0,
                "mode": "apply" if args.apply else "dry-run",
                "age_minutes": args.age_minutes,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
