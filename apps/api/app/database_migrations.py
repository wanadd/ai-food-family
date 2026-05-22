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
        "ALTER TABLE family_pantry_items ADD COLUMN IF NOT EXISTS source VARCHAR(32) NOT NULL DEFAULT 'manual'",
        "ALTER TABLE family_pantry_items ADD COLUMN IF NOT EXISTS unit VARCHAR(32) NOT NULL DEFAULT ''",
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
        """
        CREATE TABLE IF NOT EXISTS family_invites (
            id SERIAL PRIMARY KEY,
            family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
            invited_phone_normalized VARCHAR(32) NOT NULL,
            invited_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            invited_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status VARCHAR(16) NOT NULL DEFAULT 'pending',
            invite_token VARCHAR(64) NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            accepted_at TIMESTAMPTZ,
            declined_at TIMESTAMPTZ
        );
        """,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_family_invite_pending_phone
        ON family_invites (family_id, invited_phone_normalized)
        WHERE status = 'pending';
        """,
        "DROP INDEX IF EXISTS uq_family_invite_pending_phone;",
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_family_invite_pending_phone
        ON family_invites (family_id, invited_phone_normalized)
        WHERE status = 'pending' AND invited_phone_normalized != '__link__';
        """,
        "CREATE INDEX IF NOT EXISTS ix_family_invites_token ON family_invites (invite_token);",
        """
        CREATE TABLE IF NOT EXISTS telegram_bot_sessions (
            telegram_id BIGINT PRIMARY KEY,
            state VARCHAR(64) NOT NULL DEFAULT '',
            invite_token VARCHAR(64),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
