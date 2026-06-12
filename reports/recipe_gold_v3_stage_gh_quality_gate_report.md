# Recipe Gold V3 тАФ Stage G/H Quality Gate Report (mini audit)

**Generated:** 2026-06-12  
**Branch:** `feat/recipe-gold-v3-original-planam-library`  
**Base commit:** `6ddfdfa` тАФ feat(recipes): tune gold v3 generation quality gate

---

## Mini audit тАФ existing files (Stage F.1, unchanged)

| File | Status |
|------|--------|
| `apps/api/app/recipes/recipe_gold_v3_schema.py` | present |
| `apps/api/app/recipes/recipe_gold_v3_validation.py` | present |
| `apps/api/app/recipes/recipe_gold_v3_postprocess.py` | present (F.1) |
| `apps/api/app/recipes/recipe_gold_v3_prompt_builder.py` | present (F.1) |
| `backend/scripts/validate_recipe_gold_v3.py` | present |
| `backend/scripts/generate_recipe_gold_v3_dry_run.py` | present (F.1) |
| `backend/scripts/extract_povarenok_culinary_signals_v3.py` | present |

## Stage G/H тАФ new files

| File | Purpose |
|------|---------|
| `apps/api/app/recipes/recipe_gold_v3_quality_gate.py` | originality, pairwise, diversity, validator integration |
| `backend/scripts/quality_gate_recipe_gold_v3.py` | CLI + markdown report |
| `apps/api/tests/test_recipe_gold_v3_quality_gate.py` | 17 unit/integration tests |

---

## What the gate checks

1. **Originality vs Povarenok signals** тАФ title similarity, quoted fragments, forbidden signal fields
2. **Source leakage** тАФ `source_url`, `original_title`, `original_steps`
3. **Pairwise duplicates** тАФ title / ingredient / step similarity inside batch
4. **Validator scores** тАФ every recipe valid, score тЙе min_score, batch avg тЙе avg_score
5. **Nutrition completeness** тАФ kcal, protein, fat, carbs, fiber, salt, sugar
6. **Shopping readiness** тАФ shopping_name, canonical unit, display_amount
7. **Restriction safety** тАФ hard contradictions
8. **Diversity** тАФ category >60% hard fail; meal_type >80% warning only; main ingredient >50% warning

---

## PASS / FAIL criteria

| Check | Hard FAIL | Warning only |
|-------|-----------|--------------|
| Source leakage | yes | тАФ |
| Title vs signal тЙе 0.72 | yes | 0.55тАУ0.72 moderate |
| Title vs recipe тЙе 0.80 | yes | тАФ |
| Ingredient overlap тЙе 0.85 | yes | тЙе 0.65 moderate |
| Steps тЙе 0.75 + related title/ingredients | yes | тАФ |
| Category > 60% (batch тЙе10) | yes | тАФ |
| Meal type > 80% | no | yes |
| Main ingredient family > 50% | error + warning | тАФ |
| avg_score < threshold | yes | тАФ |
| `--fail-on-warning` | warnings тЖТ FAIL | тАФ |

**Lunch-only batch:** warning `meal_type_concentration_warning`, not automatic FAIL (Stage F signals may be lunch-focused).

---

## Stage G/H hotfix (post-VPS)

VPS false FAIL causes fixed:

1. **Mojibake-safe source** тАФ Russian markers via Unicode escapes; `casefold()` + `isalnum()` tokenization (no `[╨░-╤П]` regex).
2. **Main ingredient family** тАФ detection from `ingredients[].shopping_name/name`; `other`-only batch no longer hard-fails.
3. **Signal originality** тАФ hard `title_too_close_to_signal` only vs real `original_title`/`source_title`/`raw_title`/`title` in signal; abstract hints тЖТ warning only.
4. **No compare-all-signals fallback** тАФ only linked `source_signal_ids` checked.

Re-run quality gate on VPS after applying `stage_gh_hotfix.patch`.

---

See `patches/STAGE_GH_VPS_APPLY.md` for full deploy + run instructions.

```bash
docker compose -f docker-compose.prod.yml exec api bash -lc \
  'cd /app && PYTHONPATH=/app:/app/apps/api python backend/scripts/quality_gate_recipe_gold_v3.py \
  --input exports/recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl \
  --signals exports/povarenok_culinary_signals_v3_100.jsonl \
  --report reports/recipe_gold_v3_stage_gh_quality_gate_report.gpt4o_mini.md \
  --min-score 85 --avg-score 90 --dry-run'
```

Expected based on F.1: **PASS** for both gpt-4o-mini and gpt-4.1 batches.

---

## Not done

- DB import
- Image generation
- Safe reset
- Production DB changes
