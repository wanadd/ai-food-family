"""Planning V2 with immutable revisions and explicit empty slots."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260924_0007"
down_revision: str | None = "20260924_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "plans_v2",
        sa.Column("plan_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("household_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("owner_person_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("plan_kind", sa.String(length=32), nullable=False, server_default="HOUSEHOLD"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_person_id"], ["core_persons.person_id"], ondelete="SET NULL"),
        sa.CheckConstraint("plan_kind IN ('HOUSEHOLD', 'PERSONAL')", name="ck_plans_v2_kind"),
        sa.CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="ck_plans_v2_status"),
    )
    op.create_table(
        "plan_revisions",
        sa.Column("revision_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("source_kind", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["plan_id"], ["plans_v2.plan_id"], ondelete="CASCADE"),
        sa.CheckConstraint("revision_number > 0", name="ck_plan_revisions_number_positive"),
        sa.CheckConstraint("source_kind IN ('AI_GENERATED', 'MANUAL', 'REPLACEMENT', 'LEGACY_MIGRATION', 'SYSTEM_REPAIR')", name="ck_plan_revisions_source"),
        sa.UniqueConstraint("plan_id", "revision_number", name="uq_plan_revisions_number"),
    )
    op.create_table(
        "plan_slots",
        sa.Column("slot_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("revision_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("slot_key", sa.String(length=96), nullable=False),
        sa.Column("planned_date", sa.Date(), nullable=False),
        sa.Column("meal_type", sa.String(length=32), nullable=False),
        sa.Column("slot_state", sa.String(length=24), nullable=False, server_default="EMPTY"),
        sa.Column("recipe_version_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("manual_override", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["revision_id"], ["plan_revisions.revision_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["recipe_versions.recipe_version_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("slot_state IN ('EMPTY', 'ASSIGNED')", name="ck_plan_slots_state"),
        sa.CheckConstraint("(slot_state = 'EMPTY' AND recipe_version_id IS NULL) OR (slot_state = 'ASSIGNED' AND recipe_version_id IS NOT NULL)", name="ck_plan_slots_state_recipe"),
        sa.UniqueConstraint("revision_id", "slot_key", name="uq_plan_slots_revision_key"),
    )
    op.create_table(
        "plan_slot_participants",
        sa.Column("slot_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("participation_state", sa.String(length=24), nullable=False, server_default="PARTICIPATING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["slot_id"], ["plan_slots.slot_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.CheckConstraint("participation_state IN ('PARTICIPATING', 'ABSENT', 'UNKNOWN')", name="ck_plan_slot_participation"),
        sa.PrimaryKeyConstraint("slot_id", "person_id"),
    )
    op.create_table(
        "plan_slot_portions",
        sa.Column("slot_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("portion_value", sa.Float(), nullable=True),
        sa.Column("portion_unit", sa.String(length=32), nullable=True),
        sa.Column("source_kind", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
        sa.ForeignKeyConstraint(["slot_id"], ["plan_slots.slot_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.CheckConstraint("portion_value IS NULL OR portion_value > 0", name="ck_plan_slot_portion_positive"),
        sa.CheckConstraint("portion_value IS NULL OR portion_unit IS NOT NULL", name="ck_plan_slot_portion_unit"),
        sa.CheckConstraint("source_kind IN ('EXPLICIT', 'ADULT_FALLBACK', 'CHILD_FALLBACK', 'UNKNOWN')", name="ck_plan_slot_portion_source"),
        sa.PrimaryKeyConstraint("slot_id", "person_id"),
    )
    op.create_table(
        "plan_legacy_mappings",
        sa.Column("mapping_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("legacy_menu_id", sa.Integer(), nullable=False),
        sa.Column("canonical_plan_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("mapping_status", sa.String(length=24), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["canonical_plan_id"], ["plans_v2.plan_id"], ondelete="SET NULL"),
        sa.CheckConstraint("mapping_status IN ('MAPPED', 'COMPATIBILITY', 'REVIEW_REQUIRED')", name="ck_plan_legacy_mapping_status"),
        sa.UniqueConstraint("legacy_menu_id", name="uq_plan_legacy_mapping_menu"),
    )
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_plan_revision_update()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'plan revision % is immutable', OLD.revision_id;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_plan_revisions_immutable
        BEFORE UPDATE ON plan_revisions
        FOR EACH ROW EXECUTE FUNCTION prevent_plan_revision_update()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_plan_revisions_immutable ON plan_revisions")
    op.execute("DROP FUNCTION IF EXISTS prevent_plan_revision_update()")
    op.drop_table("plan_legacy_mappings")
    op.drop_table("plan_slot_portions")
    op.drop_table("plan_slot_participants")
    op.drop_table("plan_slots")
    op.drop_table("plan_revisions")
    op.drop_table("plans_v2")
