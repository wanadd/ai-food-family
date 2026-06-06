# PLANAM LEGACY DECOMMISSION AUDIT

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation` (после Sprint 1.5)  
**Тип:** read-only аудит — код не менялся

**Источники истины (приоритет):**

1. `docs/PLANAM_V1_FINAL_VISION.md`
2. `docs/PLANAM_V1_RELEASE_BLUEPRINT.md`
3. `docs/PLANAM_V1_PRODUCT_MASTER.md`
4. `docs/PLANAM_V1_HOME_STATES.md`
5. `docs/PLANAM_V1_IMAGE_STRATEGY.md`
6. `docs/PLANAM_V1_SHOPPING_MODEL_UPDATE.md`

---

## Executive summary

Проект работает в **двух параллельных UI-стеках**, переключаемых флагом `NEXT_PUBLIC_PLANAM_UI_2026`.

| Среда | UI по умолчанию |
|-------|-----------------|
| Локально (`.env.example`) | Legacy |
| Production (`apps/web/Dockerfile.prod`) | **V1 / 2026** |

**Главный риск:** production уже на V1-оболочке, но **legacy-маршруты, компоненты и backend-модели остаются в репозитории** и частично доступны пользователю. Это создаёт риск возврата старой логики при отключении флага, прямой навигации на legacy URL или при встраивании legacy-компонентов в V1-экраны.

**Оценка зрелости V1:** ~**55–60%** пользовательского пути в production; ~**40–45%** кодовой базы frontend/backend — legacy или гибрид.

---

# ЧАСТЬ 1 — UI АУДИТ

## 1.1 Мастер-переключатель

| Файл | Назначение | Статус | Причина |
|------|------------|--------|---------|
| `apps/web/lib/planam/feature-flags.ts` | `isPlanamUi2026Enabled()`, `isPlanamRouteRedirectsEnabled()` | **Используется** | Единственный UI feature flag |
| `apps/web/components/layout/AppShellBridge.tsx` | Выбор shell | **Используется** | Точка входа из `AppProviders` |
| `apps/web/lib/planam/ui-scope.ts` | `data-planam-ui="2026"` на `<html>` | **Используется** | Переключает body-токены в CSS |
| `apps/web/Dockerfile.prod` | `NEXT_PUBLIC_PLANAM_UI_2026=true` | **Используется** | Prod default = V1 |

## 1.2 Layouts / Shell

| Файл | Назначение | Статус | Причина |
|------|------------|--------|---------|
| `components/planam-2026/layout/AppShell2026.tsx` | V1 shell: header, sub-tabs, bottom nav | **Используется** | Prod shell |
| `components/planam-2026/layout/ShellHeader2026.tsx` | V1 top bar + back | **Используется** | Через AppShell2026 |
| `components/planam-2026/navigation/BottomNavigation2026.tsx` | V1 bottom nav (5 tabs) | **Используется** | nav-config-2026 |
| `components/planam-2026/navigation/SectionSubTabs2026.tsx` | Plan sub-tabs | **Используется** | /plan/* |
| `components/layout/AppShell.tsx` | Legacy shell + DevModeBanner | **Частично** | Активен при flag=false |
| `components/layout/ScreenLayout.tsx` | Legacy page chrome (cream/stone) | **Частично** | ~20 legacy экранов + embedded account |
| `components/layout/SectionHub.tsx` | Legacy hub без bottom chrome | **Частично** | PlanAmHome, NutritionistDashboard |
| `components/layout/BottomNavigation.tsx` | Legacy nav (emoji, emerald) | **Частично** | flag=false |
| `components/layout/BottomNav.tsx` | Re-export | **Не используется** | Нет импортов |
| `components/layout/BottomBackButton.tsx` | Legacy Telegram back | **Не используется** | @deprecated, нет импортов |
| `components/layout/TopBackLink.tsx` | Deprecated alias | **Не используется** | Нет импортов |
| `components/layout/SegmentedTabs.tsx` | Legacy in-section tabs | **Частично** | MenuSubTabs, ShoppingSubTabs |
| `components/layout/StickyBottomBar.tsx` | Legacy sticky CTA | **Частично** | menu/family/nutrition legacy |
| `components/dev/DevModeBanner.tsx` | Dev banner | **Частично** | Только legacy AppShell |

**Примечание:** `ScreenLayout2026` **не существует**. V1 использует `AppShell2026` + скрытие header через `isShellHeaderHidden2026()`.

## 1.3 Home

| Файл | Назначение | Статус | Причина |
|------|------------|--------|---------|
| `components/home-2026/Home2026.tsx` | V1 home | **Используется** | `/` при flag on |
| `components/home-2026/PlanAmHero2026.tsx` | V1 hero | **Используется** | Единственный hero UI |
| `components/home-2026/PlanAmStatusRows2026.tsx` | Status rows | **Используется** | Home2026 |
| `components/home-2026/MealFallbackPlate2026.tsx` | Fallback plate | **Используется** | Hero + RecipeImage2026 |
| `lib/home/planam-hero-2026.ts` | Hero state machine | **Используется** | Источник логики hero |
| `components/home/PlanAmHome.tsx` | Legacy home hub | **Частично** | `/` при flag off |
| `components/home/HomeTodayCard.tsx` | Legacy today card | **Не используется** | Orphan |
| `components/home/HomeQuickActions.tsx` | Legacy quick actions | **Не используется** | Orphan |
| `components/home/HomeAskPlanAm.tsx` | Legacy AI ask | **Не используется** | Orphan |
| `components/home/HomeRecommendations.tsx` | Legacy recommendations | **Не используется** | Orphan |
| `components/home/HomeShoppingCard.tsx` | Legacy shopping card | **Не используется** | Orphan |
| `components/home/HomeFamilySummary.tsx` | Legacy family summary | **Не используется** | Orphan |
| `components/home-2026/HomeHero2026.tsx` | Superseded hero | **Не используется** | Заменён PlanAmHero2026 |
| `components/home-2026/NextActionCard2026.tsx` | Sprint 1 artifact | **Не используется** | Не в Home2026 |
| `components/home-2026/PlanSnapshot2026.tsx` | Plan snapshot | **Не используется** | Не в Home2026 |
| `components/home-2026/AIInsight2026.tsx` | AI insight | **Не используется** | Убран из home в Sprint 1 |
| `components/home-2026/RecipeRail2026.tsx` | Recipe rail | **Не используется** | Не в Home2026 |
| `components/home-2026/HomeQuickActions2026.tsx` | Quick actions grid | **Не используется** | Убран в Sprint 1 |

## 1.4 V1 screen stacks (источники истины по доменам)

| Директория | Назначение | Статус |
|------------|------------|--------|
| `components/plan-2026/` | Plan week/today/generate | **Используется** |
| `components/dom-2026/` | Shopping, pantry, leftovers | **Используется** |
| `components/wellness-2026/` | Wellness home/chat | **Используется** |
| `components/recipes-2026/` | Recipe catalog/detail | **Используется** |
| `components/onboarding-2026/` | Onboarding flow | **Используется** |
| `components/planam-2026/` | Design system + shell + account hub | **Используется** |
| `components/monetization-2026/` | Subscription/paywall | **Частично** (banner unused) |

## 1.5 Legacy screen stacks

| Директория | Назначение | Статус | Противоречие V1 |
|------------|------------|--------|-----------------|
| `components/menu/` | Menu hub, planner, current | **Частично** | Дублирует `/plan/*`; старые табы |
| `components/shopping/ShoppingListView.tsx` | Legacy shopping UI | **Частично** | flag off; shared subcomponents |
| `components/pantry/` | Legacy pantry | **Частично** | `/shopping/pantry` доступен |
| `components/nutritionist/` | Health dashboard | **Частично** | `/health/*` vs `/wellness` |
| `components/progress/` | Progress dashboard | **Частично** | Нет `/wellness/progress` page |
| `components/profile/` | Profile hub | **Частично** | Redirect → account, но код жив |
| `components/family/` | Family management | **Частично** | Встроен в `/account/family` |
| `components/settings/` | Settings pages | **Частично** | Re-export через `/account/settings/*` |
| `components/notifications/` | Notifications | **Частично** | Встроен в account |
| `components/subscription/` | Legacy subscription | **Частично** | `/subscription` без redirect |
| `components/recipes/` | Legacy catalog/detail | **Частично** | `/menu/recipes`, modal patterns |
| `components/onboarding/` | Legacy wizard | **Не используется** | OnboardingWizard orphan |
| `components/care/` | Care settings | **Частично** | `/health/care` → notifications |

## 1.6 Navigation configs

| Файл | Статус | Причина |
|------|--------|---------|
| `lib/navigation/nav-config-2026.ts` | **V1 SoT** | Bottom nav, account hub, shell header |
| `lib/navigation/nav-config.ts` | **Legacy** | BottomNavigation, MenuSubTabs |
| `lib/navigation/route-migration-2026.ts` | **Мост** | Middleware redirects |
| `lib/plan/plan-paths.ts` | **Гибрид** | Flag-aware plan URLs |

**Расхождение табов (противоречие V1):**

| Legacy | V1 |
|--------|-----|
| Меню → `/menu` | Сегодня → `/plan/today` |
| Здоровье → `/health` | Здоровье → `/wellness` |
| Профиль → `/profile` | Профиль → `/account` |

## 1.7 Styles / Tokens

| Артефакт | Эра | Статус | Где |
|----------|-----|--------|-----|
| `--pa-bg-*`, `--pa-brand-*` (globals.css) | V1 | **Используется** | 2026 screens, `pa-*` tailwind |
| `.pa26-*` typography | V1 | **Используется** | ~60 файлов 2026 |
| `cream-*`, `graphite-*`, `sage-*` (tailwind) | Legacy Phase 1 | **Частично** | ScreenLayout, menu, pantry, admin |
| `stone-*`, `emerald-*` | Pre-Phase-1 | **Частично** | BottomNavigation, onboarding, settings, admin |
| `.pa-card`, `.pa-btn*` | Legacy helpers | **Частично** | Remapped под 2026 в globals.css |
| `docs/PLANAM_COLOR_SYSTEM_V1.md` | V1 doc | **SoT для цветов** | Sprint 1.5 |

**Смешение:** V1 account routes встраивают legacy `FamilyDashboard`, `NutritionProfileForm`, `SettingsScaffold` — в одном экране встречаются `stone-100`, `cream-border` и `pa-*`.

## 1.8 Hooks

| Файл | Статус | Причина |
|------|--------|---------|
| `lib/home/use-compact-viewport.ts` | **V1** | PlanAmHero2026 |
| `lib/planam/embedded-2026.ts` | **Мост** | Legacy components в /account/* |
| `lib/use-protected-screen.ts` | **Legacy** | MenuHub, ShoppingListView, Pantry |
| `lib/cache/use-cached-query.ts` | **Не используется** | Orphan |
| `components/planam-2026/navigation/useTelegramBackButton2026.ts` | **V1** | Telegram BackButton |

---

# ЧАСТЬ 2 — ROUTES АУДИТ

## 2.1 V1 маршруты (требуют `NEXT_PUBLIC_PLANAM_UI_2026=true`)

| Route | Page | Component |
|-------|------|-----------|
| `/` | `app/page.tsx` | `Home2026` |
| `/plan` | `app/plan/page.tsx` | `PlanWeek2026` |
| `/plan/today` | `app/plan/today/page.tsx` | `PlanToday2026` |
| `/plan/generate` | `app/plan/generate/page.tsx` | `PlanGenerate2026` |
| `/plan/recipes` | `app/plan/recipes/page.tsx` | `RecipeCatalog2026` |
| `/plan/recipes/[id]` | `app/plan/recipes/[id]/page.tsx` | `RecipeDetail2026` |
| `/wellness` | `app/wellness/page.tsx` | `WellnessHome2026` |
| `/wellness/chat` | `app/wellness/chat/page.tsx` | `WellnessChat2026` |
| `/account` | `app/account/page.tsx` | `AccountHub2026` |
| `/account/family` | `app/account/family/page.tsx` | `FamilyDashboard` ⚠️ legacy |
| `/account/nutrition` | `app/account/nutrition/page.tsx` | `NutritionProfileForm` ⚠️ |
| `/account/notifications` | `app/account/notifications/page.tsx` | `NotificationsView` ⚠️ |
| `/account/subscription` | `app/account/subscription/page.tsx` | `SubscriptionHub2026` |
| `/account/settings/*` | `app/account/settings/*/page.tsx` | Legacy settings re-export ⚠️ |
| `/home/pantry` | `app/home/pantry/page.tsx` | `Pantry2026` |
| `/shopping` | `app/shopping/page.tsx` | `Shopping2026` (dual) |
| `/shopping/leftovers` | `app/shopping/leftovers/page.tsx` | `Leftovers2026` (dual) |
| `/onboarding` | `app/onboarding/page.tsx` | `Onboarding2026Flow` (dual) |

## 2.2 Legacy маршруты (активны при flag=false; **часть доступна в prod**)

| Route | Статус в prod (UI 2026 on, broad redirects **off**) | Компонент |
|-------|------------------------------------------------------|-----------|
| `/menu` | **Доступен** (нет forced redirect) | MenuHub |
| `/menu/current` | **Доступен** | MenuCurrentView |
| `/menu/generate` | **Доступен** | MenuPlanner |
| `/menu/favorites` | **Доступен** | FavoritesView |
| `/menu/collections/*` | **Доступен** | Collections |
| `/menu/event` | **Доступен** | Event wizard |
| `/menu/settings` | **Доступен** | MenuSettingsPage |
| `/health` | **Доступен** | NutritionistDashboard |
| `/health/today` | **Доступен** | HealthTodayView |
| `/health/chat` | **Доступен** | HealthChatPageClient |
| `/progress` | **Доступен** | ProgressDashboard |
| `/subscription` | **Доступен** | SubscriptionDashboard |
| `/shopping/pantry` | **Доступен** | PantryDashboard |
| `/profile/*` | Redirect → `/account` | ProfileDashboard |
| `/family` | Redirect → `/account/family` | FamilyDashboard |
| `/settings/*` | Redirect → `/account/settings` | Settings |
| `/recipes/*` | Redirect → `/plan/recipes` | RecipeDetailLegacy |
| `/menu/recipes` | Redirect → `/plan/recipes` | RecipesView |

## 2.3 Redirect-only маршруты

| Route | Target |
|-------|--------|
| `/home` | `/` |
| `/home/shopping` | `/shopping` (2026) |
| `/recipes` | `/plan/recipes` or `/menu/recipes` |
| `/pantry` | `/shopping/pantry` |
| `/menu/leftovers` | `/shopping/leftovers` |
| `/menu/scenarios` | `/menu/recipes` |
| `/nutritionist/*` | `/health/*` |
| `/health/care` | `/notifications` |

## 2.4 Middleware (`apps/web/middleware.ts`)

**Всегда редиректит** (при UI 2026): `/profile`, `/family`, `/notifications`, `/settings`, `/recipes`, `/menu/recipes`

**Требует `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=true`:** `/menu`, `/health`, `/progress`, `/subscription`, `/shopping` → V1 paths

## 2.5 Маршруты без страницы (миграция объявлена, UI нет)

| Target | Статус |
|--------|--------|
| `/plan/favorites` | **Нет page.tsx** |
| `/plan/collections` | **Нет page.tsx** |
| `/wellness/progress` | **Нет page.tsx** |

## 2.6 Что ещё открывается пользователю в production

При текущих настройках prod (UI 2026 on, broad redirects off):

- ✅ Основной путь: `/`, `/plan/*`, `/shopping`, `/wellness`, `/account`
- ⚠️ Прямые legacy URL: `/menu/*`, `/health/*`, `/progress`, `/subscription`, `/shopping/pantry`
- ⚠️ Admin: `/admin/*` (скрыт от nav, но доступен)
- ⚠️ Dev: `/dev/planam-2026` (DS preview)

**Удалить после V1:** весь блок `/menu/*`, `/health/*`, `/nutritionist/*`, `/profile/*`, `/progress` (как отдельный route), legacy `/subscription`, `/shopping/pantry`, `/recipes/[id]` legacy detail.

---

# ЧАСТЬ 3 — COMPONENTS: SOURCE OF TRUTH

## 3.1 V1 — источники истины

| Домен | SoT компонент | SoT логика |
|-------|---------------|------------|
| Shell | `AppShell2026` | `nav-config-2026.ts` |
| Home | `Home2026` + `PlanAmHero2026` | `planam-hero-2026.ts` |
| Plan | `plan-2026/*` | `lib/plan/*` |
| Shopping UI | `Shopping2026` | `categories-v1.ts`, `shopping-groups.ts` |
| Wellness | `wellness-2026/*` | `lib/wellness/*` |
| Recipes UI | `recipes-2026/*` | `lib/recipes/*` |
| Account hub | `AccountHub2026` | `ACCOUNT_HUB_ITEMS_2026` |
| Design system | `planam-2026/ui/*`, `cards/*` | `PLANAM_COLOR_SYSTEM_V1.md` |
| Telegram back | `TelegramBackBridge2026` | `useTelegramBackButton2026.ts` |

## 3.2 Legacy — остатки старой версии

| Компонент | Роль | Риск |
|-----------|------|------|
| `AppShell` + `BottomNavigation` | Legacy shell | Возврат при flag off |
| `ScreenLayout` / `SectionHub` | Legacy chrome | Смешение стилей в account |
| `MenuHub`, `MenuPlanner`, `MenuCurrentView` | Старое «Меню» | Дублирует plan |
| `ShoppingListView` | Старые покупки | Другая UX, те же API |
| `NutritionistDashboard`, `HealthTodayView` | Старое «Здоровье» | Дублирует wellness |
| `ProgressDashboard` | Отдельный progress | Нет V1 route |
| `RecipesView`, `RecipeDetailLegacy` | Старый каталог | Старые карточки без V1 media |
| `OnboardingWizard` | Старый onboarding | Orphan |
| `FamilyDashboard`, `NutritionProfileForm` | Shared forms | **Встроены в V1 account** — нельзя удалить без замены |

## 3.3 Гибридный мост

`usePlanam2026Embedded()` — legacy-компоненты рендерятся без `ScreenLayout` внутри `/account/*`. Это **намеренный мост**, не полноценный V1.

---

# ЧАСТЬ 4 — COLOR SYSTEM АУДИТ

## 4.1 V1 (новые)

| Token | Light | Файл |
|-------|-------|------|
| `--pa-bg-canvas` | `#FFFFFF` | `globals.css` |
| `--pa-brand-primary` | `#2F9E44` | `globals.css` |
| `--pa-text-primary` | `#1A1F1C` | `globals.css` |
| `sage-500` | `#2F9E44` | `tailwind.config.ts` |
| `.pa26-hero`, `.pa26-page-title` | typography | `globals.css` |

**Использование:** ~60 файлов с `pa-*` / `pa26-*` (2026 stacks).

## 4.2 Legacy (старые)

| Token | Происхождение | Использование (оценка) |
|-------|---------------|------------------------|
| `cream-*` | Phase 1 warm UI | ~120+ файлов |
| `graphite-*` | Phase 1 text | menu, profile, pantry |
| `sage-*` (old `#5E8B57`) | Заменён в config, но классы остались | mixed |
| `stone-*` | Pre-brand | ~45 файлов (settings, onboarding, admin) |
| `emerald-*` | Legacy nav CTA | BottomNavigation, auth |
| `.pa-card`, `.pa-btn-primary` | Legacy helpers | menu, shopping legacy |

## 4.3 Theme providers

| Файл | Статус |
|------|--------|
| `components/planam-2026/theme/ThemeProvider.tsx` | V1 + legacy Telegram bg |
| `components/TelegramProvider.tsx` | Shared; fallback `#fbf7ef` (2026) / `#f8fafc` (legacy) |

## 4.4 Противоречия V1

- V1 Vision требует свежесть и белый canvas — **достигнуто в 2026 shell**, но legacy embedded screens тянут cream/stone.
- `RecipeImage2026`, `MealFallbackPlate2026` всё ещё используют `bg-cream-deep`.
- Admin panel полностью на stone/emerald — **вне V1 scope**, но визуально другой продукт.

---

# ЧАСТЬ 5 — SHOPPING MODEL АУДИТ

## 5.1 V1 frontend (SoT)

| Файл | Роль |
|------|------|
| `lib/shopping/categories-v1.ts` | 15 канонических категорий; `продукты` **запрещён** |
| `lib/shopping/category-suggest.ts` | Классификатор + normalize |
| `lib/dom/shopping-groups.ts` | Группировка с normalize |

## 5.2 Backend (legacy drift)

| Файл | Проблема |
|------|----------|
| `api/app/services/shopping_category_service.py` | Seeds `продукты` как **первую** system category |
| `api/app/services/shopping_categories.py` | `FOOD_CATEGORIES` включает `продукты`; fallback infer → `продукты` |
| `api/app/models/pantry.py` | DB default `category='продукты'` |
| `api/app/schemas/pantry.py` | API default `продукты` |
| `api/app/services/pantry.py` | Fallback `продукты` |
| `api/app/database_migrations.py` | Column default `продукты` |

**Лишние backend categories vs V1:** `заморозка`, `сладости`, `бытовые`, `животные`, legacy slugs `овощи`, `мясо`, `рыба`, `молочное`, `крупы`, `хлеб`, `дом_и_химия`, `питомцы`, `фрукты` (без `_ягоды`).

## 5.3 Frontend legacy defaults

| Файл | Проблема |
|------|----------|
| `lib/pantry/types.ts`, `lib/pantry/api.ts` | default `продукты` |
| `components/pantry/PantryDashboard.tsx` | fallback `продукты` |
| `components/pantry/PantryItemForm.tsx` | fallback `продукты` |
| `components/recipes/FromPantrySection.tsx` | category `продукты` |

## 5.4 Tests / fixtures

| Файл | Статус |
|------|--------|
| `api/tests/test_shopping_infer_category.py` | Ожидает `продукты` — **противоречит V1** |
| `api/tests/test_shopping_category_service.py` | Создаёт rows `продукты` |
| `web/lib/shopping/category-suggest.test.ts` | V1 assertions ✅ |

## 5.5 DB

Таблица `shopping_categories` хранит slug из seed — в существующих БД **`продукты` уже есть** как system row. Frontend нормализует при отображении, но **запись в API может сохранять старый slug**.

---

# ЧАСТЬ 6 — RECIPE MODEL АУДИТ

## 6.1 Используется в V1

| Артефакт | Роль |
|----------|------|
| `api/app/models/recipe.py` | Core recipes table |
| `api/app/routers/recipes.py` | Catalog API |
| `api/app/routers/menus.py` | Menu generation |
| `components/recipes-2026/*` | V1 catalog/detail UI |
| `lib/recipes/recipe-media.ts` | Image variants (grid/hero/thumb) |

## 6.2 Seed / demo data

| Файл | Содержимое | Статус |
|------|------------|--------|
| `api/app/data/recipe_seed.py` | **15** hand-written recipes | Auto-seed if DB empty |
| `api/app/data/recipe_catalog_seed.py` | Programmatic catalog (~50+ recipes) | Fill if count < 50 |
| `api/app/services/recipes/catalog.py` | `seed_recipes_if_empty()` | **Active on API startup** |
| `scripts/seed_recipes.py` | Manual seed script | Ops tool |

**Качество:** catalog seed использует placeholder steps («Подготовьте продукты…») — **не готово для V1 Image Strategy** (реальные фото).

## 6.3 Recipe Engine (sub-features)

| Feature | Flag | Default | V1 relevance |
|---------|------|---------|--------------|
| `RECIPE_ENGINE_V1` | config | `false` | Search enhancements — **off** |
| `RECIPE_COLLECTIONS` | config | `true` | Collections — legacy `/menu/collections` |
| `RECIPE_HISTORY` | config | `true` | Cook history |
| `RECIPE_SCENARIOS` | config | `true` | Scenario chips — legacy UI |
| Tables: `recipe_collections`, `recipe_history`, `recipe_scenarios`, `recipe_explanations` | — | — | Engine tables |

## 6.4 Import pipeline

| Файл | Статус |
|------|--------|
| `backend/scripts/import_recipes.py` | Offline JSON importer — **готов для V2 import** |
| `api/app/models/recipe.py` → `recipe_import_jobs` | Schema only — **нет active router** |
| `backend/scripts/audit_recipe_*.py` | QA/enrichment scripts |

## 6.5 Legacy UI (не V1)

| Компонент | Route |
|-----------|-------|
| `RecipesView.tsx` | `/menu/recipes` (redirected) |
| `RecipeDetailLegacy.tsx` | `/recipes/[id]` (redirected) |
| `RecipeDetailModal.tsx` | Modal pattern — menu flow |
| `FavoritesView`, `CollectionsView` | No V1 pages yet |

## 6.6 Можно удалить (после миграции)

- Legacy recipe detail page (`RecipeDetailLegacy.tsx`) — после подтверждения redirect coverage
- Placeholder catalog seed — **не удалять до импорта реальных рецептов**
- `RecipeDetailModal` — после переноса всех entry points на V1 sheets

---

# ЧАСТЬ 7 — DATABASE АУДИТ

**Управление схемой:** `database.py` (`create_all`) + `database_migrations.py` (inline DDL). Alembic **нет**.

## 7.1 Используются (core V1)

| Таблица | V1 usage |
|---------|----------|
| `users`, `user_profiles`, `user_preferences` | Auth, onboarding, nutrition |
| `families`, `family_members`, `family_invites` | Family model |
| `family_menu_selections` | Plan/menu |
| `family_shopping_lists` | Shopping |
| `shopping_categories` | Categories ⚠️ legacy slugs |
| `family_pantry_items` | Pantry |
| `recipes`, `recipe_ingredients`, `recipe_steps`, `recipe_tags` | Catalog |
| `meal_checkins`, `meal_leftovers` | Today/outcomes |
| `meal_eating_schedules` | Schedules |
| `water_intake_logs` | Wellness water |
| `deferred_nutrition_advice` | Wellness insight |
| `user_subscriptions`, `subscription_plans` | Monetization |
| `user_notification_settings` | Notifications |

## 7.2 Используются (secondary / Sprint 2+)

| Таблица | Статус |
|---------|--------|
| `recipe_collections`, `collection_recipes` | Legacy collections — нет V1 page |
| `recipe_favorites` | Нет `/plan/favorites` |
| `recipe_history` | Backend only |
| `recipe_scenarios`, `recipe_explanations` | Engine — legacy UI |
| `family_recipe_preferences` | Per-member prefs |
| `progress_entries`, `training_entries`, `nutrition_targets` | Progress — нет V1 page |
| `event_plans` | `/menu/event` legacy |
| `care_settings`, `care_notifications`, `care_events` | Care — redirect to notifications |
| `ama_wallets`, `ama_transactions`, `ai_usage_logs` | AMS/billing |
| `telegram_bot_sessions` | Bot FSM |

## 7.3 Admin / ops

| Таблица | Статус |
|---------|--------|
| `admin_sessions`, `admin_login_attempts`, `admin_actions`, `admin_error_logs` | Admin panel |

## 7.4 Schema-only / low activity

| Таблица | Вердикт |
|---------|---------|
| `recipe_import_jobs` | **Оставить** — для будущего import |
| `recipe_ratings`, `recipe_allergens`, `recipe_restrictions` | **Оставить** — catalog metadata |

## 7.5 Удаление таблиц

| Вердикт | Таблицы |
|---------|---------|
| **Не удалять** | Все core tables — данные пользователей |
| **Удалить после релиза** | Нет кандидатов без миграции данных |
| **Неизвестно** | `care_*` — зависит от Sprint 2 notifications model |

---

# ЧАСТЬ 8 — API АУДИТ

## 8.1 Active (V1 critical path)

| Router | Prefix | V1 screens |
|--------|--------|------------|
| `auth.py` | `/auth` | Telegram login |
| `users.py` | `/users` | App context |
| `menus.py` | `/menus` | Plan, home overview |
| `meal_checkins.py` | `/meal-checkins` | Today outcomes |
| `shopping_lists.py` | `/shopping-lists` | Shopping |
| `shopping_categories.py` | `/shopping-categories` | Categories |
| `pantry.py` | `/pantry` | Pantry |
| `nutrition_profile.py` | `/nutrition-profile` | Account nutrition |
| `nutritionist.py` | `/nutritionist` | Wellness advice |
| `progress.py` | `/progress` | Wellness metrics |
| `recipes.py` | `/recipes` | Catalog |
| `subscriptions.py` | `/subscriptions` | Account subscription |
| `families.py` | `/families` | Account family |
| `notifications.py` | `/notifications` | Account notifications |
| `onboarding.py` | `/onboarding` | Onboarding |

## 8.2 Legacy / dual consumers

| Router | Legacy consumer | V1 consumer |
|--------|-----------------|-------------|
| `menus.py` | MenuHub, MenuPlanner | PlanWeek2026, Home2026 |
| `nutritionist.py` | NutritionistDashboard | WellnessHome2026 |
| `progress.py` | ProgressDashboard | Wellness (partial) |
| `recipes.py` | RecipesView | RecipeCatalog2026 |
| `care.py` | CareSettingsPanel | Minimal — redirect |

## 8.3 Deprecated patterns

| Pattern | Location |
|---------|----------|
| `продукты` category infer | `shopping_categories.py` |
| Legacy slug normalization server-side | Partial — client ahead of server |
| `recipe_engine_v1=false` | Gates enhanced search — not V1 blocker |

## 8.4 Feature flags (backend)

`apps/api/app/config.py`: `RECIPE_ENGINE_V1`, `RECIPE_COLLECTIONS`, `RECIPE_HISTORY`, `RECIPE_SCENARIOS`, `ADMIN_PANEL_ENABLED`, etc.

## 8.5 Feature flags (frontend)

| Flag | Default | Role |
|------|---------|------|
| `NEXT_PUBLIC_PLANAM_UI_2026` | false (true in prod Dockerfile) | Master UI |
| `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS` | false | Full legacy→V1 redirects |
| `NEXT_PUBLIC_PLANAM_DEFER_PHONE_GATE` | true | Phone gate timing |

---

# ЧАСТЬ 9 — TELEGRAM АУДИТ

## 9.1 V1 integrations

| Файл | Функция | Статус |
|------|---------|--------|
| `components/TelegramProvider.tsx` | initData auth, user, colorScheme | **Используется** |
| `lib/telegram-webapp.ts` | WebApp SDK loader, ThemeParams types | **Используется** |
| `useTelegramBackButton2026.ts` | BackButton show/hide/onClick | **V1** |
| `TelegramBackBridge2026.tsx` | Headless bridge in AppShell2026 | **V1** |
| `ScreenBack2026.tsx` | Fallback ← when no BackButton | **V1** |
| `lib/navigation/back-navigation-2026.ts` | returnTo logic | **V1** |
| `planam-2026/theme/ThemeProvider.tsx` | Reads themeParams.bg_color | **Гибрид** |

## 9.2 Legacy integrations

| Файл | Статус |
|------|--------|
| `layout/BottomBackButton.tsx` | **Не используется** |
| `layout/TopBackLink.tsx` | **Не используется** |
| `layout/ScreenBackNav.tsx` | Legacy screens |
| `TelegramAuthPanel.tsx` | Auth fallback (stone/emerald) |
| `OpenMiniAppButton.tsx` | Marketing helper |

## 9.3 Backend Telegram

| Файл | Роль |
|------|------|
| `routers/telegram_bot.py` | Webhook |
| `services/telegram_bot.py` | Update processing |
| `telegram/bot.py` | Menu button setup |
| `models/bot_session.py` | FSM sessions |

**Противоречие V1:** `TelegramProvider` fallback bg `#fbf7ef` — старый cream, не V1 white `#FFFFFF`.

---

# ЧАСТЬ 10 — V1 SOURCE OF TRUTH

## 10.1 Product documentation (единственный продуктовый SoT)

| Документ | Область |
|----------|---------|
| `PLANAM_V1_FINAL_VISION.md` | Hero, сценарии, принципы |
| `PLANAM_V1_RELEASE_BLUEPRINT.md` | Release scope, screens |
| `PLANAM_V1_PRODUCT_MASTER.md` | Index, backlog link |
| `PLANAM_V1_HOME_STATES.md` | Hero priority states |
| `PLANAM_V1_IMAGE_STRATEGY.md` | Recipe media |
| `PLANAM_V1_SHOPPING_MODEL_UPDATE.md` | Shopping categories |
| `PLANAM_COLOR_SYSTEM_V1.md` | Color tokens |

## 10.2 Code SoT (implementation)

| Область | SoT |
|---------|-----|
| UI shell | `AppShell2026`, `nav-config-2026.ts` |
| Home hero | `planam-hero-2026.ts`, `PlanAmHero2026.tsx` |
| Shopping categories (client) | `categories-v1.ts` |
| Plan routes | `lib/plan/plan-paths.ts` |
| Feature flags | `lib/planam/feature-flags.ts` |
| Design tokens | `globals.css` + `tailwind.config.ts` |

## 10.3 Не является SoT (устаревшие спеки)

- `docs/PLANAM_UX_UI_2026_MASTER_SPEC.md` — pre-V1 freeze, частично superseded
- `docs/PLANAM_DESIGN_SYSTEM_2026.md` — Phase 1 cream/sage
- `docs/UI_SYSTEM_AUDIT.md` — historical

---

# ЧАСТЬ 11 — LEGACY REMOVAL PLAN (summary)

Полный backlog: **`docs/PLANAM_LEGACY_REMOVAL_BACKLOG.md`**

| Timing | Examples |
|--------|----------|
| **Сразу** | Orphan home components, unused 2026 artifacts, deprecated nav aliases |
| **После Sprint 2** | `/menu/*` pages, `/health/*`, legacy shopping/pantry UI, backend `продукты` |
| **После релиза** | Dual flag system, legacy AppShell, recipe placeholder seeds |
| **Не удалять** | Shared API, DB tables, account embedded forms, TelegramProvider, admin |

---

# ЧАСТЬ 12 — FINAL SCORE

## 12.1 Процент V1

| Слой | V1 % | Комментарий |
|------|------|-------------|
| Production user journeys | **~60%** | 5-tab nav + home/plan/shopping/wellness/account |
| Frontend components | **~35%** | 199 TSX; ~76 в *-2026 dirs, но много hybrid |
| Frontend styles | **~45%** | pa/pa26 растут; cream/stone доминируют в legacy |
| Routes (accessible) | **~50%** | V1 primary + legacy still reachable |
| Shopping model | **~55%** | Client V1; server legacy |
| Recipe media | **~25%** | UI ready; seed data без фото |
| Backend API | **~80%** | Shared — не legacy, но category infer legacy |
| Database | **~90%** | Schema shared; не требует split |

**Итого проект:** ~**55% V1 / ~45% legacy-hybrid**

## 12.2 Самые опасные legacy зоны

1. **Dual UI flag** — один env var возвращает весь legacy product
2. **Reachable legacy routes** — `/menu`, `/health`, `/progress` без broad redirects
3. **Backend shopping `продукты`** — перезаписывает V1 нормализацию при записи
4. **Account embedded legacy** — визуальный и UX разрыв внутри V1 hub
5. **Placeholder recipe seeds** — блокируют Image Strategy

## 12.3 Что мешает Sprint 2

- Параллельные menu/plan codepaths
- Нет V1 pages для favorites/collections/progress
- Shopping backend не синхронизирован с `categories-v1.ts`
- Legacy components в account без V1 redesign
- Route migration неполная (broad redirects off)

---

# ФИНАЛЬНЫЙ ВЕРДИКТ

## Можно ли начинать очищать проект?

**Да — осторожно, слоями.** Production уже на V1 shell; orphan frontend и deprecated nav — безопасный первый шаг. Удаление routes и backend categories — только после Sprint 2 replacements.

## Что удалить первым

1. Orphan `components/home/*` (кроме PlanAmHome — пока flag off)
2. Unused `home-2026/*` exports (HomeHero, NextAction, AIInsight, etc.)
3. `BottomNav.tsx`, `BottomBackButton.tsx`, `TopBackLink.tsx`
4. `components/onboarding/` wizard (orphan)
5. `RoutePlaceholder2026`, `HomeMonetizationBanner2026`

## Что категорически нельзя трогать

1. `TelegramProvider`, auth flow, `api-client.ts`
2. `menus.py`, `shopping_lists.py`, core DB tables
3. `FamilyDashboard`, `NutritionProfileForm`, `NotificationSettingsForm` — до V1 replacement screens
4. `AppShellBridge` + feature flag — до полного cutover
5. `recipe_seed.py` / catalog — до импорта реальных рецептов с фото
6. Admin panel stack
7. Product docs V1 freeze set

---

*Аудит выполнен без изменений кода. См. `PLANAM_LEGACY_REMOVAL_BACKLOG.md` для приоритизированного плана удаления.*
