from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import re
from typing import Any

from sqlalchemy import Engine, event, inspect, text
from sqlalchemy.orm import Session


class ApplicationMutationBlocked(RuntimeError):
    """A normal application mutation is not allowed during cutover."""

    def __init__(self, reason: str = "CUTOVER_WRITE_PAUSED") -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class CutoverExecutionContext:
    run_id: str
    environment: str
    lock_name: str = "v2_cutover"
    lock_verified: bool = False
    state: str = "LEGACY"
    execution_authorized: bool = False


_execution_context: ContextVar[CutoverExecutionContext | None] = ContextVar("planam_cutover_execution", default=None)
_async_context: ContextVar[bool] = ContextVar("planam_async_execution", default=False)


@contextmanager
def cutover_execution(context: CutoverExecutionContext):
    token = _execution_context.set(context)
    try:
        yield context
    finally:
        _execution_context.reset(token)


@contextmanager
def async_execution():
    token = _async_context.set(True)
    try:
        yield
    finally:
        _async_context.reset(token)


def _domain_for_table(table_name: str) -> str:
    name = table_name.lower()
    prefixes = {
        "food": "FOOD_PROFILE", "nutrition": "NUTRITION_TARGET", "recipe": "RECIPE",
        "plan": "PLANNING", "menu": "PLANNING", "shopping": "SHOPPING",
        "pantry": "PANTRY", "receipt": "RECEIPT", "external_food": "RECEIPT",
        "cooking": "COOKING", "consumption": "CONSUMPTION", "meal_consumption": "CONSUMPTION",
        "health": "HEALTH", "progress": "HEALTH", "training": "HEALTH",
        "subscription": "ENTITLEMENT", "entitlement": "ENTITLEMENT", "billing": "ENTITLEMENT",
        "notification": "NOTIFICATION", "care_notification": "NOTIFICATION",
        "job": "JOBS", "outbox": "OUTBOX", "task": "JOBS",
        "admin": "ADMIN", "user": "CORE", "family": "CORE", "core_": "CORE",
    }
    for prefix, domain in prefixes.items():
        if name.startswith(prefix) or f"_{prefix}" in name:
            return domain
    return "CORE"


def _is_v2_table(table_name: str) -> bool:
    name = table_name.lower()
    return name.startswith(("core_", "food_", "nutrition_target_versions", "recipe_v2", "recipes_v2", "planning_", "shopping_v2", "pantry_v2", "cooking_v2", "consumption_v2", "health_v2", "entitlement_v2"))


def _runtime_tables_available(connection) -> bool:
    try:
        return inspect(connection).has_table("cutover_runtime_control") and inspect(connection).has_table("cutover_runtime_authority")
    except Exception:
        return False


def _application_write_guard(session: Session, flush_context: Any, instances: Any) -> None:
    if not session.new and not session.dirty and not session.deleted:
        return
    execution = _execution_context.get()
    connection = session.connection()
    if not _runtime_tables_available(connection):
        return
    if execution is not None:
        # Runtime writes must be established by the caller; a context alone
        # never grants normal application code a bypass flag.
        if (execution.environment.upper() != "PRODUCTION" or not execution.run_id or not execution.lock_verified or not execution.execution_authorized or execution.state not in {"WRITE_PAUSED", "ASYNC_DRAINED", "MIGRATED", "BACKFILLING"}):
            raise ApplicationMutationBlocked("INVALID_CUTOVER_EXECUTION_CONTEXT")
        return
    paused = connection.execute(text("SELECT enabled FROM cutover_runtime_control WHERE control_name = 'WRITE_PAUSED'" )).scalar()
    if bool(paused):
        raise ApplicationMutationBlocked()
    if _async_context.get():
        frozen = connection.execute(text("SELECT enabled FROM cutover_runtime_control WHERE control_name = 'ASYNC_FROZEN'" )).scalar()
        if bool(frozen):
            raise ApplicationMutationBlocked("CUTOVER_ASYNC_FROZEN")
    for obj in (*session.new, *session.dirty, *session.deleted):
        mapper = inspect(obj, raiseerr=False)
        table = getattr(getattr(mapper, "mapper", None), "local_table", None)
        if table is None:
            continue
        table_name = table.name
        domain = _domain_for_table(table_name)
        mode = connection.execute(text("SELECT writer_mode FROM cutover_runtime_authority WHERE domain = :domain"), {"domain": domain}).scalar()
        if mode is None:
            continue
        target = "V2" if _is_v2_table(table_name) else "LEGACY"
        if mode != target:
            raise ApplicationMutationBlocked("WRITER_AUTHORITY_MISMATCH")


def _application_commit_guard(session: Session) -> None:
    _application_write_guard(session, None, None)


def _application_dml_guard(orm_execute_state: Any) -> None:
    statement = str(orm_execute_state.statement).lstrip()
    if not getattr(orm_execute_state, "is_dml", False) and not re.match(r"^(?:INSERT|UPDATE|DELETE)\b", statement, re.IGNORECASE):
        return
    session = orm_execute_state.session
    connection = session.connection()
    if not _runtime_tables_available(connection):
        return
    execution = _execution_context.get()
    if execution is not None:
        if (execution.environment.upper() != "PRODUCTION" or not execution.run_id or not execution.lock_verified or not execution.execution_authorized or execution.state not in {"WRITE_PAUSED", "ASYNC_DRAINED", "MIGRATED", "BACKFILLING"}):
            raise ApplicationMutationBlocked("INVALID_CUTOVER_EXECUTION_CONTEXT")
        return
    paused = connection.execute(text("SELECT enabled FROM cutover_runtime_control WHERE control_name = 'WRITE_PAUSED'" )).scalar()
    if bool(paused):
        raise ApplicationMutationBlocked()
    if _async_context.get():
        frozen = connection.execute(text("SELECT enabled FROM cutover_runtime_control WHERE control_name = 'ASYNC_FROZEN'" )).scalar()
        if bool(frozen):
            raise ApplicationMutationBlocked("CUTOVER_ASYNC_FROZEN")
    match = re.search(r"\b(?:into|update|delete\s+from)\s+([\w\".]+)", statement, re.IGNORECASE)
    if not match:
        return
    table_name = match.group(1).replace('"', "").split(".")[-1]
    domain = _domain_for_table(table_name)
    mode = connection.execute(text("SELECT writer_mode FROM cutover_runtime_authority WHERE domain = :domain"), {"domain": domain}).scalar()
    if mode is not None and mode != ("V2" if _is_v2_table(table_name) else "LEGACY"):
        raise ApplicationMutationBlocked("WRITER_AUTHORITY_MISMATCH")


def _engine_dml_guard(conn: Any, clauseelement: Any, multiparams: Any, params: Any, execution_options: Any) -> None:
    statement = str(clauseelement).lstrip()
    if not re.match(r"^(?:INSERT|UPDATE|DELETE)\b", statement, re.IGNORECASE):
        return
    if "cutover_runtime_" in statement.lower():
        return
    if not _runtime_tables_available(conn):
        return
    execution = _execution_context.get()
    if execution is not None:
        if (execution.environment.upper() != "PRODUCTION" or not execution.run_id or not execution.lock_verified or not execution.execution_authorized or execution.state not in {"WRITE_PAUSED", "ASYNC_DRAINED", "MIGRATED", "BACKFILLING"}):
            raise ApplicationMutationBlocked("INVALID_CUTOVER_EXECUTION_CONTEXT")
        return
    paused = conn.execute(text("SELECT enabled FROM cutover_runtime_control WHERE control_name = 'WRITE_PAUSED'" )).scalar()
    if bool(paused):
        raise ApplicationMutationBlocked()
    if _async_context.get() and conn.execute(text("SELECT enabled FROM cutover_runtime_control WHERE control_name = 'ASYNC_FROZEN'" )).scalar():
        raise ApplicationMutationBlocked("CUTOVER_ASYNC_FROZEN")


event.listen(Session, "before_flush", _application_write_guard)
event.listen(Session, "before_commit", _application_commit_guard)
event.listen(Session, "do_orm_execute", _application_dml_guard)
event.listen(Engine, "before_execute", _engine_dml_guard)
