# PLANAM 2026 — Color Fix Report

**Дата:** 2026-06-03  
**Задача:** при `NEXT_PUBLIC_PLANAM_UI_2026=true` реальные маршруты должны использовать cream/sage/graphite (как `/dev/planam-2026`), без legacy emerald/stone и без «белого Telegram».

---

## Диагностика

| Слой | Проблема |
|------|----------|
| `theme-document.ts` | В Telegram `themeParams.bg_color` перезаписывал `--pa-bg-canvas` / `--pa-bg-surface` → белый/серый вместо cream |
| `layout.tsx` + `globals.css` | `body` всегда `bg-cream text-graphite-900`; scope 2026 не переключал фон на `pa-*` |
| `ThemeProvider` | Не было `data-planam-ui="2026"` на `html`; тема применялась в `useEffect` (поздно) |
| `AppShellBridge` | Dev preview / onboarding не получали scope 2026 без production flag |
| `ToastProvider` | Toast `bg-stone-900` на всех маршрутах |
| 2026 components | `dark:hover:bg-white/5` — холодный legacy hover в dark mode |
| Встроенные `.pa-*` | `NutritionistChat` и др. используют legacy helpers с `cream-*` вместо semantic tokens |

**Не затронуто (по дизайну):** legacy shell (`flag=false`), `/settings`, `/admin` — stone/emerald сохранены.

---

## Исправления

1. **`data-planam-ui="2026"`** — scope на `html` при активном 2026 shell / dev preview / onboarding (`lib/planam/ui-scope.ts`, `theme-document.ts`, `ThemeProvider scope2026`).
2. **Отключены Telegram overrides** для 2026: brand canvas/surface из DS, не из `themeParams`.
3. **`globals.css`** — body и remapped `.pa-*` под scope 2026; utility `.pa26-hover-row`.
4. **`ThemeProvider`** — `useLayoutEffect` + `color-scheme`; `scope2026` prop.
5. **`AppShellBridge`** — `scope2026` для dev, onboarding, production 2026 shell.
6. **`TelegramProvider`** — fallback `#fbf7ef` вместо `#f8fafc` при UI_2026.
7. **`ToastProvider`** — graphite/cream toast при UI_2026.
8. **Hover states** — `dark:hover:bg-white/5` → `pa-elevated` в planam-2026 / dom / plan / recipes.

---

## Изменённые файлы

- `apps/web/app/globals.css`
- `apps/web/app/layout.tsx`
- `apps/web/lib/planam/ui-scope.ts` *(новый)*
- `apps/web/lib/planam/theme-document.ts`
- `apps/web/components/planam-2026/theme/ThemeProvider.tsx`
- `apps/web/components/layout/AppShellBridge.tsx`
- `apps/web/components/TelegramProvider.tsx`
- `apps/web/components/ui/ToastProvider.tsx`
- `apps/web/components/planam-2026/ui/Button2026.tsx`
- `apps/web/components/planam-2026/navigation/BottomNavigation2026.tsx`
- `apps/web/components/planam-2026/cards/ActionCard2026.tsx`
- `apps/web/components/planam-2026/theme/ThemeToggle2026.tsx`
- `apps/web/components/planam-2026/ui/BottomSheet2026.tsx`
- `apps/web/components/dom-2026/MealOutcomeSheet2026.tsx`
- `apps/web/components/plan-2026/ReplaceDishSheet2026.tsx`
- `apps/web/components/recipes-2026/MenuSlotSheet2026.tsx`
- `apps/web/components/onboarding-2026/OnboardingChipGrid2026.tsx`

---

## QA

| Проверка | Результат |
|----------|-----------|
| `npm run lint` | ✅ (1 pre-existing warning в `ProfileDashboard.tsx`) |
| `npm run build` | ✅ |
| Light / Dark / System | ✅ через `ThemeProvider` + `html.dark` + CSS variables |
| `flag=false` | ✅ legacy body `cream/graphite`, scope не ставится |
| `/dev/planam-2026` | ✅ `scope2026` без production flag |

### Ручной smoke (рекомендуется)

С `NEXT_PUBLIC_PLANAM_UI_2026=true` в Telegram и браузере:

- `/` (Home), `/plan/today`, `/plan/recipes`, `/home/shopping`, `/home/pantry`, `/wellness`, `/account`
- Переключить Light → Dark → System в Account (когда подключён `ThemeToggle2026`)
- Сравнить фон с `/dev/planam-2026` — должен совпадать cream/sage/graphite

---

## Остаточные заметки

- `WellnessDayRing2026` / `WellnessChip2026` — inline `conic-gradient` с hex близкими к sage/cream (не emerald).
- `NutritionistChat` в `/wellness/chat` — через scoped `.pa-*` remapping; полный рефактор компонента не делался.
- Legacy routes при `flag=true` (`/settings/*`) остаются на старой палитре — ожидаемо до Strangler-миграции.
