"""Lightweight schema upgrades for databases created before personal mode."""

from __future__ import annotations

import re
from collections.abc import Sequence

from sqlalchemy import Connection, Engine, text

# Schema authority is intentionally explicit. New shared-Base registrations must
# not silently become CREATE_ALL-owned tables.
M1_CUSTOM_TABLES: frozenset[str] = frozenset(
    {
        "food_identities",
        "food_safety_facts",
        "packaged_products",
        "product_instances",
        "derived_decisions",
    }
)

# These tables have no current shared-Base owner and remain custom-SQL-owned.
CUSTOM_SQL_TABLES: frozenset[str] = M1_CUSTOM_TABLES | frozenset(
    {"deferred_nutrition_advice", "water_intake_logs"}
)

# Positive allowlist for the legacy tables owned by SQLAlchemy create_all.
CREATE_ALL_TABLES: frozenset[str] = frozenset(
    {
        "admin_actions",
        "admin_error_logs",
        "admin_login_attempts",
        "admin_sessions",
        "ai_usage_logs",
        "ama_transactions",
        "ama_wallets",
        "care_events",
        "care_notifications",
        "care_settings",
        "cooking_batch_events",
        "cooking_batches",
        "event_plans",
        "external_food_logs",
        "families",
        "family_invites",
        "family_members",
        "family_menu_selections",
        "family_pantry_items",
        "family_shopping_lists",
        "food_matches",
        "food_nutrient_facts",
        "meal_checkins",
        "meal_consumption_logs",
        "meal_consumption_reminder_events",
        "meal_eating_schedules",
        "meal_leftovers",
        "nutrition_targets",
        "progress_entries",
        "recipe_allergens",
        "recipe_favorites",
        "recipe_ingredients",
        "recipe_import_jobs",
        "recipe_ratings",
        "recipe_restrictions",
        "recipe_steps",
        "recipe_tags",
        "recipes",
        "shopping_categories",
        "subscription_plans",
        "telegram_bot_sessions",
        "training_entries",
        "user_notification_settings",
        "user_preferences",
        "user_profiles",
        "user_subscriptions",
        "users",
    }
)

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

LEGACY_PREREQUISITE_TABLES: frozenset[str] = frozenset({"users", "families"})

if CREATE_ALL_TABLES & CUSTOM_SQL_TABLES:
    raise RuntimeError("schema authority sets overlap: CREATE_ALL and custom SQL")
if CREATE_ALL_TABLES & RECIPE_ENGINE_TABLES:
    raise RuntimeError("schema authority sets overlap: CREATE_ALL and Recipe Engine")
if CUSTOM_SQL_TABLES & RECIPE_ENGINE_TABLES:
    raise RuntimeError("schema authority sets overlap: custom SQL and Recipe Engine")

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


def _p0_data_schema_01d_m1_statements() -> list[str]:
    """Return the first additive P0 evidence schema slice.

    This slice is intentionally limited to new reference/evidence tables. It
    does not alter existing tables, backfill data, or change runtime models.
    """
    return [
        _create_table_if_missing(
            "food_identities",
            """
            CREATE TABLE food_identities (
                id SERIAL PRIMARY KEY,
                canonical_key VARCHAR(160) NOT NULL,
                canonical_name VARCHAR(200) NOT NULL,
                food_class VARCHAR(64),
                default_state VARCHAR(32),
                status VARCHAR(24) NOT NULL DEFAULT 'review',
                source_id VARCHAR(64),
                source_version VARCHAR(128),
                source_record_locator VARCHAR(512),
                provenance_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
                confidence VARCHAR(32) NOT NULL DEFAULT 'unknown',
                review_status VARCHAR(32) NOT NULL DEFAULT 'needs_review',
                reviewed_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                reviewed_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_food_identities_canonical_key UNIQUE (canonical_key)
            )
            """,
        ),
        _create_table_if_missing(
            "food_safety_facts",
            """
            CREATE TABLE food_safety_facts (
                id SERIAL PRIMARY KEY,
                food_identity_id INTEGER NOT NULL REFERENCES food_identities(id) ON DELETE CASCADE,
                concept_id VARCHAR(64) NOT NULL,
                relation_type VARCHAR(32) NOT NULL,
                fact_status VARCHAR(24) NOT NULL DEFAULT 'unknown',
                source_id VARCHAR(64),
                source_version VARCHAR(128),
                source_record_locator VARCHAR(512),
                evidence_notes TEXT,
                confidence VARCHAR(32) NOT NULL DEFAULT 'unknown',
                provenance_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
                review_status VARCHAR(32) NOT NULL DEFAULT 'needs_review',
                effective_from TIMESTAMPTZ,
                effective_to TIMESTAMPTZ,
                is_current BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_food_safety_fact_current UNIQUE (
                    food_identity_id,
                    concept_id,
                    relation_type,
                    source_id,
                    source_version,
                    source_record_locator
                )
            )
            """,
        ),
        _create_table_if_missing(
            "packaged_products",
            """
            CREATE TABLE packaged_products (
                id SERIAL PRIMARY KEY,
                gtin VARCHAR(32),
                brand VARCHAR(160),
                product_name VARCHAR(240) NOT NULL,
                market VARCHAR(32) NOT NULL DEFAULT 'unknown',
                status VARCHAR(24) NOT NULL DEFAULT 'review',
                label_ingredients_text TEXT,
                contains_allergens_json JSONB,
                may_contain_text TEXT,
                cross_contact_text TEXT,
                nutrition_panel_json JSONB,
                verified_gf_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
                pasteurization_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
                rte_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
                aspartame_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
                source_id VARCHAR(64),
                source_version VARCHAR(128),
                source_record_locator VARCHAR(512),
                provenance_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
                review_status VARCHAR(32) NOT NULL DEFAULT 'needs_review',
                captured_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_packaged_products_gtin_market UNIQUE (gtin, market)
            )
            """,
        ),
        _create_table_if_missing(
            "product_instances",
            """
            CREATE TABLE product_instances (
                id SERIAL PRIMARY KEY,
                packaged_product_id INTEGER NOT NULL REFERENCES packaged_products(id) ON DELETE RESTRICT,
                family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                quantity VARCHAR(80),
                unit VARCHAR(32),
                opened_at TIMESTAMPTZ,
                expires_at DATE,
                acquired_at TIMESTAMPTZ,
                status VARCHAR(24) NOT NULL DEFAULT 'active',
                observation_json JSONB,
                source_id VARCHAR(64),
                source_version VARCHAR(128),
                source_record_locator VARCHAR(512),
                provenance_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT ck_product_instances_owner CHECK (
                    family_id IS NOT NULL OR user_id IS NOT NULL
                )
            )
            """,
        ),
        _create_table_if_missing(
            "derived_decisions",
            """
            CREATE TABLE derived_decisions (
                id SERIAL PRIMARY KEY,
                subject_type VARCHAR(32) NOT NULL,
                subject_id INTEGER NOT NULL,
                decision VARCHAR(16) NOT NULL,
                reason_codes_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                algorithm_version VARCHAR(64) NOT NULL,
                profile_version VARCHAR(64),
                input_snapshot_json JSONB NOT NULL,
                input_snapshot_hash VARCHAR(128) NOT NULL,
                evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                is_current BOOLEAN NOT NULL DEFAULT TRUE,
                superseded_by_id INTEGER REFERENCES derived_decisions(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_derived_decision_snapshot UNIQUE (
                    subject_type,
                    subject_id,
                    algorithm_version,
                    input_snapshot_hash
                )
            )
            """,
        ),
        "CREATE INDEX IF NOT EXISTS ix_food_safety_identity_current ON food_safety_facts (food_identity_id, concept_id, relation_type, is_current)",
        "CREATE INDEX IF NOT EXISTS ix_packaged_products_status_review ON packaged_products (status, review_status)",
        "CREATE INDEX IF NOT EXISTS ix_product_instances_family_status ON product_instances (family_id, status, packaged_product_id)",
        "CREATE INDEX IF NOT EXISTS ix_derived_decisions_subject_time ON derived_decisions (subject_type, subject_id, evaluated_at)",
    ]


def _p0_data_schema_01d_m2_statements() -> list[str]:
    """Return the accepted M2 identity/source/provenance extensions only."""
    return [
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS food_identity_id INTEGER",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'recipe_ingredients_food_identity_id_fkey'
            ) THEN
                ALTER TABLE recipe_ingredients
                ADD CONSTRAINT recipe_ingredients_food_identity_id_fkey
                FOREIGN KEY (food_identity_id) REFERENCES food_identities(id) ON DELETE SET NULL;
            END IF;
        END $$;
        """,
        "ALTER TABLE food_matches ADD COLUMN IF NOT EXISTS food_identity_id INTEGER",
        "ALTER TABLE food_matches ADD COLUMN IF NOT EXISTS source_version VARCHAR(64)",
        "ALTER TABLE food_matches ADD COLUMN IF NOT EXISTS is_current BOOLEAN NOT NULL DEFAULT TRUE",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'food_matches_food_identity_id_fkey'
            ) THEN
                ALTER TABLE food_matches
                ADD CONSTRAINT food_matches_food_identity_id_fkey
                FOREIGN KEY (food_identity_id) REFERENCES food_identities(id) ON DELETE SET NULL;
            END IF;
        END $$;
        """,
        "ALTER TABLE food_nutrient_facts ADD COLUMN IF NOT EXISTS food_identity_id INTEGER",
        "ALTER TABLE food_nutrient_facts ADD COLUMN IF NOT EXISTS is_current BOOLEAN NOT NULL DEFAULT TRUE",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'food_nutrient_facts_food_identity_id_fkey'
            ) THEN
                ALTER TABLE food_nutrient_facts
                ADD CONSTRAINT food_nutrient_facts_food_identity_id_fkey
                FOREIGN KEY (food_identity_id) REFERENCES food_identities(id) ON DELETE SET NULL;
            END IF;
        END $$;
        """,
        "ALTER TABLE family_pantry_items ADD COLUMN IF NOT EXISTS product_instance_id INTEGER",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'family_pantry_items_product_instance_id_fkey'
            ) THEN
                ALTER TABLE family_pantry_items
                ADD CONSTRAINT family_pantry_items_product_instance_id_fkey
                FOREIGN KEY (product_instance_id) REFERENCES product_instances(id) ON DELETE SET NULL;
            END IF;
        END $$;
        """,
        "CREATE INDEX IF NOT EXISTS ix_food_matches_identity_current ON food_matches (food_identity_id, source_id, is_current)",
        "CREATE INDEX IF NOT EXISTS ix_food_nutrients_identity_current ON food_nutrient_facts (food_identity_id, nutrient_key, is_current)",
        "CREATE INDEX IF NOT EXISTS ix_pantry_product_instance ON family_pantry_items (product_instance_id)",
    ]


def _p0_data_schema_01d_m3_statements() -> list[str]:
    """Return the accepted Slice 3 recipe and target-history extensions."""
    return [
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS food_match_status VARCHAR(24)",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS normalized_quantity NUMERIC",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS normalized_unit VARCHAR(32)",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS quantity_conversion_status VARCHAR(24)",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS quantity_conversion_provenance_json JSONB",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS mass_equivalent_g NUMERIC",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS expected_process_state VARCHAR(32)",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS expected_process_source VARCHAR(512)",
        "ALTER TABLE nutrition_targets ADD COLUMN IF NOT EXISTS effective_from TIMESTAMPTZ",
        "ALTER TABLE nutrition_targets ADD COLUMN IF NOT EXISTS effective_to TIMESTAMPTZ",
        "ALTER TABLE nutrition_targets ADD COLUMN IF NOT EXISTS supersedes_id INTEGER",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'nutrition_targets_supersedes_id_fkey'
            ) THEN
                ALTER TABLE nutrition_targets
                ADD CONSTRAINT nutrition_targets_supersedes_id_fkey
                FOREIGN KEY (supersedes_id) REFERENCES nutrition_targets(id) ON DELETE SET NULL;
            END IF;
        END $$;
        """,
    ]


def _p0_data_schema_01d_m4_statements() -> list[str]:
    """Return the accepted Slice 4 cooking and consumption extensions."""
    return [
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS completion_status VARCHAR(24)",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS process_confirmation_status VARCHAR(24)",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS process_evidence_json JSONB",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS substitution_status VARCHAR(24)",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS safety_review_status VARCHAR(24)",
        "ALTER TABLE cooking_batch_events ADD COLUMN IF NOT EXISTS product_instance_id INTEGER",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'cooking_batch_events_product_instance_id_fkey'
            ) THEN
                ALTER TABLE cooking_batch_events
                ADD CONSTRAINT cooking_batch_events_product_instance_id_fkey
                FOREIGN KEY (product_instance_id) REFERENCES product_instances(id) ON DELETE SET NULL;
            END IF;
        END $$;
        """,
        "ALTER TABLE cooking_batch_events ADD COLUMN IF NOT EXISTS recipe_ingredient_id INTEGER",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'cooking_batch_events_recipe_ingredient_id_fkey'
            ) THEN
                ALTER TABLE cooking_batch_events
                ADD CONSTRAINT cooking_batch_events_recipe_ingredient_id_fkey
                FOREIGN KEY (recipe_ingredient_id) REFERENCES recipe_ingredients(id) ON DELETE SET NULL;
            END IF;
        END $$;
        """,
        "ALTER TABLE meal_consumption_logs ADD COLUMN IF NOT EXISTS cooking_batch_id INTEGER",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'meal_consumption_logs_cooking_batch_id_fkey'
            ) THEN
                ALTER TABLE meal_consumption_logs
                ADD CONSTRAINT meal_consumption_logs_cooking_batch_id_fkey
                FOREIGN KEY (cooking_batch_id) REFERENCES cooking_batches(id) ON DELETE SET NULL;
            END IF;
        END $$;
        """,
        "CREATE INDEX IF NOT EXISTS ix_cooking_batch_events_batch_captured ON cooking_batch_events (batch_id, created_at)",
        "CREATE INDEX IF NOT EXISTS ix_consumption_member_date_batch ON meal_consumption_logs (family_member_id, planned_date, cooking_batch_id)",
    ]


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
        "ALTER TABLE family_pantry_items ADD COLUMN IF NOT EXISTS category VARCHAR(64) NOT NULL DEFAULT 'другое';",
        "ALTER TABLE family_pantry_items ALTER COLUMN category SET DEFAULT 'другое';",
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
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS age_months INTEGER",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS gender VARCHAR(24)",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS height_cm INTEGER",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS weight_kg DOUBLE PRECISION",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS nutrition_goal VARCHAR(32)",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS activity_level VARCHAR(32)",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS physical_activity_group VARCHAR(32)",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS life_stage VARCHAR(32)",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS medical_restrictions TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS typed_safety_profile JSONB NOT NULL DEFAULT '[]'",
        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS typed_medical_context JSONB NOT NULL DEFAULT '[]'",
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
            target_origin VARCHAR(32) NOT NULL DEFAULT 'legacy',
            provenance_status VARCHAR(32) NOT NULL DEFAULT 'unreviewed',
            evidence_id VARCHAR(64),
            source_id VARCHAR(64),
            source_version VARCHAR(64),
            calculation_method VARCHAR(128),
            calculation_inputs_json JSONB,
            calculated_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_nutrition_targets_user_id ON nutrition_targets (user_id);",
        "ALTER TABLE nutrition_targets ADD COLUMN IF NOT EXISTS target_origin VARCHAR(32) NOT NULL DEFAULT 'legacy'",
        "ALTER TABLE nutrition_targets ADD COLUMN IF NOT EXISTS provenance_status VARCHAR(32) NOT NULL DEFAULT 'unreviewed'",
        "ALTER TABLE nutrition_targets ADD COLUMN IF NOT EXISTS evidence_id VARCHAR(64)",
        "ALTER TABLE nutrition_targets ADD COLUMN IF NOT EXISTS source_id VARCHAR(64)",
        "ALTER TABLE nutrition_targets ADD COLUMN IF NOT EXISTS source_version VARCHAR(64)",
        "ALTER TABLE nutrition_targets ADD COLUMN IF NOT EXISTS calculation_method VARCHAR(128)",
        "ALTER TABLE nutrition_targets ADD COLUMN IF NOT EXISTS calculation_inputs_json JSONB",
        "ALTER TABLE nutrition_targets ADD COLUMN IF NOT EXISTS calculated_at TIMESTAMPTZ",
        """
        UPDATE nutrition_targets
        SET target_origin = 'legacy'
        WHERE target_origin IS NULL;
        """,
        """
        UPDATE nutrition_targets
        SET provenance_status = 'unreviewed'
        WHERE provenance_status IS NULL;
        """,
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_nutrition_targets_origin'
            ) THEN
                ALTER TABLE nutrition_targets
                ADD CONSTRAINT ck_nutrition_targets_origin
                CHECK (target_origin IN ('evidence_auto', 'manual', 'clinician', 'legacy'));
            END IF;
        END $$;
        """,
        "ALTER TABLE nutrition_targets DROP CONSTRAINT IF EXISTS ck_nutrition_targets_provenance_status",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_nutrition_targets_provenance_status'
            ) THEN
                ALTER TABLE nutrition_targets
                ADD CONSTRAINT ck_nutrition_targets_provenance_status
                CHECK (provenance_status IN ('unreviewed', 'valid', 'verified', 'invalid', 'needs_review'));
            END IF;
        END $$;
        """,
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_nutrition_targets_evidence_auto_provenance'
            ) THEN
                ALTER TABLE nutrition_targets
                ADD CONSTRAINT ck_nutrition_targets_evidence_auto_provenance
                CHECK (
                    target_origin <> 'evidence_auto'
                    OR (
                        evidence_id IS NOT NULL
                        AND source_id IS NOT NULL
                        AND source_version IS NOT NULL
                        AND calculation_method IS NOT NULL
                        AND calculation_inputs_json IS NOT NULL
                        AND calculated_at IS NOT NULL
                    )
                );
            END IF;
        END $$;
        """,
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_nutrition_targets_non_evidence_no_provenance'
            ) THEN
                ALTER TABLE nutrition_targets
                ADD CONSTRAINT ck_nutrition_targets_non_evidence_no_provenance
                CHECK (
                    target_origin = 'evidence_auto'
                    OR (
                        evidence_id IS NULL
                        AND source_id IS NULL
                        AND source_version IS NULL
                        AND calculation_method IS NULL
                        AND calculation_inputs_json IS NULL
                        AND calculated_at IS NULL
                    )
                );
            END IF;
        END $$;
        """,
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
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS hero_image_url VARCHAR(512)",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(512)",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS is_drink BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS is_alcoholic BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS alcohol_percent DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS caffeine_mg DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS suitable_for_children BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS suitable_for_sport BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS suitable_for_event BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        # Recipe-level nutrition summary (additive; populated by
        # calculate_recipe_nutrition_summary.py). All nullable / defaulted.
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_kcal_total DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_protein_total DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_fat_total DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_carbs_total DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_kcal_per_serving DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_protein_per_serving DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_fat_per_serving DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_carbs_per_serving DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_servings DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_serving_size_text TEXT",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_confidence VARCHAR(24)",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_coverage_json JSONB",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_calculated_at TIMESTAMPTZ",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_source VARCHAR(64)",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_source_kind VARCHAR(64)",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_provenance_json JSONB",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_needs_review BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS nutrition_review_reason VARCHAR(64)",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS gluten_free_status VARCHAR(32)",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS gluten_free_provenance_status VARCHAR(32)",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS gluten_free_provenance_json JSONB",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS sodium_mg_per_serving DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS salt_g_per_serving DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS phenylalanine_mg_per_serving DOUBLE PRECISION",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS medical_safety_facts_json JSONB",
        """
        CREATE TABLE IF NOT EXISTS food_nutrient_facts (
            id SERIAL PRIMARY KEY,
            canonical_food_key VARCHAR(120) NOT NULL,
            nutrient_key VARCHAR(48) NOT NULL,
            value DOUBLE PRECISION,
            unit VARCHAR(24) NOT NULL,
            basis_amount DOUBLE PRECISION NOT NULL,
            basis_unit VARCHAR(24) NOT NULL,
            source_id VARCHAR(64) NOT NULL,
            source_record_locator VARCHAR(256) NOT NULL,
            source_version VARCHAR(64) NOT NULL,
            source_data_type VARCHAR(64),
            fdc_id INTEGER,
            food_state VARCHAR(32) NOT NULL DEFAULT 'unknown',
            provenance_status VARCHAR(32) NOT NULL,
            source_food_name VARCHAR(200),
            source_food_description TEXT,
            source_nutrient_id VARCHAR(64),
            source_nutrient_name VARCHAR(120),
            match_method VARCHAR(64),
            match_confidence VARCHAR(32),
            review_status VARCHAR(32),
            review_notes TEXT,
            edible_portion_basis VARCHAR(120),
            preparation_method VARCHAR(120),
            loss_or_retention_metadata JSONB,
            retrieved_or_imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_food_nutrient_fact_source_record UNIQUE (
                canonical_food_key,
                nutrient_key,
                food_state,
                source_id,
                source_record_locator
            ),
            CONSTRAINT ck_food_nutrient_fact_provenance_status CHECK (
                provenance_status IN (
                    'external_verified',
                    'external_imported_unreviewed',
                    'manual_reviewed',
                    'internal_legacy_unsourced',
                    'unavailable'
                )
            ),
            CONSTRAINT ck_food_nutrient_fact_external_provenance CHECK (
                provenance_status <> 'external_verified'
                OR (
                    source_id <> 'SRC-PLANAM-V1-NUTRITION-FACTS'
                    AND source_record_locator IS NOT NULL
                    AND source_version IS NOT NULL
                )
            ),
            CONSTRAINT ck_food_nutrient_fact_planam_internal CHECK (
                source_id <> 'SRC-PLANAM-V1-NUTRITION-FACTS'
                OR provenance_status = 'internal_legacy_unsourced'
            ),
            CONSTRAINT ck_food_nutrient_fact_fdc_identity CHECK (
                source_id <> 'SRC-USDA-FDC'
                OR (fdc_id IS NOT NULL AND source_data_type IS NOT NULL)
            )
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_food_nutrient_facts_food ON food_nutrient_facts (canonical_food_key);",
        "CREATE INDEX IF NOT EXISTS ix_food_nutrient_facts_source ON food_nutrient_facts (source_id);",
        "CREATE INDEX IF NOT EXISTS ix_food_nutrient_facts_fdc_id ON food_nutrient_facts (fdc_id);",
        """
        CREATE TABLE IF NOT EXISTS food_matches (
            id SERIAL PRIMARY KEY,
            normalized_ingredient_name VARCHAR(160) NOT NULL,
            original_ingredient_text VARCHAR(300),
            status VARCHAR(32) NOT NULL,
            canonical_food_key VARCHAR(120),
            source_id VARCHAR(64),
            source_record_locator VARCHAR(256),
            source_food_name VARCHAR(200),
            food_state VARCHAR(32) NOT NULL DEFAULT 'unknown',
            match_method VARCHAR(64) NOT NULL DEFAULT 'candidate_only',
            match_confidence VARCHAR(32) NOT NULL DEFAULT 'none',
            brand VARCHAR(120),
            review_reason VARCHAR(120),
            reviewed_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_food_match_identity UNIQUE (
                normalized_ingredient_name,
                food_state,
                brand
            ),
            CONSTRAINT ck_food_match_status CHECK (
                status IN ('matched', 'ambiguous', 'unmatched', 'manual_review_required')
            ),
            CONSTRAINT ck_food_match_candidate_only CHECK (
                status <> 'matched' OR match_method <> 'candidate_only'
            )
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_food_matches_name ON food_matches (normalized_ingredient_name);",
        "CREATE INDEX IF NOT EXISTS ix_food_matches_status ON food_matches (status);",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS original_title VARCHAR(200)",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS normalized_title VARCHAR(200)",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS display_title VARCHAR(200)",
        "UPDATE recipes SET original_title = title WHERE original_title IS NULL",
        """
        UPDATE recipes
        SET normalized_title = lower(trim(regexp_replace(title, '\\s+', ' ', 'g')))
        WHERE normalized_title IS NULL AND title IS NOT NULL
        """,
        "CREATE INDEX IF NOT EXISTS ix_recipes_normalized_title ON recipes (normalized_title)",
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
        # Ingredient quality model (to_taste / nutrition / shopping / photo); all nullable/defaulted.
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS quantity_mode VARCHAR(16)",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS quantity_text VARCHAR(64)",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS is_to_taste BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS nutrition_precision VARCHAR(24)",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS shopping_priority VARCHAR(16)",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS needs_review BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS needs_review_reason VARCHAR(64)",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS photo_visibility VARCHAR(16)",
        "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS manual_review_status VARCHAR(16)",
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
            allergen VARCHAR(64) NOT NULL,
            concept_id VARCHAR(64),
            relation_type VARCHAR(32),
            provenance_status VARCHAR(32),
            confidence VARCHAR(32),
            source_id VARCHAR(64),
            source_record_locator VARCHAR(256),
            evidence_notes TEXT
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_recipe_allergens_recipe_id ON recipe_allergens (recipe_id);",
        "ALTER TABLE recipe_allergens ADD COLUMN IF NOT EXISTS concept_id VARCHAR(64)",
        "ALTER TABLE recipe_allergens ADD COLUMN IF NOT EXISTS relation_type VARCHAR(32)",
        "ALTER TABLE recipe_allergens ADD COLUMN IF NOT EXISTS provenance_status VARCHAR(32)",
        "ALTER TABLE recipe_allergens ADD COLUMN IF NOT EXISTS confidence VARCHAR(32)",
        "ALTER TABLE recipe_allergens ADD COLUMN IF NOT EXISTS source_id VARCHAR(64)",
        "ALTER TABLE recipe_allergens ADD COLUMN IF NOT EXISTS source_record_locator VARCHAR(256)",
        "ALTER TABLE recipe_allergens ADD COLUMN IF NOT EXISTS evidence_notes TEXT",
        "CREATE INDEX IF NOT EXISTS ix_recipe_allergens_concept_id ON recipe_allergens (concept_id);",
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
        # shopping_categories: remove duplicate system/user rows (HTTP 500 on menu select)
        """
        DELETE FROM shopping_categories AS a
        USING shopping_categories AS b
        WHERE a.is_system = TRUE
          AND a.user_id IS NOT NULL
          AND b.is_system = TRUE
          AND b.user_id = a.user_id
          AND b.name = a.name
          AND a.id > b.id;
        """,
        """
        DELETE FROM shopping_categories AS a
        USING shopping_categories AS b
        WHERE a.is_system = TRUE
          AND a.family_id IS NOT NULL
          AND b.is_system = TRUE
          AND b.family_id = a.family_id
          AND b.name = a.name
          AND a.id > b.id;
        """,
        """
        DELETE FROM shopping_categories AS a
        USING shopping_categories AS b
        WHERE a.is_system = TRUE
          AND a.user_id IS NOT NULL
          AND b.is_system = TRUE
          AND b.user_id = a.user_id
          AND b.slug = a.slug
          AND a.id > b.id;
        """,
        """
        DELETE FROM shopping_categories AS a
        USING shopping_categories AS b
        WHERE a.is_system = TRUE
          AND a.family_id IS NOT NULL
          AND b.is_system = TRUE
          AND b.family_id = a.family_id
          AND b.slug = a.slug
          AND a.id > b.id;
        """,
        """
        DELETE FROM shopping_categories AS a
        USING shopping_categories AS b
        WHERE a.is_system = FALSE
          AND a.user_id IS NOT NULL
          AND b.is_system = FALSE
          AND b.user_id = a.user_id
          AND b.slug = a.slug
          AND a.id > b.id;
        """,
        """
        DELETE FROM shopping_categories AS a
        USING shopping_categories AS b
        WHERE a.is_system = FALSE
          AND a.family_id IS NOT NULL
          AND b.is_system = FALSE
          AND b.family_id = a.family_id
          AND b.slug = a.slug
          AND a.id > b.id;
        """,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_shopping_categories_system_user_slug
        ON shopping_categories (user_id, slug)
        WHERE is_system = TRUE AND user_id IS NOT NULL;
        """,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_shopping_categories_system_user_name
        ON shopping_categories (user_id, name)
        WHERE is_system = TRUE AND user_id IS NOT NULL;
        """,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_shopping_categories_system_family_slug
        ON shopping_categories (family_id, slug)
        WHERE is_system = TRUE AND family_id IS NOT NULL;
        """,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_shopping_categories_system_family_name
        ON shopping_categories (family_id, name)
        WHERE is_system = TRUE AND family_id IS NOT NULL;
        """,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_shopping_categories_user_slug
        ON shopping_categories (user_id, slug)
        WHERE is_system = FALSE AND user_id IS NOT NULL;
        """,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_shopping_categories_family_slug
        ON shopping_categories (family_id, slug)
        WHERE is_system = FALSE AND family_id IS NOT NULL;
        """,
        """
        CREATE TABLE IF NOT EXISTS meal_consumption_logs (
            id SERIAL PRIMARY KEY,
            family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            family_member_id INTEGER REFERENCES family_members(id) ON DELETE SET NULL,
            logged_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            menu_selection_id INTEGER REFERENCES family_menu_selections(id) ON DELETE SET NULL,
            day_index INTEGER,
            planned_date DATE,
            meal_type VARCHAR(16),
            recipe_id INTEGER REFERENCES recipes(id) ON DELETE SET NULL,
            recipe_title VARCHAR(300),
            status VARCHAR(16) NOT NULL DEFAULT 'unknown',
            portion_multiplier DOUBLE PRECISION NOT NULL DEFAULT 1,
            quantity DOUBLE PRECISION,
            unit VARCHAR(32),
            calories_estimated DOUBLE PRECISION,
            protein_estimated DOUBLE PRECISION,
            fat_estimated DOUBLE PRECISION,
            carbs_estimated DOUBLE PRECISION,
            note VARCHAR(500),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_meal_consumption_logs_family_day ON meal_consumption_logs (family_id, menu_selection_id, day_index);",
        "CREATE INDEX IF NOT EXISTS ix_meal_consumption_logs_user_date ON meal_consumption_logs (user_id, planned_date);",
        "ALTER TABLE meal_consumption_logs ALTER COLUMN family_id DROP NOT NULL",
        """
        CREATE TABLE IF NOT EXISTS meal_consumption_reminder_events (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            menu_selection_id INTEGER REFERENCES family_menu_selections(id) ON DELETE SET NULL,
            day_index INTEGER,
            planned_date DATE,
            meal_type VARCHAR(16) NOT NULL,
            reminder_kind VARCHAR(64) NOT NULL DEFAULT 'meal_consumption_missing',
            status VARCHAR(32) NOT NULL DEFAULT 'planned',
            due_at TIMESTAMPTZ,
            sent_at TIMESTAMPTZ,
            skipped_reason VARCHAR(100),
            telegram_message_id INTEGER,
            error_message VARCHAR(500),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_meal_consumption_reminder_events_user_date ON meal_consumption_reminder_events (user_id, planned_date, meal_type);",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_meal_consumption_reminder_events_idempotency ON meal_consumption_reminder_events (user_id, planned_date, meal_type, COALESCE(menu_selection_id, 0), COALESCE(day_index, -1), reminder_kind);",
        """
        CREATE TABLE IF NOT EXISTS cooking_batches (
            id SERIAL PRIMARY KEY,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            owner_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            created_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            recipe_id INTEGER REFERENCES recipes(id) ON DELETE SET NULL,
            recipe_title VARCHAR(300),
            menu_selection_id INTEGER REFERENCES family_menu_selections(id) ON DELETE SET NULL,
            day_index INTEGER,
            planned_date DATE,
            meal_type VARCHAR(16),
            batch_status VARCHAR(32) NOT NULL DEFAULT 'active',
            total_servings DOUBLE PRECISION NOT NULL DEFAULT 1,
            remaining_servings DOUBLE PRECISION NOT NULL DEFAULT 1,
            serving_unit VARCHAR(32) NOT NULL DEFAULT 'порция',
            cooked_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_cooking_batches_family_id ON cooking_batches (family_id);",
        "CREATE INDEX IF NOT EXISTS ix_cooking_batches_owner_user_id ON cooking_batches (owner_user_id);",
        "CREATE INDEX IF NOT EXISTS ix_cooking_batches_recipe_id ON cooking_batches (recipe_id);",
        "CREATE INDEX IF NOT EXISTS ix_cooking_batches_menu_day ON cooking_batches (menu_selection_id, day_index);",
        "CREATE INDEX IF NOT EXISTS ix_cooking_batches_planned_date ON cooking_batches (planned_date);",
        """
        CREATE TABLE IF NOT EXISTS cooking_batch_events (
            id SERIAL PRIMARY KEY,
            batch_id INTEGER NOT NULL REFERENCES cooking_batches(id) ON DELETE CASCADE,
            event_type VARCHAR(32) NOT NULL,
            actor_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            servings_delta DOUBLE PRECISION,
            remaining_after DOUBLE PRECISION,
            note VARCHAR(500),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_cooking_batch_events_batch_id ON cooking_batch_events (batch_id);",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS recipe_yield_amount DOUBLE PRECISION;",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS recipe_yield_unit VARCHAR(32);",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS serving_size_amount DOUBLE PRECISION;",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS serving_size_unit VARCHAR(32);",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS estimated_servings DOUBLE PRECISION;",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS yield_type VARCHAR(32);",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS total_amount_value DOUBLE PRECISION;",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS total_amount_unit VARCHAR(32);",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS remaining_amount_value DOUBLE PRECISION;",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS remaining_amount_unit VARCHAR(32);",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS serving_size_value DOUBLE PRECISION;",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS serving_size_unit VARCHAR(32);",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS estimated_total_servings DOUBLE PRECISION;",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS estimated_remaining_servings DOUBLE PRECISION;",
        "ALTER TABLE cooking_batches ADD COLUMN IF NOT EXISTS yield_type VARCHAR(32);",
        """
        CREATE TABLE IF NOT EXISTS external_food_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
            meal_type VARCHAR(16),
            planned_date DATE NOT NULL,
            source_type VARCHAR(32) NOT NULL DEFAULT 'manual',
            input_text VARCHAR(2000),
            input_media_id VARCHAR(128),
            parsed_title VARCHAR(300),
            calories_estimated DOUBLE PRECISION,
            protein_estimated DOUBLE PRECISION,
            fat_estimated DOUBLE PRECISION,
            carbs_estimated DOUBLE PRECISION,
            confidence DOUBLE PRECISION,
            status VARCHAR(32) NOT NULL DEFAULT 'draft',
            linked_meal_consumption_log_id INTEGER REFERENCES meal_consumption_logs(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_external_food_logs_user_date ON external_food_logs (user_id, planned_date);",
        "CREATE INDEX IF NOT EXISTS ix_external_food_logs_family_date ON external_food_logs (family_id, planned_date);",
        # Hotfix 1.8H: notification onboarding + quiet defaults
        "ALTER TABLE user_notification_settings ADD COLUMN IF NOT EXISTS notifications_onboarded BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE user_notification_settings ADD COLUMN IF NOT EXISTS care_mode VARCHAR(16) NOT NULL DEFAULT 'off'",
        "ALTER TABLE user_notification_settings ADD COLUMN IF NOT EXISTS enabled_notification_types JSONB NOT NULL DEFAULT '[]'",
        "ALTER TABLE care_notifications ADD COLUMN IF NOT EXISTS semantic_key VARCHAR(64)",
        "CREATE INDEX IF NOT EXISTS ix_care_notifications_semantic ON care_notifications (user_id, type, semantic_key, created_at)",
        "ALTER TABLE user_notification_settings ALTER COLUMN buy_reminder_enabled SET DEFAULT FALSE",
        "ALTER TABLE user_notification_settings ALTER COLUMN cook_reminder_enabled SET DEFAULT FALSE",
        "ALTER TABLE user_notification_settings ALTER COLUMN cook_breakfast_enabled SET DEFAULT FALSE",
        "ALTER TABLE user_notification_settings ALTER COLUMN cook_lunch_enabled SET DEFAULT FALSE",
        "ALTER TABLE user_notification_settings ALTER COLUMN cook_dinner_enabled SET DEFAULT FALSE",
        "ALTER TABLE care_settings ALTER COLUMN menu_enabled SET DEFAULT FALSE",
        "ALTER TABLE care_settings ALTER COLUMN shopping_enabled SET DEFAULT FALSE",
        "ALTER TABLE care_settings ALTER COLUMN pantry_enabled SET DEFAULT FALSE",
        "ALTER TABLE care_settings ALTER COLUMN care_level SET DEFAULT 'off'",
        """
        UPDATE user_notification_settings u SET
            notifications_onboarded = TRUE,
            care_mode = CASE COALESCE(cs.care_level, 'off')
                WHEN 'minimal' THEN 'minimal'
                WHEN 'standard' THEN 'normal'
                WHEN 'active' THEN 'active'
                ELSE 'off'
            END
        FROM care_settings cs
        WHERE cs.user_id = u.user_id
          AND u.notifications_onboarded = FALSE
          AND (
            u.buy_reminder_enabled OR u.cook_reminder_enabled
            OR cs.menu_enabled OR cs.shopping_enabled OR cs.pantry_enabled
            OR cs.care_level NOT IN ('off')
          );
        """,
        """
        UPDATE user_notification_settings SET notifications_onboarded = TRUE
        WHERE notifications_onboarded = FALSE
          AND (buy_reminder_enabled OR cook_reminder_enabled);
        """,
    ] + _p0_data_schema_01d_m1_statements() + _p0_data_schema_01d_m2_statements() + _p0_data_schema_01d_m3_statements() + _p0_data_schema_01d_m4_statements()


def _execute_statements(connection: Connection, statements: Sequence[str]) -> None:
    for statement in statements:
        connection.execute(text(statement))


def _metadata_tables_for_authority(base: type, table_names: frozenset[str]) -> list:
    """Select only explicitly CREATE_ALL-owned tables from shared metadata."""
    return [
        table
        for table in base.metadata.sorted_tables
        if table.name in table_names
    ]


def _create_all_allowlisted(connection: Connection, base: type, table_names: frozenset[str]) -> None:
    base.metadata.create_all(
        bind=connection,
        tables=_metadata_tables_for_authority(base, table_names),
        checkfirst=True,
    )


def _custom_post_create_statements() -> list[str]:
    """Return custom operations that are safe after allowlisted create_all.

    The historical stream still exposes its complete statement list for the
    migration-contract tests. Bootstrap execution filters CREATE TABLE blocks
    for CREATE_ALL-owned names, leaving only additive operations plus the
    explicitly custom-owned M1 and Recipe Engine phases.
    """
    slices = (
        _p0_data_schema_01d_m1_statements()
        + _p0_data_schema_01d_m2_statements()
        + _p0_data_schema_01d_m3_statements()
        + _p0_data_schema_01d_m4_statements()
    )
    historical = _schema_statements()
    post_legacy = historical[: -len(slices)]
    filtered: list[str] = []
    for statement in post_legacy:
        match = re.search(
            r"CREATE TABLE(?: IF NOT EXISTS)?\s+([A-Za-z_][A-Za-z0-9_]*)",
            statement,
            re.IGNORECASE,
        )
        if match and match.group(1) in CREATE_ALL_TABLES:
            continue
        filtered.append(statement)
    return (
        filtered
        + _p0_data_schema_01d_m2_statements()
        + _p0_data_schema_01d_m3_statements()
        + _p0_data_schema_01d_m4_statements()
    )


def _bootstrap_phase_order() -> tuple[str, ...]:
    return (
        "legacy_prerequisites",
        "m1_pre_create",
        "legacy_create_all",
        "custom_post_create",
    )


def _ensure_database_schema_on_connection(connection: Connection, base: type) -> None:
    """Run the ordered schema phases inside the caller's transaction and lock."""
    _create_all_allowlisted(connection, base, LEGACY_PREREQUISITE_TABLES)
    _execute_statements(connection, _p0_data_schema_01d_m1_statements())
    _create_all_allowlisted(
        connection,
        base,
        CREATE_ALL_TABLES - LEGACY_PREREQUISITE_TABLES,
    )
    _execute_statements(connection, _custom_post_create_statements())
    from app.services.shopping_category_migration import (  # noqa: PLC0415
        migrate_shopping_categories_v1,
    )

    migrate_shopping_categories_v1(connection)


def ensure_database_schema(engine: Engine, base: type) -> None:
    """Create/upgrade schema once per startup cluster (safe with multiple uvicorn workers)."""
    with engine.begin() as connection:
        try:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(:lock_id)"),
                {"lock_id": SCHEMA_ADVISORY_LOCK_ID},
            )
            _ensure_database_schema_on_connection(connection, base)
        except BaseException:
            try:
                connection.rollback()
            except BaseException:
                try:
                    connection.invalidate()
                except BaseException:
                    pass
            raise


def run_schema_migrations(engine: Engine) -> None:
    """Backward-compatible entry point (prefer ``ensure_database_schema``)."""
    with engine.begin() as connection:
        _execute_statements(connection, _schema_statements())
