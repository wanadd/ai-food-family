from __future__ import annotations

from app.cutover.runtime_store import RuntimeStore


class RuntimeAudit:
    def __init__(self, store: RuntimeStore) -> None:
        self.store = store

    def record(self, run_id: str, action: str, result: str, details: dict | None = None) -> None:
        with self.store.engine.begin() as conn:
            self.store.audit(conn, run_id, action, result, details)

    def status(self, run_id: str) -> dict | None:
        return self.store.get_run(run_id)
