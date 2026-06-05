# PLANAM Recipe Catalog Quality v1 — Report

Дата: 2026-06-05  
Ветка: `sprint-0/planam-2026-foundation`  
Базовый коммит: `ea5fb00 feat(recipes): import first recipe batch and connect UI`

## 1. Что исправлено

### GET `/recipes` — пагинация

- Параметры `limit` (default **50**, max **100**) и `offset` (default **0**)
- `q` и `search` по-прежнему совместимы; при обоих используется **`q`**
- Ответ: `{ items, total }` — `total` = полное число после фильтров, `items` = страница

### Поиск

- По `title`, `original_title`, `normalized_title`, `description`
- По именам ингредиентов (`recipe_ingredients.name`)

### Нормализация названий (без потери оригинала)

Миграция в `database_migrations.py`:

- `original_title` — исходник (`= title` для существующих)
- `normalized_title` — для поиска и дублей
- `display_title` — опционально для каталога

Утилита: `apps/api/app/services/recipes/title_normalize.py`  
Импортёр и аудит обновляют поля при записи / `--fix-titles`.

### meal_type

- Каталожный минимум: `breakfast`, `lunch`, `dinner`, `snack`
- Расширенные типы (dessert, drink, …) маппятся в snack при импорте
- Аудит `--fix-meal-types` привёл существующие записи к 4 типам

### Backend tests

- `test_shopping_category_service.py` — стандартные импорты + создание `User`/`Family` таблиц (исправлены 4 ERROR при полном прогоне)
- `backend/pytest.ini` — `cd backend && python -m pytest` находит `apps/api/tests`
- Новый тест пагинации в `test_recipes_catalog.py`

### UI

- `fetchRecipes` отправляет `limit=50` по умолчанию
- Карточки используют `display_title ?? title`
- `original_title` в API только в detail и только если отличается от показываемого title

### Аудит каталога

Скрипт: `backend/scripts/audit_recipe_catalog.py`  
Отчёт: `reports/recipe_catalog_quality.md` (174 рецепта)

## 2. Результат `/recipes?limit=10`

```text
HTTP 200
items=10
total=174
```

## 3. Результат поиска

| Запрос | items | total |
|--------|-------|-------|
| `?q=курица` | 9 | 9 |
| `?search=курица` | 9 | 9 |
| `?q=суп` | 19 | 19 |
| `?q=котлеты` | 8 | 8 |

## 4. pytest

```bash
cd backend
python -m pytest
```

```text
28 passed in ~10s
```

## 5. Аудит каталога (174 рецепта)

Основные находки (`reports/recipe_catalog_quality.md`):

| Проблема | Количество |
|----------|------------|
| Без ингредиентов (legacy seed) | 15 |
| Без шагов (legacy seed) | 15 |
| Мало ингредиентов (<3) | 74 |
| Алкоголь-related в названии | 3 |
| Десерт не family-priority | 1 |
| Заготовки/маринады | 1 |
| Дубли normalized title | 0 |
| Invalid meal_type / source_type | 0 |

После `--fix-titles --fix-meal-types`: все `original_title` и `normalized_title` заполнены, meal_type только из 4 допустимых.

## 6. QA frontend

| Команда | Результат |
|---------|-----------|
| `npm run lint` | OK (warning ProfileDashboard — допустим) |
| `npm run build` (UI_2026=true) | OK |
| `npm run build` (UI_2026=false) | OK |

## 7. Backlog

- Пагинация «загрузить ещё» в UI при `total > limit`
- Обогащение шагов/КБЖУ для 15 legacy seed без структуры
- Снижение false-positive в alcohol-related (например «безалкогольный», «виноград»)
- FTS / релевантность поиска (Recipe Engine v1)
- Исправление `event_plan.py` — тот же паттерн `meals=[]` в MenuVariant

## Критерии готовности

| Критерий | Статус |
|----------|--------|
| `/recipes?limit=10` | OK |
| `/recipes?q=курица` | OK |
| `/recipes?search=курица` | OK |
| backend tests green | OK (28 passed) |
| `reports/recipe_catalog_quality.md` | OK |
| Отчёт создан | OK |
| lint / build | OK |
