from __future__ import annotations

from contextlib import contextmanager
from enum import StrEnum
from threading import Lock
from typing import Iterator


class CutoverState(StrEnum):
    LEGACY = "LEGACY"
    SHADOW = "SHADOW"
    WRITE_PAUSED = "WRITE_PAUSED"
    BACKFILLED = "BACKFILLED"
    RECONCILED = "RECONCILED"
    V2_ACTIVE = "V2_ACTIVE"
    STABILIZING = "STABILIZING"
    V2_ONLY = "V2_ONLY"


ALLOWED_TRANSITIONS: dict[CutoverState, frozenset[CutoverState]] = {
    CutoverState.LEGACY: frozenset({CutoverState.SHADOW}),
    CutoverState.SHADOW: frozenset({CutoverState.WRITE_PAUSED}),
    CutoverState.WRITE_PAUSED: frozenset({CutoverState.BACKFILLED, CutoverState.LEGACY}),
    CutoverState.BACKFILLED: frozenset({CutoverState.RECONCILED, CutoverState.WRITE_PAUSED}),
    CutoverState.RECONCILED: frozenset({CutoverState.V2_ACTIVE, CutoverState.BACKFILLED}),
    CutoverState.V2_ACTIVE: frozenset({CutoverState.STABILIZING, CutoverState.RECONCILED}),
    CutoverState.STABILIZING: frozenset({CutoverState.V2_ONLY, CutoverState.V2_ACTIVE}),
    CutoverState.V2_ONLY: frozenset({CutoverState.STABILIZING}),
}


class CutoverStateMachine:
    def __init__(self, initial: CutoverState = CutoverState.LEGACY) -> None:
        self.state = initial
        self.writer_mode = "LEGACY"
        self.reader_mode = "LEGACY"
        self.write_paused = False
        self._lock = Lock()

    def transition(self, target: CutoverState) -> CutoverState:
        with self._lock:
            if target not in ALLOWED_TRANSITIONS[self.state]:
                raise ValueError(f"invalid cutover transition {self.state}->{target}")
            self.state = target
            if target is CutoverState.WRITE_PAUSED:
                self.write_paused = True
            if target in {CutoverState.LEGACY, CutoverState.V2_ONLY}:
                self.write_paused = False
            return self.state

    def set_writer(self, mode: str) -> None:
        if mode not in {"LEGACY", "V2"} or (mode == "V2" and self.state not in {CutoverState.RECONCILED, CutoverState.V2_ACTIVE, CutoverState.STABILIZING, CutoverState.V2_ONLY}):
            raise ValueError("writer switch requires reconciled cutover state")
        self.writer_mode = mode

    def set_reader(self, mode: str) -> None:
        if mode not in {"LEGACY", "SHADOW", "V2_COMPAT", "V2"}:
            raise ValueError("unknown reader mode")
        self.reader_mode = mode

    def assert_write_allowed(self) -> None:
        if self.write_paused:
            raise RuntimeError("CUTOVER_WRITE_PAUSED")

    @contextmanager
    def cutover_lock(self) -> Iterator[None]:
        acquired = self._lock.acquire(blocking=False)
        if not acquired:
            raise RuntimeError("CUTOVER_LOCK_HELD")
        try:
            yield
        finally:
            self._lock.release()
