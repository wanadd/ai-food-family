from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FamilyMenuSelection(Base):
    __tablename__ = "family_menu_selections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    variant: Mapped[str] = mapped_column(String(16))
    menu_data: Mapped[dict] = mapped_column(JSONB)
    selected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    family = relationship("Family")
    user = relationship("User")
