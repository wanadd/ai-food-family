from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
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
from app.services import family as family_service

router = APIRouter(prefix="/families", tags=["families"])


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
    response_model=FamilyMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def invite_family_member_by_phone(
    family_id: int,
    payload: FamilyInviteByPhoneRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> FamilyMemberResponse:
    return family_service.invite_member_by_phone(db, user, family_id, payload)


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
