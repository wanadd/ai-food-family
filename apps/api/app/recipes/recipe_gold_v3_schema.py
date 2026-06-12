"""PLANAM Recipe Gold V3 schema — generation/import contract (no DB writes)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SCHEMA_VERSION = "recipe_gold_v3"

ALLOWED_STATUSES: frozenset[str] = frozenset({"gold"})
ALLOWED_SOURCE_TYPES: frozenset[str] = frozenset(
    {"generated_original", "manual_original"}
)
ALLOWED_MEAL_TYPES: frozenset[str] = frozenset(
    {"breakfast", "lunch", "dinner", "snack"}
)
ALLOWED_CATEGORIES: frozenset[str] = frozenset(
    {"main", "soup", "salad", "side", "breakfast", "snack", "dessert", "drink"}
)
ALLOWED_DIFFICULTIES: frozenset[str] = frozenset({"easy", "medium", "hard"})
ALLOWED_FAMILY_FIT: frozenset[str] = frozenset({"high", "medium", "low"})
ALLOWED_SIMILARITY_RISK: frozenset[str] = frozenset({"low", "medium", "high"})
ALLOWED_CUISINE_STYLES: frozenset[str] = frozenset(
    {
        "домашняя",
        "современная",
        "семейная",
        "средиземноморская",
        "азиатская",
        "unknown",
    }
)

ALLOWED_INGREDIENT_CATEGORIES: frozenset[str] = frozenset(
    {
        "мясо_птица",
        "мясо",
        "свинина",
        "рыба",
        "морепродукты",
        "молочные продукты",
        "яйца",
        "крупы",
        "паста",
        "овощи",
        "фрукты/ягоды",
        "сладкое",
        "выпечка/тесто",
        "бобовые",
        "орехи",
        "масла/соусы",
        "специи",
        "напитки",
        "прочее",
    }
)

ALLOWED_UNITS: frozenset[str] = frozenset(
    {
        "г",
        "кг",
        "мл",
        "л",
        "шт",
        "ст.л.",
        "ч.л.",
        "по вкусу",
        "щепотка",
        "зубчик",
        "пучок",
    }
)

ENGLISH_TITLE_PREFIXES: tuple[str, ...] = (
    "high protein:",
    "pro small portion:",
    "pre-workout:",
)

FORBIDDEN_TECHNICAL_CATEGORIES: frozenset[str] = frozenset(
    {"eggs", "casserole", "sport", "porridge", "dairy", "bowl"}
)

PRODUCTION_READY_MIN_SCORE = 85
MIN_INGREDIENTS = 4
MAX_INGREDIENTS_DEFAULT = 18
MIN_STEPS = 4
MIN_STEP_TEXT_LEN = 25
MIN_TITLE_LEN = 8
MAX_TITLE_LEN = 80


class OriginalityBlock(BaseModel):
    is_original_planam_recipe: bool = True
    no_source_title_used: bool = True
    no_source_steps_used: bool = True
    no_direct_copy: bool = True
    source_similarity_risk: Literal["low", "medium", "high"] = "low"
    originality_notes: str = ""


class IngredientGoldV3(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount: float = Field(gt=0)
    unit: str
    display_amount: str = Field(min_length=1, max_length=80)
    category: str
    optional: bool = False
    shopping_name: str = Field(min_length=1, max_length=120)


class StepGoldV3(BaseModel):
    step_number: int = Field(ge=1)
    text: str = Field(min_length=25)


class NutritionPerServingGoldV3(BaseModel):
    kcal: float = Field(gt=0)
    protein_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fiber_g: float | None = None
    salt_g: float | None = None
    sugar_g: float | None = None


class ShoppingBlockGoldV3(BaseModel):
    aggregation_safe: bool = True
    has_fractional_amounts: bool = False
    rounding_notes: str = ""


class ImagePromptDataGoldV3(BaseModel):
    dish_visual_summary: str = Field(min_length=10)
    serving_style: str = "единый сервиз PLANAM"
    avoid_visuals: list[str] = Field(
        default_factory=lambda: ["текст", "логотипы", "руки", "грязный фон"]
    )


class QualityBlockGoldV3(BaseModel):
    score: int = 0
    flags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RecipeGoldV3(BaseModel):
    """Canonical Gold V3 recipe document (nutrition_per_serving-first)."""

    schema_version: Literal["recipe_gold_v3"] = SCHEMA_VERSION
    status: Literal["gold"] = "gold"
    source_type: Literal["generated_original", "manual_original"]
    source_signal_ids: list[str] = Field(default_factory=list)
    originality: OriginalityBlock
    title: str = Field(min_length=MIN_TITLE_LEN, max_length=MAX_TITLE_LEN)
    subtitle: str = ""
    description: str = Field(min_length=20)
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    category: Literal[
        "main", "soup", "salad", "side", "breakfast", "snack", "dessert", "drink"
    ]
    cuisine_style: str = "семейная"
    servings: int = Field(ge=1, le=8)
    prep_time_min: int = Field(ge=0, le=300)
    cook_time_min: int = Field(ge=0, le=300)
    total_time_min: int = Field(ge=0, le=600)
    difficulty: Literal["easy", "medium", "hard"]
    family_fit: Literal["high", "medium", "low"] = "high"
    ingredients: list[IngredientGoldV3] = Field(min_length=MIN_INGREDIENTS)
    steps: list[StepGoldV3] = Field(min_length=MIN_STEPS)
    nutrition_per_serving: NutritionPerServingGoldV3
    restriction_keys: list[str] = Field(default_factory=list)
    allergen_keys: list[str] = Field(default_factory=list)
    diet_tags: list[str] = Field(default_factory=list)
    shopping: ShoppingBlockGoldV3 = Field(default_factory=ShoppingBlockGoldV3)
    image_prompt_data: ImagePromptDataGoldV3
    quality: QualityBlockGoldV3 = Field(default_factory=QualityBlockGoldV3)
