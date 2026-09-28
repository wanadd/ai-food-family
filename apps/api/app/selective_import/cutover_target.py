"""Read-only preflight for an Alembic-owned PostgreSQL cutover target."""

from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.selective_import.pipeline import ImportPipelineError


EXPECTED_HEAD = "20260928_0020"
IMPORT_TABLES = (
    "core_accounts", "core_persons", "core_auth_identities", "core_households",
    "core_memberships", "legacy_id_mappings", "food_profiles",
    "food_profile_facts", "food_profile_reconfirmations", "recipes_v2",
    "recipe_versions", "recipe_legacy_mappings", "recipe_archive_fallbacks",
    "shopping_lists", "shopping_items", "entitlement_grants",
    "entitlement_consumptions", "nutrition_target_versions", "notification_preferences",
)
SYSTEM_TABLES = frozenset({"alembic_version", "source_registry", "evidence_sources", "safety_rules"})


def verify_cutover_target(
    engine: Engine, *, expected_database: str, source_database: str,
    expected_head: str, previous_counts: dict[str, int] | None = None,
) -> tuple[str, dict[str, int]]:
    if engine.dialect.name != "postgresql" or expected_head != EXPECTED_HEAD:
        raise ImportPipelineError("CUTOVER target must be PostgreSQL at the approved head")
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    required = {"alembic_version", *IMPORT_TABLES}
    if not required.issubset(tables):
        raise ImportPipelineError("CUTOVER target schema is incomplete")
    checked_tables = sorted(name for name in tables if name not in SYSTEM_TABLES and not name.startswith("cutover_runtime_"))
    with engine.connect() as connection:
        actual_database = connection.execute(text("SELECT current_database()" )).scalar_one()
        if actual_database != expected_database or actual_database.lower() == source_database.lower():
            raise ImportPipelineError("CUTOVER target database identity mismatch")
        heads = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
        if heads != [EXPECTED_HEAD]:
            raise ImportPipelineError("CUTOVER target Alembic head mismatch")
        quote = engine.dialect.identifier_preparer.quote
        counts = {name: int(connection.execute(text(f"SELECT count(*) FROM {quote(name)}")).scalar_one()) for name in checked_tables}
    if previous_counts is None:
        if any(counts.values()):
            raise ImportPipelineError("CUTOVER target already contains canonical import data")
    elif counts != previous_counts:
        raise ImportPipelineError("CUTOVER idempotency target differs from the prior apply")
    return actual_database, counts
