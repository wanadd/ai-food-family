# PLANAM UX Polish V2 — отчёт

Дата: 2026-06-03  
Ветка: `sprint-0/planam-2026-foundation`

## 1. Что исправлено

### Этап 1 — убраны переходы в legacy UI

- Account Hub больше не ведёт на `/profile`, `/family`, `/notifications`, `/settings`.
- Добавлены маршруты `/account/*` с 2026-оболочкой (без дублирующего `ScreenLayout`).
- Legacy-страницы редиректят в 2026 при `NEXT_PUBLIC_PLANAM_UI_2026=true` (page-level + middleware).
- `/recipes`, `/recipes/[id]`, `/menu/recipes` → `/plan/recipes` в UI 2026.

### Этап 2 — возврат по контексту (`returnTo`)

- Расширен `lib/navigation/return-to.ts`: `withReturnTo`, `readReturnTo`, `backLabelForReturnTo`.
- `useTelegramBackButton2026` и `ScreenBack2026` учитывают `returnTo` в query.
- Прокинут `returnTo` в сценарии: Главная→Здоровье, Сегодня→Заменить→Каталог→Рецепт, Покупки→Запасы.

### Этап 3 — один профиль

- Единая точка входа: `/account` с карточкой пользователя и hub-меню.
- Подстраницы: `/account/family`, `/account/nutrition`, `/account/notifications`, `/account/settings/*`.
- Legacy `/profile`, `/family`, `/notifications`, `/settings` редиректят в account-ветку.

### Этап 4 — категории покупок

- Унифицирован `infer_category` → канонические slug (овощи_зелень, мясо_птица, яйца, специи_соусы, бакалея и др.).
- Яйца проверяются до мяса (исправлено «Яйцо куриное → Мясо»).
- Специи/соусы: ванилин, сунели, шафран, томатная паста.
- Синхронизирован `apps/web/lib/shopping/category-suggest.ts`.
- В `SYSTEM_CATEGORIES` добавлены `бакалея`, `специи_соусы`.

### Этап 5 — нижняя навигация

- Было: Сегодня · Покупки · **Главная** · Профиль.
- Стало: Сегодня · Покупки · **Здоровье** · Профиль.
- Главная (`/`) — через логотип 🏠 в shell header и стартовый маршрут, не во вкладках.

### Этап 6 — дубли заголовков

- Shell header скрыт на: `/`, `/wellness`, `/account`, `/plan/today`, `/plan/recipes`.
- В embedded-режиме убран заголовок `ScreenLayout` на account-подстраницах.
- `/account` показывает один заголовок «Профиль» в hub.

### Этап 7 — компактность скролла

- Уменьшены отступы на `/account` (`py-4`, safe-area).
- `/wellness` и `/` уже используют компактные `pb-2` / `pb-2` layouts.

---

## 2. Legacy-маршруты, убранные из UI 2026

| Legacy | 2026 |
|--------|------|
| `/profile` | `/account` |
| `/profile/nutrition` | `/account/nutrition` |
| `/family` | `/account/family` |
| `/notifications` | `/account/notifications` |
| `/settings` | `/account/settings` |
| `/settings/*` | `/account/settings/*` |
| `/recipes` | `/plan/recipes` |
| `/recipes/[id]` | `/plan/recipes/[id]` |
| `/menu/recipes` | `/plan/recipes` |

Middleware (при `UI_2026=true`) всегда редиректит критичные префиксы: `/profile`, `/family`, `/notifications`, `/settings`, `/recipes`, `/menu/recipes`.

---

## 3. Реализация `returnTo`

- Query-параметр: `returnTo=/path`.
- Хелпер: `withReturnTo(href, returnTo)`.
- Back: `resolveBackTarget2026(pathname, searchParams)` — при наличии `returnTo` всегда `router.push(target)`, иначе `router.back()` с fallback.
- Метки кнопки «Назад»: `backLabelForReturnTo` (Главная, Сегодня, Рецепты, Профиль…).

---

## 4. Исправленные категории

| Продукт | Было | Стало |
|---------|------|-------|
| Яйцо куриное | мясо | яйца |
| Яйцо | продукты/мясо | яйца |
| Уцхо-сунели, Шафран, Ванилин | продукты | специи_соусы |
| Мука | крупы (frontend) | бакалея |
| Макароны | крупы | крупы_макароны |
| Помидор, Картофель, Огурец | овощи | овощи_зелень |
| Томатная паста | овощи | специи_соусы |

---

## 5. Нижняя навигация

`NAV_TABS_2026`: plan → shopping → **wellness** → account.  
`getActiveTabId2026`: `/wellness` подсвечивает вкладку «Здоровье»; `/` и `/home/*` — без активной вкладки.

---

## 6. Убранные дубли заголовков

- Shell + ScreenLayout на `/profile`, `/settings`, `/notifications` — устранено через embedded + redirects.
- Shell + subtab chips на `/plan/today`, `/plan/recipes` — shell скрыт, остаются subtabs.
- «Профиль / Профиль» на `/account` — один заголовок в hub.

---

## 7. Компактные экраны

- `/account` — `py-4`, встроенный header.
- `/` — `pb-2` (Home2026).
- `/wellness` — `pb-2`, один h1 на экране.

---

## 8. QA

| Проверка | Результат |
|----------|-----------|
| `pytest` (backend) | **81 passed** |
| `npm run lint` | **OK** (2 pre-existing img warnings) |
| `npm run build` UI_2026=true | **OK** |
| `npm run build` UI_2026=false | **OK** |

---

## 9. Backlog

- `/wellness/progress` — маршрут в migration map, экран не реализован.
- `/plan/favorites`, `/plan/collections` — planned subtabs.
- Полная замена cream/stone `ScreenLayout` на 2026-компоненты внутри account forms (сейчас embedded-режим без legacy header).
- `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS` для широких menu/shopping редиректов (опционально).
- Home → Запасы (`/home/pantry`) — добавить явный quick action с `returnTo=/` при необходимости.

---

## Критерии готовности

- [x] Нет переходов из UI 2026 в legacy (критичные маршруты)
- [x] Назад по `returnTo` / fallback
- [x] Один профиль (`/account`)
- [x] Здоровье в нижнем баре
- [x] Категории покупок исправлены
- [x] Нет дублей заголовков на ключевых экранах
- [x] pytest / lint / build OK
