# Recipe Gold V3 — Stage F Generation Report

**Generated:** 2026-06-12 11:42 UTC
**Branch:** `unknown`
**Commit:** `unknown`
**Mode:** `api`
**Real API run:** `True`

## Parameters

- Signals: `exports/povarenok_culinary_signals_v3_100.jsonl`
- Output: `exports/recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl`
- Limit: `10`
- Max cost USD: `1.5`
- Model: `gpt-4o-mini`
- Model override CLI: `gpt-4o-mini`
- Temperature: `0.7`
- Retry invalid: `2`
- Retry below score: `85`

## Summary

- Attempted: `10`
- Valid generated: `10`
- Invalid failed: `0`
- Retries used: `8`
- Low-score retries: `0`

## Quality gate

- Retry below score threshold: `85`
- Output includes only recipes with validator ok=True and score >= 85

- API calls: `18`
- Estimated cost USD: `0.90`
- Avg validation score: `99.4`
- Originality safety: `PASS`

## Generated titles

- Котлеты с овощами
- Крупа с овощами
- Куриный суп с овощами
- Куриные грудки с фруктами и овощами
- Запеканка с курицей и овощами
- Суп с фаршированной свининой
- Овощной суп-пюре
- Салат с морепродуктами
- Салат с курицей и фруктами
- Овощной суп с бобовыми

## Meal types

- lunch: `10`

## Categories

- soup: `4`
- main: `3`
- salad: `2`
- side: `1`

## Restriction keys

- none

## Allergen keys

- eggs: `2`
- milk: `2`
- seafood: `1`

## Validation errors

- missing_macro: `24`
- missing_kcal: `8`

## Validation warnings

- title_too_many_words: `2`
- too_many_optional_ingredients: `1`

## Sample recipes (2)

- `{"title": "Котлеты с овощами", "meal_type": "lunch", "category": "main", "servings": 4, "ingredients_count": 8, "steps_count": 4, "score": 100}`
- `{"title": "Крупа с овощами", "meal_type": "lunch", "category": "side", "servings": 4, "ingredients_count": 6, "steps_count": 4, "score": 100}`

## Not done

- DB import
- Image generation
- Safe reset
- Production DB changes

## Next stage

Stage G/H — originality + quality gate; Stage R importer after approval.
