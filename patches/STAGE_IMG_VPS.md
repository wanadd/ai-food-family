# Stage IMG — VPS rollout (Gold V3 batch 256–265)

**Branch:** `feat/recipe-gold-v3-original-planam-library`  
**Scope:** hero image generation for Stage R recipes only — no import/schema changes.

## Files to deploy

| File | Action |
|------|--------|
| `docs/PLANAM_RECIPE_IMAGE_MASTER_PROMPT.md` | new |
| `apps/api/app/recipes/image_generation_config.py` | new |
| `apps/api/app/recipes/recipe_gold_v3_image_pipeline.py` | new |
| `backend/scripts/estimate_recipe_image_generation_cost_v3.py` | new |
| `backend/scripts/generate_recipe_images_v3.py` | new |
| `backend/scripts/validate_recipe_images_v3.py` | new |
| `apps/api/tests/test_recipe_gold_v3_image_pipeline.py` | new |

Reuses existing (no changes required):

- `backend/scripts/openai_recipe_image_client.py`
- `backend/scripts/process_recipe_images.py`
- `backend/scripts/apply_recipe_images.py` (URL pattern)
- `backend/scripts/_image_paths.py`

## Pre-flight on VPS

```bash
cd /var/www/ai-food-family   # or your deploy path
git status                   # must be clean before patch
test -n "$PLANAM_IMAGE_OPENAI_API_KEY" && echo "PLANAM_IMAGE_OPENAI_API_KEY=set" || echo "MISSING"
test -f reports/recipe_gold_v3_stage_r_created_ids.json && echo "Stage R IDs report OK"
```

Confirm Stage R backup exists (`reports/recipe_gold_v3_pre_import_db_snapshot.md` or backup script output).

## Build / restart API

```bash
docker compose -f docker-compose.prod.yml build api
docker compose -f docker-compose.prod.yml up -d api
```

## Step 1 — Cost estimate (no generation)

```bash
docker compose -f docker-compose.prod.yml exec api \
  python backend/scripts/estimate_recipe_image_generation_cost_v3.py \
  --ids 256,257,258,259,260,261,262,263,264,265
```

Expect: `would_generate=10`, `estimated_usd=0.63`, reports under `reports/recipe_image_generation_cost_estimate_v3.*`

## Step 2 — Dry-run generate

```bash
docker compose -f docker-compose.prod.yml exec api \
  python backend/scripts/generate_recipe_images_v3.py \
  --ids 256,257,258,259,260,261,262,263,264,265
```

Expect: `mode=dry-run`, `recommendation=PASS`, no API calls, no new files.

## Step 3 — Apply (real generation)

```bash
docker compose -f docker-compose.prod.yml exec api \
  python backend/scripts/generate_recipe_images_v3.py \
  --apply \
  --max-cost-usd 1.00 \
  --ids 256,257,258,259,260,261,262,263,264,265
```

Cap `1.00` is above estimate `0.63` — adjust if pricing changes.

## Step 4 — Validate

```bash
docker compose -f docker-compose.prod.yml exec api \
  python backend/scripts/validate_recipe_images_v3.py \
  --ids 256,257,258,259,260,261,262,263,264,265

curl -I https://planam.ru/recipe-images/256/hero.webp
```

Expect: `recommendation=PASS`, HTTP 200 on hero URLs.

## Idempotent re-run

Re-run generate without `--force` → `skipped=10`, no new API spend.

## Rollback

1. **DB URLs only** — set `hero_image_url`, `image_url`, `thumbnail_url` to NULL for IDs 256–265 (Stage R backup has pre-import state; images were NULL after import).
2. **Files** — remove only folders `recipe-images/256` … `recipe-images/265` on host (`/var/www/ai-food-family-data/recipe-images/`). Do not touch other IDs.
3. **No safe reset**, no old recipe updates.

## Env (prod)

```env
PLANAM_IMAGE_OPENAI_API_KEY=sk-...   # never log value
RECIPE_IMAGES_HOST_DIR=/var/www/ai-food-family-data/recipe-images
RECIPE_IMAGES_DIR=/app/public/recipe-images
RECIPE_IMAGES_PUBLIC_URL=/recipe-images
```
