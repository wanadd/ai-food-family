# Recipe Gold V3 тАФ Stage G/H Decision Report

**Generated:** 2026-06-12  
**Branch:** `feat/recipe-gold-v3-original-planam-library`  
**Base commit:** `6ddfdfa`

---

## 1. Stage F.1 result recap

| model | attempted | valid | invalid | avg_score | api_calls | cost | originality |
|-------|-----------|-------|---------|-----------|-----------|------|-------------|
| gpt-4o-mini | 10 | 10 | 0 | 99.4 | 18 | $0.90 | PASS |
| gpt-4.1 | 10 | 10 | 0 | 98.8 | 12 | $1.20 | PASS |

F.1 warnings only: `title_too_many_words`, `too_many_optional_ingredients` (mini); `title_too_many_words` (strong).

---

## 2. Expected inputs for Stage G/H

| Batch | Path (VPS) |
|-------|------------|
| gpt-4o-mini | `exports/recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl` |
| gpt-4.1 | `exports/recipe_gold_v3_generated_10_dry_run.strong.jsonl` |
| Signals | `exports/povarenok_culinary_signals_v3_100.jsonl` |

---

## 3. VPS quality gate тАФ pending

Stage G/H code restored locally. Run on VPS after applying `stage_gh_only.patch`:

- `reports/recipe_gold_v3_stage_gh_quality_gate_report.gpt4o_mini.md`
- `reports/recipe_gold_v3_stage_gh_quality_gate_report.strong.md`

**Expected:** both batches **PASS** (10/10 valid, avg тЙе 98, no source leakage, no hard duplicates).

---

## 4. Default recommendation (pre-VPS confirmation)

**Stage R importer dry-run batch:** `exports/recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl`

- Highest avg score (99.4), lower cost
- gpt-4.1 retained as fallback if mini gate fails (unlikely)

Switch to gpt-4.1 only if mini FAIL or clearly worse on originality/diversity.

---

## 5. Importer not run

Stage G/H is gate-only. Stage R requires explicit approval after VPS gate PASS.

---

## 6. Safety confirmations

| Action | Status |
|--------|--------|
| DB import | not run |
| Photo generation | not run |
| Safe reset | not run |
| Production DB changes | not run |

---

## 7. Next step

1. Apply `stage_gh_only.patch` on VPS, rebuild api
2. Run quality gate on both F.1 batches
3. If PASS тЖТ Stage R importer dry-run with **gpt-4o-mini** batch
4. If FAIL тЖТ fix generation/diversity, re-run F.1 subset
