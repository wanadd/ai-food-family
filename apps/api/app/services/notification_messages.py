from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.menu import MenuVariant
from app.schemas.shopping_list import ShoppingListItem
from app.services.app_scope import get_or_create_preferences, resolve_scope
from app.services.shopping_list import _get_latest_selection, _get_or_create_list


def build_buy_reminder_text(db: Session, user: User) -> str:
    prefs = get_or_create_preferences(db, user)
    try:
        scope = resolve_scope(db, user, prefs.active_mode)
    except Exception:
        scope = resolve_scope(db, user, "personal")

    shopping_list = _get_or_create_list(db, scope)
    mode_label = "семейный" if scope.is_family else "личный"

    if not shopping_list.items:
        return (
            f"🛒 <b>Напоминание о покупках</b> ({mode_label} режим)\n\n"
            "Выберите меню в приложении — список покупок соберётся автоматически."
        )

    items = [ShoppingListItem.model_validate(raw) for raw in shopping_list.items]
    unchecked = [item for item in items if not item.checked]

    if not unchecked:
        return (
            f"🛒 <b>Напоминание о покупках</b> ({mode_label} режим)\n\n"
            "Все позиции отмечены. Можно планировать меню на следующий день."
        )

    preview = "\n".join(
        f"• {item.name} — {item.amount}" for item in unchecked[:5]
    )
    extra = ""
    if len(unchecked) > 5:
        extra = f"\n<i>…и ещё {len(unchecked) - 5}</i>"

    return (
        f"🛒 <b>Напоминание: пора закупиться!</b> ({mode_label})\n\n"
        f"Осталось <b>{len(unchecked)}</b> из {len(items)} позиций:\n"
        f"{preview}{extra}"
    )


def build_cook_reminder_text(db: Session, user: User) -> str:
    prefs = get_or_create_preferences(db, user)
    try:
        scope = resolve_scope(db, user, prefs.active_mode)
    except Exception:
        scope = resolve_scope(db, user, "personal")

    selection = _get_latest_selection(db, scope)
    mode_label = "семейный" if scope.is_family else "личный"

    if selection is None:
        return (
            f"👨‍🍳 <b>Напоминание о готовке</b> ({mode_label} режим)\n\n"
            "Меню на сегодня ещё не выбрано. Откройте AI Меню и нажмите «Выбрать»."
        )

    menu = MenuVariant.model_validate(selection.menu_data)
    from app.services.menu_labels import VARIANT_META

    meal_labels = {
        "breakfast": "Завтрак",
        "lunch": "Обед",
        "dinner": "Ужин",
        "snack": "Перекус",
    }
    variant_label = VARIANT_META.get(menu.variant, {}).get("title", menu.title)

    meal_lines = "\n".join(
        f"• <b>{meal_labels.get(meal.meal_type, meal.meal_type)}</b>: "
        f"{meal.name} ({meal.prep_time_minutes} мин)"
        for meal in menu.meals
    )

    return (
        f"👨‍🍳 <b>Пора готовить!</b> ({mode_label})\n\n"
        f"Меню: <i>{menu.title}</i> ({variant_label})\n\n"
        f"{meal_lines}\n\n"
        f"⏱ Суммарно у плиты: ~{menu.total_prep_minutes} мин"
    )
