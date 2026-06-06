"""Tests for conflict-safe shopping category V1 migration."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.shopping_category_migration import (  # noqa: E402
    _MIGRATION_FLAG,
    migrate_shopping_categories_v1,
    shopping_list_items_pg_sql,
)


def _make_engine():
    """SQLite engine mirroring the production tables touched by the migration."""
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE shopping_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug VARCHAR(64) NOT NULL,
                    name VARCHAR(120) NOT NULL,
                    icon VARCHAR(16),
                    is_food BOOLEAN NOT NULL DEFAULT 1,
                    is_system BOOLEAN NOT NULL DEFAULT 0,
                    user_id INTEGER,
                    family_id INTEGER,
                    created_at TEXT
                )
                """
            )
        )
        # Mirror the production unique constraints that caused the outage.
        conn.execute(
            text(
                "CREATE UNIQUE INDEX uq_sc_user_slug "
                "ON shopping_categories (user_id, slug)"
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX uq_sc_family_slug "
                "ON shopping_categories (family_id, slug)"
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE family_pantry_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    family_id INTEGER,
                    name VARCHAR(120),
                    category VARCHAR(64) DEFAULT 'другое',
                    quantity VARCHAR(80),
                    unit VARCHAR(32) DEFAULT ''
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE family_shopping_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    family_id INTEGER,
                    menu_selection_id INTEGER,
                    items TEXT,
                    updated_at TEXT
                )
                """
            )
        )
    return engine


def _insert_category(conn, slug: str, name: str, user_id: int | None = None) -> None:
    conn.execute(
        text(
            "INSERT INTO shopping_categories (slug, name, is_system, user_id) "
            "VALUES (:slug, :name, 1, :user_id)"
        ),
        {"slug": slug, "name": name, "user_id": user_id},
    )


def _user_slugs(engine, user_id: int) -> list[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT slug FROM shopping_categories "
                "WHERE user_id = :uid ORDER BY id"
            ),
            {"uid": user_id},
        ).fetchall()
    return [row[0] for row in rows]


def test_rename_when_only_old_slug_present():
    engine = _make_engine()
    with engine.begin() as conn:
        _insert_category(conn, "бытовые", "Бытовые", user_id=1)

    with engine.begin() as conn:
        migrate_shopping_categories_v1(conn)

    assert _user_slugs(engine, 1) == ["быт_уборка"]


def test_collapse_when_old_and_new_slug_coexist():
    engine = _make_engine()
    with engine.begin() as conn:
        _insert_category(conn, "бытовые", "Бытовые", user_id=1)
        _insert_category(conn, "быт_уборка", "Быт и уборка", user_id=1)

    # Must not raise on the unique (user_id, slug) constraint.
    with engine.begin() as conn:
        migrate_shopping_categories_v1(conn)

    assert _user_slugs(engine, 1) == ["быт_уборка"]


def test_rerun_is_idempotent_and_safe():
    engine = _make_engine()
    with engine.begin() as conn:
        _insert_category(conn, "бытовые", "Бытовые", user_id=1)

    with engine.begin() as conn:
        migrate_shopping_categories_v1(conn)

    # Clear the guard flag to force the core SQL to run a second time.
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM app_schema_flags WHERE key = :key"),
            {"key": _MIGRATION_FLAG},
        )
        migrate_shopping_categories_v1(conn)

    assert _user_slugs(engine, 1) == ["быт_уборка"]


def test_jsonb_items_category_is_migrated():
    engine = _make_engine()
    payload = json.dumps([{"name": "Порошок", "category": "бытовые"}], ensure_ascii=False)
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO family_shopping_lists (id, items) VALUES (1, :items)"),
            {"items": payload},
        )

    with engine.begin() as conn:
        migrate_shopping_categories_v1(conn)

    with engine.connect() as conn:
        raw = conn.execute(
            text("SELECT items FROM family_shopping_lists WHERE id = 1")
        ).scalar()
    items = json.loads(raw)
    assert items[0]["category"] == "быт_уборка"
    assert items[0]["name"] == "Порошок"


def test_pantry_item_category_is_migrated():
    engine = _make_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO family_pantry_items (user_id, name, category, quantity) "
                "VALUES (1, 'Порошок', 'бытовые', '1')"
            )
        )

    with engine.begin() as conn:
        migrate_shopping_categories_v1(conn)

    with engine.connect() as conn:
        category = conn.execute(
            text("SELECT category FROM family_pantry_items WHERE user_id = 1")
        ).scalar()
    assert category == "быт_уборка"


def test_jsonb_sql_uses_cast_not_double_colon_bind():
    sql = shopping_list_items_pg_sql()
    assert ":new_slug::text" not in sql
    assert "CAST(:new_slug AS text)" in sql
