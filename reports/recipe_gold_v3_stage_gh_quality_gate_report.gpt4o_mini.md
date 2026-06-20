# Recipe Gold V3 — Stage G/H Quality Gate Report

**Generated:** 2026-06-12 13:56 UTC
**Branch:** `unknown`
**Commit:** `unknown`
**Input:** `exports/recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl`
**Signals:** `exports/povarenok_culinary_signals_v3_100.jsonl`
**Mode:** `dry-run`

## Summary

- Records: `10`
- Valid (validator): `10`
- Invalid: `0`
- Avg score: `99.4`
- Min score threshold: `85`
- Avg score threshold: `90.0`
- Originality: `PASS`
- Duplicate check: `PASS`
- Diversity: `WARN`
- Quality gate: **`PASS`**

## Errors by code

- none

## Warnings by code

- title_moderately_similar: `12`
- ingredient_overlap_moderate: `2`
- meal_type_concentration_warning: `1`
- title_too_many_words: `1`
- too_many_optional_ingredients: `1`

## Per recipe

- `{"index": 0, "title": "Котлеты с овощами", "score": 100, "valid": true, "category": "main", "meal_type": "lunch", "errors": [], "warnings": ["title_moderately_similar", "meal_type_concentration_warning"]}`
- `{"index": 1, "title": "Крупа с овощами", "score": 100, "valid": true, "category": "side", "meal_type": "lunch", "errors": [], "warnings": ["meal_type_concentration_warning"]}`
- `{"index": 2, "title": "Куриный суп с овощами", "score": 100, "valid": true, "category": "soup", "meal_type": "lunch", "errors": [], "warnings": ["title_moderately_similar", "ingredient_overlap_moderate", "meal_type_concentration_warning"]}`
- `{"index": 3, "title": "Куриные грудки с фруктами и овощами", "score": 97, "valid": true, "category": "main", "meal_type": "lunch", "errors": [], "warnings": ["title_too_many_words", "meal_type_concentration_warning"]}`
- `{"index": 4, "title": "Запеканка с курицей и овощами", "score": 100, "valid": true, "category": "main", "meal_type": "lunch", "errors": [], "warnings": ["title_moderately_similar", "meal_type_concentration_warning"]}`
- `{"index": 5, "title": "Суп с фаршированной свининой", "score": 100, "valid": true, "category": "soup", "meal_type": "lunch", "errors": [], "warnings": ["title_moderately_similar", "ingredient_overlap_moderate", "meal_type_concentration_warning"]}`
- `{"index": 6, "title": "Овощной суп-пюре", "score": 100, "valid": true, "category": "soup", "meal_type": "lunch", "errors": [], "warnings": ["title_moderately_similar", "meal_type_concentration_warning"]}`
- `{"index": 7, "title": "Салат с морепродуктами", "score": 100, "valid": true, "category": "salad", "meal_type": "lunch", "errors": [], "warnings": ["title_moderately_similar", "meal_type_concentration_warning"]}`
- `{"index": 8, "title": "Салат с курицей и фруктами", "score": 97, "valid": true, "category": "salad", "meal_type": "lunch", "errors": [], "warnings": ["too_many_optional_ingredients", "title_moderately_similar", "meal_type_concentration_warning"]}`
- `{"index": 9, "title": "Овощной суп с бобовыми", "score": 100, "valid": true, "category": "soup", "meal_type": "lunch", "errors": [], "warnings": ["title_moderately_similar", "ingredient_overlap_moderate", "meal_type_concentration_warning"]}`

## Pairwise similarity findings

- `{"pair": [2, 5], "title_a": "Куриный суп с овощами", "title_b": "Суп с фаршированной свининой", "findings": [{"code": "ingredient_overlap_moderate", "severity": "warning", "message": "ingredient overlap 0.67 >= 0.65", "pair": [2, 5], "similarity": 0.667}]}`
- `{"pair": [2, 9], "title_a": "Куриный суп с овощами", "title_b": "Овощной суп с бобовыми", "findings": [{"code": "ingredient_overlap_moderate", "severity": "warning", "message": "ingredient overlap 0.67 >= 0.65", "pair": [2, 9], "similarity": 0.667}]}`

## Signal similarity findings

- `{"recipe_index": 0, "title": "Котлеты с овощами", "signal_id": "pov_sig_000002", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Котлеты с овощами"}`
- `{"recipe_index": 2, "title": "Куриный суп с овощами", "signal_id": "pov_sig_000006", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Куриный суп с овощами"}`
- `{"recipe_index": 2, "title": "Куриный суп с овощами", "signal_id": "pov_sig_000006", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Куриный суп с овощами"}`
- `{"recipe_index": 4, "title": "Запеканка с курицей и овощами", "signal_id": "pov_sig_000009", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Запеканка с курицей и овощами"}`
- `{"recipe_index": 5, "title": "Суп с фаршированной свининой", "signal_id": "pov_sig_000010", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Суп с фаршированной свининой"}`
- `{"recipe_index": 5, "title": "Суп с фаршированной свининой", "signal_id": "pov_sig_000010", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Суп с фаршированной свининой"}`
- `{"recipe_index": 6, "title": "Овощной суп-пюре", "signal_id": "pov_sig_000012", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Овощной суп-пюре"}`
- `{"recipe_index": 6, "title": "Овощной суп-пюре", "signal_id": "pov_sig_000012", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Овощной суп-пюре"}`
- `{"recipe_index": 7, "title": "Салат с морепродуктами", "signal_id": "pov_sig_000013", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Салат с морепродуктами"}`
- `{"recipe_index": 8, "title": "Салат с курицей и фруктами", "signal_id": "pov_sig_000016", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Салат с курицей и фруктами"}`
- `{"recipe_index": 9, "title": "Овощной суп с бобовыми", "signal_id": "pov_sig_000019", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Овощной суп с бобовыми"}`
- `{"recipe_index": 9, "title": "Овощной суп с бобовыми", "signal_id": "pov_sig_000019", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Овощной суп с бобовыми"}`

## Diversity

- Categories: `{"main": 3, "side": 1, "soup": 4, "salad": 2}`
- Meal types: `{"lunch": 10}`
- Main ingredient families: `{"chicken": 5, "grains": 1, "pork": 1, "vegetables": 1, "seafood": 1, "legumes_tofu": 1}`
- Category overconcentration: `False`
- Meal type overconcentration: `True`
- Main ingredient overconcentration: `False`

## Production recommendation

- **PASS** — ready for Stage R importer dry-run

## Not done

- DB import
- Image generation
- Safe reset
- Production DB changes
