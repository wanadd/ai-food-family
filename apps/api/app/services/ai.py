"""
PlanAm AI service — all OpenAI calls go through here (backend only).

Public helpers return (result, used_ai: bool) or raise AiUnavailableError / AiResponseError.
Callers should catch AiError and show `.user_message` to users.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.menu import MenuIngredient, MenuMeal, MenuVariant, MenuVariantType
from app.schemas.menu_overview import (
    RecipeEvaluationReason,
    RecipeEvaluationResponse,
    RecipeImproveResponse,
    RecipeImproveSuggestion,
)
from app.services import ai_client
from app.services.ai_context import (
    AiUserContext,
    build_ai_user_context,
    context_to_json_block,
    recipe_to_ai_dict,
)
from app.services.ai_errors import (
    MSG_AI_FAILED,
    AiError,
    AiResponseError,
    AiUnavailableError,
)
from app.services.menu_context import MenuGenerationContext
from app.services.menu_labels import VARIANT_META
from app.services.recipe_storage import aggregate_ingredients_for_shopping
from app.services.app_scope import AppScope
from app.services.shopping_categories import infer_category

logger = logging.getLogger(__name__)

MenuVariantKey = Literal["quick", "economy", "balanced"]

BOT_INTENTS = Literal[
    "add_to_pantry",
    "add_to_shopping",
    "add_leftover",
    "ask_nutritionist",
    "generate_menu",
    "show_summary",
    "unknown",
]

MENU_SYSTEM = """Ты — нутрициолог и семейный повар приложения ПланАм.
Отвечай ТОЛЬКО валидным JSON на русском.
Принцип: ПланАм советует — пользователь выбирает. Не запрещай выбор, только предупреждай.

Правила ингредиентов:
- КАЖДЫЙ продукт отдельной строкой (нельзя «перец и помидоры 400 г»).
- quantity — число, unit — г/мл/шт/ст.л. и т.д.
- category — короткий slug: овощи, мясо, молочное, крупы, drinks, другое.
- recipe_id из каталога, если блюдо из базы; иначе null.
- Алкоголь только если allow_alcohol=true; детям алкоголь не предлагать.
- При целях спорт/похудение/здоровье — warnings про алкоголь/сахар/кофеин, но не блокируй.

Структура ответа:
{
  "summary": "...",
  "reasoning_for_user": "...",
  "menu_variants": [
    {
      "variant": "quick|economy|balanced",
      "title": "...",
      "tagline": "...",
      "explanation": "...",
      "estimated_daily_cost": "до 600 ₽",
      "total_prep_minutes": 60,
      "servings": 4,
      "meals": [
        {
          "meal_type": "breakfast|lunch|dinner|snack",
          "title": "...",
          "name": "...",
          "description": "...",
          "recipe_id": null,
          "prep_time_minutes": 20,
          "calories_estimate": 350,
          "why_selected": "..."
        }
      ],
      "ingredients": [
        {"name": "...", "quantity": "200", "unit": "г", "category": "овощи", "amount": "200 г"}
      ],
      "uses_pantry": ["молоко"],
      "warnings": []
    }
  ]
}

Ровно 3 варианта: quick, economy, balanced. Учитывай запасы и остатки блюд."""

NUTRITIONIST_SYSTEM = """Ты — дружелюбный нутрициолог ПланАм.
Кратко (2–5 предложений), по-русски, без markdown.
Не упоминай OpenAI/ChatGPT.
ПланАм советует — пользователь выбирает. Не запрещай, объясняй и рекомендуй."""

BOT_PARSE_SYSTEM = """Разбери сообщение пользователя Telegram-бота ПланАм.
JSON:
{
  "intent": "add_to_pantry|add_to_shopping|add_leftover|ask_nutritionist|generate_menu|show_summary|unknown",
  "items": [{"name": "...", "quantity": "1", "unit": "шт", "category": "..."}],
  "leftover": {"dish_name": "...", "portions": 3} или null,
  "nutritionist_question": "..." или null,
  "confidence": 0.0-1.0
}
Каждый товар отдельной строкой. intent=unknown если неясно."""


@dataclass
class MenuAiResult:
    menus: list[MenuVariant]
    summary: str = ""
    reasoning: str = ""


@dataclass
class BotParseResult:
    intent: BOT_INTENTS
    items: list[dict[str, str]] = field(default_factory=list)
    leftover: dict[str, Any] | None = None
    nutritionist_question: str | None = None
    confidence: float = 0.0
    raw_text: str = ""


def ai_status_message(exc: BaseException) -> str:
    if isinstance(exc, AiError):
        return exc.user_message
    return MSG_AI_FAILED


async def generate_menu_ai(
    context: MenuGenerationContext,
    *,
    db: Session | None = None,
    user: User | None = None,
    scope: AppScope | None = None,
    persons_count: int | None = None,
    drink_mode: str = "none",
    allow_alcohol: bool = False,
) -> MenuAiResult:
    if not ai_client.is_ai_configured():
        raise AiUnavailableError()

    user_block = context.prompt_text
    catalog: list[dict] = []
    if db and user and scope:
        ai_ctx = build_ai_user_context(
            db,
            user,
            scope,
            menu_ctx=context,
            persons_count=persons_count,
            drink_mode=drink_mode,
            allow_alcohol=allow_alcohol,
        )
        user_block = context_to_json_block(ai_ctx)
        catalog = ai_ctx.recipe_catalog

    prompt = (
        f"Контекст:\n{user_block}\n\n"
        f"Каталог рецептов (используй recipe_id когда подходит): "
        f"{catalog[:40]}\n\n"
        "Сформируй меню на один день для всех персон из контекста."
    )
    data = await ai_client.chat_json(system=MENU_SYSTEM, user=prompt, temperature=0.6)
    menus = _menu_variants_from_ai(data)
    if not menus:
        logger.warning(
            "OpenAI menu JSON missing variants; keys=%s",
            list(data.keys()) if isinstance(data, dict) else type(data).__name__,
        )
        raise AiResponseError("menu_variants missing")
    return MenuAiResult(
        menus=menus,
        summary=str(data.get("summary", "")),
        reasoning=str(data.get("reasoning_for_user", "")),
    )


def _menu_variants_from_ai(data: dict[str, Any]) -> list[MenuVariant]:
    if not isinstance(data, dict):
        logger.warning("OpenAI menu response is not a dict: %s", type(data).__name__)
        return []

    raw_variants = (
        data.get("menu_variants")
        or data.get("menus")
        or data.get("variants")
        or []
    )
    if not raw_variants and isinstance(data.get("menu"), dict):
        raw_variants = [data["menu"]]
    if not raw_variants:
        logger.warning(
            "OpenAI menu JSON has no menu_variants/menus; sample=%s",
            str(data)[:500],
        )
        return []

    menus: list[MenuVariant] = []
    for item in raw_variants:
        if not isinstance(item, dict):
            logger.warning("Skip non-dict menu variant: %s", type(item).__name__)
            continue
        try:
            variant_key = item.get("variant") or "balanced"
            meta = VARIANT_META.get(variant_key, {})
            meals_raw = item.get("meals") or []
            meals: list[MenuMeal] = []
            for m in meals_raw:
                if not isinstance(m, dict):
                    continue
                meal_type = m.get("meal_type") or "lunch"
                title = m.get("title") or m.get("name") or "Блюдо"
                meals.append(
                    MenuMeal(
                        meal_type=meal_type,  # type: ignore[arg-type]
                        name=title,
                        description=m.get("description") or m.get("why_selected") or "",
                        prep_time_minutes=int(m.get("prep_time_minutes") or 25),
                        calories_estimate=_int_or_none(
                            m.get("calories_estimate") or m.get("calories")
                        ),
                        recipe_id=m.get("recipe_id"),
                    )
                )

            ingredients = _ingredients_from_ai_rows(item.get("ingredients") or [])
            if not ingredients and item.get("shopping_items"):
                ingredients = _ingredients_from_ai_rows(item["shopping_items"])

            menus.append(
                MenuVariant(
                    variant=variant_key,  # type: ignore[arg-type]
                    title=item.get("title") or meta.get("title", "Меню"),
                    tagline=item.get("tagline") or meta.get("tagline", ""),
                    explanation=item.get("explanation")
                    or data.get("reasoning_for_user", ""),
                    estimated_daily_cost=item.get("estimated_daily_cost"),
                    total_prep_minutes=int(
                        item.get("total_prep_minutes")
                        or sum(m.prep_time_minutes for m in meals)
                    ),
                    meals=meals,
                    ingredients=ingredients or [
                        MenuIngredient(name="Вода", amount="1 л", category="drinks")
                    ],
                )
            )
        except Exception:
            logger.warning("Skip invalid menu variant item", exc_info=True)
            continue

    order = ["quick", "economy", "balanced"]
    menus.sort(
        key=lambda m: order.index(m.variant) if m.variant in order else 99
    )
    if len(menus) < 3:
        logger.warning(
            "OpenAI returned %s menu variants, expected 3",
            len(menus),
        )
        return []
    return menus[:3]


def _int_or_none(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _ingredients_from_ai_rows(rows: list[dict]) -> list[MenuIngredient]:
    raw: list[dict[str, Any]] = []
    for row in rows:
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        qty = str(row.get("quantity", "1"))
        unit = str(row.get("unit", "шт"))
        category = row.get("category") or infer_category(name, None)
        amount = row.get("amount") or f"{qty} {unit}".strip()
        raw.append(
            {
                "name": name,
                "quantity": qty,
                "unit": unit,
                "category": category,
                "amount": amount,
            }
        )
    aggregated = aggregate_ingredients_for_shopping(raw)
    return [
        MenuIngredient(
            name=i["name"],
            amount=i["amount"],
            category=i.get("category"),
        )
        for i in aggregated
    ]


async def nutritionist_answer(
    ctx: AiUserContext,
    question: str,
) -> str:
    if not ai_client.is_ai_configured():
        raise AiUnavailableError()
    system = NUTRITIONIST_SYSTEM + "\nКонтекст:\n" + context_to_json_block(ctx)
    return await ai_client.chat_text(
        system=system,
        user=question.strip(),
        temperature=0.6,
        max_tokens=400,
    )


async def generate_nutritionist_tip(ctx: AiUserContext) -> str:
    if not ai_client.is_ai_configured():
        raise AiUnavailableError()
    system = (
        NUTRITIONIST_SYSTEM
        + "\nДай один короткий совет дня (1–2 предложения) по контексту."
    )
    user = (
        f"Контекст:\n{context_to_json_block(ctx)}\n\n"
        "Если меню устарело после смены цели/семьи — мягко предложи обновить меню."
    )
    return await ai_client.chat_text(system=system, user=user, max_tokens=200)


async def analyze_recipe(
    recipe: Recipe,
    ctx: AiUserContext,
) -> RecipeEvaluationResponse:
    if not ai_client.is_ai_configured():
        raise AiUnavailableError()
    prompt = (
        f"Контекст пользователя:\n{context_to_json_block(ctx)}\n\n"
        f"Рецепт:\n{recipe_to_ai_dict(recipe)}\n\n"
        "Оцени рецепт. JSON:\n"
        '{"fit_level":"good|partial|not_recommended","title":"...","reasons":[{"code":"...","label":"..."}]}'
        "\nНе запрещай — формулируй как рекомендацию."
    )
    data = await ai_client.chat_json(
        system="Ты нутрициолог ПланАм. Только JSON.",
        user=prompt,
        max_tokens=800,
    )
    reasons = [
        RecipeEvaluationReason(
            code=str(r.get("code", "info")),
            label=str(r.get("label", "")),
        )
        for r in data.get("reasons", [])
        if r.get("label")
    ]
    fit = data.get("fit_level", "good")
    if fit not in ("good", "partial", "not_recommended"):
        fit = "partial"
    return RecipeEvaluationResponse(
        fit_level=fit,  # type: ignore[arg-type]
        title=str(data.get("title", "Оценка рецепта")),
        reasons=reasons[:6] or [
            RecipeEvaluationReason(code="ok", label="Решение за вами")
        ],
    )


async def improve_recipe(
    recipe: Recipe,
    ctx: AiUserContext,
    *,
    suggestion_id: str | None = None,
) -> RecipeImproveResponse:
    if not ai_client.is_ai_configured():
        raise AiUnavailableError()
    extra = f" Учти улучшение: {suggestion_id}." if suggestion_id else ""
    prompt = (
        f"Контекст:\n{context_to_json_block(ctx)}\n\n"
        f"Рецепт:\n{recipe_to_ai_dict(recipe)}\n{extra}\n"
        'JSON: {"suggestions":[{"id":"...","label":"...","description":"..."}],'
        '"applied_note":"..."}'
    )
    data = await ai_client.chat_json(
        system="Ты нутрициолог ПланАм. Предложи улучшения рецепта. Только JSON.",
        user=prompt,
        max_tokens=900,
    )
    suggestions = [
        RecipeImproveSuggestion(
            id=str(s.get("id", f"s{i}")),
            label=str(s.get("label", "")),
            description=str(s.get("description", "")),
        )
        for i, s in enumerate(data.get("suggestions", []))
        if s.get("label")
    ]
    return RecipeImproveResponse(
        suggestions=suggestions[:6],
        applied_note=data.get("applied_note"),
    )


async def parse_shopping_text(text: str, ctx: AiUserContext) -> BotParseResult:
    if not ai_client.is_ai_configured():
        raise AiUnavailableError()
    data = await ai_client.chat_json(
        system=BOT_PARSE_SYSTEM,
        user=f"Контекст:\n{context_to_json_block(ctx)}\n\nСообщение: {text}",
        temperature=0.3,
        max_tokens=600,
    )
    return _bot_parse_from_json(data, raw_text=text)


async def parse_receipt_text_or_image(
    *,
    image_bytes: bytes | None = None,
    text: str | None = None,
    ctx: AiUserContext | None = None,
) -> list[dict[str, Any]]:
    if not ai_client.is_ai_configured():
        raise AiUnavailableError()

    if image_bytes:
        prompt = (
            "Извлеки товары с чека. JSON: "
            '{"items":[{"name":"...","quantity":"1","unit":"шт","price":"99",'
            '"category":"молочное","is_food":true}]}. '
            "Каждый товар отдельно."
        )
        data = await ai_client.vision_json(prompt=prompt, image_bytes=image_bytes)
        return list(data.get("items") or [])

    if text:
        data = await ai_client.chat_json(
            system="Извлеки список покупок из текста. Только JSON с items[].",
            user=text,
            max_tokens=800,
        )
        return list(data.get("items") or [])

    return []


async def transcribe_voice(
    audio_bytes: bytes,
    *,
    mime: str = "audio/ogg",
) -> str:
    suffix = ".ogg" if "ogg" in mime else ".mp3"
    return await ai_client.transcribe_audio(
        audio_bytes, filename=f"voice{suffix}", mime=mime
    )


async def generate_event_plan_ai(
    ctx: AiUserContext,
    event_params: dict[str, Any],
) -> dict[str, Any]:
    if not ai_client.is_ai_configured():
        raise AiUnavailableError()
    prompt = (
        f"Контекст:\n{context_to_json_block(ctx)}\n\n"
        f"Событие:\n{event_params}\n\n"
        "JSON: dishes[], drinks[], shopping_items[] (каждый продукт отдельно), "
        "warnings[], estimated_cost_rub, nutrition_note."
    )
    return await ai_client.chat_json(
        system=MENU_SYSTEM + "\nРежим: Event Plan для мероприятия.",
        user=prompt,
        max_tokens=4096,
    )


def _bot_parse_from_json(data: dict[str, Any], *, raw_text: str) -> BotParseResult:
    intent = data.get("intent", "unknown")
    if intent not in (
        "add_to_pantry",
        "add_to_shopping",
        "add_leftover",
        "ask_nutritionist",
        "generate_menu",
        "show_summary",
        "unknown",
    ):
        intent = "unknown"
    items = []
    for row in data.get("items") or []:
        name = str(row.get("name", "")).strip()
        if name:
            items.append(
                {
                    "name": name,
                    "quantity": str(row.get("quantity", "1")),
                    "unit": str(row.get("unit", "шт")),
                    "category": str(row.get("category", "")),
                }
            )
    return BotParseResult(
        intent=intent,  # type: ignore[arg-type]
        items=items,
        leftover=data.get("leftover"),
        nutritionist_question=data.get("nutritionist_question"),
        confidence=float(data.get("confidence") or 0),
        raw_text=raw_text,
    )

