# PLANAM — Legacy Cleanup & Canonical Routes Audit

**Дата:** 2026-06-08  
**Ветка:** `audit/legacy-cleanup-canonical-routes` (база: `fix/visual-qa-p0-p1-hotfix`)  
**Режим:** read-only  
**Проверяющий:** Cursor Agent (автоматический аудит `apps/web` + cross-check `apps/api` для Telegram/deep links)

---

## 1. Executive summary

После P0/P1 hotfix в проекте **два параллельных контура**: canonical 2026-экраны (`Home2026`, `Plan*2026`, `dom-2026`, `wellness-2026`, `AccountHub2026`) и **legacy-дерево** (`/menu/*`, `/health/*`, `/profile/*`, `/settings/*`), которое остаётся живым через:

1. **Page-level redirects** при `NEXT_PUBLIC_PLANAM_UI_2026=true` (основной prod-путь);
2. **Middleware redirects** при дополнительном `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=true` (opt-in, по умолчанию выкл.);
3. **`requirePlanamUi2026OrRedirect` / `redirectLegacyToPlanam2026`** — двусторонние guard'ы для flag-off fallback.

**Главные выводы:**

| Область | Статус |
|---------|--------|
| Core user journeys (Home, Plan, Recipes, Shopping, Pantry, Leftovers, Wellness, Account hub, Subscription) | **2026 canonical, функционально готовы** |
| Account sub-screens (Nutrition, Notifications, Family, Settings) | **Маршруты canonical, UI legacy** — блокер удаления |
| Legacy URL surface | **~28 deprecated paths** — redirects **нельзя снимать** до обновления Telegram bot, care notifications, scheduler |
| Redirect debt | **Конфликт `/shopping` ↔ `/home/shopping`** в middleware map; **битые prefix-redirects** `/menu/event` → `/plan/event` при broad redirects |
| Safe cleanup | **6 orphan component files** + legacy page trees за redirects (после подтверждения prod flag always-on) |

**Рекомендуемый первый PR (Phase 1):** удалить неимпортируемые компоненты + починить 2026 deep links (`Pantry2026` → `/shopping`, `WellnessGoalCard2026` → `/account/nutrition`) — без снятия redirects.

---

## 2. Canonical route map

**Источники истины:** `apps/web/lib/planam/routes.ts` (`PLANAM_ROUTES`), `apps/web/lib/navigation/nav-config-2026.ts` (`ROUTES_2026`, `NAV_TABS_2026`), page guards в `apps/web/lib/planam/planam-2026-page.ts`.

**Флаги:**

```text
NEXT_PUBLIC_PLANAM_UI_2026=true          — 2026 shell + page redirects (prod)
NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=true  — middleware broad map (default: off)
```

### 2.1 Core canonical routes (подтверждено кодом)

| Route | Current component/page | Canonical? | 2026 DS? | Used in nav? | Redirect? | Status | Recommendation |
|-------|------------------------|------------|----------|--------------|-----------|--------|----------------|
| `/` | `Home2026` (flag on) / `PlanAmHome` (flag off) | **Yes** | Yes | Bottom nav «ПланАм» | — | CANONICAL_KEEP | Keep |
| `/plan/today` | `PlanToday2026` | **Yes** | Yes | Bottom nav «Сегодня» | legacy→`/menu/current` | CANONICAL_KEEP | Keep |
| `/plan` | `PlanWeek2026` | **Yes** | Yes | Plan subtab «Неделя» | legacy→`/menu` | CANONICAL_KEEP | Keep |
| `/plan/generate` | `PlanGenerate2026` | **Yes** | Yes | CTA Home/hero | legacy→`/menu/generate` | CANONICAL_KEEP | Keep |
| `/plan/recipes` | `RecipeCatalog2026` | **Yes** | Yes | Plan subtab «Рецепты» | legacy→`/menu/recipes` | CANONICAL_KEEP | Keep |
| `/plan/recipes/[id]` | `RecipeDetail2026` | **Yes** | Yes | Catalog cards | legacy→`/recipes/[id]` | CANONICAL_KEEP | Keep |
| `/shopping` | `Shopping2026` | **Yes** | Yes | Bottom nav «Покупки» | — | CANONICAL_KEEP | Keep |
| `/home/pantry` | `Pantry2026` | **Yes** | Yes | Home CTA, Shopping link | legacy→`/shopping/pantry` | CANONICAL_KEEP | Keep |
| `/home/leftovers` | `Leftovers2026` | **Yes** | Yes | Home CTA (P0 hotfix) | — | CANONICAL_KEEP | Keep; add to `PLANAM_ROUTES` formally |
| `/wellness` | `WellnessHome2026` | **Yes** | Yes | Bottom nav «Здоровье» | legacy→`/health` | CANONICAL_KEEP | Keep |
| `/wellness/chat` | `WellnessChat2026` (+ `NutritionistChat`) | **Yes** | Partial | CTA on wellness | — | CANONICAL_KEEP | Keep; migrate chat UI (Phase 3) |
| `/account` | `AccountHub2026` | **Yes** | Yes | Bottom nav «Профиль» | legacy→`/profile` | CANONICAL_KEEP | Keep |
| `/account/nutrition` | `NutritionProfileForm` | **Yes** | **No** | Account hub | legacy→`/profile/nutrition` | LEGACY_MIGRATE_FIRST | Migrate form to 2026 DS |
| `/account/subscription` | `SubscriptionHub2026` | **Yes** | Yes | Account hub | legacy→`/subscription` | CANONICAL_KEEP | Keep |
| `/account/subscription/checkout` | `PaymentStub2026` | **Yes** | Yes | Subscription CTA | — | TEMP_STUB_KEEP | Keep until payment integration |
| `/account/ams` | `AmsHub2026` | **Yes** | Yes | Account hub | legacy→`/subscription` | CANONICAL_KEEP | Keep |
| `/account/family` | `FamilyDashboard` | **Yes** | **No** | Account hub | legacy→`/family` | LEGACY_MIGRATE_FIRST | Migrate to 2026 DS |
| `/account/notifications` | `NotificationsView` | **Yes** | **No** | Account hub | legacy→`/notifications` | LEGACY_MIGRATE_FIRST | Migrate to 2026 DS |
| `/account/settings` | `SettingsHub` (inline) | **Yes** | Partial | Account hub | legacy→`/settings` | LEGACY_MIGRATE_FIRST | Migrate settings scaffold |
| `/account/settings/*` | Re-export `settings/*` pages | **Yes** | **No** | Settings menu | — | LEGACY_MIGRATE_FIRST | Shared `SettingsScaffold` |
| `/onboarding` | `Onboarding2026Flow` | **Yes** | Yes | Entry flow | legacy→`/profile/nutrition` | CANONICAL_KEEP | Keep |
| `/admin` | `AdminDashboard` + `AdminShell` | Functional | Legacy UI | — | — | CANONICAL_KEEP | KEEP_ADMIN_ONLY |
| `/admin/users`, `/admin/families`, `/admin/subscriptions`, etc. | Admin pages | Functional | Legacy UI | — | — | CANONICAL_KEEP | KEEP_ADMIN_ONLY |

### 2.2 Stubs & planned routes

| Route | Current component/page | Canonical? | 2026 DS? | Used in nav? | Redirect? | Status | Recommendation |
|-------|------------------------|------------|----------|--------------|-----------|--------|----------------|
| `/plan/favorites` | `EmptyState2026` stub | Planned | Yes | No (no guard) | middleware→from `/menu/favorites` | TEMP_STUB_KEEP | Keep stub; implement Sprint 5+ |
| `/plan/collections` | `EmptyState2026` stub | Planned | Yes | No | middleware→from `/menu/collections` | TEMP_STUB_KEEP | Keep stub |
| `/plan/collections/[id]` | redirect → `/plan/collections` | Planned | — | No | **Yes** | TEMP_STUB_KEEP | Keep redirect to list |
| `/wellness/progress` | redirect → `/wellness` | Merged | — | No | **Yes** | TEMP_STUB_DELETE_LATER | Redirect OK; delete page after backend paths updated |
| `/dev/planam-2026` | DS preview | Dev only | Yes | No | — | CANONICAL_KEEP | Keep for dev |

### 2.3 Legacy alias routes (still served, not canonical)

| Route | Current component/page | Canonical? | 2026 DS? | Used in nav? | Redirect? | Status | Recommendation |
|-------|------------------------|------------|----------|--------------|-----------|--------|----------------|
| `/shopping/leftovers` | `Leftovers2026` (flag on) / `MealLeftoversPage` (off) | Alias | Yes/legacy | Legacy nav only | — | LEGACY_REDIRECT_KEEP | Keep alias; prefer `/home/leftovers` in new code |
| `/home/shopping` | redirect → `/shopping` (UI2026) | Alias | — | `ROUTES_2026` meta | **Yes** | LEGACY_REDIRECT_KEEP | Keep meta for tab matching; fix middleware ping-pong |
| `/home` | redirect → `/` | Alias | — | — | **Yes** | LEGACY_REDIRECT_KEEP | Keep |

### 2.4 Deprecated redirect-only routes (`DEPRECATED_REDIRECT_ROUTES`)

| Route | Redirect target (UI2026) | Component if flag off | Status | Recommendation |
|-------|--------------------------|----------------------|--------|----------------|
| `/menu` | `/plan` | `MenuHub` | LEGACY_REDIRECT_KEEP | Keep redirect; delete `MenuHub` tree in Phase 2 |
| `/menu/current` | `/plan/today` | `MenuCurrentView` | LEGACY_REDIRECT_KEEP | Keep redirect |
| `/menu/generate` | `/plan/generate` | `MenuPlanner` | LEGACY_REDIRECT_KEEP | Keep redirect |
| `/menu/recipes` | `/plan/recipes` | `RecipesView` | LEGACY_REDIRECT_KEEP | Keep redirect |
| `/menu/favorites` | `/plan/favorites` | `FavoritesView` | LEGACY_REDIRECT_KEEP | Keep redirect |
| `/menu/collections` | `/plan/collections` | `CollectionsView` | LEGACY_REDIRECT_KEEP | Keep redirect |
| `/menu/collections/[id]` | — (no UI2026 redirect) | `CollectionDetailView` | LEGACY_MIGRATE_FIRST | Orphan; no 2026 replacement |
| `/menu/leftovers` | `/shopping/leftovers` | redirect only | LEGACY_REDIRECT_KEEP | Keep chain |
| `/menu/scenarios` | `/menu/recipes` → `/plan/recipes` | redirect only | LEGACY_REDIRECT_KEEP | Keep |
| `/menu/settings` | — (middleware→`/plan/settings` **404 risk**) | `MenuSettingsPage` | UNKNOWN_NEEDS_REVIEW | Map explicitly or keep page |
| `/menu/event` | — (middleware→`/plan/event` **404 risk**) | inline wizard | UNKNOWN_NEEDS_REVIEW | Hidden feature; fix migration map |
| `/recipes` | `/plan/recipes` | redirect only | LEGACY_REDIRECT_KEEP | Keep |
| `/recipes/[id]` | `/plan/recipes/[id]` | `RecipeDetailLegacy` | LEGACY_REDIRECT_KEEP | Keep |
| `/pantry` | `/shopping/pantry` → `/home/pantry` | redirect only | LEGACY_REDIRECT_KEEP | **HIGH** — Telegram bot uses `/pantry` |
| `/shopping/pantry` | `/home/pantry` | `PantryDashboard` | LEGACY_REDIRECT_KEEP | Keep |
| `/health` | `/wellness` | `NutritionistDashboard` | LEGACY_REDIRECT_KEEP | Keep |
| `/health/today` | `/wellness` | `HealthTodayView` | LEGACY_REDIRECT_KEEP | Keep |
| `/health/chat` | `/wellness/chat` | `HealthChatPageClient` | LEGACY_REDIRECT_KEEP | Keep |
| `/health/care` | `/notifications` → `/account/notifications` | redirect only | LEGACY_REDIRECT_KEEP | Keep chain |
| `/nutritionist` | `/health` → `/wellness` | redirect only | LEGACY_REDIRECT_KEEP | **HIGH** — bot + care templates |
| `/nutritionist/chat` | `/health/chat` → `/wellness/chat` | redirect only | LEGACY_REDIRECT_KEEP | Keep |
| `/nutritionist/care` | `/health/care` → notifications | redirect only | LEGACY_REDIRECT_KEEP | Keep |
| `/progress` | `/wellness` | `ProgressDashboard` | LEGACY_REDIRECT_KEEP | Keep |
| `/profile` | `/account` | `ProfileDashboard` | LEGACY_REDIRECT_KEEP | **HIGH** — care `water` template |
| `/profile/nutrition` | `/account/nutrition` | `NutritionProfileForm` | LEGACY_REDIRECT_KEEP | **HIGH** — care + onboarding legacy |
| `/family` | `/account/family` | `FamilyDashboard` | LEGACY_REDIRECT_KEEP | **HIGH** — bot menu |
| `/notifications` | `/account/notifications` | `NotificationsView` | LEGACY_REDIRECT_KEEP | Keep |
| `/settings` | `/account/settings` | `SettingsHub` | LEGACY_REDIRECT_KEEP | **HIGH** — bot menu |
| `/settings/*` | `/account/settings/*` (prefix) | `SettingsScaffold` pages | LEGACY_REDIRECT_KEEP | **HIGH** — `/settings/documents` in bot |
| `/subscription` | `/account/subscription` | `SubscriptionDashboard` | LEGACY_REDIRECT_KEEP | Keep |

### 2.5 Специальная проверка (запрошенные пути)

| Path | `page.tsx` exists? | Redirects to | In nav/CTA? | Can delete? | Keep redirect? |
|------|-------------------|--------------|-------------|-------------|----------------|
| `/plan/favorites` | Yes (stub) | — | No direct nav | No — stub | No |
| `/plan/collections` | Yes (stub) | — | No | No — stub | No |
| `/plan/collections/[id]` | Yes | `/plan/collections` | No | Page yes, redirect keep | Yes |
| `/wellness/progress` | Yes | `/wellness` | No | Page later | Yes |
| `/profile` | Yes | `/account` | Legacy only | Page yes (Phase 2) | **Yes — HIGH** |
| `/settings/*` | Yes | `/account/settings/*` | Bot + legacy | Page yes (Phase 2) | **Yes — HIGH** |
| `/menu/*` | Yes (10 routes) | Various `/plan/*` | Legacy shell only | Pages yes (Phase 2) | **Yes — HIGH** |
| `/nutritionist/*` | Yes (3 routes) | `/wellness/*` chain | Bot + care | Pages yes | **Yes — HIGH** |
| `/shopping/leftovers` | Yes | — (renders) | Legacy nav, checkin CTAs | Alias only | Optional keep |
| `/home/capture` | **No** | — | — | N/A | N/A |
| `/home/leftovers` | Yes | — | Home CTA | **No** | No |

---

## 3. Legacy routes and redirect debt

### 3.1 Middleware + migration map

**File:** `apps/web/middleware.ts` + `apps/web/lib/navigation/route-migration-2026.ts`

| From | To | Where defined | Why exists | External risk | Keep/delete recommendation |
|------|----|---------------|------------|---------------|----------------------------|
| `/menu` | `/plan` | `route-migration-2026.ts` | Menu hub rename | **HIGH** — care template `menu`, scheduler | **LEGACY_REDIRECT_KEEP** |
| `/menu/current` | `/plan/today` | migration map | Today meals | MEDIUM | **LEGACY_REDIRECT_KEEP** |
| `/menu/recipes` | `/plan/recipes` | migration map + middleware always | Recipe list | MEDIUM | **LEGACY_REDIRECT_KEEP** |
| `/menu/generate` | `/plan/generate` | migration map | Planner | MEDIUM | **LEGACY_REDIRECT_KEEP** |
| `/menu/favorites` | `/plan/favorites` | migration map | Favorites stub | LOW | **LEGACY_REDIRECT_KEEP** |
| `/menu/collections` | `/plan/collections` | migration map | Collections stub | LOW | **LEGACY_REDIRECT_KEEP** |
| `/menu/event` | `/plan/event` | migration map (prefix) | Unintended | LOW | **FIX MAP** — no `/plan/event` page |
| `/menu/settings` | `/plan/settings` | migration map (prefix) | Unintended | LOW | **FIX MAP** — add explicit rule |
| `/recipes` | `/plan/recipes` | migration map + middleware always | Legacy recipes | MEDIUM | **LEGACY_REDIRECT_KEEP** |
| `/recipes/[id]` | `/plan/recipes/[id]` | middleware always | Shared links | **HIGH** | **LEGACY_REDIRECT_KEEP** |
| `/subscription` | `/account/subscription` | migration map | Profile consolidation | MEDIUM | **LEGACY_REDIRECT_KEEP** |
| `/shopping` | `/home/shopping` | migration map | 2026 home namespace | **HIGH** — bot uses `/shopping` | **FIX** — map to `/shopping` not `/home/shopping` |
| `/shopping/pantry` | `/home/pantry` | migration map | Pantry under home | MEDIUM | **LEGACY_REDIRECT_KEEP** |
| `/pantry` | `/home/pantry` | migration map | Short alias | **HIGH** — bot `QUICK_PANTRY` | **LEGACY_REDIRECT_KEEP** |
| `/health` | `/wellness` | migration map | Rename | MEDIUM | **LEGACY_REDIRECT_KEEP** |
| `/health/today` | `/wellness` | migration map | Merged scroll | LOW | **LEGACY_REDIRECT_KEEP** |
| `/health/chat` | `/wellness/chat` | migration map | Chat move | MEDIUM | **LEGACY_REDIRECT_KEEP** |
| `/nutritionist` | `/wellness/chat` | migration map | Legacy nutritionist | **HIGH** — bot + care | **LEGACY_REDIRECT_KEEP** (consider `/wellness`) |
| `/progress` | `/wellness/progress` | migration map | Progress | MEDIUM | **LEGACY_REDIRECT_KEEP** (page redirects again to `/wellness`) |
| `/profile` | `/account` | migration map + middleware always | Account hub | **HIGH** | **LEGACY_REDIRECT_KEEP** |
| `/profile/nutrition` | `/account/nutrition` | middleware always (prefix) | Nutrition form | **HIGH** — care `water` | **LEGACY_REDIRECT_KEEP** |
| `/family` | `/account/family` | migration map + middleware always | Family | **HIGH** — bot menu | **LEGACY_REDIRECT_KEEP** |
| `/notifications` | `/account/notifications` | migration map + middleware always | Notifications | MEDIUM | **LEGACY_REDIRECT_KEEP** |
| `/settings` | `/account/settings` | migration map + middleware always | Settings | **HIGH** — bot menu | **LEGACY_REDIRECT_KEEP** |
| `/settings/*` | `/account/settings/*` | migration map (prefix) | Settings subpages | **HIGH** — `/settings/documents` | **LEGACY_REDIRECT_KEEP** |

### 3.2 Page-level redirects (not in middleware)

| From | To | Where defined | Why exists | External risk | Recommendation |
|------|----|---------------|------------|---------------|----------------|
| `/home` | `/` | `app/home/page.tsx` | Home alias | LOW | LEGACY_REDIRECT_KEEP |
| `/home/shopping` | `/shopping` | `app/home/shopping/page.tsx` | Canonical shopping | MEDIUM | LEGACY_REDIRECT_KEEP; **fixes ping-pong** |
| `/menu/leftovers` | `/shopping/leftovers` | `app/menu/leftovers/page.tsx` | Old leftovers path | MEDIUM | LEGACY_REDIRECT_KEEP |
| `/menu/scenarios` | `/menu/recipes` | `app/menu/scenarios/page.tsx` | Deprecated feature | LOW | LEGACY_REDIRECT_KEEP |
| `/nutritionist` | `/health` | `app/nutritionist/page.tsx` | Rename chain | **HIGH** | LEGACY_REDIRECT_KEEP |
| `/nutritionist/chat` | `/health/chat` | page | Chat chain | MEDIUM | LEGACY_REDIRECT_KEEP |
| `/nutritionist/care` | `/health/care` | page | Care chain | MEDIUM | LEGACY_REDIRECT_KEEP |
| `/health/care` | `/notifications` | page | Care → notifications | MEDIUM | LEGACY_REDIRECT_KEEP |
| `/pantry` | `/shopping/pantry` | page | Short path | **HIGH** | LEGACY_REDIRECT_KEEP |
| `/wellness/progress` | `/wellness` | page | Merged feature | LOW | LEGACY_REDIRECT_KEEP |
| `/plan/collections/[id]` | `/plan/collections` | page | No detail stub | LOW | LEGACY_REDIRECT_KEEP |
| `/onboarding` (legacy branch) | `/profile/nutrition` | page | Old onboarding | MEDIUM | Update to `/account/nutrition` in Phase 3 |

### 3.3 Multi-hop chains (UI2026=true)

```text
/pantry → /shopping/pantry → /home/pantry
/nutritionist → /health → /wellness
/nutritionist/chat → /health/chat → /wellness/chat
/nutritionist/care → /health/care → /notifications → /account/notifications
/onboarding (legacy) → /profile/nutrition → /account/nutrition
/menu/scenarios → /menu/recipes → /plan/recipes
```

### 3.4 Ping-pong (только при `ROUTE_REDIRECTS=true`)

```text
/shopping →[middleware]→ /home/shopping →[page]→ /shopping → …
```

**Причина:** migration map указывает `/shopping` → `/home/shopping`, а `home/shopping/page.tsx` при UI2026 возвращает на `/shopping`.  
**Рекомендация:** изменить migration map (не в этом аудите) — canonical `/shopping`.

### 3.5 Backend / Telegram external paths (read-only cross-check)

| Source | Legacy path | Canonical target | Risk |
|--------|-------------|------------------|------|
| `apps/api/app/services/bot_menu.py` | `/shopping`, `/pantry`, `/nutritionist`, `/family`, `/settings`, `/settings/documents` | 2026 equivalents | **HIGH** |
| `apps/api/app/services/bot_menu.py` | `/plan/today`, `/plan/generate` | Already 2026 | OK |
| `apps/api/app/services/care.py` CARE_TEMPLATES | `/profile/nutrition`, `/nutritionist`, `/menu`, `/shopping`, `/pantry`, `/family` | Account/wellness/plan | **HIGH** |
| `apps/api/app/services/notification_scheduler.py` | `/shopping`, `/menu` | `/shopping`, `/plan` | **HIGH** |
| `apps/api/app/services/telegram_bot.py` | `/shopping`, `/pantry` | `/shopping`, `/home/pantry` | **HIGH** |

**Правило:** пока backend не обновлён — **все перечисленные legacy redirects остаются**.

---

## 4. Legacy UI components

Компоненты со старыми токенами (`pa-card`, `graphite-*`, `cream-*`, `stone-*`) на **пользовательских** экранах при UI2026=true:

| Component/file | Used by | Route/screen | Legacy signs | User-facing? | Recommendation |
|----------------|---------|--------------|--------------|--------------|----------------|
| `nutrition-profile/NutritionProfileForm.tsx` | `account/nutrition`, `profile/nutrition` | `/account/nutrition` | `pa-card`, `graphite-*`, `cream-*` | **Yes** | **MIGRATE_TO_2026** |
| `nutrition-profile/NutritionSection.tsx` | NutritionProfileForm | same | `pa-card`, `cream-*` | Yes | MIGRATE_TO_2026 |
| `nutrition-profile/NutritionGoalDetailsFields.tsx` | NutritionProfileForm | same | `cream-border`, `graphite-*` | Yes | MIGRATE_TO_2026 |
| `notifications/NotificationsView.tsx` | `account/notifications`, `notifications` | `/account/notifications` | `pa-card`, `graphite-*` | **Yes** | **MIGRATE_TO_2026** |
| `care/CareSettingsPanel.tsx` | NotificationsView | `/account/notifications` | legacy form layout | Yes | MIGRATE_TO_2026 |
| `care/NotificationSettingsForm.tsx` | NotificationsView | same | legacy inputs | Yes | MIGRATE_TO_2026 |
| `settings/SettingsScaffold.tsx` | `settings/*`, `account/settings/*` | `/account/settings/*` | `stone-*`, legacy back nav | **Yes** | **MIGRATE_TO_2026** |
| `family/FamilyDashboard.tsx` (+ sheets) | `account/family`, `family` | `/account/family` | `pa-card`, `graphite-*` | **Yes** | **MIGRATE_TO_2026** |
| `nutritionist/NutritionistChat.tsx` | `WellnessChat2026`, `HealthChatPageClient` | `/wellness/chat` | `pa-card`, `graphite-*` | **Yes** | **MIGRATE_TO_2026** (wrapper 2026, core legacy) |
| `profile/ProfileDashboard.tsx` | `profile/page` | `/profile` (redirect) | full legacy hub | No (redirect) | SAFE_DELETE_IF_UNUSED (Phase 2) |
| `menu/MenuHub.tsx` | `menu/page` | `/menu` (redirect) | legacy plan hub | No (redirect) | SAFE_DELETE_IF_UNUSED (Phase 2) |
| `menu/MenuCurrentView.tsx` | `menu/current` | redirect | legacy today | No | SAFE_DELETE_IF_UNUSED (Phase 2) |
| `menu/MenuPlanner.tsx` | `menu/generate` | redirect | legacy wizard | No | SAFE_DELETE_IF_UNUSED (Phase 2) |
| `recipes/RecipesView.tsx` | `menu/recipes` | redirect | legacy catalog | No | SAFE_DELETE_IF_UNUSED (Phase 2) |
| `shopping/ShoppingListView.tsx` | `shopping/page` (flag off) | legacy shopping | legacy layout | No (2026 default) | KEEP_SHARED_LOGIC until flag-off removed |
| `pantry/PantryDashboard.tsx` | `shopping/pantry` | redirect | legacy pantry | No | SAFE_DELETE_IF_UNUSED (Phase 2) |
| `menu/MealLeftoversPage.tsx` | `shopping/leftovers` (flag off) | legacy leftovers | legacy | No | SAFE_DELETE_IF_UNUSED (Phase 2) |
| `nutritionist/NutritionistDashboard.tsx` | `health/page` | redirect | legacy wellness | No | SAFE_DELETE_IF_UNUSED (Phase 2) |
| `nutritionist/HealthTodayView.tsx` | `health/today` | redirect | legacy | No | SAFE_DELETE_IF_UNUSED (Phase 2) |
| `home/PlanAmHome.tsx` | `page.tsx` (flag off) | `/` legacy | legacy home | No | KEEP until flag-off removed |
| `admin/AdminShell.tsx` | `admin/layout` | `/admin/*` | legacy admin chrome | Admin only | **KEEP_ADMIN_ONLY** |
| `admin/AdminDashboard.tsx` + detail pages | admin routes | `/admin/*` | legacy | Admin only | KEEP_ADMIN_ONLY |
| `layout/AppShell.tsx` | `AppShellBridge` (flag off) | global legacy | legacy nav | No (prod 2026) | KEEP until flag-off removed |
| `layout/BottomNavigation.tsx` | `AppShell` | legacy nav | `/menu`, `/profile` links | No | KEEP until flag-off removed |
| `subscription/SubscriptionDashboard.tsx` | `subscription/page` | redirect | legacy | No | SAFE_DELETE_IF_UNUSED (Phase 2) |
| `progress/ProgressDashboard.tsx` | `progress/page` | redirect | legacy | No | SAFE_DELETE_IF_UNUSED (Phase 2) |

---

## 5. Potential unused files

| File | Imported anywhere? | Last known purpose | Safe to delete? | Notes |
|------|--------------------|--------------------|-----------------|-------|
| `components/OpenMiniAppButton.tsx` | **No** | Open TMA CTA | **Yes** (Phase 1) | Zero imports |
| `components/TelegramAuthPanel.tsx` | **No** | Auth panel | **Yes** (Phase 1) | Zero imports |
| `components/care/CareTelegramLinkCard.tsx` | **No** | Care Telegram link | **Yes** (Phase 1) | Zero imports |
| `components/recipes/FromPantrySection.tsx` | **No** | Recipe pantry section | **Yes** (Phase 1) | Zero imports |
| `components/app-mode/ModeSwitcher.tsx` | **No** | Mode toggle UI | **Yes** (Phase 1) | Zero imports; `ModeBanner` still used |
| `components/planam-2026/screens/RoutePlaceholder2026.tsx` | Barrel only | Sprint placeholder | **Yes** (Phase 1) | Exported, never consumed |
| `lib/home/redirect-path-2026.ts` (`resolveHomeRedirectPath`) | **No** | Home hero redirect map | **Partial** | Function dead; file has useful constants — wire or delete fn |
| `components/menu/MenuSettingsPage.tsx` | `menu/settings` only | Menu overrides | **No** | Route orphan risk with broad redirects |
| `app/menu/event/page.tsx` | Self | Event planner wizard | **No** | Hidden feature, API exists |

**Примечание:** `knip` не запускался (read-only, без установки зависимостей). Рекомендуется `npx knip` на cleanup-этапе.

---

## 6. Old vs new functional coverage

| Domain | New 2026 screen | Old/legacy screen | Functional coverage | Visual coverage | Can delete old? | What blocks deletion |
|--------|------------------|-------------------|---------------------|-----------------|-----------------|----------------------|
| **Home** | `Home2026` (`/`) | `PlanAmHome` | FULL | 2026_READY | Yes (page tree) | `PLANAM_UI_2026` flag-off fallback |
| **Menu/Plan** | `PlanWeek2026`, `PlanToday2026`, `PlanGenerate2026` | `MenuHub`, `MenuCurrentView`, `MenuPlanner` | FULL | 2026_READY | Yes | Redirects + flag-off; `/menu/event`, `/menu/settings` orphans |
| **Recipes** | `RecipeCatalog2026`, `RecipeDetail2026` | `RecipesView`, `RecipeDetailLegacy` | FULL | 2026_READY | Yes | `/recipes/*` external links |
| **Shopping** | `Shopping2026` | `ShoppingListView` | FULL | 2026_READY | Yes | flag-off fallback |
| **Pantry** | `Pantry2026` (`/home/pantry`) | `PantryDashboard` | FULL | 2026_READY | Yes | `/pantry` Telegram + redirects |
| **Leftovers** | `Leftovers2026` (`/home/leftovers`) | `MealLeftoversPage` (`/shopping/leftovers`) | FULL | 2026_READY | Partial | Alias route + checkin CTAs still use `/shopping/leftovers` |
| **Wellness** | `WellnessHome2026`, `WellnessChat2026` | `NutritionistDashboard`, `HealthTodayView`, `ProgressDashboard` | FULL | PARTIAL_LEGACY | Partial | `NutritionistChat` legacy inside 2026 shell; care paths |
| **Account/Profile** | `AccountHub2026` | `ProfileDashboard` | FULL | 2026_READY (hub only) | Yes (hub) | Sub-screens legacy |
| **Subscription** | `SubscriptionHub2026`, `PaymentStub2026` | `SubscriptionDashboard` | FULL | 2026_READY | Yes | `/subscription` redirect |
| **Notifications/Care** | `NotificationsView` on `/account/notifications` | `/health/care`, `/nutritionist/care`, `/settings/care` (removed?) | PARTIAL | LEGACY | No | Care settings embedded in notifications; backend templates |
| **Admin** | Same routes | `AdminShell` + dashboards | FULL | LEGACY | No | Functional requirement |
| **Settings** | `account/settings/*` (re-export) | `settings/*` pages | FULL | LEGACY | No | Bot `/settings/documents`; `SettingsScaffold` shared |

---

## 7. Nav / CTA / deep link audit

**Bottom nav 2026 (`NAV_TABS_2026`):** все ссылки canonical — `/plan/today`, `/shopping`, `/`, `/wellness`, `/account`. ✅

**Account hub (`ACCOUNT_HUB_ITEMS_2026`):** все canonical — `/account/nutrition`, `/account/family`, `/account/subscription`, `/account/ams`, `/account/notifications`, `/account/settings`. ✅

### Проблемные ссылки (non-canonical targets в 2026-коде)

| Source file | Text/CTA | Target | Target exists? | Canonical? | Recommendation |
|-------------|----------|--------|----------------|------------|----------------|
| `dom-2026/Pantry2026.tsx` | «К списку покупок» (×4) | `/home/shopping` | Yes (redirects) | **No** — use `/shopping` | Fix → `/shopping` |
| `dom-2026/Shopping2026.tsx` | «Запасы» returnTo | `/home/pantry?returnTo=/home/shopping` | Yes | Partial | Fix returnTo → `/shopping` |
| `wellness-2026/WellnessGoalCard2026.tsx` | «Настроить цель» | `/profile/nutrition` | Yes (redirects) | **No** | Fix → `/account/nutrition` |
| `family/MemberCard.tsx` | Nutrition link | `/profile/nutrition` | Yes (redirects) | No | Fix → `/account/nutrition` |
| `menu/MenuCurrentView.tsx` | «Остатки блюд» | `/shopping/leftovers` | Yes | Alias | Fix → `/home/leftovers` (when 2026) |
| `menu/MealCheckinPanel.tsx` | Leftovers link | `/shopping/leftovers` | Yes | Alias | Fix → `/home/leftovers` |
| `lib/menu/planner-options.ts` | Blocker links | `/profile/nutrition`, `/shopping/leftovers` | Yes | No | Fix → canonical paths |
| `lib/planam/routes.ts` | `leftovers` alias | `/shopping/leftovers` | Yes | Alias | Document; new code → `homeLeftovers` |
| `notifications/NotificationsView.tsx` | Back nav | `/profile` | Yes (redirects) | No | Fix → `/account` |
| `settings/SettingsScaffold.tsx` | Back nav | `/profile` or `/settings` | Yes (redirects) | No | Fix → `/account` or `/account/settings` |
| `nutrition-profile/NutritionProfileForm.tsx` | Back (non-embedded) | `/profile` | Yes (redirects) | No | Fix → `/account` |
| `lib/home/redirect-path-2026.ts` | Map (unused) | `/home/shopping`, `/profile/nutrition` | Yes | No | Wire fn or delete; fix map |
| `lib/navigation/route-migration-2026.ts` | Middleware | `/shopping` → `/home/shopping` | Yes | **Wrong canonical** | Fix map (separate PR) |

**Backend deep links (не менять в этом этапе, только учитывать):**

| Source | Target | Resolves OK via redirect? |
|--------|--------|---------------------------|
| `care.py` water | `/profile/nutrition` | Yes → `/account/nutrition` |
| `care.py` protein/menu/progress/pro | `/nutritionist` | Yes → `/wellness` (chat map) |
| `care.py` shopping | `/shopping` | Yes |
| `care.py` pantry | `/pantry` | Yes → `/home/pantry` |
| `care.py` family | `/family` | Yes → `/account/family` |
| `bot_menu.py` settings | `/settings`, `/settings/documents` | Yes → account settings |
| `notification_scheduler.py` | `/menu` | Yes → `/plan` |

---

## 8. Cleanup plan

### Phase 1 — Safe delete candidates

| File/route | Why safe | Required check before delete |
|------------|----------|------------------------------|
| `components/OpenMiniAppButton.tsx` | Zero imports | `rg OpenMiniAppButton` |
| `components/TelegramAuthPanel.tsx` | Zero imports | `rg TelegramAuthPanel` |
| `components/care/CareTelegramLinkCard.tsx` | Zero imports | `rg CareTelegramLinkCard` |
| `components/recipes/FromPantrySection.tsx` | Zero imports | `rg FromPantrySection` |
| `components/app-mode/ModeSwitcher.tsx` | Zero imports | `rg ModeSwitcher` |
| `components/planam-2026/screens/RoutePlaceholder2026.tsx` | Barrel-only export | Remove barrel export too |
| `resolveHomeRedirectPath` in `redirect-path-2026.ts` | Dead function | Wire into hero or delete fn only |

**Also Phase 1 (low-risk fixes, not deletes):**

| Item | Action |
|------|--------|
| `Pantry2026` shopping links | `/home/shopping` → `/shopping` |
| `WellnessGoalCard2026` | `/profile/nutrition` → `/account/nutrition` |
| `MemberCard` nutrition href | → `/account/nutrition` |

### Phase 2 — Keep redirect, remove legacy implementation

| Legacy route | Redirect to canonical | Why keep redirect | What can be deleted |
|--------------|----------------------|-------------------|---------------------|
| `/menu` | `/plan` | Bot scheduler, care | `MenuHub`, `MenuSubTabs`, hub-only components |
| `/menu/current` | `/plan/today` | Old bookmarks | `MenuCurrentView` tree (after flag-off removed) |
| `/menu/generate` | `/plan/generate` | Docs, old CTAs | `MenuPlanner` wizard |
| `/menu/recipes` | `/plan/recipes` | External links | `RecipesView`, `MenuSectionLayout` (if unused) |
| `/recipes`, `/recipes/[id]` | `/plan/recipes/*` | Shared recipe links | `RecipeDetailLegacy` |
| `/profile` | `/account` | Care, old nav | `ProfileDashboard` |
| `/profile/nutrition` | `/account/nutrition` | Care water, onboarding legacy | Duplicate page wrapper only |
| `/family` | `/account/family` | Bot menu | Duplicate `family/page.tsx` |
| `/notifications` | `/account/notifications` | Old settings links | Duplicate page |
| `/settings`, `/settings/*` | `/account/settings/*` | Bot documents | Duplicate `settings/page.tsx` hub |
| `/subscription` | `/account/subscription` | Old links | `SubscriptionDashboard` |
| `/pantry`, `/shopping/pantry` | `/home/pantry` | Telegram bot | `PantryDashboard` |
| `/health/*`, `/nutritionist/*`, `/progress` | `/wellness/*` | Bot, care, history | `NutritionistDashboard`, `HealthTodayView`, `ProgressDashboard` |
| `/shopping/leftovers` | Serve `Leftovers2026` or redirect `/home/leftovers` | Checkin CTAs | `MealLeftoversPage` |
| `/home/shopping` | `/shopping` | `ROUTES_2026` meta | `home/shopping/page.tsx` body (redirect-only file OK) |

### Phase 3 — Migrate first

| Area | Current legacy | Target 2026 | Blocking reason |
|------|----------------|-------------|-----------------|
| Nutrition profile | `NutritionProfileForm` | `NutritionProfile2026` (new) | Account hub CTA, onboarding, wellness goals |
| Notifications + Care | `NotificationsView`, `CareSettingsPanel`, `NotificationSettingsForm` | `Notifications2026` | Account hub; care settings UX |
| Family | `FamilyDashboard`, sheets | `Family2026` | Account hub |
| Settings subpages | `SettingsScaffold` | `Settings2026` scaffold | Account settings re-exports |
| Wellness chat core | `NutritionistChat` | Chat UI on `*2026` primitives | Visible inside `WellnessChat2026` |
| Collections/Favorites | `EmptyState2026` stubs | Full `Favorites2026`, `Collections2026` | `/menu/favorites` redirect expects real screen |
| Event planner | `/menu/event` wizard | `/plan/event` or remove | Middleware 404 risk; API `event_plans` exists |
| Backend paths | `care.py`, `bot_menu.py` templates | `PLANAM_ROUTES` paths | Redirects mask breakage — coordinate deploy |

### Phase 4 — Keep for now

| Area | Why keep |
|------|----------|
| `/admin/*` + `AdminShell` | Functional admin; session auth; separate from 2026 DS |
| `/onboarding` | Entry funnel; separate shell in `AppShellBridge` |
| `/account/subscription/checkout` `PaymentStub2026` | Payment integration pending |
| All `DEPRECATED_REDIRECT_ROUTES` redirects | Telegram bot, care notifications, scheduler, user history |
| `AppShell` + `BottomNavigation` (legacy) | Flag-off fallback until flag removed from env |
| `middleware.ts` + `route-migration-2026.ts` | Grace redirects per master spec |
| `requirePlanamUi2026OrRedirect` guards | Bidirectional flag support |
| `MealLeftoversPage` | Until `/shopping/leftovers` alias retired |
| Auth (`AppGate`, `TelegramProvider`, session) | Security — out of scope |

---

## 9. Key decisions

1. **Canonical routes:** `/`, `/plan/today`, `/plan`, `/plan/generate`, `/plan/recipes`, `/plan/recipes/[id]`, `/shopping`, `/home/pantry`, `/home/leftovers`, `/wellness`, `/wellness/chat`, `/account`, `/account/nutrition`, `/account/family`, `/account/subscription`, `/account/ams`, `/account/notifications`, `/account/settings/*`, `/onboarding`, `/admin/*`.

2. **Routes to never hard-delete (redirect only):** `/profile/*`, `/family`, `/notifications`, `/settings/*`, `/subscription`, `/menu/*`, `/recipes/*`, `/pantry`, `/health/*`, `/nutritionist/*`, `/progress`, `/shopping/pantry`, `/shopping/leftovers` (alias), `/home/shopping` — until backend Telegram/care/scheduler paths updated.

3. **Components safe to delete later (Phase 1):** `OpenMiniAppButton`, `TelegramAuthPanel`, `CareTelegramLinkCard`, `FromPantrySection`, `ModeSwitcher`, `RoutePlaceholder2026`.

4. **Components that must not be deleted until migrated:** `NutritionProfileForm`, `NotificationsView`, `CareSettingsPanel`, `NotificationSettingsForm`, `SettingsScaffold`, `FamilyDashboard`, `NutritionistChat`.

5. **Biggest legacy debt:** Account sub-screens (Nutrition, Notifications/Care, Family, Settings) — canonical routes with **fully legacy UI**; plus **redirect/migration map drift** (`/shopping` ping-pong, `/menu/event` broken prefix).

6. **First safe PR:** Phase 1 orphan file deletes + fix 2026 CTAs (`Pantry2026`, `WellnessGoalCard2026`, `MemberCard`) — no redirect removal.

7. **Do not touch:** auth flow, admin session (`X-Admin-Session`), webhooks, Docker, payment pipeline, recipe media pipeline, backend `care.py`/`bot_menu.py` without coordinated release.

---

## 10. What not to touch

| Area | Reason |
|------|--------|
| `apps/api` auth, admin, webhooks, payment | Out of audit scope; redirects depend on stable backend |
| `apps/web/middleware.ts` redirect map | Only change with explicit migration PR + QA |
| Telegram `web_app` URLs in bot/care/scheduler | User-facing deep links in production |
| `AppShellBridge` flag logic | Controls entire shell; prod depends on `PLANAM_UI_2026=true` |
| `admin/*` UI | Functional legacy acceptable per spec |
| `PaymentStub2026` / checkout flow | Monetization not complete |
| `backend/scripts/*` | Unrelated infra scripts |
| Recipe pipeline (`recipes-2026`, media architecture) | Working 2026 path |

---

## 11. Suggested next Cursor task

**Task:** `fix/2026-canonical-deep-links-and-phase1-cleanup`

1. Fix `Pantry2026`, `Shopping2026`, `WellnessGoalCard2026`, `MemberCard`, `NotificationsView`, `SettingsScaffold` back-links → canonical `PLANAM_ROUTES`.
2. Delete Phase 1 orphan components (6 files) + remove dead `resolveHomeRedirectPath` or wire it in `Home2026` hero handler.
3. Fix `route-migration-2026.ts`: `/shopping` → `/shopping` (not `/home/shopping`); add explicit rules for `/menu/event`, `/menu/settings`.
4. Run `npm run build` + `rg` import audit.
5. **Do not** remove legacy pages or middleware redirects in same PR.

**Follow-up task:** `feat/2026-notifications-nutrition-migration` — migrate `NutritionProfileForm` + `NotificationsView` to 2026 DS (largest visual debt).

---

## Appendix A — Route count summary

| Category | Count |
|----------|-------|
| Total `page.tsx` | 76 |
| Canonical 2026 (user-facing) | 22 |
| Stubs / dev / admin | 12 |
| Legacy redirect-only | 28+ |
| Orphan / review (`/menu/event`, `/menu/settings`) | 2 |

## Appendix B — Files analyzed

```text
apps/web/app/**/page.tsx (76)
apps/web/middleware.ts
apps/web/lib/planam/routes.ts
apps/web/lib/navigation/nav-config-2026.ts
apps/web/lib/navigation/route-migration-2026.ts
apps/web/lib/planam/planam-2026-page.ts
apps/web/lib/home/redirect-path-2026.ts
apps/web/components/** (189 files)
apps/api/app/services/bot_menu.py
apps/api/app/services/care.py
apps/api/app/services/notification_scheduler.py
apps/api/app/services/telegram_bot.py
```

---

*Аудит выполнен без изменений исходного кода. Единственный артефакт — этот отчёт.*
