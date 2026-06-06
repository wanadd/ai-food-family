# PLANAM — каталог компонентов

Дата: 2026-06-03

---

## Навигация

| Компонент | Путь | Где используется | Варианты |
|-----------|------|------------------|----------|
| `BottomNavigation2026` | planam-2026/navigation | `AppShell2026` | 1 (4 tabs) |
| `BottomNavigation` | layout | `AppShell` legacy | 1 (5 tabs) |
| `SectionSubTabs2026` | planam-2026/navigation | `AppShell2026` | plan chips only |
| `SegmentedTabs` | layout | legacy menu/shopping sections | generic |
| `ShellHeader2026` | planam-2026/layout | `AppShell2026` | conditional hide |
| `ScreenBack2026` | planam-2026/navigation | ShellHeader | 1 |
| `NavIcon2026` | planam-2026/navigation | BottomNav, AccountHub, cards | 15+ icon ids |
| `ScreenLayout` | layout | legacy pages | title + back + footer |
| `ScreenBackNav` | layout | legacy nested | 1 |

---

## Карточки — UI 2026

| Компонент | Путь | Экраны | Варианты |
|-----------|------|--------|----------|
| `Card2026` | planam-2026/ui | account, wellness, plan | 1 base |
| `ActionCard2026` | planam-2026/cards | AccountHub | icon + title + caption |
| `HeroCard2026` | planam-2026/cards | HomeHero | meal hero |
| `MetricCard2026` | planam-2026/cards | recipe detail | 2×2 grid |
| `InsightCard2026` | planam-2026/cards | — (exported) | 1 |
| `PlanMealCard2026` | plan-2026 | PlanToday | per meal |
| `RecipeGridCard2026` | recipes-2026 | RecipeCatalog | grid + replace mode |
| `WellnessDayRing2026` | wellness-2026 | Wellness | ring progress |
| `WellnessTodayCard2026` | wellness-2026 | Wellness | metrics |
| `WellnessGoalCard2026` | wellness-2026 | Wellness | goal |
| `WellnessWeekStrip2026` | wellness-2026 | Wellness | 7 days |
| `PlanCard2026` | monetization-2026 | Subscription | per plan tier |

---

## Карточки — Legacy

| Компонент | Путь | Экраны |
|-----------|------|--------|
| `HubTile` | ui | MenuHub |
| `MemberCard` | family | FamilyDashboard |
| `PantryItemCard` | pantry | PantryDashboard |
| `MenuVariantCard` | menu | MenuPlanner |
| `RecipeCard` (inline in views) | recipes | RecipesView, Favorites |

---

## Кнопки и UI primitives

| Компонент | Путь | Использование |
|-----------|------|---------------|
| `Button2026` | planam-2026/ui | все 2026 экраны |
| `EmptyState2026` | planam-2026/ui | error/empty states |
| `Skeleton2026` | planam-2026/ui | loading |
| `BottomSheet2026` | planam-2026/ui | 5 sheets |
| `ThemeToggle2026` | planam-2026/theme | AccountHub |
| `ToastProvider` | ui | app-wide |
| `Sheet` | ui | legacy sheets |
| `ChipSelect` | onboarding | nutrition form, onboarding |

---

## Экранные контейнеры (2026)

| Компонент | Путь | Route(s) |
|-----------|------|----------|
| `Home2026` | home-2026 | `/` |
| `PlanToday2026` | plan-2026 | `/plan/today` |
| `PlanWeek2026` | plan-2026 | `/plan` |
| `PlanGenerate2026` | plan-2026 | `/plan/generate` |
| `RecipeCatalog2026` | recipes-2026 | `/plan/recipes` |
| `RecipeDetail2026` | recipes-2026 | `/plan/recipes/[id]` |
| `Shopping2026` | dom-2026 | `/home/shopping` |
| `Pantry2026` | dom-2026 | `/home/pantry` |
| `WellnessHome2026` | wellness-2026 | `/wellness` |
| `WellnessChat2026` | wellness-2026 | `/wellness/chat` |
| `AccountHub2026` | planam-2026/account | `/account` |
| `SubscriptionHub2026` | monetization-2026 | `/account/subscription` |
| `PaymentStub2026` | monetization-2026 | checkout |
| `AmsHub2026` | monetization-2026 | `/account/ams` |
| `Onboarding2026Flow` | onboarding-2026 | `/onboarding` |

---

## Экранные контейнеры (Legacy)

| Компонент | Route(s) |
|-----------|----------|
| `PlanAmHome` | `/` (legacy) |
| `MenuHub` | `/menu` |
| `MenuCurrentView` | `/menu/current` |
| `MenuPlanner` | `/menu/generate` |
| `RecipesView` | `/menu/recipes` |
| `ShoppingListView` | `/shopping` |
| `PantryDashboard` | `/shopping/pantry` |
| `ProfileDashboard` | `/profile` |
| `NutritionistDashboard` | `/health` |
| `HealthTodayView` | `/health/today` |
| `ProgressDashboard` | `/progress` |
| `FamilyDashboard` | `/family`, `/account/family` |
| `NotificationsView` | `/notifications`, `/account/notifications` |
| `SubscriptionDashboard` | `/subscription` |
| `AdminDashboard` | `/admin/*` |

---

## Overlays (см. OVERLAYS.md)

| Тип | Count |
|-----|-------|
| Sheets | 15 |
| Modals | 2 |
| Dialogs | 2 |
| Toast | 1 |

---

## Providers (контекст)

| Provider | Данные/функция |
|----------|----------------|
| `TelegramProvider` | auth, user |
| `AppModeProvider` | personal/family mode |
| `SubscriptionProvider` | subscription overview |
| `PaywallProvider` | paywall sheet |
| `ThemeProvider` | light/dark/system |
| `ToastProvider` | notifications |

---

## Сводка

| Категория | Количество основных компонентов |
|-----------|--------------------------------|
| Navigation | 9 |
| Cards 2026 | 12 |
| Cards legacy | 5+ |
| UI primitives 2026 | 6 |
| Screen containers 2026 | 15 |
| Screen containers legacy | 15+ |
| Overlays | 20 |
| Providers | 6 |
| **Итого уникальных пользовательских компонентов (верхний уровень)** | **~88** |
