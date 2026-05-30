"""Tests for dish replacement stability."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.schemas.menu import (  # noqa: E402
    MenuDayPlan,
    MenuIngredient,
    MenuMeal,
    MenuVariant,
)
from app.services.menu_ai_legacy import _apply_replaced_meal, replace_meal  # noqa: E402
from app.services.menu_context import MenuGenerationContext  # noqa: E402


def _sample_menu() -> MenuVariant:
    return MenuVariant(
        variant="balanced",
        title="Тест",
        explanation="Тестовое меню",
        total_prep_minutes=60,
        meals=[
            MenuMeal(
                meal_type="breakfast",
                name="Завтрак",
                description="Было",
                prep_time_minutes=10,
            ),
            MenuMeal(
                meal_type="lunch",
                name="Обед",
                description="Было",
                prep_time_minutes=30,
            ),
        ],
        ingredients=[
            MenuIngredient(name="Яйца", amount="4 шт", category="яйца"),
        ],
    )


def _context() -> MenuGenerationContext:
    return MenuGenerationContext(
        scope_mode="personal",
        context_label="Тест",
        family_name=None,
        members_count=1,
        prompt_text="Контекст",
        has_family=False,
        leftovers=[],
    )


def test_replace_meal_keeps_ingredients_when_ai_returns_empty_list():
    menu = _sample_menu()
    ctx = _context()

    async def run() -> MenuVariant:
        with patch("app.services.ai_client.is_ai_configured", return_value=True), patch(
            "app.services.ai_context.build_ai_user_context",
            return_value=object(),
        ), patch(
            "app.services.ai_client.chat_json",
            new=AsyncMock(
                return_value={
                    "breakfast": "Новый завтрак",
                    "ingredients": [],
                }
            ),
        ):
            return await replace_meal(
                ctx,
                menu,
                0,
                None,
                db=object(),
                user=object(),
                scope=object(),
            )

    updated = asyncio.run(run())

    assert updated.meals[0].name == "Новый завтрак"
    assert len(updated.ingredients) == 1
    assert updated.ingredients[0].name == "Яйца"


def test_replace_meal_can_run_twice_via_fallback():
    menu = _sample_menu()
    ctx = _context()

    async def run(current: MenuVariant, meal_index: int) -> MenuVariant:
        with patch("app.services.ai_client.is_ai_configured", return_value=False):
            return await replace_meal(ctx, current, meal_index, None)

    after_first = asyncio.run(run(menu, 0))
    after_second = asyncio.run(run(after_first, 1))

    assert after_first.meals[0].name != "Завтрак"
    assert after_second.meals[1].name != "Обед"
    assert len(after_second.ingredients) == 1


def test_apply_replaced_meal_syncs_multi_day_plan():
    meals = [
        MenuMeal(
            meal_type="breakfast",
            name="Завтрак",
            description="",
            prep_time_minutes=10,
        ),
        MenuMeal(
            meal_type="lunch",
            name="Обед",
            description="",
            prep_time_minutes=30,
        ),
    ]
    menu = MenuVariant(
        variant="balanced",
        title="Неделя",
        explanation="План",
        total_prep_minutes=40,
        meals=list(meals),
        ingredients=[MenuIngredient(name="Яйца", amount="2 шт")],
        plan_days=2,
        days=[
            MenuDayPlan(day_index=1, label="День 1", meals=list(meals)),
            MenuDayPlan(
                day_index=2,
                label="День 2",
                meals=[
                    MenuMeal(
                        meal_type="breakfast",
                        name="Д2 завтрак",
                        description="",
                        prep_time_minutes=10,
                    ),
                    MenuMeal(
                        meal_type="lunch",
                        name="Д2 обед",
                        description="",
                        prep_time_minutes=30,
                    ),
                ],
            ),
        ],
    )
    day_two_view = menu.model_copy(update={"meals": menu.days[1].meals})
    new_lunch = MenuMeal(
        meal_type="lunch",
        name="Новый обед",
        description="",
        prep_time_minutes=25,
    )

    updated = _apply_replaced_meal(
        day_two_view,
        1,
        new_lunch,
        day_index=2,
    )

    assert updated.days[1].meals[1].name == "Новый обед"
    assert updated.days[0].meals[1].name == "Обед"
