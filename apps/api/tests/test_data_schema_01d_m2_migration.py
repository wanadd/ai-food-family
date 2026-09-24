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


def test_m2_has_only_the_accepted_identity_source_provenance_scope():
    statements = _p0_data_schema_01d_m2_statements()
    sql = "\n".join(statements)

    assert sql.count("ADD COLUMN IF NOT EXISTS") == 7
    assert "recipe_ingredients" in sql
    assert "food_matches" in sql
    assert "food_nutrient_facts" in sql
    assert "family_pantry_items" in sql
    assert "cooking_batches" not in sql
    assert "cooking_batch_events" not in sql
    assert "meal_consumption_logs" not in sql
    assert "nutrition_targets" not in sql
    assert "ALTER TABLE" in sql
    assert "CREATE TABLE" not in sql
    assert "DROP " not in sql
    assert "UPDATE " not in sql
    assert "INSERT INTO" not in sql
    assert "DELETE FROM" not in sql


def test_m2_columns_are_nullable_first_and_use_compatible_integer_fks():
    sql = "\n".join(_p0_data_schema_01d_m2_statements())

    assert "food_identity_id INTEGER" in sql
    assert "product_instance_id INTEGER" in sql
    assert "food_identity_id INTEGER NOT NULL" not in sql
    assert "product_instance_id INTEGER NOT NULL" not in sql
    assert "REFERENCES food_identities(id) ON DELETE SET NULL" in sql
    assert "REFERENCES product_instances(id) ON DELETE SET NULL" in sql
    assert "BIGINT" not in sql
    assert "BIGSERIAL" not in sql


def test_m2_preserves_existing_source_columns_and_food_match_semantics():
    sql = "\n".join(_p0_data_schema_01d_m2_statements())

    assert "source_version VARCHAR(64)" in sql
    assert "source_record_locator" not in sql
    assert "canonical_food_key" not in sql
    assert "normalized_ingredient_name" not in sql
    assert "match_method" not in sql
    assert "food_matches_food_identity_id_fkey" in sql
    assert "food_nutrient_facts_food_identity_id_fkey" in sql


def test_m2_indexes_are_exact_and_not_speculative():
    statements = _p0_data_schema_01d_m2_statements()
    indexes = [statement for statement in statements if "CREATE INDEX IF NOT EXISTS" in statement]

    assert len(indexes) == 3
    assert any("food_matches (food_identity_id, source_id, is_current)" in item for item in indexes)
    assert any("food_nutrient_facts (food_identity_id, nutrient_key, is_current)" in item for item in indexes)
    assert any("family_pantry_items (product_instance_id)" in item for item in indexes)


def test_m2_has_no_fabricated_safety_or_nutrient_defaults():
    sql = "\n".join(_p0_data_schema_01d_m2_statements())

    assert "DEFAULT 'safe'" not in sql.lower()
    assert "DEFAULT 'verified'" not in sql.lower()
    assert "DEFAULT 0" not in sql
    assert "Phe" not in sql
    assert "source_registry" not in sql.lower()
    assert "regulatory_sources" not in sql.lower()
    assert "food_identity_id" in sql


def test_m2_is_appended_after_m1_and_keeps_m1_tables_intact():
    all_sql = _schema_statements()
    m1 = _p0_data_schema_01d_m1_statements()
    m2 = _p0_data_schema_01d_m2_statements()

    m3 = _p0_data_schema_01d_m3_statements()
    m4 = _p0_data_schema_01d_m4_statements()
    assert all_sql[-len(m4) - len(m3) - len(m2):-len(m4) - len(m3)] == m2
    assert all_sql[-len(m4) - len(m3) - len(m2) - len(m1):-len(m4) - len(m3) - len(m2)] == m1
    m1_sql = "\n".join(m1)
    assert "CREATE TABLE food_identities" in m1_sql
    assert "CREATE TABLE food_safety_facts" in m1_sql
    assert "CREATE TABLE packaged_products" in m1_sql
    assert "CREATE TABLE product_instances" in m1_sql
    assert "CREATE TABLE derived_decisions" in m1_sql


def test_m2_do_blocks_use_balanced_postgresql_dollar_quoting():
    assert_valid_do_blocks("\n".join(_p0_data_schema_01d_m2_statements()))


def test_m2_repeated_execution_contract_is_idempotent():
    for statement in _p0_data_schema_01d_m2_statements():
        assert "IF NOT EXISTS" in statement or "IF NOT EXISTS" in statement.upper()
