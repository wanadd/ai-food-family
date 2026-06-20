# Карта переходов ПланАм

Полная схема навигации Telegram Mini App. Содержит входы/выходы с каждого экрана, реальные цепочки пользовательских действий, типы переходов и проблемные места.

> ⚠️ Разделы 1–8 ниже описывают навигацию **до** UX/UI Refinement. Актуальная архитектура навигации — в разделе «0. Новая навигация (UX/UI Refinement V1)» сразу ниже. Старые разделы будут переписаны по мере миграции контента (Этапы 2–6).

## 0. Новая навигация (UX/UI Refinement V1)

### Нижняя навигация (5 вкладок, слева направо)

| # | Вкладка | Маршрут | Активна на | Особенность |
|---|---|---|---|---|
| 1 | Меню | `/menu` | `/menu/*`, `/recipes/*` | внутренние вкладки активны (Этап 2 ✅) |
| 2 | Покупки | `/shopping` | `/shopping/*`, `/pantry/*` | центр закупок; внутренние вкладки активны (Этап 3 ✅) |
| 3 | ПланАм | `/` | `/` | центральная, AI-хаб, усиленный акцент |
| 4 | Здоровье | `/health` | `/health/*`, `/nutritionist/*` | бывш. «Нутрициолог» |
| 5 | Профиль | `/profile` | `/profile/*` | постоянная вкладка |

Источник правды: `apps/web/lib/navigation/nav-config.ts`. Рендер: `components/layout/BottomNavigation.tsx`. Навигация скрыта на `/onboarding*` и `/admin*`.

### Внутренние вкладки (sub-tabs)

- **Меню (Этап 2 ✅, контент на месте):** Моё меню (`/menu`) · Рецепты (`/menu/recipes`) · Избранное (`/menu/favorites`) · Коллекции (`/menu/collections`).
  - «Сценарии» и «Из запасов» — **не отдельные вкладки**, а фильтры/подборки внутри Рецептов. «Из запасов» использует единственный источник данных — Запасы (раздел Покупки).
  - Состояние поиска/сценария/фильтров «Рецептов» хранится в URL query (`/menu/recipes?q=…&scenario=…`).
  - Деталь рецепта остаётся на `/recipes/[id]` (в Этапе 2 не переносится).
  - Коллекции — минимальный UI: список + создание + добавление рецепта (из карточки рецепта). Переименование/удаление и rich-карточки отложены.
- **Покупки (Этап 3 ✅, контент на месте):** Покупки (`/shopping`) · Запасы (`/shopping/pantry`) · Остатки (`/shopping/leftovers`).
  - Покупки = единый центр закупок семьи, отвечает на вопрос «что купить?» и объединяет **список покупок + запасы + остатки**.
  - Единый каркас: `components/shopping/ShoppingSectionLayout.tsx` (заголовок «Покупки» + подзаголовок + вкладки) и `components/shopping/ShoppingSubTabs.tsx`.
  - Контент вкладок переиспользует существующие компоненты: `ShoppingListView`, `PantryDashboard`, `MealLeftoversPage` (backend/контракты не менялись). Акцент приведён к emerald (убран teal).

Компонент внутренних вкладок: `components/layout/SegmentedTabs.tsx`. В Меню он монтируется через `components/menu/MenuSubTabs.tsx`; в Покупках — через `components/shopping/ShoppingSubTabs.tsx`.

### Маршруты, созданные в Этапе 1 (скелет)

`/health`, `/health/chat`, `/health/care`, `/menu/recipes`, `/menu/favorites`, `/menu/collections`, `/menu/scenarios`, `/shopping/pantry`, `/shopping/leftovers`.

### Редиректы (мягкие `redirect()`, не 301)

| Откуда | Куда | Тип |
|---|---|---|
| `/nutritionist` | `/health` | постоянный (ребренд) |
| `/nutritionist/chat` | `/health/chat` | постоянный |
| `/nutritionist/care` | `/health/care` → `/notifications` | постоянный |
| `/recipes` | `/menu/recipes` | постоянный (Этап 2 ✅, инверсия) |
| `/menu/scenarios` | `/menu/recipes` | постоянный |
| `/pantry` | `/shopping/pantry` | постоянный (Этап 3 ✅, инверсия) |
| `/menu/leftovers` | `/shopping/leftovers` | постоянный (Этап 3 ✅, инверсия) |

После Этапа 2 каталог рецептов живёт на `/menu/recipes` (`/recipes` инвертирован, деталь `/recipes/[id]` остаётся). После Этапа 3 запасы и остатки живут на `/shopping/pantry` и `/shopping/leftovers`; старые `/pantry` и `/menu/leftovers` инвертированы и мягко ведут на новые. Циклов нет: новые маршруты рендерят контент напрямую, без обратных редиректов.

### Future Delivery Integration

В будущем доставка продуктов будет частью раздела **Покупки** (не отдельная нижняя вкладка и не отдельный раздел «Доставка»).

Планируемая цепочка:

```
Меню
→ список покупок
→ заказ продуктов («Заказать продукты» внутри Покупок)
→ доставка
→ обновление запасов
```

UX-архитектура Покупок уже предусматривает место под будущее действие «Заказать продукты» (см. комментарий в `SHOPPING_SUBTABS`, `nav-config.ts`, и скрытый TODO в `components/shopping/ShoppingSectionLayout.tsx`: «В будущем здесь можно будет заказать продукты из списка»). В Этапах 1–3 доставка НЕ реализуется: без API, без оплаты, без интеграций магазинов, без большой нерабочей кнопки. Доставка останется частью раздела «Покупки», а не отдельной нижней вкладкой/разделом.

---

## Условные обозначения

- `Источник` → `Цель`: куда переходит пользователь.
- Способ перехода: `tap` (кнопка), `link` (ссылка), `system` (нижняя панель / шапка), `redirect` (server-side), `modal` (открытие листа), `back` (закрытие листа/возврат), `query` (через query-параметр / `returnTo`).
- API без миграции данных не указываются.
- Маршруты обозначаются как `/path`. Sheet'ы — `↗ SheetName` (внутри одного маршрута).

---

## 1. Карты «откуда → куда»

### 1.1 `/` (Главная)

**Откуда можно попасть**

| Источник | Способ |
|---|---|
| Глобальная нижняя панель «🏠 ПланАм» | system |
| `/start` в Telegram бот | webapp deep-link |
| После онбординга (`/onboarding`) | `router.replace("/")` |
| `← На главную` из ошибок `/menu`, `/family`, `/menu/generate` | link |
| После `setMode` (с любой страницы — не редиректит, остаётся) | — |

**Куда можно перейти**

| Цель | Кнопка | Способ |
|---|---|---|
| `/profile` | Иконка профиля в шапке | link |
| `/menu` | «Открыть план» / «Составить план» | link |
| `/shopping` | «Открыть покупки» | link |
| `/pantry` | «Открыть» в карточке запасов | link |
| `/nutritionist`, `/menu`, `/shopping`, `/pantry` | Нижняя панель | system |

**Скрытые переходы**: нет.

---

### 1.2 `/menu` (Меню — хаб)

**Откуда**

| Источник | Способ |
|---|---|
| Нижняя панель «🍽 Меню» | system |
| Главная «Открыть план» / «Составить план» | link |
| Бот → reply-меню «🍽 Моё меню» / inline «Открыть меню» | web_app |
| Care-уведомление `menu` (deep-link `/menu`) | webapp link |
| Любой `← Меню` в подэкранах | link |

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `/menu/generate` | «Составить меню», «Обновить меню» | link |
| `/menu/current` | «Подробнее», «Открыть все дни», «Текущее меню» | link |
| `/menu/settings` | «Изменить на сегодня», «Изменить →» | link |
| `/menu/leftovers` | «Остатки блюд» | link |
| `/recipes` | «Рецепты» | link |
| `/` | «На главную» (error) | link |
| inline-аккордеон «Настройки меню» | toggle | inline |
| `/menu/current?replace=1` | quick-action `replace_dish` | redirect через response |
| `/subscription` | при ошибке 402 в quick-action `cheaper` (через `redirect_path`) | redirect |

**Скрытые**: `quick-action` может вернуть `redirect_path` (например, `/menu/current` или `/subscription`).

---

### 1.3 `/menu/generate`

**Откуда**

| Источник | Способ |
|---|---|
| `/menu` («Составить меню», «Обновить меню») | link |
| Empty state `/menu` | link |
| Advice CTA `/nutritionist` («Добавить в меню») | link с `returnTo` |
| Deep-link из бота (теоретически, не использован в UI) | — |

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `/menu` | «← Меню» | link |
| `/menu/current?saved=1` | «Выбрать вариант» | router.push |
| `/menu/current` | «Открыть план →» (после успешной генерации) | link |
| `/subscription` | «Тариф и Амы →» (только при 402) | link |
| inline preview варианта | «Открыть карточку» | modal |
| Назад к выбору | «← Назад к выбору» | back |
| Назад на шаг | «Назад» | inline |

**Скрытые**: после `selectMenu` query `?saved=1` показывает success-banner на `/menu/current`.

---

### 1.4 `/menu/current`

**Откуда**

| Источник | Способ |
|---|---|
| `/menu` (несколько CTA) | link |
| `/menu/generate` (после `selectMenu`) | router.push |
| `/nutritionist` («Отметить, где поели →») | link |
| `/menu/leftovers` («Отметить приёмы пищи в меню →») | link |
| Care-уведомление | deep-link |

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `/menu` | «← Меню», «Настроить план» (empty) | link |
| `/menu/leftovers` | «Остатки блюд» | link |
| `ReplaceDishModal` | «Заменить блюдо» | modal |
| inline-чипы дней / member | toggle | inline |

**Скрытые**: `?replace=1` автоматически открывает `ReplaceDishModal`.

---

### 1.5 `/menu/leftovers`

**Откуда**

| Источник | Способ |
|---|---|
| `/menu` | link |
| `/menu/current` | link |
| `MealCheckinPanel` | link |
| Бот `quick:leftover` после FSM | webapp link «🛒 Добавить в покупки/запасы» |
| Care-уведомление leftover (если включено) | deep-link |

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `/menu` | «← Меню» | link |
| `/menu/current` | «Отметить приёмы пищи в меню →» | link |

---

### 1.6 `/menu/settings`

**Откуда** — только `/menu`.

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `/menu` | back | system |
| `/menu/generate` | «Обновить меню» | link |

---

### 1.7 `/recipes`

**Откуда**

| Источник | Способ |
|---|---|
| `/menu` («Рецепты») | link |
| `/menu/recipes` | redirect (server) |
| `/nutritionist` (advice CTA «Найти рецепт» с query) | link с `?search=` |
| Кнопка «← Каталог» из `/recipes/[id]` | link |

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `/recipes/[id]` | Тап по карточке | link |
| inline favorite toggle | tap | inline |
| Фильтры/секции | local | inline |

---

### 1.8 `/recipes/[id]`

**Откуда** — каталог, `RecipeDetailModal` (с других экранов в `menuMode`).

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `/recipes` | «← Каталог», `router.push` при закрытии | link |
| `/shopping` (после `add-to-shopping`) | сообщение «Открыть покупки» (если есть) | link |
| `/menu/current` (после `add-to-menu`) | callback | inline |

---

### 1.9 `/shopping`

**Откуда**

| Источник | Способ |
|---|---|
| Нижняя панель «🛒 Покупки» | system |
| Главная «Открыть покупки» | link |
| Бот «🛒 Покупки» (reply / inline) | webapp link |
| Care-уведомление `shopping` | deep-link |
| `/pantry` («↑ К покупкам») | link |
| `/menu/leftovers` (sticky) | — |
| После `RecipeDetailModal.handleAddToShopping` (callback) | toast |

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `ShoppingItemSheet` | «+ Добавить» / «Изменить» | modal |
| `ShoppingCategorySheet` | «+ Категория» | modal |
| `CategoryPicker` (внутри sheet) | tap | modal |
| inline-toggle купленных | tap | API |

---

### 1.10 `/pantry`

**Откуда**

| Источник | Способ |
|---|---|
| Нижняя панель «📦 Запасы» | system |
| Главная «Открыть» | link |
| Бот «📦 Запасы» (reply / inline) | webapp link |
| Care-уведомление `pantry` | deep-link |
| `/shopping` (косвенно — после `toggle` товара) | автоматическое создание |

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `PantryItemForm` | «+ Добавить» / «Изменить» | modal (inline) |
| `/shopping` | «↑ К покупкам» | link |

---

### 1.11 `/nutritionist`

**Откуда**

| Источник | Способ |
|---|---|
| Нижняя панель «🥗 Нутрициолог» | system |
| Care-уведомления (`water`, `protein`, `family`, `pro`) | deep-link |
| Бот reply-меню «🥗 Нутрициолог» / inline | webapp link |

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `/profile/nutrition?returnTo=/nutritionist` | «Открыть профиль», «Изменить цель» | link |
| `/nutritionist/chat` | «Спросить нутрициолога», «Открыть чат нутрициолога» | link |
| `/progress?focus=weight&returnTo=/nutritionist` | «Добавить вес» | link |
| `/progress?focus=training&returnTo=/nutritionist` | «Добавить тренировку» | link |
| `/menu/current` | «Отметить, где поели →» | link |
| `/menu/generate?returnTo=/nutritionist` | advice CTA «Добавить в меню» | link |
| `/recipes?search=...` | «Найти рецепт» | link |
| `/shopping?add=...` | «Добавить в покупки» | link |
| `/progress` | «Подробнее в прогрессе →» (в family-progress) | link |
| Аккордеоны Family Summary / Family Progress | toggle | inline |

---

### 1.12 `/nutritionist/chat`

**Откуда** — `/nutritionist` (две CTA), бот «🥗 Нутрициолог».

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `/nutritionist` | «← Нутрициолог» | link |
| `/subscription` | при ошибке 402 | link |

---

### 1.13 `/nutritionist/care` и `/settings/care`

**Откуда** — `/nutritionist` (link), `/settings`, шапка профиля, бот reply-меню → inline «Открыть нутрициолога».

**Куда** — обратно в `/settings` или `/nutritionist` (системная панель).

---

### 1.14 `/profile`

**Откуда** — иконка профиля с `/`, кнопка «← Профиль» из `/family`, `/subscription`, `/notifications`, `/progress`, `/settings/*`.

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `/profile/nutrition` | «Питание» | link |
| `/family` | «Семья» | link |
| `/subscription` | «Подписка» | link |
| `/progress` | «Прогресс» | link |
| `/notifications` | «Уведомления» | link |
| `/settings/about` | «О приложении» | link |
| `/settings` | Шестерёнка в шапке | link |

---

### 1.15 `/profile/nutrition`

**Откуда** — `/profile`, баннер «Заполните профиль» из `/nutritionist` и `/menu/generate` (advice CTA).

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `returnTo` (если задан) или `/profile` | «Сохранить» | router.replace |
| `/profile` | back | link |

---

### 1.16 `/progress`

**Откуда** — `/profile`, `/nutritionist` (через `focus` + `returnTo`).

**Куда** — `returnTo` (по умолчанию `/profile`).

---

### 1.17 `/subscription`

**Откуда** — `/profile`, баннер лимита в `/menu/generate`, `/nutritionist/chat` (ошибка 402).

**Куда** — `/profile`.

---

### 1.18 `/family`

**Откуда** — `/profile`. Баннер «Семья: {name}» на главной (если family-режим) — статус, не ссылка.

**Куда**

| Цель | Кнопка | Способ |
|---|---|---|
| `/profile` | «← Профиль» | link |
| `AddPersonSheet` | «+ Добавить человека» | modal |
| `InviteSheet` | «Пригласить» | modal |
| `FamilyManageSheet` | «Управление семьёй» | modal |
| inline-форма виртуального участника | «Виртуальный участник» | inline screen |
| `/` | «На главную» (если нет initData) | link |

---

### 1.19 `/notifications`

**Откуда** — `/profile`, `/settings/support`.

**Куда** — back в `/profile`.

---

### 1.20 `/settings`

**Откуда** — иконка-шестерёнка в `/profile`.

**Куда** — 9 поднастроек.

---

### 1.21 `/onboarding`

**Откуда** — первый запуск (при отсутствии `data.completed`).

**Куда** — `/` после «Завершить» / «Пропустить».

---

### 1.22 `/admin/*`

**Откуда** — Telegram-бот `/admin` PIN-сессия → web-app link.

**Куда** — между табами и деталями. Возврата в основной UI нет (это отдельная панель).

---

## 2. Реальные цепочки действий

### 2.1 Создать меню (с нуля)

```
Главная (/)
↓ tap «Открыть план»
Меню (/menu)
↓ tap «Составить меню»
Мастер генерации (/menu/generate, step 0)
↓ выбрать цель → «Продолжить»
Мастер (step 1: персоны, только family)
↓ выбрать → «Продолжить»
Мастер (step 2: дни)
↓ выбрать → «Продолжить»
Мастер (step 3: бюджет + режим)
↓ выбрать → «Продолжить»
Мастер (step 4: чеклист)
↓ tap «Сгенерировать меню»
→ POST /menus/generate (списание лимита / Ams)
Фаза «Выбор» (/menu/generate, phase=choose)
↓ tap «Выбрать вариант»
→ POST /menus/select
Текущий план (/menu/current?saved=1)
```

### 2.2 Заменить блюдо

```
Текущий план (/menu/current)
↓ tap «Заменить блюдо» в карточке
ReplaceDishModal (поверх)
↓ tap «Заменить» с подсказкой
→ POST /menus/replace-dish + POST /menus/select
Текущий план (обновлён)
```

Альтернативный путь:
```
/menu → quick-action «Заменить блюдо» → /menu/current?replace=1 → ReplaceDishModal
```

### 2.3 Чекин «поел вне дома»

```
/menu/current → MealCheckinPanel
↓ выбор члена семьи (family)
↓ tap «работа»
→ POST /meal-checkins
Inline-обновление статуса
```

### 2.4 Добавить остаток через бот

```
Бот: «⚡ Быстро добавить»
→ inline «🍲 Остатки блюда»
Бот: «Что осталось?»
↓ текст «Борщ»
Бот: «Сколько порций?»
↓ «3»
→ POST /meal-leftovers (через FSM)
Бот: «Сохранено. Учтём…»
```

### 2.5 Голосовое добавление в покупки

```
Бот: voice
→ download_telegram_file + voice_input.transcribe_for_user (Whisper)
→ AI parse (списание Амов: bot_parse_text + voice_command)
Бот: распознанный список + inline pending кнопки
↓ «Сохранить» (callback pending:confirm)
→ shopping.add_item для каждой позиции
Бот: «Добавил в покупки» + ссылки на /shopping и /pantry
```

### 2.6 Покупка → запас

```
/shopping
↓ Чекбокс товара
→ PATCH /shopping/items/{id}/toggle (checked=true)
→ pantry_shopping.add_or_merge_from_shopping (автоматически)
/pantry: появилась позиция с source='shopping_list'
```

### 2.7 Создать семью

```
/profile → tap «Семья»
/family (empty)
↓ ввести имя «Семья Ивановых»
↓ галка «подтверждаю»
↓ tap «Создать семью»
→ POST /families
/family (created)
↓ tap «+ Добавить человека»
AddPersonSheet
↓ tap «Пригласить в Telegram»
InviteSheet
↓ ввести +7..., tap «Отправить»
→ POST /families/{id}/invites
Бот приглашаемого: notify_invitee_about_invite
↓ tap «Принять»
Бот: «Вы присоединились…»
```

### 2.8 Изменить цель и пересоздать меню

```
/nutritionist → tap «Изменить цель»
/profile/nutrition?returnTo=/nutritionist
↓ изменить чипы цели
↓ tap «Сохранить»
→ POST /nutrition/profile
router.replace(/nutritionist)
/nutritionist (advice freshness_status = needs_update — на /menu)
↓ переход на /menu
/menu → банер «Цель изменилась» → «Обновить меню»
/menu/generate
```

### 2.9 Покупка подписки (test-stub)

```
/profile → «Подписка»
/subscription
↓ tap «Выбрать тариф» (например, family)
→ POST /subscription/select
Тост «✓ Тариф сохранён»
```

### 2.10 Прогресс веса и возвращение

```
/nutritionist → «Добавить вес»
/progress?focus=weight&returnTo=/nutritionist (форма открыта по focus)
↓ ввести 78.5 → «Сохранить»
→ POST /progress/entries
/progress (обновлено)
↓ «← Назад» (по returnTo)
/nutritionist (KPI обновлены)
```

### 2.11 Care-уведомление → действие

```
care_scheduler отправляет пуш в Telegram
Пользователь: tap inline-кнопка «Открыть меню»
webapp link → /menu (deep-link)
```

---

## 3. Таблица переходов «источник → цель»

| Источник | Цель | Способ | Кнопка | Роут | Side-effects |
|---|---|---|---|---|---|
| `/` | `/menu` | link | Открыть план | `/menu` | — |
| `/` | `/shopping` | link | Открыть покупки | `/shopping` | — |
| `/` | `/pantry` | link | Открыть | `/pantry` | — |
| `/` | `/profile` | link | Иконка | `/profile` | — |
| `/menu` | `/menu/generate` | link | Составить / Обновить | `/menu/generate` | — |
| `/menu` | `/menu/current` | link | Подробнее / Открыть план / Текущее меню | `/menu/current` | `?replace=1` опционально |
| `/menu` | `/menu/settings` | link | Изменить на сегодня | `/menu/settings` | — |
| `/menu` | `/menu/leftovers` | link | Остатки блюд | `/menu/leftovers` | — |
| `/menu` | `/recipes` | link | Рецепты | `/recipes` | — |
| `/menu` | `/subscription` | redirect | quick-action ошибка лимита | `/subscription` | error msg |
| `/menu/generate` | `/menu/current?saved=1` | router.push | Выбрать вариант | `/menu/current` | POST /menus/select |
| `/menu/generate` | `/menu/current` | link | Открыть план | `/menu/current` | — |
| `/menu/generate` | `/subscription` | link | Тариф и Амы | `/subscription` | — |
| `/menu/current` | `/menu` | link | ← Меню | `/menu` | — |
| `/menu/current` | `/menu/leftovers` | link | Остатки блюд | `/menu/leftovers` | — |
| `/menu/current` | modal | modal | Заменить блюдо | — | — |
| `/menu/leftovers` | `/menu` | link | ← Меню | `/menu` | — |
| `/menu/leftovers` | `/menu/current` | link | Отметить приёмы | `/menu/current` | — |
| `/menu/settings` | `/menu` | back | системная | `/menu` | localStorage |
| `/menu/settings` | `/menu/generate` | link | Обновить меню | `/menu/generate` | — |
| `/shopping` | `/pantry` | косвенно | toggle (auto) | — | POST /pantry |
| `/pantry` | `/shopping` | link | ↑ К покупкам | `/shopping` | — |
| `/nutritionist` | `/profile/nutrition` | link с `returnTo` | Открыть профиль / Изменить цель | `/profile/nutrition?returnTo=/nutritionist` | — |
| `/nutritionist` | `/nutritionist/chat` | link | Спросить / Открыть чат | `/nutritionist/chat` | — |
| `/nutritionist` | `/progress` | link с focus + returnTo | Добавить вес / тренировку | `/progress?focus=...&returnTo=/nutritionist` | — |
| `/nutritionist` | `/menu/current` | link | Отметить, где поели | `/menu/current` | — |
| `/nutritionist` | `/menu/generate` | link | advice CTA | `/menu/generate?returnTo=/nutritionist` | — |
| `/nutritionist` | `/recipes` | link с `?search=` | Найти рецепт | `/recipes?search=...` | — |
| `/nutritionist` | `/shopping` | link с `?add=` | Добавить в покупки | `/shopping?add=...` | — |
| `/nutritionist/chat` | `/nutritionist` | link | ← Нутрициолог | `/nutritionist` | — |
| `/nutritionist/chat` | `/subscription` | link при 402 | Перейти к тарифу | `/subscription` | — |
| `/recipes` | `/recipes/[id]` | link | Карточка | `/recipes/[id]` | — |
| `/recipes/[id]` | `/recipes` | link | ← Каталог | `/recipes` | — |
| `/profile` | `/profile/nutrition` | link | Питание | `/profile/nutrition` | — |
| `/profile` | `/family` | link | Семья | `/family` | — |
| `/profile` | `/subscription` | link | Подписка | `/subscription` | — |
| `/profile` | `/progress` | link | Прогресс | `/progress` | — |
| `/profile` | `/notifications` | link | Уведомления | `/notifications` | — |
| `/profile` | `/settings/about` | link | О приложении | `/settings/about` | — |
| `/profile` | `/settings` | link | Шестерёнка | `/settings` | — |
| `/profile/nutrition` | `returnTo` или `/profile` | router.replace | Сохранить | как параметр | POST /nutrition/profile |
| `/progress` | `returnTo` | link | ← | как параметр | — |
| `/subscription` | `/profile` | link | ← Профиль | `/profile` | — |
| `/family` | `/profile` | link | ← Профиль | `/profile` | — |
| `/family` | sheets | modal | Добавить / Пригласить / Управление | — | — |
| `/notifications` | `/profile` | link | ← Профиль | `/profile` | — |
| `/settings` | `/settings/*` | link | список | подэкраны | — |
| `/settings/account` | `/profile` | link | ← Профиль | `/profile` | — |
| `/settings/care` | `/nutritionist/care` | дубль | — | те же кнопки | — |
| `/onboarding` | `/` | router.replace | Завершить / Пропустить | `/` | POST /onboarding/answers |
| `/admin` | tabs | link | NAV | `/admin/*` | — |
| Все основные | системная панель | system | нижняя панель | 5 целей | — |

---

## 4. Циклические переходы

- `/menu ↔ /menu/generate ↔ /menu/current ↔ /menu/leftovers ↔ /menu` — цикл главного потока меню; пользователь может ходить в любом направлении.
- `/menu ↔ /menu/settings` — туда-обратно с сохранением в `localStorage`.
- `/nutritionist ↔ /profile/nutrition ↔ /nutritionist` через `returnTo`.
- `/nutritionist ↔ /progress ↔ /nutritionist` через `returnTo` и `focus`.
- `/profile ↔ /family ↔ /profile`, `/profile ↔ /subscription ↔ /profile`, `/profile ↔ /progress ↔ /profile`.
- `/shopping → /pantry → /shopping` (по кнопке «↑ К покупкам»).
- `/settings ↔ /settings/care ≡ /nutritionist/care` — петля через дублирующийся экран.

---

## 5. Тупиковые экраны (нет выхода кроме back / нижней панели)

| Экран | Почему тупик |
|---|---|
| `/settings/units` | Заглушка, без действий |
| `/settings/privacy` | Заглушка |
| `/settings/language` | Заглушка |
| `/settings/about` | Только текст, кнопка «← Настройки» |
| `/settings/documents` | Чтение текстов; «Принять» работает только при ожидании согласия |
| `/menu/recipes` | Server-side redirect — пользователь не задерживается |
| `/admin/openai`, `/admin/errors` | Только данные/настройки, нет переходов в основную часть UI |
| `/menu/event` | Нет входа из основного UI, экран существует только по прямому URL |

---

## 6. Экраны без явного возврата

Пользователь возвращается только через нижнюю панель / системный жест:

- `/` — нет «назад», только нижняя панель.
- `/menu`, `/shopping`, `/pantry`, `/nutritionist` — основные табы.
- `/admin/*` — нет ссылок назад в основной UI (по дизайну).
- `/onboarding` — нет «← На главную» до завершения шагов.

---

## 7. Экраны с несколькими путями (на один экран ведёт ≥3 пути)

| Экран | Пути |
|---|---|
| `/menu` | Главная, нижняя панель, бот (3 источника), Care, `← Меню` из подэкранов |
| `/menu/current` | `/menu` (3 ссылки), `/menu/generate` после сохранения, `/menu/leftovers`, `/nutritionist`, Care |
| `/menu/generate` | `/menu` (3 ссылки), `/nutritionist` (advice), `/menu/settings`, Care |
| `/menu/leftovers` | `/menu`, `/menu/current`, `MealCheckinPanel`, бот FSM |
| `/profile/nutrition` | `/profile`, баннер `/nutritionist`, `/menu/generate` (advice CTA) |
| `/subscription` | `/profile`, `/menu/generate` (ошибка 402), `/nutritionist/chat` (402), `/menu` quick-action |
| `/shopping` | Главная, нижняя панель, бот (3+), Care, `/pantry`, рецепт `add-to-shopping` |
| `/pantry` | Главная, нижняя панель, бот, Care, чекбокс в `/shopping` (auto-create) |
| `/recipes` | `/menu`, `/menu/recipes`, `/nutritionist` (advice), карточка `← Каталог` |

---

## 8. Запутанная навигация

1. **Care-экран дублирован**: `/nutritionist/care` и `/settings/care` ведут на один и тот же компонент. Пользователь, попавший с разных сторон, не понимает, где он находится.
2. **Профиль доступен только с главной**: на любом экране, кроме `/`, нет ссылки на профиль; нижняя панель его не содержит. Чтобы выйти на профиль, надо вернуться на `/` или открыть подэкран через URL.
3. **Two-screen budget step в `/menu/generate`**: «Бюджет» и «Режим плана» — на одном шаге, но визуально разделены и часто воспринимаются как отдельные шаги.
4. **`/menu/settings` называется «Изменить на сегодня»**: фактически это override параметров мастера в `localStorage`, не настройки текущего дня. Возникает ожидание, что эти изменения сразу пересоберут план.
5. **`/menu/event` существует без входа из UI**: пользователь может попасть только по прямому URL (или из админки), что вызывает «потерю» функциональности.
6. **`/menu/recipes` — server redirect**: при бесшовном переходе пользователь видит мгновенный «прыжок» URL. Это сбивает с толку.
7. **Чекин и остатки конкурируют**: `/menu/current → MealCheckinPanel`, `/menu/leftovers` и Telegram-bot FSM создают похожие записи (особенно `actual_status="saved_as_leftover"`). Пользователь не понимает, где какой путь.
8. **Quick-actions `/menu`** возвращают то redirect, то сообщение в зависимости от типа. Это непредсказуемое поведение.
9. **`returnTo` цепочки**: `/nutritionist → /progress?focus=weight&returnTo=/nutritionist → ← Назад → /nutritionist`. Когда пользователь идёт глубже (`/progress → /profile`), `returnTo` теряется.
10. **Семья vs Профиль**: «Профиль питания» и «Семья → редактирование участника» имеют разный UX (формы), хотя редактируют похожие поля. Пользователь не понимает, какой профиль он сейчас редактирует.
11. **Admin не имеет «выйти на главную»**: ссылок назад в основной UI нет; пользователь должен закрыть/обновить webapp.
12. **Onboarding и `/profile/nutrition`** имеют пересекающиеся поля; после онбординга пользователю всё равно нужно открыть профиль для деталей (рост/вес/возраст).
13. **`care` и `notifications`** — два совершенно разных раздела (push-уведомления care vs cook/buy reminders). Пользователь не понимает, где включить какой тип уведомлений.
