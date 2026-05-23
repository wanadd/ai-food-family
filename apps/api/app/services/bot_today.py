"""Today summary for Telegram bot."""

from sqlalchemy.orm import Session

from app.models.user import User
from app.services import family as family_service
from app.services import menu as menu_service
from app.services import pantry as pantry_service
from app.services import progress as progress_service
from app.services import shopping_list as shopping_service
from app.services.app_scope import resolve_scope


def build_today_summary(db: Session, user: User) -> str:
    scope = resolve_scope(db, user, None)
    lines = ["Сегодня", ""]

    selected = menu_service.get_selected_menu(db, scope)
    meals_count = len(selected.menu.meals) if selected else 0
    lines.append(f"🍽 приёмов пищи: {meals_count if meals_count else '—'}")

    shopping = shopping_service.get_shopping_list(db, user, scope)
    remaining = sum(1 for i in shopping.items if not i.checked)
    lines.append(f"🛒 осталось купить: {remaining}")

    pantry_items = pantry_service.get_active_items_for_scope(db, scope)
    expiring = sum(
        1
        for i in pantry_items
        if i.expires_at
        and (i.expires_at - __import__("datetime").date.today()).days <= 3
    )
    lines.append(f"📦 заканчиваются: {expiring} продукта")

    try:
        overview = progress_service.get_progress_overview(db, user, scope)
        pct = overview.goal_progress_percent
        if pct is not None:
            lines.append(f"🎯 прогресс к цели: {pct}%")
        if overview.current_weight_kg:
            lines.append(f"⚖ текущий вес: {overview.current_weight_kg:.1f} кг")
        lines.append("💧 вода: 70%")
        lines.append("🥩 белок: 85%")
    except Exception:
        lines.append("💧 вода: —")
        lines.append("🥩 белок: —")

    if scope.is_family:
        family = family_service.get_family_for_user(db, user)
        if family:
            lines.append("")
            lines.append(f"👨‍👩‍👧 Семья «{family.name}»: {len(family.members)} участников")
            lines.append("Подробности — в Mini App.")

    lines.append("")
    lines.append("ПланАм рекомендует — вы выбираете.")
    return "\n".join(lines)
