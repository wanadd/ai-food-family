from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def connection():
    url = os.getenv("OD17_TEST_DATABASE_URL")
    if not url:
        pytest.skip("OD17_TEST_DATABASE_URL is required for PostgreSQL constraint acceptance")
    engine = create_engine(url)
    if engine.dialect.name != "postgresql" or engine.url.host not in {"127.0.0.1", "localhost"}:
        engine.dispose()
        pytest.fail("OD-17 constraint test requires local PostgreSQL")
    with engine.connect() as conn:
        outer = conn.begin()
        try:
            assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "20260928_0020"
            yield conn
        finally:
            outer.rollback()
    engine.dispose()


@pytest.mark.parametrize("table,required", [
    ("shopping_lists", "status, idempotency_key"),
    ("pantry_inventory", "display_text"),
    ("receipt_documents", "idempotency_key"),
])
def test_postgres_owner_xor(connection, table: str, required: str):
    person = str(uuid.uuid4())
    household = str(uuid.uuid4())
    connection.execute(text("INSERT INTO core_persons(person_id) VALUES (:id)"), {"id": person})
    connection.execute(text("INSERT INTO core_households(household_id) VALUES (:id)"), {"id": household})
    extra = {
        "shopping_lists": ("'ACTIVE', 'od17-test'"),
        "pantry_inventory": ("'test'"),
        "receipt_documents": ("'od17-test'"),
    }[table]
    for person_id, household_id, allowed in (
        (person, None, True), (None, household, True),
        (person, household, False), (None, None, False),
    ):
        nested = connection.begin_nested()
        pk = {"shopping_lists": "shopping_list_id", "pantry_inventory": "pantry_inventory_id", "receipt_documents": "receipt_document_id"}[table]
        statement = text(f"INSERT INTO {table} ({pk}, person_id, household_id, {required}) "
                         f"VALUES (:id, :person, :household, {extra})")
        if allowed:
            connection.execute(statement, {"id": str(uuid.uuid4()), "person": person_id, "household": household_id})
        else:
            with pytest.raises(IntegrityError):
                connection.execute(statement, {"id": str(uuid.uuid4()), "person": person_id, "household": household_id})
        nested.rollback()


def test_0019_household_list_remains_household_owned(connection):
    rows = connection.execute(text("SELECT person_id, household_id FROM shopping_lists WHERE idempotency_key='fixture'")).all()
    if not rows:
        pytest.skip("upgrade rehearsal fixture not installed")
    assert len(rows) == 1
    assert rows[0].person_id is None
    assert rows[0].household_id is not None
