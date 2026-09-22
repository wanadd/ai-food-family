from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import Connection, text

V2_MIGRATION_ADVISORY_LOCK_ID = 906_220_001


def run_with_schema_migration_lock(connection: Connection, migrate: Callable[[], None]) -> None:
    """Serialize PostgreSQL V2 migrations without making startup a DDL authority."""
    if connection.dialect.name != "postgresql":
        migrate()
        return

    lock_acquired = False
    try:
        connection.execute(
            text("SELECT pg_advisory_lock(:lock_id)"),
            {"lock_id": V2_MIGRATION_ADVISORY_LOCK_ID},
        )
        lock_acquired = True
        migrate()
    except BaseException:
        if lock_acquired:
            try:
                connection.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"),
                    {"lock_id": V2_MIGRATION_ADVISORY_LOCK_ID},
                )
            except BaseException:
                try:
                    connection.invalidate()
                except BaseException:
                    pass
        raise
    else:
        if lock_acquired:
            connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": V2_MIGRATION_ADVISORY_LOCK_ID},
            )
