from sqlalchemy.orm import Session

from app.models.menu_selection import FamilyMenuSelection
from app.models.shopping_list import FamilyShoppingList
from app.models.user import User
from app.schemas.menu import MenuVariant
from app.schemas.shopping_list import ShoppingListItem
from app.services import family as family_service
from app.services.menu_labels import VARIANT_META

MEAL_LABELS = {
    "breakfast": "Завтрак",
    "lunch": "Обед",
    "dinner": "Ужин",
    "snack": "Перекус",
}


def build_buy_reminder_text(db: Session, user: User) -> str:
    membership = family_service.get_user_membership(db, user)
    if membership is None:
        return (
            "🛒 <b>Напоминание о покупках</b>\n\n"
            "Создайте семью и выберите меню — список покупок "
            "соберётся автоматически."
        )

    shopping_list = (
        db.query(FamilyShoppingList)
        .filter(FamilyShoppingList.family_id == membership.family_id)
        .one_or_none()
    )

    if shopping_list is None or not shopping_list.items:
        return (
            "🛒 <b>Напоминание о покупках</b>\n\n"
            "Выберите меню в приложении — и мы соберём список "
            "ингредиентов для всей семьи."
        )

    items = [ShoppingListItem.model_validate(raw) for raw in shopping_list.items]
    unchecked = [item for item in items if not item.checked]

    if not unchecked:
        return (
            "🛒 <b>Напоминание о покупках</b>\n\n"
            "Отлично! Все позиции в списке отмечены. "
            "Можно планировать меню на завтра."
        )

    preview = "\n".join(
        f"• {item.name} — {item.amount}" for item in unchecked[:5]
    )
    extra = ""
    if len(unchecked) > 5:
        extra = f"\n<i>…и ещё {len(unchecked) - 5}</i>"

    return (
        f"🛒 <b>Напоминание: пора закупиться!</b>\n\n"
        f"Осталось <b>{len(unchecked)}</b> из {len(items)} позиций:\n"
        f"{preview}{extra}"
    )


def build_cook_reminder_text(db: Session, user: User) -> str:
    membership = family_service.get_user_membership(db, user)
    if membership is None:
        return (
            "👨‍🍳 <b>Напоминание о готовке</b>\n\n"
            "Создайте семью и выберите меню на день — "
            "мы напомним, что приготовить."
        )

    selection = (
        db.query(FamilyMenuSelection)
        .filter(FamilyMenuSelection.family_id == membership.family_id)
        .order_by(FamilyMenuSelection.selected_at.desc())
        .first()
    )

    if selection is None:
        return (
            "👨‍🍳 <b>Напоминание о готовке</b>\n\n"
            "Меню на сегодня ещё не выбрано. "
            "Откройте AI Меню и нажмите «Выбрать»."
        )

    menu = MenuVariant.model_validate(selection.menu_data)
    variant_label = VARIANT_META.get(menu.variant, {}).get("title", menu.title)

    meal_lines = "\n".join(
        f"• <b>{MEAL_LABELS.get(meal.meal_type, meal.meal_type)}</b>: "
        f"{meal.name} ({meal.prep_time_minutes} мин)"
        for meal in menu.meals
    )

    return (
        f"👨‍🍳 <b>Пора готовить!</b>\n\n"
        f"Меню: <i>{menu.title}</i> ({variant_label})\n\n"
        f"{meal_lines}\n\n"
        f"⏱ Суммарно у плиты: ~{menu.total_prep_minutes} мин"
    )
