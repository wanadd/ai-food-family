import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class TelegramAuthError(Exception):
    pass


@dataclass(frozen=True)
class TelegramWebAppUser:
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    photo_url: str | None = None
    is_premium: bool | None = None


def validate_init_data(
    init_data: str,
    bot_token: str,
    *,
    max_age_seconds: int = 86_400,
) -> TelegramWebAppUser:
    if not bot_token:
        raise TelegramAuthError("Telegram bot token is not configured")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise TelegramAuthError("initData hash is missing")

    auth_date_raw = parsed.get("auth_date")
    if not auth_date_raw:
        raise TelegramAuthError("auth_date is missing")

    try:
        auth_date = int(auth_date_raw)
    except ValueError as exc:
        raise TelegramAuthError("auth_date is invalid") from exc

    if time.time() - auth_date > max_age_seconds:
        raise TelegramAuthError("initData is expired")

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(parsed.items())
    )
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise TelegramAuthError("initData signature is invalid")

    user_raw = parsed.get("user")
    if not user_raw:
        raise TelegramAuthError("user is missing in initData")

    try:
        user_payload = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise TelegramAuthError("user payload is invalid") from exc

    try:
        telegram_id = int(user_payload["id"])
        first_name = str(user_payload["first_name"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TelegramAuthError("user payload is incomplete") from exc

    return TelegramWebAppUser(
        id=telegram_id,
        first_name=first_name,
        last_name=user_payload.get("last_name"),
        username=user_payload.get("username"),
        language_code=user_payload.get("language_code"),
        photo_url=user_payload.get("photo_url"),
        is_premium=user_payload.get("is_premium"),
    )
