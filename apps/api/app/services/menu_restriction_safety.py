"""Stage C: restriction safety hooks for menu generation."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.recipe import Recipe
from app.models.user import User
from app.nutrition.restriction_safety import (
    explain_recipe_restriction_conflicts,
    filter_recipes_for_profile,
    has_hard_conflicts,
    has_soft_conflicts,
    recipe_is_allowed_for_profile,
)
from app.recipes.gold_filter import query_active_recipes
from app.schemas.menu import MenuDayPlan, MenuMeal, MenuVariant

logger = logging.getLogger(__name__)

MIN_RECIPE_POOL_SIZE = 6


def resolve_menu_profile(db: Session | None, user: User | None) -> Any | None:
    if db is None or user is None:
        return None
    try:
        from app.services.onboarding import get_or_create_profile

        return get_or_create_profile(db, user)
    except Exception:
        logger.warning("menu restriction safety: profile unavailable", exc_info=True)
        return None


def apply_pre_ai_recipe_filter(
    recipes: list[Recipe],
    profile: Any | None,
) -> tuple[list[Recipe], list[str]]:
    """Remove hard-conflict recipes from the candidate pool."""
    if not recipes:
        return [], []
    if profile is None:
        logger.debug(
            "menu pre-AI filter: profile unavailable, keeping pool size %s",
            len(recipes),
        )
        return recipes, []

    before = len(recipes)
    filtered = filter_recipes_for_profile(recipes, profile)
    warnings: list[str] = []

    if len(filtered) < before:
        logger.info(
            "menu pre-AI filter: excluded %s hard-conflict recipes (%s -> %s)",
            before - len(filtered),
            before,
            len(filtered),
        )

    if not filtered:
        warnings.append(
            "Нет рецептов, подходящих под ваши ограничения. "
            "Проверьте профиль питания."
        )
        return [], warnings

    if len(filtered) < MIN_RECIPE_POOL_SIZE:
        warnings.append(
            f"После учёта ограничений осталось мало рецептов "
            f"({len(filtered)} из {before}). Меню может быть неполным."
        )
        logger.warning(
            "menu pre-AI filter: small allowed pool %s (min recommended %s)",
            len(filtered),
            MIN_RECIPE_POOL_SIZE,
        )

    return filtered, warnings


def load_restriction_safe_recipe_pool(
    db: Session,
    profile: Any | None,
) -> list[Recipe]:
    recipes = (
        query_active_recipes(db)
        .options(joinedload(Recipe.ingredient_rows))
        .all()
    )
    filtered, _ = apply_pre_ai_recipe_filter(recipes, profile)
    return filtered


def format_conflict_message(
    conflicts: list,
    *,
    action: str = "excluded",
) -> str:
    hard = [c for c in conflicts if c.severity == "hard"]
    if not hard:
        return ""
    conflict = hard[0]
    if action == "replaced":
        return (
            f"Блюдо заменено: не подходит под ограничение «{conflict.label_ru}»."
        )
    detail = conflict.reason
    if conflict.matched_ingredient:
        detail = f"найден ингредиент «{conflict.matched_ingredient}»"
    return f"Блюдо исключено: ограничение «{conflict.label_ru}», {detail}."


def _find_replacement_recipe(
    pool: list[Recipe],
    meal_type: str,
    used_ids: set[int],
    profile: Any,
) -> Recipe | None:
    for recipe in pool:
        if recipe.id in used_ids:
            continue
        if recipe.meal_type != meal_type:
            continue
        if not recipe_is_allowed_for_profile(recipe, profile):
            continue
        return recipe
    return None


def _recipe_for_meal(
    db: Session | None,
    meal: MenuMeal,
    recipe_by_id: dict[int, Recipe],
) -> Recipe | None:
    if not meal.recipe_id:
        return None
    if meal.recipe_id in recipe_by_id:
        return recipe_by_id[meal.recipe_id]
    if db is None:
        return None
    return db.query(Recipe).filter(Recipe.id == meal.recipe_id).first()


def _sanitize_meal(
    meal: MenuMeal,
    profile: Any,
    *,
    db: Session | None,
    recipe_by_id: dict[int, Recipe],
    replacement_pool: list[Recipe],
    used_ids: set[int],
) -> tuple[MenuMeal | None, list[str]]:
    notes: list[str] = []
    if profile is None:
        return meal, notes

    recipe = _recipe_for_meal(db, meal, recipe_by_id)
    if recipe is None:
        return meal, notes

    conflicts = explain_recipe_restriction_conflicts(recipe, profile)
    if not has_hard_conflicts(conflicts):
        if has_soft_conflicts(conflicts):
            soft = next(c for c in conflicts if c.severity == "soft")
            notes.append(
                "Для части ограничений есть предупреждения, но блюдо не заблокировано: "
                f"«{soft.label_ru}» — {soft.reason}."
            )
        if meal.recipe_id:
            used_ids.add(meal.recipe_id)
        return meal, notes

    replacement = _find_replacement_recipe(
        replacement_pool,
        meal.meal_type,
        used_ids,
        profile,
    )
    if replacement:
        used_ids.add(replacement.id)
        notes.append(format_conflict_message(conflicts, action="replaced"))
        return (
            meal.model_copy(
                update={
                    "name": replacement.title,
                    "description": replacement.description or meal.description,
                    "recipe_id": replacement.id,
                    "prep_time_minutes": (
                        replacement.cooking_time_minutes
                        or replacement.prep_time_minutes
                        or meal.prep_time_minutes
                    ),
                    "calories_estimate": (
                        int(replacement.calories_per_serving)
                        if replacement.calories_per_serving
                        else meal.calories_estimate
                    ),
                }
            ),
            notes,
        )

    notes.append(format_conflict_message(conflicts, action="excluded"))
    return None, notes


def _sanitize_meals_list(
    meals: list[MenuMeal],
    profile: Any | None,
    *,
    db: Session | None,
    recipe_by_id: dict[int, Recipe],
    replacement_pool: list[Recipe],
    used_ids: set[int],
) -> tuple[list[MenuMeal], list[str]]:
    out: list[MenuMeal] = []
    notes: list[str] = []
    for meal in meals:
        sanitized, meal_notes = _sanitize_meal(
            meal,
            profile,
            db=db,
            recipe_by_id=recipe_by_id,
            replacement_pool=replacement_pool,
            used_ids=used_ids,
        )
        notes.extend(meal_notes)
        if sanitized is not None:
            out.append(sanitized)
    return out, notes


def sanitize_menu_variants(
    db: Session | None,
    menus: list[MenuVariant],
    profile: Any | None,
    *,
    replacement_pool: list[Recipe] | None = None,
) -> tuple[list[MenuVariant], list[str]]:
    """Post-AI validation: replace or drop meals with hard restriction conflicts."""
    if not menus:
        return menus, []
    if profile is None:
        logger.debug("menu post-AI validation: profile unavailable, skipping")
        return menus, []

    pool = replacement_pool or []
    if db is not None and not pool:
        pool = load_restriction_safe_recipe_pool(db, profile)

    recipe_by_id = {r.id: r for r in pool}
    all_notes: list[str] = []
    sanitized: list[MenuVariant] = []

    for variant in menus:
        used_ids: set[int] = set()
        meals, meal_notes = _sanitize_meals_list(
            list(variant.meals),
            profile,
            db=db,
            recipe_by_id=recipe_by_id,
            replacement_pool=pool,
            used_ids=used_ids,
        )
        all_notes.extend(meal_notes)

        days_out: list[MenuDayPlan] | None = None
        if variant.days:
            days_out = []
            for day in variant.days:
                day_meals, day_notes = _sanitize_meals_list(
                    list(day.meals),
                    profile,
                    db=db,
                    recipe_by_id=recipe_by_id,
                    replacement_pool=pool,
                    used_ids=used_ids,
                )
                all_notes.extend(day_notes)
                if day_meals:
                    days_out.append(day.model_copy(update={"meals": day_meals}))

        explanation = variant.explanation
        variant_notes = [n for n in meal_notes if n]
        if variant_notes:
            explanation = (explanation + "\n" + "\n".join(variant_notes)).strip()

        if not meals and not days_out:
            logger.warning(
                "menu post-AI validation: variant %s has no meals after sanitization",
                variant.variant,
            )
            all_notes.append(
                f"Вариант «{variant.title}»: не осталось блюд после проверки ограничений."
            )
            continue

        sanitized.append(
            variant.model_copy(
                update={
                    "meals": meals or variant.meals,
                    "days": days_out,
                    "explanation": explanation,
                }
            )
        )

    if len(sanitized) < len(menus):
        all_notes.append(
            "Часть вариантов меню исключена из-за жёстких ограничений питания."
        )

    return sanitized or menus, all_notes


def append_safety_notes_to_menus(
    menus: list[MenuVariant],
    notes: list[str],
) -> list[MenuVariant]:
    if not notes:
        return menus
    suffix = "\n".join(dict.fromkeys(n for n in notes if n))
    return [
        m.model_copy(update={"explanation": (m.explanation + "\n" + suffix).strip()})
        for m in menus
    ]
