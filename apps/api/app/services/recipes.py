from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.data.recipe_seed import SEED_RECIPES
from app.models.recipe import Recipe, RecipeFavorite
from app.models.user import User
from app.schemas.recipe import (
    FavoriteToggleResponse,
    RecipeDetail,
    RecipeFiltersResponse,
    RecipeIngredient,
    RecipeListResponse,
    RecipeSummary,
)

FILTER_LABELS = {
    "meal_types": [
        {"value": "breakfast", "label": "Завтрак"},
        {"value": "lunch", "label": "Обед"},
        {"value": "dinner", "label": "Ужин"},
        {"value": "snack", "label": "Перекус"},
    ],
    "categories": [
        {"value": "soup", "label": "Супы"},
        {"value": "main", "label": "Основные"},
        {"value": "salad", "label": "Салаты"},
        {"value": "dessert", "label": "Десерты"},
        {"value": "quick", "label": "Быстрые"},
        {"value": "kids", "label": "Детские"},
    ],
    "diets": [
        {"value": "vegetarian", "label": "Вегетарианское"},
        {"value": "vegan", "label": "Веганское"},
        {"value": "kids_friendly", "label": "Для детей"},
        {"value": "budget", "label": "Экономное"},
        {"value": "low_sugar", "label": "Меньше сахара"},
        {"value": "low_salt", "label": "Меньше соли"},
        {"value": "pescatarian", "label": "С рыбой"},
    ],
    "difficulties": [
        {"value": "easy", "label": "Легко"},
        {"value": "medium", "label": "Средне"},
        {"value": "hard", "label": "Сложно"},
    ],
}


def seed_recipes_if_empty(db: Session) -> None:
    count = db.query(Recipe).count()
    if count > 0:
        return
    for item in SEED_RECIPES:
        db.add(Recipe(**item))
    db.commit()


def _favorite_ids(db: Session, user_id: int) -> set[int]:
    rows = (
        db.query(RecipeFavorite.recipe_id)
        .filter(RecipeFavorite.user_id == user_id)
        .all()
    )
    return {row[0] for row in rows}


def _to_summary(recipe: Recipe, favorite_ids: set[int]) -> RecipeSummary:
    return RecipeSummary(
        id=recipe.id,
        title=recipe.title,
        description=recipe.description,
        meal_type=recipe.meal_type,
        category=recipe.category,
        prep_time_minutes=recipe.prep_time_minutes,
        servings=recipe.servings,
        difficulty=recipe.difficulty,
        diets=recipe.diets or [],
        tags=recipe.tags or [],
        is_favorited=recipe.id in favorite_ids,
    )


def _to_detail(recipe: Recipe, favorite_ids: set[int]) -> RecipeDetail:
    summary = _to_summary(recipe, favorite_ids)
    return RecipeDetail(
        **summary.model_dump(),
        ingredients=[
            RecipeIngredient.model_validate(item) for item in (recipe.ingredients or [])
        ],
        steps=recipe.steps or [],
        created_at=recipe.created_at,
    )


def get_filters(db: Session) -> RecipeFiltersResponse:
    max_time = db.query(Recipe.prep_time_minutes).order_by(Recipe.prep_time_minutes.desc()).first()
    return RecipeFiltersResponse(
        meal_types=FILTER_LABELS["meal_types"],
        categories=FILTER_LABELS["categories"],
        diets=FILTER_LABELS["diets"],
        difficulties=FILTER_LABELS["difficulties"],
        max_prep_time=max_time[0] if max_time else 60,
    )


def list_recipes(
    db: Session,
    user: User,
    *,
    q: str | None = None,
    meal_type: str | None = None,
    category: str | None = None,
    diet: str | None = None,
    difficulty: str | None = None,
    max_prep_time: int | None = None,
    favorites_only: bool = False,
) -> RecipeListResponse:
    query = db.query(Recipe)
    favorite_ids = _favorite_ids(db, user.id)

    if favorites_only:
        if not favorite_ids:
            return RecipeListResponse(items=[], total=0)
        query = query.filter(Recipe.id.in_(favorite_ids))

    if meal_type:
        query = query.filter(Recipe.meal_type == meal_type)
    if category:
        query = query.filter(Recipe.category == category)
    if difficulty:
        query = query.filter(Recipe.difficulty == difficulty)
    if max_prep_time is not None:
        query = query.filter(Recipe.prep_time_minutes <= max_prep_time)
    if diet:
        query = query.filter(Recipe.diets.contains([diet]))

    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Recipe.title.ilike(term),
                Recipe.description.ilike(term),
                cast(Recipe.tags, String).ilike(term),
                cast(Recipe.ingredients, String).ilike(term),
            )
        )

    recipes = query.order_by(Recipe.title.asc()).all()
    items = [_to_summary(recipe, favorite_ids) for recipe in recipes]
    return RecipeListResponse(items=items, total=len(items))


def get_recipe(db: Session, user: User, recipe_id: int) -> RecipeDetail | None:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        return None
    favorite_ids = _favorite_ids(db, user.id)
    return _to_detail(recipe, favorite_ids)


def toggle_favorite(db: Session, user: User, recipe_id: int) -> FavoriteToggleResponse | None:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        return None

    existing = (
        db.query(RecipeFavorite)
        .filter(
            RecipeFavorite.user_id == user.id,
            RecipeFavorite.recipe_id == recipe_id,
        )
        .one_or_none()
    )

    if existing is not None:
        db.delete(existing)
        db.commit()
        return FavoriteToggleResponse(recipe_id=recipe_id, is_favorited=False)

    db.add(RecipeFavorite(user_id=user.id, recipe_id=recipe_id))
    db.commit()
    return FavoriteToggleResponse(recipe_id=recipe_id, is_favorited=True)
