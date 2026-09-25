from __future__ import annotations

import multiprocessing
import os
from collections import Counter

import pytest
from sqlalchemy import create_engine, text


POSTGRES_URL = os.getenv("PLANAM_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="PLANAM_TEST_POSTGRES_URL is required for disposable PostgreSQL concurrency tests",
)


def _init_db_worker(database_url: str, barrier, result_queue) -> None:
    os.environ["DATABASE_URL"] = database_url
    try:
        barrier.wait(timeout=60)
        from app.database import init_db

        init_db()
    except BaseException as exc:  # pragma: no cover - asserted through the queue
        result_queue.put(("error", type(exc).__name__, str(exc)))
    else:
        result_queue.put(("ok",))


def _run_concurrent_init(database_url: str, callers: int = 2) -> list[tuple]:
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(callers)
    result_queue = context.Queue()
    processes = [
        context.Process(
            target=_init_db_worker,
            args=(database_url, barrier, result_queue),
        )
        for _ in range(callers)
    ]
    for process in processes:
        process.start()
    results = [result_queue.get(timeout=180) for _ in processes]
    for process in processes:
        process.join(timeout=30)
    assert all(process.exitcode == 0 for process in processes)
    return results


def _reset_schema(database_url: str) -> None:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    engine.dispose()


def _assert_no_duplicate_relations(database_url: str) -> None:
    engine = create_engine(database_url)
    with engine.connect() as connection:
        duplicate_names = connection.execute(
            text(
                """
                SELECT relname, count(*)
                FROM pg_class
                WHERE relnamespace = 'public'::regnamespace
                GROUP BY relname
                HAVING count(*) > 1
                """
            )
        ).all()
    engine.dispose()
    assert duplicate_names == []


def test_concurrent_init_db_empty_initialized_and_higher_concurrency() -> None:
    assert POSTGRES_URL is not None
    _reset_schema(POSTGRES_URL)

    empty_results = _run_concurrent_init(POSTGRES_URL, callers=2)
    assert Counter(result[0] for result in empty_results) == Counter({"ok": 2})
    _assert_no_duplicate_relations(POSTGRES_URL)

    initialized_results = _run_concurrent_init(POSTGRES_URL, callers=2)
    assert Counter(result[0] for result in initialized_results) == Counter({"ok": 2})
    _assert_no_duplicate_relations(POSTGRES_URL)

    high_concurrency_results = _run_concurrent_init(POSTGRES_URL, callers=4)
    assert Counter(result[0] for result in high_concurrency_results) == Counter({"ok": 4})
    _assert_no_duplicate_relations(POSTGRES_URL)
