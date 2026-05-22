import logging
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.family import Family, FamilyMember, FamilyRole
from app.models.family_invite import FamilyInvite, FamilyInviteStatus
from app.models.user import User
from app.services import family as family_service
from app.services.users import (
    find_user_by_phone,
    mask_phone,
    normalize_phone,
    user_has_verified_phone,
)

logger = logging.getLogger(__name__)

# Open invite link (no phone yet); one pending link per family is reused.
LINK_INVITE_PHONE = "__link__"


def is_link_invite(invite: FamilyInvite) -> bool:
    return invite.invited_phone_normalized == LINK_INVITE_PHONE


@dataclass
class InviteCreateResult:
    invite: FamilyInvite
    family_name: str
    invitee_notified: bool
    share_url: str
    share_text: str


def build_invite_deep_link(invite_token: str) -> str:
    username = settings.telegram_bot_username.lstrip("@")
    return f"https://t.me/{username}?start=invite_{invite_token}"


def build_share_url(invite_token: str) -> str:
    deep_link = build_invite_deep_link(invite_token)
    text = "Вас пригласили в семью в ПланАм"
    from urllib.parse import quote

    return (
        "https://t.me/share/url?"
        f"url={quote(deep_link, safe='')}&text={quote(text, safe='')}"
    )


def _generate_invite_token() -> str:
    return secrets.token_urlsafe(18)


def _get_pending_invite(
    db: Session, family_id: int, phone_normalized: str
) -> FamilyInvite | None:
    return (
        db.query(FamilyInvite)
        .filter(
            FamilyInvite.family_id == family_id,
            FamilyInvite.invited_phone_normalized == phone_normalized,
            FamilyInvite.status == FamilyInviteStatus.PENDING.value,
        )
        .one_or_none()
    )


def _require_admin_membership(db: Session, user: User, family_id: int) -> FamilyMember:
    membership = family_service.get_user_membership(db, user)
    if membership is None or membership.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")
    family_service.require_admin(membership)
    return membership


def create_invite(
    db: Session,
    inviter: User,
    family_id: int,
    phone_number: str,
    *,
    contact_first_name: str | None = None,
) -> InviteCreateResult:
    if not user_has_verified_phone(inviter):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Подтвердите свой номер телефона в боте (/start)",
        )

    membership = _require_admin_membership(db, inviter, family_id)
    phone_normalized = normalize_phone(phone_number)
    if not phone_normalized or len(re.sub(r"\D", "", phone_normalized)) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите корректный номер телефона",
        )

    inviter_phone = normalize_phone(inviter.phone_number or "")
    if phone_normalized == inviter_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя пригласить себя",
        )

    existing_pending = _get_pending_invite(db, family_id, phone_normalized)
    if existing_pending is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Приглашение на этот номер уже отправлено",
        )

    invited_user = find_user_by_phone(db, phone_number)
    if invited_user is not None:
        existing_membership = family_service.get_user_membership(db, invited_user)
        if existing_membership is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь уже состоит в семье",
            )

    family = membership.family
    family_name = family.name if family else "семья"

    invite = FamilyInvite(
        family_id=family_id,
        invited_phone_normalized=phone_normalized,
        invited_user_id=invited_user.id if invited_user else None,
        invited_by_user_id=inviter.id,
        status=FamilyInviteStatus.PENDING.value,
        invite_token=_generate_invite_token(),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    logger.info(
        "Family invite created id=%s family_id=%s phone=%s",
        invite.id,
        family_id,
        mask_phone(phone_normalized),
    )

    share_url = build_share_url(invite.invite_token)
    share_text = (
        f"Вас пригласили в семью «{family_name}» в ПланАм. "
        f"Перейдите по ссылке: {build_invite_deep_link(invite.invite_token)}"
    )

    invitee_notified = bool(
        invited_user
        and user_has_verified_phone(invited_user)
        and invited_user.telegram_id
    )

    return InviteCreateResult(
        invite=invite,
        family_name=family_name,
        invitee_notified=invitee_notified,
        share_url=share_url,
        share_text=share_text,
    )


def _get_pending_link_invite(db: Session, family_id: int) -> FamilyInvite | None:
    return (
        db.query(FamilyInvite)
        .filter(
            FamilyInvite.family_id == family_id,
            FamilyInvite.invited_phone_normalized == LINK_INVITE_PHONE,
            FamilyInvite.status == FamilyInviteStatus.PENDING.value,
        )
        .order_by(FamilyInvite.created_at.desc())
        .first()
    )


def create_link_invite(db: Session, inviter: User, family_id: int) -> InviteCreateResult:
    if not user_has_verified_phone(inviter):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Подтвердите свой номер телефона в боте (/start)",
        )

    membership = _require_admin_membership(db, inviter, family_id)
    family = membership.family
    family_name = family.name if family else "семья"

    existing = _get_pending_link_invite(db, family_id)
    if existing is not None:
        share_url = build_share_url(existing.invite_token)
        share_text = (
            f"Вас пригласили в семью «{family_name}» в ПланАм. "
            f"Перейдите по ссылке: {build_invite_deep_link(existing.invite_token)}"
        )
        return InviteCreateResult(
            invite=existing,
            family_name=family_name,
            invitee_notified=False,
            share_url=share_url,
            share_text=share_text,
        )

    invite = FamilyInvite(
        family_id=family_id,
        invited_phone_normalized=LINK_INVITE_PHONE,
        invited_user_id=None,
        invited_by_user_id=inviter.id,
        status=FamilyInviteStatus.PENDING.value,
        invite_token=_generate_invite_token(),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    logger.info("Family link invite created id=%s family_id=%s", invite.id, family_id)

    share_url = build_share_url(invite.invite_token)
    share_text = (
        f"Вас пригласили в семью «{family_name}» в ПланАм. "
        f"Перейдите по ссылке: {build_invite_deep_link(invite.invite_token)}"
    )
    return InviteCreateResult(
        invite=invite,
        family_name=family_name,
        invitee_notified=False,
        share_url=share_url,
        share_text=share_text,
    )


def bind_link_invite_to_user(db: Session, invite: FamilyInvite, user: User) -> FamilyInvite:
    if not is_link_invite(invite):
        return invite
    if not user.phone_number:
        return invite

    phone_normalized = normalize_phone(user.phone_number)
    inviter = db.get(User, invite.invited_by_user_id)
    inviter_phone = normalize_phone(inviter.phone_number or "") if inviter else ""
    if phone_normalized == inviter_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя принять приглашение в свою семью как администратор",
        )

    existing_membership = family_service.get_user_membership(db, user)
    if existing_membership is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Вы уже состоите в семье",
        )

    other_pending = _get_pending_invite(db, invite.family_id, phone_normalized)
    if other_pending is not None and other_pending.id != invite.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="У вас уже есть другое приглашение в эту семью",
        )

    invite.invited_phone_normalized = phone_normalized
    invite.invited_user_id = user.id
    db.commit()
    db.refresh(invite)
    return invite


def get_invite_by_token(db: Session, token: str) -> FamilyInvite | None:
    return (
        db.query(FamilyInvite)
        .options(joinedload(FamilyInvite.family))
        .filter(FamilyInvite.invite_token == token)
        .one_or_none()
    )


def get_invite_by_id(db: Session, invite_id: int) -> FamilyInvite | None:
    return (
        db.query(FamilyInvite)
        .options(joinedload(FamilyInvite.family), joinedload(FamilyInvite.invited_by))
        .filter(FamilyInvite.id == invite_id)
        .one_or_none()
    )


def list_pending_for_family(db: Session, user: User, family_id: int) -> list[FamilyInvite]:
    _require_admin_membership(db, user, family_id)
    return (
        db.query(FamilyInvite)
        .options(joinedload(FamilyInvite.family))
        .filter(
            FamilyInvite.family_id == family_id,
            FamilyInvite.status == FamilyInviteStatus.PENDING.value,
        )
        .order_by(FamilyInvite.created_at.desc())
        .all()
    )


def list_pending_for_user_phone(db: Session, user: User) -> list[FamilyInvite]:
    if not user.phone_number:
        return []
    phone_normalized = normalize_phone(user.phone_number)
    return (
        db.query(FamilyInvite)
        .options(
            joinedload(FamilyInvite.family),
            joinedload(FamilyInvite.invited_by),
        )
        .filter(
            FamilyInvite.invited_phone_normalized == phone_normalized,
            FamilyInvite.status == FamilyInviteStatus.PENDING.value,
        )
        .order_by(FamilyInvite.created_at.desc())
        .all()
    )


def link_pending_invites_to_user(db: Session, user: User) -> list[FamilyInvite]:
    if not user.phone_number:
        return []
    phone_normalized = normalize_phone(user.phone_number)
    invites = (
        db.query(FamilyInvite)
        .options(joinedload(FamilyInvite.family))
        .filter(
            FamilyInvite.invited_phone_normalized == phone_normalized,
            FamilyInvite.status == FamilyInviteStatus.PENDING.value,
        )
        .all()
    )
    for invite in invites:
        if invite.invited_user_id is None:
            invite.invited_user_id = user.id
    db.commit()
    return invites


def user_matches_invite(user: User, invite: FamilyInvite) -> bool:
    if invite.invited_user_id and invite.invited_user_id == user.id:
        return True
    if is_link_invite(invite):
        return False
    if not user.phone_number:
        return False
    return normalize_phone(user.phone_number) == invite.invited_phone_normalized


def accept_invite(db: Session, user: User, invite_id: int) -> FamilyMember:
    invite = get_invite_by_id(db, invite_id)
    if invite is None or invite.status != FamilyInviteStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Приглашение не найдено")

    if not user_matches_invite(user, invite):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Это приглашение не для вас",
        )

    existing = family_service.get_user_membership(db, user)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Вы уже состоите в семье",
        )

    display_name = user.first_name or user.username or f"User {user.telegram_id}"
    member = FamilyMember(
        family_id=invite.family_id,
        user_id=user.id,
        display_name=display_name,
        role=FamilyRole.ADULT.value,
        goals=[],
        restrictions=[],
    )
    invite.status = FamilyInviteStatus.ACCEPTED.value
    invite.invited_user_id = user.id
    invite.accepted_at = datetime.now(timezone.utc)
    db.add(member)
    db.commit()
    db.refresh(member)
    db.refresh(invite)

    logger.info(
        "Family invite accepted id=%s user_id=%s family_id=%s",
        invite.id,
        user.id,
        invite.family_id,
    )
    return member


def decline_invite(db: Session, user: User, invite_id: int) -> FamilyInvite:
    invite = get_invite_by_id(db, invite_id)
    if invite is None or invite.status != FamilyInviteStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Приглашение не найдено")

    if not user_matches_invite(user, invite):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Это приглашение не для вас",
        )

    invite.status = FamilyInviteStatus.DECLINED.value
    invite.declined_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(invite)
    return invite


def inviter_display_name(user: User | None) -> str:
    if not user:
        return "Участник"
    return user.first_name or user.username or "Участник"
