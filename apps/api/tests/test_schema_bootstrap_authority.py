from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import Column, Integer, MetaData, Table

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import database_migrations as migrations  # noqa: E402


def test_schema_authority_sets_are_explicit_and_disjoint():
    assert migrations.CREATE_ALL_TABLES
    assert migrations.CUSTOM_SQL_TABLES
    assert migrations.RECIPE_ENGINE_TABLES
    assert not migrations.CREATE_ALL_TABLES & migrations.CUSTOM_SQL_TABLES
    assert not migrations.CREATE_ALL_TABLES & migrations.RECIPE_ENGINE_TABLES
    assert not migrations.CUSTOM_SQL_TABLES & migrations.RECIPE_ENGINE_TABLES

    assert migrations.M1_CUSTOM_TABLES <= migrations.CUSTOM_SQL_TABLES
    assert migrations.M1_CUSTOM_TABLES.isdisjoint(migrations.CREATE_ALL_TABLES)
    assert migrations.M1_CUSTOM_TABLES.isdisjoint(migrations.RECIPE_ENGINE_TABLES)


def test_positive_allowlist_does_not_auto_own_future_metadata_tables():
    metadata = MetaData()
    Table("users", metadata, Column("id", Integer, primary_key=True))
    Table("future_custom_evidence", metadata, Column("id", Integer, primary_key=True))
    base = SimpleNamespace(metadata=metadata)

    selected = migrations._metadata_tables_for_authority(
        base,
        migrations.CREATE_ALL_TABLES,
    )

    assert {table.name for table in selected} == {"users"}
    assert "future_custom_evidence" not in {
        table.name for table in selected
    }


def test_custom_post_phase_does_not_create_allowlisted_tables():
    sql = "\n".join(migrations._custom_post_create_statements())

    for table_name in migrations.CREATE_ALL_TABLES:
        assert f"CREATE TABLE {table_name}" not in sql
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" not in sql

    assert "CREATE TABLE recipe_collections" in sql
    assert "CREATE TABLE IF NOT EXISTS deferred_nutrition_advice" in sql
    assert "CREATE TABLE food_identities" not in sql
    assert "ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS food_identity_id" in sql


def test_bootstrap_order_keeps_lock_and_authority_phases(monkeypatch):
    events: list[tuple[str, object]] = []

    class Connection:
        def rollback(self):
            events.append(("rollback", None))

        def invalidate(self):
            events.append(("invalidate", None))

        def execute(self, statement, params=None):
            events.append(("connection", str(statement)))

    class Begin:
        def __enter__(self):
            return Connection()

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    class Engine:
        def begin(self):
            return Begin()

    def record_create_all(connection, base, table_names):
        events.append(("create_all", frozenset(table_names)))

    def record_sql(connection, statements):
        first = statements[0] if statements else ""
        phase = "m1" if "food_identities" in first else "post"
        events.append((phase, len(statements)))

    monkeypatch.setattr(migrations, "_create_all_allowlisted", record_create_all)
    monkeypatch.setattr(migrations, "_execute_statements", record_sql)

    import app.services.shopping_category_migration as shopping_migration

    monkeypatch.setattr(
        shopping_migration,
        "migrate_shopping_categories_v1",
        lambda connection: events.append(("shopping_categories", None)),
    )

    migrations.ensure_database_schema(Engine(), SimpleNamespace())

    phases = [event[0] for event in events]
    assert phases[:5] == [
        "connection",
        "create_all",
        "m1",
        "create_all",
        "post",
    ]
    assert phases[-2:] == ["shopping_categories", "connection"]
    assert events[1][1] == migrations.LEGACY_PREREQUISITE_TABLES
    assert events[3][1] == migrations.CREATE_ALL_TABLES - migrations.LEGACY_PREREQUISITE_TABLES
    assert "pg_advisory_lock" in events[0][1]
    assert "pg_advisory_unlock" in events[-1][1]


def test_bootstrap_failure_rolls_back_before_unlock_and_reraises_original(monkeypatch):
    events: list[str] = []
    original = RuntimeError("bootstrap failed")

    class Connection:
        def execute(self, statement, params=None):
            sql = str(statement)
            events.append(sql)

        def rollback(self):
            events.append("rollback")

        def invalidate(self):
            events.append("invalidate")

    class Begin:
        def __enter__(self):
            return Connection()

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    class Engine:
        def begin(self):
            return Begin()

    monkeypatch.setattr(
        migrations,
        "_create_all_allowlisted",
        lambda connection, base, table_names: (_ for _ in ()).throw(original),
    )

    try:
        migrations.ensure_database_schema(Engine(), SimpleNamespace())
    except RuntimeError as exc:
        assert exc is original
    else:
        raise AssertionError("expected bootstrap failure")

    assert events[0].startswith("SELECT pg_advisory_lock")
    assert events[1] == "rollback"
    assert "pg_advisory_unlock" in events[2]
    assert "invalidate" not in events


def test_unlock_failure_does_not_replace_original_exception(monkeypatch):
    events: list[str] = []
    original = RuntimeError("bootstrap failed")
    unlock_failure = RuntimeError("unlock failed")

    class Connection:
        def execute(self, statement, params=None):
            sql = str(statement)
            events.append(sql)
            if "pg_advisory_unlock" in sql:
                raise unlock_failure

        def rollback(self):
            events.append("rollback")

        def invalidate(self):
            events.append("invalidate")

    class Begin:
        def __enter__(self):
            return Connection()

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    class Engine:
        def begin(self):
            return Begin()

    monkeypatch.setattr(
        migrations,
        "_create_all_allowlisted",
        lambda connection, base, table_names: (_ for _ in ()).throw(original),
    )

    try:
        migrations.ensure_database_schema(Engine(), SimpleNamespace())
    except RuntimeError as exc:
        assert exc is original
    else:
        raise AssertionError("expected bootstrap failure")

    assert events[1] == "rollback"
    assert "pg_advisory_unlock" in events[2]
    assert events[3] == "invalidate"


def test_normal_contention_path_still_unlocks_after_success(monkeypatch):
    events: list[str] = []

    class Connection:
        def execute(self, statement, params=None):
            events.append(str(statement))

        def rollback(self):
            events.append("rollback")

        def invalidate(self):
            events.append("invalidate")

    class Begin:
        def __enter__(self):
            return Connection()

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    class Engine:
        def begin(self):
            return Begin()

    monkeypatch.setattr(migrations, "_create_all_allowlisted", lambda *args: None)
    monkeypatch.setattr(migrations, "_execute_statements", lambda *args: None)

    import app.services.shopping_category_migration as shopping_migration

    monkeypatch.setattr(
        shopping_migration,
        "migrate_shopping_categories_v1",
        lambda connection: None,
    )

    migrations.ensure_database_schema(Engine(), SimpleNamespace())

    assert "pg_advisory_lock" in events[0]
    assert "pg_advisory_unlock" in events[-1]
    assert "rollback" not in events
    assert "invalidate" not in events


def test_bootstrap_phase_order_is_stable():
    assert migrations._bootstrap_phase_order() == (
        "legacy_prerequisites",
        "m1_pre_create",
        "legacy_create_all",
        "custom_post_create",
    )
