from typing import Any

import psycopg2
import redis

from app.config import settings


def check_postgres() -> str:
    try:
        conn = psycopg2.connect(settings.database_url)
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        conn.close()
        return "ok"
    except Exception:
        return "error"


def check_redis() -> str:
    try:
        client = redis.from_url(settings.redis_url)
        client.ping()
        return "ok"
    except Exception:
        return "error"


def run_health_checks() -> dict[str, Any]:
    services = {
        "postgres": check_postgres(),
        "redis": check_redis(),
    }
    status = "ok" if all(value == "ok" for value in services.values()) else "degraded"
    return {"status": status, "services": services}
