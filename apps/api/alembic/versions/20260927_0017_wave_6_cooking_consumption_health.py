"""Canonical Wave 6 cooking, consumption and health foundations."""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260927_0017"
down_revision: str | None = "20260927_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    uid = postgresql.UUID(as_uuid=False)
    js = postgresql.JSONB()
    op.create_table(
        "cooking_sessions",
        sa.Column("cooking_session_id", uid, primary_key=True),
        sa.Column("household_id", uid, nullable=False),
        sa.Column("recipe_version_id", uid, nullable=True),
        sa.Column("plan_slot_id", uid, nullable=True),
        sa.Column("state", sa.String(24), nullable=False, server_default="STARTED"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["recipe_versions.recipe_version_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["plan_slot_id"], ["plan_slots.slot_id"], ondelete="SET NULL"),
        sa.CheckConstraint("state IN ('STARTED', 'COMPLETED', 'CANCELLED')", name="ck_cooking_sessions_state"),
        sa.UniqueConstraint("household_id", "idempotency_key", name="uq_cooking_sessions_idempotency"),
    )
    op.create_index("ix_cooking_sessions_household", "cooking_sessions", ["household_id", "started_at"])

    op.create_table(
        "prepared_foods",
        sa.Column("prepared_food_id", uid, primary_key=True),
        sa.Column("session_id", uid, nullable=False),
        sa.Column("household_id", uid, nullable=False),
        sa.Column("recipe_version_id", uid, nullable=True),
        sa.Column("display_name", sa.String(240), nullable=True),
        sa.Column("yield_quantity", sa.Float(), nullable=True),
        sa.Column("yield_unit", sa.String(32), nullable=True),
        sa.Column("yield_servings", sa.Float(), nullable=True),
        sa.Column("state", sa.String(24), nullable=False, server_default="PREPARED"),
        sa.Column("provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["session_id"], ["cooking_sessions.cooking_session_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["recipe_versions.recipe_version_id"], ondelete="SET NULL"),
        sa.CheckConstraint("yield_quantity IS NULL OR yield_quantity > 0", name="ck_prepared_foods_yield_positive"),
        sa.CheckConstraint("yield_servings IS NULL OR yield_servings > 0", name="ck_prepared_foods_servings_positive"),
        sa.CheckConstraint("yield_quantity IS NULL OR yield_unit IS NOT NULL", name="ck_prepared_foods_yield_unit"),
        sa.CheckConstraint("state IN ('PREPARED', 'DEPLETED', 'ARCHIVED')", name="ck_prepared_foods_state"),
        sa.UniqueConstraint("session_id", name="uq_prepared_foods_session"),
    )

    op.create_table(
        "cooking_events",
        sa.Column("cooking_event_id", uid, primary_key=True),
        sa.Column("session_id", uid, nullable=False),
        sa.Column("household_id", uid, nullable=False),
        sa.Column("event_kind", sa.String(32), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("payload_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["cooking_sessions.cooking_session_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.CheckConstraint("event_kind IN ('STARTED', 'COMPLETED', 'CORRECTION')", name="ck_cooking_events_kind"),
        sa.UniqueConstraint("household_id", "idempotency_key", name="uq_cooking_events_idempotency"),
    )

    op.create_table(
        "consumption_events",
        sa.Column("consumption_event_id", uid, primary_key=True),
        sa.Column("person_id", uid, nullable=False),
        sa.Column("household_id", uid, nullable=False),
        sa.Column("plan_slot_id", uid, nullable=True),
        sa.Column("recipe_version_id", uid, nullable=True),
        sa.Column("cooking_session_id", uid, nullable=True),
        sa.Column("source_kind", sa.String(32), nullable=False),
        sa.Column("state", sa.String(24), nullable=False, server_default="CONFIRMED"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("portion_state", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("confidence", sa.String(24), nullable=False, server_default="CONFIRMED"),
        sa.Column("external_description", sa.String(500), nullable=True),
        sa.Column("correction_of_event_id", uid, nullable=True),
        sa.Column("provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_slot_id"], ["plan_slots.slot_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["recipe_versions.recipe_version_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cooking_session_id"], ["cooking_sessions.cooking_session_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["correction_of_event_id"], ["consumption_events.consumption_event_id"], ondelete="SET NULL"),
        sa.CheckConstraint("source_kind IN ('PLANNED_RECIPE', 'COOKED_FOOD', 'EXTERNAL_MEAL', 'MANUAL', 'AI_PROPOSAL')", name="ck_consumption_events_source"),
        sa.CheckConstraint("state IN ('CONFIRMED', 'CORRECTED', 'RETRACTED')", name="ck_consumption_events_state"),
        sa.CheckConstraint("portion_state IN ('KNOWN', 'UNKNOWN', 'ESTIMATED')", name="ck_consumption_events_portion"),
        sa.CheckConstraint("confidence IN ('UNKNOWN', 'ESTIMATED', 'CONFIRMED')", name="ck_consumption_events_confidence"),
        sa.UniqueConstraint("household_id", "idempotency_key", name="uq_consumption_events_idempotency"),
    )
    op.create_index("ix_consumption_events_person_time", "consumption_events", ["person_id", "occurred_at"])

    op.create_table(
        "consumption_items",
        sa.Column("consumption_item_id", uid, primary_key=True),
        sa.Column("consumption_event_id", uid, nullable=False),
        sa.Column("person_id", uid, nullable=False),
        sa.Column("food_identity_key", sa.String(160), nullable=True),
        sa.Column("product_instance_key", sa.String(160), nullable=True),
        sa.Column("display_text", sa.String(240), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("nutrition_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("nutrition_provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["consumption_event_id"], ["consumption_events.consumption_event_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.CheckConstraint("quantity IS NULL OR quantity > 0", name="ck_consumption_items_quantity_positive"),
        sa.CheckConstraint("quantity IS NULL OR unit IS NOT NULL", name="ck_consumption_items_quantity_unit"),
        sa.CheckConstraint("food_identity_key IS NOT NULL OR product_instance_key IS NOT NULL OR display_text IS NOT NULL", name="ck_consumption_items_identity"),
    )

    op.create_table(
        "health_projections",
        sa.Column("projection_id", uid, primary_key=True),
        sa.Column("person_id", uid, nullable=False),
        sa.Column("projection_date", sa.Date(), nullable=False),
        sa.Column("completeness", sa.String(24), nullable=False),
        sa.Column("planned_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("actual_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("deviation_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("safety_status", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("source_refs_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("calculation_version", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.CheckConstraint("completeness IN ('COMPLETE', 'PARTIAL', 'UNKNOWN')", name="ck_health_projections_completeness"),
        sa.CheckConstraint("safety_status IN ('BLOCK', 'ESCALATE', 'UNKNOWN', 'WARN', 'SAFE')", name="ck_health_projections_safety"),
        sa.UniqueConstraint("person_id", "projection_date", "calculation_version", name="uq_health_projections_version"),
    )

    op.create_table(
        "health_deviations",
        sa.Column("deviation_id", uid, primary_key=True),
        sa.Column("projection_id", uid, nullable=False),
        sa.Column("person_id", uid, nullable=False),
        sa.Column("deviation_kind", sa.String(48), nullable=False),
        sa.Column("severity", sa.String(24), nullable=False),
        sa.Column("known_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("unknown_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["projection_id"], ["health_projections.projection_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.CheckConstraint("severity IN ('INFO', 'WARN', 'ESCALATE', 'BLOCK', 'UNKNOWN')", name="ck_health_deviations_severity"),
    )
    op.create_index("ix_health_deviations_person", "health_deviations", ["person_id", "deviation_id"])


def downgrade() -> None:
    op.drop_index("ix_health_deviations_person", table_name="health_deviations")
    op.drop_table("health_deviations")
    op.drop_table("health_projections")
    op.drop_table("consumption_items")
    op.drop_index("ix_consumption_events_person_time", table_name="consumption_events")
    op.drop_table("consumption_events")
    op.drop_table("cooking_events")
    op.drop_table("prepared_foods")
    op.drop_index("ix_cooking_sessions_household", table_name="cooking_sessions")
    op.drop_table("cooking_sessions")
