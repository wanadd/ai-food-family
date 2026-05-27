"""Catalog operations: list / get / filters / seed.

Behaviour preserved from the legacy ``app.services.recipes`` module —
this module is a structural refactor, not a functional change.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.data.recipe_seed import SEED_RECIPES
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.recipe import (
    RecipeDetail,
    RecipeFiltersResponse,
    RecipeListResponse,
)
from app.services.app_scope import AppScope
from app.services.pantry import get_active_items_for_scope
from app.services.recipe_storage import (
    get_allergens,
    get_structured_ingredients,
)
from . import repository
from app.services.recipes.mapper import to_detail, to_summary
from app.services.recipes.types import RecipeListFilters

FILTER_LABELS: dict[str, list[dict[str, str]]] = {
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
    """Populate the recipes table on first boot if it is empty."""

    count = repository.count_recipes(db)
    if count == 0:
        for item in SEED_RECIPES:
            db.add(Recipe(**item))
        db.commit()
    if repository.count_recipes(db) < 50:
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


def get_filters(db: Session) -> RecipeFiltersResponse:
    max_time = repository.get_max_cooking_time(db)
    return RecipeFiltersResponse(
        meal_types=FILTER_LABELS["meal_types"],
        categories=FILTER_LABELS["categories"],
        diets=FILTER_LABELS["diets"],
        difficulties=FILTER_LABELS["difficulties"],
        max_prep_time=max_time if max_time is not None else 60,
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
    favorite_ids = repository.favorite_ids_for_user(db, user.id)

    filters = RecipeListFilters(
        q=q,
        meal_type=meal_type or None,
        category=category or None,
        diet=diet or None,
        difficulty=difficulty or None,
        max_prep_time=max_prep_time,
        favorites_only=favorites_only,
        favorite_ids=frozenset(favorite_ids),
        for_children=for_children,
        for_sport=for_sport,
        for_event=for_event,
        drinks_only=drinks_only,
        non_alcoholic=non_alcoholic,
        alcoholic_only=alcoholic_only,
        protein_only=protein_only,
        smoothie_only=smoothie_only,
        tea_coffee_only=tea_coffee_only,
    )

    recipes = repository.query_recipes(db, filters)

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
        items.append(to_summary(recipe, favorite_ids, fit_level=fit))
    return RecipeListResponse(items=items, total=len(items))


def _matches_pantry(recipe: Recipe, pantry: set[str]) -> bool:
    for ing in get_structured_ingredients(recipe):
        name = ing["name"].lower()
        if any(p in name or name in p for p in pantry):
            return True
    return False


def get_recipe_model(db: Session, recipe_id: int) -> Recipe | None:
    return repository.get_recipe_with_relations(db, recipe_id)


def get_recipe(db: Session, user: User, recipe_id: int) -> RecipeDetail | None:
    recipe = repository.get_recipe_with_relations(db, recipe_id)
    if recipe is None:
        return None
    favorite_ids = repository.favorite_ids_for_user(db, user.id)
    return to_detail(recipe, favorite_ids)
