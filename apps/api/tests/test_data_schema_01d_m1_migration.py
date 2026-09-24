from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.database_migrations import (  # noqa: E402
    _create_table_if_missing,
    _p0_data_schema_01d_m1_statements,
    _p0_data_schema_01d_m2_statements,
    _p0_data_schema_01d_m3_statements,
    _p0_data_schema_01d_m4_statements,
    _schema_statements,
)


EXPECTED_TABLES = {
    "food_identities",
    "food_safety_facts",
    "packaged_products",
    "product_instances",
    "derived_decisions",
}


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


def test_m1_contains_only_the_five_first_slice_tables_and_indexes():
    statements = _p0_data_schema_01d_m1_statements()
    sql = "\n".join(statements)

    assert sum("CREATE TABLE" in statement for statement in statements) == 5
    assert EXPECTED_TABLES == {
        table for table in EXPECTED_TABLES if table in sql
    }
    assert sum("CREATE INDEX IF NOT EXISTS" in statement for statement in statements) == 4
    assert "ALTER TABLE" not in sql
    assert "UPDATE " not in sql
    assert "INSERT " not in sql
    assert "DELETE FROM" not in sql
    assert "DROP " not in sql
    assert "alembic" not in sql.lower()


def test_m1_keeps_unknown_and_review_defaults_explicit():
    sql = "\n".join(_p0_data_schema_01d_m1_statements())

    assert "provenance_status VARCHAR(32) NOT NULL DEFAULT 'unknown'" in sql
    assert "review_status VARCHAR(32) NOT NULL DEFAULT 'needs_review'" in sql
    assert "fact_status VARCHAR(24) NOT NULL DEFAULT 'unknown'" in sql
    assert "verified_gf_status VARCHAR(32) NOT NULL DEFAULT 'unknown'" in sql
    assert "pasteurization_status VARCHAR(32) NOT NULL DEFAULT 'unknown'" in sql
    assert "rte_status VARCHAR(32) NOT NULL DEFAULT 'unknown'" in sql
    assert "aspartame_status VARCHAR(32) NOT NULL DEFAULT 'unknown'" in sql


def test_m1_preserves_fk_lifecycle_and_deduplication_contracts():
    sql = "\n".join(_p0_data_schema_01d_m1_statements())

    assert "REFERENCES users(id) ON DELETE SET NULL" in sql
    assert "REFERENCES food_identities(id) ON DELETE CASCADE" in sql
    assert "REFERENCES packaged_products(id) ON DELETE RESTRICT" in sql
    assert "REFERENCES families(id) ON DELETE CASCADE" in sql
    assert "CONSTRAINT ck_product_instances_owner" in sql
    assert "CONSTRAINT uq_food_identities_canonical_key UNIQUE" in sql
    assert "CONSTRAINT uq_food_safety_fact_current UNIQUE" in sql
    assert "CONSTRAINT uq_packaged_products_gtin_market UNIQUE" in sql
    assert "CONSTRAINT uq_derived_decision_snapshot UNIQUE" in sql


def test_m1_uses_existing_id_width_and_idempotent_custom_helper():
    sql = "\n".join(_p0_data_schema_01d_m1_statements())

    assert sql.count("id SERIAL PRIMARY KEY") == 5
    assert "BIGSERIAL" not in sql
    assert all("IF NOT EXISTS" in statement for statement in _p0_data_schema_01d_m1_statements())
    wrapped = _create_table_if_missing("example_table", "CREATE TABLE example_table (id SERIAL PRIMARY KEY)")
    assert "information_schema.tables" in wrapped
    assert "IF NOT EXISTS" in wrapped


def test_m1_do_blocks_use_balanced_postgresql_dollar_quoting():
    assert_valid_do_blocks("\n".join(_schema_statements()))


def test_m1_is_appended_to_the_authoritative_schema_statement_stream():
    all_sql = _schema_statements()
    m1 = _p0_data_schema_01d_m1_statements()

    m2 = _p0_data_schema_01d_m2_statements()
    m3 = _p0_data_schema_01d_m3_statements()
    m4 = _p0_data_schema_01d_m4_statements()
    assert all_sql[-len(m4) - len(m3) - len(m2) - len(m1):-len(m4) - len(m3) - len(m2)] == m1
