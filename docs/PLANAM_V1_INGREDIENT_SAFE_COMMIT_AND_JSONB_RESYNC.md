# PLANAM V1 — Safe-only ingredient commit & recipes.ingredients JSONB resync

**Дата:** 2026-06-07  
**Тип:** production-safe этап (после успешного dry-run нормализации).  
**Без:** изменения названий, `to_taste`, ручных кейсов, UI, images, КБЖУ, photo
prompts.

---

## 1. Зачем нужен safe-only commit

Read-only аудит и dry-run нормализации показали системные проблемы качества
ингредиентов (категория `other` почти везде, грязные единицы). Safe-only commit
приводит `recipe_ingredients` к канону **без потери данных и без рискованных
изменений**, чтобы разблокировать список покупок, КБЖУ и photo prompt pipeline.

Источник истины — таблица `recipe_ingredients`. API читает её первой
(`get_structured_ingredients` отдаёт `ingredient_rows` раньше JSONB), поэтому
карточка и страница рецепта показывают именно нормализованные строки.

## 2. Что меняет `--commit --safe-only`

Только безопасный набор для каждой строки `recipe_ingredients`:

1. `category` → canonical shopping slug (`овощи_зелень`, `мясо_птица`, …);
2. `unit` → canonical unit (алиасы `гр→г`, `ложка→ст.л.`, чистка мусора `...4 ст.л.`);
3. `quantity` → только безопасный числовой реформат (`1,5 → 1.5`).

## 3. Что он принципиально НЕ меняет

- `name` ингредиента (в каталоге 0 вариантов написания — переименовывать нечего);
- `quantity = "по вкусу"/"немного"` (`to_taste`) — остаётся как есть;
- не выдумывает числа для плохих количеств;
- `recipes.ingredients` JSONB (это отдельный скрипт, см. ниже);
- `title`, `steps`, `images`, `source_type`, `is_active`.

Идемпотентность: повторный commit меняет **0 строк**.

## 4. Почему `to_taste` не меняется

`по вкусу` — это не число. Любая автозамена либо выдумает количество (ломает
КБЖУ), либо потеряет смысл. Правильная модель требует отдельных полей
(`quantity_mode`, `is_to_taste`, …) — это следующий этап (см.
`PLANAM_V1_CANONICAL_PRODUCTS.md` → «To taste handling»).

## 5. Почему `needs_review` не меняется

~82 строки — generic (`овощи`, `специи`), неизвестный продукт (`другое`) или
плохое количество. Их нельзя автоматически приводить к продукту/КБЖУ без потери
точности. Они только получают безопасную категорию; остальное — вручную по
отчёту `reports/ingredient_normalization_needs_review.md`.

## 6. Зачем нужен resync `recipes.ingredients` JSONB

`recipes.ingredients` — денормализованная **копия** (legacy fallback для старых
клиентов) в формате `[{"name", "amount"}]`. После safe-only commit строки
`amount` в JSONB могут устареть. `resync_recipe_ingredients_jsonb.py` пересобирает
их из `recipe_ingredients`, **не меняя структуру** (никаких новых полей, `name`
не трогается). Затрагивает только активные `v1_import` рецепты, у которых есть
строки; рецепты без строк и `manual/import` — пропускаются. Идемпотентно.

## 7. Как запустить dry-run

```bash
# нормализация (по умолчанию dry-run, БД не меняется)
python backend/scripts/normalize_recipe_ingredients.py --dry-run

# resync JSONB (по умолчанию dry-run)
python backend/scripts/resync_recipe_ingredients_jsonb.py --dry-run
python backend/scripts/resync_recipe_ingredients_jsonb.py --dry-run --limit 10
```

Отчёты:
- `reports/planam_v1_ingredient_normalization_dry_run.md` + `…normalization.json`
- `reports/ingredient_normalization_needs_review.md`
- `reports/recipe_ingredients_jsonb_resync_dry_run.md` + `.json`

## 8. Как запустить commit (только после backup)

```bash
# 1) ОБЯЗАТЕЛЬНО backup
./scripts/backup.sh

# 2) safe-only commit нормализации
python backend/scripts/normalize_recipe_ingredients.py --commit --safe-only

# 3) safe-only resync JSONB
python backend/scripts/resync_recipe_ingredients_jsonb.py --commit --safe-only
```

Commit-отчёты пишутся в ОТДЕЛЬНЫЕ файлы (dry-run не затирается):
- `reports/planam_v1_ingredient_normalization_commit.md` + `_commit.json`
- `reports/recipe_ingredients_jsonb_resync_commit.md` + `_commit.json`

## 9. Как проверить результат

```bash
# повторный dry-run должен показать резкое снижение изменений
python backend/scripts/normalize_recipe_ingredients.py --dry-run
python backend/scripts/audit_recipe_ingredients.py
```

Ожидаемо после commit:
- `category_changes` → 0 (или близко);
- `unit_changes` → 0 (или близко);
- `quantity_changes` остаётся 0;
- `to_taste` ≈ 200 (не меняем);
- `needs_review` ≈ 82 (не меняем).

Если второй dry-run показывает те же 1322/341 — commit не применился (проверьте
`DATABASE_URL` и backup перед повтором).

## 10. Как откатиться через backup

`scripts/backup.sh` создаёт `backups/<TS>/database.sql` (pg_dump). Откат:

```bash
# внутри сервера, ОСТОРОЖНО (перезаписывает БД)
cat backups/<TS>/database.sql | \
  docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

Альтернатива бэкапу, если `backup.sh` недоступен:

```bash
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U aifood aifood --no-owner --no-acl > backup_$(date +%F_%H-%M).sql
```

> Следующий этап (to_taste-модель, nutrition/shopping/photo readiness) описан в
> [`PLANAM_V1_TO_TASTE_AND_READINESS.md`](./PLANAM_V1_TO_TASTE_AND_READINESS.md).

## 11. Что делать следующим этапом

1. `to_taste` модель (отдельная миграция с полями `quantity_mode` и т.д.).
2. Ручной разбор `needs_review` по отчёту.
3. Shopping-list grouping на основе canonical category.
4. КБЖУ по числовым/канонично-единичным строкам.
5. Photo prompt pipeline (visible ingredients из отчёта readiness).

## Риски

- Низкий: safe-only commit детерминирован, идемпотентен, не трогает name/images/UI.
- JSONB resync только пересобирает legacy-копию из source of truth той же формы.
- Главный риск — отсутствие backup. Поэтому commit запрещён без backup.
