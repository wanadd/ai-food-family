"""Build OpenAI prompts for Gold V3 original recipe generation from culinary signals."""

from __future__ import annotations

import json
from typing import Any

from app.nutrition.restrictions_catalog import get_restriction_definition
from app.recipes.recipe_gold_v3_postprocess import PROMPT_ALLOWED_UNITS
from app.recipes.recipe_gold_v3_schema import (
    ALLOWED_INGREDIENT_CATEGORIES,
    PRODUCTION_READY_MIN_SCORE,
    SCHEMA_VERSION,
)

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

_RETRY_WARNING_CODES: frozenset[str] = frozenset(
    {
        "ingredient_unclear_unit",
        "unknown_ingredient_category",
        "missing_fiber",
        "missing_sugar_salt",
        "title_too_many_words",
    }
)

_CATEGORIES_FOR_PROMPT = sorted(ALLOWED_INGREDIENT_CATEGORIES)


def sanitize_signal_for_prompt(signal: dict[str, Any]) -> dict[str, Any]:
    """Return signal subset safe for AI — no titles, steps, URLs, raw ingredient names."""
    cleaned: dict[str, Any] = {}
    for key, value in signal.items():
        if key in _FORBIDDEN_SIGNAL_KEYS:
            continue
        if key in _SIGNAL_PROMPT_KEYS:
            cleaned[key] = value
    return cleaned


def build_target_profile_from_signal(signal: dict[str, Any]) -> dict[str, Any]:
    """Hints for restrictions — model must align ingredients with declared keys."""
    hints = signal.get("restriction_hints") or []
    canonical = [h for h in hints if get_restriction_definition(h)]
    return {
        "restriction_hints": canonical,
        "allergen_hints": signal.get("allergen_hints") or [],
        "note": (
            "restriction_keys must NOT contradict ingredients. "
            "If unsure — use only no_pork and no_alcohol or leave restriction_keys empty."
        ),
    }


def _ingredient_contract_block() -> str:
    units = ", ".join(f'"{u}"' for u in PROMPT_ALLOWED_UNITS)
    forbidden_units = (
        "шт., ст. л., ч. ложка, ст. ложки, ложка, стакан, зубчик, пучок, щепотка, гр, грамм"
    )
    categories = ", ".join(_CATEGORIES_FOR_PROMPT)
    return f"""ИНГРЕДИЕНТЫ (строго):
- Каждый ingredient ОБЯЗАН иметь: name, amount, unit, display_amount, category, optional, shopping_name.
- shopping_name ОБЯЗАТЕЛЕН для КАЖДОГО ингредиента (короткое нормализованное имя для списка покупок).
  Пример: name="куриное филе" → shopping_name="куриное филе";
  name="масло оливковое" → shopping_name="оливковое масло".
- Разрешённые unit: {units}.
- ЗАПРЕЩЁННЫЕ unit: {forbidden_units}.
  Для чеснока/зелени: amount=1, unit="шт", display_amount="1 шт", shopping_name="чеснок"/"петрушка".
- Разрешённые category (только из whitelist): {categories}.
- ЗАПРЕЩЁННЫЕ category: жиры, мясо птицы, приправы, жидкость, другие, eggs, dairy, sport."""


def _nutrition_contract_block() -> str:
    return """NUTRITION (nutrition_per_serving — все поля обязательны, без null):
- kcal, protein_g, fat_g, carbs_g — согласованы: kcal ≈ protein_g*4 + fat_g*9 + carbs_g*4 (±35%).
- fiber_g, salt_g, sugar_g — реалистичные оценки (не null, не нули везде).
  Пример супа: fiber_g=5, salt_g=1.2, sugar_g=3; десерт: sugar_g=10."""


def _title_contract_block() -> str:
    return """TITLE / DISPLAY_TITLE / DESCRIPTION (UI contract):
- title: полное пользовательское название на русском, 28-52 символа (макс. 64).
  Без #1, Pro, High protein, Pre-workout, AI, Gold, английских префиксов, raw slugs (side/main/soup/salad/lunch/dinner).
- display_title: ОБЯЗАТЕЛЬНО, 18-38 символов, короткое имя для карточки каталога.
  Не дублируй длинный title дословно — сократи без потери смысла.
- description: 1-2 предложения, 90-170 символов, без пустых рекламных фраз, не повторяй title.
- category/meal_type: только canonical slugs в JSON; НИКОГДА не вставляй slugs в title/display_title/description.
- nutrition_confidence: только exact|estimated|low_confidence|unavailable (для AI по умолчанию estimated).
- source_type: generated_original (AI) или manual_original (ручной); не используй import для новых PlanAm рецептов."""


def _restriction_contract_block() -> str:
    return """RESTRICTION_KEYS (не противоречить ингредиентам):
- Нельзя vegan/vegetarian/pescatarian если есть мясо/рыба/курица.
- Нельзя vegan/lactose_free/no_milk если есть молоко/сыр/творог/йогурт/сметана.
- Нельзя vegan/no_eggs если есть яйца.
- Нельзя no_pork/halal/kosher если есть свинина/бекон/ветчина.
- Нельзя no_alcohol если есть вино/пиво/алкоголь.
- Лучше пустой список или только no_pork + no_alcohol, чем противоречивые ключи."""


def build_recipe_gold_v3_system_prompt() -> str:
    return f"""Ты — шеф-редактор PLANAM. Создаёшь полностью оригинальные русскоязычные семейные рецепты.

ЖЁСТКИЕ ПРАВИЛА:
1. Язык рецепта — только русский (title, description, steps, ingredients).
2. Рецепт должен быть оригинальным PLANAM, НЕ копией внешнего источника.
3. ЗАПРЕЩЕНО: original title, source title, source steps, source_url, узнаваемая структура Povarenok,
   английские префиксы (High protein:, Pro small portion:, Pre-workout:), слово bowl в названии.
4. Culinary signal — только абстрактная подсказка (группы продуктов, методы, meal hints).
5. Ответ — ТОЛЬКО один JSON-объект без markdown.
6. Production-ready: score ≥ {PRODUCTION_READY_MIN_SCORE} после валидации.

СХЕМА (schema_version={SCHEMA_VERSION}):
- schema_version, status=gold, source_type=generated_original
- originality: is_original_planam_recipe, no_source_title_used, no_source_steps_used, no_direct_copy=true;
  source_similarity_risk=low|medium (не high)
- title (8-64 символов, русский), display_title (18-38, обязателен), subtitle, description (90-170 символов)
- meal_type: breakfast|lunch|dinner|snack
- category: main|soup|salad|side|breakfast|snack|dessert|drink
- cuisine_style, servings (1-8), prep_time_min, cook_time_min, total_time_min (=prep+cook), difficulty, family_fit
- ingredients: минимум 4
- steps: минимум 4, step_number, text >= 25 символов каждый
- restriction_keys: только canonical keys из catalog
- allergen_keys, diet_tags
- shopping: aggregation_safe=true, has_fractional_amounts, rounding_notes
- image_prompt_data: dish_visual_summary, serving_style="единый сервиз PLANAM",
  avoid_visuals=["текст","логотипы","руки","грязный фон"]
- quality: score=0, flags=[], warnings=[]

{_ingredient_contract_block()}

{_nutrition_contract_block()}

{_title_contract_block()}

{_restriction_contract_block()}

Не включай source_url, original_title, original_steps, tags (добавятся автоматически)."""


def _retry_fix_block() -> str:
    return """ИСПРАВЬ и верни ВЕСЬ JSON заново:
- У каждого ingredient должен быть shopping_name.
- Только разрешённые unit и category.
- Заполни fiber_g, salt_g, sugar_g.
- Убери противоречивые restriction_keys.
- Сократи title до 2–5 слов."""


def build_recipe_gold_v3_user_prompt(
    signal: dict[str, Any],
    target_profile: dict[str, Any] | None = None,
    *,
    validator_feedback: list[dict[str, str]] | None = None,
) -> str:
    safe_signal = sanitize_signal_for_prompt(signal)
    profile = target_profile or build_target_profile_from_signal(signal)
    parts = [
        "Создай один оригинальный рецепт PLANAM по culinary signal ниже.",
        "Используй только абстрактные подсказки signal. Не воспроизводи чужие названия и шаги.",
        "",
        "CULINARY SIGNAL (обезличенный):",
        json.dumps(safe_signal, ensure_ascii=False, indent=2),
        "",
        "TARGET PROFILE (ограничения — не противоречь ингредиентам):",
        json.dumps(profile, ensure_ascii=False, indent=2),
    ]
    if validator_feedback:
        parts.extend(
            [
                "",
                "ИСПРАВЬ ОШИБКИ/ПРЕДУПРЕЖДЕНИЯ ВАЛИДАТОРА (без копирования источника):",
                json.dumps(validator_feedback, ensure_ascii=False, indent=2),
                "",
                _retry_fix_block(),
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


def feedback_codes_for_retry() -> frozenset[str]:
    return _RETRY_WARNING_CODES
