from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.recipe import (
    FavoriteToggleResponse,
    RecipeDetail,
    RecipeFiltersResponse,
    RecipeListResponse,
)
from app.services import recipes as recipes_service

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/filters", response_model=RecipeFiltersResponse)
def get_recipe_filters(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecipeFiltersResponse:
    _ = user
    return recipes_service.get_filters(db)


@router.get("", response_model=RecipeListResponse)
def list_recipes(
    q: str | None = Query(default=None, max_length=120),
    meal_type: str | None = Query(default=None),
    category: str | None = Query(default=None),
    diet: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    max_prep_time: int | None = Query(default=None, ge=5, le=300),
    favorites_only: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecipeListResponse:
    return recipes_service.list_recipes(
        db,
        user,
        q=q,
        meal_type=meal_type or None,
        category=category or None,
        diet=diet or None,
        difficulty=difficulty or None,
        max_prep_time=max_prep_time,
        favorites_only=favorites_only,
    )


@router.get("/{recipe_id}", response_model=RecipeDetail)
def get_recipe(
    recipe_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecipeDetail:
    recipe = recipes_service.get_recipe(db, user, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe


@router.post("/{recipe_id}/favorite", response_model=FavoriteToggleResponse)
def toggle_recipe_favorite(
    recipe_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FavoriteToggleResponse:
    result = recipes_service.toggle_favorite(db, user, recipe_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return result
