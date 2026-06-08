# P0 UI/UX 2026 Fix Pack — Home, Leftovers, Dead Routes, Hero CTA

Дата: 2026-06-08  
Ветка: `fix/p0-ui-ux-home-leftovers-routes`  
База: `sprint-0/planam-2026-foundation`

---

## 1. Что изменено

### Блок 1 — TodayDishRail на Home

- Новый компонент `TodayDishRail2026` — горизонтальная лента блюд на сегодня.
- Данные из существующего `fetchMenuOverview()` / `enrichTodayMeals()`.
- Пустое состояние → CTA «Собрать меню» → `/plan/generate`.
- Карточки ведут на recipe detail (если `recipe_id`) или `/plan/today?meal=`.

### Блок 2 — Hero rule engine (P0–P4)

- `resolvePlanAmHeroState` перестроен по приоритетам:
  - **P0** `nutrition_profile` — `next_action.id === complete_nutrition` → `/account/nutrition`
  - **P1** `meal` — текущее блюдо, CTA «Открыть рецепт» + «Заменить»
  - **P2** `no_menu` — `/plan/generate`
  - **P3** `pantry_expiry` — `pantry_expiring_preview` (≤3 дн.) или `use_pantry_item` → `/home/leftovers`
  - **P4** `meal_outcome` — `next_action.id === meal_outcome` → `/shopping`
  - **fallback** — shopping / wellness / welcome
- Без новых backend-полей; при отсутствии данных — безопасный fallback.

### Блок 3 — Hero CTA / Plan Today query

- `PlanToday2026` читает `meal`, `recipeId`, `menuItemId`.
- Подсветка карточки (`ring-pa-brand`) + smooth scroll.
- Hero meal CTA ведёт на recipe detail или `/plan/today?meal=` (рабочий scroll).

### Блок 4 — Leftovers навигация

- Маршрут `/home/leftovers` → `Leftovers2026`.
- Home: карточка «Готовить из остатков» + quick action.
- Pantry: CTA «Подобрать рецепт из остатков».
- Bottom nav **не изменён** (5 вкладок).

### Блок 5 — Dead routes

| Маршрут | Поведение |
|---------|-----------|
| `/plan/favorites` | `EmptyState2026` → каталог с `?favorites_only=true` |
| `/plan/collections` | `EmptyState2026` → `/plan/recipes` |
| `/plan/collections/[id]` | redirect → `/plan/collections` |
| `/wellness/progress` | redirect → `/wellness` |

### Прочее

- `PLANAM_ROUTES` расширен: `homeLeftovers`, `planFavorites`, `planCollections`, `wellnessProgress`.
- `resolveHomeRedirectPath`: `complete_nutrition` → `/account/nutrition` (canonical 2026).

---

## 2. Затронутые файлы

**Новые:**

- `apps/web/components/home-2026/TodayDishRail2026.tsx`
- `apps/web/app/home/leftovers/page.tsx`
- `apps/web/app/plan/favorites/page.tsx`
- `apps/web/app/plan/collections/page.tsx`
- `apps/web/app/plan/collections/[id]/page.tsx`
- `apps/web/app/wellness/progress/page.tsx`

**Изменённые:**

- `apps/web/components/home-2026/Home2026.tsx`
- `apps/web/components/home-2026/PlanAmHero2026.tsx`
- `apps/web/lib/home/planam-hero-2026.ts`
- `apps/web/lib/home/planam-hero-2026.test.ts`
- `apps/web/lib/home/redirect-path-2026.ts`
- `apps/web/lib/planam/routes.ts`
- `apps/web/components/plan-2026/PlanToday2026.tsx`
- `apps/web/components/plan-2026/PlanMealCard2026.tsx`
- `apps/web/components/plan-2026/PlanTimelineSection2026.tsx`
- `apps/web/components/dom-2026/Pantry2026.tsx`

---

## 3. Проверенные маршруты

| Маршрут | Статус |
|---------|--------|
| `/` | OK — Home + rail + leftovers card |
| `/plan/today` | OK — query highlight |
| `/plan/generate` | OK |
| `/plan/recipes` | OK |
| `/shopping` | OK |
| `/home/pantry` | OK — leftovers CTA |
| `/home/leftovers` | OK — новая страница |
| `/plan/favorites` | OK — empty state, не 404 |
| `/plan/collections` | OK — empty state, не 404 |
| `/plan/collections/1` | OK — redirect |
| `/wellness` | OK |
| `/wellness/progress` | OK — redirect |

---

## 4. Проверенные CTA

- Home hero primary / secondary (meal)
- TodayDishRail «Открыть»
- Home «Готовить из остатков» / quick actions grid
- Pantry «Подобрать рецепт из остатков»
- Dead route empty states → recipes catalog

---

## 5. Build / lint

```text
cd apps/web && npm run build  → exit 0
```

Предупреждения (до задачи, не из diff):

- `@next/next/no-img-element` в `AccountHub2026.tsx`, `ProfileDashboard.tsx`

---

## 6. Backend / API / БД

**Нет изменений.**

---

## 7. Остаётся в P1/P2

- Реальные фото рецептов / CDN pipeline
- Полноценные Favorites/Collections экраны
- TodayDishRail: inline replace без перехода
- Pantry manual add/edit
- ScopeChip, capture CTAs на Home
- Notifications/Care на полных `*2026` примитивах
- Реальный payment checkout
- Admin UI polish

---

## 8. Known issues

- P0/P4 hero срабатывают только при наличии `next_action` в `MenuOverview` (backend уже отдаёт; без поля — fallback).
- `/shopping/leftovers` остаётся legacy alias; canonical — `/home/leftovers`.
- Дублирование входа в leftovers (карточка + quick action) — намеренно для discoverability.
