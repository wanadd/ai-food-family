# Recipe Gold V3 — Stage B: Canonical Restrictions Catalog + Backend Safety

**Generated:** 2026-06-10  
**Branch:** `feat/recipe-gold-v3-original-planam-library`  
**Commit (Stage B work):** uncommitted on top of `2583fe3`  
**Stage A report commit:** `75713d1` (current work started from `2583fe3` — not an error)

---

## 1. Stage A commit note

Stage A audit report (`reports/recipe_gold_v3_initial_audit.md`) references commit `75713d1`.  
Stage B work started from commit `2583fe3` (`docs(recipes): add recipe gold v3 initial audit`).

---

## 2. Live VPS DB check

**Status:** Not executed from Cursor session (no VPS shell access from local environment).

Run on VPS to complete:

```bash
cd /var/www/ai-food-family
git status
git branch --show-current
git log -1 --oneline
git pull origin feat/recipe-gold-v3-original-planam-library
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml exec api bash -lc '
cd /app && PYTHONPATH=/app:/app/apps/api python - <<PY
from sqlalchemy import create_engine, text
import os
e = create_engine(os.environ["DATABASE_URL"])
with e.connect() as c:
    total = c.execute(text("SELECT COUNT(*) FROM recipes")).scalar()
    gold_v2 = c.execute(text("""
        SELECT COUNT(*) FROM recipes
        WHERE tags @> '\''["gold_v2"]'\''::jsonb
           OR tags @> '\''["recipe_schema_v2"]'\''::jsonb
           OR tags @> '\''["status:gold"]'\''::jsonb
    """)).scalar()
    print("recipes_total", total)
    print("gold_v2_tagged", gold_v2)
    for row in c.execute(text("""
        SELECT COALESCE(source_type,'null'), COUNT(*)
        FROM recipes GROUP BY 1 ORDER BY 2 DESC
    """)):
        print("source_type", row[0], row[1])
PY
'
```

| Field | Value |
|-------|-------|
| datetime | pending VPS run |
| branch | pending |
| git commit | pending |
| recipes_total | pending |
| gold_v2_tagged | pending |
| source_type distribution | pending |

**No DB changes were made during Stage B.**

---

## 3. Mini audit summary (restrictions scope only)

| Question | Answer |
|----------|--------|
| Where stored? | `user_profiles`: `allergies`, `diets`, `restrictions` (JSONB), `medical_restrictions`, `banned_foods`, `nutrition_goal`, `activity_level` |
| API exposure before B | `NutritionProfileData` had allergies/diets but **no** `restrictions` field |
| Recipe metadata | `recipe_restrictions`, `recipe_allergens`, `recipe_tags`; fallback `recipe.diets`, JSONB `ingredients` |
| Menu safety before B | Prompt-heavy (`menu_context.py`); `_filter_candidates` uses allergy string scan only |
| Stage C hook (pre-AI) | `menu_recipe_builder.build_menus_from_recipes` after `query_active_recipes` |
| Stage C hook (post-AI) | `menu.generate_menus_for_scope` after `generate_menus` |
| Files changed in B | See §4 |
| Not touched | menu generation logic, KBJU, shopping, household 500, migrations, recipe import/generation/photos |

---

## 4. Files added / changed

### Added

| File | Purpose |
|------|---------|
| `apps/api/app/nutrition/__init__.py` | Package exports |
| `apps/api/app/nutrition/restrictions_catalog.py` | Canonical catalog + normalization API |
| `apps/api/app/nutrition/restriction_safety.py` | Recipe vs profile safety checks |
| `apps/api/tests/test_restrictions_catalog.py` | Catalog unit tests (7) |
| `apps/api/tests/test_restriction_safety.py` | Safety unit tests (20) |
| `reports/recipe_gold_v3_stage_b_restrictions.md` | This report |

### Changed

| File | Change |
|------|--------|
| `apps/api/app/schemas/nutrition_profile.py` | Added `restrictions: list[str]` |
| `apps/api/app/services/nutrition_profile.py` | Read/write normalized `restrictions` |
| `apps/api/app/services/normalization/profile.py` | Canonical normalize on `restrictions` |
| `apps/api/app/routers/nutrition_profile.py` | `GET /nutrition-profile/restrictions-catalog` |
| `apps/api/app/services/menu_recipe_builder.py` | Stage C TODO comment (pre-AI) |
| `apps/api/app/services/menu.py` | Stage C TODO comment (post-AI) |

**No DB migrations.**

---

## 5. Canonical restriction keys (28)

### religious_cultural (hard)

`no_pork`, `no_beef`, `halal`, `kosher`, `no_alcohol`

### medical_safety

| Key | Severity |
|-----|----------|
| `diabetes_friendly`, `low_salt`, `low_sugar`, `pregnancy_safe`, `child_safe` | soft |
| `lactose_free`, `gluten_free` | hard |

### dietary

| Key | Severity |
|-----|----------|
| `vegetarian`, `vegan`, `pescatarian` | hard |
| `keto`, `low_carb`, `high_protein` | soft |

### goal (soft)

`weight_loss`, `mass_gain`, `healthy_eating`

### allergen_bridge (hard)

`no_nuts`, `no_peanuts`, `no_eggs`, `no_fish`, `no_seafood`, `no_soy`, `no_milk`

---

## 6. Aliases (examples)

Normalization accepts Russian and English free-text aliases, e.g.:

- `без свинины` / `no pork` → `no_pork`
- `халяль` / `halal` → `halal`
- `без глютена` / `gluten_free` → `gluten_free`
- `вегетарианство` / `vegetarian` → `vegetarian`
- `без лактозы` / `lactose free` → `lactose_free`
- `диабет` / `diabetes` → `diabetes_friendly`

Full alias lists are in `restrictions_catalog.py` per key. Unknown values are ignored (via `get_unknown_restrictions`).

---

## 7. Hard vs soft safety

| Severity | Behavior |
|----------|----------|
| **hard** | `recipe_is_allowed_for_profile` → `False`; blocks recipe in `filter_recipes_for_profile` |
| **soft** | `RestrictionConflict` with `severity=soft`; recipe **still allowed** unless another hard conflict exists |

Hard blocks use `banned_ingredient_markers` from catalog + profile `banned_foods` + recipe allergens vs profile allergies + `is_alcoholic` for `no_alcohol`.

Soft warnings use `warning_ingredient_markers` (diabetes, low_salt, keto, etc.).

---

## 8. Conflict explanation

`explain_recipe_restriction_conflicts(recipe, profile)` returns `RestrictionConflict` items with:

- `restriction_key`, `label_ru`, `severity`, `reason`
- optional `matched_ingredient`
- `source`: `ingredients`, `allergens`, `profile`, `recipe_restrictions`, `tags`, …

Checks (in order of relevance):

1. Active profile restrictions (from `restrictions` + normalized `diets` + allergy bridges)
2. Ingredient name / full recipe text marker scan
3. `is_alcoholic` flag
4. Profile `allergies` vs recipe allergens and ingredient markers
5. Profile `banned_foods` (comma/semicolon/newline split) — always hard
6. Recipe tags/diets/restrictions contradicting profile hard rules

`medical_restrictions` free text: **not parsed** (TODO Stage C+).

---

## 9. Profile field integration

| Field | Stage B handling |
|-------|------------------|
| `restrictions` | Normalized via `normalize_restrictions`; exposed in `GET/PUT /nutrition-profile/me` |
| `diets` | Merged into active keys via alias normalization |
| `allergies` | Bridged to allergen keys (`nuts`→`no_nuts`, etc.) + direct conflict explanation |
| `banned_foods` | Hard ingredient marker conflicts |
| `medical_restrictions` | Stored unchanged; NLP parsing deferred |

UI can use:

- `GET /nutrition-profile/restrictions-catalog` — Russian labels for pickers
- `list_restrictions_for_ui()` in Python for server-side rendering

---

## 10. Stage C integration points

### Pre-AI recipe pool filtering

**File:** `apps/api/app/services/menu_recipe_builder.py`  
**Function:** `build_menus_from_recipes`  
**After:** `query_active_recipes(...).all()`  
**Hook:**

```python
from app.nutrition.restriction_safety import filter_recipes_for_profile
recipes = filter_recipes_for_profile(recipes, profile)
```

Also applicable: `apps/api/app/services/ai_context.py` (`_recipe_catalog_slice`), `apps/api/app/services/recipes/catalog.py` (`list_recipes`).

### Post-AI menu validation

**File:** `apps/api/app/services/menu.py`  
**Function:** `generate_menus_for_scope`  
**After:** `generate_menus(...)` returns variants  
**Hook:**

```python
from app.nutrition.restriction_safety import explain_recipe_restriction_conflicts, has_hard_conflicts
# For each meal recipe_id → load Recipe → explain conflicts → reject/replace if hard
```

User-facing explanation: map `RestrictionConflict.reason` + `label_ru` into menu error/replacement message.

---

## 11. What was NOT done

- Recipe generation
- Recipe import
- Photo generation
- Safe reset
- Production data changes
- Mass menu generation rewrite
- KBJU fix
- Shopping aggregation fix
- Household 500 fix
- `menu_generation_jobs`
- DB migrations

---

## 12. Verification

```bash
python -m compileall apps/api/app          # OK
cd apps/api && python -m pytest \
  tests/test_restrictions_catalog.py \
  tests/test_restriction_safety.py -q      # 27 passed
```

---

## 13. Next recommended stage

**Stage C** — wire `filter_recipes_for_profile` and `explain_recipe_restriction_conflicts` into menu generation (pre-AI pool + post-AI validation) without prompt-only safety.

Alternative **Stage D** — Povarenok culinary signals dry-run (no import).

---

## 14. Deploy notes

Stage B is deploy-safe if:

- No migrations (confirmed)
- Tests pass (27/27)
- `compileall` OK
- Backend-only changes

VPS deploy (when ready):

```bash
cd /var/www/ai-food-family
git pull origin feat/recipe-gold-v3-original-planam-library
docker compose -f docker-compose.prod.yml up -d --build api
docker compose -f docker-compose.prod.yml logs --tail=150 api
```
