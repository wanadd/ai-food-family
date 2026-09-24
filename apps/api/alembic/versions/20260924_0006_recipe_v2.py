"""Recipe V2 and bounded legacy compatibility."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260924_0006"
down_revision: str | None = "20260924_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recipes_v2",
        sa.Column("recipe_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="DRAFT"),
        sa.Column("canonical_key", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')", name="ck_recipes_v2_status"),
        sa.UniqueConstraint("canonical_key", name="uq_recipes_v2_canonical_key"),
    )
    op.create_table(
        "recipe_versions",
        sa.Column("recipe_version_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("recipe_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=24), nullable=False, server_default="DRAFT"),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("servings", sa.Float(), nullable=True),
        sa.Column("yield_amount", sa.Float(), nullable=True),
        sa.Column("yield_unit", sa.String(length=32), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("safety_claims_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("nutrition_projection_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("gold_v3_validation_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes_v2.recipe_id"], name="fk_recipe_versions_recipe", ondelete="CASCADE"),
        sa.CheckConstraint("version_number > 0", name="ck_recipe_versions_number_positive"),
        sa.CheckConstraint("lifecycle_status IN ('DRAFT', 'PUBLISHED', 'RETIRED')", name="ck_recipe_versions_status"),
        sa.CheckConstraint("servings IS NULL OR servings > 0", name="ck_recipe_versions_servings_positive"),
        sa.UniqueConstraint("recipe_id", "version_number", name="uq_recipe_versions_number"),
    )
    op.create_table(
        "recipe_ingredients_v2",
        sa.Column("ingredient_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("recipe_version_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("food_identity_key", sa.String(length=160), nullable=True),
        sa.Column("display_text", sa.String(length=300), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("preparation_expectation", sa.String(length=120), nullable=True),
        sa.Column("product_requirement_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["recipe_versions.recipe_version_id"], name="fk_recipe_ingredients_v2_version", ondelete="CASCADE"),
        sa.CheckConstraint("quantity IS NULL OR quantity > 0", name="ck_recipe_ingredients_v2_quantity_positive"),
        sa.CheckConstraint("quantity IS NULL OR unit IS NOT NULL", name="ck_recipe_ingredients_v2_quantity_unit"),
    )
    op.create_index("ix_recipe_ingredients_v2_version", "recipe_ingredients_v2", ["recipe_version_id", "sort_order"])
    op.create_table(
        "recipe_steps_v2",
        sa.Column("step_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("recipe_version_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("expected_process_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["recipe_versions.recipe_version_id"], name="fk_recipe_steps_v2_version", ondelete="CASCADE"),
        sa.UniqueConstraint("recipe_version_id", "step_number", name="uq_recipe_steps_v2_number"),
    )
    op.create_table(
        "recipe_media_assets",
        sa.Column("media_asset_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("media_role", sa.String(length=32), nullable=False),
        sa.Column("storage_ref", sa.String(length=512), nullable=False),
        sa.Column("public_url", sa.String(length=512), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("media_role IN ('MASTER', 'HERO', 'CARD', 'THUMBNAIL')", name="ck_recipe_media_role"),
    )
    op.create_table(
        "recipe_version_media",
        sa.Column("recipe_version_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("media_asset_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["recipe_versions.recipe_version_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_asset_id"], ["recipe_media_assets.media_asset_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("recipe_version_id", "media_asset_id"),
    )
    op.create_table(
        "recipe_legacy_mappings",
        sa.Column("mapping_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("legacy_recipe_id", sa.Integer(), nullable=False),
        sa.Column("canonical_recipe_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("canonical_version_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("mapping_status", sa.String(length=24), nullable=False),
        sa.Column("mapping_reason", sa.String(length=160), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["canonical_recipe_id"], ["recipes_v2.recipe_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["canonical_version_id"], ["recipe_versions.recipe_version_id"], ondelete="SET NULL"),
        sa.CheckConstraint("mapping_status IN ('MAPPED', 'ARCHIVE_FALLBACK', 'REVIEW_REQUIRED')", name="ck_recipe_legacy_mapping_status"),
        sa.UniqueConstraint("legacy_recipe_id", name="uq_recipe_legacy_mapping_legacy_id"),
    )
    op.create_table(
        "recipe_archive_fallbacks",
        sa.Column("legacy_recipe_id", sa.Integer(), primary_key=True),
        sa.Column("archive_payload_json", postgresql.JSONB(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("source_kind", sa.String(length=48), nullable=False, server_default="LEGACY_ARCHIVE"),
    )
    op.create_table(
        "recipe_validation_runs",
        sa.Column("validation_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("recipe_version_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("validator_name", sa.String(length=96), nullable=False),
        sa.Column("validator_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("result_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["recipe_versions.recipe_version_id"], ondelete="CASCADE"),
        sa.CheckConstraint("status IN ('PASS', 'FAIL', 'REVIEW_REQUIRED')", name="ck_recipe_validation_status"),
    )
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_published_recipe_version_update()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF OLD.lifecycle_status IN ('PUBLISHED', 'RETIRED') THEN
                RAISE EXCEPTION 'immutable recipe version % cannot be updated', OLD.recipe_version_id;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_recipe_versions_immutable
        BEFORE UPDATE ON recipe_versions
        FOR EACH ROW EXECUTE FUNCTION prevent_published_recipe_version_update()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_recipe_versions_immutable ON recipe_versions")
    op.execute("DROP FUNCTION IF EXISTS prevent_published_recipe_version_update()")
    op.drop_table("recipe_validation_runs")
    op.drop_table("recipe_archive_fallbacks")
    op.drop_table("recipe_legacy_mappings")
    op.drop_table("recipe_version_media")
    op.drop_table("recipe_media_assets")
    op.drop_table("recipe_steps_v2")
    op.drop_index("ix_recipe_ingredients_v2_version", table_name="recipe_ingredients_v2")
    op.drop_table("recipe_ingredients_v2")
    op.drop_table("recipe_versions")
    op.drop_table("recipes_v2")
