# Sprint 7 — Completion Report (План 2026)

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Спринт:** Plan Today · Timeline · Meal Card · Generate · Replace · Shopping · Home · Bot · Nav

**Эталоны:** [`PLANAM_UX_UI_2026_MASTER_SPEC.md`](PLANAM_UX_UI_2026_MASTER_SPEC.md) · [`PLANAM_VISUAL_MOCKUPS_2026.md`](PLANAM_VISUAL_MOCKUPS_2026.md) · [`SPRINT_0_6_AUDIT.md`](SPRINT_0_6_AUDIT.md) · [`SPRINT_6_COMPLETION_REPORT.md`](SPRINT_6_COMPLETION_REPORT.md)

**Условие:** `NEXT_PUBLIC_PLANAM_UI_2026=true`. Опциональная миграция URL: `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=true` (`route-migration-2026.ts`).

---

## Executive summary

Раздел **План** при включённом флаге 2026 закрывает полный цикл питания без обязательного возврата в legacy UI: просмотр дня (`/plan/today`), неделя (`/plan`), генерация (`/plan/generate`), каталог и деталь рецепта (`/plan/recipes`, `/plan/recipes/[id]`), AI-замена блюда, добавление в покупки, meal outcome с плана. Legacy `/menu/current` и `/menu/generate` редиректят на 2026-маршруты; Telegram Bot «Моё меню» / «Создать меню» ведут на `/plan/today` и `/plan/generate`.

---

## Части спринта

| # | Требование | Статус | Реализация |
|---|------------|--------|------------|
| 1 | `/plan/today` — главный экран, реальные данные | ✅ | `PlanToday2026` + `fetchSelectedMenu` + `fetchMenuOverview` |
| 2 | Timeline дня (Утро / День / Вечер / Перекусы) + фото | ✅ | `plan-today.ts` → `PlanTimelineSection2026` |
| 3 | Meal card: фото, название, время, ккал, статус; cook / replace / recipe | ✅ | `PlanMealCard2026` |
| 4 | `/plan/generate` — wizard 2026, без аккордеонов | ✅ | `PlanGenerate2026` (chips + variant pick) |
| 5 | Replace — `POST /menus/replace-dish`, не slot assign | ✅ | `ReplaceDishSheet2026`; gap: UI hint |
| 6 | Add to shopping — рецепт, план, карточка дня | ✅ | `add-to-shopping.ts`, `addRecipeToShopping` на detail |
| 7 | Home Hero / Recipe Rail / Next Action → Plan 2026 | ✅ | `redirect-path-2026.ts`, `recipeDetailPath`, `PLAN_PATHS` |
| 8 | Bot «Моё меню» / «Создать меню» | ✅ | `bot_menu.py` → `/plan/today`, `/plan/generate` |
| 9 | Nav `/plan`, `/plan/today`, `/plan/recipes` без заглушек | ✅ | `PlanWeek2026`, `PlanToday2026`, `RecipeCatalog2026` |

---

## Маршруты План (flag on)

| Маршрут | Экран | Legacy (flag off / без редиректа) |
|---------|--------|-----------------------------------|
| `/plan/today` | Сегодня: timeline + day picker + sheets | `/menu/current` → redirect при flag on |
| `/plan` | Неделя: дни меню → today | `/menu` (`MenuHub`) |
| `/plan/generate` | Wizard генерации | `/menu/generate` (`MenuPlanner`) |
| `/plan/recipes` | Каталог 2026 | `/menu/recipes` |
| `/plan/recipes/[id]` | Деталь 2026 | `/recipes/[id]` |

**Не в scope Sprint 7 (всё ещё legacy или отсутствуют):** `/plan/favorites`, `/plan/collections` (в migration map, страниц нет), `/menu/settings`, `/menu` hub как единый вход без флага.

---

## Новые артефакты

### Components (`components/plan-2026/`)

| Компонент | Назначение |
|-----------|------------|
| `PlanToday2026` | День: overview images, checkin status, timeline, replace/outcome query params |
| `PlanTimelineSection2026` | Секции Утро / День / Вечер / Перекусы |
| `PlanMealCard2026` | Карточка блюда + Приготовил / Заменить / Рецепт / В покупки |
| `PlanGenerate2026` | Wizard: дни, цель, режим, запасы → generate → select |
| `PlanWeek2026` | Список дней недели → `/plan/today?day=` |
| `ReplaceDishSheet2026` | AI replace + AMS confirm |

Barrel: `components/plan-2026/index.ts`.

### Lib (`lib/plan/`)

| Файл | Назначение |
|------|------------|
| `plan-paths.ts` | `PLAN_PATHS`, `resolvePlanPath`, `recipeDetailPath` |
| `plan-today.ts` | Timeline slots, `enrichMealsForDay`, `groupByTimeline`, статусы |
| `add-to-shopping.ts` | Обёртка `addMealIngredientsToShopping` по `MenuMeal` |

### Расширения существующих

| Файл | Изменение |
|------|-----------|
| `MealOutcomeSheet2026` | `dayIndex`, `plannedDate`, `preselectedMealIndex` для плана |
| `redirect-path-2026.ts` | `meal_outcome` → `/plan/today?outcome=1`, `generate_menu` → `/plan/generate` |
| `RecipeRail2026` | `recipeDetailPath`, CTA → `PLAN_PATHS.generate` |
| `RecipeDetail2026` | Replace через `ReplaceDishSheet2026`; покупки через `addRecipeToShopping` |
| `nav-config-2026.ts` | Таб План → `/plan/today` |
| `menu/current/page.tsx`, `menu/generate/page.tsx` | Redirect при UI 2026 |

---

## API (существующие endpoint)

| Endpoint | Использование в План 2026 |
|----------|-------------------------|
| `GET /menus/selected` | Today, week, generate post-select, replace, outcome, recipe replace context |
| `GET /menus/overview` | Фото блюд (`image_url`), статусы на карточках |
| `POST /menus/generate` | `PlanGenerate2026`, onboarding reuse payload builder |
| `POST /menus/select` | После выбора варианта меню |
| `POST /menus/replace-dish` | `ReplaceDishSheet2026` (+ `mergeReplaceResult`) |
| `POST /meal-checkins` | `MealOutcomeSheet2026` с `/plan/today?outcome=1` |
| `POST` add recipe to shopping (client: `addRecipeToShopping`) | Detail + meal card (по `recipe_id`) |
| `GET /recipes/{id}` | `/plan/recipes/[id]` |
| `GET /nutrition-profile`, `GET /pantry/me` | Префилл generate wizard |

Новых backend endpoint в Sprint 7 не добавлялось.

---

## Потоки пользователя (критерии готовности)

| Критерий | Путь 2026 |
|----------|-----------|
| 1. Создать меню | `/plan/generate` или Home CTA → wizard → `selectMenu` → `/plan/today` |
| 2. Посмотреть меню | `/plan/today`, `/plan` (неделя) |
| 3. Открыть рецепт | Карточка → `/plan/recipes/[id]` |
| 4. Заменить блюдо | «Заменить» → `ReplaceDishSheet2026` → `replaceDish` |
| 5. Добавить в покупки | Карточка дня / деталь рецепта |
| 6. Полный цикл без legacy | При `UI_2026=true` и редиректах — да; без флага остаётся `MenuHub` / `MenuPlanner` |

---

## Что осталось от legacy в разделе План

| Элемент | Статус |
|---------|--------|
| `MenuCurrentView`, `MenuPlanner`, `MenuHub` | В репозитории; не рендерятся при flag on + redirect с `/menu/current`, `/menu/generate` |
| `MenuSlotSheet2026` | **Только «В меню»** (slot assign) — не replace |
| `/menu/*` (favorites, collections, settings) | Без 2026-страниц; migration map указывает `/plan/favorites` — **не реализовано** |
| `/recipes/[id]` (legacy) | При flag off; при flag on rail/detail используют `/plan/recipes/[id]` |
| Backend `redirect_path` в overview | Может отдавать `/menu/...`; клиент нормализует через `resolveHomeRedirectPath` |

---

## Gaps и отклонения от Master Spec

| Gap | Детали | Приоритет |
|-----|--------|-----------|
| **Replace hint / reason** | API принимает `hint`; UI не собирает пожелание пользователя (зафиксировано в `ReplaceDishSheet2026`) | Средний |
| **Неделя без фото** | `PlanWeek2026` не мержит `overview` — `image_url: null` | Низкий |
| **Favorites / Collections 2026** | Маршруты в migration, экранов нет | Sprint 8+ |
| **Shopping add item sheet** | Как в Sprint 6 — только toggle/sync | Отдельно |
| **Wellness** | `/wellness` — `RoutePlaceholder2026` | Sprint 8+ |
| **Полный отказ от legacy кода** | Компоненты `/components/menu/*` не удалены (безопасный rollback) | По решению продукта |

---

## Интеграции

### Home 2026

| Элемент | Поведение |
|---------|-----------|
| `resolveHomeRedirectPath` | `/menu/generate` → `/plan/generate`, `/menu/current` → `/plan/today` |
| `meal_outcome` | `/plan/today?outcome=1` (sheet на плане) |
| `generate_menu` / `open_today` | `/plan/generate`, `/plan/today` |
| `RecipeRail2026` | Клик → `recipeDetailPath` или `PLAN_PATHS.today` |

### Telegram Bot

| Кнопка | URL |
|--------|-----|
| Моё меню | `/plan/today` |
| Создать меню | `/plan/generate` |

*(Предполагается, что Web App открывается с `UI_2026=true` в окружении.)*

### Meal outcome

- Home: query `?meal_outcome=1` по-прежнему может открывать sheet на Home (`Home2026`).
- План: `?outcome=1` на `/plan/today` с `dayIndex` / `preselectedMealIndex` при «Приготовил» с карточки.

---

## QA

| Проверка | Результат |
|----------|-----------|
| `npx tsc --noEmit` (`apps/web`) | ✅ |
| `npm run lint` | ✅ (pre-existing `ProfileDashboard` `<img>` warning) |
| `npm run build` | ✅ |

### Ручной сценарий (рекомендуется)

1. `NEXT_PUBLIC_PLANAM_UI_2026=true`
2. Нет меню → `/plan/generate` → выбор варианта → `/plan/today`
3. Timeline: завтрак / обед / ужин / перекусы с фото или fallback
4. Заменить блюдо → AMS dialog при лимите → обновление списка
5. «В покупки» с карточки и с `/plan/recipes/[id]`
6. Home rail → деталь рецепта; Hero CTA → generate/today
7. Bot deep links → today / generate
8. `?outcome=1` на plan/today после «Приготовил»

---

## Готовность к Wellness (Sprint 8+)

| Готово | Комментарий |
|--------|-------------|
| ✅ План как SSOT питания | Today + recipes + generate связаны с теми же menu APIs |
| ✅ Deep links из Home/Bot | Не ломают IA нижней навигации |
| ✅ Meal checkins / leftovers | Outcome sheet переиспользуется; leftovers остаются на Home (Sprint 6) |
| ⏳ Wellness routes | `/wellness`, chat, progress — stubs |
| ⏳ Cross-link Plan → Wellness | Нет CTA «забота о здоровье» на plan screens (mockup-level) |

**Вывод:** План 2026 готов как база для Wellness: данные меню, рецепты и checkins уже на общих API; следующий спринт может строить Заботу на `overview` + профиль без переделки Plan core.

---

## Критерии готовности Sprint 7

| Критерий | ✓ |
|----------|---|
| Создать меню в 2026 UI | ✅ |
| Посмотреть меню (today + week) | ✅ |
| Открыть рецепт | ✅ |
| Заменить блюдо (AI replace) | ✅ |
| Добавить в покупки | ✅ |
| Цикл без обязательного legacy UI при flag on | ✅ |

---

*Следующий фокус: Wellness 2026, `/plan/favorites` & collections, polish replace hint UI, week thumbnails from overview.*
