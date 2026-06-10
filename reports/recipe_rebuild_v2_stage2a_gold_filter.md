# Recipe Rebuild V2 — Stage 2A Gold Filter Report

## Goal

Temporarily serve only gold Recipe V2 entries in catalog/menu/search while keeping
legacy recipes in DB (no safe reset apply).

## Endpoints / services updated

| Area | File | Change |
|------|------|--------|
| Gold filter helper | `apps/api/app/recipes/gold_filter.py` | `is_gold_v2_recipe`, `apply_gold_recipe_filter`, `query_active_recipes` |
| Config | `apps/api/app/config.py` | `recipe_gold_v2_only=True` (env override) |
| Catalog list | `repository.query_recipes` + `catalog.list_recipes` | Gold filter via tags |
| API | `GET /recipes`, `GET /recipes/filters` | Default gold-only; `include_legacy=true` for admins |
| Recommendations | `recommendations.get_recommendations` | Gold filter |
| Menu generation pool | `menu_recipe_builder.build_menus_from_recipes` | `query_active_recipes` |
| Multi-day menu | `menu_days.expand_variant_to_plan_days` | Gold pool |
| AI menu context | `ai_context._recipe_catalog_slice` | Gold catalog slice |
| Event plans | `event_plan.create_event_plan` | Gold pool |
| Shopping categories | `recipe_storage._resolve_ingredient_category` | V2 slug → legacy Russian slug |
| Recipe detail | `GET /recipes/{id}` | **Unchanged** — loads by id |

## Gold tag criteria

Recipe included when `tags` contains any of:

- `gold_v2`
- `recipe_schema_v2`
- `status:gold`

## Catalog counts (expected on VPS)

| Mode | Approx count |
|------|-------------|
| Before filter (legacy + gold) | ~253 active seed/import |
| After filter (default) | ~30 gold recipes |
| Admin `include_legacy=true` | full catalog |

Run on VPS:

```bash
curl -s -H "Authorization: Bearer …" "$API/recipes?limit=500" | jq '.total'
curl -s -H "Authorization: Bearer …" "$API/recipes?limit=500&include_legacy=true" | jq '.total'  # admin only
```

## Flows checked (by design)

- **Catalog / search / from-pantry / recommendations** — gold filter via `list_recipes`
- **Menu generation** — recipe DB pool filtered in `menu_recipe_builder` + AI catalog slice
- **Replace dish / add to menu** — user picks from gold catalog; existing menu slot keeps recipe_id (detail by id)
- **Shopping list from recipe** — structured ingredients; V2 categories mapped to legacy slugs for UI groups

## Legacy visibility gaps (known)

- **Recipe history / favorites** may reference legacy ids — detail by id still opens
- **Scenario recompute** (`scenarios.py`) still scans all active recipes (background job, not user catalog)
- **Collections** not filtered in Stage 2A (low traffic)
- **Non-admin** cannot pass `include_legacy`

## Safe reset

- **Not applied** — legacy rows remain
- Gold protection in safe reset unchanged (`gold_recipe_v2` blocked)

## Tests

```bash
cd apps/api && pytest tests/test_recipe_gold_v2_filter.py tests/test_recipes_catalog.py -q
cd apps/web && npx vitest run
```

## Deploy (VPS)

```bash
git checkout feat/recipe-gold-v2-app-filter && git pull
docker compose -f docker-compose.prod.yml build api web
docker compose -f docker-compose.prod.yml up -d api web nginx
```

Set `RECIPE_GOLD_V2_ONLY=true` in `.env` (default in code).

## Ready for safe reset apply?

**Not yet.** Validate Mini App on production with gold-only catalog first (menu, replace, shopping categories). Then run safe reset dry-run again and confirm blocked gold count = 30 before any `--apply`.
