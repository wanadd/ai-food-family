"""One-time data migration: legacy shopping category slugs → PlanAm V1."""

from __future__ import annotations

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
    return """
        CREATE TABLE IF NOT EXISTS app_schema_flags (
            key VARCHAR(64) PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
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
            "INSERT INTO app_schema_flags (key) VALUES (:key) ON CONFLICT (key) DO NOTHING"
        ),
        {"key": _MIGRATION_FLAG},
    )


def _slug_updates() -> dict[str, str]:
    updates = dict(LEGACY_SLUG_MAP)
    for deprecated in DEPRECATED_SYSTEM_SLUGS:
        updates[deprecated] = normalize_category_slug(deprecated)
    return updates


def migrate_shopping_categories_v1(connection: Connection) -> None:
    """Migrate pantry, shopping list items, and category rows to V1 slugs."""
    if _is_applied(connection):
        return

    updates = _slug_updates()
    logger.info("Applying shopping categories V1 migration (%d slug maps)", len(updates))

    for old_slug, new_slug in updates.items():
        if old_slug == new_slug:
            continue

        connection.execute(
            text(
                "UPDATE shopping_categories SET slug = :new_slug "
                "WHERE slug = :old_slug"
            ),
            {"old_slug": old_slug, "new_slug": new_slug},
        )

        connection.execute(
            text(
                "UPDATE family_pantry_items SET category = :new_slug "
                "WHERE category = :old_slug"
            ),
            {"old_slug": old_slug, "new_slug": new_slug},
        )

        # JSONB array: rewrite item.category inside family_shopping_lists.items
        connection.execute(
            text(
                """
                UPDATE family_shopping_lists
                SET items = (
                    SELECT COALESCE(
                        jsonb_agg(
                            CASE
                                WHEN elem ? 'category'
                                     AND elem->>'category' = :old_slug
                                THEN jsonb_set(elem, '{category}', to_jsonb(:new_slug::text))
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
            ),
            {
                "old_slug": old_slug,
                "new_slug": new_slug,
                "like_pattern": f'%"{old_slug}"%',
            },
        )

    # Remove forbidden slug rows if any remain (should be zero after updates).
    for deprecated in DEPRECATED_SYSTEM_SLUGS:
        remaining = connection.execute(
            text("SELECT COUNT(*) FROM shopping_categories WHERE slug = :slug"),
            {"slug": deprecated},
        ).scalar()
        if remaining:
            logger.warning(
                "Deprecated category slug %r still has %s rows after migration",
                deprecated,
                remaining,
            )
            connection.execute(
                text("DELETE FROM shopping_categories WHERE slug = :slug"),
                {"slug": deprecated},
            )

    _mark_applied(connection)
    logger.info("Shopping categories V1 migration complete")
