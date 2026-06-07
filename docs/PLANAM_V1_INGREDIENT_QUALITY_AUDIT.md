# PLANAM V1 — Ingredient Quality Audit (read-only)

**Дата:** 2026-06-07  
**Режим:** строго **read-only**. Скрипт выполняет только `SELECT`. Никаких
`UPDATE/INSERT/DELETE/ALTER`, миграций, нормализации, генерации изображений или
repair commit. Результат — отчёты в `reports/`.

Цель — измерить реальное качество базы ингредиентов и готовность к будущим
этапам: нормализация, canonical products, shopping-list grouping, КБЖУ и photo
prompt pipeline. Сам этап ничего не чинит.

---

## Где лежат данные

Ингредиенты хранятся в таблице `recipe_ingredients` (`name`, `quantity`,
`unit`, `category`, `is_optional`, `notes`), привязанной к `recipes`. Аудит
берёт строки активных рецептов `source_type = v1_import`.

---

## Что проверяется

| Категория | Как детектируется |
|-----------|-------------------|
| Варианты написания / порядка слов | `normalize_key`: lower + `ё→е` + удаление пунктуации + сортировка токенов. `перец чёрный` = `черный перец` = `Перец Черный` |
| Неоднозначные семейства | `head_noun` ∈ {перец, масло, лук, уксус, мука, сахар, соус, сыр, капуста, фасоль} с >1 названием (разные продукты под одним словом) |
| Слишком общие названия | словарь `GENERIC_NAMES` (овощи, зелень, специи, мясо, рыба, сыр, …) |
| Некорректные количества | пусто, `0`, `по вкусу`, `немного`, `щепотка`, `1 пакетик` и прочее не-число; валидны числа, дроби `1/2`, диапазоны `1-2` |
| Грязные единицы | не из `CANONICAL_UNITS`; таблица `UNIT_ALIASES` даёт предлагаемый canonical (`гр→г`, `ложка→ст.л.`, `пакетик→упаковка`, …) |
| Покрытие категориями | доля строк с `category != other` (готовность shopping grouping) |

`CANONICAL_UNITS` (целевые): `г, кг, мл, л, шт, ст.л., ч.л., стакан, зубчик,
щепотка, упаковка`.

---

## Scorecard (как считается)

Все метрики 0–100%, по множеству **уникальных** названий (без двойного учёта
пересечений) или по строкам:

- **normalization_pct** = `(distinct − variant_names) / distinct` — доля названий без вариантов написания.
- **canonical_products_pct** = `(distinct − (variants ∪ ambiguous ∪ generic)) / distinct` — доля названий, готовых стать canonical product как есть.
- **shopping_grouping_pct** = доля строк с непустой shopping-категорией (`!= other`).
- **nutrition_pct** = доля строк, у которых одновременно: конкретное название (не generic) + валидное число количества + чистая единица.
- **photo_prompt_pct** = доля строк с конкретным (не generic) названием.

Это эвристики аудита, а не правила записи в БД.

---

## Запуск

Локально (из корня репозитория):

```bash
python backend/scripts/audit_recipe_ingredients.py
# при необходимости:
python backend/scripts/audit_recipe_ingredients.py --database-url postgresql://user:pass@host:5432/db
```

В api-контейнере на сервере (read-only):

```bash
docker compose -f docker-compose.prod.yml exec api sh -lc \
  "cd /app && python backend/scripts/audit_recipe_ingredients.py"
```

### Выходные файлы

- `reports/planam_v1_ingredient_quality_report.md` — человекочитаемый отчёт.
- `reports/planam_v1_ingredient_quality.json` — структурированные данные
  (варианты, семейства, generic, bad quantities sample, dirty units, scorecard).

---

## Что НЕ делает этот этап

Не нормализует, не правит ингредиенты/рецепты/покупки, не запускает image
generation и repair commit, не меняет схему БД. Это вход для следующего этапа
(canonical products), который будет отдельной задачей с dry-run и commit.

---

## Тесты

`apps/api/tests/test_recipe_ingredient_audit.py` покрывает чистые функции
(`normalize_key`, `is_generic`, `is_valid_quantity`, `canonical_unit`,
`head_noun`) и агрегатор `analyze` на синтетических данных — без обращения к БД.
