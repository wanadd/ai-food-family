# Recipe Gold V3 — Stage R Importer Dry-Run Report

**Generated:** 2026-06-13 08:04 UTC
**Branch:** `unknown`
**Commit:** `unknown`
**Input:** `exports/recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl`
**Quality report:** `reports/recipe_gold_v3_stage_gh_quality_gate_report.gpt4o_mini.md`
**Quality report PASS:** `True`
**Mode:** `dry-run`

## Safety

- DB write disabled: `True`
- Safe reset disabled: `true`
- Old recipe updates: `false`
- Old recipe deletes: `false`
- Expected count: `10`
- Actual count: `10`
- Idempotent full skip: `True`

## Summary

- Records: `10`
- Valid (validator): `10`
- Would create: `0`
- Would update: `0`
- Would skip: `10`
- Importer dry-run: **`PASS`**

## Mapping summary

- Recipe fields: `["title", "display_title", "normalized_title", "description", "meal_type", "category", "cuisine", "servings", "prep_time_minutes", "cooking_time_minutes", "difficulty", "source_type=import", "tags", "diets"]`
- Nutrition legacy UI: `["calories_per_serving", "protein_g", "fat_g", "carbs_g", "fiber_g", "sugar_g"]`
- Nutrition summary columns: `["nutrition_kcal_per_serving", "nutrition_protein_per_serving", "nutrition_fat_per_serving", "nutrition_carbs_per_serving"]`
- Nutrition extras: `["nutrition_coverage_json.fiber_g", "nutrition_coverage_json.salt_g", "nutrition_coverage_json.sugar_g"]`
- UI primary: `calories_per_serving/protein_g/fat_g/carbs_g (RecipeSummary + menu)`
- Ingredient JSONB: `name (shopping_name), amount (display_amount)`
- Ingredient rows plan: `name=shopping_name, quantity=amount, unit, category=legacy slug, is_optional`
- Shopping fields: `["shopping_name", "display_amount", "unit", "category"]`

## Per recipe plan

- `{"index": 0, "title": "Котлеты с овощами", "normalized_title": "котлеты с овощами", "score": 100, "valid": true, "would_create": false, "would_skip": true, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 8, "errors": ["duplicate_title_in_db"], "warnings": ["ui_nutrition_alias_warning"], "db_duplicate": true, "db_duplicate_gold_v3_import": true}`
- `{"index": 1, "title": "Крупа с овощами", "normalized_title": "крупа с овощами", "score": 100, "valid": true, "would_create": false, "would_skip": true, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 6, "errors": ["duplicate_title_in_db"], "warnings": ["ui_nutrition_alias_warning"], "db_duplicate": true, "db_duplicate_gold_v3_import": true}`
- `{"index": 2, "title": "Куриный суп с овощами", "normalized_title": "куриный суп с овощами", "score": 100, "valid": true, "would_create": false, "would_skip": true, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 7, "errors": ["duplicate_title_in_db"], "warnings": ["ui_nutrition_alias_warning"], "db_duplicate": true, "db_duplicate_gold_v3_import": true}`
- `{"index": 3, "title": "Куриные грудки с фруктами и овощами", "normalized_title": "куриные грудки с фруктами и овощами", "score": 97, "valid": true, "would_create": false, "would_skip": true, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 8, "errors": ["duplicate_title_in_db"], "warnings": ["ui_nutrition_alias_warning"], "db_duplicate": true, "db_duplicate_gold_v3_import": true}`
- `{"index": 4, "title": "Запеканка с курицей и овощами", "normalized_title": "запеканка с курицей и овощами", "score": 100, "valid": true, "would_create": false, "would_skip": true, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 6, "errors": ["duplicate_title_in_db"], "warnings": ["ui_nutrition_alias_warning"], "db_duplicate": true, "db_duplicate_gold_v3_import": true}`
- `{"index": 5, "title": "Суп с фаршированной свининой", "normalized_title": "суп с фаршированной свининой", "score": 100, "valid": true, "would_create": false, "would_skip": true, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 8, "errors": ["duplicate_title_in_db"], "warnings": ["ui_nutrition_alias_warning"], "db_duplicate": true, "db_duplicate_gold_v3_import": true}`
- `{"index": 6, "title": "Овощной суп-пюре", "normalized_title": "овощной суппюре", "score": 100, "valid": true, "would_create": false, "would_skip": true, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 7, "errors": ["duplicate_title_in_db"], "warnings": ["ui_nutrition_alias_warning"], "db_duplicate": true, "db_duplicate_gold_v3_import": true}`
- `{"index": 7, "title": "Салат с морепродуктами", "normalized_title": "салат с морепродуктами", "score": 100, "valid": true, "would_create": false, "would_skip": true, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 6, "errors": ["duplicate_title_in_db"], "warnings": ["ui_nutrition_alias_warning"], "db_duplicate": true, "db_duplicate_gold_v3_import": true}`
- `{"index": 8, "title": "Салат с курицей и фруктами", "normalized_title": "салат с курицей и фруктами", "score": 97, "valid": true, "would_create": false, "would_skip": true, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 8, "errors": ["duplicate_title_in_db"], "warnings": ["ui_nutrition_alias_warning", "optional_ingredient_warning"], "db_duplicate": true, "db_duplicate_gold_v3_import": true}`
- `{"index": 9, "title": "Овощной суп с бобовыми", "normalized_title": "овощной суп с бобовыми", "score": 100, "valid": true, "would_create": false, "would_skip": true, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 8, "errors": ["duplicate_title_in_db"], "warnings": ["ui_nutrition_alias_warning"], "db_duplicate": true, "db_duplicate_gold_v3_import": true}`

## DB duplicate findings

- `{"code": "duplicate_title_in_db", "index": 0, "normalized_title": "котлеты с овощами", "existing_id": 256, "existing_title": "Котлеты с овощами", "existing_source_type": "import", "is_gold_v3_import": true}`
- `{"code": "duplicate_title_in_db", "index": 1, "normalized_title": "крупа с овощами", "existing_id": 257, "existing_title": "Крупа с овощами", "existing_source_type": "import", "is_gold_v3_import": true}`
- `{"code": "duplicate_title_in_db", "index": 2, "normalized_title": "куриный суп с овощами", "existing_id": 258, "existing_title": "Куриный суп с овощами", "existing_source_type": "import", "is_gold_v3_import": true}`
- `{"code": "duplicate_title_in_db", "index": 3, "normalized_title": "куриные грудки с фруктами и овощами", "existing_id": 259, "existing_title": "Куриные грудки с фруктами и овощами", "existing_source_type": "import", "is_gold_v3_import": true}`
- `{"code": "duplicate_title_in_db", "index": 4, "normalized_title": "запеканка с курицей и овощами", "existing_id": 260, "existing_title": "Запеканка с курицей и овощами", "existing_source_type": "import", "is_gold_v3_import": true}`
- `{"code": "duplicate_title_in_db", "index": 5, "normalized_title": "суп с фаршированной свининой", "existing_id": 261, "existing_title": "Суп с фаршированной свининой", "existing_source_type": "import", "is_gold_v3_import": true}`
- `{"code": "duplicate_title_in_db", "index": 6, "normalized_title": "овощной суппюре", "existing_id": 262, "existing_title": "Овощной суп-пюре", "existing_source_type": "import", "is_gold_v3_import": true}`
- `{"code": "duplicate_title_in_db", "index": 7, "normalized_title": "салат с морепродуктами", "existing_id": 263, "existing_title": "Салат с морепродуктами", "existing_source_type": "import", "is_gold_v3_import": true}`
- `{"code": "duplicate_title_in_db", "index": 8, "normalized_title": "салат с курицей и фруктами", "existing_id": 264, "existing_title": "Салат с курицей и фруктами", "existing_source_type": "import", "is_gold_v3_import": true}`
- `{"code": "duplicate_title_in_db", "index": 9, "normalized_title": "овощной суп с бобовыми", "existing_id": 265, "existing_title": "Овощной суп с бобовыми", "existing_source_type": "import", "is_gold_v3_import": true}`

## Errors by code

- none

## Warnings by code

- idempotent_duplicate_in_db: `10`
- ui_nutrition_alias_warning: `10`
- meal_type_concentration: `1`
- optional_ingredient_warning: `1`

## UI compatibility notes

- Recipe card KBJU uses `calories_per_serving`, `protein_g`, `fat_g`, `carbs_g` — mapped from Gold V3 nutrition_per_serving.
- Recipe detail also exposes `sugar_g`, `fiber_g`; `salt_g` stored in `nutrition_coverage_json`.
- Shopping list merge uses ingredient `name` (= shopping_name) and `amount` (= display_amount).

## Not done

- DB import write
- safe reset
- old recipe updates
- old recipe deletes
