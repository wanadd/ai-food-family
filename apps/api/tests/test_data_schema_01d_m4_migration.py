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


def test_m4_has_only_accepted_cooking_and_consumption_targets():
    statements = _p0_data_schema_01d_m4_statements()
    sql = "\n".join(statements)

    assert sql.count("ADD COLUMN IF NOT EXISTS") == 10
    assert "cooking_batches" in sql
    assert "cooking_batch_events" in sql
    assert "meal_consumption_logs" in sql
    assert "recipe_ingredients" in sql
    assert "product_instances" in sql
    assert "food_identities" not in sql
    assert "packaged_products" not in sql
    assert "nutrition_targets" not in sql
    assert "CREATE TABLE" not in sql
    assert "DROP " not in sql
    assert "UPDATE " not in sql
    assert "INSERT INTO" not in sql
    assert "DELETE FROM" not in sql


def test_m4_actual_process_fields_are_nullable_and_have_no_inference_defaults():
    sql = "\n".join(_p0_data_schema_01d_m4_statements())

    expected = {
        "completion_status VARCHAR(24)",
        "started_at TIMESTAMPTZ",
        "completed_at TIMESTAMPTZ",
        "process_confirmation_status VARCHAR(24)",
        "process_evidence_json JSONB",
        "substitution_status VARCHAR(24)",
        "safety_review_status VARCHAR(24)",
    }
    actual = {
        line.split("ADD COLUMN IF NOT EXISTS ", 1)[1].strip()
        for line in sql.splitlines()
        if "ADD COLUMN IF NOT EXISTS" in line
    }
    assert expected <= actual
    assert "DEFAULT 'cooked'" not in sql.lower()
    assert "DEFAULT 'heat_treated'" not in sql.lower()
    assert "DEFAULT 'pasteurized'" not in sql.lower()
    assert "DEFAULT 'safe'" not in sql.lower()
    assert "DEFAULT 'verified'" not in sql.lower()
    assert "DEFAULT TRUE" not in sql
    assert "actual_process_state" not in sql
    assert "consumed=true" not in sql.lower()
    assert "portion=0" not in sql.lower()


def test_m4_event_and_consumption_links_are_nullable_and_set_null():
    sql = "\n".join(_p0_data_schema_01d_m4_statements())

    assert "product_instance_id INTEGER" in sql
    assert "recipe_ingredient_id INTEGER" in sql
    assert "cooking_batch_id INTEGER" in sql
    assert "product_instance_id INTEGER NOT NULL" not in sql
    assert "recipe_ingredient_id INTEGER NOT NULL" not in sql
    assert "cooking_batch_id INTEGER NOT NULL" not in sql
    assert "REFERENCES product_instances(id) ON DELETE SET NULL" in sql
    assert "REFERENCES recipe_ingredients(id) ON DELETE SET NULL" in sql
    assert "REFERENCES cooking_batches(id) ON DELETE SET NULL" in sql
    assert "BIGINT" not in sql
    assert "BIGSERIAL" not in sql


def test_m4_indexes_are_exact_and_preserve_person_scoped_consumption():
    statements = _p0_data_schema_01d_m4_statements()
    indexes = [statement for statement in statements if "CREATE INDEX IF NOT EXISTS" in statement]

    assert len(indexes) == 2
    assert any("cooking_batch_events (batch_id, created_at)" in item for item in indexes)
    assert any("meal_consumption_logs (family_member_id, planned_date, cooking_batch_id)" in item for item in indexes)
    assert "family_id, planned_date, cooking_batch_id" not in "\n".join(indexes)


def test_m4_does_not_create_product_instances_or_copy_recipe_expectations():
    sql = "\n".join(_p0_data_schema_01d_m4_statements())

    assert "CREATE TABLE product_instances" not in sql
    assert "INSERT" not in sql
    assert "expected_process_state" not in sql
    assert "expected_process_source" not in sql
    assert "FoodNutrientFact" not in sql
    assert "source_id" not in sql


def test_m4_is_ordered_after_m1_m2_m3_and_keeps_prior_slices_intact():
    all_sql = _schema_statements()
    m1 = _p0_data_schema_01d_m1_statements()
    m2 = _p0_data_schema_01d_m2_statements()
    m3 = _p0_data_schema_01d_m3_statements()
    m4 = _p0_data_schema_01d_m4_statements()

    assert all_sql[-len(m4):] == m4
    assert all_sql[-len(m4) - len(m3):-len(m4)] == m3
    assert all_sql[-len(m4) - len(m3) - len(m2):-len(m4) - len(m3)] == m2
    assert all_sql[-len(m4) - len(m3) - len(m2) - len(m1):-len(m4) - len(m3) - len(m2)] == m1
    assert "CREATE TABLE food_identities" in "\n".join(m1)
    assert "food_identity_id INTEGER" in "\n".join(m2)
    assert "expected_process_state VARCHAR(32)" in "\n".join(m3)


def test_m4_do_blocks_use_balanced_postgresql_dollar_quoting():
    assert_valid_do_blocks("\n".join(_p0_data_schema_01d_m4_statements()))


def test_m4_repeated_execution_contract_is_idempotent():
    for statement in _p0_data_schema_01d_m4_statements():
        assert "IF NOT EXISTS" in statement
