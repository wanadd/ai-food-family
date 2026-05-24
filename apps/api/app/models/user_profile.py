from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    goals: Mapped[list] = mapped_column(JSONB, default=list)
    diets: Mapped[list] = mapped_column(JSONB, default=list)
    allergies: Mapped[list] = mapped_column(JSONB, default=list)
    restrictions: Mapped[list] = mapped_column(JSONB, default=list)
    favorite_foods: Mapped[str] = mapped_column(Text, default="")
    disliked_foods: Mapped[str] = mapped_column(Text, default="")
    budget: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cooking_time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(24), nullable=True)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    nutrition_goal: Mapped[str | None] = mapped_column(String(32), nullable=True)
    activity_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    medical_restrictions: Mapped[str] = mapped_column(Text, default="")
    banned_foods: Mapped[str] = mapped_column(Text, default="")
    dish_complexity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pro_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    goal_details: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="profile")
