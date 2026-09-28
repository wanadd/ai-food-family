from __future__ import annotations

import threading
import time

from app.cutover.async_quiescence import inflight_provider_calls, provider_call, wait_for_provider_drain


def test_provider_call_drain_confirms_zero_inflight():
    started = threading.Event()

    def call() -> None:
        with provider_call():
            started.set()
            time.sleep(0.05)

    worker = threading.Thread(target=call)
    worker.start()
    assert started.wait(1)
    assert inflight_provider_calls() == 1
    assert wait_for_provider_drain(1) is True
    worker.join()
    assert inflight_provider_calls() == 0


def test_provider_call_drain_has_bounded_timeout():
    with provider_call():
        assert inflight_provider_calls() == 1
        assert wait_for_provider_drain(0.01) is False
    assert inflight_provider_calls() == 0
