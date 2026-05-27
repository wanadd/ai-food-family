"""Lightweight schema upgrades for databases created before personal mode."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Connection, Engine, text

# Recipe Engine v1 tables are created only via SQL below (not SQLAlchemy create_all).
RECIPE_ENGINE_TABLES: frozenset[str] = frozenset(
    {
        "recipe_collections",
        "collection_recipes",
        "recipe_history",
        "family_recipe_preferences",
        "recipe_scenarios",
        "recipe_explanations",
    }
)

# Stable advisory lock id for multi-worker startup (uvicorn --workers N).
SCHEMA_ADVISORY_LOCK_ID = 739_284_651


def _create_table_if_missing(table_name: str, create_sql: str) -> str:
    """Idempotent CREATE TABLE (avoids SERIAL sequence errors on duplicate DDL)."""
    body = create_sql.strip()
    if body.endswith(";"):
        body = body[:-1]
    return f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = '{table_name}'
            ) THEN
                {body};
            END IF;
        END $$;
        """


def _schema_statements() -> list[str]:
    return [
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
        """
        CREATE TABLE IF NOT EXISTS meal_leftovers (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            dish_name VARCHAR(200) NOT NULL,
            portions_remaining INTEGER NOT NULL DEFAULT 1,
            valid_until DATE,
            note VARCHAR(200),
            added_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_meal_leftovers_user_id ON meal_leftovers (user_id);",
        "CREATE INDEX IF NOT EXISTS ix_meal_leftovers_family_id ON meal_leftovers (family_id);",
        # Legal consents
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS accepted_terms BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS accepted_privacy BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS accepted_personal_data BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS legal_accepted_at TIMESTAMPTZ",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS legal_documents_version VARCHAR(32)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_skipped BOOLEAN NOT NULL DEFAULT FALSE",
        """
        UPDATE users SET
            accepted_terms = TRUE,
            accepted_privacy = TRUE,
            accepted_personal_data = TRUE,
            legal_documents_version = '2025-05-stub-v1',
            legal_accepted_at = COALESCE(legal_accepted_at, NOW())
        WHERE phone_number IS NOT NULL AND phone_number <> '';
        """,
        "ALTER TABLE telegram_bot_sessions ADD COLUMN IF NOT EXISTS payload_json JSONB NOT NULL DEFAULT '{}'",
        # Recipe catalog extensions
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS cuisine VARCHAR(64)",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS cooking_time_minutes INTEGER NOT NULL DEFAULT 30",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS calories_per_serving DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS protein_g DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS fat_g DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS carbs_g DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS fiber_g DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS sugar_g DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS source_type VARCHAR(16) NOT NULL DEFAULT 'manual'",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS source_url VARCHAR(512)",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS image_url VARCHAR(512)",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS is_drink BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS is_alcoholic BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS alcohol_percent DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS caffeine_mg DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS suitable_for_children BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS suitable_for_sport BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS suitable_for_event BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "UPDATE recipes SET cooking_time_minutes = prep_time_minutes WHERE cooking_time_minutes IS NULL OR cooking_time_minutes = 30",
        """
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
            name VARCHAR(120) NOT NULL,
            quantity VARCHAR(32) NOT NULL DEFAULT '1',
            unit VARCHAR(32) NOT NULL DEFAULT 'шт',
            category VARCHAR(32) NOT NULL DEFAULT 'other',
            is_optional BOOLEAN NOT NULL DEFAULT FALSE,
            notes VARCHAR(200)
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_recipe_ingredients_recipe_id ON recipe_ingredients (recipe_id);",
        """
        CREATE TABLE IF NOT EXISTS recipe_steps (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
            step_number INTEGER NOT NULL DEFAULT 1,
            text TEXT NOT NULL
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_recipe_steps_recipe_id ON recipe_steps (recipe_id);",
        """
        CREATE TABLE IF NOT EXISTS recipe_tags (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
            tag VARCHAR(64) NOT NULL
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_recipe_tags_recipe_id ON recipe_tags (recipe_id);",
        "CREATE INDEX IF NOT EXISTS ix_recipe_tags_tag ON recipe_tags (tag);",
        """
        CREATE TABLE IF NOT EXISTS recipe_allergens (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
            allergen VARCHAR(64) NOT NULL
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_recipe_allergens_recipe_id ON recipe_allergens (recipe_id);",
        """
        CREATE TABLE IF NOT EXISTS recipe_restrictions (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
            restriction VARCHAR(64) NOT NULL
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_recipe_restrictions_recipe_id ON recipe_restrictions (recipe_id);",
        """
        CREATE TABLE IF NOT EXISTS recipe_ratings (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            rating INTEGER,
            is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
            cooked_count INTEGER NOT NULL DEFAULT 0,
            last_cooked_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_recipe_rating_user_recipe UNIQUE (user_id, recipe_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS recipe_import_jobs (
            id SERIAL PRIMARY KEY,
            source_name VARCHAR(64) NOT NULL,
            source_url VARCHAR(512),
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            imported_count INTEGER NOT NULL DEFAULT 0,
            failed_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS event_plans (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            title VARCHAR(200) NOT NULL,
            event_type VARCHAR(64) NOT NULL,
            guests_count INTEGER NOT NULL DEFAULT 4,
            budget VARCHAR(32),
            theme VARCHAR(120),
            cuisine VARCHAR(64),
            religious_restriction VARCHAR(32) NOT NULL DEFAULT 'none',
            fasting_mode VARCHAR(32) NOT NULL DEFAULT 'none',
            drink_menu_mode VARCHAR(32) NOT NULL DEFAULT 'non_alcoholic',
            alcohol_enabled BOOLEAN NOT NULL DEFAULT FALSE,
            kids_drinks_enabled BOOLEAN NOT NULL DEFAULT TRUE,
            allergies_note TEXT,
            plan_data JSONB NOT NULL DEFAULT '{}',
            estimated_cost_rub INTEGER,
            status VARCHAR(32) NOT NULL DEFAULT 'draft',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_event_plans_user_id ON event_plans (user_id);",
        "CREATE INDEX IF NOT EXISTS ix_event_plans_family_id ON event_plans (family_id);",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS goal_details JSONB NOT NULL DEFAULT '{}'",
        "ALTER TABLE meal_leftovers ADD COLUMN IF NOT EXISTS leftover_status VARCHAR(32) NOT NULL DEFAULT 'active'",
        """
        CREATE TABLE IF NOT EXISTS meal_eating_schedules (
            id SERIAL PRIMARY KEY,
            family_member_id INTEGER NOT NULL UNIQUE REFERENCES family_members(id) ON DELETE CASCADE,
            family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
            schedule_json JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_meal_eating_schedules_family_id ON meal_eating_schedules (family_id);",
        """
        CREATE TABLE IF NOT EXISTS meal_checkins (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            family_member_id INTEGER REFERENCES family_members(id) ON DELETE SET NULL,
            meal_plan_id INTEGER,
            recipe_id INTEGER REFERENCES recipes(id) ON DELETE SET NULL,
            meal_type VARCHAR(16) NOT NULL,
            planned_date DATE NOT NULL,
            planned_servings INTEGER,
            actual_status VARCHAR(32) NOT NULL DEFAULT 'planned',
            actual_description VARCHAR(500),
            actual_calories DOUBLE PRECISION,
            actual_protein_g DOUBLE PRECISION,
            actual_fat_g DOUBLE PRECISION,
            actual_carbs_g DOUBLE PRECISION,
            leftover_servings_delta INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_meal_checkins_family_date ON meal_checkins (family_id, planned_date);",
        "CREATE INDEX IF NOT EXISTS ix_meal_checkins_user_date ON meal_checkins (user_id, planned_date);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS blocked_at TIMESTAMPTZ",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS blocked_reason VARCHAR(500)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_by_admin_id INTEGER REFERENCES users(id) ON DELETE SET NULL",
        "ALTER TABLE families ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE families ADD COLUMN IF NOT EXISTS blocked_at TIMESTAMPTZ",
        "ALTER TABLE families ADD COLUMN IF NOT EXISTS blocked_reason VARCHAR(500)",
        "ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS metadata_json JSONB",
        """
        CREATE TABLE IF NOT EXISTS admin_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            telegram_id BIGINT NOT NULL,
            session_token VARCHAR(64) NOT NULL UNIQUE,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            last_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_admin_sessions_user_id ON admin_sessions (user_id);",
        "CREATE INDEX IF NOT EXISTS ix_admin_sessions_telegram_id ON admin_sessions (telegram_id);",
        "CREATE INDEX IF NOT EXISTS ix_admin_sessions_token ON admin_sessions (session_token);",
        """
        CREATE TABLE IF NOT EXISTS admin_login_attempts (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            success BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_admin_login_attempts_telegram_id ON admin_login_attempts (telegram_id);",
        """
        CREATE TABLE IF NOT EXISTS admin_actions (
            id SERIAL PRIMARY KEY,
            admin_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            action_type VARCHAR(64) NOT NULL,
            target_type VARCHAR(32),
            target_id INTEGER,
            metadata_json JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_admin_actions_admin_user_id ON admin_actions (admin_user_id);",
        """
        CREATE TABLE IF NOT EXISTS admin_error_logs (
            id SERIAL PRIMARY KEY,
            error_type VARCHAR(32) NOT NULL DEFAULT 'unknown',
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            family_id INTEGER REFERENCES families(id) ON DELETE SET NULL,
            endpoint VARCHAR(512),
            message TEXT NOT NULL DEFAULT '',
            stack TEXT,
            status INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_admin_error_logs_created_at ON admin_error_logs (created_at);",
        """
        CREATE TABLE IF NOT EXISTS deferred_nutrition_advice (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            advice_key VARCHAR(120) NOT NULL,
            title VARCHAR(200) NOT NULL,
            body TEXT NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'deferred',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_deferred_advice_user ON deferred_nutrition_advice (user_id);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_deferred_advice_user_key ON deferred_nutrition_advice (user_id, advice_key) WHERE family_id IS NULL;",
        """
        CREATE TABLE IF NOT EXISTS water_intake_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            log_date DATE NOT NULL,
            amount_ml INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_water_intake_user_date ON water_intake_logs (user_id, log_date);",
        # Recipe Engine v1 — Sprint 2 tables (additive; sole DDL path — see RECIPE_ENGINE_TABLES)
        _create_table_if_missing(
            "recipe_collections",
            """
            CREATE TABLE recipe_collections (
                id SERIAL PRIMARY KEY,
                owner_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                owner_family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
                visibility VARCHAR(16) NOT NULL DEFAULT 'personal',
                name VARCHAR(120) NOT NULL,
                description VARCHAR(500) NOT NULL DEFAULT '',
                emoji VARCHAR(8),
                color VARCHAR(16),
                is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
                is_dynamic BOOLEAN NOT NULL DEFAULT FALSE,
                position INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
        ),
        "CREATE INDEX IF NOT EXISTS ix_recipe_collections_visibility ON recipe_collections (visibility);",
        "CREATE INDEX IF NOT EXISTS ix_recipe_collections_owner_user ON recipe_collections (owner_user_id) WHERE owner_user_id IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS ix_recipe_collections_owner_family ON recipe_collections (owner_family_id) WHERE owner_family_id IS NOT NULL;",
        _create_table_if_missing(
            "collection_recipes",
            """
            CREATE TABLE collection_recipes (
                id SERIAL PRIMARY KEY,
                collection_id INTEGER NOT NULL REFERENCES recipe_collections(id) ON DELETE CASCADE,
                recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
                position INTEGER NOT NULL DEFAULT 0,
                added_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                note VARCHAR(200),
                CONSTRAINT uq_collection_recipes_collection_recipe UNIQUE (collection_id, recipe_id)
            )
            """,
        ),
        "CREATE INDEX IF NOT EXISTS ix_collection_recipes_collection ON collection_recipes (collection_id);",
        "CREATE INDEX IF NOT EXISTS ix_collection_recipes_recipe ON collection_recipes (recipe_id);",
        _create_table_if_missing(
            "recipe_history",
            """
            CREATE TABLE recipe_history (
                id SERIAL PRIMARY KEY,
                recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                family_id INTEGER REFERENCES families(id) ON DELETE SET NULL,
                family_member_id INTEGER REFERENCES family_members(id) ON DELETE SET NULL,
                servings INTEGER,
                cooked_on DATE NOT NULL DEFAULT CURRENT_DATE,
                source VARCHAR(16) NOT NULL DEFAULT 'manual',
                notes VARCHAR(200),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
        ),
        "CREATE INDEX IF NOT EXISTS ix_recipe_history_recipe_cooked ON recipe_history (recipe_id, cooked_on DESC);",
        "CREATE INDEX IF NOT EXISTS ix_recipe_history_user_cooked ON recipe_history (user_id, cooked_on DESC) WHERE user_id IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS ix_recipe_history_family_cooked ON recipe_history (family_id, cooked_on DESC) WHERE family_id IS NOT NULL;",
        _create_table_if_missing(
            "family_recipe_preferences",
            """
            CREATE TABLE family_recipe_preferences (
                id SERIAL PRIMARY KEY,
                recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
                family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
                family_member_id INTEGER NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
                liked BOOLEAN NOT NULL DEFAULT FALSE,
                disliked BOOLEAN NOT NULL DEFAULT FALSE,
                is_loved BOOLEAN NOT NULL DEFAULT FALSE,
                note VARCHAR(200),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_family_recipe_preferences_member_recipe UNIQUE (family_member_id, recipe_id)
            )
            """,
        ),
        "CREATE INDEX IF NOT EXISTS ix_family_recipe_preferences_recipe ON family_recipe_preferences (recipe_id);",
        "CREATE INDEX IF NOT EXISTS ix_family_recipe_preferences_family ON family_recipe_preferences (family_id);",
        _create_table_if_missing(
            "recipe_scenarios",
            """
            CREATE TABLE recipe_scenarios (
                id SERIAL PRIMARY KEY,
                recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
                scenario VARCHAR(32) NOT NULL,
                score DOUBLE PRECISION NOT NULL DEFAULT 1.0,
                source VARCHAR(16) NOT NULL DEFAULT 'auto',
                CONSTRAINT uq_recipe_scenarios_recipe_scenario UNIQUE (recipe_id, scenario)
            )
            """,
        ),
        "CREATE INDEX IF NOT EXISTS ix_recipe_scenarios_scenario ON recipe_scenarios (scenario);",
        _create_table_if_missing(
            "recipe_explanations",
            """
            CREATE TABLE recipe_explanations (
                id SERIAL PRIMARY KEY,
                recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
                summary VARCHAR(500) NOT NULL DEFAULT '',
                reasons_json JSONB NOT NULL DEFAULT '{}',
                score_total DOUBLE PRECISION NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_recipe_explanations_scope UNIQUE (recipe_id, user_id, family_id)
            )
            """,
        ),
        "CREATE INDEX IF NOT EXISTS ix_recipe_explanations_recipe ON recipe_explanations (recipe_id);",
    ]


def _execute_statements(connection: Connection, statements: Sequence[str]) -> None:
    for statement in statements:
        connection.execute(text(statement))


def ensure_database_schema(engine: Engine, base: type) -> None:
    """Create/upgrade schema once per startup cluster (safe with multiple uvicorn workers)."""
    legacy_tables = [
        table
        for table in base.metadata.sorted_tables
        if table.name not in RECIPE_ENGINE_TABLES
    ]
    with engine.begin() as connection:
        connection.execute(
            text("SELECT pg_advisory_lock(:lock_id)"),
            {"lock_id": SCHEMA_ADVISORY_LOCK_ID},
        )
        try:
            base.metadata.create_all(
                bind=connection,
                tables=legacy_tables,
                checkfirst=True,
            )
            _execute_statements(connection, _schema_statements())
        finally:
            connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": SCHEMA_ADVISORY_LOCK_ID},
            )


def run_schema_migrations(engine: Engine) -> None:
    """Backward-compatible entry point (prefer ``ensure_database_schema``)."""
    with engine.begin() as connection:
        _execute_statements(connection, _schema_statements())
