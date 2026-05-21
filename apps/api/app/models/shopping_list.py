from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FamilyShoppingList(Base):
    __tablename__ = "family_shopping_lists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=True, index=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), unique=True, nullable=True, index=True
    )
    menu_selection_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_menu_selections.id", ondelete="SET NULL"),
        nullable=True,
    )
    items: Mapped[list] = mapped_column(JSONB, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    family = relationship("Family")
    owner = relationship("User", foreign_keys=[user_id])
    menu_selection = relationship("FamilyMenuSelection")
