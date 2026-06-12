# Stage G/H тАФ VPS apply + quality gate run

Base commit: `6ddfdfa` (Stage F.1). Apply Stage G/H patch on top.

---

## 1. Apply patch on VPS

```bash
cd /var/www/ai-food-family
git status
git log -1 --oneline   # expect 6ddfdfa

# copy stage_gh_only.patch to VPS, then:
git apply --check stage_gh_only.patch
git apply stage_gh_only.patch

git status   # only Stage G/H files should appear
```

Or cherry-pick / pull branch once G/H is pushed.

---

## 2. Rebuild api container

```bash
cd /var/www/ai-food-family
docker compose -f docker-compose.prod.yml build api
docker compose -f docker-compose.prod.yml up -d api
```

---

## 3. Copy F.1 batch JSONL / signals into container (if missing in /app/exports)

If batches were generated inside the container and only exist on host:

```bash
# host тЖТ container
docker compose -f docker-compose.prod.yml cp \
  exports/recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl \
  api:/app/exports/recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl

docker compose -f docker-compose.prod.yml cp \
  exports/recipe_gold_v3_generated_10_dry_run.strong.jsonl \
  api:/app/exports/recipe_gold_v3_generated_10_dry_run.strong.jsonl

docker compose -f docker-compose.prod.yml cp \
  exports/povarenok_culinary_signals_v3_100.jsonl \
  api:/app/exports/povarenok_culinary_signals_v3_100.jsonl
```

Verify inside container:

```bash
docker compose -f docker-compose.prod.yml exec api bash -lc \
  'ls -la /app/exports/recipe_gold_v3_generated_10_dry_run*.jsonl /app/exports/povarenok_culinary_signals_v3_100.jsonl'
```

---

## 4. Run quality gate

### gpt-4o-mini

```bash
docker compose -f docker-compose.prod.yml exec api bash -lc \
  'cd /app && PYTHONPATH=/app:/app/apps/api python backend/scripts/quality_gate_recipe_gold_v3.py \
  --input exports/recipe_gold_v3_generated_10_dry_run.gpt4o_mini.jsonl \
  --signals exports/povarenok_culinary_signals_v3_100.jsonl \
  --report reports/recipe_gold_v3_stage_gh_quality_gate_report.gpt4o_mini.md \
  --min-score 85 --avg-score 90 --dry-run'
```

### gpt-4.1

```bash
docker compose -f docker-compose.prod.yml exec api bash -lc \
  'cd /app && PYTHONPATH=/app:/app/apps/api python backend/scripts/quality_gate_recipe_gold_v3.py \
  --input exports/recipe_gold_v3_generated_10_dry_run.strong.jsonl \
  --signals exports/povarenok_culinary_signals_v3_100.jsonl \
  --report reports/recipe_gold_v3_stage_gh_quality_gate_report.strong.md \
  --min-score 85 --avg-score 90 --dry-run'
```

Exit code `0` = PASS, `1` = FAIL.

---

## 5. Copy reports from container to host

```bash
docker compose -f docker-compose.prod.yml cp \
  api:/app/reports/recipe_gold_v3_stage_gh_quality_gate_report.gpt4o_mini.md \
  reports/recipe_gold_v3_stage_gh_quality_gate_report.gpt4o_mini.md

docker compose -f docker-compose.prod.yml cp \
  api:/app/reports/recipe_gold_v3_stage_gh_quality_gate_report.strong.md \
  reports/recipe_gold_v3_stage_gh_quality_gate_report.strong.md
```

---

## 6. Show reports

```bash
sed -n '1,260p' reports/recipe_gold_v3_stage_gh_quality_gate_report.gpt4o_mini.md
sed -n '1,260p' reports/recipe_gold_v3_stage_gh_quality_gate_report.strong.md
```

---

## 7. Local tests (optional on VPS host)

```bash
python -m compileall apps/api/app backend/scripts
cd apps/api && python -m pytest tests/test_recipe_gold_v3_quality_gate.py -q
```

---

## Not done

- DB import
- Image generation
- Safe reset
- Production DB changes
