from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RecipeIngredientV2:
    display_text: str
    quantity: float | None = None
    unit: str | None = None
    food_identity_key: str | None = None
    preparation_expectation: str | None = None
    product_requirement: dict[str, Any] = field(default_factory=dict)

    @property
    def quantity_is_unknown(self) -> bool:
        return self.quantity is None

    @property
    def unit_is_unknown(self) -> bool:
        return self.unit is None


@dataclass(frozen=True)
class RecipeNutritionProjection:
    per_recipe: dict[str, float | None]
    servings: float | None
    complete: bool
    provenance: dict[str, Any] = field(default_factory=dict)

    @property
    def per_serving(self) -> dict[str, float | None] | None:
        if not self.complete or not self.servings or self.servings <= 0:
            return None
        return {key: (value / self.servings if value is not None else None) for key, value in self.per_recipe.items()}


def recipe_tag_proves_verified_gf(tag: str | None) -> bool:
    return False


def recipe_instruction_proves_cooking(instruction: str) -> bool:
    return False


def validate_recipe_version_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not payload.get("title"):
        errors.append("title_required")
    if payload.get("servings") is not None and payload["servings"] <= 0:
        errors.append("servings_positive")
    for ingredient in payload.get("ingredients", []):
        if ingredient.get("quantity") is not None and not ingredient.get("unit"):
            errors.append("quantity_requires_unit")
    if payload.get("nutrition_complete") and not payload.get("nutrition_provenance"):
        errors.append("nutrition_complete_requires_provenance")
    return errors
