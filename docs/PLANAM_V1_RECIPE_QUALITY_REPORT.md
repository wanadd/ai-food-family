# PLANAM V1 Recipe Quality Report

**Дата:** 2026-06-03  
**Файл каталога:** `data/planam_v1_recipes.json`  
**Импорт:** `python backend/scripts/import_recipes.py --input data/planam_v1_recipes.json --commit`

---

## Сводные метрики

| Метрика | Значение |
|---------|----------|
| Количество рецептов | **150** |
| Количество ингредиентов (сумма) | **1339** |
| Среднее ингредиентов на рецепт | **8.9** |
| Количество категорий | **4** (main, salad, soup, quick) |
| Количество meal_type | **3** (breakfast, lunch, dinner) |
| Количество фото | **0** |
| Количество без фото | **150** |
| Количество fallback (UI) | **150** |

---

## Распределение по meal_type

| meal_type | Количество |
|-----------|------------|
| dinner | 115 |
| lunch | 21 |
| breakfast | 14 |

---

## Распределение по category

| category | Количество |
|----------|------------|
| main | 71 |
| salad | 45 |
| soup | 22 |
| quick | 12 |

---

## Качество данных

| Критерий | Статус |
|----------|--------|
| Семейные блюда (фильтр Povarenok) | ✅ |
| Обычные продукты | ✅ |
| Без алкоголя | ✅ (отфильтровано) |
| Без зимних заготовок | ✅ (отфильтровано) |
| Без сложной выпечки / десертов | ✅ (отфильтровано) |
| Шаги приготовления | ✅ (3 шага-шаблон на рецепт) |
| source_type | `v1_import` |
| source_url | Povarenok URL на каждый рецепт |
| Калории / БЖУ | ❌ (не в источнике) |
| Фото | ❌ (план в `PLANAM_V1_RECIPE_IMAGE_PLAN.md`) |

---

## Валидация импорта

```text
python backend/scripts/import_recipes.py --input data/planam_v1_recipes.json --dry-run
Summary: created=150, updated=0, skipped=0, failed=0
```

---

## Pipeline

1. `convert_povarenok.py` → `exports/povarenok_planam_raw.jsonl` (80 000 строк)
2. `select_povarenok_candidates.py --limit 150` → `exports/povarenok_candidates_150.jsonl`
3. `build_planam_v1_catalog.py` → `data/planam_v1_recipes.json`
4. `import_recipes.py --commit` → PostgreSQL

Отчёты: `reports/povarenok_conversion_report.md`, `reports/povarenok_candidates_150_report.md`, `reports/planam_v1_catalog_build_report.md`
