"""NutritionTarget V2 temporal integrity.

Revision ID: 20260924_0005
Revises: 20260922_0004
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260924_0005"
down_revision: str | None = "20260922_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.create_table(
        "nutrition_target_versions",
        sa.Column("target_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("target_kind", sa.String(length=64), nullable=False),
        sa.Column("context_key", sa.String(length=128), nullable=False, server_default="default"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supersedes_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("target_values_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("origin", sa.String(length=32), nullable=False),
        sa.Column("provenance_status", sa.String(length=32), nullable=False, server_default="UNREVIEWED"),
        sa.Column("source_rule_version", sa.String(length=128), nullable=True),
        sa.Column("calculation_version", sa.String(length=128), nullable=True),
        sa.Column("evaluation_date", sa.Date(), nullable=True),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_nutrition_target_v2_period"),
        sa.CheckConstraint("origin IN ('EVIDENCE_BACKED', 'MANUAL', 'CLINICIAN', 'LEGACY_ESTIMATOR')", name="ck_nutrition_target_v2_origin"),
        sa.CheckConstraint("provenance_status IN ('UNREVIEWED', 'REVIEWED', 'AUTHORITATIVE', 'SUPERSEDED')", name="ck_nutrition_target_v2_provenance"),
        sa.CheckConstraint("target_kind <> '' AND context_key <> ''", name="ck_nutrition_target_v2_scope_not_blank"),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], name="fk_nutrition_target_v2_person", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supersedes_id"], ["nutrition_target_versions.target_id"], name="fk_nutrition_target_v2_supersedes", ondelete="SET NULL"),
        sa.UniqueConstraint("person_id", "target_kind", "context_key", "effective_from", name="uq_nutrition_target_v2_start"),
    )
    op.create_index(
        "ix_nutrition_target_v2_person_scope",
        "nutrition_target_versions",
        ["person_id", "target_kind", "context_key", "effective_from"],
    )
    op.execute(
        "ALTER TABLE nutrition_target_versions ADD CONSTRAINT "
        "ex_nutrition_target_v2_no_overlap EXCLUDE USING gist ("
        "person_id WITH =, target_kind WITH =, context_key WITH =, "
        "tstzrange(effective_from, COALESCE(effective_to, 'infinity'::timestamptz), '[)') WITH &&)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE nutrition_target_versions DROP CONSTRAINT IF EXISTS ex_nutrition_target_v2_no_overlap")
    op.drop_index("ix_nutrition_target_v2_person_scope", table_name="nutrition_target_versions")
    op.drop_table("nutrition_target_versions")
