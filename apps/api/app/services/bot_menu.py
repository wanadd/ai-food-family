"""Telegram bot main menu and section handlers."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.services import bot_session as bot_session_service
from app.services.bot_today import build_today_summary
from app.services.legal_consent import user_can_access_app
from app.telegram.messaging import send_telegram_message

MENU_TODAY = "🏠 Сегодня"
MENU_MY_MENU = "🍽 Моё меню"
MENU_SHOPPING = "🛒 Покупки"
MENU_PANTRY = "📦 Запасы"
MENU_NUTRITIONIST = "🥗 Нутрициолог"
MENU_QUICK_ADD = "⚡ Быстро добавить"
MENU_FAMILY = "👨‍👩‍👧 Семья"
MENU_SETTINGS = "⚙ Настройки"

QUICK_VOICE_HINT = "🎤 Голосом"
QUICK_RECEIPT_HINT = "📷 Фото чека"
QUICK_SHOPPING = "🛒 Добавить в покупки"
QUICK_PANTRY = "📦 Добавить в запасы"
QUICK_LEFTOVER = "🍲 Остатки блюда"

MAIN_MENU_LABELS = (
    MENU_TODAY,
    MENU_MY_MENU,
    MENU_SHOPPING,
    MENU_PANTRY,
    MENU_NUTRITIONIST,
    MENU_QUICK_ADD,
    MENU_FAMILY,
    MENU_SETTINGS,
)


def _webapp_url(path: str) -> str:
    base = (settings.telegram_webapp_url or "https://planam.ru").rstrip("/")
    return f"{base}{path}"


def main_menu_keyboard() -> dict[str, Any]:
    return {
        "keyboard": [
            [MENU_TODAY, MENU_MY_MENU],
            [MENU_SHOPPING, MENU_PANTRY],
            [MENU_NUTRITIONIST, MENU_QUICK_ADD],
            [MENU_FAMILY, MENU_SETTINGS],
        ],
        "resize_keyboard": True,
        "persistent": True,
    }


def quick_add_keyboard() -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": QUICK_VOICE_HINT, "callback_data": "quick:voice_hint"},
                {"text": QUICK_RECEIPT_HINT, "callback_data": "quick:receipt_hint"},
            ],
            [
                {"text": QUICK_SHOPPING, "web_app": {"url": _webapp_url("/shopping")}},
                {"text": QUICK_PANTRY, "web_app": {"url": _webapp_url("/pantry")}},
            ],
            [{"text": QUICK_LEFTOVER, "callback_data": "quick:leftover"}],
            [{"text": "← Назад в меню", "callback_data": "quick:back"}],
        ],
    }


async def send_main_menu(chat_id: int) -> None:
    await send_telegram_message(
        chat_id,
        "Главное меню ПланАм — выберите раздел:",
        reply_markup=main_menu_keyboard(),
    )


async def handle_menu_text(
    db: Session, user: User, chat_id: int, text: str
) -> bool:
    if not user_can_access_app(user):
        return False

    if text == MENU_TODAY:
        summary = build_today_summary(db, user)
        await send_telegram_message(chat_id, summary, reply_markup=main_menu_keyboard())
        return True

    if text == MENU_MY_MENU:
        await send_telegram_message(
            chat_id,
            "Меню и рацион — в приложении:",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "Моё меню", "web_app": {"url": _webapp_url("/plan/today")}}],
                    [{"text": "Создать меню", "web_app": {"url": _webapp_url("/plan/generate")}}],
                ],
            },
        )
        return True

    if text == MENU_SHOPPING:
        await send_telegram_message(
            chat_id,
            "Список покупок откроется в приложении.",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "Открыть покупки", "web_app": {"url": _webapp_url("/shopping")}}],
                ],
            },
        )
        return True

    if text == MENU_PANTRY:
        await send_telegram_message(
            chat_id,
            "Запасы можно вести в приложении.",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "Открыть запасы", "web_app": {"url": _webapp_url("/pantry")}}],
                ],
            },
        )
        return True

    if text == MENU_NUTRITIONIST:
        await send_telegram_message(
            chat_id,
            "Нутрициолог — советы и чат:",
            reply_markup={
                "inline_keyboard": [
                    [
                        {
                            "text": "Открыть нутрициолога",
                            "web_app": {"url": _webapp_url("/nutritionist")},
                        }
                    ],
                ],
            },
        )
        return True

    if text == MENU_QUICK_ADD:
        await send_telegram_message(
            chat_id,
            "⚡ Быстро добавить — выберите способ:",
            reply_markup=quick_add_keyboard(),
        )
        return True

    if text == MENU_FAMILY:
        await send_telegram_message(
            chat_id,
            "Семья и участники:",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "Открыть семью", "web_app": {"url": _webapp_url("/family")}}],
                ],
            },
        )
        return True

    if text == MENU_SETTINGS:
        await send_telegram_message(
            chat_id,
            "Настройки и документы:",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "Открыть настройки", "web_app": {"url": _webapp_url("/settings")}}],
                    [
                        {
                            "text": "Документы",
                            "web_app": {"url": _webapp_url("/settings/documents")},
                        }
                    ],
                ],
            },
        )
        return True

    return False


async def handle_quick_callback(
    db: Session, user: User, chat_id: int, data: str
) -> bool:
    if not data.startswith("quick:"):
        return False

    action = data.split(":", 1)[1]
    if action == "back":
        await send_main_menu(chat_id)
        return True
    if action == "voice_hint":
        await send_telegram_message(
            chat_id,
            "Отправьте голосовое сообщение со списком покупок, например:\n"
            "«Купил молоко два литра, десяток яиц, две пачки творога»",
            reply_markup=main_menu_keyboard(),
        )
        return True
    if action == "receipt_hint":
        await send_telegram_message(
            chat_id,
            "Отправьте фото чека — распознаем товары и предложим добавить в запасы.",
            reply_markup=main_menu_keyboard(),
        )
        return True
    if action == "leftover":
        bot_session_service.set_session_state(
            db, user.telegram_id, bot_session_service.STATE_LEFTOVER_DISH
        )
        await send_telegram_message(
            chat_id,
            "🍲 Остатки блюда\n\nЧто осталось? Напишите название блюда:",
            reply_markup=main_menu_keyboard(),
        )
        return True
    return False


async def handle_leftover_flow(
    db: Session, user: User, chat_id: int, text: str
) -> bool:
    session = bot_session_service.get_session(db, user.telegram_id)
    if not session or session.state not in (
        bot_session_service.STATE_LEFTOVER_DISH,
        bot_session_service.STATE_LEFTOVER_PORTIONS,
    ):
        return False

    from app.services import meal_leftovers as meal_leftovers_service
    from app.schemas.meal_leftover import MealLeftoverCreate
    from app.services.app_scope import resolve_scope

    if session.state == bot_session_service.STATE_LEFTOVER_DISH:
        dish = text.strip()
        if len(dish) < 2:
            await send_telegram_message(chat_id, "Укажите название блюда, например «Борщ».")
            return True
        bot_session_service.patch_payload(db, user.telegram_id, leftover_dish=dish)
        bot_session_service.set_session_state(
            db, user.telegram_id, bot_session_service.STATE_LEFTOVER_PORTIONS
        )
        await send_telegram_message(
            chat_id,
            f"«{dish}»\n\nСколько порций осталось? Напишите число:",
        )
        return True

    if session.state == bot_session_service.STATE_LEFTOVER_PORTIONS:
        try:
            portions = int(text.strip())
        except ValueError:
            await send_telegram_message(chat_id, "Введите число порций, например 2.")
            return True
        if portions < 1 or portions > 50:
            await send_telegram_message(chat_id, "Укажите от 1 до 50 порций.")
            return True
        payload = bot_session_service.get_payload(session)
        dish = str(payload.get("leftover_dish") or "Блюдо")
        scope = resolve_scope(db, user, None)
        meal_leftovers_service.create_leftover(
            db,
            user,
            scope,
            MealLeftoverCreate(dish_name=dish, portions_remaining=portions),
        )
        bot_session_service.clear_session_state(db, user.telegram_id)
        await send_telegram_message(
            chat_id,
            f"Сохранено: {dish} — {portions} порц.\n"
            "Учтём при меню, покупках и советах нутрициолога.",
            reply_markup=main_menu_keyboard(),
        )
        return True

    return False
