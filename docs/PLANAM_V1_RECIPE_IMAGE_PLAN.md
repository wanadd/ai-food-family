# PLANAM V1 Recipe Image Plan

**Дата:** 2026-06-03  
**Каталог:** 150 рецептов  
**Модель:** 1 master → hero / card / thumb (см. [PLANAM_V1_RECIPE_IMAGE_STYLE_SYSTEM.md](./PLANAM_V1_RECIPE_IMAGE_STYLE_SYSTEM.md))

---

## Сводка

| Статус | Количество | Доля |
|--------|------------|------|
| **Ready** | 0 | 0% |
| **Needs Image** | 150 | 100% |
| **Fallback** | 150 | 100% |
| **Generated Pilot** | 0 | 0% (prompts готовы, генерация не запущена) |
| **Needs Manual Review** | 0 | — |

---

## Ready

Рецепты с URL во всех трёх полях или хотя бы `image_url`:

_Пока нет._

---

## Needs Image

Все 150 рецептов. Приоритет:

1. **Pilot 10** — `data/planam_v1_image_pilot_batch.json`
2. **Top 50 Hero** — `reports/planam_v1_hero_top50.json`
3. Остальные 100 каталога

---

## Fallback

UI (`MealFallbackPlate2026`, `RecipeImage2026`) при отсутствии URL.

Правило: `hero_image_url ?? image_url ?? thumbnail_url ?? fallback`

---

## Generated Pilot

| # | title | status |
|---|-------|--------|
| 1–10 | см. [PLANAM_V1_RECIPE_IMAGE_AI_PILOT.md](./PLANAM_V1_RECIPE_IMAGE_AI_PILOT.md) | `planned` |

После генерации: обновить статус в pilot JSON → `generated_draft` / `approved` / `final_ready`.

---

## Needs Manual Review

Рецепты, где master **не кропается** в hero без потери блюда.

_Пока нет._ Помечать при запуске `process_recipe_images.py` вручную.

---

## Поля БД

| Поле | Файл | Назначение |
|------|------|------------|
| `hero_image_url` | `hero.webp` | Главная, Сегодня |
| `image_url` | `card_800.webp` | Каталог, карточка |
| `thumbnail_url` | `thumb_400.webp` | Превью, replace flow |

---

## Скрипты

| Скрипт | Команда |
|--------|---------|
| Prompts | `python backend/scripts/build_recipe_image_prompts.py --pilot 10` |
| Process | `python backend/scripts/process_recipe_images.py --master ... --recipe-id N` |
| Apply | `python backend/scripts/apply_recipe_images.py --dry-run` |

---

## Следующие шаги

1. Pilot 10 — AI master only
2. `process_recipe_images.py` на каждый master
3. `apply_recipe_images.py --commit`
4. Решение по бюджету: Top 50 vs 150 ([PLANAM_V1_RECIPE_IMAGE_AI_BUDGET.md](./PLANAM_V1_RECIPE_IMAGE_AI_BUDGET.md))
