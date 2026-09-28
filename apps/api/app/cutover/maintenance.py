"""Production request and async boundaries for the canonical cutover controls."""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError


class MaintenanceControlUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class MaintenanceState:
    write_paused: bool
    async_frozen: bool


def read_maintenance_state(engine: Engine) -> MaintenanceState:
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text("SELECT control_name, enabled FROM cutover_runtime_control "
                     "WHERE control_name IN ('WRITE_PAUSED', 'ASYNC_FROZEN')")
            ).all()
    except SQLAlchemyError as exc:
        raise MaintenanceControlUnavailable("CUTOVER_CONTROL_UNAVAILABLE") from exc
    controls = {name: bool(enabled) for name, enabled in rows}
    if "WRITE_PAUSED" not in controls or "ASYNC_FROZEN" not in controls:
        raise MaintenanceControlUnavailable("CUTOVER_CONTROL_INCOMPLETE")
    return MaintenanceState(controls["WRITE_PAUSED"], controls["ASYNC_FROZEN"])


def assert_async_available(engine: Engine) -> None:
    state = read_maintenance_state(engine)
    if state.write_paused or state.async_frozen:
        raise MaintenanceControlUnavailable("CUTOVER_ASYNC_FROZEN")


class WritePauseMiddleware:
    """Block before routing, authentication bootstrap, provider calls, or files."""

    _READ_WHILE_PAUSED = frozenset({"/", "/health", "/health/live", "/health/cutover"})

    def __init__(self, app, *, engine: Engine, enforce: bool) -> None:
        self.app = app
        self.engine = engine
        self.enforce = enforce

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or not self.enforce:
            await self.app(scope, receive, send)
            return
        method = scope["method"].upper()
        path = scope["path"]
        if method in {"GET", "HEAD", "OPTIONS"} and path in self._READ_WHILE_PAUSED:
            await self.app(scope, receive, send)
            return
        try:
            paused = read_maintenance_state(self.engine).write_paused
        except MaintenanceControlUnavailable:
            paused = True
        if not paused:
            await self.app(scope, receive, send)
            return
        body = json.dumps({"error": {"code": "WRITE_PAUSED", "message": "Service maintenance is active."}}).encode()
        await send({"type": "http.response.start", "status": 503, "headers": [
            (b"content-type", b"application/json"), (b"retry-after", b"30"),
            (b"cache-control", b"no-store"), (b"x-planam-write-paused", b"1"),
        ]})
        await send({"type": "http.response.body", "body": body})
