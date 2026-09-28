from __future__ import annotations
from datetime import date, datetime
from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models import CoreJSON, CoreUUID
from app.database import Base


class ShoppingList(Base):
    __tablename__ = "shopping_lists"
    __table_args__ = (CheckConstraint("(person_id IS NOT NULL AND household_id IS NULL) OR (person_id IS NULL AND household_id IS NOT NULL)", name="ck_shopping_lists_owner_xor"),)
    shopping_list_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    person_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id"), nullable=True)
    household_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_households.household_id"), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="ACTIVE")
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ShoppingDemand(Base):
    __tablename__ = "shopping_demands"
    demand_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    shopping_list_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("shopping_lists.shopping_list_id"), nullable=False)
    plan_revision_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("plan_revisions.revision_id"))
    plan_slot_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("plan_slots.slot_id"))
    recipe_version_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("recipe_versions.recipe_version_id"))
    food_identity_id: Mapped[int | None] = mapped_column(Integer)
    display_text: Mapped[str] = mapped_column(String(240))
    quantity: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(32))
    conversion_basis: Mapped[str | None] = mapped_column(String(64))
    uncertainty: Mapped[str] = mapped_column(String(24), default="UNKNOWN")
    source_kind: Mapped[str] = mapped_column(String(24))
    source_key: Mapped[str | None] = mapped_column(String(160), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(200), default="w5")
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)


class ShoppingItem(Base):
    __tablename__ = "shopping_items"
    shopping_item_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    shopping_list_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("shopping_lists.shopping_list_id"), nullable=False)
    food_identity_id: Mapped[int | None] = mapped_column(Integer)
    display_text: Mapped[str] = mapped_column(String(240))
    quantity: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(32))
    uncertainty: Mapped[str] = mapped_column(String(24), default="UNKNOWN")
    category: Mapped[str | None] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(24), default="NEEDED")
    source_kind: Mapped[str] = mapped_column(String(24))
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PurchaseEvent(Base):
    __tablename__ = "purchase_events"
    purchase_event_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    shopping_item_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("shopping_items.shopping_item_id"))
    household_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_households.household_id"), nullable=True)
    quantity: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(32))
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PantryInventory(Base):
    __tablename__ = "pantry_inventory"
    __table_args__ = (CheckConstraint("(person_id IS NOT NULL AND household_id IS NULL) OR (person_id IS NULL AND household_id IS NOT NULL)", name="ck_pantry_inventory_owner_xor"),)
    pantry_inventory_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    person_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id"), nullable=True)
    household_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_households.household_id"), nullable=True)
    food_identity_id: Mapped[int | None] = mapped_column(Integer)
    packaged_product_id: Mapped[int | None] = mapped_column(Integer)
    display_text: Mapped[str] = mapped_column(String(240))
    quantity: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(32))
    uncertainty: Mapped[str] = mapped_column(String(24), default="UNKNOWN")
    lot_code: Mapped[str | None] = mapped_column(String(160))
    expiry_date: Mapped[date | None] = mapped_column(Date)
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PantryMovement(Base):
    __tablename__ = "pantry_movements"
    pantry_movement_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    pantry_inventory_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("pantry_inventory.pantry_inventory_id"))
    household_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_households.household_id"), nullable=True)
    movement_kind: Mapped[str] = mapped_column(String(32))
    quantity_delta: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(32))
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReceiptDocument(Base):
    __tablename__ = "receipt_documents"
    __table_args__ = (CheckConstraint("(person_id IS NOT NULL AND household_id IS NULL) OR (person_id IS NULL AND household_id IS NOT NULL)", name="ck_receipt_documents_owner_xor"),)
    receipt_document_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    person_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id"), nullable=True)
    household_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_households.household_id"), nullable=True)
    media_asset_id: Mapped[str | None] = mapped_column(CoreUUID)
    provider_metadata_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    state: Mapped[str] = mapped_column(String(24), default="UPLOADING")
    idempotency_key: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReceiptProposal(Base):
    __tablename__ = "receipt_proposals"
    receipt_proposal_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    receipt_document_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("receipt_documents.receipt_document_id"))
    household_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_households.household_id"), nullable=True)
    state: Mapped[str] = mapped_column(String(24), default="REVIEW_REQUIRED")
    confidence: Mapped[str] = mapped_column(String(24), default="UNKNOWN")
    provider_metadata_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReceiptLine(Base):
    __tablename__ = "receipt_lines"
    receipt_line_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    receipt_proposal_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("receipt_proposals.receipt_proposal_id"))
    household_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_households.household_id"), nullable=True)
    position: Mapped[int] = mapped_column(Integer)
    raw_text: Mapped[str] = mapped_column(String(500))
    candidate_food_identity_id: Mapped[int | None] = mapped_column(Integer)
    candidate_product_id: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[str] = mapped_column(String(24), default="UNKNOWN")
    state: Mapped[str] = mapped_column(String(24), default="UNRESOLVED")
    quantity: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(32))
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
