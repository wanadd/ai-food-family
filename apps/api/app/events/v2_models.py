from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.core.models import CoreJSON, CoreUUID


class Event(Base):
    __tablename__ = "events_v2"
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','OPEN','PLANNING','READY','ACTIVE','COMPLETED','CANCELLED')", name="ck_events_v2_status"),
        CheckConstraint("collaboration_mode IN ('ORGANIZER_ONLY','RESTRICTIONS_COLLECTION','COLLABORATIVE_PLANNING')", name="ck_events_v2_collaboration"),
        CheckConstraint("version >= 1", name="ck_events_v2_version"),
        Index("ix_events_v2_organizer", "organizer_person_id"),
        Index("ix_events_v2_household", "household_id"),
    )

    event_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    organizer_person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="RESTRICT"), nullable=False)
    household_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_households.household_id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, default="other")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collaboration_mode: Mapped[str] = mapped_column(String(40), nullable=False, default="ORGANIZER_ONLY")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    creation_idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    metadata_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EventInvitation(Base):
    __tablename__ = "event_invitations_v2"
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','RESPONDED','REVOKED','EXPIRED')", name="ck_event_invitations_v2_status"),
        Index("ix_event_invitations_v2_event", "event_id"),
    )

    invitation_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    event_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("events_v2.event_id", ondelete="CASCADE"), nullable=False)
    created_by_person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="RESTRICT"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    token_hint: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    creation_idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    response_idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EventParticipant(Base):
    __tablename__ = "event_participants_v2"
    __table_args__ = (
        CheckConstraint("participant_kind IN ('ORGANIZER','PERSON','GUEST','DEPENDENT')", name="ck_event_participants_v2_kind"),
        CheckConstraint("age_group IN ('ADULT','CHILD','UNKNOWN')", name="ck_event_participants_v2_age"),
        CheckConstraint("attendance_status IN ('PENDING','ACCEPTED','DECLINED')", name="ck_event_participants_v2_attendance"),
        CheckConstraint("person_id IS NOT NULL OR participant_kind IN ('GUEST','DEPENDENT','ORGANIZER')", name="ck_event_participants_v2_identity"),
        Index("ix_event_participants_v2_event", "event_id"),
        Index("ix_event_participants_v2_person", "person_id"),
        UniqueConstraint("event_id", "person_id", name="uq_event_participants_v2_event_person"),
    )

    participant_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    event_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("events_v2.event_id", ondelete="CASCADE"), nullable=False)
    person_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="SET NULL"), nullable=True)
    invitation_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("event_invitations_v2.invitation_id", ondelete="SET NULL"), nullable=True)
    participant_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    age_group: Mapped[str] = mapped_column(String(16), nullable=False, default="UNKNOWN")
    attendance_status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    created_by_person_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="SET NULL"), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EventParticipantFoodFact(Base):
    __tablename__ = "event_participant_food_facts_v2"
    __table_args__ = (
        CheckConstraint("knowledge_state IN ('NOT_PROVIDED','UNKNOWN','KNOWN_NONE','KNOWN_PRESENT')", name="ck_event_food_facts_v2_state"),
        CheckConstraint("source_kind IN ('EVENT_RSVP','CORE_PERSON_PROFILE','MANUAL')", name="ck_event_food_facts_v2_source"),
    )

    fact_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    participant_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("event_participants_v2.participant_id", ondelete="CASCADE"), nullable=False, unique=True)
    knowledge_state: Mapped[str] = mapped_column(String(24), nullable=False, default="NOT_PROVIDED")
    restrictions_json: Mapped[list] = mapped_column(CoreJSON, nullable=False, default=list)
    source_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="MANUAL")
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EventMenuRevision(Base):
    __tablename__ = "event_menu_revisions_v2"
    __table_args__ = (UniqueConstraint("event_id", "revision_number", name="uq_event_menu_revisions_v2_number"),)

    revision_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    event_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("events_v2.event_id", ondelete="CASCADE"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT")
    expected_event_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by_person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="RESTRICT"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EventMenuItem(Base):
    __tablename__ = "event_menu_items_v2"
    __table_args__ = (UniqueConstraint("revision_id", "slot_key", name="uq_event_menu_items_v2_slot"),)

    menu_item_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    revision_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("event_menu_revisions_v2.revision_id", ondelete="CASCADE"), nullable=False)
    slot_key: Mapped[str] = mapped_column(String(96), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="EMPTY")
    recipe_version_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("recipe_versions.recipe_version_id", ondelete="RESTRICT"), nullable=True)
    servings: Mapped[float | None] = mapped_column(Float, nullable=True)
    safety_state: Mapped[str] = mapped_column(String(24), nullable=False, default="UNKNOWN")
    coverage_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)


class EventMenuItemParticipant(Base):
    __tablename__ = "event_menu_item_participants_v2"
    __table_args__ = (UniqueConstraint("menu_item_id", "participant_id", name="uq_event_menu_item_participant_v2"),)

    menu_item_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("event_menu_items_v2.menu_item_id", ondelete="CASCADE"), primary_key=True)
    participant_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("event_participants_v2.participant_id", ondelete="CASCADE"), primary_key=True)


class EventShoppingDemand(Base):
    __tablename__ = "event_shopping_demands_v2"
    __table_args__ = (
        CheckConstraint("uncertainty IN ('UNKNOWN','KNOWN')", name="ck_event_shopping_demands_v2_uncertainty"),
        CheckConstraint("state IN ('NEEDED','CHECKED','PURCHASED')", name="ck_event_shopping_demands_v2_state"),
        Index("ix_event_shopping_demands_v2_event", "event_id"),
        UniqueConstraint("event_id", "source_key", name="uq_event_shopping_demands_v2_source"),
    )

    demand_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    event_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("events_v2.event_id", ondelete="CASCADE"), nullable=False)
    menu_item_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("event_menu_items_v2.menu_item_id", ondelete="SET NULL"), nullable=True)
    display_text: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    uncertainty: Mapped[str] = mapped_column(String(16), nullable=False, default="UNKNOWN")
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="NEEDED")
    source_kind: Mapped[str] = mapped_column(String(48), nullable=False, default="EVENT_MENU")
    source_key: Mapped[str] = mapped_column(String(160), nullable=False)
    # Optional W5 projection; the database migration owns the cross-domain FK.
    shopping_list_id: Mapped[str | None] = mapped_column(CoreUUID, nullable=True)
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
