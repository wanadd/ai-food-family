from __future__ import annotations

import ast
import os
import sys
import uuid
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import database_migrations  # noqa: E402
from app.v2 import migration_authority  # noqa: E402
from app.v2.migration_runtime import run_with_schema_migration_lock  # noqa: E402
from app.v2.reference_contracts import (  # noqa: E402
    KnowledgeState,
    ProvenanceState,
    REFERENCE_ENUM_CONTRACTS,
)
from app.v2.uuid7 import is_uuid7, new_uuid7, uuid7_str  # noqa: E402


def _module_tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def test_wave_01_preserves_legacy_authority_counts_and_adds_v2_boundary():
    snapshot = migration_authority.current_schema_authority_snapshot()

    assert len(snapshot.legacy_create_all) == 47
    assert len(snapshot.legacy_custom_sql) == 7
    assert len(snapshot.legacy_recipe_engine) == 6
    assert snapshot.v2_versioned_migration == frozenset()
    assert snapshot.authority_overlaps == {}

    migration_authority.assert_no_schema_authority_overlaps()


def test_v2_authority_includes_all_legacy_sets_without_reclassifying_tables():
    snapshot = migration_authority.current_schema_authority_snapshot()

    assert snapshot.legacy_create_all is database_migrations.CREATE_ALL_TABLES
    assert snapshot.legacy_custom_sql is database_migrations.CUSTOM_SQL_TABLES
    assert snapshot.legacy_recipe_engine is database_migrations.RECIPE_ENGINE_TABLES


def test_v2_baseline_revision_is_marker_only():
    revision_path = API_ROOT / "alembic" / "versions" / "20260922_0001_v2_baseline.py"
    source = revision_path.read_text(encoding="utf-8")
    lowered = source.lower()

    assert 'revision: str = "20260922_0001"' in source
    assert "op.create_table" not in lowered
    assert "create table" not in lowered
    assert "core_accounts" not in lowered
    assert "food_profiles" not in lowered
    assert "recipe_versions" not in lowered


def test_startup_boundary_does_not_run_alembic_or_v2_versioned_migrations():
    database_tree = _module_tree(API_ROOT / "app" / "database.py")
    imported_modules = {
        alias.name
        for node in ast.walk(database_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_from_modules = {
        node.module
        for node in ast.walk(database_tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert "alembic" not in imported_modules
    assert not any(module.startswith("alembic") for module in imported_from_modules)
    assert "app.v2.migration_authority" not in imported_from_modules


def test_reference_enum_contracts_preserve_unknown_and_do_not_collapse_absence():
    assert KnowledgeState.values() == (
        "UNKNOWN",
        "NOT_PROVIDED",
        "KNOWN_NONE",
        "KNOWN_PRESENT",
    )
    assert "AI_PROPOSED" in ProvenanceState.values()
    assert REFERENCE_ENUM_CONTRACTS["KnowledgeState"] == KnowledgeState.values()


def test_uuid7_helper_generates_rfc_variant_version_7_values():
    generated = new_uuid7(now_ns=1_725_000_000_123_456_789)

    assert isinstance(generated, uuid.UUID)
    assert generated.version == 7
    assert generated.variant == uuid.RFC_4122
    assert str(generated).startswith("0191a203-227b-7")
    assert is_uuid7(generated)
    assert is_uuid7(str(generated))


def test_uuid7_string_helper_returns_distinct_parseable_values():
    values = {uuid7_str() for _ in range(64)}

    assert len(values) == 64
    assert all(is_uuid7(value) for value in values)


def test_v2_migration_lock_serializes_postgresql_success_path():
    events: list[str] = []

    class Connection:
        dialect = type("Dialect", (), {"name": "postgresql"})()

        def execute(self, statement, params=None):
            events.append(str(statement))

    run_with_schema_migration_lock(Connection(), lambda: events.append("migrate"))

    assert "pg_advisory_lock" in events[0]
    assert events[1] == "migrate"
    assert "pg_advisory_unlock" in events[2]


def test_v2_migration_lock_preserves_original_failure_when_unlock_fails():
    events: list[str] = []
    original = RuntimeError("migration failed")

    class Connection:
        dialect = type("Dialect", (), {"name": "postgresql"})()

        def execute(self, statement, params=None):
            sql = str(statement)
            events.append(sql)
            if "pg_advisory_unlock" in sql:
                raise RuntimeError("unlock failed")

        def invalidate(self):
            events.append("invalidate")

    try:
        run_with_schema_migration_lock(
            Connection(),
            lambda: (_ for _ in ()).throw(original),
        )
    except RuntimeError as exc:
        assert exc is original
    else:
        raise AssertionError("expected migration failure")

    assert "pg_advisory_lock" in events[0]
    assert "pg_advisory_unlock" in events[1]
    assert events[2] == "invalidate"


def test_v2_migration_lock_is_noop_for_non_postgresql():
    events: list[str] = []

    class Connection:
        dialect = type("Dialect", (), {"name": "sqlite"})()

        def execute(self, statement, params=None):
            events.append(str(statement))

    run_with_schema_migration_lock(Connection(), lambda: events.append("migrate"))

    assert events == ["migrate"]
