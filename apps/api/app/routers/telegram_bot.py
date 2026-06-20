import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings

WEBHOOK_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"
from app.database import get_db
from app.services.telegram_bot import process_telegram_update
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])
bot_router = APIRouter(prefix="/bot", tags=["telegram"])


def _validate_webhook_secret(request: Request) -> None:
    expected = (settings.telegram_webhook_secret or "").strip()
    if not expected:
        if not settings.is_development:
            logger.error(
                "Telegram webhook rejected: TELEGRAM_WEBHOOK_SECRET is not set",
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Webhook not configured",
            )
        return
    received = request.headers.get(WEBHOOK_SECRET_HEADER)
    if received != expected:
        logger.warning("Telegram webhook secret mismatch")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def _telegram_webhook_handler(
    request: Request,
    db: Session,
) -> dict[str, bool]:
    if not settings.telegram_bot_token:
        logger.warning("Telegram webhook ignored: TELEGRAM_BOT_TOKEN is not set")
        return {"ok": True}

    _validate_webhook_secret(request)

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
