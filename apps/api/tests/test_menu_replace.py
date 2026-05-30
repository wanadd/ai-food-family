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
    MenuIngredient,
    MenuMeal,
    MenuVariant,
)
from app.services.menu_ai_legacy import replace_meal  # noqa: E402
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
