"""Read-only legacy PostgreSQL snapshot for the selective V2 importer."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


QUERIES = {
    "users": "SELECT id, telegram_id AS provider_subject, 'telegram' AS provider, first_name AS display_name, is_deleted AS deleted FROM users ORDER BY id",
    "profiles": "SELECT id, user_id, allergies, medical_restrictions AS medical_notes, age FROM user_profiles ORDER BY id",
    "families": "SELECT id, name FROM families ORDER BY id",
    "family_members": "SELECT id, family_id, user_id, role FROM family_members ORDER BY id",
    "recipes": "SELECT id, title, false AS gold_v3_validated FROM recipes ORDER BY id",
    "shopping": "SELECT id, user_id, family_id, items, updated_at FROM family_shopping_lists ORDER BY id",
    "entitlements": "SELECT id, user_id, family_id, plan_code, status, started_at, trial_ends_at, current_period_ends_at, menu_generations_used FROM user_subscriptions ORDER BY id",
    "nutrition_goals": "SELECT id, user_id, person_id, family_id, calories_target, protein_target_g, fat_target_g, carbs_target_g, fiber_target_g, water_target_ml, goal_type, created_at FROM nutrition_targets ORDER BY id",
    "notification_preferences": "SELECT id, user_id, buy_reminder_enabled, cook_reminder_enabled, timezone, notifications_onboarded FROM user_notification_settings ORDER BY id",
    "plans": "SELECT id, user_id, family_id, selected_at, menu_data->'days' AS days FROM family_menu_selections ORDER BY id",
    "pantry": "SELECT id, user_id, family_id, name, quantity, unit, expires_at FROM family_pantry_items ORDER BY id",
    "events": "SELECT id, user_id, family_id, title, status, allergies_note FROM event_plans ORDER BY id",
    "cooking": "SELECT id FROM cooking_batches ORDER BY id",
    "consumption": "SELECT id FROM meal_consumption_logs ORDER BY id",
    "notifications": "SELECT id FROM care_notifications ORDER BY id",
    "admin_sessions": "SELECT id FROM admin_sessions ORDER BY id",
}

TABLES = {
    "users": "users", "profiles": "user_profiles", "families": "families",
    "family_members": "family_members", "recipes": "recipes",
    "shopping": "family_shopping_lists", "entitlements": "user_subscriptions",
    "nutrition_goals": "nutrition_targets", "notification_preferences": "user_notification_settings",
    "plans": "family_menu_selections", "pantry": "family_pantry_items",
    "events": "event_plans", "cooking": "cooking_batches",
    "consumption": "meal_consumption_logs", "notifications": "care_notifications",
    "admin_sessions": "admin_sessions",
}


def export_snapshot(database_url: str) -> tuple[dict, dict[str, int]]:
    url = make_url(database_url)
    if not url.drivername.startswith("postgresql") or not url.database:
        raise ValueError("PostgreSQL source URL required")
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
            available = set(inspect(connection).get_table_names())
            payload: dict = {"source_database": connection.execute(text("SELECT current_database()")).scalar_one()}
            states: dict[str, str] = {}
            counts: dict[str, int] = {}
            for domain, query in QUERIES.items():
                if TABLES[domain] not in available:
                    states[domain] = "SOURCE_DOMAIN_NOT_EXPORTED"
                    continue
                rows = [dict(row) for row in connection.execute(text(query)).mappings()]
                payload[domain] = rows
                counts[domain] = len(rows)
                states[domain] = "SOURCE_DOMAIN_PRESENT" if rows else "SOURCE_DOMAIN_ZERO"
            payload["source_domains"] = states
            connection.rollback()
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()
        payload["snapshot"] = f"sha256:{fingerprint}"
        return payload, counts
    finally:
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a frozen read-only legacy snapshot")
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        payload, counts = export_snapshot(args.source_url)
        raw = (json.dumps(payload, sort_keys=True, default=str, ensure_ascii=True, indent=2) + "\n").encode()
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as output:
            output.write(raw)
        print(json.dumps({"snapshot": payload["snapshot"], "sha256": hashlib.sha256(raw).hexdigest(), "counts": counts}, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"SNAPSHOT_BLOCKED:{type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
