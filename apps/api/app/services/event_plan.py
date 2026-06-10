"""Event Plan MVP — party menus from recipe catalog."""

from __future__ import annotations

import random

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.event_plan import EventPlan
from app.models.recipe import Recipe
from app.models.user import User
from app.recipes.gold_filter import query_active_recipes
from app.schemas.event_plan import (
    EventPlanCreateRequest,
    EventPlanDetail,
    EventPlanListResponse,
    EventPlanSummary,
)
from app.schemas.menu import MenuIngredient
from app.services.app_scope import AppScope
from app.services.pantry import get_active_items_for_scope
from app.services.recipe_storage import (
    aggregate_ingredients_for_shopping,
    get_structured_ingredients,
    scale_ingredients,
)
from app.services import shopping_list as shopping_list_service


EVENT_TYPE_LABELS = {
    "holiday_dinner": "Праздничный ужин",
    "holiday_lunch": "Праздничный обед",
    "birthday": "День рождения",
    "picnic": "Пикник",
    "bbq": "Барбекю",
    "romantic": "Романтический ужин",
    "kids_party": "Детский праздник",
    "sport_event": "Спортивное мероприятие",
    "fasting": "Постное мероприятие",
    "corporate": "Корпоратив",
    "custom": "Свой сценарий",
}


def _filter_event_recipes(
    recipes: list[Recipe],
    payload: EventPlanCreateRequest,
) -> list[Recipe]:
    out: list[Recipe] = []
    for r in recipes:
        if not r.is_active:
            continue
        if payload.fasting_mode not in ("none", "") and "fasting" not in (
            r.diets or []
        ):
            restr = [x.restriction for x in r.restriction_rows] if r.restriction_rows else []
            if "fasting" not in restr and r.meal_type not in ("drink", "tea"):
                if payload.fasting_mode != "none" and not r.suitable_for_event:
                    continue
        if payload.event_type == "kids_party" and not r.suitable_for_children:
            continue
        if payload.event_type == "bbq" and r.category not in ("bbq", "main", "snack"):
            if not r.suitable_for_event:
                continue
        if not payload.alcohol_enabled and r.is_alcoholic:
            continue
        out.append(r)
    return out


def create_event_plan(
    db: Session,
    user: User,
    scope: AppScope,
    payload: EventPlanCreateRequest,
) -> EventPlanDetail:
    recipes = (
        query_active_recipes(db)
        .options(joinedload(Recipe.ingredient_rows))
        .all()
    )
    candidates = _filter_event_recipes(recipes, payload)
    if not candidates:
        candidates = [r for r in recipes if r.is_active and not r.is_alcoholic]

    rng = random.Random(payload.event_type)
    food = [r for r in candidates if not r.is_drink and r.meal_type in ("lunch", "dinner", "snack", "dessert")]
    drinks = [r for r in candidates if r.is_drink]

    picked_food = rng.sample(food, min(4, len(food))) if food else []
    picked_drinks: list[Recipe] = []
    if payload.drink_menu_mode != "none":
        pool = drinks
        if payload.drink_menu_mode == "non_alcoholic":
            pool = [d for d in drinks if not d.is_alcoholic]
        elif not payload.alcohol_enabled:
            pool = [d for d in drinks if not d.is_alcoholic]
        picked_drinks = rng.sample(pool, min(3, len(pool))) if pool else []

    guests = max(1, payload.guests_count)
    dishes: list[dict] = []
    raw_ingredients: list[dict] = []

    for recipe in picked_food + picked_drinks:
        scaled = scale_ingredients(recipe, guests)
        raw_ingredients.extend(scaled)
        dishes.append(
            {
                "recipe_id": recipe.id,
                "title": recipe.title,
                "meal_type": recipe.meal_type,
                "servings": guests,
            }
        )

    shopping = aggregate_ingredients_for_shopping(raw_ingredients)
    pantry_items = get_active_items_for_scope(db, scope)
    pantry_names = {p.name.lower() for p in pantry_items}

    shopping_lines: list[dict] = []
    for line in shopping:
        if any(p in line["name"].lower() for p in pantry_names):
            line = {**line, "from_pantry": True}
        shopping_lines.append(line)

    title = payload.title or EVENT_TYPE_LABELS.get(payload.event_type, "Событие")
    plan = EventPlan(
        user_id=user.id,
        family_id=scope.family_id if scope.is_family else None,
        title=title,
        event_type=payload.event_type,
        guests_count=guests,
        budget=payload.budget,
        theme=payload.theme,
        cuisine=payload.cuisine,
        religious_restriction=payload.religious_restriction,
        fasting_mode=payload.fasting_mode,
        drink_menu_mode=payload.drink_menu_mode,
        alcohol_enabled=payload.alcohol_enabled,
        kids_drinks_enabled=payload.kids_drinks_enabled,
        allergies_note=payload.allergies_note,
        plan_data={
            "dishes": dishes,
            "shopping": shopping_lines,
            "nutrition_note": (
                "ПланАм рекомендует сбалансировать горячее и салаты; "
                "учтите аллергии гостей."
            ),
        },
        estimated_cost_rub=guests * 450,
        status="ready",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _to_detail(plan)


def list_event_plans(db: Session, user: User, scope: AppScope) -> EventPlanListResponse:
    q = db.query(EventPlan).filter(EventPlan.user_id == user.id)
    if scope.is_family and scope.family_id:
        q = q.filter(EventPlan.family_id == scope.family_id)
    rows = q.order_by(EventPlan.created_at.desc()).limit(50).all()
    return EventPlanListResponse(
        items=[
            EventPlanSummary(
                id=p.id,
                title=p.title,
                event_type=p.event_type,
                guests_count=p.guests_count,
                status=p.status,
                created_at=p.created_at,
            )
            for p in rows
        ]
    )


def get_event_plan(db: Session, user: User, plan_id: int) -> EventPlanDetail | None:
    plan = db.get(EventPlan, plan_id)
    if plan is None or plan.user_id != user.id:
        return None
    return _to_detail(plan)


def create_shopping_from_event(
    db: Session, user: User, scope: AppScope, plan_id: int
) -> None:
    plan = db.get(EventPlan, plan_id)
    if plan is None or plan.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    lines = plan.plan_data.get("shopping") or []
    from app.schemas.menu import MenuVariant

    ingredients = [
        MenuIngredient(
            name=line["name"],
            amount=line["amount"],
            category=line.get("category"),
        )
        for line in lines
        if not line.get("from_pantry")
    ]
    menu = MenuVariant(
        variant="balanced",
        title=plan.title,
        explanation="Список покупок для события",
        total_prep_minutes=0,
        meals=[],
        ingredients=ingredients,
    )
    shopping_list_service.sync_from_menu(db, scope, menu, None)


def _to_detail(plan: EventPlan) -> EventPlanDetail:
    data = plan.plan_data or {}
    return EventPlanDetail(
        id=plan.id,
        title=plan.title,
        event_type=plan.event_type,
        guests_count=plan.guests_count,
        budget=plan.budget,
        theme=plan.theme,
        cuisine=plan.cuisine,
        religious_restriction=plan.religious_restriction,
        fasting_mode=plan.fasting_mode,
        drink_menu_mode=plan.drink_menu_mode,
        alcohol_enabled=plan.alcohol_enabled,
        kids_drinks_enabled=plan.kids_drinks_enabled,
        allergies_note=plan.allergies_note,
        dishes=data.get("dishes", []),
        shopping=data.get("shopping", []),
        nutrition_note=data.get("nutrition_note"),
        estimated_cost_rub=plan.estimated_cost_rub,
        status=plan.status,
        created_at=plan.created_at,
    )
