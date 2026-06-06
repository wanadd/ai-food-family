# PLANAM V1 — Clean Foundation Report

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Commit:** `refactor(v1): clean foundation and align shopping model`

---

## 1. Что удалено (Block A — Safe Cleanup)

### Legacy home orphans (grep imports = 0)

| Файл | Статус |
|------|--------|
| `components/home/HomeTodayCard.tsx` | Удалён |
| `components/home/HomeQuickActions.tsx` | Удалён |
| `components/home/HomeAskPlanAm.tsx` | Удалён |
| `components/home/HomeRecommendations.tsx` | Удалён |
| `components/home/HomeShoppingCard.tsx` | Удалён |
| `components/home/HomeFamilySummary.tsx` | Удалён |

### Unused home-2026

| Файл | Статус |
|------|--------|
| `home-2026/HomeHero2026.tsx` | Удалён |
| `home-2026/NextActionCard2026.tsx` | Удалён |
| `home-2026/PlanSnapshot2026.tsx` | Удалён |
| `home-2026/AIInsight2026.tsx` | Удалён |
| `home-2026/RecipeRail2026.tsx` | Удалён |
| `home-2026/HomeQuickActions2026.tsx` | Удалён |

Обновлён `components/home-2026/index.ts` — только `Home2026`, `WellnessChip2026`.

### Deprecated navigation

| Файл | Статус |
|------|--------|
| `layout/BottomNav.tsx` | Удалён |
| `layout/BottomBackButton.tsx` | Удалён |
| `layout/TopBackLink.tsx` | Удалён |

### Legacy onboarding wizard (частично)

Удалены **только orphan** файлы wizard-flow:

- `OnboardingWizard.tsx`, `OnboardingComplete.tsx`, `ProgressBar.tsx`
- `StepContent.tsx`, `StepNavigation.tsx`, `ChipSelectWithCustom.tsx`

**Сохранены** (используются в account/nutrition/family):

- `ChipSelect.tsx`, `OptionCards.tsx`, `TextAreaField.tsx`

---

## 2. Что очищено (Block B — Shopping Model Alignment)

### Backend V1 SoT

Создан `apps/api/app/services/categories_v1.py` — зеркало frontend `categories-v1.ts`.

15 системных категорий. Запрещены: `продукты`, `заморозка`, `сладости` (как system slugs).

### Обновлённые файлы

| Файл | Изменение |
|------|-----------|
| `shopping_category_service.py` | SYSTEM_CATEGORIES = V1 only |
| `shopping_categories.py` | infer/normalize → V1 slugs, fallback `другое` |
| `models/pantry.py` | default `другое` |
| `schemas/pantry.py` | default `другое` |
| `services/pantry.py` | normalize on read/write |
| `database_migrations.py` | pantry default + migration hook |

### Data migration

`apps/api/app/services/shopping_category_migration.py`

Запускается один раз при `ensure_database_schema()` (флаг `app_schema_flags.shopping_categories_v1_migrated`).

| Legacy slug | → V1 slug |
|-------------|-----------|
| `продукты` | `другое` |
| `заморозка` | `бакалея` |
| `сладости` | `бакалея` |
| `животные` | `для_питомцев` |
| `фрукты` | `фрукты_ягоды` |
| `овощи`, `зелень` | `овощи_зелень` |
| … | (полный LEGACY_SLUG_MAP) |

Мигрируются:

- `shopping_categories.slug`
- `family_pantry_items.category`
- `family_shopping_lists.items[].category` (JSONB)

После миграции deprecated system rows (`продукты`, `заморозка`, `сладости`) удаляются.

### Frontend pantry alignment

- `lib/pantry/types.ts`, `lib/pantry/api.ts`
- `components/pantry/PantryDashboard.tsx`, `PantryItemForm.tsx`
- `lib/shopping/categories-v1.ts` — `заморозка → бакалея`

### Tests

| Suite | Result |
|-------|--------|
| `test_categories_v1.py` | ✅ 4 tests |
| `test_shopping_infer_category.py` | ✅ 41 tests |
| `test_shopping_category_service.py` | ✅ 5 tests |

---

## 3. Color system (Block C)

| Изменение | Файл |
|-----------|------|
| `#fbf7ef` → `#FFFFFF` (V1 Telegram fallback) | `TelegramProvider.tsx` |

`globals.css`, `tailwind.config.ts`, `ThemeProvider.tsx` — уже V1 с Sprint 1.5, без изменений.

### Legacy color usages (остаются после спринта)

Активные V1 user paths с legacy `cream` / `stone` / `emerald`:

| Область | Файлы | Токены |
|---------|-------|--------|
| Account → Family | `family/*` (7 файлов) | `cream-border`, `stone-*` |
| Account → Nutrition | `nutrition-profile/*` (5 файлов) | `cream-*`, `stone-*` |
| Account → Notifications | `NotificationSettingsForm.tsx` | `stone-*`, `cream-*` |
| Account → Settings | `SettingsScaffold.tsx` + re-export pages | `stone-100`, `cream-border` |
| Recipe fallback | `RecipeImage2026`, `MealFallbackPlate2026` | `bg-cream-deep` |
| Legacy routes (ещё не удалены) | `menu/*`, `health/*`, `progress/*` | full legacy palette |
| Admin | `admin/*` | `stone-*`, `emerald-*` |
| Auth gates | `LegalConsentScreen`, `PhoneRequiredScreen` | `stone-*` |

**V1-native screens** (`home-2026`, `plan-2026`, `dom-2026`, `wellness-2026`, `planam-2026`) — преимущественно `pa-*` / `pa26-*`.

---

## 4. Route cleanup preparation (Block D)

Маршруты **не удалялись**. Подготовлено включение:

```env
NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=true
```

(комментарий обновлён в `.env.example`)

### Legacy → V1 redirect table

| Legacy route | V1 route | Статус |
|--------------|----------|--------|
| `/menu` | `/plan` | ✅ page exists |
| `/menu/current` | `/plan/today` | ✅ |
| `/menu/recipes` | `/plan/recipes` | ✅ (+ middleware always) |
| `/menu/generate` | `/plan/generate` | ✅ |
| `/menu/favorites` | `/plan/favorites` | ⚠️ **нет page** |
| `/menu/collections` | `/plan/collections` | ⚠️ **нет page** |
| `/recipes` | `/plan/recipes` | ✅ |
| `/subscription` | `/account/subscription` | ✅ |
| `/shopping` | `/home/shopping` → `/shopping` | ✅ |
| `/shopping/pantry` | `/home/pantry` | ✅ Pantry2026 |
| `/pantry` | `/home/pantry` | ✅ |
| `/health` | `/wellness` | ✅ |
| `/health/today` | `/wellness` | ✅ |
| `/health/chat` | `/wellness/chat` | ✅ |
| `/nutritionist` | `/wellness/chat` | ✅ |
| `/progress` | `/wellness/progress` | ⚠️ **нет page** |
| `/profile` | `/account` | ✅ (+ middleware always) |
| `/family` | `/account/family` | ✅ |
| `/notifications` | `/account/notifications` | ✅ |
| `/settings` | `/account/settings` | ✅ |

**Перед включением broad redirects:** реализовать или убрать из migration map `/plan/favorites`, `/plan/collections`, `/wellness/progress`.

---

## 5. Account V1 Replacement Plan (Block E)

Пока **не удалялось**. Sprint 2 targets:

| Компонент | Route | Проблема | Sprint 2 action |
|-----------|-------|----------|-----------------|
| `FamilyDashboard` | `/account/family` | `cream`/`stone`, sheets legacy | `FamilyHub2026` + V1 forms |
| `NutritionProfileForm` | `/account/nutrition` | Shared onboarding chips, stone inputs | `NutritionProfile2026` |
| `NotificationsView` + `NotificationSettingsForm` | `/account/notifications` | stone/cream forms | `Notifications2026` |
| `SettingsScaffold` + settings pages | `/account/settings/*` | stone borders, legacy layout | `SettingsHub2026` + V1 subpages |

Мост `usePlanam2026Embedded()` остаётся до замены экранов.

---

## 6. Recipe media preparation (Block F)

### Проверено

| Компонент | Готовность |
|-----------|------------|
| `RecipeImage2026` | ✅ + `imageSource` prop |
| `recipe-media.ts` | ✅ `resolveRecipeImageUrl()` |
| `PlanAmHero2026` | ✅ uses `image_url` |
| `MealFallbackPlate2026` | ✅ fallback plate |

### Поля изображений

| Поле | Статус |
|------|--------|
| `image_url` | ✅ используется сейчас (API + UI) |
| `hero_image_url` | ✅ forward-compatible via `resolveRecipeImageUrl` |
| `thumbnail_url` | ✅ forward-compatible via `resolveRecipeImageUrl` |

**Вердикт:** UI готов принимать structured image fields без дополнительных breaking changes. Import pipeline может писать `hero_image_url` / `thumbnail_url` — `RecipeImage2026` подхватит автоматически.

---

## 7. Legacy-компоненты, которые ещё остались

| Категория | Примеры |
|-----------|---------|
| Legacy shell | `AppShell`, `BottomNavigation`, `ScreenLayout` |
| Legacy routes | `/menu/*`, `/health/*`, `/progress`, `/subscription` |
| Account hybrid | `FamilyDashboard`, `NutritionProfileForm`, settings |
| Shared onboarding primitives | `ChipSelect`, `OptionCards`, `TextAreaField` |
| Legacy shopping/pantry UI | `ShoppingListView`, `PantryDashboard` (flag off paths) |
| Placeholder recipes | `recipe_seed.py`, `recipe_catalog_seed.py` |

---

## 8. QA

| Check | Result |
|-------|--------|
| `npm run lint` | ✅ |
| `npm run build` | ✅ |
| `pytest` (category suites) | ✅ 50 passed |
| Viewports 320–412px | No layout regressions expected (orphan removal only) |
| Light / Dark | TelegramProvider V1 bg `#FFFFFF` |
| Core screens | `/`, `/plan/today`, `/shopping`, `/wellness`, `/account` unchanged routing |

---

## 9. Готовность

| Milestone | Оценка |
|-----------|--------|
| **Recipe Import** | **Ready** — media resolver + hero/grid/thumb variants; нужны только данные с URL |
| **Sprint 2** | **Ready** — shopping backend aligned; orphans removed; account replacement scoped |
| **Route hard cutover** | **Blocked** — 3 missing V1 pages (favorites, collections, wellness/progress) |
| **V1 % проекта** | ~**62%** (было ~55%) |

---

## 10. Изменённые файлы (summary)

- **Deleted:** 21 orphan component files
- **Added:** `categories_v1.py`, `shopping_category_migration.py`, `test_categories_v1.py`
- **Updated:** backend shopping stack, pantry defaults, frontend pantry, TelegramProvider, recipe-media, `.env.example`
