# Recipe Rebuild V2 — Stage 1 Summary

## 1. Old database findings

Live audit requires VPS `DATABASE_URL`. Local run failed (no Postgres). Prior V1 audit (`planam_v1_ingredient_quality.json`) showed **150 recipes**, **1339 ingredients**, ambiguous units and generic names.

Audit script ready: `backend/scripts/audit_recipe_rebuild_v2.py` → `reports/recipe_rebuild_v2_current_db_audit.md/json`

## 2. Trash scale (expected)

Heuristics target: bad units, quantity-in-name, missing KBJU/steps/photo, duplicates, alcohol/pork hits, unsuitable preserves/baking. Full counts after VPS audit run.

## 3. Prepared for V2 schema

- `docs/PLANAM_RECIPE_SCHEMA_V2.md`
- `apps/api/app/recipes/recipe_v2_validation.py`
- `apps/api/app/recipes/product_taxonomy.py` (English slugs + legacy map)
- `docs/PLANAM_MENU_GENERATION_PROMPT_V2.md`

## 4. Gold recipes

- **30** recipes in `data/recipe_v2/gold_recipes_30.jsonl`
- Builder: `data/recipe_v2/build_gold_recipes_30.py`

## 5. Validation result

- **30/30 valid** (0 errors)
- Report: `reports/recipe_rebuild_v2_gold_30_validation_report.md`

## 6. Import

- **Dry-run only** locally: 30 would-create, 0 invalid
- Report: `reports/recipe_rebuild_v2_gold_30_import_report.md`
- Production `--apply` not executed

## 7. Not deleted

- No DELETE/UPDATE on production recipes
- Safe reset script is dry-run only; `--apply` blocked without `--backup-id`

## 8. Safe reset readiness

- Script: `backend/scripts/recipe_rebuild_v2_safe_reset.py`
- Plan report: `reports/recipe_rebuild_v2_safe_reset_plan.md`
- **Do not apply** until VPS backup + explicit approval

## 9. Remaining risks

- Live audit/reset counts unknown until VPS run
- `recipe_schema_version` stored in tags until migration
- Nutrition profile UI lacks religious checkboxes (gap report filed)
- V2 English taxonomy vs legacy Russian slugs — use `legacy_shopping_slug()` at boundaries

## Tests

- `pytest` recipe V2: **26 passed**
- `vitest`: **37 passed**

## Next steps (VPS)

```bash
git checkout rebuild/recipe-rebuild-v2
./backend/scripts/backup_recipe_rebuild_v2.sh
python backend/scripts/audit_recipe_rebuild_v2.py
python backend/scripts/import_recipe_v2.py --file data/recipe_v2/gold_recipes_30.jsonl --apply
python backend/scripts/recipe_rebuild_v2_safe_reset.py --dry-run
```
