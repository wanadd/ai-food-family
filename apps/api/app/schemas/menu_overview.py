from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.menu import MenuVariant, SelectedMenuResponse

MenuFreshnessStatus = Literal["current", "needs_update", "no_menu"]
MenuRecommendationLevel = Literal["ok", "suggest_update", "update_recommended"]


class MenuPlanSummary(BaseModel):
    goal_label: str
    persons_label: str
    plan_mode_label: str
    estimated_cost_rub: int | None = None
    pantry_used_rub: int | None = None
    savings_rub: int | None = None
    has_selected_menu: bool = False
    menu_title: str | None = None


class MenuWhyReason(BaseModel):
    text: str
    included: bool = True


class MenuNutritionistAdvice(BaseModel):
    level: MenuRecommendationLevel
    title: str
    body: str
    freshness_status: MenuFreshnessStatus
    update_reason: str | None = None


class ProGoalCoverage(BaseModel):
    protein_percent: int
    fiber_percent: int
    calories_percent: int
    water_percent: int


class MenuQuickActionId(BaseModel):
    id: str


class MenuTodayMeal(BaseModel):
    meal_type: str
    label: str
    name: str | None = None


class MenuHomeAttendance(BaseModel):
    breakfast_home: int
    lunch_home: int
    dinner_home: int
    total_members: int


class MenuSettingsSummary(BaseModel):
    persons_count: int
    goal_label: str
    plan_mode_label: str
    include_drinks: bool = True
    use_pantry: bool = False


class MenuOverviewResponse(BaseModel):
    plan_summary: MenuPlanSummary
    why_reasons: list[MenuWhyReason]
    nutritionist_advice: MenuNutritionistAdvice
    selected_menu: SelectedMenuResponse | None = None
    pro_coverage: ProGoalCoverage | None = None
    is_pro: bool = False
    persons_count: int = 1
    plan_mode: str | None = None
    meal_leftovers_count: int = 0
    today_meals: list[MenuTodayMeal] = Field(default_factory=list)
    home_attendance: MenuHomeAttendance | None = None
    settings_summary: MenuSettingsSummary | None = None
    nutritionist_advice_error: str | None = None


class MenuQuickActionRequest(BaseModel):
    action: Literal[
        "cheaper",
        "more_pantry",
        "more_protein",
        "less_cooking_time",
        "replace_dish",
    ]


class MenuQuickActionResponse(BaseModel):
    action: str
    redirect_path: str | None = None
    selected_menu: SelectedMenuResponse | None = None
    message: str | None = None


class AddRecipeToMenuRequest(BaseModel):
    meal_type: str = Field(default="lunch", max_length=16)
    replace_meal_index: int | None = Field(default=None, ge=0)


RecipeFitLevel = Literal["good", "partial", "not_recommended"]


class RecipeEvaluationReason(BaseModel):
    code: str
    label: str


class RecipeEvaluationResponse(BaseModel):
    fit_level: RecipeFitLevel
    title: str
    reasons: list[RecipeEvaluationReason]


class RecipeFamilyMemberFit(BaseModel):
    member_id: int | None = None
    name: str
    status: Literal["ok", "warning"]
    note: str


class RecipeFamilyCompatibilityResponse(BaseModel):
    members: list[RecipeFamilyMemberFit]


class RecipeImproveSuggestion(BaseModel):
    id: str
    label: str
    description: str


class RecipeImproveResponse(BaseModel):
    suggestions: list[RecipeImproveSuggestion]
    improved_title: str | None = None
    improved_ingredients: list[dict] | None = None
    improved_steps: list[str] | None = None


class ApplyRecipeImproveRequest(BaseModel):
    suggestion_ids: list[str] = Field(min_length=1, max_length=6)
