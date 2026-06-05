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
    recipe_id: int | None = None
    image_url: str | None = None


HomeNextActionId = Literal[
    "complete_nutrition",
    "generate_menu",
    "shopping",
    "use_pantry_item",
    "meal_outcome",
    "open_today",
]


class HomeNextAction(BaseModel):
    """Primary CTA for Home 2026 (rule engine P0–P5)."""

    id: HomeNextActionId
    cta_label: str
    redirect_path: str
    subtitle: str | None = None
    metadata: dict = Field(default_factory=dict)


class PantryExpiringPreview(BaseModel):
    name: str
    days_until_expiry: int


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
    next_action: HomeNextAction | None = None
    shopping_unchecked_count: int = 0
    pantry_expiring_preview: PantryExpiringPreview | None = None


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


class MenuPlanItem(BaseModel):
    slot_id: str
    date: str
    meal_type: str
    recipe_id: int | None = None
    name: str
    servings: int = 2
    prep_time_minutes: int = 0
    calories_estimate: int | None = None


class AddRecipeToMenuRequest(BaseModel):
    date: str | None = Field(default=None, max_length=10)
    meal_type: str = Field(default="lunch", max_length=16)
    servings: int | None = Field(default=None, ge=1, le=50)
    replace_meal_index: int | None = Field(default=None, ge=0)


class AddRecipeToMenuResponse(BaseModel):
    item: MenuPlanItem
    created: bool = True
    menu: MenuVariant


class MenuTodayResponse(BaseModel):
    date: str
    items: list[MenuPlanItem]
    menu: MenuVariant | None = None


class ReplaceMenuSlotRequest(BaseModel):
    recipe_id: int = Field(ge=1)
    servings: int | None = Field(default=None, ge=1, le=50)


class ReplaceMenuSlotResponse(BaseModel):
    item: MenuPlanItem
    menu: MenuVariant


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
