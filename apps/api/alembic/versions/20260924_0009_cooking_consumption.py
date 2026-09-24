"""Cooking and person-scoped consumption V2."""
from __future__ import annotations
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260924_0009"
down_revision: str | None = "20260924_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
UUID = lambda: postgresql.UUID(as_uuid=False)
JSON = lambda: postgresql.JSONB()

def upgrade() -> None:
    op.create_table(
        "cooking_batches_v2",
        sa.Column("cooking_batch_id", UUID(), primary_key=True),
        sa.Column("household_id", UUID(), nullable=False),
        sa.Column("recipe_version_id", UUID(), nullable=True),
        sa.Column("plan_slot_id", UUID(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="PLANNED"),
        sa.Column("actual_yield", sa.Float(), nullable=True),
        sa.Column("actual_yield_unit", sa.String(32), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("completion_idempotency_key", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["recipe_versions.recipe_version_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["plan_slot_id"], ["plan_slots.slot_id"], ondelete="SET NULL"),
        sa.CheckConstraint("status IN ('PLANNED', 'STARTED', 'COMPLETED', 'CANCELLED')", name="ck_cooking_batch_v2_status"),
        sa.CheckConstraint("actual_yield IS NULL OR actual_yield > 0", name="ck_cooking_batch_v2_yield_positive"),
        sa.UniqueConstraint("completion_idempotency_key", name="uq_cooking_batch_completion_key"),
    )
    op.create_table(
        "cooking_events_v2",
        sa.Column("cooking_event_id", UUID(), primary_key=True),
        sa.Column("cooking_batch_id", UUID(), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("actual_product_instance_id", sa.String(120), nullable=True),
        sa.Column("process_state", sa.String(64), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("payload_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.ForeignKeyConstraint(["cooking_batch_id"], ["cooking_batches_v2.cooking_batch_id"], ondelete="CASCADE"),
        sa.CheckConstraint("event_type IN ('STARTED', 'COMPLETED', 'SUBSTITUTION', 'PRODUCT_USED', 'HEAT_TREATMENT', 'YIELD_ADJUSTMENT', 'CORRECTION')", name="ck_cooking_event_v2_type"),
        sa.UniqueConstraint("idempotency_key", name="uq_cooking_event_v2_idempotency"),
    )
    op.create_table(
        "cooking_substitutions_v2",
        sa.Column("substitution_id", UUID(), primary_key=True),
        sa.Column("cooking_batch_id", UUID(), nullable=False),
        sa.Column("planned_food_identity_key", sa.String(160), nullable=True),
        sa.Column("actual_food_identity_key", sa.String(160), nullable=True),
        sa.Column("actual_product_instance_id", sa.String(120), nullable=True),
        sa.Column("reason", sa.String(300), nullable=True),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["cooking_batch_id"], ["cooking_batches_v2.cooking_batch_id"], ondelete="CASCADE"),
        sa.CheckConstraint("actual_food_identity_key IS NOT NULL OR actual_product_instance_id IS NOT NULL", name="ck_cooking_substitution_actual"),
    )
    op.create_table(
        "consumption_events_v2",
        sa.Column("consumption_event_id", UUID(), primary_key=True),
        sa.Column("person_id", UUID(), nullable=False),
        sa.Column("cooking_batch_id", UUID(), nullable=True),
        sa.Column("recipe_version_id", UUID(), nullable=True),
        sa.Column("plan_slot_id", UUID(), nullable=True),
        sa.Column("external_description", sa.String(500), nullable=True),
        sa.Column("source_kind", sa.String(32), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="PROPOSED"),
        sa.Column("actual_portion", sa.Float(), nullable=True),
        sa.Column("actual_portion_unit", sa.String(32), nullable=True),
        sa.Column("portion_state", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("nutrition_state", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("consumption_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cooking_batch_id"], ["cooking_batches_v2.cooking_batch_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["recipe_versions.recipe_version_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["plan_slot_id"], ["plan_slots.slot_id"], ondelete="SET NULL"),
        sa.CheckConstraint("source_kind IN ('COOKING_BATCH', 'PLANNED_RECIPE', 'EXTERNAL_MEAL', 'AI_PROPOSAL', 'MANUAL')", name="ck_consumption_source_kind"),
        sa.CheckConstraint("status IN ('PROPOSED', 'CONFIRMED', 'CORRECTED', 'REJECTED')", name="ck_consumption_status"),
        sa.CheckConstraint("actual_portion IS NULL OR actual_portion > 0", name="ck_consumption_portion_positive"),
        sa.CheckConstraint("actual_portion IS NULL OR actual_portion_unit IS NOT NULL", name="ck_consumption_portion_unit"),
        sa.CheckConstraint("portion_state IN ('KNOWN', 'UNKNOWN', 'ESTIMATED')", name="ck_consumption_portion_state"),
        sa.CheckConstraint("nutrition_state IN ('KNOWN', 'UNKNOWN', 'ESTIMATED', 'INCOMPLETE')", name="ck_consumption_nutrition_state"),
        sa.UniqueConstraint("idempotency_key", name="uq_consumption_idempotency"),
    )
    op.create_table(
        "consumption_items_v2",
        sa.Column("consumption_item_id", UUID(), primary_key=True),
        sa.Column("consumption_event_id", UUID(), nullable=False),
        sa.Column("food_identity_key", sa.String(160), nullable=True),
        sa.Column("actual_product_instance_id", sa.String(120), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("nutrition_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("nutrition_provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["consumption_event_id"], ["consumption_events_v2.consumption_event_id"], ondelete="CASCADE"),
        sa.CheckConstraint("quantity IS NULL OR quantity > 0", name="ck_consumption_item_quantity_positive"),
    )
    op.create_table(
        "cooking_pantry_deductions_v2",
        sa.Column("deduction_id", UUID(), primary_key=True),
        sa.Column("cooking_batch_id", UUID(), nullable=False),
        sa.Column("pantry_movement_id", UUID(), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["cooking_batch_id"], ["cooking_batches_v2.cooking_batch_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pantry_movement_id"], ["pantry_movements_v2.movement_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("idempotency_key", name="uq_cooking_deduction_idempotency"),
    )

def downgrade() -> None:
    for table in ("cooking_pantry_deductions_v2", "consumption_items_v2", "consumption_events_v2", "cooking_substitutions_v2", "cooking_events_v2", "cooking_batches_v2"):
        op.drop_table(table)
