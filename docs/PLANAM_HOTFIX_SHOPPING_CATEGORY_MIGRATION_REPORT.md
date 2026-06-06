# PLANAM Hotfix — Shopping Category Migration

**Дата:** 2026-06-06  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Тип:** production hotfix (conflict-safe data migration)

---

## 1. Причина production outage

API падал на старте при выполнении `migrate_shopping_categories_v1(connection)` в `database_migrations.py`.

### Причина №1 — нарушение unique constraint

Миграция делала прямой:

```sql
UPDATE shopping_categories SET slug = :new_slug WHERE slug = :old_slug
```

На старой production-БД у пользователя уже существовал целевой slug, и UPDATE нарушал partial unique index `uq_shopping_categories_system_user_slug (user_id, slug)`:

```text
duplicate key value violates unique constraint "uq_shopping_categories_system_user_slug"
(user_id, slug)=(36, другое) already exists
(user_id, slug)=(36, быт_уборка) already exists
```

### Причина №2 — некорректный JSONB SQL

В JSONB-блоке использовался:

```sql
to_jsonb(:new_slug::text)
```

SQLAlchemy `text()` трактует `:new_slug` как bind-параметр, и `::text` оставался некорректным, из-за чего PostgreSQL падал:

```text
syntax error at or near ":"
```

### Временное решение на сервере

Вызов `migrate_shopping_categories_v1(connection)` был вручную отключён на сервере, чтобы поднять API. Это временно — данный hotfix возвращает корректную миграцию.

---

## 2. Исправленные файлы

| Файл | Изменение |
|------|-----------|
| `apps/api/app/services/shopping_category_migration.py` | Полностью переписана: conflict-safe, dialect-aware, исправлен JSONB |
| `apps/api/app/services/categories_v1.py` | Дополнена `LEGACY_SLUG_MAP`, `алкоголь → другое` |
| `apps/api/tests/test_shopping_category_migration.py` | Новые тесты (6 сценариев) |
| `docs/PLANAM_HOTFIX_SHOPPING_CATEGORY_MIGRATION_REPORT.md` | Этот отчёт |

`database_migrations.py` — вызов `migrate_shopping_categories_v1(connection)` остаётся активным (был отключён только на сервере); код теперь безопасен.

---

## 3. Как работает новая миграция

Для каждой пары `old_slug → new_slug` (identity-пары пропускаются):

1. **Pantry items** — `UPDATE family_pantry_items SET category` (без unique constraint, безопасно).
2. **Category rows** — 3 шага, conflict-safe:
   - **Шаг 1.** Удалить legacy-строки `old_slug`, если в той же области (`user_id` / `family_id`) уже есть строка с `new_slug`.
   - **Шаг 2.** Схлопнуть дубликаты `old_slug` в одной области, оставив строку с минимальным `id`.
   - **Шаг 3.** Переименовать оставшиеся `old_slug → new_slug` — конфликт уже невозможен.
3. **Shopping list JSONB items** — dialect-aware:
   - PostgreSQL: `jsonb_agg` + `jsonb_set(..., to_jsonb(CAST(:new_slug AS text)))`.
   - SQLite/тесты: построчный Python-трансформер (`json.loads` → замена → `json.dumps`).
4. **Cleanup** — удалить остатки deprecated-слагов.
5. Установить флаг `shopping_categories_v1_migrated` в `app_schema_flags`.

Исправление SQL:

```sql
-- было (падало):
to_jsonb(:new_slug::text)
-- стало:
to_jsonb(CAST(:new_slug AS text))
```

Флаг-таблица использует `DEFAULT CURRENT_TIMESTAMP` (портируемо: PostgreSQL + SQLite), вместо `NOW()`.

---

## 4. Поддержанные legacy slugs

### Обязательная карта

```text
продукты → другое            бытовые → быт_уборка
заморозка → бакалея          дом_и_химия → быт_уборка
сладости → бакалея           хозтовары → быт_уборка
животные → для_питомцев       детское → детские_товары
питомцы → для_питомцев        детские → детские_товары
фрукты → фрукты_ягоды         ребенку → детские_товары
ягоды → фрукты_ягоды          ребёнку → детские_товары
овощи → овощи_зелень          мясо → мясо_птица
зелень → овощи_зелень         птица → мясо_птица
рыба → рыба_морепродукты      морепродукты → рыба_морепродукты
молочное → молочные           молочные_продукты → молочные
крупы → крупы_макароны        макароны → крупы_макароны
хлеб → хлеб_выпечка           выпечка → хлеб_выпечка
специи → специи_соусы         соусы → специи_соусы
масла → специи_соусы
```

### Старые production-категории (безопасное решение)

```text
алкоголь → другое            подарки → другое
аптека → другое              ремонт → другое
одежда_и_обувь → другое       другое_продуктовое → другое
хозтовары → быт_уборка        ребенку → детские_товары
```

Принцип: при сомнении — мигрировать в `другое`, не удалять данные.

---

## 5. Добавленные тесты

`apps/api/tests/test_shopping_category_migration.py`:

| Тест | Проверяет |
|------|-----------|
| `test_rename_when_only_old_slug_present` | Есть только `бытовые` → становится `быт_уборка` |
| `test_collapse_when_old_and_new_slug_coexist` | Есть `бытовые` + `быт_уборка` → остаётся один `быт_уборка`, без падения |
| `test_rerun_is_idempotent_and_safe` | Повторный запуск (со сбросом флага) не падает и не дублирует |
| `test_jsonb_items_category_is_migrated` | `items[].category: бытовые → быт_уборка` |
| `test_pantry_item_category_is_migrated` | Pantry `category: бытовые → быт_уборка` |
| `test_jsonb_sql_uses_cast_not_double_colon_bind` | SQL не содержит `:new_slug::text`, содержит `CAST(:new_slug AS text)` |

Тесты создают unique-индексы `(user_id, slug)` и `(family_id, slug)`, воспроизводя production-constraint.

**QA:** `pytest` — 92 passed; `npm run lint` / `npm run build` — OK.

---

## 6. Почему повторный запуск безопасен

- **Guard-флаг** `shopping_categories_v1_migrated` короткозамыкает повторные запуски.
- Даже без флага каждый SQL-шаг **идемпотентен**:
  - Шаги 1–2 — `DELETE ... WHERE EXISTS` (нет строк → no-op).
  - Шаг 3 — `UPDATE WHERE slug = :old_slug` (0 строк после первого прохода).
  - JSONB/Python — повторная замена не находит `old_slug` (уже заменён).
- Conflict-safe порядок гарантирует отсутствие нарушения unique constraint при любом состоянии БД.

---

## 7. Что сделать на сервере после merge

```bash
git pull origin sprint-0/planam-2026-foundation
docker compose -f docker-compose.prod.yml build --no-cache api
docker compose -f docker-compose.prod.yml up -d api
curl https://planam.ru/api/health
```

После старта API миграция выполнится автоматически (вызов в `ensure_database_schema`), безопасно для текущего состояния production-БД. Ручное отключение вызова на сервере больше не требуется.
