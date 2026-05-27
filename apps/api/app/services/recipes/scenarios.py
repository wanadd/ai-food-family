"""Recipe scenario engine — recipe_scenarios table."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session

from app.config import settings
from app.models.recipe import Recipe
from app.models.recipe_engine import RecipeScenario
from app.models.user import User
from app.services.app_scope import AppScope
from app.services.recipes.repositories.scenarios import RecipeScenarioRepository


class ScenarioType(str, Enum):
    QUICK = "quick"
    ULTRA_QUICK = "ultra_quick"
    CHEAP = "cheap"
    KIDS_LOVED = "kids_loved"
    LOSE_WEIGHT = "lose_weight"
    GAIN_WEIGHT = "gain_weight"
    GUESTS = "guests"
    HOLIDAY = "holiday"
    WORK_LUNCH = "work_lunch"
    TRAVEL = "travel"
    FROM_PANTRY = "from_pantry"
    ALMOST_NO_COOKING = "almost_no_cooking"


AUTO_SCENARIOS = {
    ScenarioType.QUICK,
    ScenarioType.ULTRA_QUICK,
    ScenarioType.CHEAP,
    ScenarioType.KIDS_LOVED,
    ScenarioType.LOSE_WEIGHT,
    ScenarioType.GAIN_WEIGHT,
    ScenarioType.GUESTS,
    ScenarioType.HOLIDAY,
    ScenarioType.WORK_LUNCH,
    ScenarioType.TRAVEL,
    ScenarioType.ALMOST_NO_COOKING,
}


@dataclass(frozen=True)
class ScenarioMatchResult:
    scenario: ScenarioType
    matched: bool = False
    note: str | None = None


class ScenarioMatcher:
    """Deterministic scenario rules (no AI)."""

    def match_recipe(self, recipe: Recipe, scenario: ScenarioType) -> ScenarioMatchResult:
        minutes = recipe.cooking_time_minutes or recipe.prep_time_minutes or 30
        diets = [str(d).lower() for d in (recipe.diets or [])]
        tags = [str(t).lower() for t in (recipe.tags or [])]

        matched = False
        note: str | None = None

        if scenario == ScenarioType.QUICK:
            matched = minutes <= 25
            note = "до 25 минут" if matched else None
        elif scenario == ScenarioType.ULTRA_QUICK:
            matched = minutes <= 15
            note = "до 15 минут" if matched else None
        elif scenario == ScenarioType.CHEAP:
            matched = "budget" in diets or recipe.category == "quick"
            note = "экономное" if matched else None
        elif scenario == ScenarioType.KIDS_LOVED:
            matched = bool(recipe.suitable_for_children) or recipe.category == "kids"
            note = "для детей" if matched else None
        elif scenario == ScenarioType.LOSE_WEIGHT:
            cal = recipe.calories_per_serving
            matched = cal is not None and cal <= 450
            if not matched and "low_sugar" in diets:
                matched = True
            note = "для похудения" if matched else None
        elif scenario == ScenarioType.GAIN_WEIGHT:
            cal = recipe.calories_per_serving or 0
            protein = recipe.protein_g or 0
            matched = cal >= 500 or protein >= 25 or bool(recipe.suitable_for_sport)
            note = "для набора массы" if matched else None
        elif scenario == ScenarioType.GUESTS:
            matched = (recipe.servings or 0) >= 6 or bool(recipe.suitable_for_event)
            note = "для гостей" if matched else None
        elif scenario == ScenarioType.HOLIDAY:
            matched = bool(recipe.suitable_for_event) or "event" in tags
            note = "праздничное" if matched else None
        elif scenario == ScenarioType.WORK_LUNCH:
            matched = recipe.meal_type in ("lunch", "snack") and minutes <= 45
            note = "на работу" if matched else None
        elif scenario == ScenarioType.TRAVEL:
            matched = recipe.category in ("snack", "salad") or "portable" in tags
            note = "в дорогу" if matched else None
        elif scenario == ScenarioType.ALMOST_NO_COOKING:
            matched = minutes <= 10 or recipe.category == "quick"
            note = "минимум готовки" if matched else None
        elif scenario == ScenarioType.FROM_PANTRY:
            matched = False
            note = "определяется запасами отдельно"

        return ScenarioMatchResult(scenario=scenario, matched=matched, note=note)

    def match(
        self,
        *,
        scenario: ScenarioType,
        recipe_id: int,
        user: User,
        scope: AppScope | None = None,
    ) -> ScenarioMatchResult:
        _ = (recipe_id, user, scope)
        return ScenarioMatchResult(scenario=scenario, matched=False)


class ScenarioService:
    def __init__(self, db: Session, matcher: ScenarioMatcher | None = None) -> None:
        self._db = db
        self._matcher = matcher or ScenarioMatcher()
        self._repo = RecipeScenarioRepository(db)

    def recompute_for_recipe(self, recipe: Recipe) -> list[RecipeScenario]:
        if not settings.recipe_scenarios:
            return []

        self._repo.delete_for_recipe(recipe.id, source="auto")
        saved: list[RecipeScenario] = []
        for scenario in AUTO_SCENARIOS:
            result = self._matcher.match_recipe(recipe, scenario)
            if not result.matched:
                continue
            row = RecipeScenario(
                recipe_id=recipe.id,
                scenario=scenario.value,
                score=1.0,
                source="auto",
            )
            saved.append(self._repo.upsert(row))

        self._db.commit()
        return saved

    def list_for_recipe(self, recipe_id: int) -> list[RecipeScenario]:
        if not settings.recipe_scenarios:
            return []
        return self._repo.list_for_recipe(recipe_id)

    def match_any(
        self,
        *,
        recipe_id: int,
        scenarios: list[ScenarioType],
        user: User,
        scope: AppScope | None = None,
    ) -> list[ScenarioMatchResult]:
        if not settings.recipe_scenarios:
            return [ScenarioMatchResult(scenario=sc, matched=False) for sc in scenarios]

        recipe = self._db.get(Recipe, recipe_id)
        if recipe is None:
            return [ScenarioMatchResult(scenario=sc, matched=False) for sc in scenarios]

        _ = (user, scope)
        return [self._matcher.match_recipe(recipe, sc) for sc in scenarios]
