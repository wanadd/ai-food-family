import logging

from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.menu import MenuIngredient, MenuMeal, MenuVariant
from app.schemas.menu_overview import (
    ApplyRecipeImproveRequest,
    RecipeEvaluationReason,
    RecipeEvaluationResponse,
    RecipeFamilyCompatibilityResponse,
    RecipeFamilyMemberFit,
    RecipeImproveResponse,
    RecipeImproveSuggestion,
)
from app.services import family as family_service
from app.services.app_scope import AppScope
from app.services.family_member_nutrition import member_is_virtual, virtual_nutrition_from_member
from app.services.menu import get_selected_menu, select_menu
from app.services.menu_context_fingerprint import compute_context_fingerprint
from app.services.onboarding import get_or_create_profile
from app.services.ai import analyze_recipe as ai_analyze_recipe
from app.services.ai import improve_recipe as ai_improve_recipe
from app.services.ai_context import build_ai_user_context
from app.services.ai_client import is_ai_configured
from app.services.ai_errors import AiError, AiUnavailableError
from app.services import subscription as subscription_service
from app.services.subscription_catalog import AMA_COSTS
from app.services.ai_client import current_model_name

logger = logging.getLogger(__name__)

ALLERGEN_KEYWORDS = {
    "молок": "dairy",
    "сыр": "dairy",
    "творог": "dairy",
    "яйц": "eggs",
    "орех": "nuts",
    "арахис": "nuts",
    "глютен": "gluten",
    "пшениц": "gluten",
    "рыб": "fish",
    "кревет": "shellfish",
    "соя": "soy",
    "шоколад": "other",
}


def _ingredient_text(recipe: Recipe) -> str:
    from app.services.recipe_storage import get_structured_ingredients

    parts = [recipe.title, recipe.description or ""]
    for ing in get_structured_ingredients(recipe):
        parts.append(str(ing.get("name", "")))
    if recipe.is_alcoholic:
        parts.append("алкоголь")
    if recipe.caffeine_mg:
        parts.append("кофеин")
    if recipe.sugar_g and recipe.sugar_g > 15:
        parts.append("сахар")
    return " ".join(parts).lower()


def _profile_allergies(profile) -> set[str]:
    raw = profile.allergies or []
    return {str(a).lower() for a in raw}


def _member_allergies(db: Session, member) -> set[str]:
    if member_is_virtual(member):
        n = virtual_nutrition_from_member(member)
        return {str(a).lower() for a in (n.allergies or [])}
    if member.user_id:
        return _profile_allergies(get_or_create_profile(db, member.user))
    return set()


async def evaluate_recipe(
    db: Session, user: User, scope: AppScope, recipe: Recipe
) -> RecipeEvaluationResponse:
    if is_ai_configured():
        try:
            ams = subscription_service.require_ai_action(
                db,
                user,
                scope,
                "recipe_analyze",
                ama_cost=AMA_COSTS["recipe_analyze"],
            )
            ai_ctx = build_ai_user_context(db, user, scope)
            result = await ai_analyze_recipe(recipe, ai_ctx)
            subscription_service.log_ai_usage(
                db,
                user_id=user.id,
                family_id=scope.family_id,
                action_type="recipe_analyze",
                ams_spent=ams,
                model=current_model_name(),
                metadata={"recipe_id": recipe.id},
            )
            return result
        except AiUnavailableError:
            pass
        except AiError:
            logger.exception("AI recipe analyze failed")
        except Exception:
            logger.exception("AI recipe analyze failed")

    return _evaluate_recipe_heuristic(db, user, scope, recipe)


def _evaluate_recipe_heuristic(
    db: Session, user: User, scope: AppScope, recipe: Recipe
) -> RecipeEvaluationResponse:
    profile = get_or_create_profile(db, user)
    text = _ingredient_text(recipe)
    reasons: list[RecipeEvaluationReason] = []
    fit = "good"

    user_allergies = _profile_allergies(profile)
    for allergen in user_allergies:
        for kw, code in ALLERGEN_KEYWORDS.items():
            if allergen in code or allergen in kw:
                if kw in text:
                    reasons.append(
                        RecipeEvaluationReason(
                            code="allergen",
                            label=f"Возможный аллерген ({allergen})",
                        )
                    )
                    fit = "not_recommended"

    if "kids" in (recipe.diets or []) or recipe.category == "kids":
        if profile.nutrition_goal not in ("child", "kids"):
            pass
    elif recipe.category == "kids" and profile.nutrition_goal not in ("child", "kids"):
        reasons.append(
            RecipeEvaluationReason(code="kids", label="Рецепт для детей")
        )

    if profile.nutrition_goal == "lose":
        if any(w in text for w in ("сахар", "мёд", "мед ", "сироп", "торт")):
            reasons.append(
                RecipeEvaluationReason(code="sugar", label="Много сахара для похудения")
            )
            if fit == "good":
                fit = "partial"
        if "жирн" in text or recipe.category == "dessert":
            reasons.append(
                RecipeEvaluationReason(
                    code="calories", label="Высокая калорийность"
                )
            )
            if fit == "good":
                fit = "partial"

    if profile.nutrition_goal in ("sport", "gain"):
        has_protein = any(
            w in text for w in ("куриц", "индейк", "яйц", "творог", "рыб", "мяс", "боб")
        )
        if not has_protein:
            reasons.append(
                RecipeEvaluationReason(code="protein", label="Мало белка")
            )
            if fit == "good":
                fit = "partial"

    banned = (profile.banned_foods or "").lower()
    if banned:
        for part in banned.split(","):
            part = part.strip()
            if part and part in text:
                reasons.append(
                    RecipeEvaluationReason(
                        code="banned", label=f"Содержит «{part}» из списка исключений"
                    )
                )
                fit = "not_recommended"

    if scope.is_family:
        family = family_service.get_family_for_user(db, user)
        if family:
            for member in family.members:
                if member_is_virtual(member) and member.virtual_kind == "child":
                    if any(w in text for w in ("остр", "перец", "вино", "кофе")):
                        reasons.append(
                            RecipeEvaluationReason(
                                code="child",
                                label=f"Не подходит ребёнку ({member.display_name})",
                            )
                        )
                        fit = "partial" if fit == "good" else fit

    title_map = {
        "good": "Подходит для вашей цели",
        "partial": "Подходит частично",
        "not_recommended": "Не рекомендуется",
    }
    if not reasons and fit == "good":
        reasons.append(
            RecipeEvaluationReason(
                code="ok", label="Соответствует профилю — решение за вами"
            )
        )

    return RecipeEvaluationResponse(
        fit_level=fit,  # type: ignore[arg-type]
        title=title_map[fit],
        reasons=reasons[:5],
    )


def family_compatibility(
    db: Session, user: User, scope: AppScope, recipe: Recipe
) -> RecipeFamilyCompatibilityResponse:
    members_out: list[RecipeFamilyMemberFit] = []
    text = _ingredient_text(recipe)

    if not scope.is_family:
        profile = get_or_create_profile(db, user)
        ev = _evaluate_recipe_heuristic(db, user, scope, recipe)
        status = "ok" if ev.fit_level == "good" else "warning"
        members_out.append(
            RecipeFamilyMemberFit(
                member_id=None,
                name=user.first_name or "Вы",
                status=status,
                note=ev.reasons[0].label if ev.reasons else "Подходит",
            )
        )
        return RecipeFamilyCompatibilityResponse(members=members_out)

    family = family_service.get_family_for_user(db, user)
    if not family:
        return RecipeFamilyCompatibilityResponse(members=[])

    for member in family.members:
        note = "подходит"
        status: str = "ok"
        allergies = _member_allergies(db, member)
        for allergen in allergies:
            for kw in ALLERGEN_KEYWORDS:
                if kw in text and (allergen in kw or allergen in ALLERGEN_KEYWORDS[kw]):
                    status = "warning"
                    note = "проверьте аллергены"
                    break

        if member_is_virtual(member):
            n = virtual_nutrition_from_member(member)
            if member.virtual_kind == "child":
                if any(w in text for w in ("соль", "колбас", "копчен")):
                    status = "warning"
                    note = "много соли для ребёнка"
                if "кальц" not in text and any(
                    w in text for w in ("суп", "овощ", "крупа")
                ):
                    status = "warning"
                    note = "мало кальция"
            if member.virtual_kind == "elder":
                if any(w in text for w in ("соль", "копчен", "маринован")):
                    status = "warning"
                    note = "много соли"

        members_out.append(
            RecipeFamilyMemberFit(
                member_id=member.id,
                name=member.display_name,
                status=status,  # type: ignore[arg-type]
                note=note,
            )
        )

    return RecipeFamilyCompatibilityResponse(members=members_out)


async def suggest_improvements(
    db: Session, user: User, scope: AppScope, recipe: Recipe
) -> RecipeImproveResponse:
    if is_ai_configured():
        try:
            ai_ctx = build_ai_user_context(db, user, scope)
            return await ai_improve_recipe(recipe, ai_ctx)
        except (AiUnavailableError, AiError):
            logger.exception("AI recipe improve suggestions failed")

    return _suggest_improvements_heuristic(db, user, scope, recipe)


def _suggest_improvements_heuristic(
    db: Session, user: User, scope: AppScope, recipe: Recipe
) -> RecipeImproveResponse:
    profile = get_or_create_profile(db, user)
    text = _ingredient_text(recipe)
    suggestions: list[RecipeImproveSuggestion] = []

    if profile.nutrition_goal == "lose":
        suggestions.append(
            RecipeImproveSuggestion(
                id="less_calories",
                label="Уменьшить калорийность",
                description="Меньше масла и сахара, больше овощей.",
            )
        )
    if profile.nutrition_goal in ("sport", "gain"):
        suggestions.append(
            RecipeImproveSuggestion(
                id="more_protein",
                label="Увеличить белок",
                description="Добавить яйца, творог или нежирное мясо.",
            )
        )
    if any(w in text for w in ("сахар", "мёд", "сироп")):
        suggestions.append(
            RecipeImproveSuggestion(
                id="less_sugar",
                label="Уменьшить сахар",
                description="Заменить сладости на фрукты или меньше подсластителя.",
            )
        )
    if _profile_allergies(profile):
        suggestions.append(
            RecipeImproveSuggestion(
                id="remove_allergen",
                label="Убрать аллерген",
                description="Подобрать безопасную замену ингредиента.",
            )
        )
    suggestions.append(
        RecipeImproveSuggestion(
            id="use_pantry",
            label="Использовать запасы",
            description="Заменить покупки продуктами из холодильника.",
        )
    )
    suggestions.append(
        RecipeImproveSuggestion(
            id="cheaper",
            label="Сделать дешевле",
            description="Упростить состав без потери сытости.",
        )
    )

    return RecipeImproveResponse(
        suggestions=suggestions[:6],
        improved_title=None,
        improved_ingredients=None,
        improved_steps=None,
    )


async def apply_improvements(
    db: Session,
    user: User,
    scope: AppScope,
    recipe: Recipe,
    payload: ApplyRecipeImproveRequest,
) -> RecipeImproveResponse:
    if is_ai_configured():
        try:
            ams = subscription_service.require_ai_action(
                db,
                user,
                scope,
                "recipe_improve",
                ama_cost=AMA_COSTS["recipe_improve"],
            )
            ai_ctx = build_ai_user_context(db, user, scope)
            sid = payload.suggestion_ids[0] if payload.suggestion_ids else None
            result = await ai_improve_recipe(recipe, ai_ctx, suggestion_id=sid)
            subscription_service.log_ai_usage(
                db,
                user_id=user.id,
                family_id=scope.family_id,
                action_type="recipe_improve",
                ams_spent=ams,
                model=current_model_name(),
                metadata={"recipe_id": recipe.id},
            )
            if result.suggestions:
                chosen = [s for s in result.suggestions if s.id in payload.suggestion_ids]
                notes = "; ".join(s.description for s in chosen)
                ingredients = list(recipe.ingredients or [])
                steps = list(recipe.steps or [])
                if notes:
                    steps = [f"По совету нутрициолога: {notes}", *steps]
                return RecipeImproveResponse(
                    suggestions=chosen or result.suggestions[:3],
                    improved_title=f"{recipe.title} (улучшенный)",
                    improved_ingredients=ingredients,
                    improved_steps=steps,
                )
            return result
        except (AiUnavailableError, AiError):
            logger.exception("AI recipe improve apply failed")

    base = await suggest_improvements(db, user, scope, recipe)
    chosen = [s for s in base.suggestions if s.id in payload.suggestion_ids]
    notes = "; ".join(s.description for s in chosen)
    ingredients = list(recipe.ingredients or [])
    steps = list(recipe.steps or [])
    if notes:
        steps = [f"По совету нутрициолога: {notes}", *steps]
    return RecipeImproveResponse(
        suggestions=chosen,
        improved_title=f"{recipe.title} (улучшенный)",
        improved_ingredients=ingredients,
        improved_steps=steps,
    )


def add_recipe_to_menu(
    db: Session,
    user: User,
    scope: AppScope,
    recipe: Recipe,
    *,
    meal_type: str,
    replace_meal_index: int | None,
) -> MenuVariant:
    selected = get_selected_menu(db, scope)
    if selected is None:
        raise ValueError("Сначала выберите или сгенерируйте меню")

    menu = selected.menu
    meal = MenuMeal(
        meal_type=meal_type,  # type: ignore[arg-type]
        name=recipe.title,
        description=(recipe.description or "")[:500],
        prep_time_minutes=recipe.prep_time_minutes,
        calories_estimate=None,
    )
    ingredients = [
        MenuIngredient(
            name=str(i.get("name", "")),
            amount=str(i.get("amount", "")),
        )
        for i in (recipe.ingredients or [])
        if isinstance(i, dict)
    ]

    meals = list(menu.meals)
    idx = replace_meal_index
    if idx is None:
        for i, m in enumerate(meals):
            if m.meal_type == meal_type:
                idx = i
                break
    if idx is None or idx < 0 or idx >= len(meals):
        idx = min(1, len(meals) - 1)

    meals[idx] = meal
    updated = menu.model_copy(update={"meals": meals})
    if ingredients:
        merged = list(menu.ingredients)
        existing = {ing.name.lower() for ing in merged}
        for ing in ingredients:
            if ing.name.lower() not in existing:
                merged.append(ing)
        updated = updated.model_copy(update={"ingredients": merged})

    from app.schemas.menu import SelectMenuRequest
    from app.services.menu import _get_latest_selection, select_menu

    plan_mode = "healthy"
    persons_count = None
    row = _get_latest_selection(db, scope)
    if row and isinstance(row.menu_data, dict):
        meta = row.menu_data.get("_meta") or {}
        if isinstance(meta, dict):
            plan_mode = meta.get("plan_mode") or plan_mode
            persons_count = meta.get("persons_count")

    select_menu(
        db,
        user,
        scope,
        SelectMenuRequest(menu=updated),
        plan_mode=plan_mode,
        persons_count=persons_count,
    )
    return updated
