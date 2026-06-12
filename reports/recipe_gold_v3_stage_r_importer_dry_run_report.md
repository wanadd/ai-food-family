# Recipe Gold V3 — Stage R Importer Dry-Run Report

**Generated:** 2026-06-12 14:33 UTC
**Branch:** `unknown`
**Commit:** `unknown`
**Input:** `exports/recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl`
**Quality report:** `reports/recipe_gold_v3_stage_gh_quality_gate_report.gpt4o_mini.md`
**Quality report PASS:** `True`
**Mode:** `dry-run`

## Safety

- DB write disabled: `True`
- Image generation disabled: `true`
- Safe reset disabled: `true`
- Production DB unchanged: `true`

## Summary

- Records: `10`
- Valid (validator): `10`
- Would create: `10`
- Would update: `0`
- Would skip: `0`
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

## Errors by code

- none

## Warnings by code

- ui_nutrition_alias_warning: `10`
- meal_type_concentration: `1`
- optional_ingredient_warning: `1`

## Per recipe plan

- `{"index": 0, "title": "Котлеты с овощами", "normalized_title": "котлеты с овощами", "score": 100, "valid": true, "would_create": true, "would_skip": false, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 8, "errors": [], "warnings": ["ui_nutrition_alias_warning"]}`
- `{"index": 1, "title": "Крупа с овощами", "normalized_title": "крупа с овощами", "score": 100, "valid": true, "would_create": true, "would_skip": false, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 6, "errors": [], "warnings": ["ui_nutrition_alias_warning"]}`
- `{"index": 2, "title": "Куриный суп с овощами", "normalized_title": "куриный суп с овощами", "score": 100, "valid": true, "would_create": true, "would_skip": false, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 7, "errors": [], "warnings": ["ui_nutrition_alias_warning"]}`
- `{"index": 3, "title": "Куриные грудки с фруктами и овощами", "normalized_title": "куриные грудки с фруктами и овощами", "score": 97, "valid": true, "would_create": true, "would_skip": false, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 8, "errors": [], "warnings": ["ui_nutrition_alias_warning"]}`
- `{"index": 4, "title": "Запеканка с курицей и овощами", "normalized_title": "запеканка с курицей и овощами", "score": 100, "valid": true, "would_create": true, "would_skip": false, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 6, "errors": [], "warnings": ["ui_nutrition_alias_warning"]}`
- `{"index": 5, "title": "Суп с фаршированной свининой", "normalized_title": "суп с фаршированной свининой", "score": 100, "valid": true, "would_create": true, "would_skip": false, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 8, "errors": [], "warnings": ["ui_nutrition_alias_warning"]}`
- `{"index": 6, "title": "Овощной суп-пюре", "normalized_title": "овощной суппюре", "score": 100, "valid": true, "would_create": true, "would_skip": false, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 7, "errors": [], "warnings": ["ui_nutrition_alias_warning"]}`
- `{"index": 7, "title": "Салат с морепродуктами", "normalized_title": "салат с морепродуктами", "score": 100, "valid": true, "would_create": true, "would_skip": false, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 6, "errors": [], "warnings": ["ui_nutrition_alias_warning"]}`
- `{"index": 8, "title": "Салат с курицей и фруктами", "normalized_title": "салат с курицей и фруктами", "score": 97, "valid": true, "would_create": true, "would_skip": false, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 8, "errors": [], "warnings": ["ui_nutrition_alias_warning", "optional_ingredient_warning"]}`
- `{"index": 9, "title": "Овощной суп с бобовыми", "normalized_title": "овощной суп с бобовыми", "score": 100, "valid": true, "would_create": true, "would_skip": false, "would_update": 0, "nutrition_mapped": true, "ingredients_count": 8, "errors": [], "warnings": ["ui_nutrition_alias_warning"]}`

## DB duplicate findings

- none (no session or no duplicates)

## UI compatibility notes

- Recipe card KBJU uses `calories_per_serving`, `protein_g`, `fat_g`, `carbs_g` — mapped from Gold V3 nutrition_per_serving.
- Recipe detail also exposes `sugar_g`, `fiber_g`; `salt_g` stored in `nutrition_coverage_json` (no dedicated column).
- Shopping list merge uses ingredient `name` (= shopping_name) and `amount` (= display_amount).

## Next step

- Stage R apply/import only after explicit approval (not implemented in this dry-run).

## Not done

- DB import write
- image generation
- safe reset
- production DB changes
