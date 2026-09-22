"""food profiles

Revision ID: 20260922_0003
Revises: 20260922_0002
Create Date: 2026-09-22
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260922_0003"
down_revision: str | None = "20260922_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "food_profiles",
        sa.Column("food_profile_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("profile_status", sa.String(length=24), nullable=False, server_default="ACTIVE"),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("profile_status IN ('ACTIVE', 'INACTIVE', 'MERGED')", name="ck_food_profiles_status"),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], name="fk_food_profiles_person", ondelete="CASCADE"),
        sa.UniqueConstraint("person_id", name="uq_food_profiles_person"),
    )

    op.create_table(
        "food_profile_facts",
        sa.Column("fact_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("food_profile_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("fact_type", sa.String(length=64), nullable=False),
        sa.Column("fact_key", sa.String(length=160), nullable=False),
        sa.Column("knowledge_state", sa.String(length=24), nullable=False),
        sa.Column("value_json", postgresql.JSONB(), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("source_kind", sa.String(length=48), nullable=False),
        sa.Column("source_legacy_table", sa.String(length=80), nullable=False),
        sa.Column("source_legacy_id_text", sa.String(length=120), nullable=False),
        sa.Column("confirmation_status", sa.String(length=32), nullable=False, server_default="UNCONFIRMED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "knowledge_state IN ('UNKNOWN', 'NOT_PROVIDED', 'KNOWN_NONE', 'KNOWN_PRESENT')",
            name="ck_food_profile_facts_knowledge_state",
        ),
        sa.CheckConstraint(
            "confirmation_status IN ('UNCONFIRMED', 'CONFIRMED', 'NEEDS_RECONFIRMATION', 'SUPERSEDED')",
            name="ck_food_profile_facts_confirmation_status",
        ),
        sa.CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_food_profile_facts_period"),
        sa.CheckConstraint(
            "(knowledge_state = 'KNOWN_PRESENT' AND value_json IS NOT NULL) OR "
            "(knowledge_state = 'KNOWN_NONE' AND value_json IS NULL) OR "
            "(knowledge_state IN ('UNKNOWN', 'NOT_PROVIDED'))",
            name="ck_food_profile_facts_value_known_state",
        ),
        sa.ForeignKeyConstraint(
            ["food_profile_id"],
            ["food_profiles.food_profile_id"],
            name="fk_food_profile_facts_profile",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "food_profile_id",
            "fact_type",
            "fact_key",
            "source_kind",
            "source_legacy_table",
            "source_legacy_id_text",
            name="uq_food_profile_fact_legacy_source",
        ),
    )
    op.create_index(
        "ix_food_profile_facts_profile_type_state",
        "food_profile_facts",
        ["food_profile_id", "fact_type", "knowledge_state"],
    )
    op.create_index(
        "ix_food_profile_facts_profile_type_time",
        "food_profile_facts",
        ["food_profile_id", "fact_type", "effective_from"],
    )

    op.create_table(
        "food_profile_reconfirmations",
        sa.Column("reconfirmation_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("food_profile_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("fact_type", sa.String(length=64), nullable=False),
        sa.Column("fact_key", sa.String(length=160), nullable=False),
        sa.Column("reason", sa.String(length=160), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="PENDING"),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("source_kind", sa.String(length=48), nullable=False),
        sa.Column("source_legacy_table", sa.String(length=80), nullable=False),
        sa.Column("source_legacy_id_text", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('PENDING', 'RESOLVED', 'DISMISSED', 'SUPERSEDED')",
            name="ck_food_profile_reconfirmations_status",
        ),
        sa.ForeignKeyConstraint(
            ["food_profile_id"],
            ["food_profiles.food_profile_id"],
            name="fk_food_profile_reconfirmations_profile",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "food_profile_id",
            "fact_type",
            "fact_key",
            "reason",
            "source_legacy_table",
            "source_legacy_id_text",
            name="uq_food_profile_reconfirmation_source",
        ),
    )
    op.create_index(
        "ix_food_profile_reconfirmations_profile_status",
        "food_profile_reconfirmations",
        ["food_profile_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_food_profile_reconfirmations_profile_status", table_name="food_profile_reconfirmations")
    op.drop_table("food_profile_reconfirmations")
    op.drop_index("ix_food_profile_facts_profile_type_time", table_name="food_profile_facts")
    op.drop_index("ix_food_profile_facts_profile_type_state", table_name="food_profile_facts")
    op.drop_table("food_profile_facts")
    op.drop_table("food_profiles")
