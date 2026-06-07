# PLANAM V1 — Nutrition (КБЖУ) + Shopping grouping + Photo prompt pipeline

Этот этап строится поверх нормализованных ингредиентов, `to_taste`-модели и
полей качества (`quantity_mode`, `is_to_taste`, `nutrition_precision`,
`shopping_priority`, `photo_visibility`, …). Он добавляет **фактические данные
КБЖУ**, группировку для shopping list и оценку готовности к photo prompt.

> Безопасность: **не удаляет** рецепты, **не меняет** `name` / `quantity` /
> `unit` / `category`, **не трогает** JSONB, картинки и UI. Dry-run по умолчанию,
> commit — только `--safe-only`, строго идемпотентный.

## Что хранится где

| Данные | Где |
|--------|-----|
| КБЖУ per ingredient / per recipe | **отчёты** (`reports/nutrition_estimate.*`) |
| Группировка shopping list | **отчёты** (`reports/shopping_list_groups.*`) |
| Photo readiness per recipe | **отчёты** (`reports/photo_prompt_readiness.*`) |
| `nutrition_precision` (refined) | БД `recipe_ingredients` (safe-only commit) |
| `shopping_priority` (recomputed) | БД `recipe_ingredients` (safe-only commit) |

КБЖУ-значения **намеренно не пишутся в БД** — никаких новых колонок и схемных
изменений на этом этапе. В БД обновляются только два уже существующих
nullable-поля (`nutrition_precision`, `shopping_priority`).

## Источник истины по нутриентам

`backend/scripts/nutrition_data.py` — чистые данные + функции:

- `NUTRITION_FACTS` — KБЖУ на 100 г (≈171 продукт, покрытие ~93% строк каталога).
- `VOLUME_UNIT_ML`, `DENSITY`, `PIECE_WEIGHTS`, `SPECIAL_UNIT_G` — конвертация
  единиц (г, кг, мл, л, ст.л., ч.л., стакан, шт, зубчик, пучок).
- `grams_for(name, quantity, unit) -> (grams|None, hint)` — никогда не выдумывает
  граммы для `to_taste` / неизвестной единицы / неизвестного штучного веса.
- `compute_row_nutrition(...) -> RowNutrition` — kcal/б/ж/у + `precision`.

Материализованная копия для прозрачности: `data/planam_v1_nutrition_facts.json`
(source of truth остаётся `nutrition_data.py`).

### Правило `nutrition_precision`

| precision | условие |
|-----------|---------|
| `exact` | факты есть + числовое количество + масса/объём (г, кг, мл, л) |
| `estimated` | факты есть + ст.л./ч.л./стакан/шт/зубчик/пучок (через средний вес) |
| `low_confidence` | `to_taste` / generic / единица не конвертируется |
| `unavailable` | нет фактов КБЖУ для продукта |

## Скрипты

| Скрипт | Режим | Назначение |
|--------|-------|------------|
| `calculate_nutrition.py` | read-only | КБЖУ per row + per recipe |
| `generate_shopping_list_groups.py` | read-only | группировка по priority+категории |
| `evaluate_photo_prompt_readiness.py` | read-only | готовность рецепта (≥2 visible) |
| `nutrition_shopping_photo_pipeline.py` | dry-run / commit | объединяет всё + safe-only commit |

### Shopping list grouping

- группировка по `shopping_priority` + `category`;
- `hidden` — скрываются из списка покупок;
- `to_taste` / `low` / `optional` — необязательные (не в основном списке).

### Photo prompt readiness

- считаются ингредиенты с `photo_visibility ∈ {visible, optional}`;
- рецепт **ready**, если видимых **≥ 2**;
- `hidden` / `unsafe` не учитываются.

## Запуск

```bash
# read-only отчёты по отдельности
python backend/scripts/calculate_nutrition.py
python backend/scripts/generate_shopping_list_groups.py
python backend/scripts/evaluate_photo_prompt_readiness.py

# всё вместе, dry-run (по умолчанию, БД не меняется)
python backend/scripts/nutrition_shopping_photo_pipeline.py

# применить безопасные изменения (после backup БД)
python backend/scripts/nutrition_shopping_photo_pipeline.py --commit --safe-only
```

Commit обновляет только `nutrition_precision` и `shopping_priority` и меняет
строки, у которых значение реально отличается. Повторный запуск → **0 изменений**.

## Отчёты

- `reports/nutrition_estimate.md|json`
- `reports/shopping_list_groups.md|json`
- `reports/photo_prompt_readiness.md|json`
- `reports/nutrition_shopping_photo_pipeline_dry_run.md|json`
- `reports/nutrition_shopping_photo_pipeline_commit.md|json`

## Следующие шаги

1. Ручной review продуктов без фактов КБЖУ (`unavailable`) и низких precision.
2. Per-recipe нутриенты → колонки рецепта (отдельный этап, со схемой и UI).
3. Photo prompt builder для рецептов со статусом *ready*.

См. также: [PLANAM_V1_TO_TASTE_AND_READINESS.md](PLANAM_V1_TO_TASTE_AND_READINESS.md),
[PLANAM_V1_CANONICAL_PRODUCTS.md](PLANAM_V1_CANONICAL_PRODUCTS.md).
