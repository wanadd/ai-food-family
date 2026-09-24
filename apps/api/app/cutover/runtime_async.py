from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import inspect, text

from app.cutover.runtime_store import RuntimeStore


@dataclass(frozen=True)
class AsyncSnapshot:
    pending: int
    running: int
    outbox_pending: int


class AsyncControl:
    def __init__(self, engine, store: RuntimeStore) -> None:
        self.engine, self.store = engine, store

    def snapshot(self, *, jobs_table: str = "jobs", outbox_table: str = "outbox") -> AsyncSnapshot:
        inspector = inspect(self.engine)
        def count(table: str, states: tuple[str, ...]) -> int:
            if not inspector.has_table(table):
                return 0
            with self.engine.connect() as conn:
                return int(conn.execute(text(f"SELECT count(*) FROM {table} WHERE status IN (:a, :b)"), {"a": states[0], "b": states[1]}).scalar_one())
        return AsyncSnapshot(count(jobs_table, ("pending", "queued")), count(jobs_table, ("running", "leased")), count(outbox_table, ("pending", "queued")))

    def freeze(self, reason: str) -> None:
        self.store.set_control("ASYNC_FROZEN", True, reason)

    def resume(self) -> None:
        self.store.set_control("ASYNC_FROZEN", False, "resume")

    def is_frozen(self) -> bool:
        return self.store.control_enabled("ASYNC_FROZEN")

    def assert_can_acquire(self) -> None:
        if self.is_frozen():
            raise RuntimeError("CUTOVER_ASYNC_FROZEN")
