# PLANAM V1 Recipe Quality Report

**Дата:** 2026-06-03  
**Каталог:** `data/planam_v1_recipes.json`  
**Импорт:** `python backend/scripts/import_recipes.py --input data/planam_v1_recipes.json --commit`

---

## Сводные метрики

| Метрика | Значение |
|---------|----------|
| Количество рецептов | **150** |
| Количество ингредиентов (сумма) | **1339** |
| Среднее ингредиентов на рецепт | **8.9** |
| Количество meal_type | **3** (breakfast, lunch, dinner) |
| Количество category | **5** (main, salad, soup, breakfast, quick) |
| С фото (`image_url` / hero / thumb) | **0** |
| Без фото | **150** |
| Fallback (UI) | **150** |
| Top 50 Hero | **50** (`reports/planam_v1_hero_top50.json`) |
| Pilot batch (image) | **10** (`data/planam_v1_image_pilot_batch.json`) |
| `steps_generated` | **150** (100%) |

---

## Распределение meal_type

| meal_type | Количество |
|-----------|------------|
| dinner | 115 |
| lunch | 21 |
| breakfast | 14 |

---

## Распределение category

| category | Количество |
|----------|------------|
| main | 69 |
| salad | 45 |
| soup | 22 |
| breakfast | 12 |
| quick | 2 |

---

## Enrichment quality

| Поле | Покрытие |
|------|----------|
| `title` | 150/150 |
| `original_title` | 150/150 |
| `normalized_title` | 150/150 |
| `display_title` | ~40/150 (где есть декоративные кавычки) |
| `source_type=v1_import` | 150/150 |
| `source_url` | 150/150 |
| `steps_quality=steps_generated` | 150/150 |
| `short_visual_description` | 150/150 (metadata для image pipeline) |

---

## Фильтры качества (select)

| Критерий | Статус |
|----------|--------|
| Семейные блюда | ✅ |
| 3–25 ингредиентов | ✅ |
| Без алкоголя / настоек | ✅ |
| Без зимних заготовок | ✅ |
| Без сложной выпечки | ✅ |
| Без экзотики | ✅ (heuristic) |

---

## Валидация импорта

```bash
python backend/scripts/import_recipes.py --input data/planam_v1_recipes.json --dry-run
# Summary: created=150, failed=0
```

---

## Pipeline

См. [PLANAM_V1_RECIPE_IMPORT_PIPELINE.md](./PLANAM_V1_RECIPE_IMPORT_PIPELINE.md)
