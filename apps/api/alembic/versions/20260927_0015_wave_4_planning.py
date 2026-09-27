"""Canonical Wave 4 planning ownership, revisions and assignments."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260927_0015"
down_revision: str | None = "20260927_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=False)
    json_type = postgresql.JSONB()

    op.create_table(
        "plans",
        sa.Column("plan_id", uuid_type, primary_key=True),
        sa.Column("person_id", uuid_type, nullable=True),
        sa.Column("household_id", uuid_type, nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("request_fingerprint", sa.String(128), nullable=True),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "(person_id IS NOT NULL AND household_id IS NULL) OR "
            "(person_id IS NULL AND household_id IS NOT NULL)",
            name="ck_plans_owner_xor",
        ),
        sa.CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="ck_plans_status"),
        sa.UniqueConstraint("idempotency_key", name="uq_plans_idempotency"),
    )

    op.drop_constraint("plan_revisions_plan_id_fkey", "plan_revisions", type_="foreignkey")
    op.create_foreign_key(
        "fk_plan_revisions_plan",
        "plan_revisions",
        "plans",
        ["plan_id"],
        ["plan_id"],
        ondelete="CASCADE",
    )
    op.add_column("plan_revisions", sa.Column("lifecycle_status", sa.String(24), nullable=False, server_default="DRAFT"))
    op.add_column("plan_revisions", sa.Column("actor_person_id", uuid_type, nullable=True))
    op.add_column("plan_revisions", sa.Column("input_snapshot_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("plan_revisions", sa.Column("safety_snapshot_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("plan_revisions", sa.Column("idempotency_key", sa.String(128), nullable=True))
    op.add_column("plan_revisions", sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("plan_revisions", sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_plan_revisions_actor", "plan_revisions", "core_persons", ["actor_person_id"], ["person_id"], ondelete="SET NULL")
    op.create_unique_constraint("uq_plan_revisions_idempotency", "plan_revisions", ["idempotency_key"])
    op.create_check_constraint(
        "ck_plan_revisions_lifecycle",
        "plan_revisions",
        "lifecycle_status IN ('DRAFT', 'ACTIVE', 'SUPERSEDED')",
    )

    op.drop_constraint("ck_plan_slots_state", "plan_slots", type_="check")
    op.drop_constraint("ck_plan_slots_state_recipe", "plan_slots", type_="check")
    op.create_check_constraint(
        "ck_plan_slots_state_w4",
        "plan_slots",
        "slot_state IN ('ASSIGNED', 'EMPTY', 'FREE', 'CANCELLED')",
    )

    op.create_table(
        "plan_assignments",
        sa.Column("assignment_id", uuid_type, primary_key=True),
        sa.Column("slot_id", uuid_type, nullable=False),
        sa.Column("recipe_version_id", uuid_type, nullable=False),
        sa.Column("source_kind", sa.String(24), nullable=False, server_default="MANUAL"),
        sa.Column("safety_state", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.Column("provenance_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["slot_id"], ["plan_slots.slot_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["recipe_versions.recipe_version_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("source_kind IN ('GENERATED', 'MANUAL', 'REPLACEMENT')", name="ck_plan_assignments_source"),
        sa.CheckConstraint("safety_state IN ('SAFE', 'WARN', 'UNKNOWN', 'ESCALATE')", name="ck_plan_assignments_safety"),
        sa.UniqueConstraint("slot_id", name="uq_plan_assignments_slot"),
        sa.UniqueConstraint("idempotency_key", name="uq_plan_assignments_idempotency"),
    )
    op.create_index("ix_plan_assignments_recipe_version", "plan_assignments", ["recipe_version_id"])

    op.create_table(
        "plan_participants",
        sa.Column("slot_id", uuid_type, nullable=False),
        sa.Column("person_id", uuid_type, nullable=False),
        sa.Column("participation_state", sa.String(24), nullable=False, server_default="PARTICIPATING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["slot_id"], ["plan_slots.slot_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.CheckConstraint("participation_state IN ('PARTICIPATING', 'ABSENT', 'UNKNOWN')", name="ck_plan_participants_state"),
        sa.PrimaryKeyConstraint("slot_id", "person_id"),
    )
    op.create_table(
        "plan_portions",
        sa.Column("slot_id", uuid_type, nullable=False),
        sa.Column("person_id", uuid_type, nullable=False),
        sa.Column("portion_value", sa.Float(), nullable=True),
        sa.Column("portion_unit", sa.String(32), nullable=True),
        sa.Column("source_kind", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.ForeignKeyConstraint(["slot_id"], ["plan_slots.slot_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.CheckConstraint("portion_value IS NULL OR portion_value > 0", name="ck_plan_portions_positive"),
        sa.CheckConstraint("portion_value IS NULL OR portion_unit IS NOT NULL", name="ck_plan_portions_unit"),
        sa.CheckConstraint("source_kind IN ('EXPLICIT', 'ADULT_FALLBACK', 'CHILD_FALLBACK', 'UNKNOWN')", name="ck_plan_portions_source"),
        sa.PrimaryKeyConstraint("slot_id", "person_id"),
    )

    op.execute("DROP TRIGGER IF EXISTS trg_plan_revisions_immutable ON plan_revisions")
    op.execute("DROP FUNCTION IF EXISTS prevent_plan_revision_update()")
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_plan_revision_content_update()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF OLD.plan_id IS DISTINCT FROM NEW.plan_id
               OR OLD.revision_number IS DISTINCT FROM NEW.revision_number
               OR OLD.source_kind IS DISTINCT FROM NEW.source_kind
               OR OLD.metadata_json IS DISTINCT FROM NEW.metadata_json
               OR OLD.input_snapshot_json IS DISTINCT FROM NEW.input_snapshot_json
               OR OLD.safety_snapshot_json IS DISTINCT FROM NEW.safety_snapshot_json
               OR OLD.actor_person_id IS DISTINCT FROM NEW.actor_person_id THEN
                RAISE EXCEPTION 'plan revision % immutable content changed', OLD.revision_id;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_plan_revisions_immutable
        BEFORE UPDATE ON plan_revisions
        FOR EACH ROW EXECUTE FUNCTION prevent_plan_revision_content_update()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_plan_revisions_immutable ON plan_revisions")
    op.execute("DROP FUNCTION IF EXISTS prevent_plan_revision_content_update()")
    op.drop_table("plan_portions")
    op.drop_table("plan_participants")
    op.drop_index("ix_plan_assignments_recipe_version", table_name="plan_assignments")
    op.drop_table("plan_assignments")
    op.drop_constraint("ck_plan_slots_state_w4", "plan_slots", type_="check")
    op.create_check_constraint("ck_plan_slots_state", "plan_slots", "slot_state IN ('EMPTY', 'ASSIGNED')")
    op.create_check_constraint("ck_plan_slots_state_recipe", "plan_slots", "(slot_state = 'EMPTY' AND recipe_version_id IS NULL) OR (slot_state = 'ASSIGNED' AND recipe_version_id IS NOT NULL)")
    op.drop_constraint("ck_plan_revisions_lifecycle", "plan_revisions", type_="check")
    op.drop_constraint("uq_plan_revisions_idempotency", "plan_revisions", type_="unique")
    op.drop_constraint("fk_plan_revisions_actor", "plan_revisions", type_="foreignkey")
    for name in ("superseded_at", "activated_at", "idempotency_key", "safety_snapshot_json", "input_snapshot_json", "actor_person_id", "lifecycle_status"):
        op.drop_column("plan_revisions", name)
    op.drop_constraint("fk_plan_revisions_plan", "plan_revisions", type_="foreignkey")
    op.create_foreign_key("plan_revisions_plan_id_fkey", "plan_revisions", "plans_v2", ["plan_id"], ["plan_id"], ondelete="CASCADE")
    op.drop_table("plans")
