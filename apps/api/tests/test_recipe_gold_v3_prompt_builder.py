"""Tests for Gold V3 recipe prompt builder (Stage F.1)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_gold_v3_prompt_builder import (  # noqa: E402
    build_recipe_gold_v3_generation_messages,
    build_recipe_gold_v3_system_prompt,
    build_recipe_gold_v3_user_prompt,
    sanitize_signal_for_prompt,
)


def _signal_with_leaks() -> dict:
    return {
        "signal_id": "pov_sig_000099",
        "title": "Салат Винегрет",
        "source_url": "https://www.povarenok.ru/recipes/show/1/",
        "original_steps": ["нарезать", "смешать"],
        "raw_ingredient_names_normalized": ["свекла", "картофель"],
        "dish_family": "салат",
        "meal_type_hints": ["lunch"],
        "main_product_groups": ["овощи"],
        "generation_prompt_hints": ["оригинальное блюдо"],
    }


def test_prompt_does_not_include_source_url():
    user = build_recipe_gold_v3_user_prompt(_signal_with_leaks())
    assert "povarenok" not in user.lower()
    assert "source_url" not in user


def test_prompt_does_not_include_title_even_if_signal_has_title():
    user = build_recipe_gold_v3_user_prompt(_signal_with_leaks())
    assert "Винегрет" not in user
    assert "Салат Винегрет" not in user
    safe = sanitize_signal_for_prompt(_signal_with_leaks())
    assert "title" not in safe


def test_prompt_includes_schema_requirements():
    system = build_recipe_gold_v3_system_prompt()
    assert "recipe_gold_v3" in system
    assert "nutrition_per_serving" in system
    assert "минимум 4" in system.lower() or "ingredients: минимум 4" in system


def test_prompt_includes_originality_rules():
    system = build_recipe_gold_v3_system_prompt()
    assert "оригинальн" in system.lower()
    assert "ЗАПРЕЩЕНО" in system or "запрещено" in system.lower()


def test_prompt_includes_nutrition_per_serving():
    system = build_recipe_gold_v3_system_prompt()
    assert "nutrition_per_serving" in system
    assert "fiber_g" in system
    assert "salt_g" in system
    assert "sugar_g" in system


def test_prompt_includes_shopping_and_image_contract():
    system = build_recipe_gold_v3_system_prompt()
    assert "shopping_name" in system
    assert "image_prompt_data" in system
    assert "единый сервиз PLANAM" in system


def test_prompt_contains_allowed_units():
    system = build_recipe_gold_v3_system_prompt()
    for unit in ("г", "мл", "шт", "ч.л.", "ст.л.", "по вкусу"):
        assert unit in system


def test_prompt_forbids_bad_units():
    system = build_recipe_gold_v3_system_prompt()
    assert "шт." in system or "ст. л." in system
    assert "зубчик" in system


def test_prompt_requires_shopping_name_for_every_ingredient():
    system = build_recipe_gold_v3_system_prompt()
    assert "shopping_name ОБЯЗАТЕЛЕН" in system or "shopping_name" in system


def test_prompt_requires_fiber_salt_sugar():
    system = build_recipe_gold_v3_system_prompt()
    assert "fiber_g" in system and "salt_g" in system and "sugar_g" in system
    assert "null" in system.lower() or "без null" in system.lower()


def test_prompt_tells_not_to_add_contradictory_restriction_keys():
    system = build_recipe_gold_v3_system_prompt()
    assert "vegan" in system
    assert "противореч" in system.lower()


def test_generation_messages_structure():
    messages = build_recipe_gold_v3_generation_messages(_signal_with_leaks())
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert json.loads(json.dumps(sanitize_signal_for_prompt(_signal_with_leaks())))
