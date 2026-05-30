"""Heuristic menu generation and OpenAI dish replace (legacy helpers)."""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.menu import MenuIngredient, MenuMeal, MenuVariant
from app.services.menu_context import MenuGenerationContext
from app.services.menu_labels import VARIANT_META
from app.services.ai import generate_menu_ai
from app.services.ai_errors import AiError, AiUnavailableError

logger = logging.getLogger(__name__)


async def generate_menus(context: MenuGenerationContext) -> tuple[list[MenuVariant], bool]:
    try:
        result = await generate_menu_ai(context)
        return _apply_leftovers(result.menus, context.leftovers), True
    except AiUnavailableError:
        pass
    except AiError:
        logger.exception("OpenAI menu failed in legacy path")
    except Exception:
        logger.exception("OpenAI menu failed in legacy path")

    menus = _generate_fallback(context)
    return _apply_leftovers(menus, context.leftovers), False


async def replace_meal(
    context: MenuGenerationContext,
    menu: MenuVariant,
    meal_index: int,
    hint: str | None,
    *,
    db=None,
    user=None,
    scope=None,
) -> MenuVariant:
    if meal_index < 0 or meal_index >= len(menu.meals):
        raise ValueError("Invalid meal index")

    from app.config import settings
    from app.services import ai_client

    if ai_client.is_ai_configured() and db and user and scope:
        try:
            from app.services.ai_context import build_ai_user_context

            ai_ctx = build_ai_user_context(db, user, scope, menu_ctx=context)
            meal = menu.meals[meal_index]
            hint_text = f" Пожелание: {hint}." if hint else ""
            prompt = (
                f"{context.prompt_text}\n\n"
                f"Замени одно блюдо в меню «{menu.title}».\n"
                f"Блюдо ({meal.meal_type}): {meal.name} — {meal.description}.{hint_text}\n"
                'JSON: {"meal": {...}, "ingredients": [...]}'
            )
            data = await ai_client.chat_json(
                system="Ты повар ПланАм. Только JSON. Каждый ингредиент отдельной строкой.",
                user=prompt,
            )
            from app.services.menu_ai_parsing import parse_replace_meal_response

            parsed_meal = parse_replace_meal_response(data, fallback_meal=meal)
            if parsed_meal is None:
                logger.warning(
                    "OpenAI dish replace returned unrecognized format; using fallback"
                )
            else:
                updated = menu.model_copy(deep=True)
                updated.meals[meal_index] = parsed_meal
                from app.services.ai import _ingredients_from_ai_rows

                new_ingredients = _ingredients_from_ai_rows(
                    data.get("ingredients", [])
                )
                if new_ingredients:
                    updated.ingredients = new_ingredients
                updated.total_prep_minutes = sum(
                    m.prep_time_minutes for m in updated.meals
                )
                return _apply_leftovers([updated], context.leftovers)[0]
        except Exception:
            logger.exception("OpenAI dish replace failed")

    return _replace_fallback(menu, meal_index, hint)


def _apply_leftovers(menus: list[MenuVariant], leftovers: list) -> list[MenuVariant]:
    if not leftovers:
        return menus

    from app.services.pantry import leftovers_to_ingredients

    leftover_ingredients = leftovers_to_ingredients(leftovers)
    names = ", ".join(item.name for item in leftovers)
    urgency = leftovers[0].name if len(leftovers) == 1 else f"{len(leftovers)} продуктов"

    updated: list[MenuVariant] = []
    for menu in menus:
        copy = menu.model_copy(deep=True)
        copy.explanation = (
            f"{copy.explanation} Используем остатки: {names} "
            f"(в приоритете — {urgency} с ближайшим сроком)."
        )
        existing_names = {ing.name.lower() for ing in copy.ingredients}
        for ing in leftover_ingredients:
            if ing.name.lower() not in existing_names:
                copy.ingredients.insert(0, ing)
                existing_names.add(ing.name.lower())
        updated.append(copy)
    return updated


def _generate_fallback(context: MenuGenerationContext) -> list[MenuVariant]:
    if context.scope_mode == "family" and context.family_name:
        family_note = (
            f"для семьи «{context.family_name}» ({context.members_count} чел.)"
        )
    else:
        family_note = "для личного профиля"
    templates = {
        "quick": {
            "meals": [
                ("breakfast", "Йогурт с ягодами и гранолой", "Готовится за 5 минут", 5),
                ("lunch", "Куриные котлеты с гречкой", "Котлеты из фарша, гречка в пакете", 25),
                ("dinner", "Омлет с овощами", "Быстрый ужин на сковороде", 15),
            ],
            "ingredients": [
                ("Йогурт натуральный", "4 порции", "молочное"),
                ("Ягоды замороженные", "300 г", "фрукты"),
                ("Гранола", "150 г", "крупы"),
                ("Фарш куриный", "600 г", "мясо"),
                ("Гречка", "300 г", "крупы"),
                ("Яйца", "6 шт", "яйца"),
                ("Перец сладкий", "200 г", "овощи"),
                ("Помидоры", "200 г", "овощи"),
            ],
            "explanation": (
                f"Быстрое меню {family_note}: минимум активного времени у плиты."
            ),
            "cost": "до 500 ₽",
            "minutes": 45,
        },
        "economy": {
            "meals": [
                ("breakfast", "Каша овсяная с яблоком", "Сытный недорогой завтрак", 10),
                ("lunch", "Суп с чечевицей и хлебом", "Питательно и экономно", 35),
                ("dinner", "Макароны с тушёными овощами", "Бюджетный ужин", 20),
            ],
            "ingredients": [
                ("Овсяные хлопья", "400 г", "крупы"),
                ("Яблоки", "3 шт", "фрукты"),
                ("Чечевица", "300 г", "бобовые"),
                ("Морковь", "250 г", "овощи"),
                ("Лук репчатый", "150 г", "овощи"),
                ("Макароны", "400 г", "крупы"),
                ("Томатная паста", "2 ст.л.", "соусы"),
            ],
            "explanation": f"Экономное меню {family_note}.",
            "cost": "350–500 ₽",
            "minutes": 65,
        },
        "balanced": {
            "meals": [
                ("breakfast", "Творожная запеканка", "Белок и кальций", 30),
                ("lunch", "Запечённая рыба с овощами", "Омега-3", 40),
                ("dinner", "Салат с киноа и индейкой", "Сбалансированный ужин", 25),
                ("snack", "Фрукты и горсть орехов", "Перекус", 0),
            ],
            "ingredients": [
                ("Творог", "500 г", "молочное"),
                ("Яйца", "3 шт", "яйца"),
                ("Филе белой рыбы", "500 г", "рыба"),
                ("Брокколи", "300 г", "овощи"),
                ("Цукини", "300 г", "овощи"),
                ("Киноа", "200 г", "крупы"),
                ("Филе индейки", "400 г", "мясо"),
                ("Яблоки", "2 шт", "фрукты"),
                ("Бананы", "2 шт", "фрукты"),
            ],
            "explanation": f"Сбалансированное меню {family_note}.",
            "cost": "600–800 ₽",
            "minutes": 95,
        },
    }

    menus: list[MenuVariant] = []
    for variant_key in ("quick", "economy", "balanced"):
        template = templates[variant_key]
        meta = VARIANT_META[variant_key]
        menus.append(
            MenuVariant(
                variant=variant_key,  # type: ignore[arg-type]
                title=meta["title"],
                tagline=meta["tagline"],
                explanation=template["explanation"],
                estimated_daily_cost=template["cost"],
                total_prep_minutes=template["minutes"],
                meals=[
                    MenuMeal(
                        meal_type=meal_type,  # type: ignore[arg-type]
                        name=name,
                        description=desc,
                        prep_time_minutes=minutes,
                    )
                    for meal_type, name, desc, minutes in template["meals"]
                ],
                ingredients=[
                    MenuIngredient(name=n, amount=a, category=c)
                    for n, a, c in template["ingredients"]
                ],
            )
        )
    return menus


def _replace_fallback(
    menu: MenuVariant, meal_index: int, hint: str | None
) -> MenuVariant:
    alternatives = {
        "breakfast": ("Тост с авокадо и яйцом", "Питательный завтрак за 10 минут", 10),
        "lunch": ("Рис с овощами и тофу", "Лёгкий обед без мяса", 25),
        "dinner": ("Тушёная индейка с рисом", "Сытный ужин", 35),
        "snack": ("Смузи из банана и кефира", "Быстрый перекус", 5),
    }
    meal = menu.meals[meal_index]
    alt = alternatives.get(meal.meal_type, ("Суп-пюре из овощей", "Универсальная замена", 20))
    updated = menu.model_copy(deep=True)
    updated.meals[meal_index] = MenuMeal(
        meal_type=meal.meal_type,
        name=alt[0],
        description=alt[1] + (f" ({hint})" if hint else ""),
        prep_time_minutes=alt[2],
    )
    updated.total_prep_minutes = sum(m.prep_time_minutes for m in updated.meals)
    if hint:
        updated.explanation = f"{menu.explanation} Блюдо заменено: {hint}."
    return updated
