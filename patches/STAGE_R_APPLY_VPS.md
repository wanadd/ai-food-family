# Stage R APPLY ONLY — VPS flow

**Base commit:** `32571f7`  
**Patch:** `stage_r_apply_only.patch`  
**Scope:** DB import 10 Gold V3 recipes — no images

## 1. Apply patch

```bash
git apply stage_r_apply_only.patch
```

## 2. Rebuild API

```bash
docker compose build api && docker compose up -d api
```

## 3. Verify inputs

- `exports/recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl`
- `reports/recipe_gold_v3_stage_gh_quality_gate_report.gpt4o_mini.md` (PASS)

## 4. Backup

```bash
python backend/scripts/backup_recipe_gold_v3_pre_import.py
```

## 5. Final dry-run

```bash
python backend/scripts/import_recipe_gold_v3_dry_run.py \
  --dry-run --expected-count 10
```

Expect: `records=10 would_create=10 recommendation=PASS`

## 6. Apply import

```bash
python backend/scripts/import_recipe_gold_v3_dry_run.py \
  --apply --allow-write --expected-count 10
```

Stop if FAIL.

## 7. Verify

```bash
curl -s "http://localhost:8000/recipes?limit=20"
```

Check `reports/recipe_gold_v3_stage_r_created_ids.json`

## 8. Copy reports to host

- `reports/recipe_gold_v3_pre_import_db_snapshot.md`
- `reports/recipe_gold_v3_stage_r_apply_import_report.md`
- `reports/recipe_gold_v3_stage_r_created_ids.json`

## Not in this stage

- Image generation
- `PLANAM_IMAGE_OPENAI_API_KEY`
- Safe reset
- Old recipe updates/deletes
