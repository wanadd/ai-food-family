"""DB-backed jobs/outbox operational owner for cutover quiescence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import inspect, text

from app.cutover.runtime_async import AsyncControl
from app.cutover.runtime_store import RuntimeStore
from app.cutover.async_quiescence import inflight_provider_calls, wait_for_provider_drain


@dataclass(frozen=True)
class JobsOutboxStatus:
    frozen: bool | None
    active_mutating_jobs: int | None
    pending_jobs: int | None
    in_flight_jobs: int | None
    outbox_pending: int | None
    outbox_failed: int | None
    outbox_processing: int | None
    stale_legacy_workers: int | None
    quiescent: bool | None
    details: tuple[str, ...] = ()
    inflight_provider_calls: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class JobsOutboxOwner:
    """Owns observation and freeze/resume composition, not job business logic."""

    def __init__(self, engine, store: RuntimeStore) -> None:
        self.engine, self.store = engine, store
        self.async_control = AsyncControl(engine, store)

    def status(self, *, run_id: str | None = None) -> JobsOutboxStatus:
        try:
            inspector = inspect(self.engine)
            jobs = inspector.has_table("durable_jobs_v2")
            outbox = inspector.has_table("outbox_events_v2")
            if not jobs and not outbox:
                return JobsOutboxStatus(None, None, None, None, None, None, None, None, None, ("jobs/outbox tables are unavailable",))

            def count(table: str, clause: str) -> int:
                with self.engine.connect() as conn:
                    return int(conn.execute(text(f"SELECT count(*) FROM {table} WHERE {clause}")).scalar_one())

            pending = count("durable_jobs_v2", "status IN ('PENDING', 'RETRY')") if jobs else 0
            active = count("durable_jobs_v2", "status = 'RUNNING'") if jobs else 0
            outbox_pending = count("outbox_events_v2", "status = 'PENDING'") if outbox else 0
            outbox_processing = count("outbox_events_v2", "status = 'PROCESSING'") if outbox else 0
            outbox_failed = count("outbox_events_v2", "status IN ('FAILED', 'DEAD')") if outbox else 0
            frozen = self.async_control.is_frozen()
            writer = None
            if run_id:
                run = self.store.get_run(run_id)
                writer = run.get("writer_authority") if run else None
            stale = 0 if writer in {None, "V2"} else active + outbox_processing
            inflight = inflight_provider_calls()
            quiescent = frozen and active == 0 and outbox_processing == 0 and stale == 0 and inflight == 0
            return JobsOutboxStatus(frozen, active, pending, active, outbox_pending, outbox_failed, outbox_processing, stale, quiescent, (), inflight)
        except Exception as exc:
            return JobsOutboxStatus(None, None, None, None, None, None, None, None, None, (type(exc).__name__, str(exc)[:300]))

    def freeze(self, reason: str, *, timeout_seconds: float = 30.0) -> JobsOutboxStatus:
        self.async_control.freeze(reason)
        if not wait_for_provider_drain(timeout_seconds):
            raise RuntimeError("ASYNC_PROVIDER_DRAIN_TIMEOUT")
        result = self.status()
        if result.inflight_provider_calls != 0:
            raise RuntimeError("ASYNC_PROVIDER_DRAIN_UNCONFIRMED")
        return result

    def resume(self, reason: str = "resume") -> JobsOutboxStatus:
        self.async_control.resume()
        return self.status()

    def require_quiescent(self, *, run_id: str | None = None) -> JobsOutboxStatus:
        result = self.status(run_id=run_id)
        if result.quiescent is not True:
            raise RuntimeError("JOBS_OUTBOX_NOT_QUIESCENT")
        return result
