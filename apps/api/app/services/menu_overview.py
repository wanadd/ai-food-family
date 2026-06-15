import re

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.menu_overview import (
    MenuNutritionistAdvice,
    MenuOverviewResponse,
    MenuPlanSummary,
    MenuSettingsSummary,
    MenuWhyReason,
    ProGoalCoverage,
)
from app.services import family as family_service
from app.services.app_scope import AppScope
from app.services.family_member_nutrition import member_is_virtual, virtual_nutrition_from_member
from app.services.leftovers import count_active_prepared_dishes
from app.services.meal_leftovers import list_active_leftovers
from app.services.menu import _get_latest_selection
from app.services.menu_selection import get_selected_menu
from app.services.menu_context_fingerprint import (
    compute_context_fingerprint,
    get_stored_fingerprint,
)
from app.services.home_next_action import compute_home_next_action
from app.services.meal_attendance import (
    build_home_attendance_summary,
    enrich_today_meals_images,
    extract_today_meals,
)
from app.services.menu_labels import GOAL_LABELS, PLAN_MODE_PROMPT_HINTS
from app.services.onboarding import get_or_create_profile
from app.services.pantry import get_active_items_for_scope
from app.services.progress import user_has_pro

PLAN_MODE_LABELS = {
    "quick_simple": "Быстро и просто",
    "economy": "Экономно",
    "healthy": "Полезно",
    "sport": "Спорт",
    "family": "Семейное",
    "use_pantry": "Из запасов",
}

UPDATE_REASON_LABELS = {
    "profile": "Изменён профиль питания",
    "family_member": "Изменён профиль участника семьи",
    "pantry": "Обновлены запасы",
    "leftovers": "Добавлены остатки блюд",
    "persons": "Изменён состав семьи",
    "generic": "Изменились условия питания",
}


def _parse_cost_rub(text: str | None) -> int | None:
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


def _estimate_pantry_value(items) -> int:
    return min(800, max(120, len(items) * 35))


from app.services.menu_context_fingerprint import resolve_persons_count


def _goal_label(profile) -> str:
    from app.services.goal_details import format_measurable_goal_summary

    summary = format_measurable_goal_summary(profile)
    if summary:
        return summary

    key = profile.nutrition_goal or "healthy"
    return GOAL_LABELS.get(key) or NUTRITION_GOAL_FALLBACK.get(key, "Здоровое питание")


NUTRITION_GOAL_FALLBACK = {
    "maintain": "Поддержание веса",
    "lose": "Похудение",
    "gain": "Набор массы",
    "healthy": "Здоровое питание",
    "sport": "Спорт",
    "child": "Детское питание",
    "kids": "Детское питание",
}


def build_why_reasons(
    db: Session,
    user: User,
    scope: AppScope,
    *,
    has_menu: bool,
) -> list[MenuWhyReason]:
    profile = get_or_create_profile(db, user)
    pantry = get_active_items_for_scope(db, scope)
    leftovers = list_active_leftovers(db, scope)
    reasons: list[MenuWhyReason] = []

    goal = profile.nutrition_goal
    if goal:
        reasons.append(
            MenuWhyReason(
                text=f"цель «{_goal_label(profile).lower()}»",
                included=True,
            )
        )

    if scope.is_family:
        family = family_service.get_family_for_user(db, user)
        if family:
            for member in family.members:
                if member_is_virtual(member):
                    n = virtual_nutrition_from_member(member)
                    if n.allergies or n.custom_allergies:
                        reasons.append(
                            MenuWhyReason(
                                text=f"аллергию {member.display_name}",
                                included=has_menu,
                            )
                        )
                    if n.age_months is not None and member.virtual_kind == "child":
                        reasons.append(
                            MenuWhyReason(
                                text=f"возраст ребёнка ({member.display_name})",
                                included=has_menu,
                            )
                        )
                elif member.user_id and member.user_id != user.id:
                    mp = get_or_create_profile(db, member.user)
                    if mp.allergies:
                        reasons.append(
                            MenuWhyReason(
                                text=f"аллергию {member.display_name}",
                                included=has_menu,
                            )
                        )

    if pantry:
        reasons.append(
            MenuWhyReason(text="продукты из запасов", included=len(pantry) > 0)
        )
    if leftovers:
        reasons.append(
            MenuWhyReason(text="остатки готовых блюд", included=True)
        )

    pro = profile.pro_data or {}
    if pro.get("budget"):
        reasons.append(MenuWhyReason(text="бюджет семьи", included=True))
    if pro.get("cooking_time") or profile.dish_complexity:
        reasons.append(MenuWhyReason(text="время готовки", included=True))

    if not reasons:
        reasons.append(
            MenuWhyReason(text="ваш профиль питания", included=has_menu)
        )
    return reasons[:6]


def _detect_update_reason(
    db: Session,
    user: User,
    scope: AppScope,
    stored_meta: dict | None,
) -> str | None:
    if not stored_meta:
        return UPDATE_REASON_LABELS["generic"]
    stored_fp = stored_meta.get("context_fingerprint")
    if not stored_fp:
        return UPDATE_REASON_LABELS["generic"]
    current_fp = compute_context_fingerprint(
        db,
        user,
        scope,
        persons_count=stored_meta.get("persons_count"),
        plan_mode=stored_meta.get("plan_mode"),
    )
    if current_fp == stored_fp:
        return None
    if stored_meta.get("leftovers_count", 0) != len(list_active_leftovers(db, scope)):
        return UPDATE_REASON_LABELS["leftovers"]
    if scope.is_family:
        return UPDATE_REASON_LABELS["family_member"]
    return UPDATE_REASON_LABELS["profile"]


def build_nutritionist_advice(
    db: Session,
    user: User,
    scope: AppScope,
    *,
    has_menu: bool,
    menu_data: dict | None,
) -> MenuNutritionistAdvice:
    profile = get_or_create_profile(db, user)
    meta = (menu_data or {}).get("_meta") if menu_data else {}
    if not isinstance(meta, dict):
        meta = {}

    stored_fp = get_stored_fingerprint(menu_data or {})
    current_fp = compute_context_fingerprint(
        db,
        user,
        scope,
        persons_count=meta.get("persons_count"),
        plan_mode=meta.get("plan_mode"),
    )
    needs_update = has_menu and stored_fp and stored_fp != current_fp
    update_reason = _detect_update_reason(db, user, scope, meta) if needs_update else None

    if not has_menu:
        return MenuNutritionistAdvice(
            level="suggest_update",
            title="Составьте меню",
            body="ПланАм подберёт рацион с учётом целей и запасов — вы всегда можете изменить блюда сами.",
            freshness_status="no_menu",
            update_reason=None,
        )

    if needs_update:
        return MenuNutritionistAdvice(
            level="update_recommended",
            title="Рекомендация нутрициолога",
            body=(
                f"{update_reason or 'Изменились данные питания.'} "
                "Рекомендуется обновить меню, когда будете готовы."
            ),
            freshness_status="needs_update",
            update_reason=update_reason,
        )

    goal = profile.nutrition_goal
    if goal == "lose":
        return MenuNutritionistAdvice(
            level="suggest_update",
            title="Следите за белком",
            body="При похудении белок помогает сытости — при желании обновите меню с акцентом на белок.",
            freshness_status="current",
            update_reason=None,
        )

    if scope.is_family:
        family = family_service.get_family_for_user(db, user)
        if family:
            for member in family.members:
                if member_is_virtual(member) and member.virtual_kind == "child":
                    n = virtual_nutrition_from_member(member)
                    if n.age_months and n.age_months % 12 == 0:
                        return MenuNutritionistAdvice(
                            level="suggest_update",
                            title="Профиль ребёнка изменился",
                            body=f"У {member.display_name} обновился возраст — можно пересчитать рацион семьи.",
                            freshness_status="current",
                            update_reason=None,
                        )

    return MenuNutritionistAdvice(
        level="ok",
        title="Рацион соответствует целям",
        body=(
            "У семьи хороший баланс питания."
            if scope.is_family
            else "Текущий рацион соответствует вашим целям."
        ),
        freshness_status="current",
        update_reason=None,
    )


def build_pro_coverage(db: Session, user: User, scope: AppScope) -> ProGoalCoverage:
    profile = get_or_create_profile(db, user)
    pro = profile.pro_data or {}
    targets = pro.get("targets") or {}
    base = 72
    if profile.nutrition_goal == "sport":
        base = 85
    elif profile.nutrition_goal == "lose":
        base = 68
    protein = int(targets.get("protein_percent", base))
    fiber = int(targets.get("fiber_percent", max(55, base - 12)))
    calories = int(targets.get("calories_percent", base + 5))
    water = int(targets.get("water_percent", 70))
    if scope.is_family:
        protein = min(95, protein + 5)
        fiber = min(92, fiber + 3)
    return ProGoalCoverage(
        protein_percent=protein,
        fiber_percent=fiber,
        calories_percent=calories,
        water_percent=water,
    )


def get_menu_overview(db: Session, user: User, scope: AppScope) -> MenuOverviewResponse:
    profile = get_or_create_profile(db, user)
    selected = get_selected_menu(db, scope)
    persons = resolve_persons_count(db, user, scope)
    pantry_items = get_active_items_for_scope(db, scope)
    leftovers = list_active_leftovers(db, scope)

    meta: dict = {}
    menu_data = None
    selection_row = _get_latest_selection(db, scope)
    if selection_row and isinstance(selection_row.menu_data, dict):
        menu_data = selection_row.menu_data
        meta = menu_data.get("_meta") or {}
        if not isinstance(meta, dict):
            meta = {}

    plan_mode = meta.get("plan_mode") or "healthy"
    has_menu = selected is not None
    cost = _parse_cost_rub(selected.menu.estimated_daily_cost if selected else None)
    pantry_used = meta.get("pantry_used_rub") or (
        _estimate_pantry_value(pantry_items) if pantry_items else None
    )
    savings = meta.get("savings_rub") or pantry_used

    if scope.is_family:
        family = family_service.get_family_for_user(db, user)
        persons_label = (
            f"Семья: {len(family.members)} человек"
            if family
            else f"{persons} человек"
        )
    else:
        persons_label = "1 человек"

    plan_summary = MenuPlanSummary(
        goal_label=_goal_label(profile),
        persons_label=persons_label,
        plan_mode_label=PLAN_MODE_LABELS.get(plan_mode, "Сбалансированный"),
        estimated_cost_rub=cost,
        pantry_used_rub=pantry_used,
        savings_rub=savings,
        has_selected_menu=has_menu,
        menu_title=selected.menu.title if selected else None,
    )

    why = build_why_reasons(db, user, scope, has_menu=has_menu)
    advice_error: str | None = None
    try:
        advice = build_nutritionist_advice(
            db, user, scope, has_menu=has_menu, menu_data=menu_data
        )
    except Exception:
        advice = MenuNutritionistAdvice(
            level="suggest_update",
            title="Рекомендация нутрициолога",
            body="Совет временно недоступен — меню и действия работают как обычно.",
            freshness_status="current" if has_menu else "no_menu",
            update_reason=None,
        )
        advice_error = "nutritionist_unavailable"

    today_meals = extract_today_meals(menu_data) if menu_data else []
    if not today_meals and selected and getattr(selected.menu, "meals", None):
        meals_raw = [
            m.model_dump() if hasattr(m, "model_dump") else m
            for m in selected.menu.meals
        ]
        today_meals = extract_today_meals({"meals": meals_raw})
    today_meals = enrich_today_meals_images(db, today_meals)

    next_action, shopping_unchecked, pantry_preview = compute_home_next_action(
        db,
        user,
        scope,
        has_menu=has_menu,
        today_meal_count=len(today_meals),
    )

    home_attendance = build_home_attendance_summary(db, user, scope)
    settings_summary = MenuSettingsSummary(
        persons_count=persons,
        goal_label=_goal_label(profile),
        plan_mode_label=PLAN_MODE_LABELS.get(plan_mode, "Сбалансированный"),
        include_drinks=bool(meta.get("include_drinks", True)),
        use_pantry=plan_mode == "use_pantry" or bool(meta.get("use_pantry")),
    )
    is_pro = user_has_pro(db, user)

    return MenuOverviewResponse(
        plan_summary=plan_summary,
        why_reasons=why,
        nutritionist_advice=advice,
        selected_menu=selected,
        pro_coverage=build_pro_coverage(db, user, scope) if is_pro else None,
        is_pro=is_pro,
        persons_count=persons,
        plan_mode=plan_mode,
        meal_leftovers_count=len(leftovers),
        today_meals=today_meals,
        home_attendance=home_attendance,
        settings_summary=settings_summary,
        nutritionist_advice_error=advice_error,
        next_action=next_action,
        shopping_unchecked_count=shopping_unchecked,
        pantry_items_count=len(pantry_items),
        pantry_expiring_preview=pantry_preview,
        prepared_dishes_count=count_active_prepared_dishes(db, scope),
    )
