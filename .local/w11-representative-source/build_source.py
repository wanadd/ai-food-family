from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine, text


DB = "postgresql+psycopg2://postgres@127.0.0.1:55440/planam_w11_raw_source_tmp"
OUT = Path(__file__).with_name("representative.source.json")


def rows(conn, query: str, params: dict | None = None) -> list[dict]:
    return [dict(row) for row in conn.execute(text(query), params or {}).mappings()]


engine = create_engine(DB)
with engine.connect() as conn:
    users = rows(conn, """
        select id, concat_ws(' ', first_name, last_name) as display_name,
               'telegram' as provider, 'synthetic_provider_' || id as provider_subject,
               is_deleted as deleted
        from users order by id
    """)
    families = rows(conn, "select id, name from families order by id")
    family_members = rows(conn, "select id, family_id, user_id, role from family_members order by id")
    profiles = rows(conn, """
        select id, user_id, coalesce(allergies, '[]'::jsonb) as allergies,
               case when coalesce(medical_restrictions, '') = '' then null
                    else 'SYNTHETIC_AMBIGUOUS_MEDICAL_NOTE' end as medical_notes,
               age
        from user_profiles order by id
    """)
    recipes = rows(conn, """
        select id, coalesce(display_title, title, 'Untitled') as title,
               false as gold_v3_validated
        from recipes order by id
    """)
    events = rows(conn, """
        select id, allergies_note from event_plans order by id
    """)
    notifications = rows(conn, """
        select id, status from care_notifications order by id
    """)
    admin_sessions = rows(conn, """
        select id, session_token from admin_sessions order by id
    """)

    # Preserve real row cardinalities for non-promotable domains without
    # carrying their business payloads into the W10 source contract.
    domain_tables = {
        "shopping": "family_shopping_lists",
        "pantry": "family_pantry_items",
        "receipts": "recipe_import_jobs",
        "consumption": "meal_consumption_logs",
        "cooking": "cooking_batches",
        "notifications": "care_notifications",
    }
    domain_rows = {}
    for domain, table in domain_tables.items():
        domain_rows[domain] = [{"id": row["id"]} for row in rows(conn, f"select id from {table} order by id")]

source = {
    "snapshot": "planam-production-representative-20260928-sanitized-v1",
    "users": users,
    "families": families,
    "family_members": family_members,
    "profiles": profiles,
    "recipes": recipes,
    "events": events,
    "notifications": notifications,
    "admin_sessions": admin_sessions,
    **domain_rows,
}
OUT.write_text(json.dumps(source, ensure_ascii=True, sort_keys=True, indent=2), encoding="utf-8")
print(f"SOURCE_JSON=PASS records={sum(len(value) for value in source.values() if isinstance(value, list))}")
