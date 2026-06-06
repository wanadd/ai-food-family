# PLANAM Recipes Catalog Audit and Fix

**Дата:** 2026-06-06  
**Симптом:** Каталог показывает «150 рецептов», но пользователь может прокрутить только ~50 карточек.

---

## 1. Причина проблемы

Три независимых лимита, все установлены в 50:

| # | Файл | Строка | Лимит | Описание |
|---|------|--------|-------|----------|
| 1 | `apps/web/lib/recipes/api.ts` | 45 | `DEFAULT_RECIPE_LIST_LIMIT = 50` | Фронт запрашивает только 50 рецептов, если `limit` не передан явно в query |
| 2 | `apps/api/app/routers/recipes.py` | 163 | `le=100, default=50` | API отдаёт максимум 100 и по умолчанию 50 |
| 3 | `apps/api/app/services/recipes/catalog.py` | 178 | `limit: int = 50` | Дефолт сервисной функции |

`RecipeCatalog2026` (`/plan/recipes`) рендерит все пришедшие карточки плоским гридом без дополнительного усечения. Пользователь видел ровно столько рецептов, сколько пришло из API — то есть 50 из 150.

Показатель `total=150` в заголовке был корректным (API считает `total` по всему набору до пагинации), но `items` содержал только 50 записей.

---

## 2. Где находился лимит

### Frontend (`apps/web/lib/recipes/api.ts`)

```ts
// до
const DEFAULT_RECIPE_LIST_LIMIT = 50;

// после
const DEFAULT_RECIPE_LIST_LIMIT = 200;
```

`RecipeCatalog2026` вызывает `fetchRecipes(initData, query)` без явного `limit`. Без этого изменения API всегда получал `limit=50`.

### Backend router (`apps/api/app/routers/recipes.py`)

```python
# до
limit: int = Query(default=50, ge=1, le=100),

# после
limit: int = Query(default=200, ge=1, le=500),
```

Максимальный лимит был 100 — даже явный запрос `limit=200` был бы отклонён валидацией.

### Backend service (`apps/api/app/services/recipes/catalog.py`)

```python
# до
limit: int = 50,

# после
limit: int = 200,
```

Дефолт согласован с роутером.

---

## 3. Что исправлено

| Файл | Изменение |
|------|-----------|
| `apps/web/lib/recipes/api.ts` | `DEFAULT_RECIPE_LIST_LIMIT` 50 → **200** |
| `apps/api/app/routers/recipes.py` | `default=50, le=100` → **`default=200, le=500`** |
| `apps/api/app/services/recipes/catalog.py` | `limit: int = 50` → **`limit: int = 200`** |

Поиск, фильтры, избранное, карточки рецептов, image pipeline не затронуты.

---

## 4. Как проверить

После деплоя:

```bash
# Проверить что API отдаёт 150 рецептов по умолчанию
curl -H "X-Telegram-Init-Data: ..." https://planam.ru/api/recipes | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['total'], len(d['items']))"
# Ожидаемый вывод: 150 150
```

В Telegram Mini App:
1. Открыть **Сегодня → Рецепты**
2. Прокрутить до конца списка
3. Убедиться что карточек 150
4. Проверить фильтры: Завтрак / Обед / Ужин / Перекус
5. Поиск: найти рецепт из начала списка, из середины, из конца

---

## 5. Количество рецептов

| | До | После |
|-|-----|-------|
| Запрашивалось из API | 50 | 200 |
| Отображалось пользователю | ~50 | **150** |
| `total` в заголовке | 150 | 150 |

---

## 6. QA

| Проверка | Результат |
|----------|-----------|
| `pytest` (92 тестов) | ✅ passed |
| `npm run lint` | ✅ warnings only (pre-existing) |
| `npm run build` | ✅ OK |
