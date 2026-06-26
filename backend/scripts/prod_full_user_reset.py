#!/usr/bin/env python3
"""Production-safe full user reset — dry-run by default.

Removes ALL user accounts and user-owned data. Does NOT touch recipe catalog.
Apply only with: --apply --confirm FULL_USER_RESET
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

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

CONFIRM_TOKEN = "FULL_USER_RESET"

# Child tables first (approximate FK-safe order). Recipes catalog excluded.
_PURGE_TABLES: tuple[str, ...] = (
    "cooking_batch_events",
    "cooking_batches",
    "meal_consumption_reminder_events",
    "meal_consumption_logs",
    "meal_checkins",
    "meal_leftovers",
    "family_menu_selections",
    "collection_recipes",
    "recipe_explanations",
    "recipe_favorites",
    "recipe_history",
    "recipe_ratings",
    "recipe_collections",
    "family_pantry_items",
    "family_shopping_lists",
    "shopping_categories",
    "family_invites",
    "family_members",
    "deferred_nutrition_advice",
    "external_food_logs",
    "water_intake_logs",
    "progress_entries",
    "training_entries",
    "nutrition_targets",
    "care_events",
    "care_notifications",
    "care_settings",
    "event_plans",
    "ai_usage_logs",
    "ama_transactions",
    "ama_wallets",
    "user_subscriptions",
    "user_notification_settings",
    "user_preferences",
    "user_profiles",
    "admin_sessions",
    "admin_login_attempts",
    "admin_actions",
    "admin_error_logs",
    "telegram_bot_sessions",
    "families",
    "users",
)

_PROTECTED_TABLES = frozenset(
    {
        "recipes",
        "recipe_ingredients",
        "alembic_version",
        "subscription_plans",
    }
)


def _table_exists(inspector, name: str) -> bool:
    return name in inspector.get_table_names()


def _count_table(conn, table: str) -> int | None:
    try:
        return int(conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0)
    except Exception:
        return None


def _snapshot_users(conn) -> list[dict]:
    try:
        rows = conn.execute(
            text(
                "SELECT id, telegram_id, username, first_name, is_blocked, "
                "is_deleted, created_at FROM users ORDER BY id"
            )
        ).mappings().all()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _backup_table_rows(conn, table: str) -> list[dict]:
    try:
        rows = conn.execute(text(f"SELECT * FROM {table}")).mappings().all()
        out: list[dict] = []
        for row in rows:
            item = {}
            for k, v in dict(row).items():
                if hasattr(v, "isoformat"):
                    item[k] = v.isoformat()
                else:
                    item[k] = v
            out.append(item)
        return out
    except Exception:
        return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument(
        "--backup-dir",
        default="/app/backups",
        help="Backup directory inside container",
    )
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1

    engine = create_engine(url)
    inspector = inspect(engine)

    with engine.connect() as conn:
        recipes_before = _count_table(conn, "recipes")
        users = _snapshot_users(conn)
        print(f"users to remove: {len(users)}")
        for u in users[:50]:
            print(
                f"  id={u.get('id')} tg={u.get('telegram_id')} "
                f"blocked={u.get('is_blocked')} deleted={u.get('is_deleted')}"
            )
        if len(users) > 50:
            print(f"  ... and {len(users) - 50} more")

        print("\nTable counts (purge targets):")
        purge_stats: dict[str, int | None] = {}
        for table in _PURGE_TABLES:
            if not _table_exists(inspector, table):
                continue
            purge_stats[table] = _count_table(conn, table)
            print(f"  {table}: {purge_stats[table]}")

        print(f"\nrecipes (protected): {recipes_before}")
        plans = conn.execute(
            text("SELECT code, name, is_active FROM subscription_plans ORDER BY sort_order, id")
        ).mappings().all()
        print("subscription_plans:")
        for p in plans:
            print(f"  {p['code']}: {p['name']} active={p['is_active']}")

        if not args.apply:
            print("\nDry-run only. To apply: --apply --confirm FULL_USER_RESET")
            return 0

        if args.confirm != CONFIRM_TOKEN:
            print(f"Refused: --confirm must be exactly {CONFIRM_TOKEN!r}", file=sys.stderr)
            return 2

        backup_dir = Path(args.backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = backup_dir / f"full_user_reset_backup_{stamp}.json"
        backup_payload: dict[str, object] = {"users": users, "tables": {}}
        for table in _PURGE_TABLES:
            if table in _PROTECTED_TABLES:
                continue
            if not _table_exists(inspector, table):
                continue
            backup_payload["tables"][table] = _backup_table_rows(conn, table)
        backup_path.write_text(
            json.dumps(backup_payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"Backup written: {backup_path}")

        trans = conn.begin()
        try:
            if _table_exists(inspector, "recipes"):
                nulled = conn.execute(
                    text("UPDATE recipes SET user_id = NULL WHERE user_id IS NOT NULL")
                ).rowcount
                print(f"recipes user_id nulled: {nulled}")
            for table in _PURGE_TABLES:
                if table in _PROTECTED_TABLES:
                    continue
                if not _table_exists(inspector, table):
                    continue
                deleted = conn.execute(text(f"DELETE FROM {table}")).rowcount
                print(f"deleted {table}: {deleted}")
            trans.commit()
        except Exception:
            trans.rollback()
            raise

        users_after = _count_table(conn, "users")
        subs_after = _count_table(conn, "user_subscriptions")
        recipes_after = _count_table(conn, "recipes")
        print(
            f"\nAfter reset: users={users_after} subs={subs_after} "
            f"recipes={recipes_after} (was {recipes_before})"
        )
        if recipes_before is not None and recipes_after != recipes_before:
            print("ERROR: recipe count changed!", file=sys.stderr)
            return 3
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
