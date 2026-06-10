#!/usr/bin/env bash
# Backup recipe-related tables before Recipe Rebuild V2 changes.
# Run ONLY on VPS with production DATABASE_URL.
#
# Usage:
#   DATABASE_URL=postgresql://... ./backend/scripts/backup_recipe_rebuild_v2.sh
#   ./backend/scripts/backup_recipe_rebuild_v2.sh --database-url postgresql://...

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

DATABASE_URL="${DATABASE_URL:-}"
if [[ "${1:-}" == "--database-url" ]]; then
  DATABASE_URL="$2"
  shift 2
fi

if [[ -z "$DATABASE_URL" ]]; then
  echo "ERROR: set DATABASE_URL or pass --database-url" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%d_%H%M%S)"
DEST="backups/recipe_rebuild_v2/${STAMP}"
mkdir -p "$DEST"

TABLES=(
  recipes
  recipe_ingredients
  recipe_steps
  recipe_tags
  recipe_allergens
  recipe_restrictions
  recipe_collections
  collection_recipes
  recipe_history
  recipe_favorites
  recipe_ratings
  meal_checkins
)

GIT_BRANCH="$(git branch --show-current 2>/dev/null || echo unknown)"
GIT_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

echo "# Recipe Rebuild V2 Backup Manifest" > "$DEST/manifest.md"
echo "" >> "$DEST/manifest.md"
echo "- Date (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$DEST/manifest.md"
echo "- Git branch: \`$GIT_BRANCH\`" >> "$DEST/manifest.md"
echo "- Git commit: \`$GIT_COMMIT\`" >> "$DEST/manifest.md"
echo "- Backup id: \`$STAMP\`" >> "$DEST/manifest.md"
echo "" >> "$DEST/manifest.md"
echo "## Tables" >> "$DEST/manifest.md"
echo "" >> "$DEST/manifest.md"

RELATED="$DEST/related_recipe_tables.sql"
: > "$RELATED"

for t in "${TABLES[@]}"; do
  COUNT="$(psql "$DATABASE_URL" -Atc "SELECT COUNT(*) FROM ${t}" 2>/dev/null || echo "n/a")"
  echo "- \`$t\`: $COUNT rows" >> "$DEST/manifest.md"
  if [[ "$t" == "recipes" ]]; then
    psql "$DATABASE_URL" -c "\\copy (SELECT * FROM recipes) TO STDOUT" > "$DEST/recipes.sql" 2>/dev/null \
      || pg_dump "$DATABASE_URL" --table=recipes --data-only --column-inserts > "$DEST/recipes.sql"
  elif [[ "$t" == "recipe_ingredients" ]]; then
    pg_dump "$DATABASE_URL" --table=recipe_ingredients --data-only --column-inserts > "$DEST/recipe_ingredients.sql"
  else
    pg_dump "$DATABASE_URL" --table="$t" --data-only --column-inserts >> "$RELATED" 2>/dev/null || true
  fi
done

cat >> "$DEST/manifest.md" <<EOF

## Restore (example)

\`\`\`bash
# Stop writers, restore on VPS only after review
psql "\$DATABASE_URL" -f backups/recipe_rebuild_v2/${STAMP}/recipes.sql
psql "\$DATABASE_URL" -f backups/recipe_rebuild_v2/${STAMP}/recipe_ingredients.sql
psql "\$DATABASE_URL" -f backups/recipe_rebuild_v2/${STAMP}/related_recipe_tables.sql
\`\`\`

Backup directory: \`$DEST\`
EOF

echo "Backup written to $DEST"
echo "Manifest: $DEST/manifest.md"
