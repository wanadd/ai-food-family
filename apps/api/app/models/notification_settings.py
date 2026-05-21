from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserNotificationSettings(Base):
    __tablename__ = "user_notification_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    buy_reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    cook_reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    buy_reminder_time: Mapped[str] = mapped_column(String(5), default="09:00")
    cook_reminder_time: Mapped[str] = mapped_column(String(5), default="17:30")
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    last_buy_sent_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_cook_sent_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="notification_settings")
