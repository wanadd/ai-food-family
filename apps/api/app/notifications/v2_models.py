from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import CoreJSON, CoreUUID
from app.database import Base


STATES = "('pending', 'leased', 'succeeded', 'retryable', 'failed', 'dead-letter', 'manual-review')"


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        CheckConstraint("subject_kind IN ('PERSON', 'HOUSEHOLD')", name="ck_notification_preferences_subject"),
        UniqueConstraint("subject_kind", "subject_id", "channel", name="uq_notification_preferences_subject_channel"),
        UniqueConstraint("subject_kind", "subject_id", "channel", "idempotency_key", name="uq_notification_preferences_idempotency"),
        Index("ix_notification_preferences_subject", "subject_kind", "subject_id"),
    )

    preference_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    subject_kind: Mapped[str] = mapped_column(String(16))
    subject_id: Mapped[str] = mapped_column(CoreUUID)
    channel: Mapped[str] = mapped_column(String(32))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    shopping_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    cooking_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64))
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5))
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    request_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class NotificationIntent(Base):
    __tablename__ = "notification_intents"
    __table_args__ = (
        CheckConstraint("subject_kind IN ('PERSON', 'HOUSEHOLD')", name="ck_notification_intents_subject"),
        CheckConstraint(f"state IN {STATES}", name="ck_notification_intents_state"),
        UniqueConstraint("owner_domain", "aggregate_id", "intent_type", "idempotency_key", name="uq_notification_intents_key"),
        Index("ix_notification_intents_available", "state", "available_at"),
    )

    intent_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    owner_domain: Mapped[str] = mapped_column(String(64))
    aggregate_id: Mapped[str] = mapped_column(CoreUUID)
    intent_type: Mapped[str] = mapped_column(String(96))
    subject_kind: Mapped[str] = mapped_column(String(16))
    subject_id: Mapped[str] = mapped_column(CoreUUID)
    recipient_person_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="SET NULL"))
    recipient_household_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("core_households.household_id", ondelete="SET NULL"))
    state: Mapped[str] = mapped_column(String(32), default="pending")
    payload_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    navigation_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(200))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        CheckConstraint(f"state IN {STATES}", name="ck_notification_deliveries_state"),
        CheckConstraint("attempt_count >= 0", name="ck_notification_deliveries_attempts"),
        UniqueConstraint("delivery_key", name="uq_notification_deliveries_key"),
        Index("ix_notification_deliveries_claim", "state", "next_attempt_at", "lease_until"),
    )

    delivery_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    intent_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("notification_intents.intent_id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(32))
    provider: Mapped[str] = mapped_column(String(64))
    provider_subject: Mapped[str | None] = mapped_column(String(160))
    provider_message_id: Mapped[str | None] = mapped_column(String(160))
    state: Mapped[str] = mapped_column(String(32), default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(160))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(96))
    last_error_message: Mapped[str | None] = mapped_column(String(500))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_key: Mapped[str] = mapped_column(String(240))
    provider_metadata_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(f"state IN {STATES}", name="ck_jobs_state"),
        CheckConstraint("attempt_count >= 0", name="ck_jobs_attempts"),
        UniqueConstraint("kind", "idempotency_key", name="uq_jobs_key"),
        Index("ix_jobs_claim", "state", "available_at", "lease_until"),
    )

    job_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    kind: Mapped[str] = mapped_column(String(96))
    state: Mapped[str] = mapped_column(String(32), default="pending")
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    lease_owner: Mapped[str | None] = mapped_column(String(160))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int | None] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(240))
    payload_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    last_error_code: Mapped[str | None] = mapped_column(String(96))
    last_error_message: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (
        CheckConstraint("state IN ('pending', 'processed', 'failed')", name="ck_outbox_events_state"),
        UniqueConstraint("aggregate_id", "event_kind", "idempotency_key", name="uq_outbox_events_key"),
        Index("ix_outbox_events_available", "state", "available_at"),
    )

    outbox_event_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    aggregate_id: Mapped[str] = mapped_column(CoreUUID)
    event_kind: Mapped[str] = mapped_column(String(96))
    state: Mapped[str] = mapped_column(String(24), default="pending")
    payload_json: Mapped[dict] = mapped_column(CoreJSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(240))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
