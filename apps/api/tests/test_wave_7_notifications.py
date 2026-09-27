from __future__ import annotations

import ast
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1]


def test_wave_7_migration_is_additive_and_has_exact_five_tables():
    source = (API_ROOT / "alembic/versions/20260927_0018_wave_7_async_notifications.py").read_text()
    assert 'revision = "20260927_0018"' in source
    assert 'down_revision: str | None = "20260927_0017"' in source
    assert source.count('op.create_table(') == 5
    assert "notification_preferences" in source
    assert "notification_intents" in source
    assert "notification_deliveries" in source
    assert '"jobs"' in source
    assert '"outbox_events"' in source
    assert "DROP DATABASE" not in source


def test_wave_7_domain_has_no_direct_telegram_network_dependency():
    tree = ast.parse((API_ROOT / "app/notifications/v2_service.py").read_text())
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert "httpx" not in names
    assert "telegram_bot_api_url" not in names


def test_wave_7_router_exposes_only_preferences_route():
    source = (API_ROOT / "app/notifications/router.py").read_text()
    assert '"/notification-preferences"' in source
    assert source.count("@router.") == 1


def test_wave_7_platform_adapter_keeps_telegram_capability_access_isolated():
    source = (API_ROOT.parent.parent / "apps/web/lib/platform/telegram-adapter.ts").read_text()
    assert "createTelegramPlatformAdapter" in source
    assert "readTelegramWebApp" in source


def test_wave_7_update_dedupe_uses_canonical_outbox_boundary():
    source = (API_ROOT / "app/notifications/update_dedupe.py").read_text()
    assert "telegram.update.received" in source
    assert "OutboxEvent" in source
    assert "send_telegram_message" not in source
