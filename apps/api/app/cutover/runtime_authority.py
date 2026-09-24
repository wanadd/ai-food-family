from __future__ import annotations

from app.cutover.runtime_store import RuntimeStore


DOMAINS = ("CORE", "FOOD_PROFILE", "RECIPE", "PLANNING", "SHOPPING", "PANTRY", "COOKING", "CONSUMPTION", "HEALTH", "ENTITLEMENT")


class AuthorityController:
    def __init__(self, store: RuntimeStore, run_id: str) -> None:
        self.store, self.run_id = store, run_id

    def set(self, domain: str, *, reader: str, writer: str) -> None:
        if domain not in DOMAINS:
            raise ValueError("unknown domain")
        self.store.set_authority(self.run_id, domain, reader=reader, writer=writer)

    def assert_single_writer(self, modes: dict[str, str]) -> None:
        if any(mode not in {"LEGACY", "V2"} for mode in modes.values()):
            raise ValueError("invalid writer authority")
