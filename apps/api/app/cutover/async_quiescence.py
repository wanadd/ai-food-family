"""Small process-local provider-call drain primitive for cutover quiescence."""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from collections.abc import Iterator


_condition = threading.Condition()
_inflight = 0


def inflight_provider_calls() -> int:
    with _condition:
        return _inflight


@contextmanager
def provider_call() -> Iterator[None]:
    global _inflight
    with _condition:
        _inflight += 1
    try:
        yield
    finally:
        with _condition:
            _inflight -= 1
            _condition.notify_all()


def wait_for_provider_drain(timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    with _condition:
        while _inflight:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            _condition.wait(timeout=remaining)
        return True
