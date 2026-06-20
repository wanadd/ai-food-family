# PLANAM — карта навигации

Дата: 2026-06-03

## Два контура навигации

| Параметр | Legacy | UI 2026 |
|----------|--------|---------|
| Shell | `AppShell` | `AppShell2026` |
| Bottom nav config | `NAV_TABS` (5 tabs) | `NAV_TABS_2026` (4 tabs) |
| Feature flag | `NEXT_PUBLIC_PLANAM_UI_2026=false` | `NEXT_PUBLIC_PLANAM_UI_2026=true` |
| Onboarding shell | без bottom nav | без bottom nav |

---

## Bottom Navigation

### UI 2026 (`BottomNavigation2026`)

```
Сегодня → /plan/today
Покупки → /home/shopping
Здоровье → /wellness
Профиль → /account
```

- Фиксирован внизу (`AppShell2026`)
- Скрыта на: `/onboarding`, `/admin`, `/dev`
- `/` и `/home/*` — **нет активной вкладки**
- Legacy-префиксы `/profile`, `/settings`, `/family`, `/notifications` подсвечивают вкладку «Профиль»

### Legacy (`BottomNavigation`)

```
Меню → /menu
Покупки → /shopping
ПланАм (центр) → /
Здоровье → /health
Профиль → /profile
```

---

## Header Navigation

### UI 2026 (`ShellHeader2026`)

- Sticky header с заголовком (`getScreenTitle2026`)
- Элементы: `ScreenBack2026`, title, 🏠 (на главную, если pathname ≠ `/`)
- **Скрыт на:** `/`, `/wellness`, `/account`, `/plan/today`, `/plan/recipes`, immersive recipe detail, `/onboarding`, `/admin`, `/dev`

### Legacy (`ScreenLayout` + `ScreenBackNav`)

- Каждый legacy-экран задаёт `title` и `back: { label, href }` в `ScreenLayout`
- Back ведёт на фиксированный href (например `/profile`, `/settings`)

---

## Section Sub-tabs (UI 2026)

`SectionSubTabs2026` — chip-навигация под header.

**Активна только для tab «План»:**

```
Неделя → /plan
Сегодня → /plan/today
Рецепты → /plan/recipes
```

---

## Back Navigation

### UI 2026

| Механизм | Файл | Поведение |
|----------|------|-----------|
| Browser back button | `useTelegramBackButton2026` | `router.back()` если history > 1 |
| `returnTo` query | `return-to.ts` | При наличии — `router.push(returnTo)` |
| Fallback | `getBackFallback2026` | Статические fallback по pathname |
| Screen back UI | `ScreenBack2026` | Кнопка «← {label}» если нет Telegram BackButton |
| Telegram BackButton | `TelegramBackBridge2026` | Native back в Telegram WebApp |

**Fallback-таблица (без returnTo):**

| Текущий путь | Fallback |
|--------------|----------|
| `/plan/recipes/[id]` | `/plan/recipes` |
| `/plan/*` | `/plan/today` |
| `/wellness/*` | `/wellness` |
| `/account/*`, `/profile/*`, `/settings/*` | `/account` |
| `/home/*` | `/` |
| прочие | `/` |

### Legacy

- `ScreenLayout` back href — фиксированный per-screen
- `BottomBackButton` на некоторых экранах

---

## Modal / Sheet Navigation

Overlays не меняют URL (кроме query params). См. `PLANAM_CURRENT_STATE_OVERLAYS.md`.

Query-параметры, влияющие на навигацию:

| Param | Экран | Эффект |
|-------|-------|--------|
| `returnTo` | любой вложенный | Back target |
| `replaceSlot` | `/plan/recipes`, detail | Replace mode |
| `replace=1` | `/plan/today`, `/menu/current` | Open replace sheet/modal |
| `outcome=1` | `/plan/today` | Open meal outcome sheet |
| `meal_outcome=1` | `/` | Open meal outcome sheet |
| `day` | `/plan/today` | Preselect day index |
| `add` | `/shopping` | Open add item sheet |

---

## Middleware redirects (UI 2026=true)

**Всегда редиректят (без `PLANAM_ROUTE_REDIRECTS`):**

```
/profile/*     → /account/*
/family        → /account/family
/notifications → /account/notifications
/settings/*    → /account/settings/*
/recipes/*     → /plan/recipes/*
/menu/recipes  → /plan/recipes
```

**При `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=true` дополнительно:**

```
/menu          → /plan
/menu/current  → /plan/today
/shopping      → /home/shopping
/health        → /wellness
/subscription  → /account/subscription
... (см. route-migration-2026.ts)
```

---

## Карта переходов UI 2026 (основные)

```
/ (Главная)
├─ quick → /plan/today
├─ quick → /home/shopping
├─ quick → /wellness?returnTo=/
├─ sheet → LeftoversSheet (остаётся на /)
└─ bottom nav → plan | shopping | wellness | account

/plan/today (Сегодня) [tab]
├─ subtab → /plan | /plan/recipes
├─ meal → /plan/recipes/[id]?returnTo=/plan/today
├─ replace → /plan/recipes?replaceSlot&returnTo=/plan/today
├─ sheet → ReplaceDishSheet | MealOutcomeSheet
└─ empty → /plan/generate

/plan/recipes [subtab]
└─ card → /plan/recipes/[id]
    ├─ ← catalog (returnTo)
    ├─ sheet → MenuSlotSheet → /plan/today
    └─ sheet → ReplaceDishSheet

/home/shopping [tab]
└─ link → /home/pantry?returnTo=/home/shopping

/wellness [tab]
├─ → /wellness/chat
└─ → /plan/today?outcome=1

/account [tab]
├─ → /account/nutrition
├─ → /account/family
├─ → /account/subscription → checkout
├─ → /account/ams
├─ → /account/notifications
└─ → /account/settings → 5 subpages
```

---

## Карта переходов Legacy (основные)

```
/ (PlanAmHome) [center tab]
/menu [tab]
├─ subtab → /menu | /menu/recipes | /menu/favorites | /menu/collections
├─ → /menu/current
├─ → /menu/generate
└─ sheet → MenuQuickActions

/shopping [tab]
├─ subtab → /shopping/pantry | /shopping/leftovers
└─ sheets → item | category

/health [tab]
├─ → /health/today | /health/chat
└─ → /progress

/profile [tab]
├─ → /profile/nutrition | /family | /subscription | /notifications
└─ → /settings → subpages
```

---

## Список всех URL (71 маршрут)

См. `PLANAM_CURRENT_STATE_SCREENS.md` и `route-migration-2026.ts`.

**Уникальных URL в коде:** 71 page.tsx  
**Записей в ROUTE_MIGRATION_2026:** 20 пар from→to
