# PLANAM V1 Recipe Import Pipeline

**Дата:** 2026-06-03  
**Статус:** operational  
**Связанные документы:** [RECIPE_IMPORT_PIPELINE.md](./RECIPE_IMPORT_PIPELINE.md), [PLANAM_V1_RECIPE_FOUNDATION_REPORT.md](./PLANAM_V1_RECIPE_FOUNDATION_REPORT.md)

---

## Цель

Перейти от placeholder/seed рецептов к **PlanAm V1 Recipe Catalog** (100–200 семейных блюд) с единой моделью изображений.

---

## Pipeline (данные)

```text
povarenok_recipes.csv
        ↓
convert_povarenok.py
        ↓
exports/povarenok_planam_raw.jsonl
        ↓
select_povarenok_candidates.py --limit 150
        ↓
exports/povarenok_candidates_150.jsonl
        ↓
build_planam_v1_catalog.py
        ↓
data/planam_v1_recipes.json
        ↓
import_recipes.py --dry-run
import_recipes.py --commit
        ↓
archive_placeholder_recipes.py --commit
```

---

## Pipeline (изображения)

```text
Top 50 Hero list
        ↓
build_recipe_image_prompts.py --pilot 10
        ↓
data/planam_v1_image_pilot_batch.json
        ↓
[AI] 1 master image per recipe (pilot only)
        ↓
process_recipe_images.py --master ... --recipe-id N
        ↓
public/recipe-images/{id}/hero.webp
public/recipe-images/{id}/card_800.webp
public/recipe-images/{id}/thumb_400.webp
        ↓
apply_recipe_images.py --manifest ... --commit
```

**Правило:** одно master image → три crop. Отдельная генерация hero/card/thumb **запрещена**.

---

## Фильтры кандидатов

| Правило | Реализация |
|---------|------------|
| Семейные блюда | `PRIORITY_PATTERNS` в select |
| Без алкоголя / настоек | `ALCOHOL_PATTERNS` |
| Без зимних заготовок | `PRESERVE_PATTERNS` |
| Без сложной выпечки | `COMPLEX_BAKING_PATTERNS` |
| 3–25 ингредиентов | select + build |
| Странные названия | `has_strange_title()` |

---

## Enrichment (`build_planam_v1_catalog.py`)

| Поле | Источник |
|------|----------|
| `title`, `original_title` | Povarenok |
| `normalized_title` | lower + collapse spaces |
| `display_title` | strip decorative quotes |
| `meal_type`, `category` | heuristic from title |
| `steps` | template (tag `steps_generated`) |
| `source_type` | `v1_import` |
| `short_visual_description` | `recipe_image_utils` (image pipeline only) |

---

## Команды

```bash
python backend/scripts/convert_povarenok.py --limit 80000
python backend/scripts/select_povarenok_candidates.py --limit 150 --output exports/povarenok_candidates_150.jsonl
python backend/scripts/build_planam_v1_catalog.py
python backend/scripts/import_recipes.py --input data/planam_v1_recipes.json --dry-run
python backend/scripts/import_recipes.py --input data/planam_v1_recipes.json --commit
python backend/scripts/archive_placeholder_recipes.py --dry-run
```

---

## Gate placeholder seeds

`seed_recipes_if_empty()` в `catalog.py` **не выполняется**, если в БД ≥50 активных рецептов с `source_type=v1_import`.
