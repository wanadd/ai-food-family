from __future__ import annotations

from contextlib import contextmanager
from sqlalchemy import delete, insert
from app.cutover.runtime_schema import cutover_locks


class RuntimeLock:
    def __init__(self, engine, run_id: str, name: str = "v2_cutover") -> None:
        self.engine, self.run_id, self.name = engine, run_id, name
        self._connection = None

    def acquire(self) -> None:
        self._connection = self.engine.connect()
        try:
            self._connection.execute(insert(cutover_locks).values(lock_name=self.name, run_id=self.run_id))
            self._connection.commit()
        except Exception as exc:
            self._connection.rollback()
            # SQLite in-memory test engines may share one DBAPI connection;
            # invalidating it would also destroy an existing holder's lock.
            if self._connection.dialect.name != "sqlite":
                self._connection.invalidate()
            self._connection.close()
            self._connection = None
            raise RuntimeError("CUTOVER_LOCK_HELD") from exc

    def release(self) -> None:
        if self._connection is None:
            return
        try:
            self._connection.execute(delete(cutover_locks).where(cutover_locks.c.lock_name == self.name, cutover_locks.c.run_id == self.run_id))
            self._connection.commit()
        except Exception:
            self._connection.invalidate()
            raise
        finally:
            self._connection.close()
            self._connection = None

    @contextmanager
    def held(self):
        self.acquire()
        try:
            yield self
        finally:
            self.release()
