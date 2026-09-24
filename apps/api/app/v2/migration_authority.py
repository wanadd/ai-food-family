from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app import database_migrations


class SchemaAuthority(str, Enum):
    LEGACY_CREATE_ALL = "LEGACY_CREATE_ALL"
    LEGACY_CUSTOM_SQL = "LEGACY_CUSTOM_SQL"
    LEGACY_RECIPE_ENGINE = "LEGACY_RECIPE_ENGINE"
    V2_VERSIONED_MIGRATION = "V2_VERSIONED_MIGRATION"


V2_BASELINE_REVISION = "20260922_0001"
V2_ALEMBIC_VERSION_TABLE = "alembic_version"

V2_VERSIONED_MIGRATION_TABLES: frozenset[str] = frozenset(
    {
        "core_accounts",
        "core_auth_identities",
        "core_persons",
        "core_households",
        "core_memberships",
        "core_person_relationships",
        "core_permission_grants",
        "food_profile_facts",
        "food_profile_reconfirmations",
        "food_profiles",
        "food_aliases",
        "food_composition_facts",
        "food_evidence_fact_links",
        "evidence_applicability",
        "evidence_claims",
        "evidence_records",
        "evidence_sources",
        "legacy_id_mappings",
        "product_label_facts",
        "source_snapshots",
        "nutrition_target_versions",
        "recipes_v2",
        "recipe_versions",
        "recipe_ingredients_v2",
        "recipe_steps_v2",
        "recipe_media_assets",
        "recipe_version_media",
        "recipe_legacy_mappings",
        "recipe_archive_fallbacks",
        "recipe_validation_runs",
    }
)


@dataclass(frozen=True)
class SchemaAuthoritySnapshot:
    legacy_create_all: frozenset[str]
    legacy_custom_sql: frozenset[str]
    legacy_recipe_engine: frozenset[str]
    v2_versioned_migration: frozenset[str]

    def by_authority(self) -> dict[SchemaAuthority, frozenset[str]]:
        return {
            SchemaAuthority.LEGACY_CREATE_ALL: self.legacy_create_all,
            SchemaAuthority.LEGACY_CUSTOM_SQL: self.legacy_custom_sql,
            SchemaAuthority.LEGACY_RECIPE_ENGINE: self.legacy_recipe_engine,
            SchemaAuthority.V2_VERSIONED_MIGRATION: self.v2_versioned_migration,
        }

    @property
    def authority_overlaps(self) -> dict[tuple[SchemaAuthority, SchemaAuthority], frozenset[str]]:
        authorities = list(self.by_authority().items())
        overlaps: dict[tuple[SchemaAuthority, SchemaAuthority], frozenset[str]] = {}
        for index, (left_authority, left_tables) in enumerate(authorities):
            for right_authority, right_tables in authorities[index + 1 :]:
                overlap = left_tables & right_tables
                if overlap:
                    overlaps[(left_authority, right_authority)] = overlap
        return overlaps


def current_schema_authority_snapshot() -> SchemaAuthoritySnapshot:
    return SchemaAuthoritySnapshot(
        legacy_create_all=database_migrations.CREATE_ALL_TABLES,
        legacy_custom_sql=database_migrations.CUSTOM_SQL_TABLES,
        legacy_recipe_engine=database_migrations.RECIPE_ENGINE_TABLES,
        v2_versioned_migration=V2_VERSIONED_MIGRATION_TABLES,
    )


def assert_no_schema_authority_overlaps() -> None:
    overlaps = current_schema_authority_snapshot().authority_overlaps
    if overlaps:
        formatted = "; ".join(
            f"{left.value}/{right.value}: {sorted(tables)}"
            for (left, right), tables in overlaps.items()
        )
        raise RuntimeError(f"schema authority overlaps detected: {formatted}")
