# PLANAM 2026 — Final UX QA Report

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Контекст:** после цветового фикса (`PLANAM_2026_COLOR_FIX_REPORT.md`)

---

## 1. Что проверено

| Маршрут | Проверка |
|---------|----------|
| `/`, `/dev/planam-2026` | 2026 theme scope, cream/sage/graphite |
| `/plan/today` | Empty state, CTA «Создать меню» → `/plan/generate` |
| `/plan/recipes`, `/plan/recipes/[id]` | Каталог, empty states, «В меню» / «В покупки» |
| `/wellness` | Загрузка / empty / контент (не вечный skeleton) |
| `/account`, `/account/subscription` | Hub + подписка без тупика |
| `/shopping` → `/home/shopping` | Redirect при UI_2026, список, sync |
| `/shopping/pantry` → `/home/pantry` | Redirect, запасы |
| `/shopping/leftovers` | 2026-страница остатков |
| Bottom nav | План · Дом · Забота · Профиль |
| Light / Dark / System | ThemeProvider + `data-planam-ui="2026"` |
| Legacy `UI_2026=false` | Build не ломается (см. §6) |

---

## 2. Что исправлено

### `/wellness` — вечный skeleton
**Причина:** `reload()` выходил при `!initData`, `loadState` оставался `"loading"`.  
**Исправление:** при отсутствии auth — `ready` + empty state; skeleton только при реальной загрузке с `initData`.

**Empty state (по ТЗ):**
- Заголовок: «Забота пока не настроена»
- CTA: «Настроить заботу» → `/profile/nutrition`

### `/account/subscription` — тупик
**Было:** одна строка «Подписка доступна в Telegram Mini App».  
**Стало:** `SubscriptionOffline2026` — статус, PLANAM Plus, преимущества, пояснение, CTA «Открыть в Telegram» (+ toast / ссылка на бота). При ошибке API — тот же экран с «Обновить статус».

### `/shopping/leftovers` — legacy UI
**Стало:** `Leftovers2026` при `UI_2026=true` (2026 palette, empty states).

### Shopping / Pantry без auth
Empty states вместо пустого экрана при локальном просмотре без `initData`.

### Recipes — «В покупки»
`addRecipeToShopping` передаёт `X-App-Mode` (scope family/personal).

### Recipes — «В меню»
Graceful message при 500; toast без initData; sheet без JS-crash.

---

## 3. Маршруты — статус

| Маршрут | Открывается | Примечание |
|---------|-------------|------------|
| `/` | ✅ | Home2026 |
| `/dev/planam-2026` | ✅ | DS preview |
| `/plan/today` | ✅ | Empty → `/plan/generate` |
| `/plan/generate` | ✅ | Генерация меню |
| `/plan/recipes` | ✅ | Каталог + filters |
| `/plan/recipes/[id]` | ✅ | Detail + sheets |
| `/wellness` | ✅ | Empty / data / error |
| `/account` | ✅ | AccountHub2026 |
| `/account/subscription` | ✅ | Hub или offline fallback |
| `/shopping` | ✅ | Redirect → `/home/shopping` |
| `/home/shopping` | ✅ | Список + sync |
| `/shopping/pantry` | ✅ | Redirect → `/home/pantry` |
| `/shopping/leftovers` | ✅ | Leftovers2026 |

---

## 4. CTA — статус

| CTA | Маршрут / поведение |
|-----|---------------------|
| Настроить заботу | `/wellness` → `/profile/nutrition` |
| Создать меню | `/plan/today` → `/plan/generate` |
| В меню | Sheet день/приём → `assignRecipeToMenuSlot` |
| В покупки | `POST /recipes/{id}/add-to-shopping` + toast |
| Из меню (shopping) | `syncShoppingList` + toast при ошибке |
| Открыть в Telegram | `/account/subscription` offline |
| Bottom tabs | `/plan/today`, `/`, `/wellness`, `/account` |

---

## 5. Оставшиеся проблемы

| ID | Описание | Severity |
|----|----------|----------|
| R1 | Оплата — stub/checkout, не production billing | Ожидаемо |
| R2 | Каталог рецептов может быть пуст на dev API | Empty state OK |
| R3 | `ProfileDashboard.tsx` — lint warning `<img>` | Pre-existing |
| R4 | `/settings/*` при `UI_2026=true` — legacy palette | Strangler backlog |
| R5 | Wellness chat — встроенный `NutritionistChat` (legacy `.pa-*`, remapped) | Приемлемо |
| R6 | Полный E2E в Telegram не автоматизирован в этом проходе | Ручной smoke |

---

## 6. QA-команды

```text
cd apps/web
npm run lint   → OK (1 warning: ProfileDashboard.tsx)
npm run build  → OK
```

**Legacy:** при `NEXT_PUBLIC_PLANAM_UI_2026=false` build проходит; legacy shell (`AppShell` + stone/emerald nav) не изменялся в этом проходе.

---

## 7. Изменённые файлы

- `components/wellness-2026/WellnessHome2026.tsx`
- `components/monetization-2026/SubscriptionHub2026.tsx`
- `components/monetization-2026/SubscriptionOffline2026.tsx` *(новый)*
- `components/dom-2026/Leftovers2026.tsx` *(новый)*
- `components/dom-2026/Shopping2026.tsx`
- `components/dom-2026/Pantry2026.tsx`
- `components/dom-2026/index.ts`
- `components/recipes-2026/RecipeDetail2026.tsx`
- `components/recipes-2026/MenuSlotSheet2026.tsx`
- `lib/recipes/api.ts`
- `app/shopping/leftovers/page.tsx`

---

## 8. Готовность к следующему этапу (рецепты / база блюд)

**Вердикт: GO** для продолжения работ над рецептами и наполнением каталога.

Основные маршруты 2026 стабильны: нет вечных skeleton, нет тупиковых subscription/wellness экранов, CTA ведут на существующие маршруты, ошибки API не роняют UI.

**Рекомендуемый ручной smoke перед бетой:** Telegram Mini App, все 4 bottom tabs, Light/Dark toggle в Account, «Создать меню» с пустого плана, «В меню» с карточки рецепта.
