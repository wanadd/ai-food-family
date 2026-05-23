#!/usr/bin/env bash
# Restore PostgreSQL from backups/YYYY-MM-DD_HH-MM/database.sql
# Usage: ./scripts/restore.sh backups/2026-05-23_12-00
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup-directory>"
  echo "Example: $0 backups/2026-05-23_12-00"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BACKUP_DIR="$(cd "$1" 2>/dev/null && pwd || true)"
if [[ -z "$BACKUP_DIR" || ! -d "$BACKUP_DIR" ]]; then
  echo "Backup directory not found: $1"
  exit 1
fi

DUMP="$BACKUP_DIR/database.sql"
if [[ ! -f "$DUMP" ]]; then
  echo "database.sql not found in $BACKUP_DIR"
  exit 1
fi

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

echo "WARNING: This will replace the current database with:"
echo "  $DUMP"
read -r -p "Type YES to continue: " CONFIRM
if [[ "$CONFIRM" != "YES" ]]; then
  echo "Aborted."
  exit 1
fi

echo "Stopping application containers..."
docker compose -f "$COMPOSE_FILE" stop web api nginx 2>/dev/null || true

echo "Starting postgres..."
docker compose -f "$COMPOSE_FILE" up -d postgres
sleep 3

echo "Restoring database..."
docker compose -f "$COMPOSE_FILE" exec -T postgres \
  psql -U "$POSTGRES_USER" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();" \
  || true

docker compose -f "$COMPOSE_FILE" exec -T postgres \
  psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS \"$POSTGRES_DB\";"
docker compose -f "$COMPOSE_FILE" exec -T postgres \
  psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE \"$POSTGRES_DB\";"

cat "$DUMP" | docker compose -f "$COMPOSE_FILE" exec -T postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

if [[ -f "$BACKUP_DIR/env.backup" ]]; then
  read -r -p "Restore .env from backup? [y/N]: " RESTORE_ENV
  if [[ "$RESTORE_ENV" =~ ^[Yy]$ ]]; then
    cp "$BACKUP_DIR/env.backup" "$ROOT/.env"
    echo ".env restored (previous saved as .env.before-restore if existed)"
    if [[ -f "$ROOT/.env.before-restore" ]]; then
      :
    elif [[ -f "$ROOT/.env" ]]; then
      cp "$ROOT/.env" "$ROOT/.env.before-restore.bak" 2>/dev/null || true
    fi
    cp "$BACKUP_DIR/env.backup" "$ROOT/.env"
  fi
fi

echo "Starting all services..."
docker compose -f "$COMPOSE_FILE" up -d

echo "Restore finished. Check health:"
echo "  curl -s http://localhost:8000/health  (or your public /api/health)"
