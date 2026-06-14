# PLANAM Menu & Recipe Consistency V4 — Implementation Report (Phase 1)

**Дата:** 2026-06-10  
**Ветка:** `feat/recipe-gold-v3-original-planam-library`

## Сделано в Phase 1

### Задача 1 — единое название (частично)

- Backend: `_meal_from_recipe` и `attach_recipe_images` используют `public_title()` → `name` + `display_title`
- Schema: `MenuMeal.display_title`, `RecipeSummary.full_title`
- Frontend: `menuMealHeading()`, `recipeDetailHeading()` = `display_title` first
- Экраны: MenuTodayV2, PlanWeek2026

### Задача 8 — обзор меню (частично)

- Заголовок «Обзор» вместо «Неделя»
- Nav: «План питания»
- Превью дня: фото, название, тип приёма, ккал
- `pluralRu`: «2 блюда»

### Задача 9 — сегодня (частично)

- Кнопка «Показать итог дня»
- Карточки через `menuMealHeading`

### Задача 10 — каталог (частично)

- Фильтр `category` из API
- Избранное поверх фото
- `pluralRu` для счётчика рецептов
- Scroll restore при возврате из деталки

### Задача 11 — scroll restore (каталог)

- `lib/navigation/scroll-restore.ts` + sessionStorage

### Задача 13 — грамматика

- `lib/i18n/plural-ru.ts` + tests

## Не сделано (Phase 2+)

- `FamilyMenuContext` dataclass (есть только text formatter)
- `MenuGenerationMode` + feature flags
- Отдельные `ai_usage_events` / `am_usage_events`
- Favorites scoring в builder
- Explainable menu variants UI
- Visual contract migration
- Admin AI/AM split UI
- Grid/list toggle в каталоге
- Полный scroll restore на всех экранах

## Изменённые файлы

### Backend
- `apps/api/app/schemas/menu.py`
- `apps/api/app/schemas/recipe.py`
- `apps/api/app/services/menu_recipe_builder.py`
- `apps/api/app/services/menu_catalog_enrichment.py`
- `apps/api/app/services/recipes/mapper.py`
- `apps/api/tests/test_menu_catalog_enrichment.py`

### Frontend
- `apps/web/lib/i18n/plural-ru.ts`, `.test.ts`
- `apps/web/lib/menu/meal-heading.ts`, `types.ts`
- `apps/web/lib/recipes/card-title.ts`, `.test.ts`, `types.ts`
- `apps/web/lib/navigation/nav-config-2026.ts`, `scroll-restore.ts`
- `apps/web/components/plan-2026/PlanWeek2026.tsx`
- `apps/web/components/planam-v2/menu/MenuTodayV2.tsx`
- `apps/web/components/recipes-2026/RecipeGridCard2026.tsx`, `RecipeCatalog2026.tsx`

### Reports
- `reports/menu_recipe_consistency_v4_audit.md`
- `reports/recipe_visual_consistency_audit.md`
- `reports/ai_am_usage_audit.md`
- `reports/menu_recipe_consistency_v4_implementation.md`

## Ручная проверка

1. Меню → Сегодня / Обзор / Деталка рецепта — одно `display_title`
2. Обзор: фото и «2 блюда»
3. Каталог: ☆ на фото; фильтр категории; назад = тот же scroll
4. «Показать итог дня» открывает sheet

## Деплой (только после вашего подтверждения)

```bash
cd /var/www/ai-food-family
git fetch origin
git reset --hard origin/feat/recipe-gold-v3-original-planam-library
docker compose -f docker-compose.prod.yml build api web
docker compose -f docker-compose.prod.yml up -d api web
```

Relay не трогать.
