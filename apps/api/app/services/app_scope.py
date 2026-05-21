from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.services import family as family_service

AppMode = Literal["personal", "family"]


@dataclass
class AppScope:
    mode: AppMode
    user_id: int
    family_id: int | None = None

    @property
    def is_personal(self) -> bool:
        return self.mode == "personal"

    @property
    def is_family(self) -> bool:
        return self.mode == "family"


def get_or_create_preferences(db: Session, user: User) -> UserPreferences:
    prefs = (
        db.query(UserPreferences)
        .filter(UserPreferences.user_id == user.id)
        .one_or_none()
    )
    if prefs is None:
        prefs = UserPreferences(user_id=user.id, active_mode="personal")
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


def user_has_family(db: Session, user: User) -> bool:
    return family_service.get_user_membership(db, user) is not None


def get_family_id(db: Session, user: User) -> int | None:
    membership = family_service.get_user_membership(db, user)
    return membership.family_id if membership else None


def resolve_scope(
    db: Session, user: User, requested_mode: str | None = None
) -> AppScope:
    prefs = get_or_create_preferences(db, user)
    family_id = get_family_id(db, user)
    has_family = family_id is not None

    mode: AppMode = prefs.active_mode  # type: ignore[assignment]
    if requested_mode in ("personal", "family"):
        mode = requested_mode  # type: ignore[assignment]

    if mode == "family" and not has_family:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Семейный режим доступен после создания семьи",
        )

    if mode == "family":
        return AppScope(mode="family", user_id=user.id, family_id=family_id)

    return AppScope(mode="personal", user_id=user.id, family_id=None)


def set_active_mode(db: Session, user: User, mode: AppMode) -> UserPreferences:
    if mode == "family" and not user_has_family(db, user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала создайте семью",
        )
    prefs = get_or_create_preferences(db, user)
    prefs.active_mode = mode
    db.commit()
    db.refresh(prefs)
    return prefs
