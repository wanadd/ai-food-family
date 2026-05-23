from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventPlan(Base):
    __tablename__ = "event_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    guests_count: Mapped[int] = mapped_column(Integer, default=4)
    budget: Mapped[str | None] = mapped_column(String(32), nullable=True)
    theme: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cuisine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    religious_restriction: Mapped[str] = mapped_column(String(32), default="none")
    fasting_mode: Mapped[str] = mapped_column(String(32), default="none")
    drink_menu_mode: Mapped[str] = mapped_column(String(32), default="non_alcoholic")
    alcohol_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    kids_drinks_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    allergies_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    estimated_cost_rub: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
