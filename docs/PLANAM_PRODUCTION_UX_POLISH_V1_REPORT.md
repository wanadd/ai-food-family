# PLANAM Production UX Polish v1 — Report

Дата: 2026-06-05  
Ветка: `sprint-0/planam-2026-foundation`  
Коммит: `fix(ui): polish production Telegram UX`

## Цель

Улучшить продовый UX Telegram Mini App: компактная навигация, меньше лишнего скролла, понятный «Назад», тема, категории покупок, корректный prod build.

## Что исправлено

### Bottom nav (4 вкладки)

| Вкладка | Маршрут |
|---------|---------|
| Сегодня | `/plan/today` |
| Покупки | `/home/shopping` |
| Главная | `/` (центр) |
| Профиль | `/account` |

- Убрана вкладка «Здоровье» из нижней панели.
- Здоровье доступно с главной: карточка «Здоровье» → `/wellness`.
- Safe-area-bottom учтён в `BottomNavigation2026`.
- Dark mode: hover/active без белых артефактов.

Файлы: `nav-config-2026.ts`, `BottomNavigation2026.tsx`.

### Главная `/`

- Компактная структура: приветствие 👋, блюдо дня, быстрые действия (Меню / Покупки / Остатки / Здоровье), CTA «Открыть меню» и «Список покупок», AI-блок.
- Убраны длинные секции (`RecipeRail`, `WellnessChip`, `PlanSnapshot`, `NextActionCard`).
- `AppShell2026`: `flex min-h-dvh` вместо лишнего `min-h-screen` scroll.

Файлы: `Home2026.tsx`, `HomeQuickActions2026.tsx`, `AppShell2026.tsx`.

### `/wellness`

- Собственный заголовок на экране, shell header скрыт.
- Уменьшены вертикальные отступы (`pb-2`, компактный `space-y`).

Файл: `WellnessHome2026.tsx`.

### BackButton / «Назад»

- **Telegram**: `BackButton` через `useTelegramBackButton2026` + `TelegramBackBridge2026`.
- **Браузер**: кнопка «← Назад» в `ShellHeader2026` (`ScreenBack2026`).
- Логика: `router.back()` или fallback (`/plan/recipes`, `/account`, `/` и т.д.).
- Не показывается на табах: `/`, `/plan/today`, `/home/shopping`, `/account`.

Файлы: `back-navigation-2026.ts`, `ScreenBack2026.tsx`, `useTelegramBackButton2026.ts`, `TelegramBackBridge2026.tsx`, `ShellHeader2026.tsx`.

### Тема приложения

- Блок **«Тема приложения»** — первый в `/account`.
- Подпись: «Светлая / Тёмная / Как в системе».
- `ThemeToggle2026`: опция «Как в системе» вместо «Система».

### Shopping categories

- Расширен `CATEGORY_KEYWORDS` в `shopping_categories.py`.
- Новые категории: `бакалея`, `специи`, `зелень`.
- Тесты: `test_shopping_infer_category.py` (30 продуктов).
- UI labels: `lib/shopping/labels.ts`.

### Shopping маршрут

- Основной: `/home/shopping` (вкладка bottom nav).
- Legacy `/shopping` → redirect на `/home/shopping` при `UI_2026=true`.

### Production env fix

```yaml
# docker-compose.prod.yml
NEXT_PUBLIC_PLANAM_UI_2026: ${NEXT_PUBLIC_PLANAM_UI_2026:-true}
```

```dockerfile
# apps/web/Dockerfile.prod
ARG NEXT_PUBLIC_PLANAM_UI_2026=true
ENV NEXT_PUBLIC_PLANAM_UI_2026=$NEXT_PUBLIC_PLANAM_UI_2026
```

Флаг доступен на этапе `next build`.

## QA результаты

| Проверка | Результат |
|----------|-----------|
| `cd apps/api && python -m pytest` | **70 passed** |
| `npm run lint` | OK (1 pre-existing warning в ProfileDashboard) |
| `npm run build` (UI_2026=true) | OK |
| `npm run build` (UI_2026=false) | OK |

## Telegram smoke QA (ручная)

Рекомендуется проверить в Mini App:

1. Главная — без лишнего скролла, быстрые действия
2. Сегодня / Покупки / Профиль — 4 вкладки
3. Здоровье — с главной, не в bottom nav
4. Рецепт / настройки — «Назад» или Telegram BackButton
5. `/account` — переключатель темы
6. Покупки — категории после «В список»

## Backlog

- Weekly Menu Engine / AI-генерация меню
- Полный редизайн всех экранов
- Drag-and-drop календарь
- Автоподбор замены по КБЖУ
- E2E smoke в CI для Telegram WebApp

## Критерии готовности

| Критерий | Статус |
|----------|--------|
| Bottom nav = 4 вкладки | OK |
| Главная без лишнего скролла | OK |
| `/wellness` компактнее | OK |
| Back / Telegram BackButton | OK |
| Тема в `/account` | OK |
| Категории покупок | OK |
| `/home/shopping` основной маршрут | OK |
| `NEXT_PUBLIC_PLANAM_UI_2026` в prod build | OK |
| pytest / lint / build | OK |
| Отчёт | OK |
