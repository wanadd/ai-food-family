# PLANAM V1 — Recipe Image Pilot Report

**Дата:** 2026-06-06  
**Объём:** 10 рецептов (pilot only)  
**Источник:** `data/planam_v1_image_pilot_batch.json`  
**Модель:** `gpt-image-1` · master `1536×1024` · quality `medium`  
**Концепция:** 1 рецепт → 1 master image → hero / card / thumb (crop)

---

## 1. Что создано

| Файл | Назначение |
|------|-----------|
| `backend/scripts/openai_recipe_image_client.py` | Клиент image-генерации на **отдельном** ключе |
| `backend/scripts/run_recipe_image_pilot.py` | Pilot runner: single / batch / dry-run / commit |
| `docs/PLANAM_V1_RECIPE_IMAGE_PILOT_REPORT.md` | Этот отчёт |
| `docs/PLANAM_V1_RECIPE_IMAGE_PILOT_BUDGET_REPORT.md` | Стоимость pilot / Top50 / 150 / 1000 |
| `docs/PLANAM_V1_RECIPE_IMAGE_TOKEN_SETUP.md` | Настройка отдельного ключа |
| `reports/planam_v1_recipe_image_pilot_results.json` | Результаты (заполняется при `--commit`) |

Изменены: `apps/api/app/config.py` (`PLANAM_IMAGE_OPENAI_API_KEY`),
`backend/scripts/process_recipe_images.py` и `apply_recipe_images.py`
(путь по умолчанию → `apps/web/public/recipe-images`), `.gitignore`.

---

## 2. Pilot batch (10 рецептов)

| # | title | meal_type | category | vessel |
|---|-------|-----------|----------|--------|
| 1 | Куриные котлеты с картофельным пюре в духовке | dinner | main | flat plate |
| 2 | Мясные «розы», фаршированные гречневой крупой | dinner | main | flat plate |
| 3 | Рыба «Красное и белое» | dinner | main | flat plate |
| 4 | Куриный суп с домашней лапшой | lunch | soup | deep bowl |
| 5 | Чисто английский завтрак из овсянки | breakfast | breakfast | bowl |
| 6 | Мацовая запеканка с грибами | dinner | main | plate/portion |
| 7 | Спагетти с курицей в сливочном соусе | dinner | main | flat plate |
| 8 | Салат «Баклажанчик» | lunch | salad | shallow bowl |
| 9 | Салат «Винегретная фантазия» | lunch | salad | shallow bowl |
| 10 | Гречка с грибами портабелла или шампиньонами | dinner | side | bowl/plate |

---

## 3. Pipeline

```text
pilot batch entry
  → resolve DB recipe (by id, fallback by normalized_title)
  → generate_master_image()  →  apps/web/public/recipe-images/{id}/master.png
  → process_master()         →  master.webp, hero.webp, card_800.webp, thumb_400.webp
  → apply_urls_to_db()       →  hero_image_url, image_url, thumbnail_url
  → results JSON
```

`recipe_id` в pilot batch — это индекс (1..10). На сервере runner находит
**реальный** id рецепта в БД по title и использует его для папки и URL.

URL пишутся локальные (под Next static): `/recipe-images/{id}/hero.webp` и т.д.
Совместимы с будущим CDN-переключением (`apply_recipe_images.py --base-url`).

---

## 4. Статусы

`planned → generated_draft → approved / rejected / needs_retry → final_ready`

Текущий статус всех 10: **planned** (генерация выполняется на сервере после
добавления `PLANAM_IMAGE_OPENAI_API_KEY` — см. Token Setup).

---

## 5. Результаты (заполнить после запуска)

После `--commit` файл `reports/planam_v1_recipe_image_pilot_results.json`
содержит для каждого рецепта: `recipe_id`, `title`, `prompt`, `status`,
`duration_s`, `cost_usd`, `usage`, `urls`, `quality_score`, `approved`.

| recipe_id | title | status | cost | duration | quality | approved |
|-----------|-------|--------|------|----------|---------|----------|
| 1–10 | см. batch | pending | — | — | — | — |

---

## 6. Стоимость

Оценка (medium, 1536×1024): **$0.063 / рецепт** → **pilot 10 ≈ $0.63**.
Полная модель — `PLANAM_V1_RECIPE_IMAGE_PILOT_BUDGET_REPORT.md`.

---

## 6b. Hotfix — ID resolution (2026-06-06)

Баг: pilot JSON `recipe_id` (индекс батча 1..10) использовался как PK в БД →
фото попадали в архивные `manual`-рецепты id 1..10 вместо активных `v1_import`.

Фикс:
- `backend/scripts/recipe_id_resolver.py` — единый источник истины: поиск по
  title среди `source_type='v1_import' AND is_active=true`; 0 или >1 → ошибка.
- `run_recipe_image_pilot.py` и `apply_recipe_images.py` больше не используют
  pilot/manifest id как PK — только title.
- `backend/scripts/repair_recipe_image_assignments.py` — переносит URL на верный
  рецепт и очищает их у ошибочных id 1..10 (`--dry-run` / `--commit`).
- `tests/test_recipe_image_resolver.py` — 6 тестов (title → верный v1_import id).

Repair на сервере:
```bash
docker compose -f docker-compose.prod.yml exec api \
  python backend/scripts/repair_recipe_image_assignments.py --dry-run
docker compose -f docker-compose.prod.yml exec api \
  python backend/scripts/repair_recipe_image_assignments.py --commit
```

## 7. Что НЕ делалось (по ТЗ)

- Не запускался Top 50 и не все 150.
- Не настраивался CDN.
- Не менялся UI / Hero / каталог / shopping / wellness / family.
- Реальные ключи и тяжёлые изображения не коммитятся.
