# Recipe Gold V3 — Initial Audit

**Generated:** 2026-06-12  
**Branch:** `feat/recipe-gold-v3-original-planam-library` @ `75713d1`  
**Base:** `feat/recipe-gold-v2-app-filter` (Stage 2A gold filter deployed)  
**Audit scope:** codebase + local exports (production DB queries require VPS)

---

## 1. Environment snapshot

| Check | Result |
|-------|--------|
| Git branch | `feat/recipe-gold-v3-original-planam-library` |
| Local Docker | **Unavailable** (Docker Desktop not running) |
| VPS docker/ps/logs | **Not run from this session** — run on VPS per §29 master spec |
| Production backup id (user report) | `20260610_132656` |
| Safe reset `--apply` | **Not executed** (correct) |

### VPS commands to complete live DB section

```bash
cd /var/www/ai-food-family
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
        WHERE tags @> '"'"'["gold_v2"]'"'"'::jsonb
           OR tags @> '"'"'["recipe_schema_v2"]'"'"'::jsonb
           OR tags @> '"'"'["status:gold"]'"'"'::jsonb
    """)).scalar()
    print("recipes_total", total)
    print("gold_v2_tagged", gold_v2)
    for row in c.execute(text("""
        SELECT COALESCE(source_type,'null'), COUNT(*) FROM recipes GROUP BY 1 ORDER BY 2 DESC
    """)):
        print("source_type", row[0], row[1])
PY
'
```

**Expected from prior VPS work (not re-verified here):**

| Metric | Approx value |
|--------|-------------|
| Total recipes | ~253 |
| Gold V2 (imported 30) | ~30 |
| Legacy (seed/import/v1) | ~223 |
| Safe reset would delete | ~207 |
| Safe reset blocked (gold + protected) | ~46 |

---

## 2. Why Gold V2 is not production-ready

Manual QA + seed file review confirm the user's assessment. Current `data/recipe_v2/gold_recipes_30.jsonl` is a **technical test seed**, not a user-facing library.

### 2.1 English / AI prefixes in titles

Examples from gold seed:

| Title | Issue |
|-------|-------|
| `High protein: говядина с брокколи` | English prefix |
| `Pro small portion: яйца с авокадо` | English prefix |
| `Pre-workout: банан с арахисовой пастой` | English prefix |
| `Творожная bowl с фруктами` | English word in Russian title |

### 2.2 Technical / English categories & tags

- Recipe `category` values: `eggs`, `casserole`, `porridge`, `sport` (English slugs)
- Tags: `gold_v2`, `breakfast_omelet`, `pro_high_protein` (mixed EN)
- Restrictions in V2 validator use keys like `no_pork` — **not exposed as Russian UI labels**

### 2.3 Steps quality

- Several recipes have 1–3 short steps (`"Смешать…"`, `"Подать…"`)
- Gold V3 requirement: **minimum 4 steps**, each ≥25 chars

### 2.4 КБЖУ split-brain bug (confirmed in code)

**Symptom:** Top metric chip shows kcal/B/J/U; block «КБЖУ на порцию» shows dashes.

**Root cause:**

| Layer | Field used |
|-------|------------|
| Import V2 (`import_recipe_v2.py`) | Writes `calories_per_serving`, `protein_g`, `fat_g`, `carbs_g` |
| Mapper (`mapper.nutrition_summary`) | Reads `nutrition_kcal_per_serving`, `nutrition_protein_per_serving`, … |
| UI top line (`RecipeDetail2026.nutritionLine`) | Falls back to legacy `calories_per_serving` ✅ |
| UI block (`perServingMacros`) | Uses `nutrition_summary.*_per_serving` only → **empty** ❌ |

**Fix direction (Stage N):** Single contract `nutrition_per_serving` populated on import + mapper fallback to legacy columns.

### 2.5 Shopping list issues (confirmed in code)

`aggregate_ingredients_for_shopping()` (`recipe_storage.py`):

- Merges only on **exact** `(normalize_name_key(name), unit, category)` tuple
- Does **not** canonicalize `яйцо` vs `яйца`
- No rounding (`173.3 г` passes through)
- Category from V2 English slug partially mapped via `_resolve_ingredient_category` (Stage 2A), but aggregation key still splits variants

### 2.6 Images

- Gold V2 recipes have `image_url: null`
- No hero.webp assigned for gold batch
- Existing image pipeline is V1-oriented (see §8)

---

## 3. Povarenok data sources

### 3.1 Files found

| Path | Lines (local) | Role |
|------|---------------|------|
| `exports/povarenok_planam_raw.jsonl` | large raw scrape | Source |
| `exports/povarenok_candidates_100.jsonl` | **100** | Selected candidates |
| `exports/povarenok_candidates_150.jsonl` | 150 | Extended selection |
| `exports/povarenok_import_100.json` | JSON batch | Legacy import format |
| `exports/povarenok_enriched_100.jsonl` | enriched | Old enrichment path |
| `exports/povarenok_enrichment_input_100.jsonl` | input | Enrichment input |

### 3.2 Povarenok scripts

| Script | Purpose |
|--------|---------|
| `backend/scripts/select_povarenok_candidates.py` | Filter alcohol/preserves/complex baking |
| `backend/scripts/audit_povarenok_jsonl.py` | Quality audit |
| `backend/scripts/convert_povarenok.py` | Format conversion |
| `backend/scripts/analyze_povarenok_dataset.py` | Dataset stats |
| `backend/scripts/prepare_povarenok_enrichment_input.py` | Legacy enrichment prep |

### 3.3 Raw record shape (example)

```json
{
  "source": "povarenok",
  "source_url": "https://www.povarenok.ru/recipes/show/10625/",
  "title": "Салат \"Баклажанчик\"",
  "ingredients": [...],
  "steps": []
}
```

**Critical:** Current exports retain **original Povarenok title and ingredient names**. V3 pipeline must **not** import these directly — only neutral culinary signals (Stage D).

### 3.4 V3 input file for extraction

Master spec: `exports/povarenok_candidates_100.jsonl` — **exists locally (100 records)**.

---

## 4. Recipe data model map

### 4.1 Core tables (`apps/api/app/models/recipe.py`)

| Table / JSONB | Purpose |
|---------------|---------|
| `recipes` | Title, meal_type, category, servings, times, legacy KBJU columns, `nutrition_*` summary columns, `tags` JSONB, `ingredients`/`steps` JSONB mirrors |
| `recipe_ingredients` | Structured rows: name, quantity, unit, category |
| `recipe_steps` | step_number, text |
| `recipe_tags` | Normalized tag rows |
| `recipe_allergens` | Allergen rows |
| `recipe_restrictions` | Restriction key rows |
| `recipe_favorites` | User favorites |
| `recipe_ratings` | Ratings |

### 4.2 Engine tables (`recipe_engine.py`)

| Table | Purpose |
|-------|---------|
| `recipe_collections` / `collection_recipes` | Collections |
| `recipe_history` | Cooking history |
| `recipe_scenarios` | Scenario matching |
| `recipe_explanations` | Explainability |
| `family_recipe_preferences` | Family prefs |

### 4.3 Menu / shopping links

| Table | Link |
|-------|------|
| `meal_checkins` | `recipe_id` |
| Shopping list | JSONB items on scope list (not recipe_id FK); built from menu ingredients |

### 4.4 Gold tagging convention today

| Tag | Meaning |
|-----|---------|
| `gold_v2` | Test seed marker |
| `recipe_schema_v2` | Schema version marker |
| `status:gold` | Status marker |

V3 will add: `gold_v3`, `recipe_schema_v3`.

---

## 5. API / services map (recipes → UI)

| Flow | Endpoint / service | Gold filter (Stage 2A) |
|------|-------------------|--------------------------|
| Catalog | `GET /recipes` → `catalog.list_recipes` → `repository.query_recipes` | ✅ `gold_filter.py` |
| Search | `SearchService` → `catalog.list_recipes` | ✅ |
| Detail by id | `GET /recipes/{id}` → `get_recipe_with_relations` | ❌ **No filter** (by design) |
| Recommendations | `GET /recipes/recommendations` | ✅ |
| From pantry | `GET /recipes/from-pantry` | ✅ |
| Menu pool | `menu_recipe_builder.build_menus_from_recipes` | ✅ `query_active_recipes` |
| Multi-day menu | `menu_days.expand_variant_to_plan_days` | ✅ |
| AI catalog slice | `ai_context._recipe_catalog_slice` | ✅ |
| Event plans | `event_plan.create_event_plan` | ✅ |
| Add to shopping | `authoring.add_recipe_to_shopping` | N/A (by recipe id) |
| Replace dish | `POST /menus/replace-dish` + catalog pick | Partial (AI may invent) |
| Menu generate | `POST /menus/generate` | Uses filtered pool via AI context |

**Config:** `recipe_gold_v2_only=True` (`RECIPE_GOLD_V2_ONLY`), admin `include_legacy=true`.

**Not yet implemented:** `RECIPE_GOLD_VERSION=v3`, `gold_v3` filter, `menu_generation_jobs`.

---

## 6. Nutrition & restrictions (profiles)

### 6.1 User profile (`user_profiles`)

| Field | Type | Used for |
|-------|------|----------|
| `allergies` | JSONB list | Allergies |
| `diets` | JSONB list | Diets |
| `restrictions` | JSONB list | Exists in DB, **weak API/UI exposure** |
| `medical_restrictions` | text | Free text |
| `banned_foods` | text | Free text |
| `nutrition_goal`, `activity_level` | strings | Goals |

### 6.2 Nutrition profile API (`NutritionProfileData`)

- Exposes: `allergies`, `diets`, `medical_restrictions`, `banned_foods`
- **Missing:** canonical religious/cultural keys (`halal`, `no_pork`, …)
- Gap report: `reports/nutrition_profile_religious_restrictions_gap.md`

### 6.3 Recipe restrictions today

- `recipe_restrictions` rows + `diets` JSONB
- V2 validator uses `excludes`, `religious_tags`, `diet_tags` in JSONL only
- **No shared `restrictions_catalog.py`** yet
- Menu safety is **prompt-heavy**, not backend-guaranteed

**Stage B/C requirement:** Single canonical catalog + `recipe_is_allowed_for_profile()` before/after AI.

---

## 7. Shopping & categories

| Module | Path | Notes |
|--------|------|-------|
| V1 categories | `apps/api/app/services/categories_v1.py` | Russian slugs incl. `быт_уборка` |
| V2 taxonomy | `apps/api/app/recipes/product_taxonomy.py` | English slugs + legacy map |
| Infer category | `shopping_categories.infer_category` | Name heuristics |
| Aggregation | `recipe_storage.aggregate_ingredients_for_shopping` | **Needs V3 rewrite** |
| Manual add | `shopping_list.create_item` → `resolve_category_for_item` | Household via `быт_уборка` |

### «Дом и быт» 500 error

- Category slug in system: `быт_уборка` (label «Быт и уборка»)
- `create_item` calls `resolve_category_for_item` — failure likely in category resolution or non-food path
- **Needs VPS reproduction** with API logs (Stage O)

---

## 8. Image provider / token / cost (existing V1 pipeline)

### 8.1 Provider configuration

| Setting | Value |
|---------|-------|
| Provider | **OpenAI Images** |
| Client | `backend/scripts/openai_recipe_image_client.py` |
| Default model | `gpt-image-1` |
| Default size | `1536x1024` |
| Default quality | `medium` |
| Output | master image → crop to hero/card/thumb |

### 8.2 API key (env names only — never log values)

| Priority | Env variable |
|----------|--------------|
| 1 | `PLANAM_IMAGE_OPENAI_API_KEY` |
| 2 | `IMAGE_OPENAI_API_KEY` (alias in config) |
| 3 (fallback) | `OPENAI_API_KEY` |

Config: `apps/api/app/config.py` → `effective_image_openai_api_key`

### 8.3 Cost estimates (from `COST_TABLE` in client)

| Size | Quality | ~USD/image |
|------|---------|------------|
| 1536x1024 | medium | **$0.063** |
| 1536x1024 | high | $0.25 |
| 1024x1024 | medium | $0.042 |

**Batch estimates (medium, 1536x1024):**

| Batch | Est. cost |
|-------|-----------|
| 10 | ~$0.63 |
| 30 | ~$1.89 |
| 50 | ~$3.15 |
| 100 | ~$6.30 |
| 300 | ~$18.90 |
| 1000 | ~$63.00 |

### 8.4 Master photo style docs (existing)

| Document | Status |
|----------|--------|
| `docs/PLANAM_V1_RECIPE_IMAGE_STYLE_SYSTEM.md` | **Freeze for V1** — single serviz, light kitchen, no text |
| `docs/PLANAM_V1_RECIPE_IMAGE_AI_PROMPTS.md` | Prompt templates |
| `docs/PLANAM_V1_RECIPE_IMAGE_TOKEN_SETUP.md` | Key setup |
| `docs/PLANAM_V1_RECIPE_IMAGE_AI_BUDGET.md` | Budget notes |

**V3 action:** Promote to `PLANAM_RECIPE_IMAGE_MASTER_PROMPT.md` + `PLANAM_RECIPE_IMAGE_STYLE_V3.md` (Stage J).

### 8.5 Image scripts

- `build_recipe_image_prompts.py`
- `run_recipe_image_pilot.py`
- `process_recipe_images.py`
- `apply_recipe_images.py`
- `audit_recipe_images.py`

**Not yet:** `generate_recipe_images_v3.py`, `estimate_recipe_image_generation_cost_v3.py`, cost guard `--max-cost-usd`.

---

## 9. Menu generation (current vs required)

### 9.1 Current architecture

| Component | Behavior |
|-----------|----------|
| API | `POST /menus/generate` — **synchronous** request |
| Frontend | `GenerateMenuV2.tsx` → `generateMenus()` — awaits full response |
| Loading UI | `AiProcessLoadingV2` — in-page, not durable |
| Background | **None** — connection drop / Mini App minimize = failed generation |

### 9.2 Required (Stage P/Q)

- Table `menu_generation_jobs`
- `POST /menu/generation-jobs` + polling
- Full-screen `MenuGenerationFullScreen` with resume on app return
- Backend validation after AI (restrictions + shopping)

---

## 10. Existing V2/V3 building blocks

| Asset | Path | V3 reuse |
|-------|------|----------|
| Gold filter | `apps/api/app/recipes/gold_filter.py` | Extend for `gold_v3` |
| V2 validation | `apps/api/app/recipes/recipe_v2_validation.py` | Basis for V3 validator |
| Product taxonomy | `apps/api/app/recipes/product_taxonomy.py` | Shopping categories |
| Safe reset | `backend/scripts/recipe_rebuild_v2_safe_reset.py` | Keep dry-run only |
| Import V2 | `backend/scripts/import_recipe_v2.py` | Template for import V3 |
| Povarenok selector | `select_povarenok_candidates.py` | Reference for signal extraction filters |

**Not started:** originality validation, diversity gate, restrictions catalog, shopping aggregation V3, menu jobs.

---

## 11. Gaps vs master spec (priority order)

| Stage | Item | Status |
|-------|------|--------|
| A | This audit | ✅ |
| B | Canonical restrictions catalog | ❌ |
| C | Menu hard/soft constraints | ❌ |
| D | Povarenok signal extraction | ❌ |
| E | Gold V3 schema + validator | ❌ |
| F | Original recipe generation | ❌ |
| G | Originality validation | ❌ |
| H | Quality gate | ❌ |
| I | Diversity gate | ❌ |
| J | Master photo prompt V3 docs | ❌ (V1 docs exist) |
| K | Image cost audit script | ❌ (table in client exists) |
| L | Image generation V3 pipeline | ❌ |
| M | Shopping aggregation V3 | ❌ |
| N | КБЖУ detail fix | ❌ |
| O | Дом и быт 500 fix | ❌ |
| P | Menu generation jobs | ❌ |
| Q | Full-screen menu UI | ❌ |
| R | Importer V3 | ❌ |
| S | Gold filter V3 | ❌ |
| T | Admin debug visibility | ❌ |
| U | Rollback plan | ❌ |

---

## 12. Recommended next steps (strict order)

1. **VPS:** Run live DB queries from §1 and append counts to this report.
2. **Stage B:** `restrictions_catalog.py` + `restriction_safety.py` + doc.
3. **Stage D:** `extract_povarenok_culinary_signals_v3.py` on `povarenok_candidates_100.jsonl` (dry-run, no import).
4. **Stage E–H:** Schema + validators (no generation until signal report reviewed).
5. **Stage F:** Generate **10** recipes only (`--limit 10 --dry-run` first).
6. **Stage K:** Cost estimate before any `--apply` image generation.
7. **Stage N + M + O:** Fix КБЖУ contract, shopping aggregation, household 500 in parallel with first batch QA.
8. **Do not:** safe reset apply, mass import, mass image generation without approval.

---

## 13. Safety checklist (unchanged)

- [x] Safe reset `--apply` not run
- [x] Legacy recipes not deleted
- [x] Povarenok not imported to production in this audit
- [ ] Gold V3 pipeline not started (by design — audit only)

---

*Next deliverable: `reports/povarenok_culinary_signals_v3_report.md` after Stage D extraction on VPS/local with API keys for generation disabled.*
