# Sprint 5 — Completion Report (Recipe Experience 2026)

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Спринт:** Recipe Experience 2026 — каталог, карточка, меню, избранное, медиа

---

## Executive summary

Реализован **полноценный опыт работы с рецептами** при `NEXT_PUBLIC_PLANAM_UI_2026=true`: каталог на `/plan/recipes`, immersive-карточка на `/plan/recipes/[id]`, добавление и замена блюда через **BottomSheet2026** (без отдельных страниц), избранное через существующий API, медиа по PLANAM Recipe Media Architecture с fallback. Legacy `/menu/recipes` и `/recipes/[id]` **не изменялись**.

---

## Маршруты

| Маршрут | Flag off | Flag on |
|---------|----------|---------|
| `/plan/recipes` | redirect / legacy map → `/menu/recipes` | `RecipeCatalog2026` |
| `/plan/recipes/[id]` | — (2026 only) | `RecipeDetail2026` (immersive, без старого modal) |

**Не используется:** legacy `RecipeDetailModal` на `/recipes/[id]` для 2026-пути.

**Shell:** на `/plan/recipes/[id]` скрыт `ShellHeader2026` (hero edge-to-edge).

**Заголовок детали:** `getScreenTitle2026` — regex `/^\/plan\/recipes\/\d+/` → «Рецепт».

**Миграция (opt-in redirects):** `/menu/recipes` → `/plan/recipes` в `route-migration-2026.ts`.

---

## Части спринта (чеклист)

| # | Требование | Статус |
|---|------------|--------|
| 1 | Каталог 2-col grid: фото, название, время, ккал, метки | ✅ `RecipeCatalog2026` + `RecipeGridCard2026` |
| 2 | Карточка рецепта: hero, КБЖУ, время, сложность, ингредиенты, шаги | ✅ `RecipeDetail2026` |
| 3 | Добавить в меню — bottom sheet: день → слот → подтверждение | ✅ `MenuSlotSheet2026` mode=`add` |
| 4 | Замена блюда — bottom sheet, существующая логика | ✅ `assignRecipeToMenuSlot` + `addRecipeToMenu` / `selectMenu` |
| 5 | Избранное | ✅ `POST /recipes/{id}/favorite` |
| 6 | Photo: hero 16:9, grid 1:1, thumb 4:3 + fallback | ✅ `recipe-media.ts` + `RecipeImage2026` |
| 7 | Empty states | ✅ `EmptyState2026` (пустой каталог, поиск, избранное, категория) |
| 8 | Loading — skeleton, без спиннеров | ✅ `Skeleton2026` |
| 9 | Dark mode | ✅ токены `pa-*`, `dark:` на карточках и sheet |
| 10 | Производительность | ✅ `sizes`, CDN `w`/`webp`, `unoptimized` Image |

---

## Новые компоненты

| Компонент | Назначение |
|-----------|------------|
| `RecipeCatalog2026` | Поиск, chips (приём / избранное), 2-col grid, empty/loading |
| `RecipeGridCard2026` | Карточка каталога + toggle избранного |
| `RecipeDetail2026` | Immersive detail, CTA «В меню» / «Заменить» / ★ |
| `RecipeImage2026` | `next/image` + `MealFallbackPlate2026` |
| `MenuSlotSheet2026` | Общий flow: день → meal → confirm (`add` \| `replace`) |

### Lib

| Файл | Назначение |
|------|------------|
| `lib/recipes/recipe-media.ts` | Варианты `grid` / `hero` / `thumb`, aspect, sizes, CDN optimize |
| `lib/recipes/menu-from-recipe.ts` | `recipeToMenuMeal`, `assignRecipeToMenuSlot` |

Barrel: `components/recipes-2026/index.ts`.

---

## API

| Endpoint | Использование |
|----------|----------------|
| `GET /recipes` | Каталог (`q`, `meal_type`, `favorites_only`) |
| `GET /recipes/filters` | Опционально (chips из `CATALOG_MEAL_FILTERS` на клиенте) |
| `GET /recipes/{id}` | Деталь рецепта |
| `POST /recipes/{id}/favorite` | Избранное (каталог + деталь) |
| `GET /menus/selected` (via `fetchSelectedMenu`) | Дни/слоты для sheet |
| `POST` add recipe to menu (`addRecipeToMenu`) | Однодневное меню / replace index |
| `POST /menus/select` | Многодневное меню после client-side merge слота |

### Backend (минимальное расширение, без новой миграции в спринте)

| Изменение | Файл |
|-----------|------|
| `image_url` на `RecipeSummary` | `apps/api/app/schemas/recipe.py` |
| Маппинг `recipe.image_url` | `apps/api/app/services/recipes/mapper.py` |

Поле `image_url` уже есть в модели `recipes` (миграция колонки ранее).

---

## image_url и fallback

| Слой | Поведение |
|------|-----------|
| API | `RecipeSummary` / `RecipeDetail` → `image_url?: string \| null` |
| Web types | `apps/web/lib/recipes/types.ts` |
| Optimize | `optimizeRecipeImageUrl`: для `cdn.planam` — `w`, `fm=webp`, `q=80` по варианту |
| Отображение | `hasRecipeImage` → иначе `MealFallbackPlate2026` по `meal_type` |
| Next Image | `unoptimized` (remote без whitelist в `next.config`), `sizes` по варианту |

**Варианты медиа (PLANAM_RECIPE_MEDIA_ARCHITECTURE):**

| Variant | Aspect | Width hint |
|---------|--------|------------|
| `grid` | 1:1 | 400px |
| `hero` | 16:9 (`aspect-video`) | 1200px |
| `thumb` | 4:3 | 400px |

`thumb` зарезервирован в lib; в Sprint 5 основной UI — `grid` + `hero`.

---

## Добавить / заменить в меню

Flow **не отдельная страница** — `BottomSheet2026`:

1. Выбор дня (`getMenuDays`)
2. Выбор приёма (список `mealsForDayIndex`)
3. Подтверждение

**Бизнес-логика (без новых backend-правил):**

- `assignRecipeToMenuSlot` → для короткого меню `addRecipeToMenu` + `selectMenu`; для недели — patch `days` + `selectMenu`
- После успеха: `invalidateCache` (`selected-menu`, `menu-overview`, `shopping-list`), redirect `/plan/today`

**Замена vs AI `replaceDish`:** в 2026 UI «Заменить» = **подстановка выбранного рецепта в слот плана** (тот же путь, что add с `replace_meal_index` / overwrite meal). Отдельный AI replace flow **не подключался** — по требованию переиспользовать существующую логику слота.

---

## Избранное

- API: `toggleRecipeFavorite` — уже в `lib/recipes/api.ts`
- Каталог: chip «Избранное» + `favorites_only=true`; при снятии звезды — удаление из списка
- Деталь: кнопка ★/☆
- Empty: «Пока нет избранных»

---

## Изменённые файлы (основные)

```
apps/web/app/plan/recipes/page.tsx
apps/web/app/plan/recipes/[id]/page.tsx
apps/web/components/recipes-2026/*
apps/web/lib/recipes/recipe-media.ts
apps/web/lib/recipes/menu-from-recipe.ts
apps/web/lib/recipes/types.ts
apps/web/lib/navigation/nav-config-2026.ts
apps/web/components/planam-2026/layout/ShellHeader2026.tsx
apps/api/app/schemas/recipe.py
apps/api/app/services/recipes/mapper.py
docs/SPRINT_5_COMPLETION_REPORT.md
```

---

## UI / DS

- `Skeleton2026`, `EmptyState2026`, `Button2026`, `Card2026`, `BottomSheet2026`
- Sticky search bar в каталоге (`bg-pa-canvas/95`, backdrop)
- Immersive detail: back link поверх hero, `pb-28` под bottom nav

---

## QA

| Проверка | Результат |
|----------|-----------|
| `npx tsc --noEmit` (apps/web) | ✅ |
| `npm run lint` | ✅ (pre-existing warning в `ProfileDashboard.tsx`) |
| `npm run build` | ✅ |

### Ручной сценарий

1. `NEXT_PUBLIC_PLANAM_UI_2026=true`
2. Открыть **План → Рецепты** (`/plan/recipes`)
3. Поиск, фильтр приёма, избранное
4. Карточка → `/plan/recipes/{id}` — hero, КБЖУ, шаги
5. «В меню» / «Заменить» — sheet, день, слот, confirm → `/plan/today`
6. Light/Dark — карточки, sheet, fallback plate
7. Рецепт без `image_url` — fallback, без broken image

---

## Производительность

| Мера | Деталь |
|------|--------|
| Не грузить full-res на grid | `w=400` на CDN, `sizes="(max-width: 512px) 50vw, 200px"` |
| Hero cap | `max-h-[40vh]`, hero width 1200 |
| `unoptimized` | Избегаем Next optimizer на внешних URL в TMA |
| Skeleton вместо spinner | Каталог 6× rect 1:1, деталь hero + text |

**Риск TMA:** очень длинные URL без CDN — отдаются as-is; при массовом каталоге без `image_url` только fallback (лёгкий).

---

## Риски

| Риск | Митигация |
|------|-----------|
| Нет выбранного меню | Sheet показывает «Сначала создайте меню» |
| `image_url` пустой у большинства рецептов | Fallback plate по `meal_type` |
| Remote images не в `next.config` domains | `unoptimized` + прямой src |
| «Заменить» ≠ AI swap | Документировано: slot assign, не `replaceDish` |
| Redirect migration выключен по умолчанию | Старые URL `/menu/recipes` работают до opt-in |
| Деталь: header скрыт, bottom nav остаётся | Back на hero; при необходимости Sprint 6 — hide nav на immersive |

---

## Готовность к Sprint 6 (Shopping + Pantry + Meal Outcome)

| Готово | Задача Sprint 6 |
|--------|-----------------|
| ✅ Recipe catalog + detail + favorites | Pantry-driven recipes (`from_pantry` уже в API query) |
| ✅ Menu slot assignment | Meal outcome после готовки |
| ✅ Cache invalidation shopping-list | Shopping list UX 2026 |
| ✅ `image_url` pipeline | Shopping / pantry cards с тем же `RecipeImage2026` |
| ⏳ `/plan/shopping`, `/home/pantry` stubs | Полные экраны Sprint 6 |
| ⏳ Thumb 4:3 в списках покупок | Вариант `thumb` в media lib готов |

---

## Критерии готовности Sprint 5

| Критерий | ✓ |
|----------|---|
| Смотреть каталог рецептов | ✅ |
| Красивые карточки рецептов | ✅ immersive detail |
| Видеть фотографии (+ fallback) | ✅ |
| Добавлять рецепт в меню | ✅ bottom sheet |
| Заменять блюда | ✅ slot replace |
| Light/Dark | ✅ |
| Только при UI_2026 flag | ✅ `requirePlanamUi2026OrRedirect` |
| Legacy recipes без поломки | ✅ |

---

*Следующий спринт: Shopping + Pantry + Meal Outcome.*
