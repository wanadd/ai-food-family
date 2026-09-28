"""Allow person or household ownership for Shopping, Pantry, and Receipt roots."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260928_0020"
down_revision = "20260927_0019"
branch_labels = None
depends_on = None


ROOTS = ("shopping_lists", "pantry_inventory", "receipt_documents")
CHILDREN = ("purchase_events", "pantry_movements", "receipt_proposals", "receipt_lines")


def upgrade() -> None:
    uid = postgresql.UUID(as_uuid=False)
    op.add_column("notification_preferences", sa.Column("shopping_enabled", sa.Boolean(), nullable=True))
    op.add_column("notification_preferences", sa.Column("cooking_enabled", sa.Boolean(), nullable=True))
    for table in ROOTS:
        op.add_column(table, sa.Column("person_id", uid, nullable=True))
        op.create_foreign_key(f"fk_{table}_person", table, "core_persons", ["person_id"], ["person_id"], ondelete="CASCADE")
        op.alter_column(table, "household_id", existing_type=uid, nullable=True)
        op.create_check_constraint(
            f"ck_{table}_owner_xor", table,
            "(person_id IS NOT NULL AND household_id IS NULL) OR (person_id IS NULL AND household_id IS NOT NULL)",
        )
        op.create_index(f"ix_{table}_person", table, ["person_id"])
    for table in CHILDREN:
        op.alter_column(table, "household_id", existing_type=uid, nullable=True)

    op.create_unique_constraint("uq_shopping_lists_person_status", "shopping_lists", ["person_id", "status"])
    op.create_unique_constraint("uq_shopping_lists_person_idempotency", "shopping_lists", ["person_id", "idempotency_key"])
    op.create_unique_constraint("uq_purchase_events_item_idempotency", "purchase_events", ["shopping_item_id", "idempotency_key"])
    op.create_unique_constraint("uq_pantry_movements_inventory_idempotency", "pantry_movements", ["pantry_inventory_id", "idempotency_key"])
    op.create_unique_constraint("uq_receipt_documents_person_idempotency", "receipt_documents", ["person_id", "idempotency_key"])
    op.create_unique_constraint("uq_receipt_proposals_document_idempotency", "receipt_proposals", ["receipt_document_id", "idempotency_key"])


def downgrade() -> None:
    connection = op.get_bind()
    op.drop_column("notification_preferences", "cooking_enabled")
    op.drop_column("notification_preferences", "shopping_enabled")
    for table in ROOTS:
        if connection.execute(sa.text(f"SELECT EXISTS (SELECT 1 FROM {table} WHERE person_id IS NOT NULL)")).scalar_one():
            raise RuntimeError("Cannot downgrade OD-17 while person-owned records exist")
    op.drop_constraint("uq_receipt_proposals_document_idempotency", "receipt_proposals", type_="unique")
    op.drop_constraint("uq_receipt_documents_person_idempotency", "receipt_documents", type_="unique")
    op.drop_constraint("uq_pantry_movements_inventory_idempotency", "pantry_movements", type_="unique")
    op.drop_constraint("uq_purchase_events_item_idempotency", "purchase_events", type_="unique")
    op.drop_constraint("uq_shopping_lists_person_idempotency", "shopping_lists", type_="unique")
    op.drop_constraint("uq_shopping_lists_person_status", "shopping_lists", type_="unique")
    uid = postgresql.UUID(as_uuid=False)
    for table in CHILDREN:
        op.alter_column(table, "household_id", existing_type=uid, nullable=False)
    for table in ROOTS:
        op.drop_index(f"ix_{table}_person", table_name=table)
        op.drop_constraint(f"ck_{table}_owner_xor", table, type_="check")
        op.alter_column(table, "household_id", existing_type=uid, nullable=False)
        op.drop_constraint(f"fk_{table}_person", table, type_="foreignkey")
        op.drop_column(table, "person_id")
