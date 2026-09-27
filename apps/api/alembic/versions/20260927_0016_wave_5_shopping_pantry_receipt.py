"""Canonical Wave 5 shopping, pantry and receipt foundations."""
from __future__ import annotations
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260927_0016"
down_revision: str | None = "20260927_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    uid = postgresql.UUID(as_uuid=False)
    js = postgresql.JSONB()
    op.create_table(
        "shopping_lists",
        sa.Column("shopping_list_id", uid, primary_key=True),
        sa.Column("household_id", uid, nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="ACTIVE"),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="ck_shopping_lists_status"),
        sa.UniqueConstraint("household_id", "status", name="uq_shopping_lists_household_status"),
        sa.UniqueConstraint("household_id", "idempotency_key", name="uq_shopping_lists_idempotency"),
    )
    # 0008 created the precursor shopping_demands table. Reuse it and move
    # its list FK to the canonical household list instead of duplicating it.
    op.drop_constraint("shopping_demands_shopping_list_id_fkey", "shopping_demands", type_="foreignkey")
    op.create_foreign_key("fk_shopping_demands_list", "shopping_demands", "shopping_lists", ["shopping_list_id"], ["shopping_list_id"], ondelete="CASCADE")
    for column in (
        sa.Column("food_identity_id", sa.Integer(), nullable=True),
        sa.Column("conversion_basis", sa.String(64), nullable=True),
        sa.Column("uncertainty", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("source_key", sa.String(160), nullable=True),
    ):
        op.add_column("shopping_demands", column)
    for constraint in ("ck_shopping_demands_quantity_positive", "ck_shopping_demands_quantity_unit", "ck_shopping_demands_quantity_state", "ck_shopping_demands_source"):
        op.drop_constraint(constraint, "shopping_demands", type_="check")
    op.create_check_constraint("ck_shopping_demands_positive", "shopping_demands", "quantity IS NULL OR quantity > 0")
    op.create_check_constraint("ck_shopping_demands_uncertainty", "shopping_demands", "uncertainty IN ('KNOWN', 'UNKNOWN', 'OPTIONAL', 'TO_TASTE')")
    op.create_check_constraint("ck_shopping_demands_source", "shopping_demands", "source_kind IN ('PLAN', 'MANUAL', 'PANTRY', 'RECEIPT', 'OTHER', 'PANTRY_REPLENISHMENT')")
    op.create_unique_constraint("uq_shopping_demands_source", "shopping_demands", ["shopping_list_id", "source_key"])
    op.create_table(
        "shopping_items",
        sa.Column("shopping_item_id", uid, primary_key=True),
        sa.Column("shopping_list_id", uid, nullable=False),
        sa.Column("food_identity_id", sa.Integer(), nullable=True),
        sa.Column("display_text", sa.String(240), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("uncertainty", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("state", sa.String(24), nullable=False, server_default="NEEDED"),
        sa.Column("source_kind", sa.String(24), nullable=False),
        sa.Column("provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["shopping_list_id"], ["shopping_lists.shopping_list_id"], ondelete="CASCADE"),
        sa.CheckConstraint("quantity IS NULL OR quantity > 0", name="ck_shopping_items_positive"),
        sa.CheckConstraint("state IN ('NEEDED', 'CHECKED', 'PURCHASED', 'REMOVED', 'DEFERRED')", name="ck_shopping_items_state"),
        sa.UniqueConstraint("shopping_list_id", "idempotency_key", name="uq_shopping_items_idempotency"),
    )
    op.create_table(
        "purchase_events",
        sa.Column("purchase_event_id", uid, primary_key=True),
        sa.Column("shopping_item_id", uid, nullable=False),
        sa.Column("household_id", uid, nullable=False),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["shopping_item_id"], ["shopping_items.shopping_item_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("household_id", "idempotency_key", name="uq_purchase_events_idempotency"),
    )
    op.create_table(
        "pantry_inventory",
        sa.Column("pantry_inventory_id", uid, primary_key=True),
        sa.Column("household_id", uid, nullable=False),
        sa.Column("food_identity_id", sa.Integer(), nullable=True),
        sa.Column("packaged_product_id", sa.Integer(), nullable=True),
        sa.Column("display_text", sa.String(240), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("uncertainty", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("lot_code", sa.String(160), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.CheckConstraint("quantity IS NULL OR quantity >= 0", name="ck_pantry_inventory_nonnegative"),
        sa.CheckConstraint("uncertainty IN ('KNOWN', 'UNKNOWN')", name="ck_pantry_inventory_uncertainty"),
    )
    op.create_table(
        "pantry_movements",
        sa.Column("pantry_movement_id", uid, primary_key=True),
        sa.Column("pantry_inventory_id", uid, nullable=False),
        sa.Column("household_id", uid, nullable=False),
        sa.Column("movement_kind", sa.String(32), nullable=False),
        sa.Column("quantity_delta", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["pantry_inventory_id"], ["pantry_inventory.pantry_inventory_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.CheckConstraint("movement_kind IN ('MANUAL', 'SHOPPING_PURCHASE', 'RECEIPT_CONFIRMATION', 'IMPORT', 'OTHER')", name="ck_pantry_movements_kind"),
        sa.CheckConstraint("quantity_delta IS NULL OR quantity_delta <> 0", name="ck_pantry_movements_delta"),
        sa.UniqueConstraint("household_id", "idempotency_key", name="uq_pantry_movements_idempotency"),
    )
    op.create_table(
        "receipt_documents",
        sa.Column("receipt_document_id", uid, primary_key=True),
        sa.Column("household_id", uid, nullable=False),
        sa.Column("media_asset_id", uid, nullable=True),
        sa.Column("provider_metadata_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("state", sa.String(24), nullable=False, server_default="UPLOADING"),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("household_id", "idempotency_key", name="uq_receipt_documents_idempotency"),
        sa.CheckConstraint("state IN ('UPLOADING', 'PROCESSING', 'REVIEW', 'CONFIRMED', 'PARTIAL', 'FAILED')", name="ck_receipt_documents_state"),
    )
    op.create_table(
        "receipt_proposals",
        sa.Column("receipt_proposal_id", uid, primary_key=True),
        sa.Column("receipt_document_id", uid, nullable=False),
        sa.Column("household_id", uid, nullable=False),
        sa.Column("state", sa.String(24), nullable=False, server_default="REVIEW_REQUIRED"),
        sa.Column("confidence", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("provider_metadata_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["receipt_document_id"], ["receipt_documents.receipt_document_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.CheckConstraint("state IN ('REVIEW_REQUIRED', 'VERIFIED', 'FAILED', 'PARTIAL')", name="ck_receipt_proposals_state"),
        sa.CheckConstraint("confidence IN ('HIGH', 'MEDIUM', 'LOW', 'UNKNOWN')", name="ck_receipt_proposals_confidence"),
        sa.UniqueConstraint("household_id", "idempotency_key", name="uq_receipt_proposals_idempotency"),
    )
    op.create_table(
        "receipt_lines",
        sa.Column("receipt_line_id", uid, primary_key=True),
        sa.Column("receipt_proposal_id", uid, nullable=False),
        sa.Column("household_id", uid, nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("raw_text", sa.String(500), nullable=False),
        sa.Column("candidate_food_identity_id", sa.Integer(), nullable=True),
        sa.Column("candidate_product_id", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("state", sa.String(24), nullable=False, server_default="UNRESOLVED"),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["receipt_proposal_id"], ["receipt_proposals.receipt_proposal_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.CheckConstraint("state IN ('UNRESOLVED', 'REVIEW_REQUIRED', 'CONFIRMED', 'REJECTED')", name="ck_receipt_lines_state"),
        sa.CheckConstraint("quantity IS NULL OR quantity > 0", name="ck_receipt_lines_positive"),
        sa.UniqueConstraint("receipt_proposal_id", "position", name="uq_receipt_lines_position"),
    )
    for table, cols in {
        "shopping_demands": ["shopping_list_id", "plan_revision_id"],
        "shopping_items": ["shopping_list_id", "state"],
        "pantry_inventory": ["household_id", "display_text"],
        "pantry_movements": ["pantry_inventory_id", "created_at"],
        "receipt_documents": ["household_id", "state"],
        "receipt_proposals": ["receipt_document_id", "state"],
        "receipt_lines": ["receipt_proposal_id", "state"],
    }.items():
        op.create_index(f"ix_{table}_{'_'.join(cols)}", table, cols)


def downgrade() -> None:
    for table in ("receipt_lines", "receipt_proposals", "receipt_documents", "pantry_movements", "pantry_inventory", "purchase_events", "shopping_items", "shopping_demands", "shopping_lists"):
        op.drop_table(table)
