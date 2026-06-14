from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MealConsumptionLog(Base):
    __tablename__ = "meal_consumption_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    family_member_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_members.id", ondelete="SET NULL"), index=True, nullable=True
    )
    logged_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    menu_selection_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_menu_selections.id", ondelete="SET NULL"), nullable=True
    )
    day_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    planned_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    meal_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    recipe_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True
    )
    recipe_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="unknown")
    portion_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    calories_estimated: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_estimated: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_estimated: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_estimated: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
