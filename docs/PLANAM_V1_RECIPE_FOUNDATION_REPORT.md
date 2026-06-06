# PLANAM V1 Recipe Foundation + Image Pipeline Report

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Режим:** данные + image pipeline — без Sprint 2, AI Nutritionist, доставки, Visual Polish, массовой генерации

---

## Итог (8 вопросов)

| # | Вопрос | Ответ |
|---|--------|-------|
| 1 | Какие рецепты подготовлены | **150** V1 в `data/planam_v1_recipes.json`; **10** pilot prompts |
| 2 | Сколько в V1 каталоге | **150** (цель 100–200 ✅) |
| 3 | Какие старые seed остаются | 15 demo + 64 catalog placeholder в коде |
| 4 | Какие seed архивировать | Все placeholder titles + `source_type=seed` → `archive_placeholder_recipes.py` |
| 5 | Готов ли import | ✅ dry-run 150/150; `--commit` на окружении с `DATABASE_URL` |
| 6 | Готов ли UI к изображениям | ✅ `hero_image_url`, `image_url`, `thumbnail_url` + fallback |
| 7 | Готов ли pilot AI photo | ✅ prompts + style system + scripts; **генерация не запущена** |
| 8 | Следующие шаги | pilot 10 → cost model → Top 50 decision → apply URLs |

---

## Recipe Data Inventory

| Источник | Кол-во | Используется | Роль | Оставить | Архивировать | Удалить позже | Риск |
|----------|--------|--------------|------|----------|--------------|---------------|------|
| `recipe_seed.py` | 15 | API startup (пустая БД) | Demo bootstrap | — | ✅ после V1 import | Позже | Средний — дубли title |
| `recipe_catalog_seed.py` | 64 | API fill <50 | Placeholder catalog | — | ✅ | Позже | Высокий — drinks/alcohol/event |
| `sample_recipes.json` | 20 | Ручной QA | Dev sample | Dev only | — | Позже | Низкий |
| `scripts/seed_recipes.py` | — | Manual ops | Legacy ops | — | Deprecate | Позже | Низкий |
| `seed_recipes_if_empty()` | — | API startup | Auto-seed gate | Логика gate | N/A | — | **Снят при ≥50 v1_import** |
| `data/planam_v1_recipes.json` | 150 | **Primary V1** | Production catalog | ✅ | — | — | Низкий |
| `exports/povarenok_*.jsonl` | 80k/150 | Pipeline | Build artifacts | Локально | — | — | Низкий (gitignore) |
| `data/planam_v1_image_pilot_batch.json` | 10 | Image pilot | AI prompts | ✅ | — | — | Низкий |
| `reports/planam_v1_hero_top50.json` | 50 | Hero priority | Marketing/UX | ✅ | — | — | Низкий |
| Test fixtures | — | pytest | CI | ✅ | — | — | Нет |

---

## Block B — V1 Recipe Catalog

| Этап | Скрипт | Результат |
|------|--------|-----------|
| Convert | `convert_povarenok.py` | 80 000 raw |
| Select | `select_povarenok_candidates.py --limit 150` | 150 candidates |
| Build | `build_planam_v1_catalog.py` | enriched JSON |
| Import | `import_recipes.py --dry-run` | 150 OK |

Требования: семейные, 3–25 ингредиентов, без алкоголя/заготовок/выпечки — ✅

---

## Block C — Enrichment

Поля в каталоге: `title`, `original_title`, `normalized_title`, `display_title`, `description`, `ingredients`, `steps`, `meal_type`, `category`, `source_type=v1_import`, `source_url`, image URLs (null), `steps_quality=steps_generated`, `short_visual_description`.

---

## Block D — Image Model

| Слой | Статус |
|------|--------|
| DB `hero_image_url`, `thumbnail_url` | ✅ migration |
| Model / schema / mapper | ✅ |
| `import_recipes.py` | ✅ |
| Frontend `types.ts`, `recipe-media.ts` | ✅ |
| Hero API `enrich_today_meals_images` | ✅ cascade |

---

## Blocks E–K — Image Pipeline

| Документ | Содержание |
|----------|------------|
| [PLANAM_V1_RECIPE_IMAGE_STYLE_SYSTEM.md](./PLANAM_V1_RECIPE_IMAGE_STYLE_SYSTEM.md) | Style + vessel mapping + one-master rule + storage |
| [PLANAM_V1_RECIPE_IMAGE_AI_PROMPTS.md](./PLANAM_V1_RECIPE_IMAGE_AI_PROMPTS.md) | Master prompt template + builder |
| [PLANAM_V1_RECIPE_IMAGE_AI_PILOT.md](./PLANAM_V1_RECIPE_IMAGE_AI_PILOT.md) | Pilot 10 table |
| [PLANAM_V1_RECIPE_IMAGE_AI_BUDGET.md](./PLANAM_V1_RECIPE_IMAGE_AI_BUDGET.md) | Cost formula (TBD after pilot) |
| [PLANAM_V1_RECIPE_IMPORT_PIPELINE.md](./PLANAM_V1_RECIPE_IMPORT_PIPELINE.md) | Full data + image pipeline |

### Скрипты

| Скрипт | Назначение |
|--------|------------|
| `recipe_image_utils.py` | Vessel mapping, prompts |
| `build_recipe_image_prompts.py` | Pilot batch JSON |
| `process_recipe_images.py` | master → hero/card/thumb WebP |
| `apply_recipe_images.py` | URL → DB |
| `archive_placeholder_recipes.py` | Placeholder → `is_active=false` |

---

## Block N — Placeholder Gate

```python
# catalog.py: skip seeds if v1_count >= 50
```

```bash
python backend/scripts/archive_placeholder_recipes.py --dry-run
python backend/scripts/archive_placeholder_recipes.py --commit  # after import
```

---

## Block O–P — Reports

- [PLANAM_V1_RECIPE_QUALITY_REPORT.md](./PLANAM_V1_RECIPE_QUALITY_REPORT.md)
- [PLANAM_V1_RECIPE_IMAGE_PLAN.md](./PLANAM_V1_RECIPE_IMAGE_PLAN.md)

---

## Block Q — Top 50 Hero

`reports/planam_v1_hero_top50.json` — 50 рецептов для Главная / Сегодня / Замена / Рекомендации.

Pilot 10 = первые 10 из этого списка.

---

## QA

| Check | Result |
|-------|--------|
| `cd apps/api && python -m pytest` | 86 passed |
| `cd apps/web && npm run lint` | OK (warnings only) |
| `cd apps/web && npm run build` | OK |
| `import_recipes.py --dry-run` | 150/150 |
| `archive_placeholder_recipes.py --dry-run` | requires DB |
| `process_recipe_images.py --help` | OK |
| `apply_recipe_images.py --help` | OK |

---

## Следующие шаги

1. `import_recipes.py --commit` на staging
2. `archive_placeholder_recipes.py --commit`
3. AI pilot 10 (master only)
4. Заполнить `actual_cost` → бюджет Top 50 / 150
5. Visual Polish — отдельный этап
