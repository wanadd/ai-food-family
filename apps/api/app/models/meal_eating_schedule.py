from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MealEatingSchedule(Base):
    __tablename__ = "meal_eating_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    family_member_id: Mapped[int] = mapped_column(
        ForeignKey("family_members.id", ondelete="CASCADE"), unique=True, index=True
    )
    family_id: Mapped[int] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True
    )
    schedule_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
