import asyncio
from types import SimpleNamespace

import pytest
import redis

from app.config import settings
from app.services import ai_client, legacy_outbound_guard as guard, telegram_bot
from app.telegram import bot, files, messages, messaging


class FakeRedis:
    value = None

    def get(self, key):
        assert key == guard.FROZEN_KEY
        return self.value


class ForbiddenHttpClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, *args, **kwargs):
        raise AssertionError("provider POST must not run")

    async def get(self, *args, **kwargs):
        raise AssertionError("provider GET must not run")


@pytest.fixture
def frozen(monkeypatch):
    state = FakeRedis()
    state.value = b"1"
    monkeypatch.setattr(settings, "legacy_outbound_guard_enabled", True)
    monkeypatch.setattr(settings, "telegram_bot_token", "test-token")
    monkeypatch.setattr(settings, "telegram_outbound_enabled", True)
    monkeypatch.setattr(guard, "redis_client", lambda: state)
    monkeypatch.setattr("httpx.AsyncClient", ForbiddenHttpClient)
    return state


def test_shared_flag_fail_closed_and_normal_mode(frozen, monkeypatch):
    assert guard.outbound_allowed() is False
    frozen.value = None
    assert guard.outbound_allowed() is True
    frozen.value = b"unexpected"
    assert guard.outbound_allowed() is False
    def unavailable():
        raise redis.ConnectionError()

    monkeypatch.setattr(guard, "redis_client", unavailable)
    assert guard.outbound_allowed() is False


def test_telegram_sites_suppress_all_http_calls(frozen):
    assert asyncio.run(messages.send_telegram_message(123, "test")) is False
    assert asyncio.run(messaging.send_telegram_message(123, "test")) is None
    assert asyncio.run(messaging.answer_callback_query("callback")) is None
    assert asyncio.run(telegram_bot.send_telegram_message(123, "test")) is None
    assert asyncio.run(telegram_bot.answer_callback_query("callback")) is None
    assert asyncio.run(files.download_telegram_file("file")) is None
    with pytest.raises(guard.OutboundFrozen):
        asyncio.run(bot._telegram_api("getWebhookInfo"))


def test_ai_and_ocr_sites_suppress_provider_calls(frozen, monkeypatch):
    class ForbiddenCreate:
        async def create(self, **kwargs):
            raise AssertionError("AI provider must not run")

    client = SimpleNamespace(
        chat=SimpleNamespace(completions=ForbiddenCreate()),
        audio=SimpleNamespace(transcriptions=ForbiddenCreate()),
    )
    monkeypatch.setattr(ai_client, "get_openai_client", lambda: client)
    for call in (
        lambda: ai_client.chat_text(system="s", user="u"),
        lambda: ai_client.chat_json(system="s", user="u"),
        lambda: ai_client.transcribe_audio(b"audio"),
        lambda: ai_client.vision_json(prompt="p", image_bytes=b"image"),
    ):
        with pytest.raises(ai_client.AiResponseError):
            asyncio.run(call())
