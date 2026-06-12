# Recipe Gold V3 — Stage F Generation Report

**Generated:** 2026-06-12 11:53 UTC
**Branch:** `unknown`
**Commit:** `unknown`
**Mode:** `api`
**Real API run:** `True`

## Parameters

- Signals: `exports/povarenok_culinary_signals_v3_100.jsonl`
- Output: `exports/recipe_gold_v3_generated_10_dry_run.strong.jsonl`
- Limit: `10`
- Max cost USD: `3.0`
- Model: `gpt-4.1`
- Model override CLI: `gpt-4.1`
- Temperature: `0.7`
- Retry invalid: `2`
- Retry below score: `85`

## Summary

- Attempted: `10`
- Valid generated: `10`
- Invalid failed: `0`
- Retries used: `2`
- Low-score retries: `0`

## Quality gate

- Retry below score threshold: `85`
- Output includes only recipes with validator ok=True and score >= 85

- API calls: `12`
- Estimated cost USD: `1.20`
- Avg validation score: `98.8`
- Originality safety: `PASS`

## Generated titles

- Нежные куриные котлеты с овощами
- Перловка с запечёнными овощами
- Суп с курицей и печёной морковью
- Курица с овощами и яблоками
- Запечённая курица с овощным слоем
- Суп с фаршированными овощами и сливками
- Овощной суп с тофу
- Салат с кальмарами и свежим огурцом
- Салат с курицей, яблоком и свежими овощами
- Летний овощной суп с фасолью

## Meal types

- lunch: `6`
- dinner: `4`

## Categories

- soup: `4`
- main: `3`
- salad: `2`
- side: `1`

## Restriction keys

- no_pork: `2`
- no_alcohol: `2`

## Allergen keys

- eggs: `4`
- milk: `3`
- seafood: `1`

## Validation errors

- restriction_safety_conflict: `2`
- diet_contradiction: `1`

## Validation warnings

- title_too_many_words: `4`

## Sample recipes (2)

- `{"title": "Нежные куриные котлеты с овощами", "meal_type": "dinner", "category": "main", "servings": 4, "ingredients_count": 9, "steps_count": 5, "score": 100}`
- `{"title": "Перловка с запечёнными овощами", "meal_type": "dinner", "category": "side", "servings": 4, "ingredients_count": 7, "steps_count": 4, "score": 100}`

## Not done

- DB import
- Image generation
- Safe reset
- Production DB changes

## Next stage

Stage G/H — originality + quality gate; Stage R importer after approval.
