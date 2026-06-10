# Recipe Rebuild V2 — Backup Manifest Example

Example manifest produced by `backend/scripts/backup_recipe_rebuild_v2.sh` on VPS.

---

# Recipe Rebuild V2 Backup Manifest

- Date (UTC): 2026-06-10T12:00:00Z
- Git branch: `rebuild/recipe-rebuild-v2`
- Git commit: `abc1234`
- Backup id: `20260610_120000`

## Tables

- `recipes`: 150 rows
- `recipe_ingredients`: 1339 rows
- `recipe_steps`: 890 rows
- `recipe_tags`: 42 rows
- `recipe_allergens`: 18 rows
- `recipe_restrictions`: 12 rows
- `recipe_collections`: 5 rows
- `collection_recipes`: 120 rows
- `recipe_history`: 340 rows
- `recipe_favorites`: 87 rows
- `recipe_ratings`: 56 rows
- `meal_checkins`: 210 rows

## Files

```
backups/recipe_rebuild_v2/20260610_120000/
  recipes.sql
  recipe_ingredients.sql
  related_recipe_tables.sql
  manifest.md
```

## Restore (example)

```bash
# VPS only — stop writers first
psql "$DATABASE_URL" -f backups/recipe_rebuild_v2/20260610_120000/recipes.sql
psql "$DATABASE_URL" -f backups/recipe_rebuild_v2/20260610_120000/recipe_ingredients.sql
psql "$DATABASE_URL" -f backups/recipe_rebuild_v2/20260610_120000/related_recipe_tables.sql
```

## Run backup

```bash
cd /var/www/ai-food-family
DATABASE_URL=postgresql://... ./backend/scripts/backup_recipe_rebuild_v2.sh
```

**Stage 1:** backup script prepared; live backup must be executed on VPS before any `--apply` reset or mass import.
