from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ShoppingCategory(Base):
    __tablename__ = "shopping_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(120))
    icon: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_food: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
