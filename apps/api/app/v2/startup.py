from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import inspect, text

from app.v2.migration_authority import V2_MIGRATION_HEAD, V2_VERSIONED_MIGRATION_TABLES


@dataclass(frozen=True)
class SchemaCompatibility:
    compatible: bool
    migration_head: str | None
    missing_tables: tuple[str, ...]


def check_v2_schema_compatibility(engine, *, expected_head: str = V2_MIGRATION_HEAD) -> SchemaCompatibility:
    """Read-only startup gate; ordinary workers never repair schema with DDL."""
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    missing = tuple(sorted(V2_VERSIONED_MIGRATION_TABLES - existing))
    head: str | None = None
    if "alembic_version" in existing:
        with engine.connect() as connection:
            head = connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar_one_or_none()
    return SchemaCompatibility(compatible=head == expected_head and not missing, migration_head=head, missing_tables=missing)


def assert_v2_schema_compatible(engine, *, expected_head: str = V2_MIGRATION_HEAD) -> None:
    result = check_v2_schema_compatibility(engine, expected_head=expected_head)
    if not result.compatible:
        raise RuntimeError(
            f"V2 schema is incompatible: head={result.migration_head!r}, "
            f"expected={expected_head!r}, missing={list(result.missing_tables)!r}"
        )
