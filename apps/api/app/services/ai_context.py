"""Build rich prompts for PlanAm AI (menu, nutritionist, bot, recipes)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.user import User
from app.services.app_scope import AppScope
from app.services.meal_leftovers import (
    format_meal_leftovers_for_prompt,
    list_active_leftovers,
)
from app.services.menu_context import build_menu_context
from app.services.menu_context import MenuGenerationContext
from app.services.onboarding import get_or_create_profile
from app.services.pantry import format_leftovers_for_prompt, get_active_items_for_scope
from app.services.recipe_storage import get_structured_ingredients
from app.services.menu_selection import get_selected_menu
from app.services.progress import user_has_pro


@dataclass
class AiUserContext:
    scope_mode: str
    prompt_text: str
    profile_summary: str
    family_summary: str
    pantry_summary: str
    meal_leftovers_summary: str
    menu_summary: str
    recipe_catalog: list[dict[str, Any]] = field(default_factory=list)
    persons_count: int = 1
    drink_mode: str = "none"
    allow_alcohol: bool = False
    is_pro: bool = False
    event_mode: dict[str, Any] | None = None
    extras: dict[str, Any] = field(default_factory=dict)


def _recipe_catalog_slice(db: Session, *, limit: int = 40) -> list[dict[str, Any]]:
    rows = (
        db.query(Recipe)
        .filter(Recipe.is_active.is_(True))
        .order_by(Recipe.title.asc())
        .limit(limit)
        .all()
    )
    catalog: list[dict[str, Any]] = []
    for r in rows:
        catalog.append(
            {
                "id": r.id,
                "title": r.title,
                "meal_type": r.meal_type,
                "is_drink": bool(r.is_drink),
                "is_alcoholic": bool(r.is_alcoholic),
                "suitable_for_children": bool(r.suitable_for_children),
                "suitable_for_sport": bool(r.suitable_for_sport),
                "calories_per_serving": r.calories_per_serving,
                "cooking_time_minutes": r.cooking_time_minutes,
            }
        )
    return catalog


def build_ai_user_context(
    db: Session,
    user: User,
    scope: AppScope,
    *,
    menu_ctx: MenuGenerationContext | None = None,
    persons_count: int | None = None,
    drink_mode: str = "none",
    allow_alcohol: bool = False,
    event_mode: dict[str, Any] | None = None,
) -> AiUserContext:
    menu_ctx = menu_ctx or build_menu_context(db, user, scope)
    profile = get_or_create_profile(db, user)
    pantry = get_active_items_for_scope(db, scope)
    cooked = list_active_leftovers(db, scope)
    selected = get_selected_menu(db, scope)

    pantry_lines = format_leftovers_for_prompt(pantry) if pantry else ["нет"]
    leftover_lines = format_meal_leftovers_for_prompt(cooked)

    menu_summary = "Меню не выбрано."
    if selected:
        meals = ", ".join(m.name for m in selected.menu.meals)
        menu_summary = f"План «{selected.menu.title}»: {meals}"

    persons = persons_count or menu_ctx.members_count

    drink_note = ""
    if drink_mode and drink_mode != "none":
        drink_note = f"Напитки в меню: режим «{drink_mode}»."
    if not allow_alcohol:
        drink_note += " Алкоголь НЕ предлагать (пользователь не включил)."

    return AiUserContext(
        scope_mode=menu_ctx.scope_mode,
        prompt_text=menu_ctx.prompt_text,
        profile_summary=_profile_summary(profile),
        family_summary=menu_ctx.prompt_text if menu_ctx.scope_mode == "family" else "",
        pantry_summary="\n".join(pantry_lines),
        meal_leftovers_summary="\n".join(leftover_lines),
        menu_summary=menu_summary,
        recipe_catalog=_recipe_catalog_slice(db),
        persons_count=persons,
        drink_mode=drink_mode,
        allow_alcohol=allow_alcohol,
        is_pro=user_has_pro(db, user),
        event_mode=event_mode,
        extras={
            "family_name": menu_ctx.family_name,
            "members_count": menu_ctx.members_count,
            "drink_note": drink_note,
        },
    )


def _profile_summary(profile) -> str:
    parts = [
        f"цель: {profile.nutrition_goal or 'не задана'}",
        f"аллергии: {', '.join(profile.allergies or []) or 'нет'}",
        f"ограничения: {', '.join(profile.restrictions or []) or 'нет'}",
    ]
    if profile.medical_restrictions:
        parts.append(f"мед. особенности: {profile.medical_restrictions}")
    if profile.favorite_foods:
        parts.append(f"любит: {profile.favorite_foods}")
    disliked = ", ".join(
        x for x in (profile.disliked_foods, profile.banned_foods) if x
    )
    if disliked:
        parts.append(f"не любит/запрещено: {disliked}")
    if profile.age:
        parts.append(f"возраст: {profile.age}")
    if profile.budget:
        parts.append(f"бюджет: {profile.budget}")
    if profile.cooking_time:
        parts.append(f"время готовки: {profile.cooking_time}")
    return "; ".join(parts)


def context_to_json_block(ctx: AiUserContext) -> str:
    payload = {
        "scope": ctx.scope_mode,
        "persons_count": ctx.persons_count,
        "profile": ctx.profile_summary,
        "pantry": ctx.pantry_summary,
        "meal_leftovers": ctx.meal_leftovers_summary,
        "current_menu": ctx.menu_summary,
        "drink_mode": ctx.drink_mode,
        "allow_alcohol": ctx.allow_alcohol,
        "is_pro": ctx.is_pro,
        "recipe_catalog": ctx.recipe_catalog,
        "event": ctx.event_mode,
        "instructions": ctx.extras.get("drink_note", ""),
    }
    if ctx.scope_mode == "family":
        payload["family_context"] = ctx.prompt_text
    return json.dumps(payload, ensure_ascii=False, indent=2)


def recipe_to_ai_dict(recipe: Recipe) -> dict[str, Any]:
    return {
        "id": recipe.id,
        "title": recipe.title,
        "description": recipe.description,
        "meal_type": recipe.meal_type,
        "is_drink": recipe.is_drink,
        "is_alcoholic": recipe.is_alcoholic,
        "caffeine_mg": recipe.caffeine_mg,
        "sugar_g": recipe.sugar_g,
        "ingredients": get_structured_ingredients(recipe),
        "diets": recipe.diets or [],
    }
