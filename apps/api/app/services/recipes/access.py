"""Recipe write access rules (P0-5)."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.deps import is_admin_user
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.recipe import RecipeCreateRequest, RecipeUpdateRequest

DRAFT_SOURCE_TYPE = "draft"
DRAFT_OWNER_PREFIX = "planam:draft-owner:"


def recipe_owner_user_id(recipe: Recipe) -> int | None:
    url = (recipe.source_url or "").strip()
    if not url.startswith(DRAFT_OWNER_PREFIX):
        return None
    suffix = url[len(DRAFT_OWNER_PREFIX) :]
    if suffix.isdigit():
        return int(suffix)
    return None


def is_user_owned_draft(recipe: Recipe, user: User) -> bool:
    return (
        (recipe.source_type or "").strip() == DRAFT_SOURCE_TYPE
        and recipe_owner_user_id(recipe) == user.id
    )


def assert_can_create_recipe(user: User, payload: RecipeCreateRequest) -> None:
    if is_admin_user(user):
        return
    if (payload.source_type or "").strip() != DRAFT_SOURCE_TYPE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only draft recipes can be created",
        )


def assert_can_update_recipe(
    user: User,
    recipe: Recipe,
    payload: RecipeUpdateRequest,
) -> None:
    if is_admin_user(user):
        return
    if not is_user_owned_draft(recipe, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recipe is not editable",
        )
    if payload.is_active is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot publish recipes",
        )
