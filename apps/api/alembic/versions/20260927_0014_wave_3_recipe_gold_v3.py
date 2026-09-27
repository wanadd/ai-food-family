"""Wave 3 canonical Recipe Gold V3 contract."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260927_0014"
down_revision: str | None = "20260927_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_type = postgresql.JSONB()
    for name, column in (
        ("gold_v3_payload_json", sa.Column("gold_v3_payload_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb"))),
        ("source_provenance_json", sa.Column("source_provenance_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb"))),
        ("originality_json", sa.Column("originality_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb"))),
        ("quality_score", sa.Column("quality_score", sa.Integer(), nullable=True)),
        ("publication_reason", sa.Column("publication_reason", sa.String(160), nullable=True)),
        ("last_idempotency_key", sa.Column("last_idempotency_key", sa.String(128), nullable=True)),
    ):
        op.add_column("recipe_versions", column)
    op.create_check_constraint(
        "ck_recipe_versions_quality_score",
        "recipe_versions",
        "quality_score IS NULL OR quality_score BETWEEN 0 AND 100",
    )

    for column in (
        sa.Column("shopping_name", sa.String(160), nullable=True),
        sa.Column("normalized_quantity", sa.Float(), nullable=True),
        sa.Column("normalized_unit", sa.String(32), nullable=True),
        sa.Column("quantity_mode", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("optional", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("process_state", sa.String(48), nullable=True),
        sa.Column("mapping_status", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column("mapping_provenance_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
    ):
        op.add_column("recipe_ingredients_v2", column)
    op.create_check_constraint(
        "ck_recipe_ingredients_v2_normalized_quantity_positive",
        "recipe_ingredients_v2",
        "normalized_quantity IS NULL OR normalized_quantity > 0",
    )

    for column in (
        sa.Column("content_hash", sa.String(128), nullable=True),
        sa.Column("provenance_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(24), nullable=False, server_default="READY"),
    ):
        op.add_column("recipe_media_assets", column)
    op.create_index("ix_recipe_media_assets_content_hash", "recipe_media_assets", ["content_hash"])

    op.create_table(
        "recipe_version_tags_v2",
        sa.Column("tag_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("recipe_version_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tag_type", sa.String(32), nullable=False, server_default="GENERAL"),
        sa.Column("tag_value", sa.String(96), nullable=False),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["recipe_versions.recipe_version_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("recipe_version_id", "tag_type", "tag_value", name="uq_recipe_version_tag_v2"),
    )

    op.create_table(
        "recipe_favorites_v2",
        sa.Column("favorite_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("recipe_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["account_id"], ["core_accounts.account_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes_v2.recipe_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["version_id"], ["recipe_versions.recipe_version_id"], ondelete="SET NULL"),
        sa.UniqueConstraint("account_id", "recipe_id", name="uq_recipe_favorite_v2_account_recipe"),
        sa.UniqueConstraint("account_id", "idempotency_key", name="uq_recipe_favorite_v2_idempotency"),
    )


def downgrade() -> None:
    op.drop_table("recipe_favorites_v2")
    op.drop_table("recipe_version_tags_v2")
    op.drop_index("ix_recipe_media_assets_content_hash", table_name="recipe_media_assets")
    for name in ("status", "provenance_json", "content_hash"):
        op.drop_column("recipe_media_assets", name)
    op.drop_constraint("ck_recipe_ingredients_v2_normalized_quantity_positive", "recipe_ingredients_v2", type_="check")
    for name in ("mapping_provenance_json", "mapping_status", "process_state", "optional", "quantity_mode", "normalized_unit", "normalized_quantity", "shopping_name"):
        op.drop_column("recipe_ingredients_v2", name)
    op.drop_constraint("ck_recipe_versions_quality_score", "recipe_versions", type_="check")
    for name in ("last_idempotency_key", "publication_reason", "quality_score", "originality_json", "source_provenance_json", "gold_v3_payload_json"):
        op.drop_column("recipe_versions", name)
