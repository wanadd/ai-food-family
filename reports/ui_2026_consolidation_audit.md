# PLANAM V1 — Frontend 2026 UI consolidation audit

Companion to `reports/planam_project_consolidation_audit.md`. Focus: app shell,
bottom navigation, 2026 vs legacy components, design tokens, mobile Telegram
Mini App ergonomics.

---

## 1. Единый shell

Выбор shell — `components/layout/AppShellBridge.tsx`:

| условие | shell | bottom nav | header |
|---------|-------|------------|--------|
| `/dev/planam-2026*`, `/onboarding*` | plain `div` + 2026 theme | нет | нет |
| `NEXT_PUBLIC_PLANAM_UI_2026=true` | `AppShell2026` | `BottomNavigation2026` | `ShellHeader2026` (скрыт на immersive) |
| иначе (legacy) | `AppShell` | `BottomNavigation` | — |
| `/admin*` | `AdminShell` (внутри AppProviders) | скрыт | свой top-nav |

**Действие:** prod использует `NEXT_PUBLIC_PLANAM_UI_2026=true` → все основные
экраны идут через `AppShell2026`. Legacy `AppShell`/`BottomNavigation` —
fallback под выключенным флагом, кандидаты V2.

---

## 2. Bottom navigation — не ведёт на deprecated routes

`NAV_TABS_2026` (`nav-config-2026.ts`): `/plan/today` · `/shopping` · `/`
(центр) · `/wellness` · `/account`. Все 5 — **ACTIVE_2026**, ни одного
deprecated. Подтаб-навигация плана: `/plan`, `/plan/today`, `/plan/recipes`.

Legacy `NAV_TABS` (`nav-config.ts`) ведёт на `/menu`, `/health`, `/profile`
(deprecated) — используется только legacy shell под выключенным флагом.

**Действие:** канонический реестр путей зафиксирован в
`apps/web/lib/planam/routes.ts` (`PLANAM_ROUTES`), чтобы компоненты не
хардкодили старые пути.

---

## 3. Экраны → 2026-компоненты

| экран | 2026-компонент | legacy (под флагом / V2) |
|-------|----------------|--------------------------|
| App shell | `planam-2026/layout/AppShell2026` | `layout/AppShell` |
| Bottom nav | `planam-2026/navigation/BottomNavigation2026` | `layout/BottomNavigation` |
| Home | `home-2026/Home2026` | `home/PlanAmHome` |
| Plan Today | `plan-2026/PlanToday2026` | `menu/MenuCurrentView` |
| Plan Week / Generate | `plan-2026/PlanWeek2026`, `PlanGenerate2026` | `menu/MenuHub`, `MenuPlanner` |
| Recipes | `recipes-2026/RecipeCatalog2026`, `RecipeDetail2026`, `RecipeGridCard2026` | `recipes/RecipesView`, `RecipeCard` |
| Shopping | `dom-2026/Shopping2026` | `shopping/ShoppingListView` |
| Pantry | `dom-2026/Pantry2026` | `pantry/PantryDashboard` |
| Leftovers | `dom-2026/Leftovers2026` | `menu/MealLeftoversPage` |
| Wellness / Nutritionist | `wellness-2026/WellnessHome2026`, `WellnessChat2026` | `nutritionist/NutritionistDashboard`, `HealthTodayView` |
| Notifications | `NotificationsView` (shared) | — |
| Account / Profile | `planam-2026/account/AccountHub2026` | `profile/ProfileDashboard` |
| Subscription | `monetization-2026/SubscriptionHub2026` | `subscription/SubscriptionDashboard` |

**Shared (не дубль, используются обоими):** `FamilyDashboard`,
`NotificationsView`, `NutritionProfileForm`, `SettingsScaffold`.

---

## 4. Дизайн-токены / UI-примитивы

Единые примитивы — `components/planam-2026/ui/`: `Button2026`, `Card2026`,
`EmptyState2026`, `Skeleton2026`, `BottomSheet2026` (+ `ActionCard2026`,
`HeroCard2026`, `InsightCard2026`, `MetricCard2026`, `ThemeToggle2026`).
Тема — `lib/planam/theme.ts` / `theme-document.ts` / `ui-scope.ts`.

**Действие (V2):** заменить остаточные старые цвета/карточки в legacy
компонентах на токены; новые экраны обязаны использовать `*2026` примитивы.

---

## 5. Mobile Telegram Mini App ergonomics

- Категории/блоки свёрнуты по умолчанию (Shopping: авто-раскрытие только при
  активном поиске — внедрено в `dom-2026/Shopping2026`).
- Bottom nav thumb-friendly (5 вкладок, центр — ПланАм).
- Immersive recipe detail (`/plan/recipes/[id]`) — full-bleed hero, без header.
- Минимум скролла: hub-страницы (`AccountHub2026`, `WellnessHome2026`) —
  компактные списки.

---

## 6. Задачи / статусы

1. Единый shell для всех основных страниц — **да** (`AppShell2026` под флагом prod).
2. Bottom nav не ведёт на deprecated — **да**.
3. Кнопки/карточки используют 2026-компоненты — **да** на canonical экранах.
4. Старые цвета → токены — **частично**; остаток в legacy → V2.
5. Дубли компонентов отмечены — **да** (раздел 3).
6. Пустые старые страницы redirect/delete later — **да** (redirect есть).
7. Mobile-эргономика — **базово готова** (свёрнутые блоки, thumb nav).

---

## 7. UI legacy candidates (Legacy Cleanup V2)

- `components/home/PlanAmHome.tsx`
- `components/layout/{AppShell,BottomNavigation,BottomBackButton,TopBackLink}.tsx`
- `lib/navigation/nav-config.ts`
- `components/profile/ProfileDashboard.tsx`
- `components/menu/{MenuHub,MenuCurrentView,MenuPlanner,MenuVariantCard,MealLeftoversPage}.tsx`
- `components/recipes/{RecipesView,RecipeCard}.tsx`
- `components/shopping/ShoppingListView.tsx`
- `components/pantry/PantryDashboard.tsx`
- `components/nutritionist/{NutritionistDashboard,HealthTodayView}.tsx`
- `components/subscription/SubscriptionDashboard.tsx`

Удалять только после выключения legacy-fallback (флаг `NEXT_PUBLIC_PLANAM_UI_2026`
постоянно on в prod) и grep/import-check/build.
