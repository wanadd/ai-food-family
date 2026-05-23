from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    accepted_terms: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    accepted_privacy: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    accepted_personal_data: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    legal_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    legal_documents_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phone_skipped: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    family_membership = relationship(
        "FamilyMember", back_populates="user", uselist=False
    )
    notification_settings = relationship(
        "UserNotificationSettings",
        back_populates="user",
        uselist=False,
    )
    recipe_favorites = relationship(
        "RecipeFavorite",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    preferences = relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
    )
