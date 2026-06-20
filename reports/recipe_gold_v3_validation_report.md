# Recipe Gold V3 Validation Report

**Generated:** 2026-06-12 09:56 UTC
**Branch:** `feat/recipe-gold-v3-original-planam-library`
**Commit:** `428d9fb feat(recipes): add povarenok culinary signals dry-run extractor`
**Mode:** `dry-run`

## Summary

- Input: `exports\recipe_gold_v3_validation_samples.jsonl`
- Records: `5`
- Valid: `1`
- Invalid: `4`
- Average score: `87.8`

## Errors by code

- english_title_prefix: `1`
- too_few_steps: `1`
- restriction_contradiction: `1`
- restriction_safety_conflict: `1`
- missing_kcal: `1`

## Warnings by code

- missing_sugar_salt: `5`
- title_too_many_words: `1`
- kcal_out_of_range: `1`

## Per-record

### 1. Куриное филе с овощами в духовке — VALID (score 94)
- WARN `title_too_many_words`: title contains many words/adjectives
- WARN `missing_sugar_salt`: sugar_g/salt_g missing

### 2. High protein: курица с рисом — INVALID (score 89)
- ERROR `english_title_prefix`: title contains forbidden prefix: high protein:
- WARN `missing_sugar_salt`: sugar_g/salt_g missing

### 3. Быстрый овощной салат — INVALID (score 89)
- ERROR `too_few_steps`: at least 4 steps required
- WARN `missing_sugar_salt`: sugar_g/salt_g missing

### 4. Свинина с картофелем без свинины — INVALID (score 81)
- ERROR `restriction_contradiction`: no_pork but pork ingredient present
- ERROR `restriction_safety_conflict`: restriction safety conflict: Без свинины
- WARN `missing_sugar_salt`: sugar_g/salt_g missing

### 5. Гречка с грибами — INVALID (score 86)
- ERROR `missing_kcal`: nutrition_per_serving.kcal must be > 0
- WARN `missing_sugar_salt`: sugar_g/salt_g missing
- WARN `kcal_out_of_range`: kcal looks unusual: 0.0
