import hashlib
import json
from datetime import date

from sqlalchemy.orm import Session

from app.models.user import User
from app.services import family as family_service
from app.services.app_scope import AppScope
from app.services.family_member_nutrition import (
    member_is_virtual,
    virtual_nutrition_from_member,
)
from app.services.meal_leftovers import list_active_leftovers
from app.services.onboarding import get_or_create_profile
from app.services.pantry import get_active_items_for_scope


def _profile_snapshot(profile) -> dict:
    goal_details = profile.goal_details if isinstance(profile.goal_details, dict) else {}
    return {
        "nutrition_goal": profile.nutrition_goal,
        "goal_details": goal_details,
        "activity_level": profile.activity_level,
        "age": profile.age,
        "gender": profile.gender,
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "allergies": profile.allergies or [],
        "diets": profile.diets or [],
        "disliked_foods": profile.disliked_foods,
        "medical_restrictions": profile.medical_restrictions,
        "banned_foods": profile.banned_foods,
        "dish_complexity": profile.dish_complexity,
        "budget": (profile.pro_data or {}).get("budget"),
        "cooking_time": (profile.pro_data or {}).get("cooking_time"),
    }


def _member_snapshot(db: Session, member) -> dict:
    if member_is_virtual(member):
        n = virtual_nutrition_from_member(member)
        return {
            "id": member.id,
            "name": member.display_name,
            "virtual": True,
            "age_months": n.age_months,
            "nutrition_goal": n.nutrition_goal,
            "allergies": n.allergies,
            "custom_allergies": n.custom_allergies,
            "restrictions": n.restrictions,
            "custom_restrictions": n.custom_restrictions,
            "favorite_foods": n.favorite_foods,
            "disliked_foods": n.disliked_foods,
            "notes": n.notes,
        }
    if member.user_id is None:
        return {"id": member.id, "name": member.display_name}
    profile = get_or_create_profile(db, member.user)
    return {
        "id": member.id,
        "user_id": member.user_id,
        "name": member.display_name,
        "profile": _profile_snapshot(profile),
    }


def compute_context_fingerprint(
    db: Session,
    user: User,
    scope: AppScope,
    *,
    persons_count: int | None = None,
    plan_mode: str | None = None,
) -> str:
    profile = get_or_create_profile(db, user)
    pantry = get_active_items_for_scope(db, scope)
    leftovers = list_active_leftovers(db, scope)
    today = date.today().isoformat()

    payload: dict = {
        "scope": scope.mode,
        "family_id": scope.family_id,
        "user_id": scope.user_id,
        "date": today,
        "persons_count": persons_count,
        "plan_mode": plan_mode,
        "profile": _profile_snapshot(profile),
        "pantry": [
            {
                "name": i.name,
                "quantity": i.quantity,
                "expires_at": i.expires_at.isoformat() if i.expires_at else None,
            }
            for i in pantry
        ],
        "meal_leftovers": [
            {
                "dish": lo.dish_name,
                "portions": lo.portions_remaining,
                "until": lo.valid_until.isoformat() if lo.valid_until else None,
            }
            for lo in leftovers
        ],
        "members": [],
    }

    if scope.is_family:
        family = family_service.get_family_for_user(db, user)
        if family:
            payload["members"] = [
                _member_snapshot(db, m) for m in sorted(family.members, key=lambda m: m.id)
            ]
            if persons_count is None:
                payload["persons_count"] = len(family.members)

    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def resolve_persons_count(db: Session, user: User, scope: AppScope) -> int:
    if scope.is_personal:
        return 1
    from app.services.meal_attendance import count_home_eaters

    home, _total = count_home_eaters(db, scope, meal_type="lunch")
    if home > 0:
        return home
    family = family_service.get_family_for_user(db, user)
    if family and family.members:
        return len(family.members)
    return 1


def get_stored_fingerprint(menu_data: dict) -> str | None:
    meta = menu_data.get("_meta") if isinstance(menu_data, dict) else None
    if isinstance(meta, dict):
        fp = meta.get("context_fingerprint")
        return str(fp) if fp else None
    return None
