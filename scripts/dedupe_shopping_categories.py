#!/usr/bin/env python3
"""One-off cleanup for duplicate shopping_categories rows in production.

Shopping list items store category as a slug string in JSONB (family_shopping_lists.items),
not as a FK to shopping_categories.id — no item reassignment is required.

Usage (from repo root):
  python scripts/dedupe_shopping_categories.py
  python scripts/dedupe_shopping_categories.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API_ROOT = os.path.join(ROOT, "apps", "api")
sys.path.insert(0, API_ROOT)

os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal, engine  # noqa: E402
from app.database_migrations import _schema_statements  # noqa: E402

AUDIT_SQL = """
SELECT name, is_system, COUNT(*) AS cnt
FROM shopping_categories
GROUP BY name, is_system
HAVING COUNT(*) > 1
ORDER BY cnt DESC, name;
"""

PER_USER_DUPES_SQL = """
SELECT user_id, name, slug, COUNT(*) AS cnt, ARRAY_AGG(id ORDER BY id) AS ids
FROM shopping_categories
WHERE is_system = TRUE AND user_id IS NOT NULL
GROUP BY user_id, name, slug
HAVING COUNT(*) > 1
ORDER BY cnt DESC;
"""


def _print_rows(title: str, rows) -> None:
    print(f"\n=== {title} ===")
    if not rows:
        print("(none)")
        return
    for row in rows:
        print(dict(row._mapping))


def main() -> int:
    parser = argparse.ArgumentParser(description="Dedupe shopping_categories")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show duplicates only; do not delete or create indexes",
    )
    args = parser.parse_args()

    with engine.connect() as conn:
        _print_rows("Global duplicates by name (audit query)", conn.execute(text(AUDIT_SQL)).fetchall())
        _print_rows(
            "Per-user system duplicates (name+slug)",
            conn.execute(text(PER_USER_DUPES_SQL)).fetchall(),
        )

    if args.dry_run:
        print("\nDry run — no changes applied.")
        return 0

    dedupe_stmts = [
        stmt
        for stmt in _schema_statements()
        if "shopping_categories" in stmt and ("DELETE FROM" in stmt or "CREATE UNIQUE INDEX" in stmt)
    ]

    with engine.begin() as conn:
        for stmt in dedupe_stmts:
            conn.execute(text(stmt))

    print(f"\nApplied {len(dedupe_stmts)} dedupe/index statements.")

    with engine.connect() as conn:
        remaining = conn.execute(text(AUDIT_SQL)).fetchall()
        _print_rows("Remaining global duplicates by name", remaining)

    db = SessionLocal()
    try:
        from app.services.app_scope import AppScope
        from app.services.shopping_category_service import ensure_system_categories

        user_ids = [
            row[0]
            for row in db.execute(
                text(
                    "SELECT DISTINCT user_id FROM shopping_categories "
                    "WHERE user_id IS NOT NULL"
                )
            ).fetchall()
        ]
        for uid in user_ids:
            ensure_system_categories(db, AppScope(mode="personal", user_id=uid))
        print(f"Re-seeded system categories for {len(user_ids)} users (idempotent check).")
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
