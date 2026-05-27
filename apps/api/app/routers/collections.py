from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.models.user import User
from app.routers.recipe_engine_common import require_feature
from app.schemas.recipe_collection import (
    AddRecipesToCollectionRequest,
    CollectionCreateRequest,
    CollectionDetailResponse,
    CollectionResponse,
    CollectionUpdateRequest,
)
from app.services.app_scope import AppScope
from app.services import recipes as recipes_service
from app.services.recipes.collections import (
    CollectionDetail,
    CollectionRef,
    CollectionService,
    CollectionVisibility,
)

router = APIRouter(prefix="/collections", tags=["collections"])


def _collection_response(ref: CollectionRef) -> CollectionResponse:
    return CollectionResponse(
        id=ref.id,
        name=ref.name,
        visibility=ref.visibility.value,
        description=ref.description,
        emoji=ref.emoji,
        color=ref.color,
        is_pinned=ref.is_pinned,
        is_dynamic=ref.is_dynamic,
        recipes_count=ref.recipes_count,
        owner_user_id=ref.owner_user_id,
        owner_family_id=ref.owner_family_id,
    )


def _collection_detail_response(detail: CollectionDetail) -> CollectionDetailResponse:
    return CollectionDetailResponse(
        collection=_collection_response(detail.ref),
        recipe_ids=list(detail.recipe_ids),
    )


def _collection_or_404(
    service: CollectionService,
    collection_id: int,
    *,
    user: User,
    scope: AppScope,
) -> CollectionDetail:
    detail = service.get(collection_id, user=user, scope=scope)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )
    return detail


@router.get("", response_model=list[CollectionResponse])
def list_collections(
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> list[CollectionResponse]:
    require_feature(settings.recipe_collections, "RECIPE_COLLECTIONS")
    collections = CollectionService(db).list_visible(user, scope)
    return [_collection_response(ref) for ref in collections]


@router.post(
    "",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_collection(
    payload: CollectionCreateRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> CollectionResponse:
    require_feature(settings.recipe_collections, "RECIPE_COLLECTIONS")
    try:
        ref = CollectionService(db).create(
            name=payload.name,
            visibility=CollectionVisibility(payload.visibility),
            user=user,
            scope=scope,
            description=payload.description,
            emoji=payload.emoji,
            color=payload.color,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return _collection_response(ref)


@router.get("/{collection_id}", response_model=CollectionDetailResponse)
def get_collection(
    collection_id: int,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> CollectionDetailResponse:
    require_feature(settings.recipe_collections, "RECIPE_COLLECTIONS")
    detail = _collection_or_404(
        CollectionService(db), collection_id, user=user, scope=scope
    )
    return _collection_detail_response(detail)


@router.patch("/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: int,
    payload: CollectionUpdateRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> CollectionResponse:
    require_feature(settings.recipe_collections, "RECIPE_COLLECTIONS")
    changes = payload.model_dump(exclude_unset=True)
    ref = CollectionService(db).update(
        collection_id,
        user=user,
        scope=scope,
        **changes,
    )
    if ref is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )
    return _collection_response(ref)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: int,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> None:
    require_feature(settings.recipe_collections, "RECIPE_COLLECTIONS")
    ok = CollectionService(db).delete(collection_id, user=user, scope=scope)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )


@router.post("/{collection_id}/recipes", response_model=CollectionDetailResponse)
def add_recipes_to_collection(
    collection_id: int,
    payload: AddRecipesToCollectionRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> CollectionDetailResponse:
    require_feature(settings.recipe_collections, "RECIPE_COLLECTIONS")
    service = CollectionService(db)
    _collection_or_404(service, collection_id, user=user, scope=scope)

    missing = [
        recipe_id
        for recipe_id in payload.recipe_ids
        if recipes_service.get_recipe_model(db, recipe_id) is None
    ]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe not found: {missing[0]}",
        )

    service.add_recipes(collection_id, payload.recipe_ids, user=user, scope=scope)
    detail = _collection_or_404(service, collection_id, user=user, scope=scope)
    return _collection_detail_response(detail)


@router.delete(
    "/{collection_id}/recipes/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_recipe_from_collection(
    collection_id: int,
    recipe_id: int,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> None:
    require_feature(settings.recipe_collections, "RECIPE_COLLECTIONS")
    ok = CollectionService(db).remove_recipe(
        collection_id,
        recipe_id,
        user=user,
        scope=scope,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection recipe not found",
        )
