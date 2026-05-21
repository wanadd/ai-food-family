import json
import logging
from typing import Any

import httpx

from app.config import settings
from app.schemas.menu import MenuIngredient, MenuMeal, MenuVariant, MenuVariantType
from app.services.menu_context import MenuGenerationContext
from app.services.menu_labels import VARIANT_META

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — нутрициолог и семейный повар для приложения AI Food Family.
Отвечай ТОЛЬКО валидным JSON без markdown.
Учитывай всех членов семьи, их цели, диеты, аллергии, ограничения, бюджет и время готовки.
Если указаны остатки в холодильнике — строй блюда вокруг них, сокращай список покупок.
Не включай продукты из списка аллергий и запретов.
Меню на один день: завтрак, обед, ужин (можно лёгкий перекус).
Все тексты на русском."""

async def generate_menus(context: MenuGenerationContext) -> tuple[list[MenuVariant], bool]:
    if settings.openai_api_key:
        try:
            menus = await _generate_with_openai(context)
            return menus, True
        except Exception:
            logger.exception("OpenAI menu generation failed, using fallback")

    menus = _generate_fallback(context)
    return _apply_leftovers(menus, context.leftovers), False


async def replace_meal(
    context: MenuGenerationContext,
    menu: MenuVariant,
    meal_index: int,
    hint: str | None,
) -> MenuVariant:
    if meal_index < 0 or meal_index >= len(menu.meals):
        raise ValueError("Invalid meal index")

    if settings.openai_api_key:
        try:
            updated = await _replace_with_openai(context, menu, meal_index, hint)
            return _apply_leftovers([updated], context.leftovers)[0]
        except Exception:
            logger.exception("OpenAI dish replace failed, using fallback")

    updated = _replace_fallback(menu, meal_index, hint)
    return _apply_leftovers([updated], context.leftovers)[0]


async def _generate_with_openai(context: MenuGenerationContext) -> list[MenuVariant]:
    user_prompt = (
        f"{context.prompt_text}\n\n"
        "Верни ровно 3 варианта меню: quick (быстрое), economy (экономное), "
        "balanced (сбалансированное). Для каждого — объяснение почему подходит семье, "
        "список блюд и общий список ингредиентов на день."
    )
    data = await _openai_chat_json(user_prompt)
    menus = _parse_menus(data["menus"])
    return _apply_leftovers(menus, context.leftovers)


async def _replace_with_openai(
    context: MenuGenerationContext,
    menu: MenuVariant,
    meal_index: int,
    hint: str | None,
) -> MenuVariant:
    meal = menu.meals[meal_index]
    hint_text = f" Пожелание: {hint}." if hint else ""
    user_prompt = (
        f"{context.prompt_text}\n\n"
        f"Замени одно блюдо в меню «{menu.title}».\n"
        f"Блюдо для замены ({meal.meal_type}): {meal.name} — {meal.description}.{hint_text}\n"
        "Верни JSON: {\"meal\": {...}, \"ingredients\": [...]}} — новое блюдо и "
        "обновлённый полный список ингредиентов на день для этого меню."
    )
    data = await _openai_chat_json(user_prompt, single_meal=True)
    updated = menu.model_copy(deep=True)
    updated.meals[meal_index] = MenuMeal.model_validate(data["meal"])
    updated.ingredients = [
        MenuIngredient.model_validate(item) for item in data["ingredients"]
    ]
    updated.total_prep_minutes = sum(m.prep_time_minutes for m in updated.meals)
    return updated


async def _openai_chat_json(user_prompt: str, *, single_meal: bool = False) -> dict[str, Any]:
    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
    }

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        body = response.json()

    content = body["choices"][0]["message"]["content"]
    return json.loads(content)


def _parse_menus(raw_menus: list[dict[str, Any]]) -> list[MenuVariant]:
    variants: list[MenuVariant] = []
    for item in raw_menus:
        variant_key = item.get("variant")
        meta = VARIANT_META.get(variant_key, {})
        if not item.get("title"):
            item["title"] = meta.get("title", item.get("variant", "Меню"))
        if not item.get("tagline"):
            item["tagline"] = meta.get("tagline", "")
        variants.append(MenuVariant.model_validate(item))

    order = ["quick", "economy", "balanced"]
    variants.sort(key=lambda menu: order.index(menu.variant) if menu.variant in order else 99)
    return variants


def _generate_fallback(context: MenuGenerationContext) -> list[MenuVariant]:
    family_note = (
        f"для семьи «{context.family_name}» ({context.members_count} чел.)"
        if context.has_family
        else "для вашего профиля"
    )
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
                ("Перец и помидоры", "400 г", "овощи"),
            ],
            "explanation": (
                f"Быстрое меню {family_note}: минимум активного времени у плиты, "
                "подходит при ограничении по времени готовки."
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
                ("Морковь и лук", "500 г", "овощи"),
                ("Макароны", "400 г", "крупы"),
                ("Томатная паста", "2 ст.л.", "соусы"),
            ],
            "explanation": (
                f"Экономное меню {family_note}: доступные продукты, "
                "учитывает цель экономии бюджета."
            ),
            "cost": "350–500 ₽",
            "minutes": 65,
        },
        "balanced": {
            "meals": [
                (
                    "breakfast",
                    "Творожная запеканка",
                    "Белок и кальций на завтрак",
                    30,
                ),
                (
                    "lunch",
                    "Запечённая рыба с овощами",
                    "Омега-3 и клетчатка",
                    40,
                ),
                (
                    "dinner",
                    "Салат с киноа и индейкой",
                    "Лёгкий сбалансированный ужин",
                    25,
                ),
                ("snack", "Фрукты и горсть орехов", "Перекус без готовки", 0),
            ],
            "ingredients": [
                ("Творог", "500 г", "молочное"),
                ("Яйца", "3 шт", "яйца"),
                ("Филе белой рыбы", "500 г", "рыба"),
                ("Брокколи и цукини", "600 г", "овощи"),
                ("Киноа", "200 г", "крупы"),
                ("Филе индейки", "400 г", "мясо"),
                ("Яблоки и бананы", "4 шт", "фрукты"),
            ],
            "explanation": (
                f"Сбалансированное меню {family_note}: разнообразие белков, "
                "овощей и умеренное время готовки."
            ),
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


def _apply_leftovers(
    menus: list[MenuVariant], leftovers: list
) -> list[MenuVariant]:
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
        updated.explanation = f"{menu.explanation} Блюдо заменено с учётом пожелания: {hint}."
    return updated
