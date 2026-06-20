"""Schemas for menu day/week nutrition aggregation responses."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Confidence = Literal["exact", "estimated", "low_confidence", "unavailable"]


class NutritionMacros(BaseModel):
    kcal: float = 0
    protein: float = 0
    fat: float = 0
    carbs: float = 0


class NutritionTargets(BaseModel):
    kcal: int | None = None
    protein: int | None = None
    fat: int | None = None
    carbs: int | None = None


class NutritionProgress(BaseModel):
    kcal_pct: int | None = None
    protein_pct: int | None = None
    fat_pct: int | None = None
    carbs_pct: int | None = None


class NutritionCoverage(BaseModel):
    total_items: int = 0
    calculated_items: int = 0
    exact_items: int = 0
    estimated_items: int = 0
    low_confidence_items: int = 0
    unavailable_items: int = 0
    coverage_pct: int = 0


class MealNutritionItem(BaseModel):
    recipe_id: int | None = None
    name: str = ""
    kcal: float | None = None
    confidence: Confidence | None = None


class MealNutritionBlock(BaseModel):
    meal_type: str
    totals: NutritionMacros
    items: list[MealNutritionItem] = []


class DayNutritionResponse(BaseModel):
    date: str
    totals: NutritionMacros
    targets: NutritionTargets
    progress: NutritionProgress
    confidence: Confidence
    coverage: NutritionCoverage
    meals: list[MealNutritionBlock] = []
    warnings: list[str] = []


class WeekNutritionResponse(BaseModel):
    start_date: str
    end_date: str
    days: list[DayNutritionResponse] = []
    weekly_total: NutritionMacros
    weekly_average: NutritionMacros
    days_with_full_calc: int = 0
    confidence: Confidence
    warnings: list[str] = []
