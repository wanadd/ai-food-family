"""Add recipes to the selected menu plan by date and meal slot."""

from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.menu import (
    MenuDayPlan,
    MenuIngredient,
    MenuMeal,
    MenuVariant,
    SelectMenuRequest,
)
from app.services.app_scope import AppScope
from app.services.menu_days import day_label
from app.services.menu_selection import get_selected_menu
from app.services.recipe_storage import get_structured_ingredients
from app.services.recipe_storage import aggregate_ingredients_for_shopping, scale_ingredients
from app.services.recipes.mapper import public_title
from app.services.recipes.title_normalize import catalog_meal_type

logger = logging.getLogger(__name__)

MEAL_SLOT_ORDER = ("breakfast", "lunch", "dinner", "snack")
PLACEHOLDER_NAME = "Свободно"
DEFAULT_SERVINGS = 2


def parse_plan_date(value: str) -> date:
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError("date must be YYYY-MM-DD") from exc


def make_slot_id(date_iso: str, meal_type: str) -> str:
    return f"{date_iso}:{meal_type}"


def empty_slot(meal_type: str, date_iso: str) -> MenuMeal:
    return MenuMeal(
        meal_type=meal_type,  # type: ignore[arg-type]
        name=PLACEHOLDER_NAME,
        description="",
        prep_time_minutes=0,
        slot_id=make_slot_id(date_iso, meal_type),
        recipe_id=None,
        servings=None,
    )


def default_day(day_date: date, day_index: int) -> MenuDayPlan:
    date_iso = day_date.isoformat()
    return MenuDayPlan(
        day_index=day_index,
        label=day_label(day_index, day_date),
        date_iso=date_iso,
        meals=[empty_slot(mt, date_iso) for mt in MEAL_SLOT_ORDER],
    )


def create_scaffold_menu(target_date: date) -> MenuVariant:
    days = [
        default_day(target_date + timedelta(days=offset), offset + 1)
        for offset in range(7)
    ]
    first = days[0]
    return MenuVariant(
        variant="balanced",
        title="Мой план",
        tagline="",
        explanation="План питания",
        total_prep_minutes=0,
        meals=list(first.meals),
        ingredients=[MenuIngredient(name="По плану", amount="—")],
        plan_days=7,
        days=days,
    )


def _normalize_meal_type(meal_type: str) -> str:
    normalized = catalog_meal_type(meal_type.strip().lower())
    if normalized not in MEAL_SLOT_ORDER:
        raise ValueError(f"meal_type must be one of: {', '.join(MEAL_SLOT_ORDER)}")
    return normalized


def parse_slot_id(slot_id: str) -> tuple[str, str]:
    """Return (date_iso, meal_type) from slot id like 2026-06-05:dinner."""
    normalized = slot_id.strip()
    if ":" not in normalized:
        raise ValueError("Invalid menu item id")
    date_iso, meal_type = normalized.split(":", 1)
    parse_plan_date(date_iso)
    meal_type_norm = _normalize_meal_type(meal_type)
    return date_iso, meal_type_norm


def _ensure_day(menu: MenuVariant, target_date: date) -> tuple[MenuVariant, MenuDayPlan]:
    date_iso = target_date.isoformat()
    days = list(menu.days or [])
    if not days:
        day = default_day(target_date, 1)
        menu = menu.model_copy(update={"days": [day], "plan_days": 1, "meals": list(day.meals)})
        return menu, day

    for day in days:
        if day.date_iso == date_iso:
            return menu, day

    next_index = max(day.day_index for day in days) + 1
    day = default_day(target_date, next_index)
    days.append(day)
    menu = menu.model_copy(update={"days": days, "plan_days": len(days)})
    return menu, day


def _slots_for_day(day: MenuDayPlan, date_iso: str) -> list[MenuMeal]:
    meals = list(day.meals)
    known = {meal.slot_id for meal in meals if meal.slot_id}
    for meal_type in MEAL_SLOT_ORDER:
        sid = make_slot_id(date_iso, meal_type)
        if sid not in known:
            meals.append(empty_slot(meal_type, date_iso))
    return meals


def recipe_to_menu_meal(
    recipe: Recipe,
    *,
    meal_type: str,
    date_iso: str,
    servings: int,
) -> MenuMeal:
    prep = recipe.prep_time_minutes or recipe.cooking_time_minutes or 30
    calories = (
        int(recipe.calories_per_serving)
        if recipe.calories_per_serving is not None
        else None
    )
    return MenuMeal(
        meal_type=meal_type,  # type: ignore[arg-type]
        name=public_title(recipe),
        description=(recipe.description or "")[:500],
        prep_time_minutes=prep,
        calories_estimate=calories,
        recipe_id=recipe.id,
        servings=servings,
        slot_id=make_slot_id(date_iso, meal_type),
    )


def _merge_ingredients(menu: MenuVariant, recipe: Recipe, servings: int) -> list[MenuIngredient]:
    merged = list(menu.ingredients)
    existing = {ing.name.lower() for ing in merged}
    scale = servings / max(recipe.servings or DEFAULT_SERVINGS, 1)
    for raw in get_structured_ingredients(recipe):
        name = str(raw.get("name", "")).strip()
        amount = str(raw.get("amount", "")).strip()
        if not name or not amount:
            continue
        if scale != 1 and amount:
            amount = f"{amount} ×{scale:.1f}".rstrip("0").rstrip(".")
        if name.lower() not in existing:
            merged.append(MenuIngredient(name=name, amount=amount))
            existing.add(name.lower())
    if not merged:
        merged = [MenuIngredient(name="По плану", amount="—")]
    return merged


def _active_recipe_servings(menu: MenuVariant) -> dict[int, int]:
    """Collect current active recipe ids from menu slots.

    The selected menu's ingredient aggregate is derived from active slots only;
    stale `menu.ingredients` must not be treated as source of truth after
    replace/delete/add operations.
    """
    recipe_servings: dict[int, int] = {}
    source_days = list(menu.days or [])
    meal_groups = [day.meals for day in source_days] if source_days else [menu.meals]
    for meals in meal_groups:
        for meal in meals:
            if meal.recipe_id is None:
                continue
            if not meal.name.strip() or meal.name == PLACEHOLDER_NAME:
                continue
            servings = meal.servings or DEFAULT_SERVINGS
            recipe_servings[int(meal.recipe_id)] = recipe_servings.get(
                int(meal.recipe_id), 0
            ) + int(max(servings, 1))
    return recipe_servings


def recompute_menu_ingredients_from_active_meals(
    db: Session,
    menu: MenuVariant,
    *,
    preserve_existing_if_no_active: bool = False,
) -> MenuVariant:
    """Return menu with fresh ingredients rebuilt from active recipe slots."""
    recipe_servings = _active_recipe_servings(menu)
    if not recipe_servings:
        if preserve_existing_if_no_active:
            return menu
        return menu.model_copy(update={"ingredients": []})

    scaled: list[dict] = []
    for recipe_id, servings in recipe_servings.items():
        recipe = db.get(Recipe, recipe_id)
        if recipe is None:
            continue
        recipe_servings_base = getattr(recipe, "servings", None)
        if not isinstance(recipe_servings_base, (int, float)):
            continue
        scaled.extend(scale_ingredients(recipe, max(servings, 1)))

    ingredients = [
        MenuIngredient(**item) for item in aggregate_ingredients_for_shopping(scaled)
    ]
    return menu.model_copy(update={"ingredients": ingredients})


def _sync_flat_meals(menu: MenuVariant, target_date: date) -> list[MenuMeal]:
    date_iso = target_date.isoformat()
    if menu.days:
        for day in menu.days:
            if day.date_iso == date_iso:
                return list(day.meals)
        return list(menu.days[0].meals)
    return list(menu.meals)


def menu_item_dict(meal: MenuMeal, date_iso: str) -> dict:
    return {
        "slot_id": meal.slot_id or make_slot_id(date_iso, meal.meal_type),
        "date": date_iso,
        "meal_type": meal.meal_type,
        "recipe_id": meal.recipe_id,
        "name": meal.name,
        "servings": meal.servings or DEFAULT_SERVINGS,
        "prep_time_minutes": meal.prep_time_minutes,
        "calories_estimate": meal.calories_estimate,
    }


def add_recipe_to_plan(
    db: Session,
    user: User,
    scope: AppScope,
    recipe: Recipe,
    *,
    plan_date: str,
    meal_type: str,
    servings: int | None = None,
) -> tuple[dict, MenuVariant, bool]:
    """Return (item_dict, updated_menu, created_new_assignment)."""
    target = parse_plan_date(plan_date)
    meal_type_norm = _normalize_meal_type(meal_type)
    date_iso = target.isoformat()
    slot = make_slot_id(date_iso, meal_type_norm)
    target_servings = servings or recipe.servings or DEFAULT_SERVINGS

    selected = get_selected_menu(db, scope)
    menu = selected.menu if selected is not None else create_scaffold_menu(target)
    menu, day = _ensure_day(menu, target)
    meals = _slots_for_day(day, date_iso)

    created = True
    new_meal = recipe_to_menu_meal(
        recipe,
        meal_type=meal_type_norm,
        date_iso=date_iso,
        servings=target_servings,
    )

    replaced = False
    for index, meal in enumerate(meals):
        meal_slot = meal.slot_id or make_slot_id(date_iso, meal.meal_type)
        if meal_slot != slot and meal.meal_type != meal_type_norm:
            continue
        if (
            meal.recipe_id == recipe.id
            and meal.name != PLACEHOLDER_NAME
            and meal.recipe_id is not None
        ):
            created = False
            new_meal = meal
            break
        meals[index] = new_meal
        replaced = True
        break

    if not replaced:
        meals.append(new_meal)

    updated_days = [
        day_plan.model_copy(update={"meals": meals})
        if day_plan.date_iso == date_iso
        else day_plan
        for day_plan in (menu.days or [])
    ]
    updated = menu.model_copy(
        update={
            "days": updated_days,
            "meals": _sync_flat_meals(
                menu.model_copy(update={"days": updated_days}), target
            ),
            "total_prep_minutes": sum(m.prep_time_minutes for m in meals),
        }
    )
    updated = recompute_menu_ingredients_from_active_meals(db, updated)

    from app.services.menu import select_menu

    select_menu(db, user, scope, SelectMenuRequest(menu=updated))
    logger.info(
        "menu.add_recipe user=%s date=%s meal_type=%s recipe_id=%s created=%s",
        user.id,
        date_iso,
        meal_type_norm,
        recipe.id,
        created,
    )
    return menu_item_dict(new_meal, date_iso), updated, created


def get_plan_for_date(
    db: Session,
    scope: AppScope,
    *,
    plan_date: str,
) -> tuple[str, list[dict], MenuVariant | None]:
    target = parse_plan_date(plan_date)
    date_iso = target.isoformat()
    selected = get_selected_menu(db, scope)
    if selected is None:
        return date_iso, [], None

    menu = selected.menu
    if not menu.days:
        items = [
            menu_item_dict(meal, date_iso)
            for meal in menu.meals
            if meal.recipe_id is not None and meal.name != PLACEHOLDER_NAME
        ]
        return date_iso, items, menu

    day = next((d for d in menu.days if d.date_iso == date_iso), None)
    if day is None:
        return date_iso, [], menu

    items = [
        menu_item_dict(meal, date_iso)
        for meal in day.meals
        if meal.recipe_id is not None and meal.name != PLACEHOLDER_NAME
    ]
    return date_iso, items, menu


def remove_menu_item(
    db: Session,
    user: User,
    scope: AppScope,
    slot_id: str,
) -> MenuVariant:
    if ":" not in slot_id:
        raise ValueError("Invalid menu item id")

    date_iso, meal_type = slot_id.split(":", 1)
    meal_type_norm = _normalize_meal_type(meal_type)
    selected = get_selected_menu(db, scope)
    if selected is None:
        raise ValueError("Меню не найдено")

    menu = selected.menu
    if not menu.days:
        raise ValueError("Блюдо не найдено в плане")

    day = next((d for d in menu.days if d.date_iso == date_iso), None)
    if day is None:
        raise ValueError("Блюдо не найдено в плане")

    meals = list(day.meals)
    found = False
    for index, meal in enumerate(meals):
        current_slot = meal.slot_id or make_slot_id(date_iso, meal.meal_type)
        if current_slot != slot_id and meal.meal_type != meal_type_norm:
            continue
        meals[index] = empty_slot(meal_type_norm, date_iso)
        found = True
        break

    if not found:
        raise ValueError("Блюдо не найдено в плане")

    target = parse_plan_date(date_iso)
    updated_days = [
        day_plan.model_copy(update={"meals": meals})
        if day_plan.date_iso == date_iso
        else day_plan
        for day_plan in menu.days
    ]
    updated = menu.model_copy(
        update={
            "days": updated_days,
            "meals": _sync_flat_meals(
                menu.model_copy(update={"days": updated_days}), target
            ),
        }
    )
    updated = recompute_menu_ingredients_from_active_meals(db, updated)

    from app.services.menu import select_menu

    select_menu(db, user, scope, SelectMenuRequest(menu=updated))
    return updated


def replace_recipe_in_slot(
    db: Session,
    user: User,
    scope: AppScope,
    recipe: Recipe,
    *,
    slot_id: str,
    servings: int | None = None,
) -> tuple[dict, MenuVariant]:
    """Replace (or fill) a meal slot with the given recipe."""
    date_iso, meal_type_norm = parse_slot_id(slot_id)
    target = parse_plan_date(date_iso)
    slot = make_slot_id(date_iso, meal_type_norm)
    target_servings = servings or recipe.servings or DEFAULT_SERVINGS

    selected = get_selected_menu(db, scope)
    menu = selected.menu if selected is not None else create_scaffold_menu(target)
    menu, day = _ensure_day(menu, target)
    meals = _slots_for_day(day, date_iso)

    new_meal = recipe_to_menu_meal(
        recipe,
        meal_type=meal_type_norm,
        date_iso=date_iso,
        servings=target_servings,
    )

    replaced = False
    for index, meal in enumerate(meals):
        meal_slot = meal.slot_id or make_slot_id(date_iso, meal.meal_type)
        if meal_slot != slot and meal.meal_type != meal_type_norm:
            continue
        meals[index] = new_meal
        replaced = True
        break

    if not replaced:
        meals.append(new_meal)

    updated_days = [
        day_plan.model_copy(update={"meals": meals})
        if day_plan.date_iso == date_iso
        else day_plan
        for day_plan in (menu.days or [])
    ]
    updated = menu.model_copy(
        update={
            "days": updated_days,
            "meals": _sync_flat_meals(
                menu.model_copy(update={"days": updated_days}), target
            ),
            "total_prep_minutes": sum(m.prep_time_minutes for m in meals),
        }
    )
    updated = recompute_menu_ingredients_from_active_meals(db, updated)

    from app.services.menu import select_menu

    select_menu(db, user, scope, SelectMenuRequest(menu=updated))
    logger.info(
        "menu.replace_slot user=%s slot=%s recipe_id=%s",
        user.id,
        slot,
        recipe.id,
    )
    return menu_item_dict(new_meal, date_iso), updated
