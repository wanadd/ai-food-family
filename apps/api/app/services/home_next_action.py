"""Home 2026 next-action rule engine (CR2)."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.menu_overview import HomeNextAction, PantryExpiringPreview
from app.services.app_scope import AppScope
from app.services.meal_daily_nutrition import list_checkins_for_date
from app.services.nutrition_profile import is_profile_complete
from app.services.onboarding import get_or_create_profile
from app.services.pantry import get_active_items_for_scope
from app.services.shopping_list import get_shopping_list


def _pantry_expiring_preview(db: Session, scope: AppScope) -> PantryExpiringPreview | None:
    today = date.today()
    items = get_active_items_for_scope(db, scope)
    best: PantryExpiringPreview | None = None
    for item in items:
        if item.expires_at is None:
            continue
        days = (item.expires_at - today).days
        if days > 2:
            continue
        if best is None or days < best.days_until_expiry:
            best = PantryExpiringPreview(name=item.name, days_until_expiry=days)
    return best


def _shopping_unchecked(db: Session, user: User, scope: AppScope) -> int:
    try:
        lst = get_shopping_list(db, user, scope)
    except Exception:
        return 0
    return max(0, lst.total_count - lst.checked_count)


def _needs_meal_outcome(db: Session, scope: AppScope, today_meal_count: int) -> bool:
    if today_meal_count == 0:
        return False
    checkins = list_checkins_for_date(db, scope, date.today())
    return len(checkins) < min(today_meal_count, 3)


def compute_home_next_action(
    db: Session,
    user: User,
    scope: AppScope,
    *,
    has_menu: bool,
    today_meal_count: int,
) -> tuple[HomeNextAction, int, PantryExpiringPreview | None]:
    profile = get_or_create_profile(db, user)
    shopping_unchecked = _shopping_unchecked(db, user, scope)
    pantry_preview = _pantry_expiring_preview(db, scope)

    if not is_profile_complete(profile):
        return (
            HomeNextAction(
                id="complete_nutrition",
                cta_label="Настроим питание за 30 сек",
                redirect_path="/profile/nutrition",
                subtitle="Цель и ограничения — для точного плана",
            ),
            shopping_unchecked,
            pantry_preview,
        )

    if not has_menu:
        return (
            HomeNextAction(
                id="generate_menu",
                cta_label="Составить план на неделю",
                redirect_path="/menu/generate",
                subtitle="Персональные блюда с учётом ваших предпочтений",
            ),
            shopping_unchecked,
            pantry_preview,
        )

    if shopping_unchecked > 0:
        return (
            HomeNextAction(
                id="shopping",
                cta_label=f"Докупить {shopping_unchecked} позиций",
                redirect_path="/shopping",
                subtitle="Список из вашего меню",
                metadata={"unchecked_count": shopping_unchecked},
            ),
            shopping_unchecked,
            pantry_preview,
        )

    if pantry_preview is not None:
        return (
            HomeNextAction(
                id="use_pantry_item",
                cta_label=f"Использовать {pantry_preview.name}",
                redirect_path="/shopping/pantry",
                subtitle=f"Срок годности · {pantry_preview.days_until_expiry} дн.",
                metadata={"product_name": pantry_preview.name},
            ),
            shopping_unchecked,
            pantry_preview,
        )

    if _needs_meal_outcome(db, scope, today_meal_count):
        return (
            HomeNextAction(
                id="meal_outcome",
                cta_label="Отметить: поели?",
                redirect_path="/menu/current",
                subtitle="Займёт 10 секунд",
            ),
            shopping_unchecked,
            pantry_preview,
        )

    return (
        HomeNextAction(
            id="open_today",
            cta_label="Что готовим сегодня",
            redirect_path="/menu/current",
            subtitle=None,
        ),
        shopping_unchecked,
        pantry_preview,
    )
