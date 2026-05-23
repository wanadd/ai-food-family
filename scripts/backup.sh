#!/usr/bin/env bash
# Create PostgreSQL dump + copy .env into backups/YYYY-MM-DD_HH-MM/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
if [[ ! -f "$COMPOSE_FILE" ]]; then
  COMPOSE_FILE="docker-compose.yml"
fi

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:-aifood}"
POSTGRES_DB="${POSTGRES_DB:-aifood}"
TS="$(date +%Y-%m-%d_%H-%M)"
TARGET="$ROOT/backups/$TS"
mkdir -p "$TARGET"

echo "Creating backup in $TARGET"

docker compose -f "$COMPOSE_FILE" exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" --no-owner --no-acl \
  > "$TARGET/database.sql"

if [[ -f "$ROOT/.env" ]]; then
  cp "$ROOT/.env" "$TARGET/env.backup"
else
  echo "Warning: .env not found, skipping env.backup"
fi

date -u +"%Y-%m-%dT%H:%M:%SZ" > "$TARGET/timestamp.txt"
echo "Backup complete: $TARGET"
