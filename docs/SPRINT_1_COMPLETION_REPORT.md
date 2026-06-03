# Sprint 1 — Completion Report (PLANAM 2026 Design System)

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Спринт:** Design System 2026 + Theme Engine + UI Primitives + Shell Foundation

---

## Цель спринта

Реализовать Design System 2026, Theme Engine и базовые UI primitives **без** переписывания старого приложения, без изменений БД/API и без влияния на production при выключенном feature flag.

**Критерии готовности:** выполнены (см. §7).

---

## 1. Theme Engine

| Элемент | Реализация |
|---------|------------|
| Режимы | Light / Dark / System |
| Provider | `components/planam-2026/theme/ThemeProvider.tsx` |
| Persistence | `localStorage` ключ `planam-2026-theme` |
| Toggle | `ThemeToggle2026` (сегментированный control) |
| Dark mode | `class="dark"` на `html` через `lib/planam/theme-document.ts` |
| Legacy safety | `ThemeProvider active={false}` — не трогает `html`, когда flag выключен |
| Telegram | `readTelegramWebApp().themeParams.bg_color` → только `--pa-bg-canvas`; sage primary не меняется |
| System + TMA | При `preference=system` и Telegram — учитывается `WebApp.colorScheme` |

---

## 2. Design Tokens

Обновлены `app/globals.css` и `tailwind.config.ts`:

- Семантические CSS-переменные по [`PLANAM_DESIGN_SYSTEM_2026.md`](PLANAM_DESIGN_SYSTEM_2026.md) §1.3 (light + `.dark`)
- Tailwind `darkMode: 'class'`, префикс `pa-*` (canvas, surface, elevated, foreground, muted, brand, accent, success, warning, error, border)
- Typography utilities: `.pa26-hero`, `.pa26-page-title`, … `.pa26-micro`
- Новые компоненты **не** используют `emerald-*` / `stone-*`

Legacy `.pa-*` и cream/sage/graphite в tailwind **сохранены** для старых экранов.

---

## 3. UI Primitives 2026

| Компонент | Путь |
|-----------|------|
| `Button2026` | `components/planam-2026/ui/Button2026.tsx` |
| `Card2026` | `components/planam-2026/ui/Card2026.tsx` |
| `HeroCard2026` | `components/planam-2026/cards/HeroCard2026.tsx` |
| `ActionCard2026` | `components/planam-2026/cards/ActionCard2026.tsx` |
| `InsightCard2026` | `components/planam-2026/cards/InsightCard2026.tsx` |
| `MetricCard2026` | `components/planam-2026/cards/MetricCard2026.tsx` |
| `BottomSheet2026` | `components/planam-2026/ui/BottomSheet2026.tsx` |
| `EmptyState2026` | `components/planam-2026/ui/EmptyState2026.tsx` |
| `Skeleton2026` | `components/planam-2026/ui/Skeleton2026.tsx` |
| `ThemeToggle2026` | `components/planam-2026/theme/ThemeToggle2026.tsx` |

Barrel: `components/planam-2026/index.ts`

Все поддерживают light/dark, screen-agnostic props, готовы для Home 2026 (Sprint 2).

---

## 4. App Shell Foundation

| Файл | Назначение |
|------|------------|
| `components/planam-2026/layout/AppShell2026.tsx` | Stub nav: План · Дом (center) · Забота · Account (disabled, Sprint 2) |
| `components/layout/AppShellBridge.tsx` | Маршрутизация shell по flag + dev preview |

**Поведение:**

- `NEXT_PUBLIC_PLANAM_UI_2026=false` (default) → старый `AppShell` + старая нижняя навигация
- `NEXT_PUBLIC_PLANAM_UI_2026=true` → `AppShell2026` + ThemeProvider (активный)
- `/dev/planam-2026` → ThemeProvider, **без** старой и без 2026 bottom nav (только preview)

---

## 5. Demo / Preview route

**URL:** `/dev/planam-2026`

- Обходит `AppGate` (как admin) — доступен в браузере без Telegram auth
- Не ломает production: не в меню, не меняет `/`
- Демонстрирует все primitives + ThemeToggle + BottomSheet

---

## 6. Изменённые и новые файлы

### Новые

```
apps/web/lib/planam/cn.ts
apps/web/lib/planam/theme.ts
apps/web/lib/planam/theme-document.ts
apps/web/components/planam-2026/** (theme, ui, cards, layout, index.ts)
apps/web/components/layout/AppShellBridge.tsx
apps/web/app/dev/planam-2026/page.tsx
docs/SPRINT_1_COMPLETION_REPORT.md
```

### Изменённые

```
apps/web/app/globals.css
apps/web/tailwind.config.ts
apps/web/components/AppProviders.tsx
apps/web/components/layout/AppShell.tsx
apps/web/components/auth/AppGate.tsx
```

### Не изменялись (по scope)

- `apps/api/**` — БД, API, платежи
- Старые экраны и маршруты
- `components/ui/Sheet.tsx` (legacy; 2026 — `BottomSheet2026`)

---

## 7. Feature flag

```env
# apps/web/.env.local
NEXT_PUBLIC_PLANAM_UI_2026=false   # default — старый UI
NEXT_PUBLIC_PLANAM_UI_2026=true    # включает AppShell2026 + активный ThemeProvider
```

Preview **не требует** flag: откройте `/dev/planam-2026`.

Код: `lib/planam/feature-flags.ts` → `isPlanamUi2026Enabled()`.

---

## 8. Проверки

| Проверка | Результат |
|----------|-----------|
| `npx tsc --noEmit` (apps/web) | ✅ Pass |
| `npm run lint` (apps/web) | ✅ Pass (pre-existing warning в `ProfileDashboard.tsx`) |
| `npm run build` (apps/web) | ✅ Pass, route `/dev/planam-2026` в бандле |
| API tests `test_home_next_action.py` | ✅ 2 passed (регрессия Sprint 0) |

Отдельного web test suite нет — добавлены не были (scope).

---

## 9. Риски и ограничения

| Риск | Статус |
|------|--------|
| Telegram `themeParams` vs DS dark | Частично: только canvas override; при конфликте пользователь может выбрать Light/Dark явно |
| `html.dark` + legacy emerald экраны при flag=true | При включении flag старые страницы могут визуально смешиваться до Strangler — ожидаемо до Sprint 2–3 |
| Hero `imageUrl` внешние домены | В preview без фото; для Sprint 2 — `next.config` images / CDN |
| Shell stub без роутов | Навигация не кликабельна до Sprint 2 |
| Дублирование Sheet legacy / BottomSheet2026 | Миграция по экранам в следующих спринтах |

---

## 10. Готовность к Sprint 2 (Navigation + Home Foundation)

| Готово | Комментарий |
|--------|-------------|
| ✅ Tokens + dark | Home 2026 может использовать `pa-*` / `.pa26-*` |
| ✅ Card primitives | Hero rail, Action strips, Insight, Metric |
| ✅ Theme | Account → Оформление можно подключить к `usePlanamTheme` |
| ✅ Shell stub | Заменить disabled buttons на `nav-config-2026` |
| ⏳ Overview consumer | API CR2 уже в Sprint 0; UI — Sprint 3 |
| ⏳ Redirects menu→plan | Sprint 2 |

**Рекомендуемые первые задачи Sprint 2:**

1. `lib/navigation/nav-config-2026.ts` + `BottomNavigation2026`
2. Route stubs `app/plan`, `app/home`, `app/wellness`, `app/account`
3. Grace redirects со старых URL
4. Подключить `Home2026` к `GET /menus/overview` (Sprint 3)

---

## 11. Критерии готовности Sprint 1

| Критерий | ✓ |
|----------|---|
| Старый UI при `PLANAM_UI_2026=false` | ✅ |
| Preview route показывает DS | ✅ `/dev/planam-2026` |
| Light / Dark / System | ✅ |
| Компоненты готовы для Home 2026 | ✅ |
| Нет изменений БД/API | ✅ |

---

*Отчёт подготовлен по завершении Sprint 1. Обновлять roadmap при старте Sprint 2.*
