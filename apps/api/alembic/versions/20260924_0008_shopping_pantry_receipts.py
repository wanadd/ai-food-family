"""Shopping, pantry, acquisition and receipt proposal V2."""
from __future__ import annotations
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260924_0008"
down_revision: str | None = "20260924_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = lambda: postgresql.UUID(as_uuid=False)
JSON = lambda: postgresql.JSONB()

def upgrade() -> None:
    op.create_table(
        "shopping_lists_v2",
        sa.Column("shopping_list_id", UUID(), primary_key=True),
        sa.Column("household_id", UUID(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="OPEN"),
        sa.Column("context_key", sa.String(128), nullable=False, server_default="default"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.CheckConstraint("status IN ('OPEN', 'CLOSED', 'ARCHIVED')", name="ck_shopping_lists_v2_status"),
    )
    op.create_table(
        "shopping_demands",
        sa.Column("demand_id", UUID(), primary_key=True),
        sa.Column("shopping_list_id", UUID(), nullable=False),
        sa.Column("food_identity_key", sa.String(160), nullable=True),
        sa.Column("display_text", sa.String(300), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("quantity_state", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("source_kind", sa.String(32), nullable=False),
        sa.Column("plan_id", UUID(), nullable=True),
        sa.Column("plan_revision_id", UUID(), nullable=True),
        sa.Column("plan_slot_id", UUID(), nullable=True),
        sa.Column("recipe_version_id", UUID(), nullable=True),
        sa.Column("participant_person_id", UUID(), nullable=True),
        sa.Column("product_requirement_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["shopping_list_id"], ["shopping_lists_v2.shopping_list_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans_v2.plan_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["plan_revision_id"], ["plan_revisions.revision_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["plan_slot_id"], ["plan_slots.slot_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["recipe_versions.recipe_version_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["participant_person_id"], ["core_persons.person_id"], ondelete="SET NULL"),
        sa.CheckConstraint("quantity IS NULL OR quantity > 0", name="ck_shopping_demands_quantity_positive"),
        sa.CheckConstraint("quantity IS NULL OR unit IS NOT NULL", name="ck_shopping_demands_quantity_unit"),
        sa.CheckConstraint("quantity_state IN ('KNOWN', 'UNKNOWN', 'REVIEW_REQUIRED')", name="ck_shopping_demands_quantity_state"),
        sa.CheckConstraint("source_kind IN ('PLAN', 'MANUAL', 'PANTRY_REPLENISHMENT', 'OTHER')", name="ck_shopping_demands_source"),
        sa.UniqueConstraint("idempotency_key", name="uq_shopping_demands_idempotency"),
    )
    op.create_table(
        "shopping_list_items_v2",
        sa.Column("item_id", UUID(), primary_key=True),
        sa.Column("shopping_list_id", UUID(), nullable=False),
        sa.Column("food_identity_key", sa.String(160), nullable=True),
        sa.Column("display_text", sa.String(300), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("item_kind", sa.String(24), nullable=False),
        sa.Column("item_state", sa.String(24), nullable=False, server_default="OPEN"),
        sa.Column("product_requirement_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["shopping_list_id"], ["shopping_lists_v2.shopping_list_id"], ondelete="CASCADE"),
        sa.CheckConstraint("item_kind IN ('MANUAL', 'DERIVED', 'MIXED')", name="ck_shopping_items_v2_kind"),
        sa.CheckConstraint("item_state IN ('OPEN', 'CHECKED', 'ACQUIRED', 'NOT_NEEDED')", name="ck_shopping_items_v2_state"),
    )
    op.create_table(
        "purchase_events_v2",
        sa.Column("purchase_id", UUID(), primary_key=True),
        sa.Column("household_id", UUID(), nullable=False),
        sa.Column("shopping_item_id", UUID(), nullable=True),
        sa.Column("receipt_proposal_id", UUID(), nullable=True),
        sa.Column("verified_status", sa.String(24), nullable=False),
        sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_reference", sa.String(200), nullable=True),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shopping_item_id"], ["shopping_list_items_v2.item_id"], ondelete="SET NULL"),
        sa.CheckConstraint("verified_status IN ('PROPOSED', 'VERIFIED', 'REJECTED')", name="ck_purchase_verified_status"),
        sa.UniqueConstraint("external_reference", name="uq_purchase_external_reference"),
    )
    op.create_table(
        "pantry_inventory_v2",
        sa.Column("inventory_id", UUID(), primary_key=True),
        sa.Column("household_id", UUID(), nullable=False),
        sa.Column("food_identity_key", sa.String(160), nullable=True),
        sa.Column("product_instance_id", sa.String(120), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("quantity_state", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("expiration_state", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.CheckConstraint("quantity IS NULL OR quantity >= 0", name="ck_pantry_inventory_quantity_nonnegative"),
        sa.CheckConstraint("quantity_state IN ('KNOWN', 'UNKNOWN', 'REVIEW_REQUIRED')", name="ck_pantry_inventory_quantity_state"),
        sa.CheckConstraint("expiration_state IN ('KNOWN', 'UNKNOWN', 'ESTIMATED')", name="ck_pantry_inventory_expiration_state"),
    )
    op.create_table(
        "pantry_movements_v2",
        sa.Column("movement_id", UUID(), primary_key=True),
        sa.Column("inventory_id", UUID(), nullable=False),
        sa.Column("movement_type", sa.String(32), nullable=False),
        sa.Column("quantity_delta", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("purchase_id", UUID(), nullable=True),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["inventory_id"], ["pantry_inventory_v2.inventory_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchase_events_v2.purchase_id"], ondelete="SET NULL"),
        sa.CheckConstraint("movement_type IN ('ACQUIRED', 'MANUAL_ADD', 'ADJUSTMENT', 'CONSUMED', 'USED_FOR_COOKING', 'DISCARDED', 'EXPIRED', 'CORRECTION')", name="ck_pantry_movement_type"),
        sa.CheckConstraint("quantity_delta IS NULL OR quantity_delta <> 0", name="ck_pantry_movement_nonzero"),
        sa.UniqueConstraint("idempotency_key", name="uq_pantry_movement_idempotency"),
    )
    op.create_table(
        "receipt_documents_v2",
        sa.Column("receipt_id", UUID(), primary_key=True),
        sa.Column("household_id", UUID(), nullable=False),
        sa.Column("raw_storage_ref", sa.String(512), nullable=True),
        sa.Column("raw_content_hash", sa.String(128), nullable=True),
        sa.Column("retention_policy", sa.String(64), nullable=False, server_default="REVIEW_WINDOW"),
        sa.Column("retain_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("raw_content_hash", name="uq_receipt_raw_hash"),
    )
    op.create_table(
        "receipt_proposals_v2",
        sa.Column("proposal_id", UUID(), primary_key=True),
        sa.Column("receipt_id", UUID(), nullable=False),
        sa.Column("extraction_kind", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="REVIEW_REQUIRED"),
        sa.Column("confidence", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("payload_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipt_documents_v2.receipt_id"], ondelete="CASCADE"),
        sa.CheckConstraint("extraction_kind IN ('OCR', 'AI', 'MANUAL')", name="ck_receipt_proposal_extraction"),
        sa.CheckConstraint("status IN ('REVIEW_REQUIRED', 'VERIFIED', 'REJECTED')", name="ck_receipt_proposal_status"),
        sa.CheckConstraint("confidence IN ('UNKNOWN', 'LOW', 'MEDIUM', 'HIGH')", name="ck_receipt_proposal_confidence"),
    )
    op.create_table(
        "receipt_lines_v2",
        sa.Column("line_id", UUID(), primary_key=True),
        sa.Column("proposal_id", UUID(), nullable=False),
        sa.Column("raw_text", sa.String(300), nullable=False),
        sa.Column("matched_kind", sa.String(24), nullable=False, server_default="UNRESOLVED"),
        sa.Column("matched_key", sa.String(160), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("match_status", sa.String(24), nullable=False, server_default="REVIEW_REQUIRED"),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["proposal_id"], ["receipt_proposals_v2.proposal_id"], ondelete="CASCADE"),
        sa.CheckConstraint("matched_kind IN ('PACKAGED_PRODUCT', 'FOOD_IDENTITY', 'UNRESOLVED')", name="ck_receipt_line_match_kind"),
        sa.CheckConstraint("match_status IN ('REVIEW_REQUIRED', 'VERIFIED', 'REJECTED')", name="ck_receipt_line_match_status"),
        sa.CheckConstraint("quantity IS NULL OR quantity > 0", name="ck_receipt_line_quantity_positive"),
    )
    op.create_index("ix_shopping_demands_plan_trace", "shopping_demands", ["plan_revision_id", "plan_slot_id", "recipe_version_id"])
    op.create_index("ix_pantry_movements_inventory_time", "pantry_movements_v2", ["inventory_id", "created_at"])

def downgrade() -> None:
    op.drop_index("ix_pantry_movements_inventory_time", table_name="pantry_movements_v2")
    op.drop_index("ix_shopping_demands_plan_trace", table_name="shopping_demands")
    for table in ("receipt_lines_v2", "receipt_proposals_v2", "receipt_documents_v2", "pantry_movements_v2", "pantry_inventory_v2", "purchase_events_v2", "shopping_list_items_v2", "shopping_demands", "shopping_lists_v2"):
        op.drop_table(table)
