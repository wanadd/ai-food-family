# Recipe Gold V3 — Stage C: Menu Restriction Safety Integration

**Generated:** 2026-06-10  
**Branch:** `feat/recipe-gold-v3-original-planam-library`  
**Base commit:** `87eb0d6` (Stage B)  
**Status:** implemented locally, **not committed** (awaiting user confirmation)

---

## 1. Mini audit summary

| Zone | Files |
|------|-------|
| Pre-AI recipe pool | `menu_recipe_builder.build_menus_from_recipes`, `ai_context._recipe_catalog_slice`, `menu_days.expand_variant_to_plan_days` |
| AI generation | `menu_ai.generate_menus` → `ai.generate_menu_ai` / `build_menus_from_recipes` fallback |
| Post-AI result | `menu.generate_menus_for_scope` after `generate_menus` |
| Profile source | `onboarding.get_or_create_profile` via `resolve_menu_profile` |
| Not touched | KBJU, shopping, household 500, menu_generation_jobs, recipe import/generation |

---

## 2. Files changed

### Added

| File | Purpose |
|------|---------|
| `apps/api/app/services/menu_restriction_safety.py` | Pre/post-AI hooks, explanations, replacement logic |
| `apps/api/tests/test_menu_restriction_safety.py` | 11 Stage C tests |
| `reports/recipe_gold_v3_stage_c_menu_safety.md` | This report |

### Modified

| File | Change |
|------|--------|
| `apps/api/app/services/menu_recipe_builder.py` | `apply_pre_ai_recipe_filter` after `query_active_recipes` |
| `apps/api/app/services/menu.py` | `sanitize_menu_variants` after `generate_menus` |
| `apps/api/app/services/ai_context.py` | Filter AI recipe catalog by profile |
| `apps/api/app/services/menu_days.py` | Pre-filter multi-day expansion pool |

**No DB migrations.**

---

## 3. Pre-AI filtering

**Hook:** `menu_recipe_builder.build_menus_from_recipes` — immediately after loading recipes, before `_filter_candidates`.

```python
recipes, pool_warnings = apply_pre_ai_recipe_filter(recipes, profile)
if len(recipes) < MIN_RECIPE_POOL_SIZE:
    return None
```

**Also:**
- `ai_context._recipe_catalog_slice(db, profile=profile)` — AI prompt catalog excludes hard-conflict recipes
- `menu_days.expand_variant_to_plan_days` — days 2+ use filtered pool

**Behavior:**
- Hard conflicts removed via `filter_recipes_for_profile`
- Soft conflicts stay in pool
- Missing profile → pool unchanged, debug log
- Pool &lt; 6 after filter → `build_menus_from_recipes` returns `None` (controlled fallback to AI/heuristic), **never** re-adds forbidden recipes
- Warnings appended to variant `explanation` when pool is small

---

## 4. Post-AI validation

**Hook:** `menu.generate_menus_for_scope` — after `generate_menus(...)`, before `expand_variant_to_plan_days`.

```python
menus, safety_notes = sanitize_menu_variants(db, menus, profile, replacement_pool=safe_pool)
```

**Per meal with `recipe_id`:**
1. `explain_recipe_restriction_conflicts(recipe, profile)`
2. Hard conflict → try replacement from `safe_pool` (same `meal_type`, allowed)
3. No replacement → meal removed
4. Soft conflict → meal kept, warning in `explanation`

**User-facing messages (in `explanation`):**
- `Блюдо исключено: ограничение «…», …`
- `Блюдо заменено: не подходит под ограничение «…».`
- `Для части ограничений есть предупреждения, но блюдо не заблокировано: …`

---

## 5. Hard vs soft handling

| Type | Pre-AI | Post-AI |
|------|--------|---------|
| Hard | Removed from pool | Replace or drop meal |
| Soft | Stays in pool | Kept with warning text |

---

## 6. Edge cases

| Case | Behavior |
|------|----------|
| Profile unavailable | No filter/validation crash; pool and menus unchanged |
| Too few allowed recipes | Warning text; builder returns `None` if &lt; 6 |
| AI picks forbidden `recipe_id` | Post-AI catches and replaces/removes |
| Meal without `recipe_id` | Skipped (no ingredient-level check on Stage C) |

---

## 7. Tests

| Suite | Count | Result |
|-------|-------|--------|
| `test_restrictions_catalog.py` | 7 | passed |
| `test_restriction_safety.py` | 20 | passed |
| `test_menu_restriction_safety.py` | 11 | passed |
| **Total** | **38** | **passed** |

Stage C test cases:
1. pre-AI no_pork removes pork
2. pre-AI keeps allowed
3. vegetarian removes chicken/fish
4. vegan removes egg/milk
5. soft restriction does not remove
6. post-AI hard conflict → replace
7. post-AI allows clean menu
8. banned_foods → replace
9. allergies → replace
10. missing profile no crash
11. resolve_menu_profile without db

```bash
python -m compileall apps/api/app   # OK
cd apps/api && python -m pytest \
  tests/test_restrictions_catalog.py \
  tests/test_restriction_safety.py \
  tests/test_menu_restriction_safety.py -q
```

---

## 8. What was NOT done

- Recipe generation
- Recipe import
- Photo generation
- Safe reset
- Production DB changes
- KBJU (Stage N)
- Shopping aggregation (Stage M)
- Household 500 (Stage O)
- `menu_generation_jobs` (Stage P)

---

## 9. Next recommended stage

**Stage D** — Povarenok culinary signals dry-run (no import).  
Or **Stage E** — original recipe generation pipeline design.

Parallel backlog: Stage N/M/O for KBJU, shopping, household.

---

## 10. Unrelated local changes (excluded)

Not part of Stage C commit:
- `apps/web/tsconfig.tsbuildinfo`
- `reports/visual_qa_p0_p1_hotfix.md` (deleted)
- `apps/web/build_log.txt`
