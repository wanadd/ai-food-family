from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.deps import get_verified_user
from app.models.user import User
from app.schemas.family import (
    FamilyCreateRequest,
    FamilyInviteByPhoneRequest,
    FamilyMemberCreateRequest,
    FamilyMemberResponse,
    FamilyMemberUpdateRequest,
    FamilyResponse,
)
from app.schemas.family_invite import FamilyInviteCreateRequest, FamilyInviteResponse
from app.services import family_invites as family_invites_service
from app.services.family_invites import InviteCreateResult, build_invite_deep_link
from app.services.users import mask_phone
from app.services import family as family_service
from app.services.telegram_bot import notify_invitee_about_invite

router = APIRouter(prefix="/families", tags=["families"])


async def _notify_invitee_background(invite_id: int, invitee_notified: bool) -> None:
    if not invitee_notified:
        return
    db = SessionLocal()
    try:
        await notify_invitee_about_invite(db, invite_id)
    finally:
        db.close()


def _invite_response_from_result(result: InviteCreateResult) -> FamilyInviteResponse:
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


@router.post("", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
def create_family(
    payload: FamilyCreateRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> FamilyResponse:
    return family_service.create_family(db, user, payload)


@router.get("/me", response_model=FamilyResponse | None)
def get_my_family(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> FamilyResponse | None:
    return family_service.get_my_family(db, user)


@router.post(
    "/{family_id}/invite-by-phone",
    response_model=FamilyInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
def invite_family_member_by_phone(
    family_id: int,
    payload: FamilyInviteByPhoneRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> FamilyInviteResponse:
    response = family_service.invite_member_by_phone(db, user, family_id, payload)
    background_tasks.add_task(
        _notify_invitee_background,
        response.id,
        response.invitee_notified,
    )
    return response


@router.post(
    "/{family_id}/invites",
    response_model=FamilyInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_family_invite(
    family_id: int,
    payload: FamilyInviteCreateRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> FamilyInviteResponse:
    result = family_invites_service.create_invite(
        db, user, family_id, payload.phone_number
    )
    response = _invite_response_from_result(result)
    background_tasks.add_task(
        _notify_invitee_background,
        response.id,
        response.invitee_notified,
    )
    return response


@router.get("/{family_id}/invites", response_model=list[FamilyInviteResponse])
def list_family_invites(
    family_id: int,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> list[FamilyInviteResponse]:
    invites = family_invites_service.list_pending_for_family(db, user, family_id)
    return [
        FamilyInviteResponse(
            id=inv.id,
            family_id=inv.family_id,
            status=inv.status,
            invite_token=inv.invite_token,
            invited_phone_masked=mask_phone(inv.invited_phone_normalized),
            invited_user_id=inv.invited_user_id,
            share_url=family_invites_service.build_share_url(inv.invite_token),
            share_text=f"Приглашение в семью «{inv.family.name if inv.family else ''}»",
            deep_link=build_invite_deep_link(inv.invite_token),
            invitee_notified=inv.invited_user_id is not None,
            family_name=inv.family.name if inv.family else "",
            created_at=inv.created_at,
        )
        for inv in invites
    ]


@router.post(
    "/{family_id}/members",
    response_model=FamilyMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_family_member(
    family_id: int,
    payload: FamilyMemberCreateRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> FamilyMemberResponse:
    return family_service.add_member(db, user, family_id, payload)


@router.patch("/{family_id}/members/{member_id}", response_model=FamilyMemberResponse)
def update_family_member(
    family_id: int,
    member_id: int,
    payload: FamilyMemberUpdateRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> FamilyMemberResponse:
    return family_service.update_member(db, user, family_id, member_id, payload)


@router.delete("/{family_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_family_member(
    family_id: int,
    member_id: int,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> None:
    family_service.delete_member(db, user, family_id, member_id)
