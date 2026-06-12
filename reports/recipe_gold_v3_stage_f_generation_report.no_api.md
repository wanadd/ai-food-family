# Recipe Gold V3 — Stage F Generation Report

**Generated:** 2026-06-12 10:04 UTC
**Branch:** `feat/recipe-gold-v3-original-planam-library`
**Commit:** `464f95a feat(recipes): add gold v3 schema validator and generation contract`
**Mode:** `no-api`
**Real API run:** `False`

## Parameters

- Signals: `exports\povarenok_culinary_signals_v3_100.jsonl`
- Output: `exports\recipe_gold_v3_generated_10_dry_run.no_api.jsonl`
- Limit: `10`
- Max cost USD: `0.01`
- Model: `gpt-4o-mini`
- Temperature: `0.7`

## Summary

- Attempted: `10`
- Valid generated: `10`
- Invalid failed: `0`
- Retries used: `0`
- API calls: `0`
- Estimated cost USD: `0.00`
- Avg validation score: `100.0`
- Originality safety: `PASS`

## Generated titles

- Котлеты из чечевицы #1
- Гречка с овощами #2
- Овощной суп #3
- Овощной салат #4
- Овощная запеканка #5
- Овощной суп #6
- Овощной суп #7
- Овощной салат #8
- Овощной салат #9
- Куриный суп #10

## Meal types

- lunch: `10`

## Categories

- soup: `4`
- main: `3`
- salad: `2`
- side: `1`

## Restriction keys

- vegan: `7`
- no_eggs: `4`
- lactose_free: `3`
- no_milk: `3`
- no_pork: `2`
- no_soy: `2`
- kosher: `2`
- vegetarian: `2`
- no_alcohol: `1`
- gluten_free: `1`
- halal: `1`
- pescatarian: `1`
- no_seafood: `1`

## Allergen keys

- none

## Validation errors

- none

## Validation warnings

- none

## Sample recipes (2)

- `{"title": "Котлеты из чечевицы #1", "meal_type": "lunch", "category": "main", "servings": 4, "ingredients_count": 4, "steps_count": 4, "score": 100}`
- `{"title": "Гречка с овощами #2", "meal_type": "lunch", "category": "side", "servings": 4, "ingredients_count": 4, "steps_count": 4, "score": 100}`

## Not done

- DB import
- Image generation
- Safe reset
- Production DB changes

## Next stage

Stage G/H — originality + quality gate; Stage R importer after approval.
