from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MealConsumptionReminderEvent(Base):
    __tablename__ = "meal_consumption_reminder_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True, nullable=True
    )
    menu_selection_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_menu_selections.id", ondelete="SET NULL"), nullable=True
    )
    day_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    planned_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    meal_type: Mapped[str] = mapped_column(String(16))
    reminder_kind: Mapped[str] = mapped_column(
        String(64), default="meal_consumption_missing"
    )
    status: Mapped[str] = mapped_column(String(32), default="planned")
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    skipped_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    telegram_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
