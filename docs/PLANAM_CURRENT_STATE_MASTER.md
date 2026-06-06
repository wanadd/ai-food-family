# PLANAM — Current State Master Audit

Дата: 2026-06-03  
Ветка: `sprint-0/planam-2026-foundation`  
Тип аудита: продуктовый снимок кодовой базы (без UX-оценок, без рекомендаций).

---

## 1. Созданные документы

| # | Документ | Содержание |
|---|----------|------------|
| 1 | [PLANAM_CURRENT_STATE_SCREENS.md](./PLANAM_CURRENT_STATE_SCREENS.md) | Полная карта экранов |
| 2 | [PLANAM_CURRENT_STATE_ACTIONS.md](./PLANAM_CURRENT_STATE_ACTIONS.md) | Аудит кнопок и действий |
| 3 | [PLANAM_CURRENT_STATE_NAVIGATION.md](./PLANAM_CURRENT_STATE_NAVIGATION.md) | Карта навигации |
| 4 | [PLANAM_CURRENT_STATE_USER_FLOWS.md](./PLANAM_CURRENT_STATE_USER_FLOWS.md) | Пользовательские сценарии |
| 5 | [PLANAM_CURRENT_STATE_OVERLAYS.md](./PLANAM_CURRENT_STATE_OVERLAYS.md) | Модалки и sheets |
| 6 | [PLANAM_CURRENT_STATE_LAYOUTS.md](./PLANAM_CURRENT_STATE_LAYOUTS.md) | Экранное пространство |
| 7 | [PLANAM_CURRENT_STATE_DATA.md](./PLANAM_CURRENT_STATE_DATA.md) | Данные и API |
| 8 | [PLANAM_CURRENT_STATE_COMPONENTS.md](./PLANAM_CURRENT_STATE_COMPONENTS.md) | Каталог компонентов |
| 9 | [PLANAM_CURRENT_STATE_MASTER.md](./PLANAM_CURRENT_STATE_MASTER.md) | Этот документ |

---

## 2. Список экранов (сводка)

### UI 2026 (production default, 22 маршрута)

```
/                          Home2026
/home                      → redirect /
/home/shopping             Shopping2026
/home/pantry               Pantry2026
/plan                       PlanWeek2026
/plan/today                 PlanToday2026
/plan/generate              PlanGenerate2026
/plan/recipes               RecipeCatalog2026
/plan/recipes/[id]          RecipeDetail2026
/wellness                   WellnessHome2026
/wellness/chat              WellnessChat2026
/account                    AccountHub2026
/account/nutrition          NutritionProfileForm
/account/family             FamilyDashboard
/account/notifications      NotificationsView
/account/settings           SettingsHub
/account/settings/*         5 subpages
/account/subscription       SubscriptionHub2026
/account/subscription/checkout  PaymentStub2026
/account/ams                AmsHub2026
/onboarding                 Onboarding2026Flow
```

### Legacy (существуют параллельно, 35+ маршрутов)

```
/menu, /menu/current, /menu/generate, /menu/recipes, /menu/favorites,
/menu/collections, /menu/collections/[id], /menu/settings, /menu/event
/shopping, /shopping/pantry, /shopping/leftovers
/profile, /profile/nutrition, /family, /notifications, /settings/*
/health, /health/today, /health/chat, /progress, /subscription
/recipes, /recipes/[id]
```

### Системные

```
/onboarding, /admin/* (9), /dev/planam-2026
```

### Redirect-only (~10)

```
/home, /recipes, /pantry, /nutritionist/*, /menu/scenarios,
/menu/leftovers, /health/care, ...
```

---

## 3. Список действий (сводка)

| Группа | Кол-во |
|--------|--------|
| Bottom nav + header + subtabs | 7 |
| UI 2026 экраны | ~95 |
| Legacy экраны | ~45 |
| Overlays (кнопки внутри) | ~55 |
| Admin | ~25 |
| **Итого** | **~227** |

Детали: [ACTIONS.md](./PLANAM_CURRENT_STATE_ACTIONS.md)

---

## 4. Пользовательские сценарии (13)

1. Открыть рецепт
2. Добавить рецепт в меню
3. Заменить блюдо
4. Добавить в покупки
5. Посмотреть остатки
6. Открыть здоровье
7. Изменить настройки
8. Подключить семью
9. Оформить подписку
10. Сгенерировать меню
11. Онбординг
12. Чат с нутрициологом
13. Отметить приём пищи

Детали: [USER_FLOWS.md](./PLANAM_CURRENT_STATE_USER_FLOWS.md)

---

## 5. Навигация (сводка)

### Bottom Navigation UI 2026

`Сегодня | Покупки | Здоровье | Профиль`

### Bottom Navigation Legacy

`Меню | Покупки | ПланАм | Здоровье | Профиль`

### Back Navigation

- `returnTo` query param
- `getBackFallback2026` static fallbacks
- Telegram BackButton
- Legacy ScreenLayout back href

### Middleware redirects (UI 2026)

20 пар в `route-migration-2026.ts`

Детали: [NAVIGATION.md](./PLANAM_CURRENT_STATE_NAVIGATION.md)

---

## 6. Модалки и sheets (20)

| Тип | Count |
|-----|-------|
| Legacy Sheet wrappers | 7 |
| BottomSheet2026 | 5 |
| Custom family sheets | 3 |
| Modal | 2 |
| Dialog | 2 |
| Toast | 1 |

Детали: [OVERLAYS.md](./PLANAM_CURRENT_STATE_OVERLAYS.md)

---

## 7. Компоненты (~88)

| Категория | Count |
|-----------|-------|
| Navigation | 9 |
| Cards 2026 | 12 |
| Screen containers 2026 | 15 |
| Screen containers legacy | 15+ |
| UI primitives | 6 |
| Overlays | 20 |
| Providers | 6 |

Детали: [COMPONENTS.md](./PLANAM_CURRENT_STATE_COMPONENTS.md)

---

## 8. Маршруты (71)

| Категория | Count |
|-----------|-------|
| Всего `page.tsx` | **71** |
| UI 2026-only | 22 |
| Legacy-only | 35 |
| Dual-mode (flag branch) | 14 |
| Redirect-only | ~10 |
| **Экранов с UI** | **~58** |

---

## 9. API (23 модуля, ~45 prefixes)

```
/auth, /users/me/app-context, /menus/*, /recipes/*, /collections/*,
/shopping-lists/*, /shopping-categories, /pantry/*, /meal-checkins/*,
/meal-leftovers/*, /nutrition-profile/me, /nutritionist/*, /progress/*,
/families/*, /notifications/settings, /care/*, /subscriptions/*,
/legal/*, /onboarding/me, /event-plans/*, /admin/*
```

Детали: [DATA.md](./PLANAM_CURRENT_STATE_DATA.md)

---

## 10. Архитектурные факты

| Факт | Значение |
|------|----------|
| Два UI-контура | Legacy + UI 2026 |
| Переключатель | `NEXT_PUBLIC_PLANAM_UI_2026` |
| Production default | `true` (Dockerfile.prod) |
| Shell 2026 | `AppShellBridge` → `AppShell2026` |
| Shell legacy | `AppShellBridge` → `AppShell` |
| Onboarding | отдельный shell без bottom nav |
| Admin/Dev | без bottom nav |
| Реальные данные | backend API (FastAPI) |
| Заглушки | PaymentStub2026, skeletons, empty states |
| Кэш | session-cache in-memory |

---

## Финальные метрики

| Метрика | Значение |
|---------|----------|
| Созданных документов | **9** |
| Зарегистрированных маршрутов | **71** |
| Экранов с UI | **~58** |
| Пользовательских сценариев | **13** |
| Задокументированных действий | **~227** |
| Overlay-компонентов | **20** |
| API модулей | **23** |
| Основных UI-компонентов | **~88** |

---

*Аудит выполнен без изменений кода. Только факты из текущего состояния репозитория.*
