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
        CREATE TABLE IF NOT EXISTS shopping_categories (
            id SERIAL PRIMARY KEY,
            slug VARCHAR(64) NOT NULL,
            name VARCHAR(120) NOT NULL,
            icon VARCHAR(16),
            is_food BOOLEAN NOT NULL DEFAULT TRUE,
            is_system BOOLEAN NOT NULL DEFAULT FALSE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_shopping_categories_user ON shopping_categories (user_id);",
        "CREATE INDEX IF NOT EXISTS ix_shopping_categories_family ON shopping_categories (family_id);",
        "ALTER TABLE family_pantry_items ADD COLUMN IF NOT EXISTS category VARCHAR(64) NOT NULL DEFAULT 'продукты';",
        "ALTER TABLE family_pantry_items ADD COLUMN IF NOT EXISTS note VARCHAR(200);",
        "ALTER TABLE family_pantry_items ALTER COLUMN expires_at DROP NOT NULL;",
        """
        CREATE TABLE IF NOT EXISTS telegram_bot_sessions (
            telegram_id BIGINT PRIMARY KEY,
            state VARCHAR(64) NOT NULL DEFAULT '',
            invite_token VARCHAR(64),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        # Nutrition profile (stage 2)
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS age INTEGER",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS gender VARCHAR(24)",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS height_cm INTEGER",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS weight_kg DOUBLE PRECISION",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS nutrition_goal VARCHAR(32)",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS activity_level VARCHAR(32)",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS medical_restrictions TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS banned_foods TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS dish_complexity VARCHAR(32)",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS pro_data JSONB NOT NULL DEFAULT '{}'",
        # Family members: virtual participants and nutrition
        "ALTER TABLE family_members ADD COLUMN IF NOT EXISTS is_virtual BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE family_members ADD COLUMN IF NOT EXISTS virtual_kind VARCHAR(32)",
        "ALTER TABLE family_members ADD COLUMN IF NOT EXISTS allow_admin_profile_edit BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE family_members ADD COLUMN IF NOT EXISTS nutrition_profile JSONB NOT NULL DEFAULT '{}'",
        """
        UPDATE family_members
        SET is_virtual = TRUE
        WHERE user_id IS NULL AND is_virtual = FALSE;
        """,
        # Subscriptions & AMA (stage 7)
        """
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id SERIAL PRIMARY KEY,
            code VARCHAR(32) NOT NULL UNIQUE,
            name VARCHAR(120) NOT NULL,
            price_rub INTEGER NOT NULL DEFAULT 0,
            max_profiles INTEGER NOT NULL DEFAULT 1,
            monthly_menu_generations INTEGER,
            monthly_ams INTEGER NOT NULL DEFAULT 0,
            features JSONB NOT NULL DEFAULT '{}',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE SET NULL,
            plan_code VARCHAR(32) NOT NULL,
            status VARCHAR(24) NOT NULL DEFAULT 'active',
            started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            trial_ends_at TIMESTAMPTZ,
            current_period_ends_at TIMESTAMPTZ,
            menu_generations_used INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_user_subscriptions_user_id ON user_subscriptions (user_id);",
        """
        CREATE TABLE IF NOT EXISTS ama_wallets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            balance INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_ama_wallet_user ON ama_wallets (user_id) WHERE family_id IS NULL;",
        """
        CREATE TABLE IF NOT EXISTS ama_transactions (
            id SERIAL PRIMARY KEY,
            wallet_id INTEGER NOT NULL REFERENCES ama_wallets(id) ON DELETE CASCADE,
            amount INTEGER NOT NULL,
            type VARCHAR(16) NOT NULL,
            reason VARCHAR(64) NOT NULL,
            metadata_json JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS ai_usage_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE SET NULL,
            action_type VARCHAR(64) NOT NULL,
            ams_spent INTEGER NOT NULL DEFAULT 0,
            model VARCHAR(64),
            input_tokens INTEGER,
            output_tokens INTEGER,
            estimated_cost DOUBLE PRECISION,
            metadata_json JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_ai_usage_logs_user_id ON ai_usage_logs (user_id);",
        # AI Care System (stage 8)
        """
        CREATE TABLE IF NOT EXISTS care_settings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            water_enabled BOOLEAN NOT NULL DEFAULT FALSE,
            protein_enabled BOOLEAN NOT NULL DEFAULT FALSE,
            menu_enabled BOOLEAN NOT NULL DEFAULT TRUE,
            shopping_enabled BOOLEAN NOT NULL DEFAULT TRUE,
            pantry_enabled BOOLEAN NOT NULL DEFAULT TRUE,
            progress_enabled BOOLEAN NOT NULL DEFAULT FALSE,
            family_enabled BOOLEAN NOT NULL DEFAULT FALSE,
            pro_enabled BOOLEAN NOT NULL DEFAULT FALSE,
            care_level VARCHAR(16) NOT NULL DEFAULT 'standard',
            quiet_hours_start VARCHAR(5),
            quiet_hours_end VARCHAR(5),
            timezone VARCHAR(64),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS care_notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE SET NULL,
            type VARCHAR(32) NOT NULL,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            payload JSONB,
            status VARCHAR(16) NOT NULL DEFAULT 'pending',
            scheduled_at TIMESTAMPTZ,
            sent_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_care_notifications_user_id ON care_notifications (user_id);",
        """
        CREATE TABLE IF NOT EXISTS care_events (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE SET NULL,
            event_type VARCHAR(64) NOT NULL,
            source VARCHAR(64) NOT NULL DEFAULT 'care',
            payload JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_care_events_user_id ON care_events (user_id);",
        # PRO progress (stage 9)
        """
        CREATE TABLE IF NOT EXISTS progress_entries (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            person_id INTEGER REFERENCES family_members(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            weight_kg DOUBLE PRECISION,
            body_fat_percent DOUBLE PRECISION,
            waist_cm DOUBLE PRECISION,
            chest_cm DOUBLE PRECISION,
            hips_cm DOUBLE PRECISION,
            notes TEXT,
            recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_progress_entries_user_id ON progress_entries (user_id);",
        """
        CREATE TABLE IF NOT EXISTS training_entries (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            person_id INTEGER REFERENCES family_members(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            training_type VARCHAR(64) NOT NULL,
            duration_minutes INTEGER,
            intensity VARCHAR(16) NOT NULL DEFAULT 'medium',
            calories_burned INTEGER,
            notes TEXT,
            training_date DATE NOT NULL DEFAULT CURRENT_DATE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_training_entries_user_id ON training_entries (user_id);",
        """
        CREATE TABLE IF NOT EXISTS nutrition_targets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            person_id INTEGER REFERENCES family_members(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            calories_target INTEGER,
            protein_target_g INTEGER,
            fat_target_g INTEGER,
            carbs_target_g INTEGER,
            fiber_target_g INTEGER,
            water_target_ml INTEGER,
            goal_type VARCHAR(32),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_nutrition_targets_user_id ON nutrition_targets (user_id);",
        # Per-meal cook reminders
        "ALTER TABLE user_notification_settings ADD COLUMN IF NOT EXISTS cook_breakfast_enabled BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE user_notification_settings ADD COLUMN IF NOT EXISTS cook_lunch_enabled BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE user_notification_settings ADD COLUMN IF NOT EXISTS cook_dinner_enabled BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE user_notification_settings ADD COLUMN IF NOT EXISTS cook_breakfast_time VARCHAR(5) NOT NULL DEFAULT '08:00'",
        "ALTER TABLE user_notification_settings ADD COLUMN IF NOT EXISTS cook_lunch_time VARCHAR(5) NOT NULL DEFAULT '13:00'",
        "ALTER TABLE user_notification_settings ADD COLUMN IF NOT EXISTS cook_dinner_time VARCHAR(5) NOT NULL DEFAULT '18:00'",
        "ALTER TABLE user_notification_settings ADD COLUMN IF NOT EXISTS last_breakfast_sent_date DATE",
        "ALTER TABLE user_notification_settings ADD COLUMN IF NOT EXISTS last_lunch_sent_date DATE",
        "ALTER TABLE user_notification_settings ADD COLUMN IF NOT EXISTS last_dinner_sent_date DATE",
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
