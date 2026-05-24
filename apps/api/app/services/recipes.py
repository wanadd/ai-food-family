from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session, joinedload

from app.data.recipe_seed import SEED_RECIPES
from app.models.recipe import Recipe, RecipeFavorite
from app.models.user import User
from app.schemas.menu import MenuIngredient, MenuVariant
from app.schemas.recipe import (
    FavoriteToggleResponse,
    RecipeCreateRequest,
    RecipeDetail,
    RecipeFiltersResponse,
    RecipeIngredient,
    RecipeListResponse,
    RecipeRecommendationItem,
    RecipeRecommendationsResponse,
    RecipeSummary,
    RecipeUpdateRequest,
)
from app.services.app_scope import AppScope
from app.services.onboarding import get_or_create_profile
from app.services.pantry import get_active_items_for_scope
from app.services.recipe_storage import (
    aggregate_ingredients_for_shopping,
    get_allergens,
    get_restrictions,
    get_structured_ingredients,
    get_structured_steps,
    get_tags,
    persist_recipe_structure,
    scale_ingredients,
)
from app.services import shopping_list as shopping_list_service

FILTER_LABELS = {
    "meal_types": [
        {"value": "breakfast", "label": "Завтрак"},
        {"value": "lunch", "label": "Обед"},
        {"value": "dinner", "label": "Ужин"},
        {"value": "snack", "label": "Перекус"},
        {"value": "dessert", "label": "Десерт"},
        {"value": "drink", "label": "Напитки"},
        {"value": "smoothie", "label": "Смузи"},
        {"value": "protein_shake", "label": "Протеиновые"},
        {"value": "tea", "label": "Чай"},
        {"value": "coffee", "label": "Кофе"},
        {"value": "cocktail", "label": "Коктейли"},
    ],
    "drink_modes": [
        {"value": "none", "label": "Не добавлять"},
        {"value": "non_alcoholic", "label": "Только безалкогольные"},
        {"value": "sport", "label": "Спорт / протеин"},
        {"value": "tea_coffee", "label": "Чай / кофе"},
        {"value": "cocktail", "label": "Коктейльная карта"},
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
    if count == 0:
        for item in SEED_RECIPES:
            db.add(Recipe(**item))
        db.commit()
    if db.query(Recipe).count() < 50:
        from app.data.recipe_catalog_seed import CATALOG_RECIPES
        from app.services.recipe_storage import persist_recipe_structure

        for data in CATALOG_RECIPES:
            if db.query(Recipe).filter(Recipe.title == data["title"]).count():
                continue
            recipe = Recipe(
                title=data["title"],
                description=data.get("description", ""),
                meal_type=data["meal_type"],
                category=data.get("category", "main"),
                cooking_time_minutes=data.get("cooking_time_minutes", 30),
                prep_time_minutes=data.get("prep_time_minutes"),
                servings=data.get("servings", 4),
                difficulty=data.get("difficulty", "easy"),
                calories_per_serving=data.get("calories_per_serving"),
                protein_g=data.get("protein_g"),
                is_drink=data.get("is_drink", False),
                is_alcoholic=data.get("is_alcoholic", False),
                suitable_for_children=data.get("suitable_for_children", True),
                suitable_for_sport=data.get("suitable_for_sport", False),
                suitable_for_event=data.get("suitable_for_event", False),
                source_type=data.get("source_type", "import"),
                diets=data.get("diets", []),
                tags=data.get("tags", []),
            )
            db.add(recipe)
            db.flush()
            persist_recipe_structure(
                db,
                recipe,
                ingredients=data["ingredients"],
                steps=data["steps"],
                tags=data.get("tags"),
                allergens=data.get("allergens"),
                restrictions=data.get("restrictions"),
            )
        db.commit()


def _favorite_ids(db: Session, user_id: int) -> set[int]:
    rows = (
        db.query(RecipeFavorite.recipe_id)
        .filter(RecipeFavorite.user_id == user_id)
        .all()
    )
    return {row[0] for row in rows}


def _prep_minutes(recipe: Recipe) -> int:
    return recipe.prep_time_minutes or recipe.cooking_time_minutes or 30


def _to_summary(
    recipe: Recipe,
    favorite_ids: set[int],
    *,
    fit_level: str | None = None,
) -> RecipeSummary:
    return RecipeSummary(
        id=recipe.id,
        title=recipe.title,
        description=recipe.description or "",
        meal_type=recipe.meal_type,
        category=recipe.category,
        prep_time_minutes=_prep_minutes(recipe),
        cooking_time_minutes=recipe.cooking_time_minutes or _prep_minutes(recipe),
        servings=recipe.servings,
        difficulty=recipe.difficulty,
        diets=recipe.diets or [],
        tags=get_tags(recipe),
        is_favorited=recipe.id in favorite_ids,
        is_drink=bool(recipe.is_drink),
        is_alcoholic=bool(recipe.is_alcoholic),
        calories_per_serving=recipe.calories_per_serving,
        protein_g=recipe.protein_g,
        suitable_for_children=recipe.suitable_for_children,
        suitable_for_sport=recipe.suitable_for_sport,
        suitable_for_event=recipe.suitable_for_event,
        fit_level=fit_level,  # type: ignore[arg-type]
    )


def _to_detail(recipe: Recipe, favorite_ids: set[int]) -> RecipeDetail:
    summary = _to_summary(recipe, favorite_ids)
    structured = get_structured_ingredients(recipe)
    return RecipeDetail(
        **summary.model_dump(),
        ingredients=[
            RecipeIngredient(
                name=i["name"],
                amount=i["amount"],
                quantity=i.get("quantity"),
                unit=i.get("unit"),
                category=i.get("category"),
                is_optional=i.get("is_optional", False),
            )
            for i in structured
        ],
        steps=get_structured_steps(recipe),
        allergens=get_allergens(recipe),
        restrictions=get_restrictions(recipe),
        sugar_g=recipe.sugar_g,
        caffeine_mg=recipe.caffeine_mg,
        alcohol_percent=recipe.alcohol_percent,
        cuisine=recipe.cuisine,
        source_type=recipe.source_type or "manual",
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
    )


def get_filters(db: Session) -> RecipeFiltersResponse:
    max_time = (
        db.query(Recipe.cooking_time_minutes)
        .order_by(Recipe.cooking_time_minutes.desc())
        .first()
    )
    return RecipeFiltersResponse(
        meal_types=FILTER_LABELS["meal_types"],
        categories=FILTER_LABELS["categories"],
        diets=FILTER_LABELS["diets"],
        difficulties=FILTER_LABELS["difficulties"],
        max_prep_time=max_time[0] if max_time else 60,
        drink_modes=FILTER_LABELS.get("drink_modes", []),
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
    from_pantry: bool = False,
    for_children: bool = False,
    for_sport: bool = False,
    for_event: bool = False,
    drinks_only: bool = False,
    non_alcoholic: bool = False,
    alcoholic_only: bool = False,
    protein_only: bool = False,
    smoothie_only: bool = False,
    tea_coffee_only: bool = False,
    exclude_allergens: str | None = None,
    goal: str | None = None,
    scope: AppScope | None = None,
) -> RecipeListResponse:
    query = db.query(Recipe).filter(Recipe.is_active.is_(True))
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
        query = query.filter(Recipe.cooking_time_minutes <= max_prep_time)
    if diet:
        query = query.filter(Recipe.diets.contains([diet]))
    if for_children:
        query = query.filter(Recipe.suitable_for_children.is_(True))
    if for_sport:
        query = query.filter(Recipe.suitable_for_sport.is_(True))
    if for_event:
        query = query.filter(Recipe.suitable_for_event.is_(True))
    if drinks_only:
        query = query.filter(Recipe.is_drink.is_(True))
    if non_alcoholic:
        query = query.filter(Recipe.is_alcoholic.is_(False))
    if alcoholic_only:
        query = query.filter(Recipe.is_alcoholic.is_(True))
    if protein_only:
        query = query.filter(Recipe.meal_type == "protein_shake")
    if smoothie_only:
        query = query.filter(Recipe.meal_type == "smoothie")
    if tea_coffee_only:
        query = query.filter(Recipe.meal_type.in_(["tea", "coffee"]))

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

    if from_pantry and scope:
        pantry = {p.name.lower() for p in get_active_items_for_scope(db, scope)}
        recipes = [r for r in recipes if _matches_pantry(r, pantry)]

    if exclude_allergens:
        allergen = exclude_allergens.lower()
        recipes = [
            r
            for r in recipes
            if allergen not in " ".join(get_allergens(r)).lower()
            and allergen not in (r.title + r.description).lower()
        ]

    if goal in ("weight_loss", "sport", "health"):
        if goal == "sport":
            recipes.sort(key=lambda r: (not r.suitable_for_sport, r.title))

    from app.services.recipe_analysis import quick_recipe_fit_level

    items = []
    for recipe in recipes:
        fit = quick_recipe_fit_level(db, user, scope) if scope is not None else None
        items.append(_to_summary(recipe, favorite_ids, fit_level=fit))
    return RecipeListResponse(items=items, total=len(items))


def _matches_pantry(recipe: Recipe, pantry: set[str]) -> bool:
    for ing in get_structured_ingredients(recipe):
        name = ing["name"].lower()
        if any(p in name or name in p for p in pantry):
            return True
    return False


def get_recipe_model(db: Session, recipe_id: int) -> Recipe | None:
    return (
        db.query(Recipe)
        .options(
            joinedload(Recipe.ingredient_rows),
            joinedload(Recipe.step_rows),
            joinedload(Recipe.tag_rows),
            joinedload(Recipe.allergen_rows),
            joinedload(Recipe.restriction_rows),
        )
        .filter(Recipe.id == recipe_id)
        .one_or_none()
    )


def get_recipe(db: Session, user: User, recipe_id: int) -> RecipeDetail | None:
    recipe = get_recipe_model(db, recipe_id)
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


def create_recipe(db: Session, payload: RecipeCreateRequest) -> RecipeDetail:
    recipe = Recipe(
        title=payload.title,
        description=payload.description,
        meal_type=payload.meal_type,
        category=payload.category,
        cooking_time_minutes=payload.cooking_time_minutes,
        prep_time_minutes=payload.cooking_time_minutes,
        servings=payload.servings,
        difficulty=payload.difficulty,
        is_drink=payload.is_drink,
        is_alcoholic=payload.is_alcoholic,
        source_type=payload.source_type,
    )
    db.add(recipe)
    db.flush()
    ings = [i.model_dump() for i in payload.ingredients]
    persist_recipe_structure(
        db,
        recipe,
        ingredients=ings,
        steps=payload.steps,
        tags=payload.tags,
        allergens=payload.allergens,
        restrictions=payload.restrictions,
    )
    db.commit()
    db.refresh(recipe)
    return _to_detail(recipe, set())


def update_recipe(
    db: Session, recipe_id: int, payload: RecipeUpdateRequest
) -> RecipeDetail | None:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        return None
    if payload.title is not None:
        recipe.title = payload.title
    if payload.description is not None:
        recipe.description = payload.description
    if payload.is_active is not None:
        recipe.is_active = payload.is_active
    db.commit()
    db.refresh(recipe)
    return _to_detail(recipe, set())


def get_recommendations(
    db: Session, user: User, scope: AppScope, *, limit: int = 10
) -> RecipeRecommendationsResponse:
    profile = get_or_create_profile(db, user)
    recipes = (
        db.query(Recipe)
        .filter(Recipe.is_active.is_(True), Recipe.is_alcoholic.is_(False))
        .limit(80)
        .all()
    )
    goal = profile.goal or "healthy"
    items: list[RecipeRecommendationItem] = []
    for recipe in recipes:
        score = 0.5
        reason = "Подходит по каталогу"
        if goal in ("sport", "mass", "cut") and recipe.suitable_for_sport:
            score += 0.3
            reason = "Подходит для спортивной цели"
        if recipe.meal_type == "protein_shake" and goal in ("sport", "mass"):
            score += 0.2
            reason = "Протеиновый напиток для вашей цели"
        items.append(
            RecipeRecommendationItem(
                id=recipe.id,
                title=recipe.title,
                meal_type=recipe.meal_type,
                score=score,
                reason=reason,
            )
        )
    items.sort(key=lambda x: x.score, reverse=True)
    return RecipeRecommendationsResponse(items=items[:limit])


def add_recipe_to_shopping(
    db: Session,
    user: User,
    scope: AppScope,
    recipe: Recipe,
    *,
    servings: int | None = None,
) -> None:
    target = servings or recipe.servings or 4
    scaled = scale_ingredients(recipe, target)
    aggregated = aggregate_ingredients_for_shopping(scaled)
    ingredients = [
        MenuIngredient(
            name=i["name"], amount=i["amount"], category=i.get("category")
        )
        for i in aggregated
    ]
    menu = MenuVariant(
        variant="balanced",
        title=recipe.title,
        explanation="Ингредиенты из рецепта",
        total_prep_minutes=recipe.cooking_time_minutes or 30,
        meals=[],
        ingredients=ingredients,
    )
    shopping_list_service.sync_from_menu(db, scope, menu, None)
