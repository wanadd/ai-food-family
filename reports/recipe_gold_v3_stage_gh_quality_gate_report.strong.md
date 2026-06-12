# Recipe Gold V3 — Stage G/H Quality Gate Report

**Generated:** 2026-06-12 13:56 UTC
**Branch:** `unknown`
**Commit:** `unknown`
**Input:** `exports/recipe_gold_v3_generated_10_dry_run.strong.jsonl`
**Signals:** `exports/povarenok_culinary_signals_v3_100.jsonl`
**Mode:** `dry-run`

## Summary

- Records: `10`
- Valid (validator): `10`
- Invalid: `0`
- Avg score: `98.8`
- Min score threshold: `85`
- Avg score threshold: `90.0`
- Originality: `PASS`
- Duplicate check: `PASS`
- Diversity: `PASS`
- Quality gate: **`PASS`**

## Errors by code

- none

## Warnings by code

- title_moderately_similar: `11`
- title_too_many_words: `4`

## Per recipe

- `{"index": 0, "title": "Нежные куриные котлеты с овощами", "score": 100, "valid": true, "category": "main", "meal_type": "dinner", "errors": [], "warnings": ["title_moderately_similar"]}`
- `{"index": 1, "title": "Перловка с запечёнными овощами", "score": 100, "valid": true, "category": "side", "meal_type": "dinner", "errors": [], "warnings": []}`
- `{"index": 2, "title": "Суп с курицей и печёной морковью", "score": 97, "valid": true, "category": "soup", "meal_type": "lunch", "errors": [], "warnings": ["title_too_many_words", "title_moderately_similar"]}`
- `{"index": 3, "title": "Курица с овощами и яблоками", "score": 100, "valid": true, "category": "main", "meal_type": "dinner", "errors": [], "warnings": []}`
- `{"index": 4, "title": "Запечённая курица с овощным слоем", "score": 100, "valid": true, "category": "main", "meal_type": "dinner", "errors": [], "warnings": []}`
- `{"index": 5, "title": "Суп с фаршированными овощами и сливками", "score": 97, "valid": true, "category": "soup", "meal_type": "lunch", "errors": [], "warnings": ["title_too_many_words", "title_moderately_similar"]}`
- `{"index": 6, "title": "Овощной суп с тофу", "score": 100, "valid": true, "category": "soup", "meal_type": "lunch", "errors": [], "warnings": ["title_moderately_similar"]}`
- `{"index": 7, "title": "Салат с кальмарами и свежим огурцом", "score": 97, "valid": true, "category": "salad", "meal_type": "lunch", "errors": [], "warnings": ["title_too_many_words", "title_moderately_similar"]}`
- `{"index": 8, "title": "Салат с курицей, яблоком и свежими овощами", "score": 97, "valid": true, "category": "salad", "meal_type": "lunch", "errors": [], "warnings": ["title_too_many_words", "title_moderately_similar"]}`
- `{"index": 9, "title": "Летний овощной суп с фасолью", "score": 100, "valid": true, "category": "soup", "meal_type": "lunch", "errors": [], "warnings": ["title_moderately_similar"]}`

## Pairwise similarity findings

- none

## Signal similarity findings

- `{"recipe_index": 0, "title": "Нежные куриные котлеты с овощами", "signal_id": "pov_sig_000002", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Нежные куриные котлеты с овощами"}`
- `{"recipe_index": 2, "title": "Суп с курицей и печёной морковью", "signal_id": "pov_sig_000006", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Суп с курицей и печёной морковью"}`
- `{"recipe_index": 2, "title": "Суп с курицей и печёной морковью", "signal_id": "pov_sig_000006", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Суп с курицей и печёной морковью"}`
- `{"recipe_index": 5, "title": "Суп с фаршированными овощами и сливками", "signal_id": "pov_sig_000010", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Суп с фаршированными овощами и сливками"}`
- `{"recipe_index": 5, "title": "Суп с фаршированными овощами и сливками", "signal_id": "pov_sig_000010", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Суп с фаршированными овощами и сливками"}`
- `{"recipe_index": 6, "title": "Овощной суп с тофу", "signal_id": "pov_sig_000012", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Овощной суп с тофу"}`
- `{"recipe_index": 6, "title": "Овощной суп с тофу", "signal_id": "pov_sig_000012", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Овощной суп с тофу"}`
- `{"recipe_index": 7, "title": "Салат с кальмарами и свежим огурцом", "signal_id": "pov_sig_000013", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Салат с кальмарами и свежим огурцом"}`
- `{"recipe_index": 8, "title": "Салат с курицей, яблоком и свежими овощами", "signal_id": "pov_sig_000016", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Салат с курицей, яблоком и свежими овощами"}`
- `{"recipe_index": 9, "title": "Летний овощной суп с фасолью", "signal_id": "pov_sig_000019", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Летний овощной суп с фасолью"}`
- `{"recipe_index": 9, "title": "Летний овощной суп с фасолью", "signal_id": "pov_sig_000019", "code": "title_moderately_similar", "severity": "warning", "message": "title shares abstract signal vocabulary 0.85 (not a source title leak)", "similarity": 0.85, "recipe_title": "Летний овощной суп с фасолью"}`

## Diversity

- Categories: `{"main": 3, "side": 1, "soup": 4, "salad": 2}`
- Meal types: `{"dinner": 4, "lunch": 6}`
- Main ingredient families: `{"chicken": 5, "grains": 1, "pork": 1, "legumes_tofu": 2, "seafood": 1}`
- Category overconcentration: `False`
- Meal type overconcentration: `False`
- Main ingredient overconcentration: `False`

## Production recommendation

- **PASS** — ready for Stage R importer dry-run

## Not done

- DB import
- Image generation
- Safe reset
- Production DB changes
