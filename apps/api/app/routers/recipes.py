from datetime import date

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user, is_admin_user
from app.schemas.menu_overview import (
    AddRecipeToMenuRequest,
    AddRecipeToMenuResponse,
    ApplyRecipeImproveRequest,
    MenuPlanItem,
    RecipeEvaluationResponse,
    RecipeFamilyCompatibilityResponse,
    RecipeImproveResponse,
)
from app.schemas.recipe import (
    AddRecipeToShoppingRequest,
    FavoriteToggleResponse,
    RecipeCreateRequest,
    RecipeDetail,
    RecipeFiltersResponse,
    RecipeListResponse,
    RecipeRecommendationsResponse,
    RecipeUpdateRequest,
)
from app.config import settings
from app.routers.recipe_engine_common import require_feature
from app.schemas.recipe_engine_api import (
    CookingEventResponse,
    CookingStatsResponse,
    FromPantryListResponse,
    FromPantryRecipeItem,
    MarkCookedRequest,
    RecipeHistoryListResponse,
    RecipeRateRequest,
    RecipeRateResponse,
    RecipeSummaryRef,
    RecipeScenariosListResponse,
    RecipeWhyResponse,
    RecommendationReasonResponse,
    ScenarioListItemResponse,
)
from app.services import recipe_analysis
from app.services.app_scope import AppScope
from app.services.pantry import get_active_items_for_scope
from app.services.recipe_storage import get_structured_ingredients
from app.services import recipes as recipes_service
from app.services.recipes.cooking_history import (
    CookingEvent,
    CookingHistoryService,
    HistoryTypes,
)
from app.services.recipes.explainability import ExplainabilityService
from app.services.recipes.family_preferences import FamilyPreferenceService
from app.services.recipes.access import assert_can_create_recipe, assert_can_update_recipe
from app.services.recipes.scenarios import ScenarioService, ScenarioType
from app.models.user import User

router = APIRouter(prefix="/recipes", tags=["recipes"])
logger = logging.getLogger(__name__)


def _to_why_response(result) -> RecipeWhyResponse:
    return RecipeWhyResponse(
        recipe_id=result.recipe_id,
        summary=result.summary,
        positives=[
            RecommendationReasonResponse(
                code=entry.reason,
                label=entry.label,
                kind=entry.kind,
                weight=entry.weight,
            )
            for entry in result.positives
        ],
        warnings=[
            RecommendationReasonResponse(
                code=entry.reason,
                label=entry.label,
                kind=entry.kind,
                weight=entry.weight,
            )
            for entry in result.warnings
        ],
        hard_blocks=[
            RecommendationReasonResponse(
                code=entry.reason,
                label=entry.label,
                kind=entry.kind,
                weight=entry.weight,
            )
            for entry in result.hard_blocks
        ],
        score_total=result.score_total,
    )


def _to_cooking_event_response(event: CookingEvent) -> CookingEventResponse:
    return CookingEventResponse(
        id=event.id or 0,
        recipe_id=event.recipe_id,
        cooked_on=event.cooked_on,
        servings=event.servings,
        source=event.source.value,
        notes=event.notes,
        user_id=event.user_id,
        family_id=event.family_id,
        family_member_id=event.family_member_id,
    )


def _normalized_ingredient_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _ingredient_in_pantry(name: str, pantry_names: set[str]) -> bool:
    normalized = _normalized_ingredient_name(name)
    if not normalized:
        return False
    return any(
        item == normalized or item in normalized or normalized in item
        for item in pantry_names
    )


@router.get("/filters", response_model=RecipeFiltersResponse)
def get_recipe_filters(
    include_legacy: bool = Query(default=False),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> RecipeFiltersResponse:
    legacy = include_legacy and is_admin_user(user)
    return recipes_service.get_filters(db, include_legacy=legacy)


@router.get("/recommendations", response_model=RecipeRecommendationsResponse)
def recipe_recommendations(
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> RecipeRecommendationsResponse:
    return recipes_service.get_recommendations(db, user, scope)


@router.post("", response_model=RecipeDetail)
def create_recipe(
    payload: RecipeCreateRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> RecipeDetail:
    assert_can_create_recipe(user, payload)
    return recipes_service.create_recipe(db, payload, user=user)


@router.get("", response_model=RecipeListResponse)
def list_recipes(
    q: str | None = Query(default=None, max_length=120),
    search: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    meal_type: str | None = Query(default=None),
    category: str | None = Query(default=None),
    diet: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    max_prep_time: int | None = Query(default=None, ge=5, le=300),
    favorites_only: bool = Query(default=False),
    from_pantry: bool = Query(default=False),
    for_children: bool = Query(default=False),
    for_sport: bool = Query(default=False),
    for_event: bool = Query(default=False),
    drinks_only: bool = Query(default=False),
    non_alcoholic: bool = Query(default=False),
    alcoholic_only: bool = Query(default=False),
    protein_only: bool = Query(default=False),
    smoothie_only: bool = Query(default=False),
    tea_coffee_only: bool = Query(default=False),
    exclude_allergens: str | None = Query(default=None),
    goal: str | None = Query(default=None),
    scenario: str | None = Query(default=None),
    include_legacy: bool = Query(default=False),
    sort: str | None = Query(
        default=None,
        description="Catalog sort: default quality-first; use title for legacy A-Z",
    ),
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> RecipeListResponse:
    query_text = (q or search or "").strip() or None
    legacy = include_legacy and is_admin_user(user)
    logger.info(
        "GET /recipes q=%r search=%r limit=%d offset=%d meal_type=%r scenario=%r user=%s",
        q,
        search,
        limit,
        offset,
        meal_type,
        scenario,
        user.id,
    )
    if scenario:
        require_feature(settings.recipe_scenarios, "RECIPE_SCENARIOS")
        try:
            scenario = ScenarioType(scenario).value
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unknown recipe scenario",
            ) from exc

    result = recipes_service.list_recipes(
        db,
        user,
        q=query_text,
        meal_type=meal_type or None,
        category=category or None,
        diet=diet or None,
        difficulty=difficulty or None,
        max_prep_time=max_prep_time,
        favorites_only=favorites_only,
        from_pantry=from_pantry,
        for_children=for_children,
        for_sport=for_sport,
        for_event=for_event,
        drinks_only=drinks_only,
        non_alcoholic=non_alcoholic,
        alcoholic_only=alcoholic_only,
        protein_only=protein_only,
        smoothie_only=smoothie_only,
        tea_coffee_only=tea_coffee_only,
        exclude_allergens=exclude_allergens,
        goal=goal,
        scenario=scenario,
        scope=scope,
        limit=limit,
        offset=offset,
        include_legacy=legacy,
        sort=sort,
    )
    logger.info("GET /recipes -> total=%d", result.total)
    return result


@router.get("/history", response_model=RecipeHistoryListResponse)
def recipe_history(
    limit: int = Query(default=50, ge=1, le=200),
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> RecipeHistoryListResponse:
    require_feature(settings.recipe_history, "RECIPE_HISTORY")
    events = CookingHistoryService(db).list_scope_events(
        user=user, scope=scope, limit=limit
    )
    return RecipeHistoryListResponse(
        items=[_to_cooking_event_response(event) for event in events],
        total=len(events),
    )


@router.get("/from-pantry", response_model=FromPantryListResponse)
def recipes_from_pantry(
    max_missing: int = Query(default=3, ge=0, le=20),
    limit: int = Query(default=30, ge=1, le=100),
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> FromPantryListResponse:
    _ = user
    pantry_names = {
        _normalized_ingredient_name(item.name)
        for item in get_active_items_for_scope(db, scope)
        if item.name
    }
    if not pantry_names:
        return FromPantryListResponse(items=[], total=0)

    candidates = recipes_service.list_recipes(db, user, scope=scope).items
    rows: list[FromPantryRecipeItem] = []
    for summary in candidates:
        recipe = recipes_service.get_recipe_model(db, summary.id)
        if recipe is None:
            continue

        ingredients = [
            str(item.get("name", "")).strip()
            for item in get_structured_ingredients(recipe)
            if str(item.get("name", "")).strip()
        ]
        total = len(ingredients)
        if total == 0:
            continue

        missing = [
            name
            for name in ingredients
            if not _ingredient_in_pantry(name, pantry_names)
        ]
        have = total - len(missing)
        if have <= 0 or len(missing) > max_missing:
            continue

        rows.append(
            FromPantryRecipeItem(
                recipe_id=summary.id,
                title=summary.title,
                have=have,
                total=total,
                missing_ingredients=missing,
                coverage_ratio=round(have / total, 3),
                summary=RecipeSummaryRef(
                    id=summary.id,
                    title=summary.title,
                    meal_type=summary.meal_type,
                    category=summary.category,
                    cooking_time_minutes=summary.cooking_time_minutes,
                ),
            )
        )

    rows.sort(key=lambda item: (-item.coverage_ratio, len(item.missing_ingredients), item.title))
    return FromPantryListResponse(items=rows[:limit], total=len(rows))


@router.get("/scenarios", response_model=RecipeScenariosListResponse)
def recipe_scenarios(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> RecipeScenariosListResponse:
    _ = user
    require_feature(settings.recipe_scenarios, "RECIPE_SCENARIOS")
    items = [
        ScenarioListItemResponse(
            scenario=scenario.value,
            label=label,
            recipes_count=count,
            active=True,
        )
        for scenario, label, count in ScenarioService(db).list_available()
    ]
    return RecipeScenariosListResponse(items=items)


@router.patch("/{recipe_id}", response_model=RecipeDetail)
def patch_recipe(
    recipe_id: int,
    payload: RecipeUpdateRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> RecipeDetail:
    from app.services.recipes import repository as recipe_repository

    recipe = recipe_repository.get_recipe_by_id(db, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    assert_can_update_recipe(user, recipe, payload)
    result = recipes_service.update_recipe(db, recipe_id, payload)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return result


@router.get("/{recipe_id}", response_model=RecipeDetail)
def get_recipe(
    recipe_id: int,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> RecipeDetail:
    recipe = recipes_service.get_recipe(db, user, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe


@router.get("/{recipe_id}/why", response_model=RecipeWhyResponse)
def recipe_why(
    recipe_id: int,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> RecipeWhyResponse:
    require_feature(settings.recipe_explainability, "RECIPE_EXPLAINABILITY")
    _recipe_or_404(db, user, recipe_id)
    result = ExplainabilityService(db).explain(recipe_id, user=user, scope=scope)
    return _to_why_response(result)


@router.post(
    "/{recipe_id}/cooked",
    response_model=CookingEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def mark_recipe_cooked(
    recipe_id: int,
    payload: MarkCookedRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> CookingEventResponse:
    require_feature(settings.recipe_history, "RECIPE_HISTORY")
    _recipe_or_404(db, user, recipe_id)
    event = CookingHistoryService(db).mark_cooked(
        event=CookingEvent(
            recipe_id=recipe_id,
            cooked_on=payload.cooked_on or date.today(),
            servings=payload.servings,
            source=HistoryTypes(payload.source),
            notes=payload.notes,
            family_member_id=payload.family_member_id,
        ),
        user=user,
        scope=scope,
    )
    return _to_cooking_event_response(event)


@router.get("/{recipe_id}/history", response_model=RecipeHistoryListResponse)
def recipe_history_for_recipe(
    recipe_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> RecipeHistoryListResponse:
    require_feature(settings.recipe_history, "RECIPE_HISTORY")
    _recipe_or_404(db, user, recipe_id)
    service = CookingHistoryService(db)
    events = service.list_events(recipe_id=recipe_id, user=user, scope=scope, limit=limit)
    stats = service.get_stats(recipe_id=recipe_id, user=user, scope=scope)
    return RecipeHistoryListResponse(
        items=[_to_cooking_event_response(event) for event in events],
        total=len(events),
        stats=CookingStatsResponse(
            recipe_id=recipe_id,
            cooked_count=stats.cooked_count,
            last_cooked_on=stats.last_cooked_on,
        ),
    )


@router.post("/{recipe_id}/rate", response_model=RecipeRateResponse)
def rate_recipe_for_family(
    recipe_id: int,
    payload: RecipeRateRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> RecipeRateResponse:
    require_feature(settings.family_recipe_preferences, "FAMILY_RECIPE_PREFERENCES")
    _recipe_or_404(db, user, recipe_id)
    if scope.family_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Family recipe preferences require family scope",
        )

    member = db.get(FamilyMember, payload.family_member_id)
    if member is None or member.family_id != scope.family_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family member not found",
        )

    liked = bool(payload.liked)
    disliked = bool(payload.disliked)
    is_loved = bool(payload.is_loved)
    if payload.rating == "loved":
        liked, disliked, is_loved = True, False, True
    elif payload.rating == "liked":
        liked, disliked, is_loved = True, False, False
    elif payload.rating == "disliked":
        liked, disliked, is_loved = False, True, False

    saved = FamilyPreferenceService(db).set_preference(
        recipe_id=recipe_id,
        family_id=scope.family_id,
        family_member_id=payload.family_member_id,
        liked=liked,
        disliked=disliked,
        is_loved=is_loved,
        note=payload.note,
    )
    return RecipeRateResponse(
        recipe_id=saved.recipe_id,
        family_member_id=saved.family_member_id,
        liked=saved.liked,
        disliked=saved.disliked,
        is_loved=saved.is_loved,
        note=saved.note,
    )


@router.post("/{recipe_id}/favorite", response_model=FavoriteToggleResponse)
def toggle_recipe_favorite(
    recipe_id: int,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> FavoriteToggleResponse:
    result = recipes_service.toggle_favorite(db, user, recipe_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return result


def _recipe_or_404(db: Session, user: User, recipe_id: int):
    _ = user
    recipe = recipes_service.get_recipe_model(db, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe


@router.get("/{recipe_id}/evaluate", response_model=RecipeEvaluationResponse)
async def evaluate_recipe(
    recipe_id: int,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> RecipeEvaluationResponse:
    recipe = _recipe_or_404(db, user, recipe_id)
    return await recipe_analysis.evaluate_recipe(db, user, scope, recipe)


@router.get("/{recipe_id}/family-compatibility", response_model=RecipeFamilyCompatibilityResponse)
def recipe_family_compatibility(
    recipe_id: int,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> RecipeFamilyCompatibilityResponse:
    recipe = _recipe_or_404(db, user, recipe_id)
    return recipe_analysis.family_compatibility(db, user, scope, recipe)


@router.get("/{recipe_id}/improve", response_model=RecipeImproveResponse)
async def improve_recipe_suggestions(
    recipe_id: int,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> RecipeImproveResponse:
    recipe = _recipe_or_404(db, user, recipe_id)
    return await recipe_analysis.suggest_improvements(db, user, scope, recipe)


@router.post("/{recipe_id}/improve", response_model=RecipeImproveResponse)
async def apply_recipe_improve(
    recipe_id: int,
    payload: ApplyRecipeImproveRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> RecipeImproveResponse:
    recipe = _recipe_or_404(db, user, recipe_id)
    return await recipe_analysis.apply_improvements(db, user, scope, recipe, payload)


@router.post("/{recipe_id}/add-to-shopping", status_code=status.HTTP_204_NO_CONTENT)
def add_recipe_to_shopping(
    recipe_id: int,
    payload: AddRecipeToShoppingRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> None:
    recipe = _recipe_or_404(db, user, recipe_id)
    recipes_service.add_recipe_to_shopping(
        db, user, scope, recipe, servings=payload.servings
    )


@router.post("/{recipe_id}/add-to-menu", response_model=AddRecipeToMenuResponse)
def add_recipe_to_menu(
    recipe_id: int,
    payload: AddRecipeToMenuRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> AddRecipeToMenuResponse:
    from app.services.menu_recipe_plan import add_recipe_to_plan

    recipe = _recipe_or_404(db, user, recipe_id)
    plan_date = payload.date or date.today().isoformat()
    try:
        item_dict, menu, created = add_recipe_to_plan(
            db,
            user,
            scope,
            recipe,
            plan_date=plan_date,
            meal_type=payload.meal_type,
            servings=payload.servings,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return AddRecipeToMenuResponse(
        item=MenuPlanItem(**item_dict),
        created=created,
        menu=menu,
    )
