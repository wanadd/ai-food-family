from sqlalchemy.orm import Session

from app.models.family import FamilyMember
from app.models.user import User
from app.models.user_profile import UserProfile
from app.services.family_member_nutrition import (
    member_is_virtual,
    nutrition_goal_display,
    virtual_nutrition_from_member,
)
from app.services.member_age import format_age_months_ru
from app.nutrition.allergen_ontology import CONCEPT_LABEL_RU, typed_entries_from_profile
from app.nutrition.medical_safety import format_medical_context
from app.services.member_age import (
    age_resolution_to_dict,
    format_age_resolution_ru,
    resolve_age,
    resolve_age_for_profile,
)
from app.services.menu_labels import (
    ALLERGY_LABELS,
    DIET_LABELS,
    GOAL_LABELS,
    MEMBER_RESTRICTION_LABELS,
    label_map,
)
from app.services.onboarding import get_or_create_profile

VIRTUAL_ALLERGY_LABELS = {
    **ALLERGY_LABELS,
    "fish": "рыба",
    "citrus": "цитрусовые",
    "chocolate": "шоколад",
    "strawberry": "клубника",
    "other": "другое",
}

VIRTUAL_RESTRICTION_LABELS = {
    **MEMBER_RESTRICTION_LABELS,
    "gluten_free": "без глютена",
    "lactose_free": "без лактозы",
    "no_sugar": "без сахара",
    "low_carb": "низкоуглеводное",
    "other": "другое",
}


def format_family_member_for_menu(db: Session, member: FamilyMember) -> str:
    name = member.display_name
    role_note = "виртуальный участник" if member_is_virtual(member) else "аккаунт Telegram"

    if member_is_virtual(member):
        n = virtual_nutrition_from_member(member)
        parts = [f"- {name} ({role_note}):"]

        kind = member.virtual_kind
        age_resolution = resolve_age(age_months=n.age_months, age=n.age)
        if n.age_months is not None:
            parts.append(
                f"  возраст: {format_age_months_ru(n.age_months, kind=kind)}"
            )
        elif kind == "child":
            parts.append("  возраст: ребёнок, возраст не указан")
        if age_resolution.age_source != "none":
            parts.append(
                "  возрастной профиль: "
                f"{age_resolution.population_scope}; "
                f"band={age_resolution.age_band or 'unknown'}; "
                f"status={age_resolution.resolution_status}"
            )
            if age_resolution.is_infant:
                parts.append(
                    "  infant_scope=true; обычное семейное меню не сертифицируется "
                    "как питание для младенца"
                )
            if age_resolution.has_conflict:
                parts.append("  конфликт возраста: age_months не совпадает с age")

        goal_label = nutrition_goal_display(n)
        if goal_label:
            parts.append(f"  цель: {goal_label}")

        allergy_values = [
            *(n.allergies or []),
            *(n.custom_allergies or []),
        ]
        restriction_values = [
            *(n.restrictions or []),
            *(n.custom_restrictions or []),
        ]
        parts.append(f"  аллергии: {_join(allergy_values, VIRTUAL_ALLERGY_LABELS)}")
        parts.append(
            f"  ограничения: {_join(restriction_values, VIRTUAL_RESTRICTION_LABELS)}"
        )
        typed = _format_typed_safety_entries(typed_entries_from_profile(n))
        if typed:
            parts.append(f"  typed safety: {typed}")
        medical = format_medical_context(n)
        if medical:
            parts.append(f"  typed medical context: {medical}")
        if n.favorite_foods:
            parts.append(f"  любит: {n.favorite_foods}")
        if n.disliked_foods:
            parts.append(f"  не любит: {n.disliked_foods}")
        if n.notes:
            parts.append(f"  особенности: {n.notes}")
        return "\n".join(parts)

    if member.user_id is None:
        return (
            f"- {name} ({role_note}): цели — {_join(member.goals or [], GOAL_LABELS)}; "
            f"ограничения — {_join(member.restrictions or [], MEMBER_RESTRICTION_LABELS)}"
        )

    user = db.query(User).filter(User.id == member.user_id).one_or_none()
    if user is None:
        return f"- {name}: данные недоступны"

    profile = get_or_create_profile(db, user)
    return _format_telegram_profile_block(name, role_note, profile)


def _format_telegram_profile_block(
    name: str, role_note: str, profile: UserProfile
) -> str:
    from app.services.menu_context import _format_user_block

    block = _format_user_block(name, profile)
    return block.replace(f"- {name}:", f"- {name} ({role_note}):", 1)


def _format_typed_safety_entries(entries) -> str:
    parts = []
    for entry in entries:
        label = CONCEPT_LABEL_RU.get(entry.concept_id, entry.concept_id)
        parts.append(f"{entry.kind}:{label}({entry.origin})")
    return ", ".join(parts)


def age_resolution_for_member(db: Session, member: FamilyMember) -> dict:
    if member_is_virtual(member):
        n = virtual_nutrition_from_member(member)
        return age_resolution_to_dict(resolve_age(age_months=n.age_months, age=n.age))
    if member.user_id is None:
        return age_resolution_to_dict(resolve_age())
    user = db.query(User).filter(User.id == member.user_id).one_or_none()
    if user is None:
        return age_resolution_to_dict(resolve_age())
    return age_resolution_to_dict(resolve_age_for_profile(get_or_create_profile(db, user)))


def _join(values: list[str], mapping: dict[str, str]) -> str:
    labels = label_map(values, mapping)
    custom = [v for v in values if v and v not in mapping]
    labels.extend(custom)
    return ", ".join(labels) if labels else "не указано"
