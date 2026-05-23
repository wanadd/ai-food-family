from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.pantry import FamilyPantryItem
from app.models.user import User
from app.services import family as family_service
from app.services.app_scope import AppScope
from app.services.menu_labels import (
    ALLERGY_LABELS,
    BUDGET_LABELS,
    COOKING_TIME_LABELS,
    DIET_LABELS,
    GOAL_LABELS,
    MEMBER_RESTRICTION_LABELS,
    RESTRICTION_LABELS,
    label_map,
)
from app.services.nutrition_profile_labels import (
    ACTIVITY_LABELS,
    DISH_COMPLEXITY_LABELS,
    GENDER_LABELS,
    NUTRITION_GOAL_LABELS,
)
from app.services.family_menu_context import format_family_member_for_menu
from app.services.onboarding import get_or_create_profile
from app.services.pantry import format_leftovers_for_prompt, get_active_items_for_scope


@dataclass
class MenuGenerationContext:
    scope_mode: str
    context_label: str
    family_name: str | None
    members_count: int
    prompt_text: str
    has_family: bool
    leftovers: list[FamilyPantryItem] = field(default_factory=list)


def build_menu_context(db: Session, user: User, scope: AppScope) -> MenuGenerationContext:
    profile = get_or_create_profile(db, user)
    family = family_service.get_family_for_user(db, user)
    leftovers = get_active_items_for_scope(db, scope)

    lines: list[str] = ["Сформируй меню на один день."]

    if scope.is_personal:
        lines.append("Режим: личный (один пользователь).")
        lines.append(_format_user_block(user.first_name or "Вы", profile))
        lines.extend(_format_leftovers_block(leftovers))
        return MenuGenerationContext(
            scope_mode="personal",
            context_label="Личный режим",
            family_name=None,
            members_count=1,
            prompt_text="\n".join(lines),
            has_family=family is not None,
            leftovers=leftovers,
        )

    if family is None:
        raise ValueError("Family scope without family membership")

    persons = len(family.members)
    lines.append(
        f"Режим: семейный. Семья: {family.name}. "
        f"Готовить на {persons} персон (все участники ниже)."
    )
    lines.append(
        "Учти цели, аллергии и ограничения КАЖДОГО участника; "
        "порции рассчитай на указанное число персон."
    )
    for member in sorted(
        family.members,
        key=lambda m: (0 if m.role == "admin" else 1, m.display_name.lower()),
    ):
        lines.append(format_family_member_for_menu(db, member))
    lines.extend(_format_leftovers_block(leftovers))

    return MenuGenerationContext(
        scope_mode="family",
        context_label=f"Семья «{family.name}»",
        family_name=family.name,
        members_count=len(family.members),
        prompt_text="\n".join(lines),
        has_family=True,
        leftovers=leftovers,
    )


def _format_leftovers_block(items: list[FamilyPantryItem]) -> list[str]:
    if not items:
        return ["Остатки в холодильнике: не указаны."]
    lines = [
        "Остатки в холодильнике (ОБЯЗАТЕЛЬНО использовать в меню, "
        "минимизировать закупки этих продуктов; сначала трать то, что скоро истекает):",
    ]
    lines.extend(format_leftovers_for_prompt(items))
    return lines


def _format_user_block(name: str, profile) -> str:
    parts = [f"- {name}:"]
    if profile.nutrition_goal:
        parts.append(
            f"  цель питания: {NUTRITION_GOAL_LABELS.get(profile.nutrition_goal, profile.nutrition_goal)}"
        )
    else:
        parts.append(f"  цели: {_join_labels(profile.goals, GOAL_LABELS)}")
    if profile.activity_level:
        parts.append(
            f"  активность: {ACTIVITY_LABELS.get(profile.activity_level, profile.activity_level)}"
        )
    if profile.age:
        parts.append(f"  возраст: {profile.age}")
    if profile.gender:
        parts.append(
            f"  пол: {GENDER_LABELS.get(profile.gender, profile.gender)}"
        )
    if profile.height_cm and profile.weight_kg:
        parts.append(
            f"  рост/вес: {profile.height_cm} см, {profile.weight_kg} кг"
        )
    parts.append(f"  диеты: {_join_labels(profile.diets, DIET_LABELS)}")
    parts.append(f"  аллергии: {_join_labels(profile.allergies, ALLERGY_LABELS)}")
    parts.append(f"  ограничения: {_join_labels(profile.restrictions, RESTRICTION_LABELS)}")
    if profile.medical_restrictions:
        parts.append(f"  мед. ограничения: {profile.medical_restrictions}")
    if profile.budget:
        parts.append(f"  бюджет: {BUDGET_LABELS.get(profile.budget, profile.budget)}")
    if profile.cooking_time:
        parts.append(
            f"  время готовки: {COOKING_TIME_LABELS.get(profile.cooking_time, profile.cooking_time)}"
        )
    if profile.dish_complexity:
        parts.append(
            f"  сложность блюд: {DISH_COMPLEXITY_LABELS.get(profile.dish_complexity, profile.dish_complexity)}"
        )
    if profile.favorite_foods:
        parts.append(f"  любимое: {profile.favorite_foods}")
    disliked_parts = [
        p.strip()
        for p in (profile.disliked_foods, profile.banned_foods)
        if p and p.strip()
    ]
    if disliked_parts:
        parts.append(f"  не любит / запрещено: {'; '.join(disliked_parts)}")
    pro = profile.pro_data or {}
    if pro.get("track_macros"):
        parts.append("  PRO: учитывать КБЖУ при подборе меню")
    if pro.get("workouts_enabled"):
        freq = pro.get("workout_frequency") or ""
        goal = pro.get("workout_goal") or ""
        extra = ", ".join(x for x in (goal, freq) if x)
        parts.append(f"  PRO: тренировки{' — ' + extra if extra else ''}")
    return "\n".join(parts)


def _format_member_block(
    name: str, role: str, goals: list[str], restrictions: list[str]
) -> str:
    return (
        f"- {name} ({role}): цели — {_join_labels(goals, GOAL_LABELS)}; "
        f"ограничения/аллергии — {_join_labels(restrictions, MEMBER_RESTRICTION_LABELS)}"
    )


def _join_labels(values: list[str], mapping: dict[str, str]) -> str:
    labels = label_map(values, mapping)
    return ", ".join(labels) if labels else "не указано"
