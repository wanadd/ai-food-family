from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MealCheckin(Base):
    __tablename__ = "meal_checkins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True, nullable=True
    )
    family_member_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_members.id", ondelete="SET NULL"), index=True, nullable=True
    )
    meal_plan_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recipe_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True
    )
    meal_type: Mapped[str] = mapped_column(String(16))
    planned_date: Mapped[date] = mapped_column(Date, index=True)
    planned_servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_status: Mapped[str] = mapped_column(String(32), default="planned")
    actual_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    actual_calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    leftover_servings_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
