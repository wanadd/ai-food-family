from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import CoreJSON, CoreUUID
from app.database import Base


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (
        CheckConstraint(
            "(person_id IS NOT NULL AND household_id IS NULL) OR (person_id IS NULL AND household_id IS NOT NULL)",
            name="ck_plans_owner_xor",
        ),
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="ck_plans_status"),
        UniqueConstraint("idempotency_key", name="uq_plans_idempotency"),
        Index("ix_plans_person", "person_id"),
        Index("ix_plans_household", "household_id"),
    )

    plan_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    person_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="CASCADE"), nullable=True)
    household_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_households.household_id", ondelete="CASCADE"), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)


class PlanRevision(Base):
    __tablename__ = "plan_revisions"
    __table_args__ = (
        CheckConstraint("revision_number > 0", name="ck_plan_revisions_number_positive"),
        CheckConstraint("lifecycle_status IN ('DRAFT', 'ACTIVE', 'SUPERSEDED')", name="ck_plan_revisions_lifecycle"),
        UniqueConstraint("plan_id", "revision_number", name="uq_plan_revisions_number"),
        UniqueConstraint("idempotency_key", name="uq_plan_revisions_idempotency"),
    )

    revision_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    plan_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("plans.plan_id", ondelete="CASCADE"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT")
    actor_person_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="SET NULL"), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    input_snapshot_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    safety_snapshot_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PlanSlot(Base):
    __tablename__ = "plan_slots"
    __table_args__ = (
        CheckConstraint("slot_state IN ('ASSIGNED', 'EMPTY', 'FREE', 'CANCELLED')", name="ck_plan_slots_state_w4"),
        UniqueConstraint("revision_id", "slot_key", name="uq_plan_slots_revision_key"),
        Index("ix_plan_slots_revision_date", "revision_id", "planned_date"),
    )

    slot_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    revision_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("plan_revisions.revision_id", ondelete="CASCADE"), nullable=False)
    slot_key: Mapped[str] = mapped_column(String(96), nullable=False)
    planned_date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(32), nullable=False)
    slot_state: Mapped[str] = mapped_column(String(24), nullable=False, default="FREE")
    recipe_version_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("recipe_versions.recipe_version_id", ondelete="RESTRICT"), nullable=True)
    manual_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PlanAssignment(Base):
    __tablename__ = "plan_assignments"
    __table_args__ = (
        CheckConstraint("source_kind IN ('GENERATED', 'MANUAL', 'REPLACEMENT')", name="ck_plan_assignments_source"),
        CheckConstraint("safety_state IN ('SAFE', 'WARN', 'UNKNOWN', 'ESCALATE')", name="ck_plan_assignments_safety"),
        UniqueConstraint("slot_id", name="uq_plan_assignments_slot"),
        UniqueConstraint("idempotency_key", name="uq_plan_assignments_idempotency"),
    )

    assignment_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    slot_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("plan_slots.slot_id", ondelete="CASCADE"), nullable=False)
    recipe_version_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("recipe_versions.recipe_version_id", ondelete="RESTRICT"), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(24), nullable=False, default="MANUAL")
    safety_state: Mapped[str] = mapped_column(String(16), nullable=False, default="UNKNOWN")
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PlanParticipant(Base):
    __tablename__ = "plan_participants"
    __table_args__ = (CheckConstraint("participation_state IN ('PARTICIPATING', 'ABSENT', 'UNKNOWN')", name="ck_plan_participants_state"),)

    slot_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("plan_slots.slot_id", ondelete="CASCADE"), primary_key=True)
    person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="CASCADE"), primary_key=True)
    participation_state: Mapped[str] = mapped_column(String(24), nullable=False, default="PARTICIPATING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PlanPortion(Base):
    __tablename__ = "plan_portions"
    __table_args__ = (
        CheckConstraint("portion_value IS NULL OR portion_value > 0", name="ck_plan_portions_positive"),
        CheckConstraint("portion_value IS NULL OR portion_unit IS NOT NULL", name="ck_plan_portions_unit"),
        CheckConstraint("source_kind IN ('EXPLICIT', 'ADULT_FALLBACK', 'CHILD_FALLBACK', 'UNKNOWN')", name="ck_plan_portions_source"),
    )

    slot_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("plan_slots.slot_id", ondelete="CASCADE"), primary_key=True)
    person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="CASCADE"), primary_key=True)
    portion_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    portion_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_kind: Mapped[str] = mapped_column(String(24), nullable=False, default="UNKNOWN")
