"""Tests for Telegram API URL helper."""

from __future__ import annotations

from unittest.mock import patch

from app.telegram.api_urls import (
    DEFAULT_TELEGRAM_API_BASE_URL,
    telegram_api_base_url,
    telegram_bot_api_url,
    telegram_file_url,
)


def test_default_base_url():
    with patch("app.telegram.api_urls.settings") as mock_settings:
        mock_settings.telegram_api_base_url = ""
        assert telegram_api_base_url() == DEFAULT_TELEGRAM_API_BASE_URL


def test_custom_relay_base_url():
    with patch("app.telegram.api_urls.settings") as mock_settings:
        mock_settings.telegram_api_base_url = "https://tg-relay.planam.ru/"
        mock_settings.telegram_bot_token = "test-token"
        assert telegram_api_base_url() == "https://tg-relay.planam.ru"
        assert (
            telegram_bot_api_url("sendMessage")
            == "https://tg-relay.planam.ru/bottest-token/sendMessage"
        )
        assert (
            telegram_file_url("photos/file_1.jpg")
            == "https://tg-relay.planam.ru/file/bottest-token/photos/file_1.jpg"
        )


def test_strips_method_slash():
    with patch("app.telegram.api_urls.settings") as mock_settings:
        mock_settings.telegram_api_base_url = "https://api.telegram.org"
        mock_settings.telegram_bot_token = "abc"
        assert telegram_bot_api_url("/getWebhookInfo") == "https://api.telegram.org/botabc/getWebhookInfo"
