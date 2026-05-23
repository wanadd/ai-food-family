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
from app.schemas.family_member_nutrition import (
    AllowAdminEditRequest,
    MemberNutritionUpdateRequest,
    VirtualMemberCreateRequest,
    VirtualNutritionProfile,
)
from app.schemas.nutrition_profile import NutritionProfileData, NutritionProData
from app.services import family_member_nutrition as member_nutrition
from app.services.nutrition_profile import save_nutrition_profile
from app.services.onboarding import get_or_create_profile


def _role_label(role: str) -> str:
    return "Админ" if role == FamilyRole.ADMIN.value else "Участник"


def _member_response(
    db: Session, member: FamilyMember, current_user: User
) -> FamilyMemberResponse:
    is_virtual = member_nutrition.member_is_virtual(member)
    is_you = member.user_id == current_user.id
    is_admin_viewer = False
    membership = get_user_membership(db, current_user)
    if membership and membership.family_id == member.family_id:
        is_admin_viewer = membership.role == FamilyRole.ADMIN.value

    goal_label = member_nutrition.nutrition_goal_label_for_member(db, member)
    if is_virtual:
        complete = member_nutrition.virtual_nutrition_complete(
            member_nutrition.virtual_nutrition_from_member(member)
        )
        summary = None
    else:
        complete = member_nutrition.telegram_member_nutrition_complete(db, member)
        summary = (
            member_nutrition.nutrition_summary_for_telegram_member(db, member)
            if is_admin_viewer and not is_you
            else None
        )

    can_admin_edit = is_admin_viewer and (
        is_virtual or (not is_you and member.allow_admin_profile_edit)
    )

    virtual_nutrition = None
    if is_virtual and is_admin_viewer:
        virtual_nutrition = member_nutrition.virtual_nutrition_from_member(member)
    elif (
        can_admin_edit
        and not is_virtual
        and member.user_id
        and is_admin_viewer
    ):
        linked = db.query(User).filter(User.id == member.user_id).one_or_none()
        if linked:
            profile = get_or_create_profile(db, linked)
            virtual_nutrition = VirtualNutritionProfile(
                age=profile.age,
                nutrition_goal=profile.nutrition_goal,
                allergies=profile.allergies or [],
                restrictions=profile.restrictions or [],
                diets=profile.diets or [],
                favorite_foods=profile.favorite_foods or "",
                disliked_foods=profile.disliked_foods or "",
                notes=profile.medical_restrictions or "",
            )

    return FamilyMemberResponse(
        id=member.id,
        family_id=member.family_id,
        user_id=member.user_id,
        display_name=member.display_name,
        role=member.role,
        goals=member.goals or [],
        restrictions=member.restrictions or [],
        is_you=is_you,
        is_virtual=is_virtual,
        member_type="virtual" if is_virtual else "telegram",
        role_label=_role_label(member.role),
        nutrition_goal_label=goal_label,
        nutrition_profile_complete=complete,
        allow_admin_profile_edit=member.allow_admin_profile_edit,
        virtual_kind=member.virtual_kind,
        can_admin_edit_nutrition=can_admin_edit,
        nutrition_summary=summary,
        virtual_nutrition=virtual_nutrition,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


def _family_response(db: Session, family: Family, current_user: User) -> FamilyResponse:
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
    member_responses = [
        _member_response(db, member, current_user) for member in members
    ]
    return FamilyResponse(
        id=family.id,
        name=family.name,
        members=member_responses,
        members_count=len(member_responses),
        plan_label="Семейный",
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
        is_virtual=False,
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
    return _family_response(db, family, user)


def get_my_family(db: Session, user: User) -> FamilyResponse | None:
    family = get_family_for_user(db, user)
    if family is None:
        return None
    return _family_response(db, family, user)


def invite_member_by_phone(
    db: Session,
    user: User,
    family_id: int,
    payload: FamilyInviteByPhoneRequest,
):
    from app.services import family_invites as invite_service
    from app.schemas.family_invite import FamilyInviteResponse
    from app.services.family_invites import build_invite_deep_link, is_link_invite
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
        is_link_invite=is_link_invite(invite),
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
        is_virtual=True,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return _member_response(db, member, user)


def add_virtual_member(
    db: Session,
    user: User,
    family_id: int,
    payload: VirtualMemberCreateRequest,
) -> FamilyMemberResponse:
    membership = get_user_membership(db, user)
    if membership is None or membership.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")
    require_admin(membership)

    member = FamilyMember(
        family_id=family_id,
        display_name=payload.display_name.strip(),
        role=payload.role,
        is_virtual=True,
        virtual_kind=payload.virtual_kind,
        goals=[],
        restrictions=[],
    )
    member_nutrition.apply_virtual_nutrition_to_member(member, payload.nutrition)
    db.add(member)
    db.commit()
    db.refresh(member)
    return _member_response(db, member, user)


def update_member_nutrition(
    db: Session,
    user: User,
    family_id: int,
    member_id: int,
    payload: MemberNutritionUpdateRequest,
) -> FamilyMemberResponse:
    membership = get_user_membership(db, user)
    if membership is None or membership.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.id == member_id, FamilyMember.family_id == family_id)
        .one_or_none()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    is_virtual = member_nutrition.member_is_virtual(member)
    is_you = member.user_id == user.id
    is_admin = membership.role == FamilyRole.ADMIN.value

    if is_virtual:
        if not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        member_nutrition.apply_virtual_nutrition_to_member(member, payload.nutrition)
        db.commit()
        db.refresh(member)
        return _member_response(db, member, user)

    if is_you:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use nutrition profile settings for your account",
        )

    if not is_admin or not member.allow_admin_profile_edit:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if member.user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid member")

    linked_user = db.query(User).filter(User.id == member.user_id).one()
    nutrition = payload.nutrition
    profile_data = NutritionProfileData(
        age=nutrition.age,
        nutrition_goal=nutrition.nutrition_goal,
        allergies=nutrition.allergies,
        medical_restrictions=nutrition.notes,
        banned_foods="",
        diets=nutrition.diets,
        favorite_foods=nutrition.favorite_foods,
        disliked_foods=nutrition.disliked_foods,
        completed=member_nutrition.virtual_nutrition_complete(nutrition),
        pro=NutritionProData(),
    )
    save_nutrition_profile(db, linked_user, profile_data)
    db.refresh(member)
    return _member_response(db, member, user)


def set_allow_admin_profile_edit(
    db: Session, user: User, payload: AllowAdminEditRequest
) -> FamilyMemberResponse:
    membership = get_user_membership(db, user)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not in a family")
    if member_nutrition.member_is_virtual(membership):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not applicable for virtual members",
        )

    membership.allow_admin_profile_edit = payload.allow_admin_profile_edit
    db.commit()
    db.refresh(membership)
    return _member_response(db, membership, user)


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
    if not member_nutrition.member_is_virtual(member):
        if payload.goals is not None or payload.restrictions is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Edit nutrition profile in account settings",
            )

    db.commit()
    db.refresh(member)
    return _member_response(db, member, user)


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
