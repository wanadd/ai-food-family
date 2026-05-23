import logging

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.services.app_scope import AppScope
from app.services.menu import get_selected_menu
from app.services.nutrition_profile import profile_to_nutrition_schema
from app.services.onboarding import get_or_create_profile
from app.services import pantry as pantry_service
from app.services import subscription as subscription_service
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
    ams_spent = subscription_service.require_ai_action(
        db,
        user,
        scope,
        "nutritionist_ask",
        ama_cost=AMA_COSTS["nutritionist_ask"],
    )

    profile = get_or_create_profile(db, user)
    nutrition = profile_to_nutrition_schema(profile)
    goal = nutrition.nutrition_goal

    selected = get_selected_menu(db, scope)
    menu_title = selected.menu.title if selected else None
    pantry_list = pantry_service.list_pantry(db, user, scope)
    pantry_count = pantry_list.active_count

    if settings.openai_api_key:
        try:
            answer = await _ask_openai(
                message=message,
                goal=goal,
                menu_title=menu_title,
                pantry_count=pantry_count,
                restrictions=nutrition.medical_restrictions or "",
                allergies=", ".join(
                    a for a in nutrition.allergies if a != "none"
                ),
            )
            subscription_service.log_ai_usage(
                db,
                user_id=user.id,
                family_id=scope.family_id,
                action_type="nutritionist_ask",
                ams_spent=ams_spent,
                model=settings.openai_model,
                metadata={"used_ai": True},
            )
            return answer, True
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
    return _fallback_answer(message, goal, menu_title), False


async def _ask_openai(
    *,
    message: str,
    goal: str | None,
    menu_title: str | None,
    pantry_count: int,
    restrictions: str,
    allergies: str,
) -> str:
    context_parts = [
        "Ты — дружелюбный нутрициолог приложения ПланАм.",
        "Отвечай кратко (2–4 предложения), по-русски, без markdown.",
        "Не упоминай ChatGPT или OpenAI.",
        f"Цель пользователя: {GOAL_LABELS.get(goal or '', goal or 'не задана')}.",
    ]
    if menu_title:
        context_parts.append(f"Текущий план питания: {menu_title}.")
    if pantry_count:
        context_parts.append(f"В запасах около {pantry_count} активных позиций.")
    if allergies:
        context_parts.append(f"Аллергии: {allergies}.")
    if restrictions:
        context_parts.append(f"Ограничения: {restrictions}.")

    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": "\n".join(context_parts)},
            {"role": "user", "content": message},
        ],
        "temperature": 0.6,
        "max_tokens": 280,
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        body = response.json()

    return body["choices"][0]["message"]["content"].strip()
