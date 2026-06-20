# Sprint 2 — Completion Report (PLANAM 2026 Navigation + Routes)

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Спринт:** Navigation 2026, route structure, App Shell, Account Hub, migration map

---

## Цель спринта

Реализовать **структуру приложения** PLANAM 2026 (навигация и маршруты) без Home 2026, рецептов и онбординга.

**Критерии готовности:** выполнены (§7).

---

## 1. Navigation 2026

| Элемент | Файл |
|---------|------|
| Конфиг (SSOT) | `lib/navigation/nav-config-2026.ts` |
| Нижняя навигация | `components/planam-2026/navigation/BottomNavigation2026.tsx` |
| Иконки | `components/planam-2026/navigation/NavIcon2026.tsx` |
| Подвкладки секций | `components/planam-2026/navigation/SectionSubTabs2026.tsx` |

**Вкладки (только при `NEXT_PUBLIC_PLANAM_UI_2026=true`):**

| Вкладка | href | Центр |
|---------|------|-------|
| План | `/plan` | |
| Дом | `/` | ✓ |
| Забота | `/wellness` | |
| Профиль | `/account` | |

При `flag=false` — `AppShellBridge` → legacy `AppShell` + `nav-config.ts` (5 вкладок).

---

## 2. Route structure

| Маршрут | Файл | Содержимое Sprint 2 |
|---------|------|---------------------|
| `/` | `app/page.tsx` | Flag on: заглушка «Дом»; flag off: `PlanAmHome` |
| `/plan` | `app/plan/page.tsx` | Заглушка |
| `/plan/today` | `app/plan/today/page.tsx` | Заглушка |
| `/plan/recipes` | `app/plan/recipes/page.tsx` | Заглушка (рецепты не в scope) |
| `/home` | `app/home/page.tsx` | Redirect → `/` |
| `/home/shopping` | `app/home/shopping/page.tsx` | Заглушка |
| `/home/pantry` | `app/home/pantry/page.tsx` | Заглушка |
| `/wellness` | `app/wellness/page.tsx` | Заглушка |
| `/account` | `app/account/page.tsx` | **Account Hub** |

Guard: `requirePlanamUi2026OrRedirect()` — при выключенном flag новые URL ведут на legacy (`LEGACY_FALLBACK_BY_2026_PATH`).

---

## 3. nav-config-2026 (единый источник)

Экспорты:

- `NAV_TABS_2026`, `PLAN_SUBTABS_2026`, `HOME_SUBTABS_2026`, `WELLNESS_SUBTABS_2026`
- `ACCOUNT_HUB_ITEMS_2026`, `ROUTES_2026`
- `getActiveTabId2026`, `isNavHidden2026`, `getScreenTitle2026`, `getSubTabsForTab2026`
- `ACCOUNT_LEGACY_PREFIXES_2026` — `/profile`, `/family`, … подсвечивают вкладку «Профиль»

Хардкод href/labels вне этого файла **не добавлялся**.

---

## 4. App Shell 2026

`components/planam-2026/layout/AppShell2026.tsx`:

- **Верх:** `ShellHeader2026` (заголовок из `nav-config-2026`)
- **Подзаголовок:** `SectionSubTabs2026` (План / Дом / Забота)
- **Контент:** `children`
- **Низ:** `BottomNavigation2026`
- **Тема:** через `ThemeProvider` в `AppShellBridge` (Light / Dark / System)

---

## 5. Account Hub

`components/planam-2026/account/AccountHub2026.tsx` на `/account`:

| Пункт | Ссылка |
|-------|--------|
| Профиль | `/profile` |
| Семья | `/family` |
| Подписка | `/subscription` |
| Уведомления | `/notifications` |
| Настройки | `/settings` |
| Оформление | inline `ThemeToggle2026` |

---

## 6. Redirect strategy

| Файл | Назначение |
|------|------------|
| `lib/navigation/route-migration-2026.ts` | Карта `ROUTE_MIGRATION_2026` + `resolveMigrationTarget()` |
| `middleware.ts` | Редиректы **только** если оба flag: `PLANAM_UI_2026` + `PLANAM_ROUTE_REDIRECTS` |

```env
NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=false   # default — старые URL без redirect
```

Примеры в карте: `/menu` → `/plan`, `/shopping` → `/home/shopping`, `/health` → `/wellness`, `/profile` → `/account`.

**Старые маршруты не удалены.**

---

## 7. Изменённые и новые файлы

### Новые

```
apps/web/lib/navigation/nav-config-2026.ts
apps/web/lib/navigation/route-migration-2026.ts
apps/web/lib/planam/planam-2026-page.ts
apps/web/lib/planam/layout-constants-2026.ts
apps/web/middleware.ts
apps/web/components/planam-2026/navigation/*
apps/web/components/planam-2026/layout/ShellHeader2026.tsx
apps/web/components/planam-2026/account/AccountHub2026.tsx
apps/web/components/planam-2026/screens/RoutePlaceholder2026.tsx
apps/web/app/plan/**/page.tsx
apps/web/app/home/**/page.tsx
apps/web/app/wellness/page.tsx
apps/web/app/account/page.tsx
docs/SPRINT_2_COMPLETION_REPORT.md
```

### Изменённые

```
apps/web/app/page.tsx
apps/web/components/planam-2026/layout/AppShell2026.tsx
apps/web/components/planam-2026/index.ts
apps/web/lib/planam/feature-flags.ts
apps/web/.env.example
```

### Без изменений (scope)

- API / БД / платежи
- `PlanAmHome`, рецепты, онбординг
- `components/ui/Sheet.tsx`, legacy `nav-config.ts`

---

## 8. Feature flags

```env
NEXT_PUBLIC_PLANAM_UI_2026=false          # legacy app (default)
NEXT_PUBLIC_PLANAM_UI_2026=true           # shell 2026 + новые маршруты
NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=false  # grace redirects (optional)
```

Preview DS: `/dev/planam-2026` (без изменений Sprint 1).

---

## 9. QA

| Проверка | Результат |
|----------|-----------|
| `npx tsc --noEmit` | ✅ Pass |
| `npm run lint` | ✅ Pass (pre-existing `ProfileDashboard` warning) |
| `npm run build` | ✅ Pass — новые routes в бандле |

**Ручная проверка:**

| Сценарий | Ожидание |
|----------|----------|
| `UI_2026=false` | `/` = старый Home, 5-tab nav, `/plan` → redirect `/menu` |
| `UI_2026=true` | 4-tab nav, заглушки, `/account` = hub |
| `UI_2026=true` + `ROUTE_REDIRECTS=true` | `/menu` → `/plan`, и т.д. |

---

## 10. Риски

| Риск | Митигация |
|------|-----------|
| Два корня «Дом» (`/` и `/home`) | `/home` → redirect `/` |
| Legacy экраны без 2026-стилей | До Strangler; hub ссылается на старые страницы |
| Active tab на глубоких legacy URL | `ACCOUNT_LEGACY_PREFIXES_2026` для профиля |
| `/` при flag on — не Home 2026 | Явная заглушка; Sprint 3 |
| Middleware + query string | Редирект сохраняет search params (Next clone) |

---

## 11. Готовность к Sprint 3 (Home 2026)

| Готово | Задача Sprint 3 |
|--------|-----------------|
| ✅ Маршрут `/` + tab «Дом» | `Home2026Page`, Hero, Today rail |
| ✅ `nav-config-2026` | `next_action` CTA из overview |
| ✅ Shell + theme | Подключить реальные карточки Sprint 1 |
| ✅ API overview (Sprint 0) | Consumer в `components/home-2026/*` |
| ⏳ `/plan/today` контент | После или параллельно с Home |
| ⏳ Redirects production | Включить `ROUTE_REDIRECTS` на staging |

---

## 12. Критерии готовности Sprint 2

| # | Критерий | ✓ |
|---|----------|---|
| 1 | Рабочий AppShell 2026 | ✅ |
| 2 | Новая нижняя навигация | ✅ |
| 3 | Структура маршрутов | ✅ |
| 4 | Account Hub | ✅ |
| 5 | Feature flag | ✅ |
| 6 | Старый UI не сломан | ✅ (default flag off) |

---

*Обновлять при старте Sprint 3 (Home 2026 + overview).*
