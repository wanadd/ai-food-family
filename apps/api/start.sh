#!/bin/sh
set -e

HOST="${UVICORN_HOST:-0.0.0.0}"
PORT="${UVICORN_PORT:-8000}"

# Production must never use --reload (WatchFiles / hot reload).
if [ "${ENVIRONMENT:-development}" = "production" ]; then
  WORKERS="${UVICORN_WORKERS:-2}"
  exec uvicorn app.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --proxy-headers \
    --forwarded-allow-ips "*"
fi

exec uvicorn app.main:app \
  --host "$HOST" \
  --port "$PORT" \
  --reload
