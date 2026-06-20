"""Stage C: menu generation restriction safety hooks."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

from app.nutrition.restriction_safety import recipe_is_allowed_for_profile
from app.schemas.menu import MenuIngredient, MenuMeal, MenuVariant
from app.services.menu_restriction_safety import (
    apply_pre_ai_recipe_filter,
    resolve_menu_profile,
    sanitize_menu_variants,
)


@dataclass
class FakeProfile:
    restrictions: list[str] = field(default_factory=list)
    diets: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    banned_foods: str = ""
    medical_restrictions: str = ""


@dataclass
class FakeRecipe:
    id: int
    title: str
    description: str = ""
    meal_type: str = "lunch"
    ingredients: list[dict] = field(default_factory=list)
    cooking_time_minutes: int = 30
    prep_time_minutes: int = 30
    calories_per_serving: float | None = 300.0
    is_alcoholic: bool = False
    tags: list[str] = field(default_factory=list)
    diets: list[str] = field(default_factory=list)
    allergens: list[str] = field(default_factory=list)


def _recipe(recipe_id: int, name: str, meal_type: str = "lunch") -> FakeRecipe:
    return FakeRecipe(
        id=recipe_id,
        title=name,
        meal_type=meal_type,
        ingredients=[{"name": name}],
    )


def _menu_with_meals(*meals: MenuMeal) -> MenuVariant:
    return MenuVariant(
        variant="balanced",
        title="Тест",
        explanation="Тестовое меню",
        total_prep_minutes=60,
        meals=list(meals),
        ingredients=[MenuIngredient(name="Вода", amount="1 л")],
    )


def test_pre_ai_filter_removes_pork_for_no_pork_profile():
    profile = FakeProfile(restrictions=["no_pork"])
    recipes = [
        _recipe(1, "свинина", "lunch"),
        _recipe(2, "курица", "lunch"),
        _recipe(3, "рис", "dinner"),
    ]
    filtered, _ = apply_pre_ai_recipe_filter(recipes, profile)
    ids = {r.id for r in filtered}
    assert 1 not in ids
    assert 2 in ids


def test_pre_ai_filter_keeps_allowed_recipe():
    profile = FakeProfile(restrictions=["no_pork"])
    recipes = [_recipe(2, "курица")]
    filtered, warnings = apply_pre_ai_recipe_filter(recipes, profile)
    assert len(filtered) == 1
    assert filtered[0].id == 2
    assert not any("Нет рецептов" in w for w in warnings)


def test_pre_ai_vegetarian_removes_meat_and_fish():
    profile = FakeProfile(restrictions=["vegetarian"])
    recipes = [
        _recipe(1, "курица"),
        _recipe(2, "лосось"),
        _recipe(3, "овощной суп"),
    ]
    filtered, _ = apply_pre_ai_recipe_filter(recipes, profile)
    assert {r.id for r in filtered} == {3}


def test_pre_ai_vegan_removes_egg_and_milk():
    profile = FakeProfile(restrictions=["vegan"])
    recipes = [
        _recipe(1, "яйца"),
        _recipe(2, "молоко"),
        _recipe(3, "овощи"),
    ]
    filtered, _ = apply_pre_ai_recipe_filter(recipes, profile)
    assert {r.id for r in filtered} == {3}


def test_pre_ai_soft_restriction_does_not_remove_recipe():
    profile = FakeProfile(restrictions=["diabetes_friendly"])
    recipes = [_recipe(1, "сахар")]
    filtered, _ = apply_pre_ai_recipe_filter(recipes, profile)
    assert len(filtered) == 1


def test_post_ai_validation_detects_hard_conflict_and_replaces():
    profile = FakeProfile(restrictions=["no_pork"])
    bad = _recipe(1, "свинина", "lunch")
    good = _recipe(2, "курица", "lunch")
    pool = [bad, good]
    menu = _menu_with_meals(
        MenuMeal(
            meal_type="lunch",
            name="Свинина",
            prep_time_minutes=30,
            recipe_id=1,
        )
    )
    sanitized, notes = sanitize_menu_variants(
        None,
        [menu],
        profile,
        replacement_pool=pool,
    )
    assert sanitized[0].meals[0].recipe_id == 2
    assert any("заменено" in n.lower() for n in notes)


def test_post_ai_validation_allows_clean_menu():
    profile = FakeProfile(restrictions=["no_pork"])
    good = _recipe(2, "курица", "lunch")
    menu = _menu_with_meals(
        MenuMeal(
            meal_type="lunch",
            name="Курица",
            prep_time_minutes=30,
            recipe_id=2,
        )
    )
    sanitized, notes = sanitize_menu_variants(
        None,
        [menu],
        profile,
        replacement_pool=[good],
    )
    assert sanitized[0].meals[0].recipe_id == 2
    assert not any("исключено" in n.lower() for n in notes)


def test_banned_foods_block_matching_recipe_in_post_ai():
    profile = FakeProfile(banned_foods="авокадо")
    bad = _recipe(1, "авокадо", "lunch")
    good = _recipe(2, "салат", "lunch")
    menu = _menu_with_meals(
        MenuMeal(
            meal_type="lunch",
            name="Авокадо",
            prep_time_minutes=10,
            recipe_id=1,
        )
    )
    sanitized, notes = sanitize_menu_variants(
        None,
        [menu],
        profile,
        replacement_pool=[bad, good],
    )
    assert sanitized[0].meals[0].recipe_id == 2
    assert notes


def test_allergies_block_matching_ingredient():
    profile = FakeProfile(allergies=["nuts"])
    bad = _recipe(1, "миндаль", "lunch")
    assert not recipe_is_allowed_for_profile(bad, profile)
    menu = _menu_with_meals(
        MenuMeal(
            meal_type="lunch",
            name="Миндаль",
            prep_time_minutes=10,
            recipe_id=1,
        )
    )
    good = _recipe(2, "овощи", "lunch")
    sanitized, _ = sanitize_menu_variants(
        None,
        [menu],
        profile,
        replacement_pool=[bad, good],
    )
    assert sanitized[0].meals[0].recipe_id == 2


def test_missing_profile_does_not_crash_pre_and_post_ai():
    recipes = [_recipe(1, "свинина"), _recipe(2, "курица")]
    filtered, _ = apply_pre_ai_recipe_filter(recipes, None)
    assert len(filtered) == 2

    menu = _menu_with_meals(
        MenuMeal(
            meal_type="lunch",
            name="Свинина",
            prep_time_minutes=30,
            recipe_id=1,
        )
    )
    sanitized, notes = sanitize_menu_variants(None, [menu], None, replacement_pool=recipes)
    assert sanitized[0].meals[0].recipe_id == 1
    assert notes == []


def test_resolve_menu_profile_returns_none_without_db():
    assert resolve_menu_profile(None, MagicMock()) is None
