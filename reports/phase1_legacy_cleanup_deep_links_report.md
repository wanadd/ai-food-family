# PLANAM — Phase 1 Legacy Cleanup: Deep Links + Orphan Components

**Дата:** 2026-06-08  
**Ветка:** `fix/2026-canonical-deep-links-and-phase1-cleanup`  
**База:** `fix/visual-qa-p0-p1-hotfix`  
**Режим:** Phase 1 safe cleanup (по `reports/legacy_cleanup_canonical_routes_audit.md`)

---

## 1. Executive summary

Выполнен первый безопасный cleanup после read-only аудита:

- Исправлены **2026 user-facing deep links** на canonical routes
- Устранён **redirect ping-pong** `/shopping ↔ /home/shopping` в migration map
- Добавлены **explicit rules** для `/menu/event` и `/menu/settings`
- Удалены **6 orphan-компонентов** с нулевыми импортами
- Удалён мёртвый файл `redirect-path-2026.ts` (функция не импортировалась)

**Не изменялись:** backend/API/БД/auth/admin/payment/Docker/Telegram bot/care scheduler, middleware redirects (кроме migration map), legacy pages/routes.

---

## 2. Canonical deep links — исправлено

| Файл | Было | Стало |
|------|------|-------|
| `components/dom-2026/Pantry2026.tsx` | `/home/shopping` (×4) | `PLANAM_ROUTES.shopping` |
| `components/dom-2026/Shopping2026.tsx` | `/home/pantry?returnTo=/home/shopping` | `PLANAM_ROUTES.pantry` + `returnTo=/shopping` |
| `components/wellness-2026/WellnessGoalCard2026.tsx` | `/profile/nutrition` (×2) | `PLANAM_ROUTES.accountNutrition` |
| `components/family/MemberCard.tsx` | `/profile/nutrition` | `/account/nutrition` |
| `components/notifications/NotificationsView.tsx` | back → `/profile` | back → `/account` |
| `components/settings/SettingsScaffold.tsx` | back → `/settings`, `/profile` | `/account/settings`, `/account` |
| `components/nutrition-profile/NutritionProfileForm.tsx` | returnTo fallback `/profile` | `/account` |
| `lib/menu/planner-options.ts` | `/profile/nutrition`, `/shopping/pantry`, `/shopping/leftovers` | `PLANAM_ROUTES.accountNutrition`, `.pantry`, `.homeLeftovers` |

### `PLANAM_ROUTES` — проверка ключей

Все требуемые canonical keys уже присутствуют в `lib/planam/routes.ts`:

```text
shopping          → /shopping
pantry            → /home/pantry
homeLeftovers     → /home/leftovers
account           → /account
accountNutrition  → /account/nutrition
accountSettings   → /account/settings
```

Legacy alias `leftovers: "/shopping/leftovers"` **сохранён** (не удалялся в этом PR).

---

## 3. Legacy ссылки — что осталось и почему

| Место | Путь | Причина оставить |
|-------|------|------------------|
| `lib/planam/routes.ts` | `leftovers: "/shopping/leftovers"` | Legacy alias по спецификации PR |
| `lib/navigation/nav-config-2026.ts` | `/home/shopping` в `ROUTES_2026`, tab matching | Alias meta + redirect page; tab detection |
| `lib/navigation/back-navigation-2026.ts` | `/home/shopping` в `MAIN_TAB_PATHS` | Распознавание старых returnTo/history |
| `lib/navigation/return-to.ts` | `/home/shopping` в `TAB_ROOTS_2026`, label matcher | Обратная совместимость returnTo query |
| `app/home/shopping/page.tsx` | redirect → `/shopping` | Canonical alias route (не удалялся) |
| `app/onboarding/page.tsx` | legacy branch → `/profile/nutrition` | Flag-off path; redirect chain работает |
| `components/menu/MenuCurrentView.tsx` | `/shopping/leftovers` | Legacy-only (redirect при UI2026) |
| `components/menu/MealCheckinPanel.tsx` | `/shopping/leftovers` | Legacy checkin flow |
| `components/profile/ProfileDashboard.tsx` | `/profile/nutrition` | Legacy-only (redirect при UI2026) |
| `components/nutritionist/*` | `/profile/nutrition` | Legacy health screens |
| `components/family/FamilyDashboard.tsx` | `/profile` fallback | Legacy non-embedded shell |
| `components/subscription/SubscriptionDashboard.tsx` | `/profile` back | Legacy subscription page |
| `lib/navigation/nav-config.ts` | `/shopping/leftovers` | Legacy bottom nav |

**2026 user-facing компоненты** (`dom-2026/*`, `wellness-2026/WellnessGoalCard2026`, `family/MemberCard`, `notifications`, `settings`, `nutrition-profile`) — **очищены**.

---

## 4. Route migration map — изменения

**Файл:** `apps/web/lib/navigation/route-migration-2026.ts`

### 4.1 Ping-pong `/shopping`

**Удалено правило:**

```text
/shopping → /home/shopping  (exact)
```

**Результат:** при `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=true` middleware больше не перенаправляет `/shopping` на `/home/shopping`. Canonical `/shopping` остаётся стабильным. `/home/shopping` по-прежнему редиректит на `/shopping` через `app/home/shopping/page.tsx`.

**Сохранено:** `/shopping/pantry → /home/pantry`, `/pantry → /home/pantry`.

### 4.2 Битые prefix redirects

**Добавлены explicit rules (перед prefix `/menu`):**

| From | To | Note |
|------|-----|------|
| `/menu/event` | `/plan/generate` | Event planner → ближайший canonical planning flow |
| `/menu/settings` | `/account/settings` | Menu settings → account settings |

**Реорганизация:** все exact `/menu/*` rules вынесены **перед** prefix rule `/menu → /plan`, чтобы `/menu/event` не превращался в `/plan/event` (404).

---

## 5. Orphan components — удалено

| Файл | Import check | Статус |
|------|--------------|--------|
| `components/OpenMiniAppButton.tsx` | 0 imports | ✅ Удалён |
| `components/TelegramAuthPanel.tsx` | 0 imports | ✅ Удалён |
| `components/care/CareTelegramLinkCard.tsx` | 0 imports | ✅ Удалён |
| `components/recipes/FromPantrySection.tsx` | 0 imports | ✅ Удалён |
| `components/app-mode/ModeSwitcher.tsx` | 0 imports | ✅ Удалён |
| `components/planam-2026/screens/RoutePlaceholder2026.tsx` | barrel only | ✅ Удалён + export из `planam-2026/index.ts` |

---

## 6. `resolveHomeRedirectPath`

**Выбран вариант А (расширенный):** удалён весь файл `apps/web/lib/home/redirect-path-2026.ts`.

**Обоснование:**

- `resolveHomeRedirectPath` не импортировалась нигде в `apps/web`
- `LEGACY_TO_2026` использовалась только внутри этой функции
- Файл содержал устаревший map (`/shopping → /home/shopping`, `/profile/nutrition` без нормализации)
- Удаление безопаснее, чем оставлять мёртвый код с неверными путями

---

## 7. Проверки

### 7.1 Import audit (orphans)

```bash
grep -R "OpenMiniAppButton|TelegramAuthPanel|CareTelegramLinkCard|FromPantrySection|ModeSwitcher|RoutePlaceholder2026" apps/web
```

**Результат:** только `tsconfig.tsbuildinfo` (артефакт build) — сломанных импортов нет.

### 7.2 Legacy links audit (2026 components)

```bash
grep -R "/home/shopping|/profile/nutrition|/shopping/leftovers" apps/web/components/dom-2026
grep -R "/home/shopping|/profile/nutrition|/shopping/leftovers" apps/web/components/wellness-2026/WellnessGoalCard2026.tsx
```

**Результат:** 0 matches в 2026 user-facing компонентах.

### 7.3 Build

```bash
cd apps/web && npm run build
```

**Результат:** ✅ **exit code 0** — compiled successfully, 73 static pages, middleware 27.2 kB.

Предупреждения ESLint (pre-existing): `@next/next/no-img-element` в `AccountHub2026`, `ProfileDashboard`.

### 7.4 Route expectations (логические)

| Route | Ожидание | Статус |
|-------|----------|--------|
| `/shopping` | Canonical, без ping-pong | ✅ migration map исправлен |
| `/home/shopping` | redirect → `/shopping` | ✅ `home/shopping/page.tsx` без изменений |
| `/menu/event` | → `/plan/generate` (не 404) | ✅ explicit rule |
| `/menu/settings` | → `/account/settings` (не 404) | ✅ explicit rule |
| `/home/pantry`, `/home/leftovers` | Canonical dom routes | ✅ без изменений |
| `/account/nutrition` | Canonical nutrition | ✅ deep links исправлены |

---

## 8. Scope confirmation

| Область | Изменено? |
|---------|-----------|
| `apps/web` frontend | ✅ Да (deep links, migration map, orphans) |
| `apps/api` / backend | ❌ Нет |
| БД | ❌ Нет |
| Auth / admin session | ❌ Нет |
| Payment | ❌ Нет |
| Docker / Nginx | ❌ Нет |
| Telegram bot (`bot_menu.py`, `care.py`, etc.) | ❌ Нет |
| Legacy routes/pages | ❌ Не удалялись |
| Middleware (`middleware.ts`) | ❌ Не менялся (только migration map) |
| Nutrition/Notifications UI migration | ❌ Не в scope |

---

## 9. Осталось на Phase 2/3

### Phase 2 — Keep redirect, remove legacy implementation

- Удалить legacy page trees за redirects (`/menu/*`, `/profile/*`, `/health/*`, etc.)
- Удалить `MenuHub`, `ProfileDashboard`, `PantryDashboard`, `MealLeftoversPage`, …
- Обновить `return-to.ts` / `back-navigation-2026.ts`: убрать `/home/shopping` из TAB_ROOTS

### Phase 3 — Migrate first

- `NutritionProfileForm` → 2026 DS
- `NotificationsView` / `CareSettingsPanel` → 2026 DS
- `FamilyDashboard`, `SettingsScaffold` → 2026 DS
- `NutritionistChat` core UI
- Backend care/bot paths → `PLANAM_ROUTES` (координированный релиз)

---

## 10. Files changed

```text
M  apps/web/components/dom-2026/Pantry2026.tsx
M  apps/web/components/dom-2026/Shopping2026.tsx
M  apps/web/components/wellness-2026/WellnessGoalCard2026.tsx
M  apps/web/components/family/MemberCard.tsx
M  apps/web/components/notifications/NotificationsView.tsx
M  apps/web/components/settings/SettingsScaffold.tsx
M  apps/web/components/nutrition-profile/NutritionProfileForm.tsx
M  apps/web/lib/menu/planner-options.ts
M  apps/web/lib/navigation/route-migration-2026.ts
M  apps/web/components/planam-2026/index.ts
D  apps/web/lib/home/redirect-path-2026.ts
D  apps/web/components/OpenMiniAppButton.tsx
D  apps/web/components/TelegramAuthPanel.tsx
D  apps/web/components/care/CareTelegramLinkCard.tsx
D  apps/web/components/recipes/FromPantrySection.tsx
D  apps/web/components/app-mode/ModeSwitcher.tsx
D  apps/web/components/planam-2026/screens/RoutePlaceholder2026.tsx
A  reports/phase1_legacy_cleanup_deep_links_report.md
```
