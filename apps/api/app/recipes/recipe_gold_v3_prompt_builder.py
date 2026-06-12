"""Build OpenAI prompts for Gold V3 original recipe generation from culinary signals."""

from __future__ import annotations

import json
from typing import Any

from app.recipes.recipe_gold_v3_schema import SCHEMA_VERSION

# Keys safe to pass into AI prompts (no raw Povarenok text / URLs / ingredient names).
_SIGNAL_PROMPT_KEYS: frozenset[str] = frozenset(
    {
        "signal_id",
        "dish_family",
        "meal_type_hints",
        "category_hints",
        "main_product_groups",
        "secondary_product_groups",
        "cooking_methods",
        "equipment_hints",
        "complexity",
        "family_fit",
        "time_bucket",
        "nutrition_style_hints",
        "restriction_hints",
        "allergen_hints",
        "seasonality_hints",
        "generation_prompt_hints",
        "ingredient_count_bucket",
    }
)

_FORBIDDEN_SIGNAL_KEYS: frozenset[str] = frozenset(
    {
        "title",
        "original_title",
        "steps",
        "original_steps",
        "source_url",
        "description",
        "raw_ingredient_names_normalized",
        "copied_source_text",
    }
)


def sanitize_signal_for_prompt(signal: dict[str, Any]) -> dict[str, Any]:
    """Return signal subset safe for AI — no titles, steps, URLs, raw ingredient names."""
    cleaned: dict[str, Any] = {}
    for key, value in signal.items():
        if key in _FORBIDDEN_SIGNAL_KEYS:
            continue
        if key in _SIGNAL_PROMPT_KEYS:
            cleaned[key] = value
    return cleaned


def build_recipe_gold_v3_system_prompt() -> str:
    return f"""Ты — шеф-редактор PLANAM. Создаёшь полностью оригинальные русскоязычные семейные рецепты.

ЖЁСТКИЕ ПРАВИЛА:
1. Язык рецепта — только русский (title, description, steps, ingredients).
2. Рецепт должен быть оригинальным PLANAM, НЕ копией внешнего источника.
3. ЗАПРЕЩЕНО: original title, source title, source steps, source_url, узнаваемая структура Povarenok,
   английские префиксы (High protein:, Pro small portion:, Pre-workout:), слово bowl в названии.
4. Culinary signal — только абстрактная подсказка (группы продуктов, методы, meal hints).
5. Ответ — ТОЛЬКО один JSON-объект без markdown.

СХЕМА (schema_version={SCHEMA_VERSION}):
- schema_version, status=gold, source_type=generated_original
- originality: is_original_planam_recipe, no_source_title_used, no_source_steps_used, no_direct_copy=true;
  source_similarity_risk=low|medium (не high)
- title (8-80 символов, русский), subtitle, description (мин. 20 символов)
- meal_type: breakfast|lunch|dinner|snack
- category: main|soup|salad|side|breakfast|snack|dessert|drink
- cuisine_style, servings (1-8), prep_time_min, cook_time_min, total_time_min, difficulty, family_fit
- ingredients: минимум 4, каждый с name, amount>0, unit, display_amount, category (русские группы),
  shopping_name, optional
- steps: минимум 4, step_number, text >= 25 символов каждый
- nutrition_per_serving: kcal>0, protein_g, fat_g, carbs_g (согласованы с kcal), fiber_g опционально
- restriction_keys: только из canonical catalog (no_pork, vegetarian, gluten_free, …)
- allergen_keys, diet_tags
- shopping: aggregation_safe=true, has_fractional_amounts, rounding_notes
- image_prompt_data: dish_visual_summary, serving_style="единый сервиз PLANAM",
  avoid_visuals=["текст","логотипы","руки","грязный фон"]
- quality: score=0, flags=[], warnings=[]

Не включай source_url, original_title, original_steps, tags (добавятся автоматически)."""


def build_recipe_gold_v3_user_prompt(
    signal: dict[str, Any],
    target_profile: dict[str, Any] | None = None,
    *,
    validator_feedback: list[dict[str, str]] | None = None,
) -> str:
    safe_signal = sanitize_signal_for_prompt(signal)
    parts = [
        "Создай один оригинальный рецепт PLANAM по culinary signal ниже.",
        "Используй только абстрактные подсказки signal. Не воспроизводи чужие названия и шаги.",
        "",
        "CULINARY SIGNAL (обезличенный):",
        json.dumps(safe_signal, ensure_ascii=False, indent=2),
    ]
    if target_profile:
        parts.extend(
            [
                "",
                "TARGET PROFILE (учитывай ограничения):",
                json.dumps(target_profile, ensure_ascii=False, indent=2),
            ]
        )
    if validator_feedback:
        parts.extend(
            [
                "",
                "ИСПРАВЬ ОШИБКИ ВАЛИДАТОРА (без копирования источника):",
                json.dumps(validator_feedback, ensure_ascii=False, indent=2),
            ]
        )
    parts.append("")
    parts.append("Верни только JSON-объект рецепта Gold V3.")
    return "\n".join(parts)


def build_recipe_gold_v3_generation_messages(
    signal: dict[str, Any],
    target_profile: dict[str, Any] | None = None,
    *,
    validator_feedback: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": build_recipe_gold_v3_system_prompt()},
        {
            "role": "user",
            "content": build_recipe_gold_v3_user_prompt(
                signal,
                target_profile,
                validator_feedback=validator_feedback,
            ),
        },
    ]
