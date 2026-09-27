from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import CoreJSON, CoreUUID
from app.database import Base


class CookingSession(Base):
    __tablename__ = "cooking_sessions"
    __table_args__ = (
        CheckConstraint("state IN ('STARTED', 'COMPLETED', 'CANCELLED')", name="ck_cooking_sessions_state"),
        UniqueConstraint("household_id", "idempotency_key", name="uq_cooking_sessions_idempotency"),
        Index("ix_cooking_sessions_household", "household_id", "started_at"),
    )
    cooking_session_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    household_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_households.household_id", ondelete="CASCADE"))
    recipe_version_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("recipe_versions.recipe_version_id", ondelete="RESTRICT"))
    plan_slot_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("plan_slots.slot_id", ondelete="SET NULL"))
    state: Mapped[str] = mapped_column(String(24), default="STARTED")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PreparedFood(Base):
    __tablename__ = "prepared_foods"
    __table_args__ = (
        CheckConstraint("yield_quantity IS NULL OR yield_quantity > 0", name="ck_prepared_foods_yield_positive"),
        CheckConstraint("yield_servings IS NULL OR yield_servings > 0", name="ck_prepared_foods_servings_positive"),
        CheckConstraint("yield_quantity IS NULL OR yield_unit IS NOT NULL", name="ck_prepared_foods_yield_unit"),
        CheckConstraint("state IN ('PREPARED', 'DEPLETED', 'ARCHIVED')", name="ck_prepared_foods_state"),
        UniqueConstraint("session_id", name="uq_prepared_foods_session"),
    )
    prepared_food_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    session_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("cooking_sessions.cooking_session_id", ondelete="CASCADE"))
    household_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_households.household_id", ondelete="CASCADE"))
    recipe_version_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("recipe_versions.recipe_version_id", ondelete="SET NULL"))
    display_name: Mapped[str | None] = mapped_column(String(240))
    yield_quantity: Mapped[float | None] = mapped_column(Float)
    yield_unit: Mapped[str | None] = mapped_column(String(32))
    yield_servings: Mapped[float | None] = mapped_column(Float)
    state: Mapped[str] = mapped_column(String(24), default="PREPARED")
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CookingEvent(Base):
    __tablename__ = "cooking_events"
    __table_args__ = (
        CheckConstraint("event_kind IN ('STARTED', 'COMPLETED', 'CORRECTION')", name="ck_cooking_events_kind"),
        UniqueConstraint("household_id", "idempotency_key", name="uq_cooking_events_idempotency"),
    )
    cooking_event_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    session_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("cooking_sessions.cooking_session_id", ondelete="CASCADE"))
    household_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_households.household_id", ondelete="CASCADE"))
    event_kind: Mapped[str] = mapped_column(String(32))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    payload_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(200))


class ConsumptionEvent(Base):
    __tablename__ = "consumption_events"
    __table_args__ = (
        CheckConstraint("source_kind IN ('PLANNED_RECIPE', 'COOKED_FOOD', 'EXTERNAL_MEAL', 'MANUAL', 'AI_PROPOSAL')", name="ck_consumption_events_source"),
        CheckConstraint("state IN ('CONFIRMED', 'CORRECTED', 'RETRACTED')", name="ck_consumption_events_state"),
        CheckConstraint("portion_state IN ('KNOWN', 'UNKNOWN', 'ESTIMATED')", name="ck_consumption_events_portion"),
        CheckConstraint("confidence IN ('UNKNOWN', 'ESTIMATED', 'CONFIRMED')", name="ck_consumption_events_confidence"),
        UniqueConstraint("household_id", "idempotency_key", name="uq_consumption_events_idempotency"),
        Index("ix_consumption_events_person_time", "person_id", "occurred_at"),
    )
    consumption_event_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="CASCADE"))
    household_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_households.household_id", ondelete="CASCADE"))
    plan_slot_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("plan_slots.slot_id", ondelete="SET NULL"))
    recipe_version_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("recipe_versions.recipe_version_id", ondelete="SET NULL"))
    cooking_session_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("cooking_sessions.cooking_session_id", ondelete="SET NULL"))
    source_kind: Mapped[str] = mapped_column(String(32))
    state: Mapped[str] = mapped_column(String(24), default="CONFIRMED")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    portion_state: Mapped[str] = mapped_column(String(24), default="UNKNOWN")
    confidence: Mapped[str] = mapped_column(String(24), default="CONFIRMED")
    external_description: Mapped[str | None] = mapped_column(String(500))
    correction_of_event_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("consumption_events.consumption_event_id", ondelete="SET NULL"))
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConsumptionItem(Base):
    __tablename__ = "consumption_items"
    __table_args__ = (
        CheckConstraint("quantity IS NULL OR quantity > 0", name="ck_consumption_items_quantity_positive"),
        CheckConstraint("quantity IS NULL OR unit IS NOT NULL", name="ck_consumption_items_quantity_unit"),
        CheckConstraint("food_identity_key IS NOT NULL OR product_instance_key IS NOT NULL OR display_text IS NOT NULL", name="ck_consumption_items_identity"),
    )
    consumption_item_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    consumption_event_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("consumption_events.consumption_event_id", ondelete="CASCADE"))
    person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="CASCADE"))
    food_identity_key: Mapped[str | None] = mapped_column(String(160))
    product_instance_key: Mapped[str | None] = mapped_column(String(160))
    display_text: Mapped[str | None] = mapped_column(String(240))
    quantity: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(32))
    nutrition_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    nutrition_provenance_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)


class HealthProjection(Base):
    __tablename__ = "health_projections"
    __table_args__ = (
        CheckConstraint("completeness IN ('COMPLETE', 'PARTIAL', 'UNKNOWN')", name="ck_health_projections_completeness"),
        CheckConstraint("safety_status IN ('BLOCK', 'ESCALATE', 'UNKNOWN', 'WARN', 'SAFE')", name="ck_health_projections_safety"),
        UniqueConstraint("person_id", "projection_date", "calculation_version", name="uq_health_projections_version"),
    )
    projection_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="CASCADE"))
    projection_date: Mapped[date] = mapped_column(Date)
    completeness: Mapped[str] = mapped_column(String(24))
    planned_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    actual_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    deviation_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    safety_status: Mapped[str] = mapped_column(String(24), default="UNKNOWN")
    source_refs_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    calculation_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HealthDeviation(Base):
    __tablename__ = "health_deviations"
    __table_args__ = (CheckConstraint("severity IN ('INFO', 'WARN', 'ESCALATE', 'BLOCK', 'UNKNOWN')", name="ck_health_deviations_severity"), Index("ix_health_deviations_person", "person_id", "deviation_id"))
    deviation_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    projection_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("health_projections.projection_id", ondelete="CASCADE"))
    person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="CASCADE"))
    deviation_kind: Mapped[str] = mapped_column(String(48))
    severity: Mapped[str] = mapped_column(String(24))
    known_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    unknown_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
