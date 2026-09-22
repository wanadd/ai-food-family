from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

API_ROOT = Path(__file__).resolve().parents[1]


def _acceptance_url() -> str:
    url = os.getenv("PLANAM_V2_POSTGRES_ACCEPTANCE_URL")
    if not url:
        pytest.skip("PLANAM_V2_POSTGRES_ACCEPTANCE_URL is not configured")
    return url


def _reset_public_schema(url: str) -> None:
    engine = create_engine(url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
    finally:
        engine.dispose()


def _run_alembic(url: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["ALEMBIC_DATABASE_URL"] = url
    env["DATABASE_URL"] = url
    return subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        cwd=API_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _assert_alembic_head(url: str) -> None:
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    finally:
        engine.dispose()

    assert revision == "20260922_0001"


def test_v2_baseline_real_postgresql_acceptance():
    url = _acceptance_url()
    _reset_public_schema(url)

    fresh = _run_alembic(url)
    assert fresh.returncode == 0, fresh.stderr
    _assert_alembic_head(url)

    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE wave01_sentinel (id INTEGER PRIMARY KEY, label TEXT NOT NULL)"))
            connection.execute(text("INSERT INTO wave01_sentinel (id, label) VALUES (1, 'preserve')"))
    finally:
        engine.dispose()

    repeat = _run_alembic(url)
    assert repeat.returncode == 0, repeat.stderr

    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            preserved = connection.execute(text("SELECT label FROM wave01_sentinel WHERE id = 1")).scalar_one()
            tables = set(
                connection.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public'"
                    )
                ).scalars()
            )
    finally:
        engine.dispose()

    assert preserved == "preserve"
    assert {"alembic_version", "wave01_sentinel"} <= tables
    assert "core_accounts" not in tables
    assert "food_profiles" not in tables
    assert "recipe_versions" not in tables

    _reset_public_schema(url)
    first = subprocess.Popen(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        cwd=API_ROOT,
        env={**os.environ, "ALEMBIC_DATABASE_URL": url, "DATABASE_URL": url},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    second = subprocess.Popen(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        cwd=API_ROOT,
        env={**os.environ, "ALEMBIC_DATABASE_URL": url, "DATABASE_URL": url},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    first_stdout, first_stderr = first.communicate(timeout=30)
    second_stdout, second_stderr = second.communicate(timeout=30)

    assert first.returncode == 0, first_stderr or first_stdout
    assert second.returncode == 0, second_stderr or second_stdout
    _assert_alembic_head(url)

    engine = create_engine(url)
    try:
        connection = engine.connect()
        transaction = connection.begin()
        try:
            with pytest.raises(Exception):
                connection.execute(text("SELECT * FROM definitely_missing_wave01_table"))
            with pytest.raises(Exception):
                connection.execute(text("SELECT 1"))
        finally:
            transaction.rollback()
            connection.close()
    finally:
        engine.dispose()

    after_abort = _run_alembic(url)
    assert after_abort.returncode == 0, after_abort.stderr
    _assert_alembic_head(url)
