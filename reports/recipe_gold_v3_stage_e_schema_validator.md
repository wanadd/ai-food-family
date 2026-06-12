# Recipe Gold V3 — Stage E: Schema + Validator + Generation Contract

**Generated:** 2026-06-12  
**Branch:** `feat/recipe-gold-v3-original-planam-library`  
**Base commit:** `428d9fb` (Stage D)  
**Status:** implemented locally, **not committed**

---

## 1. Mini audit summary

| Topic | Finding |
|-------|---------|
| V2 reuse | `recipe_v2_validation.py`, `validate_recipe_v2.py`, `import_recipe_v2.py`, `PLANAM_RECIPE_SCHEMA_V2.md` |
| DB fields | `calories_per_serving`, `protein_g` + `nutrition_*_per_serving` (split-brain) |
| V3 nutrition contract | **`nutrition_per_serving` first**; legacy mapper → Stage N |
| Stage R importer | should write `nutrition_*_per_serving` + JSONB mirror from V3 contract |
| Stage N UI | read `nutrition_per_serving` via mapper, not legacy-only |
| Not touched | menu generation, gold_filter, production DB, OpenAI |

---

## 2. Files added

| File | Purpose |
|------|---------|
| `apps/api/app/recipes/recipe_gold_v3_schema.py` | Pydantic models + constants |
| `apps/api/app/recipes/recipe_gold_v3_validation.py` | Validator + score |
| `backend/scripts/validate_recipe_gold_v3.py` | CLI + markdown report |
| `exports/recipe_gold_v3_validation_samples.jsonl` | 5 fixture records |
| `docs/PLANAM_RECIPE_GOLD_V3_GENERATION_CONTRACT.md` | Generation contract |
| `apps/api/tests/test_recipe_gold_v3_validation.py` | 22 tests |
| `reports/recipe_gold_v3_validation_report.md` | CLI output |
| `reports/recipe_gold_v3_stage_e_schema_validator.md` | This report |

## 3. Files changed

| File | Change |
|------|--------|
| `apps/api/app/recipes/__init__.py` | export `validate_recipe_gold_v3` |

---

## 4. Schema summary

- `schema_version`: `recipe_gold_v3`
- `status`: `gold`
- `source_type`: `generated_original` | `manual_original`
- `nutrition_per_serving`: `{kcal, protein_g, fat_g, carbs_g, fiber_g?, salt_g?, sugar_g?}`
- min 4 ingredients, min 4 steps (25+ chars each)
- Russian title 8–80 chars
- `restriction_keys` from Stage B catalog
- `shopping_name`, `display_amount` per ingredient
- `image_prompt_data` for future photo pipeline

---

## 5. Validator checks (A–K)

| Group | Examples |
|-------|----------|
| Required fields | schema_version, originality, nutrition_per_serving, … |
| Schema values | meal_type, category, difficulty |
| Title | English prefixes, bowl, URL, Cyrillic required |
| Originality | flags must be true, risk != high |
| Ingredients | count, units, categories, shopping fields |
| Steps | count, length, vague/unsafe text |
| Nutrition | kcal, macros, macro-kcal consistency |
| Restrictions | unknown keys, diet contradictions, `restriction_safety` |
| Shopping | display_amount, shopping_name |
| Image prompt | summary required, no people/text emphasis |
| Score | 100 − errors×8 − warnings×3; production ≥85 |

---

## 6. Sample validation results

CLI: `validate_recipe_gold_v3.py --input exports/recipe_gold_v3_validation_samples.jsonl`

| Metric | Value |
|--------|-------|
| Records | 5 |
| Valid | 1 |
| Invalid | 4 |
| Avg score | 87.8 |

| Sample | Expected failure |
|--------|------------------|
| Куриное филе с овощами | valid |
| High protein: … | `english_title_prefix` |
| Быстрый овощной салат | `too_few_steps` |
| Свинина … no_pork | `restriction_contradiction` |
| Гречка с грибами | `missing_kcal` |

---

## 7. Tests

```
test_recipe_gold_v3_validation.py     22 passed
test_extract_povarenok_culinary_signals_v3.py  10 passed
test_restrictions_catalog.py             7 passed
test_restriction_safety.py            20 passed
test_menu_restriction_safety.py       11 passed
Total: 70 passed
compileall: OK
```

---

## 8. Not done

- Recipe generation (Stage F)
- Recipe import
- Image generation
- Safe reset
- Production DB changes
- Migrations
- KBJU UI fix (Stage N)
- Shopping aggregation (Stage M)

---

## 9. Next stage

**Stage F** — generate 10 original recipes dry-run only (OpenAI with explicit approval), validate each with `validate_recipe_gold_v3`, no DB import.
