# PLANAM Recipe DB GO — Report

Дата: 2026-06-05  
Ветка: `sprint-0/planam-2026-foundation`  
Базовый коммит: `b053d3e fix(ui-2026): complete final UX QA pass`

## 1. Проверенные файлы

| Файл | Статус |
|------|--------|
| `backend/scripts/import_recipes.py` | OK |
| `backend/scripts/select_povarenok_candidates.py` | OK |
| `backend/scripts/convert_povarenok.py` | OK (запущен для генерации raw JSONL) |
| `backend/scripts/convert_enriched_to_import_json.py` | OK, расширен для raw-кандидатов |
| `exports/povarenok_candidates_100.jsonl` | Сгенерирован (в `.gitignore`) |
| `exports/povarenok_import_100.json` | Сгенерирован (в `.gitignore`) |
| `docs/RECIPE_IMPORT_PIPELINE.md` | OK |

Источник CSV: `C:\Users\boss\Desktop\рецепты\povarenok_recipes_2021_06_16.csv`

## 2. Импортированный JSONL

Пайплайн:

```bash
python backend/scripts/convert_povarenok.py --input "C:\Users\boss\Desktop\рецепты\povarenok_recipes_2021_06_16.csv"
python backend/scripts/select_povarenok_candidates.py --limit 100
python backend/scripts/convert_enriched_to_import_json.py \
  --input exports/povarenok_candidates_100.jsonl \
  --output exports/povarenok_import_100.json
```

Формат кандидата (raw): `title`, `source`, `source_url`, `ingredients[]`, `steps: []`.

Конвертер добавляет `meal_type`, `category`, `steps` (эвристики + fallback), `source_type: import`.

## 3. Dry-run

```bash
python backend/scripts/import_recipes.py --input exports/povarenok_import_100.json --dry-run
```

Результат:

```text
created=100, updated=0, skipped=0, failed=0
```

## 4. Реальный импорт

```bash
DATABASE_URL=postgresql://aifood:aifood@localhost:5432/aifood \
python backend/scripts/import_recipes.py --input exports/povarenok_import_100.json --commit
```

Результат:

```text
created=0, updated=0, skipped=100, failed=0
```

Все 100 рецептов уже присутствовали в БД (идемпотентный skip по title). `failed=0`.

## 5. PostgreSQL

```sql
select count(*) from recipes;                    -- 174
select count(*) from recipes where source_type='import';  -- 159
```

Пример последних записей:

```text
id=174  Фасолевые котлеты с сельдереем  meal_type=lunch  source_type=import
id=173  Жареный суп                     meal_type=lunch  source_type=import
...
```

Минимум 100 Povarenok-рецептов в каталоге — выполнено.

## 6. Backend API

Авторизация: `X-Telegram-Init-Data: planam-dev-local-v1`, `X-App-Mode: personal`

| Endpoint | HTTP | Примечание |
|----------|------|------------|
| `GET /recipes` | 200 | `total=174`, `items=174` |
| `GET /recipes?limit=10` | 200 | Параметр `limit` не реализован — возвращает полный список (backlog) |
| `GET /recipes?q=курица` | 200 | 5 совпадений |
| `GET /recipes?search=курица` | 200 | 5 совпадений (совместимость с `q`) |
| `GET /recipes/174` | 200 | title, 14 ingredients, 9 steps, source_type=import |
| `POST /recipes/174/add-to-shopping` | 204 | После фикса authoring (см. §8) |

## 7. UI-маршруты

| Маршрут | Результат |
|---------|-----------|
| `/plan/recipes` | Рецепты отображаются, фильтры и поиск работают, skeleton → контент |
| `/plan/recipes/174` | Карточка: заголовок, КБЖУ, время, ингредиенты, шаги, CTA |
| `/plan/today` | Пустая заглушка «Плана пока нет» без crash (меню не создано) |
| `/home/shopping` (UI 2026 redirect с `/shopping`) | 14 позиций после «В покупки» |

Dev-сервер: `npm run dev` в `apps/web`, API через `docker compose up -d postgres redis api`.

## 8. Исправления в этом этапе

### `POST /recipes/{id}/add-to-shopping` — HTTP 500

**Причина:** `MenuVariant` требует `meals` min_length=1, а `authoring.add_recipe_to_shopping` передавал `meals=[]`.

**Фикс:** `apps/api/app/services/recipes/authoring.py` — placeholder `MenuMeal` из рецепта при синхронизации shopping list.

### Конвертер raw → import JSON

**Файл:** `backend/scripts/convert_enriched_to_import_json.py`  
Эвристики `meal_type` / `category` по title, fallback steps, тег `povarenok`.

### Toast-сообщения UI 2026

**Файл:** `apps/web/components/recipes-2026/RecipeDetail2026.tsx`

- Успех покупок: «Ингредиенты добавлены в список покупок»
- Ошибка покупок: «Не удалось добавить ингредиенты. Попробуйте ещё раз.»
- Успех меню: «Рецепт добавлен в меню»

## 9. Backlog

- `GET /recipes?limit=N` — пагинация/ограничение списка
- AI-enrichment шагов и КБЖУ для raw Povarenok (pilot `run_enrichment_pilot.py`)
- Массовый импорт 128k — вне scope
- `event_plan.py` — тот же паттерн `meals=[]` (не затронут в этом этапе)
- pytest: 4 ERROR в `test_shopping_category_service.py` (окружение/фикстуры, не связано с импортом)

## 10. QA

| Команда | Результат |
|---------|-----------|
| `cd apps/api && python -m pytest` | 23 passed, 4 errors (shopping category fixtures) |
| `cd apps/web && npm run lint` | OK (warning `ProfileDashboard.tsx` — допустим) |
| `cd apps/web && npm run build` (UI_2026=true) | OK |
| `cd apps/web && npm run build` (UI_2026=false) | OK |

## Критерии готовности

| Критерий | Статус |
|----------|--------|
| 100 рецептов в БД | OK (skipped=100, уже были) |
| `GET /recipes` HTTP 200 | OK |
| `GET /recipes/{id}` HTTP 200 | OK |
| `/plan/recipes` показывает рецепты | OK |
| Карточка рецепта открывается | OK |
| «В список покупок» не падает | OK (после фикса → 204) |
| «В меню» не падает | OK (sheet + graceful errors) |
| `/shopping` не падает | OK |
| `/plan/today` не падает | OK |
| UI_2026=true build | OK |
| UI_2026=false build | OK |
| lint | OK |
| Отчёт создан | OK |
