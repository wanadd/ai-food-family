"""SQLAlchemy access layer for recipes.

Contract for this module:

  - Pure DB access. No domain logic, no Pydantic DTOs.
  - Functions return ORM objects, raw collections, or counts.
  - Filtering on computed predicates (pantry match, allergen string scan)
    happens **above** this layer — see ``catalog.list_recipes``.

This split allows higher layers (catalog, search, recommendations) to be
swapped or augmented without rewriting query logic, and is a precondition
for the FTS migration planned in ``docs/RECIPE_ENGINE_V1.md`` § 2.4.
"""

from __future__ import annotations

from sqlalchemy import exists, or_
from sqlalchemy.orm import Session, joinedload

from app.models.recipe import Recipe, RecipeFavorite, RecipeIngredientRow
from app.recipes.gold_filter import apply_gold_recipe_filter
from app.services.recipes.types import RecipeListFilters


def count_recipes(db: Session) -> int:
    return db.query(Recipe).count()


def get_recipe_by_id(db: Session, recipe_id: int) -> Recipe | None:
    return db.get(Recipe, recipe_id)


def get_recipe_with_relations(db: Session, recipe_id: int) -> Recipe | None:
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


def favorite_ids_for_user(db: Session, user_id: int) -> set[int]:
    rows = (
        db.query(RecipeFavorite.recipe_id)
        .filter(RecipeFavorite.user_id == user_id)
        .all()
    )
    return {row[0] for row in rows}


def find_favorite(
    db: Session, user_id: int, recipe_id: int
) -> RecipeFavorite | None:
    return (
        db.query(RecipeFavorite)
        .filter(
            RecipeFavorite.user_id == user_id,
            RecipeFavorite.recipe_id == recipe_id,
        )
        .one_or_none()
    )


def get_max_cooking_time(db: Session, *, include_legacy: bool = False) -> int | None:
    query = apply_gold_recipe_filter(
        db.query(Recipe).filter(Recipe.is_active.is_(True)),
        include_legacy=include_legacy,
    )
    row = query.order_by(Recipe.cooking_time_minutes.desc()).first()
    return row.cooking_time_minutes if row else None


def query_recipes(db: Session, filters: RecipeListFilters) -> list[Recipe]:
    """Apply scalar filters and return the matching active recipes.

    Result is fetched without a fixed public order — ``catalog_sort`` applies
    the quality-first default in ``catalog.list_recipes``.
    """

    query = db.query(Recipe).filter(Recipe.is_active.is_(True))
    query = apply_gold_recipe_filter(query, include_legacy=filters.include_legacy)

    if filters.favorites_only:
        if not filters.favorite_ids:
            return []
        query = query.filter(Recipe.id.in_(filters.favorite_ids))
    if filters.meal_type:
        query = query.filter(Recipe.meal_type == filters.meal_type)
    if filters.category:
        query = query.filter(Recipe.category == filters.category)
    if filters.difficulty:
        query = query.filter(Recipe.difficulty == filters.difficulty)
    if filters.max_prep_time is not None:
        query = query.filter(Recipe.cooking_time_minutes <= filters.max_prep_time)
    if filters.diet:
        query = query.filter(Recipe.diets.contains([filters.diet]))
    if filters.for_children:
        query = query.filter(Recipe.suitable_for_children.is_(True))
    if filters.for_sport:
        query = query.filter(Recipe.suitable_for_sport.is_(True))
    if filters.for_event:
        query = query.filter(Recipe.suitable_for_event.is_(True))
    if filters.drinks_only:
        query = query.filter(Recipe.is_drink.is_(True))
    if filters.non_alcoholic:
        query = query.filter(Recipe.is_alcoholic.is_(False))
    if filters.alcoholic_only:
        query = query.filter(Recipe.is_alcoholic.is_(True))
    if filters.protein_only:
        query = query.filter(Recipe.meal_type == "protein_shake")
    if filters.smoothie_only:
        query = query.filter(Recipe.meal_type == "smoothie")
    if filters.tea_coffee_only:
        query = query.filter(Recipe.meal_type.in_(["tea", "coffee"]))

    if filters.q:
        term = f"%{filters.q.strip()}%"
        ingredient_match = exists().where(
            RecipeIngredientRow.recipe_id == Recipe.id,
            RecipeIngredientRow.name.ilike(term),
        )
        query = query.filter(
            or_(
                Recipe.title.ilike(term),
                Recipe.original_title.ilike(term),
                Recipe.normalized_title.ilike(term),
                Recipe.description.ilike(term),
                ingredient_match,
            )
        )

    return query.order_by(Recipe.id.desc()).all()
