from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExternalFoodLog(Base):
    __tablename__ = "external_food_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True, nullable=True
    )
    meal_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    planned_date: Mapped[date] = mapped_column(Date, index=True)
    source_type: Mapped[str] = mapped_column(String(32), default="manual")
    input_text: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    input_media_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    parsed_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    calories_estimated: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_estimated: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_estimated: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_estimated: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    linked_meal_consumption_log_id: Mapped[int | None] = mapped_column(
        ForeignKey("meal_consumption_logs.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
