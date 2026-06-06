# PLANAM V1 Recipe Image Plan

**Дата:** 2026-06-03  
**Каталог:** `data/planam_v1_recipes.json` (150 рецептов)  
**Источник данных:** Povarenok CSV → pipeline (без URL фото в исходнике)

---

## Сводка

| Статус | Количество | Доля |
|--------|------------|------|
| **Ready** (есть фото) | 0 | 0% |
| **Needs Image** (запланировано, URL пустой) | 150 | 100% |
| **Fallback** (UI без фото) | 150 | 100% |

Поля модели:

| Поле | Статус в V1 |
|------|-------------|
| `image_url` | Колонка + импорт; все `null` |
| `hero_image_url` | Миграция + API + импорт; все `null` |
| `thumbnail_url` | Миграция + API + импорт; все `null` |

Frontend (`resolveRecipeImageUrl`) и Hero (`MealFallbackPlate2026`) готовы: при `null` показывается fallback-тарелка по `meal_type`.

---

## Ready

Рецепты с хотя бы одним из `image_url`, `hero_image_url`, `thumbnail_url`:

_Пока нет._

---

## Needs Image

Все 150 рецептов V1 требуют фото до Visual Polish. Приоритет — [Top 50 Hero Recipes](PLANAM_V1_RECIPE_FOUNDATION_REPORT.md#block-h-top-50-hero-recipes).

Целевая схема URL (см. `PLANAM_RECIPE_MEDIA_ARCHITECTURE.md`):

```text
https://cdn.planam.ru/recipes/{recipe_id}/hero.jpg
https://cdn.planam.ru/recipes/{recipe_id}/card_800.webp
https://cdn.planam.ru/recipes/{recipe_id}/thumb_400.webp
```

До CDN: одно поле `image_url` как master; `hero_image_url` / `thumbnail_url` — опционально при batch-импорте.

---

## Fallback

Пока фото нет, UI использует `MealFallbackPlate2026` (Hero, карточки каталога, деталь рецепта).

| # | Рецепт | meal_type | category |
|---|--------|-----------|----------|
| 1 | Салат "Баклажанчик" | dinner | salad |
| 2 | Куриные котлеты с картофельным пюре в духовке | dinner | main |
| 3 | Рыба «Красное и белое» | dinner | main |
| 4 | Салат "Винегретная фантазия" | dinner | salad |
| 5 | Гречка с грибами портабелла или шампиньонами | dinner | main |
| 6 | Куриный суп с домашней лапшой | lunch | soup |
| 7 | Котлеты с картофелем | dinner | main |
| 8 | Салат овощной "По-гречески" | dinner | salad |
| 9 | Мацовая запеканка с грибами | dinner | main |
| 10 | Запеканка из творога со сметаной | dinner | main |

_Полный список: 150 рецептов в `data/planam_v1_recipes.json`; все в статусе Fallback._

---

## Следующие шаги (до Visual Polish)

1. Batch-назначение `image_url` для Top 50 Hero.
2. CDN или object storage + resize convention.
3. Опционально: AI/stock pipeline без изменения контракта API.
