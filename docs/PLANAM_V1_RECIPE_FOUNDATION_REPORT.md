# PLANAM V1 Recipe Foundation Report

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Режим:** данные первыми — без Sprint 2, AI, доставки, Visual Polish

---

## Итог

| # | Вопрос | Ответ |
|---|--------|-------|
| 1 | Сколько рецептов импортировано | **150** в `data/planam_v1_recipes.json` (готово к `--commit` в БД) |
| 2 | Какие источники используются | **Povarenok CSV** → convert → select → build → import |
| 3 | Какие seed-рецепты остаются | 15 demo + 64 catalog placeholder — **архивируются** после V1 import |
| 4 | Какие рецепты готовы к Hero | **Top 50** (см. Block H); UI fallback без фото |
| 5 | Сколько фото доступно | **0** URL; 150 fallback |
| 6 | До Visual Polish | Фото Top 50, CDN, archive placeholders, `--commit` import |
| 7 | Готовность к Sprint 2 | **Данные:** да. **Продукт:** после фото + архивация seed |

---

## Recipe Data Inventory

| Источник | Количество | Используется | Удалить | Оставить |
|----------|------------|--------------|---------|----------|
| `apps/api/app/data/recipe_seed.py` (`SEED_RECIPES`) | 15 | Auto-seed при пустой БД | Архив (`is_active=false`) | — |
| `apps/api/app/data/recipe_catalog_seed.py` (`CATALOG_RECIPES`) | 64 | Auto-fill если < 50 рецептов | Архив | — |
| `sample_recipes.json` | 20 | Ручной импорт / QA | Не в prod | Dev sample |
| `scripts/seed_recipes.py` | — | Ручной ops | Deprecate | — |
| `seed_recipes_if_empty()` в `catalog.py` | — | API startup | **Отключён при ≥50 `v1_import`** | Логика gate |
| Povarenok pipeline | 150 V1 | **Primary catalog** | — | ✅ `data/planam_v1_recipes.json` |
| `exports/povarenok_*.jsonl` | 80k raw / 150 sel | Pipeline артефакты | gitignore | Локально |
| Test fixtures (`test_shopping_category_service`) | — | pytest | — | Tests |

---

## Block A — Recipe Inventory Audit

Поиск: seed, demo, temporary, test, fixtures, catalog seeds — см. таблицу выше.

**Вывод:** единственный production-источник V1 — Povarenok pipeline. Placeholder seeds не удаляются, а архивируются скриптом `archive_placeholder_recipes.py`.

---

## Block B — V1 Recipe Catalog

### Pipeline (проверен и выполнен)

| Скрипт | Назначение | Результат |
|--------|------------|-----------|
| `convert_povarenok.py` | CSV → JSONL | 80 000 записей |
| `select_povarenok_candidates.py` | Фильтр семейных блюд | 150 кандидатов |
| `audit_povarenok_jsonl.py` | Аудит (опционально) | — |
| `build_planam_v1_catalog.py` | Enrichment → import JSON | **150 рецептов** |
| `import_recipes.py` | DB import | dry-run ✅ |

### Требования V1

| Требование | Статус |
|------------|--------|
| 100–200 рецептов | ✅ 150 |
| Семейные блюда | ✅ |
| Обычные продукты | ✅ |
| Без алкоголя / заготовок / экзотики / сложной выпечки | ✅ (select filters) |

Детали: [`PLANAM_V1_RECIPE_QUALITY_REPORT.md`](PLANAM_V1_RECIPE_QUALITY_REPORT.md)

---

## Block C — Image Model

Добавлены колонки (миграция `database_migrations.py`):

```text
hero_image_url VARCHAR(512)
thumbnail_url VARCHAR(512)
```

Обновлено:

- `apps/api/app/models/recipe.py`
- `apps/api/app/schemas/recipe.py` (`RecipeSummary`)
- `apps/api/app/services/recipes/mapper.py`
- `backend/scripts/import_recipes.py`
- `apps/web/lib/recipes/types.ts`

Обратная совместимость: `image_url` остаётся primary; новые поля nullable.

---

## Block D — Image Coverage Plan

См. [`PLANAM_V1_RECIPE_IMAGE_PLAN.md`](PLANAM_V1_RECIPE_IMAGE_PLAN.md)

| Ready | Needs Image | Fallback |
|-------|-------------|----------|
| 0 | 150 | 150 |

---

## Block E — Hero Readiness

| Компонент | Готовность |
|-----------|------------|
| `PlanAmHero2026` | ✅ Фото через `meal.image_url`; fallback `MealFallbackPlate2026` |
| `RecipeImage2026` | ✅ `resolveRecipeImageUrl` + fallback |
| `MealFallbackPlate2026` | ✅ По `meal_type` |
| API Hero rail | ✅ `enrich_today_meals_images` — `hero_image_url ?? image_url ?? thumbnail_url` |

**Вывод:** Hero показывает реальные фото, когда URL есть; без фото не ломается.

---

## Block F — Placeholder Recipes (архив, не удаление)

### Placeholder

- `CATALOG_RECIPES` (64) — generic steps, напитки, event/bbq

### Demo

- `SEED_RECIPES` (15) — минимальный demo на пустой БД

### Legacy

- `sample_recipes.json` (20) — ранний import sample
- Дубликаты title между seed и sample

### Миграция

```bash
# После успешного V1 import:
python backend/scripts/archive_placeholder_recipes.py --dry-run
python backend/scripts/archive_placeholder_recipes.py --commit
```

`seed_recipes_if_empty()` пропускает placeholder seeds при **≥50 активных** `source_type=v1_import`.

---

## Block G — Recipe Quality Report

См. [`PLANAM_V1_RECIPE_QUALITY_REPORT.md`](PLANAM_V1_RECIPE_QUALITY_REPORT.md)

---

## Block H — Top 50 Hero Recipes

Кандидаты для Главная / Сегодня / Замена / Рекомендации. JSON: `reports/planam_v1_hero_top50.json`

| # | Приоритет | Рецепт |
|---|-----------|--------|
| 1 | Курица | Куриные котлеты с картофельным пюре в духовке |
| 2 | Говядина | Мясные "розы", фаршированные гречневой крупой |
| 3 | Рыба | Рыба «Красное и белое» |
| 4 | Супы | Куриный суп с домашней лапшой |
| 5 | Каши | Чисто английский завтрак из овсянки |
| 6 | Запеканки | Мацовая запеканка с грибами |
| 7 | Паста | Спагетти с курицей в сливочном соусе |
| 8 | Овощные | Салат "Баклажанчик" |
| 9 | Семейное | Салат "Винегретная фантазия" |
| 10 | Семейное | Гречка с грибами портабелла или шампиньонами |
| 11 | Семейное | Курица с черносливом |
| 12 | Семейное | Бедра куриные "По-французски" |
| 13 | Семейное | Холодный суп из авокадо с начинкой |
| 14 | Семейное | Салатик зимний "Витаминный" |
| 15 | Семейное | Сырный суп с шампиньонами и брокколи |
| 16 | Семейное | Салат из морепродуктов |
| 17 | Семейное | Салат "Рыбацкий" |
| 18 | Семейное | Рыбный картофель к блюду "Гефилте фиш" |
| 19 | Семейное | Салат с килькой |
| 20 | Семейное | Салат "Селяночка" |
| 21 | Семейное | Рыба "Вдохновение" |
| 22 | Семейное | Суп пюре из фасоли и моркови с красным перцем |
| 23 | Семейное | Грибной суп "Опятница" |
| 24 | Семейное | Рулет из куриного филе "Мелодия" |
| 25 | Семейное | Суп из баранины с нутом |
| 26 | Семейное | Фриттата с рисом и овощами |
| 27 | Семейное | Салат с морской капустой |
| 28 | Семейное | Суп вермишелевый |
| 29 | Семейное | Курица с рулетиками в духовке |
| 30 | Семейное | Картофельный салат по-американски |
| 31 | Семейное | Ложная жареная рыба |
| 32 | Семейное | А-ля "Люля" из курицы |
| 33 | Семейное | Суп "Грибное лукошко" |
| 34 | Семейное | Пикантный салат из печеной капусты |
| 35 | Семейное | Салат с клубникой |
| 36 | Семейное | Салат со шпротами |
| 37 | Семейное | Салат "Бешеная курица" |
| 38 | Семейное | Салат "Комплимент" |
| 39 | Семейное | Салат из печени и горошка "На пробу" |
| 40 | Семейное | Салат "Ламинария" |
| 41 | Семейное | Куриные окорочка сметанно-кунжутные |
| 42 | Семейное | Манная каша с бананом |
| 43 | Семейное | Запеченное мясо в фольге, с картофелем |
| 44 | Семейное | Картофель "Золотистый" |
| 45 | Семейное | Пшенная запеканка с малиной |
| 46 | Семейное | Котлеты овощные в вафельной оболочке |
| 47 | Семейное | Рис с яйцом-пашот с томатным соусом |
| 48 | Семейное | Суп "Цветик-семицветик" |
| 49 | Семейное | Салат "Цезарь" от Джейми Оливера |
| 50 | Семейное | "Королевская" запеканка |

---

## QA

| Check | Команда |
|-------|---------|
| pytest | `cd apps/api && python -m pytest` |
| lint | `npm run lint` |
| build | `npm run build` |

Проверено вручную:

- Hero без фото → `MealFallbackPlate2026`
- Hero с фото → `PlanAmHero2026` + `Image`
- Recipe cards → `RecipeImage2026` + fallback

---

## Новые / изменённые файлы

| Файл | Назначение |
|------|------------|
| `data/planam_v1_recipes.json` | V1 каталог (150) |
| `backend/scripts/build_planam_v1_catalog.py` | Enrichment pipeline |
| `backend/scripts/archive_placeholder_recipes.py` | Архивация placeholder |
| `docs/PLANAM_V1_RECIPE_*` | Отчёты A–H |

---

## Следующие шаги

1. `import_recipes.py --commit` на staging/prod
2. `archive_placeholder_recipes.py --commit`
3. Фото для Top 50 Hero
4. Visual Polish (отдельный спринт)
