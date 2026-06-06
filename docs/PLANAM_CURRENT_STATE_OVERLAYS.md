# PLANAM — модалки, sheets, dialogs

Дата: 2026-06-03

## Базовые примитивы

| Компонент | Путь | Тип |
|-----------|------|-----|
| `Sheet` | `components/ui/Sheet.tsx` | Bottom sheet (legacy design) |
| `BottomSheet2026` | `components/planam-2026/ui/BottomSheet2026.tsx` | Bottom sheet (2026 design) |

**Drawer:** не используется в коде.

---

## Инвентарь overlays (20 компонентов)

### Sheets (legacy `Sheet`)

| # | Компонент | Вызывается из | Когда открывается | Что делает | Как закрывается | После закрытия |
|---|-----------|---------------|-------------------|------------|-----------------|----------------|
| 1 | `ShoppingItemSheet` | `ShoppingListView` | «+ Добавить», edit item, `?add=` | Форма позиции покупок | Backdrop / «Закрыть» / save | Parent clears state; save → list reload |
| 2 | `ShoppingCategorySheet` | `ShoppingListView` | «+ Категория» | Создание категории | Backdrop / save | Category list refresh |
| 3 | `PantryItemForm` | `PantryDashboard` | Add / edit pantry | CRUD запасов | Backdrop / save | List refresh |
| 4 | `MenuQuickActionsSheet` | `MenuHub` | «Настроить меню» | Grid quick actions | Backdrop / pick action | Opens `AmaConfirmDialog` |
| 5 | `RecipeFiltersSheet` | `RecipesView` | «Фильтры» | Filter chips | «Готово» / backdrop | URL query updated |
| 6 | `ScenarioChips` (embedded) | `RecipesView` | «Ещё» scenarios | Extra scenario chips | Backdrop / select | Chip applied |
| 7 | `MenuDayOverview` (embedded) | `MenuCurrentView` | Tap meal row | Meal detail | Backdrop / links | Navigate or replace |

### Sheets (2026 `BottomSheet2026`)

| # | Компонент | Вызывается из | Когда | Что делает | Закрытие | После |
|---|-----------|---------------|-------|------------|----------|-------|
| 8 | `LeftoversSheet2026` | `Home2026` | Quick «Остатки» | List leftovers, consume, recipes | Backdrop / «Закрыть» | State `leftoversOpen=false` |
| 9 | `MealOutcomeSheet2026` | `Home2026`, `PlanToday2026` | outcome CTA, `?outcome=1`, cook | Multi-step meal checkin | Backdrop / «Готово» | Cache invalidate, reload |
| 10 | `ReplaceDishSheet2026` | `PlanToday2026`, `RecipeDetail2026` | Replace CTA, `?replace=1` | Pick meal → AMA → AI replace | Backdrop / success | Navigate/reload plan |
| 11 | `MenuSlotSheet2026` | `RecipeDetail2026` | «В меню» | Date/meal/servings picker | Backdrop / submit | Navigate `/plan/today?saved=1` |
| 12 | `PaywallSheet2026` | `PaywallProvider` (global) | Insufficient AMA | Upgrade CTAs | Backdrop / CTA | `closePaywall()` or navigate checkout |

### Custom sheets (не используют примитив)

| # | Компонент | Вызывается из | Когда | Что делает | Закрытие | После |
|---|-----------|---------------|-------|------------|----------|-------|
| 13 | `AddPersonSheet` | `FamilyDashboard` | Add member | Invite vs virtual choice | Backdrop / cancel / pick | Chain to InviteSheet or form |
| 14 | `InviteSheet` | `FamilyDashboard` | From AddPerson | Phone/link invite | Header «Закрыть» | `lastInvite` set |
| 15 | `FamilyManageSheet` | `FamilyDashboard` | «Управление семьёй» | Rename/delete/leave/transfer | Header close / success | Family reload |

### Modals

| # | Компонент | Вызывается из | Когда | Что делает | Закрытие | После |
|---|-----------|---------------|-------|------------|----------|-------|
| 16 | `ReplaceDishModal` | `MenuCurrentView` | `?replace=1` | Pick meal to replace | «Отмена» | Opens AMA dialog |
| 17 | `RecipeDetailModal` | `RecipeDetailLegacy` | Page load | Full-screen recipe (legacy) | ✕ → `/menu/recipes` | Navigate away |

### Dialogs

| # | Компонент | Вызывается из | Когда | Что делает | Закрытие | После |
|---|-----------|---------------|-------|------------|----------|-------|
| 18 | `AmaConfirmDialog` | MenuHub, MenuCurrent, ReplaceDishSheet, RecipeDetailModal, NutritionistChat, WellnessChat | Before AMA spend | Confirm cost | «Передумал» | Clear pending; or execute API |
| 19 | `AdminConfirmDialog` | Admin user/family detail | Destructive admin actions | Inline confirm | «Отмена» | API action |

### Toast (не modal, но overlay feedback)

| # | Компонент | Где | Когда |
|---|-----------|-----|-------|
| 20 | `ToastProvider` | App-wide | API success/error messages |

---

## Глобальные overlay-провайдеры

| Провайдер | Файл | Overlay |
|-----------|------|---------|
| `PaywallProvider` | `monetization-2026/PaywallProvider.tsx` | `PaywallSheet2026` |
| `ToastProvider` | `ui/ToastProvider.tsx` | Toast notifications |

---

## Сводка

| Тип | Количество |
|-----|------------|
| Sheet (legacy primitive usages) | 7 |
| BottomSheet2026 wrappers | 5 |
| Custom family sheets | 3 |
| Modal | 2 |
| Dialog | 2 |
| Toast | 1 |
| **Всего overlay-компонентов** | **20** |
