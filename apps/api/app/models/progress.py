from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProgressEntry(Base):
    __tablename__ = "progress_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    person_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_members.id", ondelete="CASCADE"), nullable=True, index=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), nullable=True, index=True
    )
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    body_fat_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    chest_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    hips_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TrainingEntry(Base):
    __tablename__ = "training_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    person_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_members.id", ondelete="CASCADE"), nullable=True, index=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), nullable=True, index=True
    )
    training_type: Mapped[str] = mapped_column(String(64))
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    intensity: Mapped[str] = mapped_column(String(16), default="medium")
    calories_burned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    training_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class NutritionTarget(Base):
    __tablename__ = "nutrition_targets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    person_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_members.id", ondelete="CASCADE"), nullable=True, index=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), nullable=True, index=True
    )
    calories_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein_target_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fat_target_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    carbs_target_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fiber_target_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    water_target_ml: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goal_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
