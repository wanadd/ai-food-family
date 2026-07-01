#!/usr/bin/env bash
set -euo pipefail

# Run on the VPS. This is read-only against Postgres.
# Required env: DATABASE_URL or PG* variables usable by pg_dump.

BACKUP_DIR="${LOCAL_PARITY_BACKUP_DIR:-/var/www/ai-food-family/backups/local-parity}"
STAMP="$(date +%Y%m%d_%H%M)"
OUT="${BACKUP_DIR}/planam_prod_snapshot_${STAMP}.dump"

mkdir -p "${BACKUP_DIR}"

if [[ -n "${DATABASE_URL:-}" ]]; then
  pg_dump "${DATABASE_URL}" --format=custom --no-owner --no-acl --file="${OUT}"
else
  pg_dump --format=custom --no-owner --no-acl --file="${OUT}"
fi

chmod 600 "${OUT}"
echo "Local parity snapshot written: ${OUT}"
