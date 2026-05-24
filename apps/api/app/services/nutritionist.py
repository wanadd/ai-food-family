import logging

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.app_scope import AppScope
from app.services.menu_selection import get_selected_menu
from app.services.nutrition_profile import profile_to_nutrition_schema
from app.services.onboarding import get_or_create_profile
from app.services import subscription as subscription_service
from app.services.ai import generate_nutritionist_tip, nutritionist_answer
from app.services.ai_context import build_ai_user_context
from app.services.ai_errors import AiError, AiUnavailableError, MSG_AI_UNAVAILABLE
from app.services.ai_client import current_model_name, is_ai_configured
from app.services.subscription_catalog import AMA_COSTS

logger = logging.getLogger(__name__)

QUICK_HINTS: dict[str, str] = {
    "белок": "Добавьте белок в обед и ужин: яйца, творог, рыбу или бобовые.",
    "калор": "Снижайте калории постепенно: больше овощей, меньше сладкого между приёмами.",
    "запас": "В меню выберите режим «Использовать запасы» — ПланАм подберёт блюда из дома.",
}

GOAL_LABELS: dict[str, str] = {
    "maintain": "Поддержание веса",
    "lose": "Похудение",
    "gain": "Набор массы",
    "healthy": "Здоровое питание",
    "sport": "Спорт",
    "kids": "Детское питание",
}


def _fallback_answer(message: str, goal: str | None, menu_title: str | None) -> str:
    lower = message.lower()
    for key, hint in QUICK_HINTS.items():
        if key in lower:
            return hint

    if not goal:
        return (
            "Заполните профиль питания — тогда ПланАм сможет давать "
            "персональные рекомендации."
        )

    goal_label = GOAL_LABELS.get(goal, goal)
    if menu_title:
        return (
            f"Сейчас у вас план «{menu_title}», цель — {goal_label}. "
            "Следуйте меню и отмечайте покупки — так советы станут точнее."
        )
    return (
        f"Ваша цель — {goal_label}. Составьте план в разделе «Меню», "
        "и рекомендации станут персональнее."
    )


async def ask_nutritionist(
    db: Session,
    user: User,
    scope: AppScope,
    message: str,
) -> tuple[str, bool]:
    profile = get_or_create_profile(db, user)
    nutrition = profile_to_nutrition_schema(profile)
    goal = nutrition.nutrition_goal
    selected = get_selected_menu(db, scope)
    menu_title = selected.menu.title if selected else None

    if not is_ai_configured():
        return MSG_AI_UNAVAILABLE, False

    ams_spent = subscription_service.require_ai_action(
        db,
        user,
        scope,
        "nutritionist_ask",
        ama_cost=AMA_COSTS["nutritionist_ask"],
    )

    ai_ctx = build_ai_user_context(db, user, scope)

    try:
        answer = await nutritionist_answer(ai_ctx, message)
        subscription_service.log_ai_usage(
            db,
            user_id=user.id,
            family_id=scope.family_id,
            action_type="nutritionist_ask",
            ams_spent=ams_spent,
            model=current_model_name(),
            metadata={"used_ai": True},
        )
        return answer, True
    except AiUnavailableError:
        logger.info("Nutritionist AI unavailable")
    except AiError:
        logger.exception("Nutritionist OpenAI call failed")
    except Exception:
        logger.exception("Nutritionist OpenAI call failed")

    subscription_service.log_ai_usage(
        db,
        user_id=user.id,
        family_id=scope.family_id,
        action_type="nutritionist_ask",
        ams_spent=ams_spent,
        model=None,
        metadata={"used_ai": False},
    )
    return (
        "ПланАм временно не смог обработать запрос. Попробуйте ещё раз.",
        False,
    )


async def daily_tip(
    db: Session,
    user: User,
    scope: AppScope,
) -> tuple[str, bool]:
    """Optional AI tip for menu overview (no AMA charge)."""
    if not is_ai_configured():
        return "", False
    ai_ctx = build_ai_user_context(db, user, scope)
    try:
        tip = await generate_nutritionist_tip(ai_ctx)
        return tip, True
    except (AiUnavailableError, AiError):
        return "", False
