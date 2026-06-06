# PLANAM — экранное пространство (layouts)

Дата: 2026-06-03  
Только описание. Без оценок.

---

## UI 2026 — основные экраны

### `/` — Главная (`Home2026`)

| Параметр | Значение |
|----------|----------|
| Скролл | да |
| Обязателен | при длинном контенте (баннер + insight) |
| Основных блоков | 6: header, hero, quick actions, CTA row, monetization banner, AI insight |
| Карточек | 4 quick action tiles + hero card + optional cards |
| CTA | 6+ (quick actions, 2 primary buttons, hero actions) |
| Фото | recipe image в hero (если есть menu) |
| Таблицы | нет |
| Списки | нет (tiles grid 2×2) |
| Shell header | скрыт |
| Bottom nav offset | `BOTTOM_NAV_OFFSET_2026` |

### `/plan/today` — Сегодня

| Параметр | Значение |
|----------|----------|
| Скролл | да (timeline meals) |
| Блоков | day chips, action row, timeline sections |
| Карточек | 1+ `PlanMealCard2026` per meal |
| CTA | 3 header + 4+ per meal card |
| Фото | recipe thumbnail per meal |
| Списки | timeline grouped list |
| Shell header | скрыт (subtabs only) |

### `/plan/recipes` — Каталог

| Параметр | Значение |
|----------|----------|
| Скролл | да |
| Блоков | search, filter chips, grid |
| Карточек | grid 2 col `RecipeGridCard2026` |
| CTA | search, filters, per-card link |
| Фото | да (recipe images) |
| Shell header | скрыт |

### `/plan/recipes/[id]` — Рецепт

| Параметр | Значение |
|----------|----------|
| Скролл | да |
| Блоков | hero image, title, metrics grid, ingredients, steps |
| Карточек | metric cards, ingredient list |
| CTA | 4–6 buttons sticky bottom area |
| Фото | hero 16:9 |
| Shell header | скрыт (immersive); inline «← Каталог» |

### `/home/shopping` — Покупки

| Параметр | Значение |
|----------|----------|
| Скролл | да |
| Блоков | toolbar, category groups |
| Карточек | items per category (list rows) |
| CTA | sync, hide checked, pantry link |
| Списки | да (grouped) |
| Shell header | да («Список покупок») |

### `/wellness` — Здоровье

| Параметр | Значение |
|----------|----------|
| Скролл | да (при полных данных) |
| Блоков | header, ring, today card, water, insight, goal, week strip, 2 CTA |
| Карточек | 5–7 |
| CTA | 2 wide buttons + water +/- |
| Shell header | скрыт (own h1) |

### `/account` — Профиль

| Параметр | Значение |
|----------|----------|
| Скролл | минимальный (hub fits viewport на многих устройствах) |
| Блоков | header, user card, 7 hub items |
| Карточек | 8 (1 user + 7 actions) |
| CTA | 7 links + theme toggle |
| Shell header | скрыт (own h1) |

### `/account/family` — Семья

| Параметр | Значение |
|----------|----------|
| Скролл | да (при нескольких участниках) |
| Блоков | create form OR family info + members + next step |
| Карточек | member cards |
| CTA | 3–5 buttons |
| Embedded mode | без ScreenLayout header |

### `/account/nutrition` — Питание

| Параметр | Значение |
|----------|----------|
| Скролл | да (много секций) |
| Блоков | progress bar + 7 collapsible sections |
| CTA | 1 sticky save |
| Формы | chips, toggles, number inputs |

---

## Legacy — основные экраны

### `/menu` — MenuHub

| Параметр | Значение |
|----------|----------|
| Скролл | да |
| Блоков | summary, tiles, next action |
| CTA | 3+ links + quick actions sheet |
| SegmentedTabs | 4 menu subtabs |

### `/shopping` — ShoppingListView

| Параметр | Значение |
|----------|----------|
| Скролл | да |
| Блоков | toolbar, categories, items |
| CTA | 5+ toolbar buttons |
| Списки | grouped by category |
| Sheets | add item, add category |

### `/profile` — ProfileDashboard

| Параметр | Значение |
|----------|----------|
| Скролл | да |
| Блоков | user card, nutrition link, 6 menu items |
| CTA | 7+ links |
| ScreenLayout | title «Профиль» + gear icon |

### `/health/today` — HealthTodayView

| Параметр | Значение |
|----------|----------|
| Скролл | да |
| Блоков | advice, meals, progress, water, pantry |
| Карточек | multiple panels |

---

## Onboarding `/onboarding`

| Параметр | Значение |
|----------|----------|
| Скролл | да (per step) |
| Bottom nav | скрыта |
| Блоков | progress, step content, nav buttons |
| Full-screen | да (отдельный shell) |

---

## Admin `/admin/*`

| Параметр | Значение |
|----------|----------|
| Скролл | да |
| Bottom nav | скрыта |
| Таблицы | да (users, families lists) |
| Layout | `AdminShell` sidebar/tabs |

---

## Shell-константы

| Константа | Значение |
|-----------|----------|
| `BOTTOM_NAV_OFFSET_2026` | `calc(4.75rem + safe-area-inset-bottom)` |
| Safe area | `env(safe-area-inset-top)` на headers |
| Max width | `max-w-lg` на большинстве 2026 экранов |
