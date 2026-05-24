from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MealLeftover(Base):
    __tablename__ = "meal_leftovers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True, nullable=True
    )
    dish_name: Mapped[str] = mapped_column(String(200))
    portions_remaining: Mapped[int] = mapped_column(Integer, default=1)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    leftover_status: Mapped[str] = mapped_column(String(32), default="active")
    added_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    family = relationship("Family")
    owner = relationship("User", foreign_keys=[user_id])
