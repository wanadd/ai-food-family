from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CookingBatch(Base):
    __tablename__ = "cooking_batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True, nullable=True
    )
    owner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    recipe_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipes.id", ondelete="SET NULL"), index=True, nullable=True
    )
    recipe_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    menu_selection_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_menu_selections.id", ondelete="SET NULL"), nullable=True
    )
    day_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    planned_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    meal_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    batch_status: Mapped[str] = mapped_column(
        String(32), default="active", server_default="active"
    )
    total_servings: Mapped[float] = mapped_column(Float, default=1.0, server_default="1")
    remaining_servings: Mapped[float] = mapped_column(
        Float, default=1.0, server_default="1"
    )
    serving_unit: Mapped[str] = mapped_column(
        String(32), default="порция", server_default="порция"
    )
    cooked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    events = relationship(
        "CookingBatchEvent",
        back_populates="batch",
        cascade="all, delete-orphan",
    )


class CookingBatchEvent(Base):
    __tablename__ = "cooking_batch_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("cooking_batches.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(32))
    actor_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    servings_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    remaining_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    batch = relationship("CookingBatch", back_populates="events")
