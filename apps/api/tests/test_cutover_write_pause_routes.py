from __future__ import annotations

import asyncio

from app.cutover import maintenance
from app.main import app


def _invoke(middleware, method: str, path: str) -> tuple[int | None, bool]:
    messages = []
    called = False

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    async def inner(scope, receive, send):
        nonlocal called
        called = True
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    guard = middleware(inner, engine=object(), enforce=True)
    asyncio.run(guard({"type": "http", "method": method, "path": path}, receive, send))
    start = next((message for message in messages if message["type"] == "http.response.start"), None)
    return (start["status"] if start else None), called


def test_all_registered_mutations_are_blocked_before_handler(monkeypatch):
    monkeypatch.setattr(maintenance, "read_maintenance_state", lambda _: maintenance.MaintenanceState(True, True))
    routes = sorted({(method, route.path) for route in app.routes for method in (getattr(route, "methods", None) or [])
                     if method in {"POST", "PUT", "PATCH", "DELETE"}})
    assert routes
    for method, path in routes:
        status, called = _invoke(maintenance.WritePauseMiddleware, method, path)
        assert (status, called) == (503, False), (method, path)


def test_pause_off_passes_and_health_remains_readable(monkeypatch):
    monkeypatch.setattr(maintenance, "read_maintenance_state", lambda _: maintenance.MaintenanceState(False, False))
    assert _invoke(maintenance.WritePauseMiddleware, "POST", "/api/v2/persons/test/shopping/items") == (204, True)
    monkeypatch.setattr(maintenance, "read_maintenance_state", lambda _: maintenance.MaintenanceState(True, True))
    assert _invoke(maintenance.WritePauseMiddleware, "GET", "/health/cutover") == (204, True)
    assert _invoke(maintenance.WritePauseMiddleware, "GET", "/api/v2/persons/test/shopping") == (503, False)


def test_missing_control_fails_closed(monkeypatch):
    def unavailable(_):
        raise maintenance.MaintenanceControlUnavailable("missing")

    monkeypatch.setattr(maintenance, "read_maintenance_state", unavailable)
    assert _invoke(maintenance.WritePauseMiddleware, "POST", "/api/v2/persons/test/shopping/items") == (503, False)
