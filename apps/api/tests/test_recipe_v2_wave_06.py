from app.recipes.legacy_resolver import resolve_legacy_recipe
from app.recipes.v2_contracts import (
    RecipeIngredientV2,
    RecipeNutritionProjection,
    recipe_instruction_proves_cooking,
    recipe_tag_proves_verified_gf,
    validate_recipe_version_payload,
)


def test_recipe_identity_and_version_contract_is_explicit():
    assert validate_recipe_version_payload({"title": "Soup", "servings": 2, "ingredients": []}) == []
    assert validate_recipe_version_payload({"title": "", "servings": 0}) == ["title_required", "servings_positive"]


def test_unknown_quantity_and_unit_are_preserved():
    ingredient = RecipeIngredientV2("egg")
    assert ingredient.quantity_is_unknown
    assert ingredient.unit_is_unknown


def test_quantity_does_not_allow_fake_grams_or_unitless_amounts():
    assert "quantity_requires_unit" in validate_recipe_version_payload(
        {"title": "Soup", "ingredients": [{"display_text": "egg", "quantity": 1}]}
    )


def test_per_serving_projection_requires_complete_known_servings():
    complete = RecipeNutritionProjection({"kcal": 400}, 2, True)
    incomplete = RecipeNutritionProjection({"kcal": None}, 2, False)
    assert complete.per_serving == {"kcal": 200.0}
    assert incomplete.per_serving is None


def test_recipe_tags_and_instructions_are_not_evidence():
    assert not recipe_tag_proves_verified_gf("gluten_free")
    assert not recipe_instruction_proves_cooking("Cook until steaming hot")


def test_legacy_mapping_is_bounded_and_archive_is_fallback():
    mapped = resolve_legacy_recipe(10, {10: ("recipe", "version")}, {})
    archived = resolve_legacy_recipe(11, {}, {11: {"title": "Legacy"}})
    assert (mapped.status, mapped.canonical_recipe_id, mapped.canonical_version_id) == ("MAPPED", "recipe", "version")
    assert archived.status == "ARCHIVE_FALLBACK"
    assert archived.archive_payload == {"title": "Legacy"}
