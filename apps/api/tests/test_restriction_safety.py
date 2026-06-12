from dataclasses import dataclass, field

from app.nutrition.restriction_safety import (
    explain_recipe_restriction_conflicts,
    has_hard_conflicts,
    has_soft_conflicts,
    recipe_is_allowed_for_profile,
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
    title: str = ""
    description: str = ""
    ingredients: list[dict] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    diets: list[str] = field(default_factory=list)
    allergens: list[str] = field(default_factory=list)
    restrictions: list[str] = field(default_factory=list)
    is_alcoholic: bool = False


def _recipe_with(*ingredient_names: str) -> FakeRecipe:
    return FakeRecipe(ingredients=[{"name": name} for name in ingredient_names])


def _profile_with_restriction(key: str) -> FakeProfile:
    return FakeProfile(restrictions=[key])


def _hard_conflict_for(profile: FakeProfile, recipe: FakeRecipe) -> bool:
    conflicts = explain_recipe_restriction_conflicts(recipe, profile)
    return has_hard_conflicts(conflicts)


def test_no_pork_blocks_svinina():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("свинина"), _profile_with_restriction("no_pork")
    )


def test_no_pork_blocks_bacon():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("бекон"), _profile_with_restriction("no_pork")
    )


def test_no_alcohol_blocks_wine():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("вино"), _profile_with_restriction("no_alcohol")
    )


def test_vegetarian_blocks_chicken():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("курица"), _profile_with_restriction("vegetarian")
    )


def test_vegetarian_blocks_salmon():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("лосось"), _profile_with_restriction("vegetarian")
    )


def test_vegan_blocks_eggs():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("яйца"), _profile_with_restriction("vegan")
    )


def test_vegan_blocks_cheese():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("сыр"), _profile_with_restriction("vegan")
    )


def test_pescatarian_blocks_chicken_allows_salmon():
    profile = _profile_with_restriction("pescatarian")
    assert not recipe_is_allowed_for_profile(_recipe_with("курица"), profile)
    assert recipe_is_allowed_for_profile(_recipe_with("лосось"), profile)


def test_gluten_free_blocks_wheat_flour():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("мука пшеничная"), _profile_with_restriction("gluten_free")
    )


def test_lactose_free_blocks_milk():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("молоко"), _profile_with_restriction("lactose_free")
    )


def test_no_eggs_blocks_eggs():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("яйца"), _profile_with_restriction("no_eggs")
    )


def test_no_fish_blocks_salmon():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("лосось"), _profile_with_restriction("no_fish")
    )


def test_no_seafood_blocks_shrimp():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("креветки"), _profile_with_restriction("no_seafood")
    )


def test_no_nuts_blocks_peanut():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("арахис"), _profile_with_restriction("no_nuts")
    )


def test_no_soy_blocks_tofu():
    assert not recipe_is_allowed_for_profile(
        _recipe_with("тофу"), _profile_with_restriction("no_soy")
    )


def test_recipe_without_conflicts_is_allowed():
    profile = _profile_with_restriction("no_pork")
    recipe = _recipe_with("курица", "рис")
    assert recipe_is_allowed_for_profile(recipe, profile)


def test_hard_conflict_blocks_recipe():
    profile = _profile_with_restriction("no_pork")
    recipe = _recipe_with("свинина")
    conflicts = explain_recipe_restriction_conflicts(recipe, profile)
    assert has_hard_conflicts(conflicts)
    assert not recipe_is_allowed_for_profile(recipe, profile)


def test_soft_conflict_does_not_block():
    profile = _profile_with_restriction("diabetes_friendly")
    recipe = _recipe_with("сахар")
    conflicts = explain_recipe_restriction_conflicts(recipe, profile)
    assert has_soft_conflicts(conflicts)
    assert not has_hard_conflicts(conflicts)
    assert recipe_is_allowed_for_profile(recipe, profile)


def test_allergies_produce_conflict_explanation():
    profile = FakeProfile(allergies=["nuts"])
    recipe = _recipe_with("миндаль")
    conflicts = explain_recipe_restriction_conflicts(recipe, profile)
    assert any(c.source == "profile" and "орех" in c.label_ru.lower() for c in conflicts)
    assert not recipe_is_allowed_for_profile(recipe, profile)


def test_banned_foods_produce_hard_conflict():
    profile = FakeProfile(banned_foods="авокадо")
    recipe = _recipe_with("авокадо")
    conflicts = explain_recipe_restriction_conflicts(recipe, profile)
    assert has_hard_conflicts(conflicts)
    assert not recipe_is_allowed_for_profile(recipe, profile)
