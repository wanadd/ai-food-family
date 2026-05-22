import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services.telegram_bot import process_telegram_update
from app.telegram.bot import get_webhook_info, resolve_webhook_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])
bot_router = APIRouter(prefix="/bot", tags=["telegram"])


async def _telegram_webhook_handler(
    request: Request,
    db: Session,
) -> dict[str, bool]:
    if not settings.telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot is not configured",
        )

    update: dict[str, Any] = await request.json()
    update_id = update.get("update_id")
    message = update.get("message") or {}
    text = (message.get("text") or "")[:80]
    has_contact = bool(message.get("contact"))

    logger.info(
        "Telegram update received: update_id=%s text=%r has_contact=%s",
        update_id,
        text,
        has_contact,
    )

    try:
        await process_telegram_update(db, update)
    except Exception:
        logger.exception("Telegram update processing failed: update_id=%s", update_id)

    return {"ok": True}


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    return await _telegram_webhook_handler(request, db)


@bot_router.post("/webhook")
async def bot_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    """Alias for deployments that register /bot/webhook."""
    return await _telegram_webhook_handler(request, db)


@router.get("/webhook/info")
async def telegram_webhook_info() -> dict:
    """Debug: current webhook URL in env and on Telegram servers."""
    return await get_webhook_info()


@router.get("/webhook/url")
def telegram_webhook_url() -> dict[str, str | None]:
    return {
        "webhook_url": resolve_webhook_url(),
        "endpoint_paths": [
            "/telegram/webhook",
            "/bot/webhook",
            "/api/telegram/webhook (via nginx)",
            "/api/bot/webhook (via nginx)",
        ],
    }
