"""Lightweight schema upgrades for databases created before personal mode."""

from sqlalchemy import Engine, text


def run_schema_migrations(engine: Engine) -> None:
    statements = [
        # Menu selections: personal scope uses user_id + family_id IS NULL
        "ALTER TABLE family_menu_selections ADD COLUMN IF NOT EXISTS user_id INTEGER",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'family_menu_selections_user_id_fkey'
            ) THEN
                ALTER TABLE family_menu_selections
                ADD CONSTRAINT family_menu_selections_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
            END IF;
        END $$;
        """,
        "ALTER TABLE family_menu_selections ALTER COLUMN family_id DROP NOT NULL",
        "CREATE INDEX IF NOT EXISTS ix_family_menu_selections_user_id ON family_menu_selections (user_id)",
        # Shopping lists
        "ALTER TABLE family_shopping_lists ADD COLUMN IF NOT EXISTS user_id INTEGER",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'family_shopping_lists_user_id_fkey'
            ) THEN
                ALTER TABLE family_shopping_lists
                ADD CONSTRAINT family_shopping_lists_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
            END IF;
        END $$;
        """,
        "ALTER TABLE family_shopping_lists ALTER COLUMN family_id DROP NOT NULL",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_family_shopping_lists_user_id ON family_shopping_lists (user_id)",
        # Pantry
        "ALTER TABLE family_pantry_items ADD COLUMN IF NOT EXISTS user_id INTEGER",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'family_pantry_items_user_id_fkey'
            ) THEN
                ALTER TABLE family_pantry_items
                ADD CONSTRAINT family_pantry_items_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
            END IF;
        END $$;
        """,
        "ALTER TABLE family_pantry_items ALTER COLUMN family_id DROP NOT NULL",
        "CREATE INDEX IF NOT EXISTS ix_family_pantry_items_user_id ON family_pantry_items (user_id)",
        # User preferences (active app mode)
        """
        CREATE TABLE IF NOT EXISTS user_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            active_mode VARCHAR(16) NOT NULL DEFAULT 'personal',
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_user_preferences_user_id ON user_preferences (user_id)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(32)",
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
