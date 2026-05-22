from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.family import Family, FamilyMember, FamilyRole
from app.models.user import User
from app.schemas.family import (
    FamilyCreateRequest,
    FamilyInviteByPhoneRequest,
    FamilyMemberCreateRequest,
    FamilyMemberUpdateRequest,
    FamilyResponse,
    FamilyMemberResponse,
)
from app.services.users import find_user_by_phone, user_has_verified_phone


def _member_response(member: FamilyMember, current_user: User) -> FamilyMemberResponse:
    return FamilyMemberResponse(
        id=member.id,
        family_id=member.family_id,
        user_id=member.user_id,
        display_name=member.display_name,
        role=member.role,
        goals=member.goals or [],
        restrictions=member.restrictions or [],
        is_you=member.user_id == current_user.id,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


def _family_response(family: Family, current_user: User) -> FamilyResponse:
    membership = next(
        (member for member in family.members if member.user_id == current_user.id),
        None,
    )
    members = sorted(
        family.members,
        key=lambda member: (
            0 if member.role == FamilyRole.ADMIN.value else 1,
            member.display_name.lower(),
        ),
    )
    return FamilyResponse(
        id=family.id,
        name=family.name,
        members=[_member_response(member, current_user) for member in members],
        your_role=membership.role if membership else None,
        created_at=family.created_at,
        updated_at=family.updated_at,
    )


def get_user_membership(db: Session, user: User) -> FamilyMember | None:
    return (
        db.query(FamilyMember)
        .options(joinedload(FamilyMember.family).joinedload(Family.members))
        .filter(FamilyMember.user_id == user.id)
        .one_or_none()
    )


def get_family_for_user(db: Session, user: User) -> Family | None:
    membership = get_user_membership(db, user)
    if membership is None:
        return None
    return membership.family


def require_admin(member: FamilyMember) -> None:
    if member.role != FamilyRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only family admin can perform this action",
        )


def create_family(
    db: Session, user: User, payload: FamilyCreateRequest
) -> FamilyResponse:
    existing = get_user_membership(db, user)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already in a family",
        )

    display_name = user.first_name or user.username or f"User {user.telegram_id}"
    family = Family(name=payload.name.strip())
    admin_member = FamilyMember(
        family=family,
        user_id=user.id,
        display_name=display_name,
        role=FamilyRole.ADMIN.value,
        goals=[],
        restrictions=[],
    )
    db.add(family)
    db.add(admin_member)
    db.commit()
    db.refresh(family)
    family = (
        db.query(Family)
        .options(joinedload(Family.members))
        .filter(Family.id == family.id)
        .one()
    )
    return _family_response(family, user)


def get_my_family(db: Session, user: User) -> FamilyResponse | None:
    family = get_family_for_user(db, user)
    if family is None:
        return None
    return _family_response(family, user)


def invite_member_by_phone(
    db: Session,
    user: User,
    family_id: int,
    payload: FamilyInviteByPhoneRequest,
):
    from app.services import family_invites as invite_service
    from app.schemas.family_invite import FamilyInviteResponse
    from app.services.family_invites import build_invite_deep_link
    from app.services.users import mask_phone

    result = invite_service.create_invite(db, user, family_id, payload.phone_number)
    invite = result.invite
    return FamilyInviteResponse(
        id=invite.id,
        family_id=invite.family_id,
        status=invite.status,
        invite_token=invite.invite_token,
        invited_phone_masked=mask_phone(invite.invited_phone_normalized),
        invited_user_id=invite.invited_user_id,
        share_url=result.share_url,
        share_text=result.share_text,
        deep_link=build_invite_deep_link(invite.invite_token),
        invitee_notified=result.invitee_notified,
        family_name=result.family_name,
        created_at=invite.created_at,
    )


def add_member(
    db: Session,
    user: User,
    family_id: int,
    payload: FamilyMemberCreateRequest,
) -> FamilyMemberResponse:
    membership = get_user_membership(db, user)
    if membership is None or membership.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")
    require_admin(membership)

    if payload.role == FamilyRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add another admin. Transfer admin role instead.",
        )

    member = FamilyMember(
        family_id=family_id,
        display_name=payload.display_name.strip(),
        role=payload.role,
        goals=payload.goals,
        restrictions=payload.restrictions,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return _member_response(member, user)


def update_member(
    db: Session,
    user: User,
    family_id: int,
    member_id: int,
    payload: FamilyMemberUpdateRequest,
) -> FamilyMemberResponse:
    membership = get_user_membership(db, user)
    if membership is None or membership.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")
    require_admin(membership)

    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.id == member_id, FamilyMember.family_id == family_id)
        .one_or_none()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if payload.display_name is not None:
        member.display_name = payload.display_name.strip()
    if payload.role is not None:
        if payload.role == FamilyRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign admin role to members",
            )
        if (
            member.role == FamilyRole.ADMIN.value
            and member.user_id == user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin cannot change own role",
            )
        member.role = payload.role
    if payload.goals is not None:
        member.goals = payload.goals
    if payload.restrictions is not None:
        member.restrictions = payload.restrictions

    db.commit()
    db.refresh(member)
    return _member_response(member, user)


def delete_member(
    db: Session, user: User, family_id: int, member_id: int
) -> None:
    membership = get_user_membership(db, user)
    if membership is None or membership.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")
    require_admin(membership)

    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.id == member_id, FamilyMember.family_id == family_id)
        .one_or_none()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if member.role == FamilyRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the family admin",
        )

    db.delete(member)
    db.commit()
