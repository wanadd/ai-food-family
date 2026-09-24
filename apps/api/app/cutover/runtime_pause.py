from __future__ import annotations

from app.cutover.runtime_store import RuntimeStore


class WritePause:
    def __init__(self, store: RuntimeStore) -> None:
        self.store = store

    def pause(self, reason: str) -> None:
        self.store.set_control("WRITE_PAUSED", True, reason)

    def resume(self) -> None:
        self.store.set_control("WRITE_PAUSED", False, "resume")

    def assert_allowed(self) -> None:
        if self.store.control_enabled("WRITE_PAUSED"):
            raise RuntimeError("CUTOVER_WRITE_PAUSED")
