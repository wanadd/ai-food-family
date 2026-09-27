from app.recipes.v2_publication import evaluate_publication_gate
from app.recipes.v2_contracts import RecipeIngredientV2, RecipeNutritionProjection, validate_recipe_version_payload


def _candidate(**overrides):
    candidate = {
        "schema_version": "recipe_gold_v3", "status": "gold", "source_type": "manual_original",
        "source_signal_ids": [],
        "originality": {"is_original_planam_recipe": True, "no_source_title_used": True, "no_source_steps_used": True, "no_direct_copy": True, "source_similarity_risk": "low"},
        "title": "Домашний овощной суп", "description": "Подробное описание домашнего овощного супа для семейного стола.",
        "meal_type": "lunch", "category": "soup", "servings": 4, "prep_time_min": 10, "cook_time_min": 30, "total_time_min": 40, "difficulty": "easy",
        "ingredients": [{"name": "морковь", "amount": 1, "unit": "шт", "display_amount": "1 шт", "category": "овощи", "shopping_name": "морковь"} for _ in range(4)],
        "steps": [{"step_number": number, "text": "Нарежьте продукты и готовьте блюдо до полной готовности."} for number in range(1, 5)],
        "nutrition_per_serving": {"kcal": 100, "protein_g": 3, "fat_g": 2, "carbs_g": 15, "fiber_g": 2, "salt_g": 1, "sugar_g": 2},
        "restriction_keys": [], "allergen_keys": [], "diet_tags": [], "image_prompt_data": {"dish_visual_summary": "Домашний суп в тарелке"},
    }
    candidate.update(overrides)
    return candidate


def test_unknown_quantity_and_unit_remain_explicit():
    ingredient = RecipeIngredientV2("яйцо")
    assert ingredient.quantity_is_unknown
    assert ingredient.unit_is_unknown
    assert "quantity_requires_unit" in validate_recipe_version_payload({"title": "Суп", "ingredients": [{"display_text": "яйцо", "quantity": 1}]})


def test_publication_gate_rejects_block_and_ai_safe_override():
    result = evaluate_publication_gate(_candidate(safety_state="BLOCK", ai_override={"safe": True}))
    assert not result.allowed
    assert "safety_block" in result.reasons
    assert "ai_safe_override_forbidden" in result.reasons


def test_quality_score_does_not_clear_unknown_safety():
    result = evaluate_publication_gate(_candidate(safety_state="UNKNOWN"))
    assert not result.allowed
    assert "safety_unknown" in result.reasons


def test_per_serving_projection_does_not_turn_missing_nutrient_into_zero():
    projection = RecipeNutritionProjection({"kcal": 400, "protein_g": None}, 2, True)
    assert projection.per_serving == {"kcal": 200.0, "protein_g": None}
