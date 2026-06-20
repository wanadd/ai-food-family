"""One-time data migration: legacy shopping category slugs → PlanAm V1.

Conflict-safe and idempotent. Re-running the migration must never raise
(e.g. on a unique ``(user_id, slug)`` collision) and must not duplicate data.

Strategy per ``old_slug → new_slug`` pair:
  1. Migrate dependent data (pantry items, shopping list JSONB items).
  2. Drop legacy ``shopping_categories`` rows that would collide with an
     already-existing target ``new_slug`` row in the same scope.
  3. Collapse duplicate legacy rows in the same scope (keep lowest id).
  4. Rename the remaining ``old_slug`` rows to ``new_slug``.

If ``old_slug`` is already gone, every step is a safe no-op.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.services.categories_v1 import (
    DEPRECATED_SYSTEM_SLUGS,
    LEGACY_SLUG_MAP,
    normalize_category_slug,
)

logger = logging.getLogger(__name__)

_MIGRATION_FLAG = "shopping_categories_v1_migrated"


def _migration_table_sql() -> str:
    # CURRENT_TIMESTAMP is portable across PostgreSQL and SQLite (unlike NOW()).
    return """
        CREATE TABLE IF NOT EXISTS app_schema_flags (
            key VARCHAR(64) PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """


def _is_applied(connection: Connection) -> bool:
    connection.execute(text(_migration_table_sql()))
    row = connection.execute(
        text("SELECT 1 FROM app_schema_flags WHERE key = :key"),
        {"key": _MIGRATION_FLAG},
    ).first()
    return row is not None


def _mark_applied(connection: Connection) -> None:
    connection.execute(
        text(
            "INSERT INTO app_schema_flags (key) VALUES (:key) "
            "ON CONFLICT (key) DO NOTHING"
        ),
        {"key": _MIGRATION_FLAG},
    )


def slug_update_pairs() -> list[tuple[str, str]]:
    """Return ``(old_slug, new_slug)`` pairs, excluding identity mappings."""
    updates: dict[str, str] = dict(LEGACY_SLUG_MAP)
    for deprecated in DEPRECATED_SYSTEM_SLUGS:
        updates.setdefault(deprecated, normalize_category_slug(deprecated))
    return [(old, new) for old, new in updates.items() if new and old != new]


def shopping_list_items_pg_sql() -> str:
    """PostgreSQL JSONB rewrite of ``items[].category``.

    Uses ``CAST(:new_slug AS text)`` — the legacy ``:new_slug::text`` form is
    parsed incorrectly by SQLAlchemy ``text()`` and breaks PostgreSQL.
    """
    return """
        UPDATE family_shopping_lists
        SET items = (
            SELECT COALESCE(
                jsonb_agg(
                    CASE
                        WHEN elem ? 'category'
                             AND elem->>'category' = :old_slug
                        THEN jsonb_set(
                            elem,
                            '{category}',
                            to_jsonb(CAST(:new_slug AS text))
                        )
                        ELSE elem
                    END
                ),
                '[]'::jsonb
            )
            FROM jsonb_array_elements(
                CASE
                    WHEN jsonb_typeof(items) = 'array' THEN items
                    ELSE '[]'::jsonb
                END
            ) AS elem
        )
        WHERE items IS NOT NULL
          AND items::text LIKE :like_pattern
    """


def _migrate_category_rows(connection: Connection, old_slug: str, new_slug: str) -> None:
    """Conflict-safe rename of ``shopping_categories`` rows for one pair."""
    # 1. Drop legacy rows that collide with an existing target row in scope.
    connection.execute(
        text(
            """
            DELETE FROM shopping_categories
            WHERE slug = :old_slug
              AND EXISTS (
                  SELECT 1 FROM shopping_categories b
                  WHERE b.slug = :new_slug
                    AND b.id <> shopping_categories.id
                    AND (
                        (shopping_categories.user_id IS NOT NULL
                         AND b.user_id = shopping_categories.user_id)
                        OR (shopping_categories.family_id IS NOT NULL
                            AND b.family_id = shopping_categories.family_id)
                        OR (shopping_categories.user_id IS NULL
                            AND shopping_categories.family_id IS NULL
                            AND b.user_id IS NULL
                            AND b.family_id IS NULL)
                    )
              )
            """
        ),
        {"old_slug": old_slug, "new_slug": new_slug},
    )

    # 2. Collapse duplicate legacy rows in the same scope (keep lowest id).
    connection.execute(
        text(
            """
            DELETE FROM shopping_categories
            WHERE slug = :old_slug
              AND EXISTS (
                  SELECT 1 FROM shopping_categories b
                  WHERE b.slug = :old_slug
                    AND b.id < shopping_categories.id
                    AND (
                        (shopping_categories.user_id IS NOT NULL
                         AND b.user_id = shopping_categories.user_id)
                        OR (shopping_categories.family_id IS NOT NULL
                            AND b.family_id = shopping_categories.family_id)
                        OR (shopping_categories.user_id IS NULL
                            AND shopping_categories.family_id IS NULL
                            AND b.user_id IS NULL
                            AND b.family_id IS NULL)
                    )
              )
            """
        ),
        {"old_slug": old_slug},
    )

    # 3. Rename the survivors — now guaranteed conflict-free in scope.
    connection.execute(
        text(
            "UPDATE shopping_categories SET slug = :new_slug WHERE slug = :old_slug"
        ),
        {"old_slug": old_slug, "new_slug": new_slug},
    )


def _migrate_pantry_items(connection: Connection, old_slug: str, new_slug: str) -> None:
    connection.execute(
        text(
            "UPDATE family_pantry_items SET category = :new_slug "
            "WHERE category = :old_slug"
        ),
        {"old_slug": old_slug, "new_slug": new_slug},
    )


def _migrate_shopping_list_items_python(
    connection: Connection, mapping: dict[str, str]
) -> None:
    """Portable JSONB-items rewrite for non-PostgreSQL backends (tests)."""
    rows = connection.execute(
        text("SELECT id, items FROM family_shopping_lists")
    ).fetchall()
    for row in rows:
        raw = row._mapping["items"]
        items = raw
        if isinstance(items, (str, bytes)):
            try:
                items = json.loads(items)
            except (ValueError, TypeError):
                continue
        if not isinstance(items, list):
            continue
        changed = False
        for item in items:
            if isinstance(item, dict) and "category" in item:
                current = item.get("category")
                target = mapping.get(current)
                if target and target != current:
                    item["category"] = target
                    changed = True
        if changed:
            connection.execute(
                text("UPDATE family_shopping_lists SET items = :items WHERE id = :id"),
                {
                    "items": json.dumps(items, ensure_ascii=False),
                    "id": row._mapping["id"],
                },
            )


def _migrate_shopping_list_items(
    connection: Connection, pairs: list[tuple[str, str]]
) -> None:
    if connection.dialect.name == "postgresql":
        statement = text(shopping_list_items_pg_sql())
        for old_slug, new_slug in pairs:
            connection.execute(
                statement,
                {
                    "old_slug": old_slug,
                    "new_slug": new_slug,
                    "like_pattern": f'%"{old_slug}"%',
                },
            )
    else:
        _migrate_shopping_list_items_python(connection, dict(pairs))


def _cleanup_deprecated(connection: Connection) -> None:
    for deprecated in DEPRECATED_SYSTEM_SLUGS:
        remaining = connection.execute(
            text("SELECT COUNT(*) FROM shopping_categories WHERE slug = :slug"),
            {"slug": deprecated},
        ).scalar()
        if remaining:
            logger.warning(
                "Deprecated category slug %r still has %s rows; deleting",
                deprecated,
                remaining,
            )
            connection.execute(
                text("DELETE FROM shopping_categories WHERE slug = :slug"),
                {"slug": deprecated},
            )


def migrate_shopping_categories_v1(connection: Connection) -> None:
    """Migrate pantry, shopping list items, and category rows to V1 slugs.

    Idempotent: a per-flag guard short-circuits repeat runs, and every SQL
    step is conflict-safe so re-running the core logic never raises.
    """
    if _is_applied(connection):
        return

    pairs = slug_update_pairs()
    logger.info(
        "Applying shopping categories V1 migration (%d slug maps)", len(pairs)
    )

    for old_slug, new_slug in pairs:
        _migrate_pantry_items(connection, old_slug, new_slug)
        _migrate_category_rows(connection, old_slug, new_slug)

    _migrate_shopping_list_items(connection, pairs)
    _cleanup_deprecated(connection)

    _mark_applied(connection)
    logger.info("Shopping categories V1 migration complete")
