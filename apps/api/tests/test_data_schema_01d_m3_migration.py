from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.database_migrations import (  # noqa: E402
    _p0_data_schema_01d_m1_statements,
    _p0_data_schema_01d_m2_statements,
    _p0_data_schema_01d_m3_statements,
    _p0_data_schema_01d_m4_statements,
    _schema_statements,
)


def assert_valid_do_blocks(sql: str) -> None:
    lines = [line.strip() for line in sql.splitlines()]
    openers = [line for line in lines if line.startswith("DO ")]
    closers = [line for line in lines if line.startswith("END $") and line.endswith(";")]
    assert "DO $" not in openers
    assert "END $;" not in closers
    assert len(openers) == len(closers)
    for opener, closer in zip(openers, closers):
        tag = opener.removeprefix("DO ")
        assert closer == f"END {tag};"


def test_m3_has_only_accepted_recipe_and_target_history_tables():
    statements = _p0_data_schema_01d_m3_statements()
    sql = "\n".join(statements)

    assert sql.count("ADD COLUMN IF NOT EXISTS") == 11
    assert "recipe_ingredients" in sql
    assert "nutrition_targets" in sql
    assert "recipes " not in sql
    assert "cooking_batches" not in sql
    assert "cooking_batch_events" not in sql
    assert "meal_consumption_logs" not in sql
    assert "CREATE TABLE" not in sql
    assert "CREATE INDEX" not in sql
    assert "DROP " not in sql


def test_m3_recipe_fields_are_nullable_and_preserve_recipe_intent_boundary():
    sql = "\n".join(_p0_data_schema_01d_m3_statements())

    expected = {
        "food_match_status VARCHAR(24)",
        "normalized_quantity NUMERIC",
        "normalized_unit VARCHAR(32)",
        "quantity_conversion_status VARCHAR(24)",
        "quantity_conversion_provenance_json JSONB",
        "mass_equivalent_g NUMERIC",
        "expected_process_state VARCHAR(32)",
        "expected_process_source VARCHAR(512)",
    }
    assert expected <= set(
        line.split("ADD COLUMN IF NOT EXISTS ", 1)[1].strip()
        for line in sql.splitlines()
        if "ADD COLUMN IF NOT EXISTS" in line
    )
    assert "expected_process_state VARCHAR(32) NOT NULL" not in sql
    assert "DEFAULT 'cooked'" not in sql.lower()
    assert "DEFAULT 'pasteurized'" not in sql.lower()
    assert "DEFAULT 'safe'" not in sql.lower()
    assert "actual_process" not in sql.lower()
    assert "actual_heat" not in sql.lower()
    assert "consumption" not in sql.lower()


def test_m3_target_history_is_person_scoped_and_legacy_safe():
    sql = "\n".join(_p0_data_schema_01d_m3_statements())

    assert "nutrition_targets ADD COLUMN IF NOT EXISTS effective_from TIMESTAMPTZ" in sql
    assert "nutrition_targets ADD COLUMN IF NOT EXISTS effective_to TIMESTAMPTZ" in sql
    assert "nutrition_targets ADD COLUMN IF NOT EXISTS supersedes_id INTEGER" in sql
    assert "supersedes_id INTEGER NOT NULL" not in sql
    assert "REFERENCES nutrition_targets(id) ON DELETE SET NULL" in sql
    assert "family-average" not in sql.lower()
    assert "INSERT" not in sql
    assert "UPDATE" not in sql
    assert "source_id" not in sql
    assert "SRC-" not in sql


def test_m3_uses_compatible_integer_fk_and_no_fabricated_defaults():
    sql = "\n".join(_p0_data_schema_01d_m3_statements())

    assert "BIGINT" not in sql
    assert "BIGSERIAL" not in sql
    assert "DEFAULT 0" not in sql
    assert "DEFAULT FALSE" not in sql
    assert "DEFAULT 'verified'" not in sql.lower()
    assert "DEFAULT 'safe'" not in sql.lower()
    assert "DEFAULT 'unknown'" not in sql.lower()


def test_m3_is_ordered_after_m1_and_m2_without_changing_them():
    all_sql = _schema_statements()
    m1 = _p0_data_schema_01d_m1_statements()
    m2 = _p0_data_schema_01d_m2_statements()
    m3 = _p0_data_schema_01d_m3_statements()

    m4 = _p0_data_schema_01d_m4_statements()
    assert all_sql[-len(m4) - len(m3):-len(m4)] == m3
    assert all_sql[-len(m4) - len(m3) - len(m2):-len(m4) - len(m3)] == m2
    assert all_sql[-len(m4) - len(m3) - len(m2) - len(m1):-len(m4) - len(m3) - len(m2)] == m1
    assert "CREATE TABLE food_identities" in "\n".join(m1)
    assert "food_identity_id INTEGER" in "\n".join(m2)


def test_m3_do_blocks_use_balanced_postgresql_dollar_quoting():
    assert_valid_do_blocks("\n".join(_p0_data_schema_01d_m3_statements()))


def test_m3_repeated_execution_contract_is_idempotent():
    for statement in _p0_data_schema_01d_m3_statements():
        assert "IF NOT EXISTS" in statement
