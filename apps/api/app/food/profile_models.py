from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.models import CoreJSON, CoreUUID
from app.database import Base

FoodFactValueJSON = JSON(none_as_null=True).with_variant(JSONB(none_as_null=True), "postgresql")


class FoodProfile(Base):
    __tablename__ = "food_profiles"
    __table_args__ = (
        CheckConstraint("profile_status IN ('ACTIVE', 'INACTIVE', 'MERGED')", name="ck_food_profiles_status"),
    )

    food_profile_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    person_id: Mapped[str] = mapped_column(
        CoreUUID,
        ForeignKey("core_persons.person_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    profile_status: Mapped[str] = mapped_column(String(24), nullable=False, default="ACTIVE")
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    facts = relationship("FoodProfileFact", back_populates="food_profile", cascade="all, delete-orphan")
    reconfirmations = relationship(
        "FoodProfileReconfirmation",
        back_populates="food_profile",
        cascade="all, delete-orphan",
    )


class FoodProfileFact(Base):
    __tablename__ = "food_profile_facts"
    __table_args__ = (
        UniqueConstraint(
            "food_profile_id",
            "fact_type",
            "fact_key",
            "source_kind",
            "source_legacy_table",
            "source_legacy_id_text",
            name="uq_food_profile_fact_legacy_source",
        ),
        CheckConstraint(
            "knowledge_state IN ('UNKNOWN', 'NOT_PROVIDED', 'KNOWN_NONE', 'KNOWN_PRESENT')",
            name="ck_food_profile_facts_knowledge_state",
        ),
        CheckConstraint(
            "confirmation_status IN ('UNCONFIRMED', 'CONFIRMED', 'NEEDS_RECONFIRMATION', 'SUPERSEDED')",
            name="ck_food_profile_facts_confirmation_status",
        ),
        CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_food_profile_facts_period"),
        CheckConstraint(
            "(knowledge_state = 'KNOWN_PRESENT' AND value_json IS NOT NULL) OR "
            "(knowledge_state = 'KNOWN_NONE' AND value_json IS NULL) OR "
            "(knowledge_state IN ('UNKNOWN', 'NOT_PROVIDED'))",
            name="ck_food_profile_facts_value_known_state",
        ),
        Index("ix_food_profile_facts_profile_type_state", "food_profile_id", "fact_type", "knowledge_state"),
        Index("ix_food_profile_facts_profile_type_time", "food_profile_id", "fact_type", "effective_from"),
    )

    fact_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    food_profile_id: Mapped[str] = mapped_column(
        CoreUUID,
        ForeignKey("food_profiles.food_profile_id", ondelete="CASCADE"),
        nullable=False,
    )
    fact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    fact_key: Mapped[str] = mapped_column(String(160), nullable=False)
    knowledge_state: Mapped[str] = mapped_column(String(24), nullable=False)
    value_json: Mapped[dict | list | None] = mapped_column(FoodFactValueJSON, nullable=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    source_kind: Mapped[str] = mapped_column(String(48), nullable=False)
    source_legacy_table: Mapped[str] = mapped_column(String(80), nullable=False)
    source_legacy_id_text: Mapped[str] = mapped_column(String(120), nullable=False)
    confirmation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNCONFIRMED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    food_profile = relationship("FoodProfile", back_populates="facts")


class FoodProfileReconfirmation(Base):
    __tablename__ = "food_profile_reconfirmations"
    __table_args__ = (
        UniqueConstraint(
            "food_profile_id",
            "fact_type",
            "fact_key",
            "reason",
            "source_legacy_table",
            "source_legacy_id_text",
            name="uq_food_profile_reconfirmation_source",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'RESOLVED', 'DISMISSED', 'SUPERSEDED')",
            name="ck_food_profile_reconfirmations_status",
        ),
        Index("ix_food_profile_reconfirmations_profile_status", "food_profile_id", "status"),
    )

    reconfirmation_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    food_profile_id: Mapped[str] = mapped_column(
        CoreUUID,
        ForeignKey("food_profiles.food_profile_id", ondelete="CASCADE"),
        nullable=False,
    )
    fact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    fact_key: Mapped[str] = mapped_column(String(160), nullable=False)
    reason: Mapped[str] = mapped_column(String(160), nullable=False)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING")
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    source_kind: Mapped[str] = mapped_column(String(48), nullable=False)
    source_legacy_table: Mapped[str] = mapped_column(String(80), nullable=False)
    source_legacy_id_text: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    food_profile = relationship("FoodProfile", back_populates="reconfirmations")
