# PLANAM — инвентаризация данных по экранам

Дата: 2026-06-03  
Источник API: `apps/web/lib/**/api.ts` (23 модуля).

---

## Глобальные данные (app-wide)

| Данные | API | Провайдер | Реальные / мок |
|--------|-----|-----------|----------------|
| Telegram auth | `POST /auth/telegram` | `TelegramProvider` | реальные (Telegram initData) |
| Dev login | `POST /auth/dev-login` | `TelegramProvider` (dev) | реальные в dev |
| App context (personal/family) | `GET/PATCH /users/me/app-context` | `AppModeProvider` | реальные |
| Subscription overview | `GET /subscriptions/me` | `SubscriptionProvider` | реальные |
| Legal consent | `GET /legal/documents`, `POST /legal/accept` | gate screens | реальные |

---

## По экранам UI 2026

### `/` — Home2026

| Данные | API endpoint | Заглушки |
|--------|--------------|----------|
| Menu overview (hero, next action, insight) | `GET /menus/overview` | Skeleton при loading |
| Subscription banner | `GET /subscriptions/me` | null если нет данных |
| User greeting | Telegram `user` object | — |
| Family scope label | `app-context` | — |

### `/plan/today` — PlanToday2026

| Данные | API | Заглушки |
|--------|-----|----------|
| Selected menu variant | `GET /menus/selected` | EmptyState если null |
| Meal checkins today | `GET /meal-checkins/today` | — |
| Menu overview (images) | `GET /menus/overview` | optional catch |

### `/plan` — PlanWeek2026

| Данные | API | Заглушки |
|--------|-----|----------|
| Selected menu | `GET /menus/selected` | Empty state |

### `/plan/generate` — PlanGenerate2026

| Данные | API | Заглушки |
|--------|-----|----------|
| Nutrition profile | `GET /nutrition-profile/me` | defaults |
| Pantry items | `GET /pantry/me` | empty list |
| Generated variants | `POST /menus/generate` | loading state |
| Select result | `POST /menus/select` | — |

### `/plan/recipes` — RecipeCatalog2026

| Данные | API | Заглушки |
|--------|-----|----------|
| Recipe list | `GET /recipes?q&meal_type&...` | EmptyState |
| Filters metadata | `GET /recipes/filters` | — |

### `/plan/recipes/[id]` — RecipeDetail2026

| Данные | API | Заглушки |
|--------|-----|----------|
| Recipe detail | `GET /recipes/{id}` | EmptyState error |
| Selected menu (for slot sheet) | `GET /menus/selected` | — |
| Favorite state | in recipe object | — |

### `/home/shopping` — Shopping2026

| Данные | API | Заглушки |
|--------|-----|----------|
| Shopping list | `GET /shopping-lists/me` | Empty → CTA home |
| Categories | `GET /shopping-categories` | fallback labels in `labels.ts` |
| Sync | `POST /shopping-lists/sync` | — |

### `/home/pantry` — Pantry2026

| Данные | API | Заглушки |
|--------|-----|----------|
| Pantry items | `GET /pantry/me` | EmptyState |
| Categories | `GET /shopping-categories` | — |

### `/wellness` — WellnessHome2026

| Данные | API | Заглушки |
|--------|-----|----------|
| Menu overview | `GET /menus/overview` | — |
| Progress overview | `GET /progress/me` | — |
| Nutrition profile | `GET /nutrition-profile/me` | empty → setup CTA |
| Water today | `GET /nutritionist/water/today` | — |
| Meal checkins | `GET /meal-checkins/today` | — |
| Progress history | `GET /progress/history` | week strip |

### `/wellness/chat` — WellnessChat2026

| Данные | API | Заглушки |
|--------|-----|----------|
| Chat messages | local state + `POST /nutritionist/ask` | welcome prompt |
| AMA balance | `GET /subscriptions/me` | via confirm dialog |

### `/account` — AccountHub2026

| Данные | API | Заглушки |
|--------|-----|----------|
| User (name, avatar) | Telegram provider | placeholder card |
| Theme | localStorage | — |

### `/account/nutrition` — NutritionProfileForm

| Данные | API | Заглушки |
|--------|-----|----------|
| Profile | `GET /nutrition-profile/me` | `INITIAL_NUTRITION_PROFILE` |
| Family allow-admin | `GET /families/me` | — |
| Save | `PUT /nutrition-profile/me` | — |

### `/account/family` — FamilyDashboard

| Данные | API | Заглушки |
|--------|-----|----------|
| Family | `GET /families/me` | create form if null |
| Invites | `POST .../invites/link`, `invite-by-phone` | — |
| Members CRUD | family API | — |

### `/account/notifications` — NotificationsView

| Данные | API | Заглушки |
|--------|-----|----------|
| Notification settings | `GET/PUT /notifications/settings` | — |
| Care settings | `GET/PATCH /care/settings` | — |

### `/account/subscription` — SubscriptionHub2026

| Данные | API | Заглушки |
|--------|-----|----------|
| Overview, plans | `GET /subscriptions/me` | Skeleton / Offline |
| Plan catalog display | `PLAN_CATALOG_2026` (static) + API plans | merged |
| Select plan | `POST /subscriptions/select-plan` | — |

### `/account/subscription/checkout` — PaymentStub2026

| Данные | API | Заглушки |
|--------|-----|----------|
| Checkout | stub UI | **заглушка** (не реальная оплата) |
| returnTo | query param | — |

### `/account/ams` — AmsHub2026

| Данные | API | Заглушки |
|--------|-----|----------|
| AMA balance | `GET /subscriptions/me` | — |

---

## Legacy экраны (ключевые)

### `/shopping` — ShoppingListView

| Данные | API |
|--------|-----|
| Shopping list + CRUD | `/shopping-lists/*`, `/shopping-categories` |

### `/menu` — MenuHub

| Данные | API |
|--------|-----|
| Overview | `/menus/overview` |
| Quick actions | `/menus/quick-action` |

### `/menu/current` — MenuCurrentView

| Данные | API |
|--------|-----|
| Selected menu | `/menus/selected` |
| Replace | `/menus/replace-dish` |
| Checkins | `/meal-checkins/*` |

### `/profile` — ProfileDashboard

| Данные | API |
|--------|-----|
| Nutrition summary | `/nutrition-profile/me` |
| User | Telegram |

### `/progress` — ProgressDashboard

| Данные | API |
|--------|-----|
| Overview, history, entries | `/progress/*` |

---

## API modules — полный список (23)

| Модуль | Endpoints (сводка) |
|--------|-------------------|
| `lib/api.ts` | `/auth/*` |
| `lib/app-mode/api.ts` | `/users/me/app-context` |
| `lib/admin/api.ts` | `/admin/*` |
| `lib/care/api.ts` | `/care/*` |
| `lib/event-plan/api.ts` | `/event-plans/*` |
| `lib/family/api.ts` | `/families/*` |
| `lib/legal/api.ts` | `/legal/*` |
| `lib/meal-checkins/api.ts` | `/meal-checkins/*` |
| `lib/meal-leftovers/api.ts` | `/meal-leftovers/*` |
| `lib/menu/api.ts` | `/menus/*` |
| `lib/menu/overview-api.ts` | `/menus/overview`, `/menus/quick-action` |
| `lib/notifications/api.ts` | `/notifications/settings` |
| `lib/nutrition-profile/api.ts` | `/nutrition-profile/me` |
| `lib/nutritionist/api.ts` | `/nutritionist/ask` |
| `lib/nutritionist/deferred-advice-api.ts` | `/nutritionist/deferred-advice/*` |
| `lib/onboarding/api.ts` | `/onboarding/me` (dormant) |
| `lib/pantry/api.ts` | `/pantry/*` |
| `lib/progress/api.ts` | `/progress/*` |
| `lib/recipes/api.ts` | `/recipes/*`, `/collections/*` |
| `lib/recipes/analysis-api.ts` | `/recipes/{id}/evaluate`, `add-to-menu`, etc. |
| `lib/shopping/api.ts` | `/shopping-lists/*`, `/shopping-categories` |
| `lib/subscription/api.ts` | `/subscriptions/*` |
| `lib/water-intake/api.ts` | `/nutritionist/water/*` |

**Всего уникальных API path prefixes:** ~45

---

## Заглушки и моки (факты)

| Место | Тип |
|-------|-----|
| `PaymentStub2026` | UI stub checkout |
| `PLAN_CATALOG_2026` | Static plan metadata merged with API |
| `category-suggest.ts` | Client-side heuristic (не API) |
| `FALLBACK_META` in `labels.ts` | Fallback emoji/labels |
| `Skeleton2026` / `Skeleton` | Loading placeholders |
| `EmptyState2026` | Empty placeholders |
| `OnboardingWizard` + `onboarding/api.ts` | Dormant (не в active routes 2026) |
| Dev login | `authenticateDevLogin` for non-Telegram dev |

---

## Кэширование (session)

`lib/cache/session-cache.ts` — in-memory cache keys:

- `menuOverview(mode)`
- `selectedMenu(mode)`
- `shopping-list(mode)`
- `pantry(mode)`
- `progressOverview(mode)`

Используется на: Home, Plan Today, Wellness, Shopping.
