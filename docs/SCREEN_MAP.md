# Карта экранов ПланАм

Сводный реестр всех экранов Telegram Mini App, модальных листов и админских страниц. Данные собраны из репозитория `ai-food-family` без изменений кода. Маршруты — App Router (`apps/web/app/**/page.tsx`), компоненты — `apps/web/components/**`.

> ⚠️ UX/UI Refinement V1 (Этап 1) ввёл новую архитектуру навигации и скелет маршрутов. Реестр экранов ниже отражает прежнюю структуру и будет обновляться по мере миграции контента (Этапы 2–6). Краткая сводка новой структуры — в разделе «0» ниже.

## 0. Навигационная архитектура (UX/UI Refinement V1)

Нижняя навигация — 5 вкладок: **Меню** (`/menu`) · **Покупки** (`/shopping`) · **ПланАм** (`/`, центр / AI-хаб) · **Здоровье** (`/health`) · **Профиль** (`/profile`). Источник правды: `apps/web/lib/navigation/nav-config.ts`.

**Новые маршруты (скелет, Этап 1):**

| Маршрут | Тип в Этапе 1 | Назначение |
|---|---|---|
| `/health` | route | Раздел «Здоровье» (рендерит `NutritionistDashboard`, ребренд — Этап 5) |
| `/health/chat` | route | Чат нутрициолога (back → `/health`) |
| `/health/care` | redirect → `/notifications` | сохранение прежнего поведения |
| `/menu/recipes` | route (Этап 2 ✅) | вкладка «Рецепты» → `RecipesView` (URL-state: `q`, `scenario`, фильтры) |
| `/menu/favorites` | route (Этап 2 ✅) | вкладка «Избранное» → `FavoritesView` |
| `/menu/collections` | route (Этап 2 ✅) | вкладка «Коллекции» → `CollectionsView` (список + создание) |
| `/menu/collections/[id]` | route (Этап 2 ✅) | деталь коллекции → `CollectionDetailView` (recipe_ids, без N+1) |
| `/menu/scenarios` | redirect → `/menu/recipes` | фильтр-подборка (не отдельная вкладка) |
| `/shopping/pantry` | redirect → `/pantry` | вкладка «Запасы» (Этап 3) |
| `/shopping/leftovers` | redirect → `/menu/leftovers` | вкладка «Остатки» (Этап 3) |

**Этап 2 (Меню + Рецепты) ✅:** каталог рецептов переехал во вкладку `/menu/recipes`; `/recipes` инвертирован (redirect → `/menu/recipes`). Деталь рецепта остаётся на `/recipes/[id]`. Из «Моё меню» убрана плитка «Рецепты» (теперь это вкладка). Backend/контракты не менялись.

**Старые маршруты:** `/nutritionist`, `/nutritionist/chat`, `/nutritionist/care` — мягкие `redirect()` на `/health*`. `/pantry`, `/menu/leftovers` остаются живыми до Этапа 3.

**Future Delivery Integration:** доставка продуктов в будущем — часть раздела **Покупки** (не отдельная вкладка/раздел). Цепочка: Меню → список покупок → заказ продуктов → доставка → обновление запасов. В Этапе 1 не реализуется (без API/оплаты/интеграций); место под действие «Заказать продукты» заложено в UX-архитектуре Покупок.

---

## Условные обозначения

- `Тип`: `route` — отдельный URL; `sheet` — модальный лист поверх экрана; `modal` — диалог/оверлей; `inline` — внутренняя секция, открываемая внутри страницы.
- API-вызовы пишутся в формате `METHOD /path`. Базовый префикс — `getApiBaseUrl()` (`https://planam.ru/api` по умолчанию в продакшне).
- Возврат назад — где есть `back={…}` или явный `← Назад / ← Меню` / системная нижняя панель (`BottomNavigation`).

---

## 1. Главная — `/`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/page.tsx` → `components/home/PlanAmHome.tsx` |
| Где открывается | Глобально (нижняя панель «ПланАм»), при `/start` бота, после регистрации |
| Как попасть | Логотип / иконка `🏠 ПланАм` в нижней панели, авторизация после онбординга |
| Назначение | Сводка дня и быстрый вход в основные разделы |
| Данные | Меню сегодня, осталось купить, в запасах, скоро заканчиваются |
| API | `GET /menus/selected`, `GET /shopping/list`, `GET /pantry` |
| Компоненты | `PlanAmHome`, `ProfileIcon` (inline SVG), `BottomNavigation` |
| Изменяет данные | Нет (read-only) |
| Состояния | `loading`, `hasPlan`, `modeLoading` |
| Модальные | Нет |
| Возврат | Системный (нижняя панель, кнопка профиля) |
| Дубликат | Часть «Сегодня» дублируется в `/menu` и в боте (`build_today_summary`) |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| Иконка профиля | `/` | navigate | `/profile` | — | — |
| Открыть план | `/` | navigate | `/menu` | — | — |
| Открыть покупки | `/` | navigate | `/shopping` | — | — |
| Открыть (запасы) | `/` | navigate | `/pantry` | — | — |
| Составить план | `/` | navigate | `/menu` | — | — |

---

## 2. Меню (хаб) — `/menu`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/menu/page.tsx` → `components/menu/MenuHub.tsx` |
| Где открывается | Нижняя панель «🍽 Меню», переход с главной, deep-link из бота |
| Назначение | Обзор плана, рекомендация нутрициолога, быстрые действия, переходы внутрь |
| Данные | `plan_summary`, `nutritionist_advice`, `today_meals`, `home_attendance`, `settings_summary`, `meal_leftovers_count` |
| API | `GET /menus/overview`, `POST /menus/overview/quick-action` |
| Компоненты | `MenuHub`, `ScreenLayout`, `ProtectedScreenFallback`, `PageLoading` |
| Изменяет данные | Может пересоздать меню через quick-action |
| Состояния | `loadState`, `acting`, `message`, `settingsOpen` |
| Модальные | Inline-аккордеон «Настройки меню» |
| Возврат | Нижняя панель |
| Дубликат | Блок «Сегодня» = главная; `Настройки меню` ≡ `/menu/settings` |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| Составить меню | `/menu` (empty) | navigate | `/menu/generate` | — | — |
| Обновить меню | `/menu` (needs_update) | navigate | `/menu/generate` | — | — |
| Сделать дешевле | `/menu` | quick-action | redirect или сообщение | `POST /menus/overview/quick-action` | `cheaper` → 402/400 |
| Использовать запасы | `/menu` | quick-action | сообщение | `POST /menus/overview/quick-action` | — |
| Больше белка | `/menu` | quick-action | сообщение | `POST /menus/overview/quick-action` | — |
| Меньше времени на готовку | `/menu` | quick-action | сообщение | `POST /menus/overview/quick-action` | — |
| Заменить блюдо | `/menu` | navigate | `/menu/current?replace=1` | `POST /menus/overview/quick-action` | — |
| Подробнее → | `/menu` | navigate | `/menu/current` | — | — |
| Открыть все дни → | `/menu` | navigate | `/menu/current` | — | — |
| Изменить на сегодня → | `/menu` | navigate | `/menu/settings` | — | — |
| Настройки меню (раскрыть) | `/menu` | toggle | inline | — | — |
| Изменить → (в раскрытом блоке) | `/menu` | navigate | `/menu/settings` | — | — |
| Остатки блюд | `/menu` | navigate | `/menu/leftovers` | — | — |
| Рецепты | `/menu` | navigate | `/recipes` | — | — |
| Текущее меню → | `/menu` | navigate | `/menu/current` | — | — |
| Повторить | `/menu` (error) | refetch | — | `GET /menus/overview` | сеть |
| На главную | `/menu` (error) | navigate | `/` | — | — |

---

## 3. Мастер генерации — `/menu/generate`

| Поле | Значение |
|---|---|
| Тип | route + полноэкранный preview (modal) |
| Файл | `app/menu/generate/page.tsx` → `components/menu/MenuPlanner.tsx` |
| Где открывается | Кнопка «Составить меню», «Обновить меню» |
| Назначение | Мастер 4–5 шагов и выбор одного из 3 вариантов |
| Данные | Цель, персоны, дни, бюджет, режим плана, статус чеклиста; готовые варианты |
| API | `GET /nutrition/profile`, `GET /menus/selected`, `GET /pantry`, `POST /menus/generate`, `POST /menus/select` |
| Компоненты | `MenuPlanner`, `MenuWizardSteps`, `MenuChooseVariants`, `MenuVariantCard`, `MenuPlannerSection`, `StickyBottomBar` |
| Изменяет данные | `family_menu_selections` после `selectMenu` |
| Состояния | `phase` (setup/choose), `wizardStep`, `wizardGoal`, `goalStepError`, `generating`, `selecting`, `previewMenu`, `generateSuccess`, `personsCount`, `planMode`, `wizardBudget`, `wizardDays` |
| Модальные | Полноэкранный preview варианта (`previewMenu`) |
| Возврат | `← Меню`, `← Назад к настройкам`, `Назад` по шагу |
| Дубликат | «Бюджет» и «Режим плана» — два шага про деньги |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| ← Меню | wizard | navigate | `/menu` | — | — |
| ← Назад к настройкам | choose | `setPhase('setup')` | inline | — | — |
| Чипы целей | step 0 | `setWizardGoal` | inline | — | required |
| Чипы персон | step 1 (family) | `setPersonsCount` | inline | — | — |
| Чипы дней | step 2 | `setWizardDays` | inline | — | — |
| Чипы бюджета | step 3 | `setWizardBudget` | inline | — | — |
| Чипы режима плана | step 3 | `changePlanMode` | `localStorage` | — | — |
| Назад | sticky | `setWizardStep(s-1)` | inline | — | — |
| Продолжить | sticky | `handleWizardContinue` | inline | — | «Выберите цель» |
| Сгенерировать меню | sticky (last step) | `handleGenerate` | choose-фаза | `POST /menus/generate` | 402 menu_generation_limit, сеть |
| Выбрать вариант | `MenuChooseVariants` | `handleSelect` | `/menu/current?saved=1` | `POST /menus/select` | 400/500 |
| ← Назад к выбору | preview modal | `setPreviewMenu(null)` | inline | — | — |
| Открыть план → | success banner | navigate | `/menu/current` | — | — |
| Тариф и Амы → | error 402 | navigate | `/subscription` | — | — |
| Открыть план → | секция «Текущий план» | navigate | `/menu/current` | — | — |

---

## 4. Текущий план — `/menu/current`

| Поле | Значение |
|---|---|
| Тип | route + модалка замены |
| Файл | `app/menu/current/page.tsx` → `components/menu/MenuCurrentView.tsx` |
| Где открывается | «Подробнее», «Текущее меню», «Открыть план», «Заменить блюдо» |
| Назначение | Просмотр меню по дням, замена блюд, чекины приёмов |
| Данные | `MenuVariant`, `selected_at`, `meal_checkins` на дату |
| API | `GET /menus/selected`, `POST /menus/replace-dish`, `POST /menus/select`, `GET /meal-checkins/today`, `POST /meal-checkins` |
| Компоненты | `MenuCurrentView`, `MenuDayPicker`, `MenuVariantCard`, `MealCheckinPanel`, `ReplaceDishModal` |
| Изменяет данные | `family_menu_selections`, `meal_checkins`, опосредованно `meal_leftovers` |
| Состояния | `menu`, `dayIndex`, `replaceTarget`, `replacing`, `error`, `justSaved` |
| Модальные | `ReplaceDishModal` |
| Возврат | `back={ label: "Меню", href: "/menu" }` |
| Дубликат | Карточка варианта = в мастере |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| ← Меню | header | navigate | `/menu` | — | — |
| Настроить план | empty state | navigate | `/menu` | — | — |
| Чипы дней | `MenuDayPicker` | `setDayIndex` | inline | — | — |
| Заменить блюдо (в карточке) | `MenuVariantCard` | open modal | `ReplaceDishModal` | — | — |
| Заменить (в модалке) | `ReplaceDishModal` | `handleReplace` | inline | `POST /menus/replace-dish`, `POST /menus/select` | 402/500 |
| Где поели: дома / работа / кафе / ресторан / доставка / другое | `MealCheckinPanel` | `markMeal` | inline | `POST /meal-checkins` | сеть |
| Член семьи (чип) | `MealCheckinPanel` | `setMemberId` | inline | — | — |
| Остатки блюд | bottom | navigate | `/menu/leftovers` | — | — |
| Закрыть модалку | `ReplaceDishModal` | `onClose` | inline | — | — |

---

## 5. Остатки блюд — `/menu/leftovers`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/menu/leftovers/page.tsx` → `components/menu/MealLeftoversPage.tsx` |
| Где открывается | Из `/menu`, `/menu/current`, бот `quick:leftover`, из чекинов |
| Назначение | CRUD по остаткам блюд, изменение статуса |
| Данные | Список остатков, статусы, кто добавил |
| API | `GET /meal-leftovers`, `POST /meal-leftovers`, `PATCH /meal-leftovers/{id}`, `DELETE /meal-leftovers/{id}` |
| Компоненты | `MealLeftoversPage`, `StickyBottomBar` |
| Изменяет данные | `meal_leftovers` |
| Состояния | `items`, `dishName`, `portions`, `saving`, `updatingId`, `saveSuccess` |
| Модальные | Нет |
| Возврат | `back={ label: "Меню", href: "/menu" }` |
| Дубликат | Создание остатка = бот сценарий `quick:leftover` + автодобавление через чекины |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| ← Меню | header | navigate | `/menu` | — | — |
| Удалить | list item | `deleteMealLeftover` | inline | `DELETE /meal-leftovers/{id}` | 404 |
| Статус (Активно / Доедено / Заморожено / Испорчено) | list item | `setStatus` | inline | `PATCH /meal-leftovers/{id}` | 422 |
| Добавить остаток | sticky form | `handleAdd` | inline | `POST /meal-leftovers` | validation |
| Отметить приёмы пищи в меню → | bottom | navigate | `/menu/current` | — | — |

---

## 6. Настройки меню — `/menu/settings`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/menu/settings/page.tsx` → `components/menu/MenuSettingsPage.tsx` |
| Где открывается | «Изменить на сегодня», «Изменить →» из `/menu` |
| Назначение | Override персон и режима плана в `localStorage` |
| Данные | `planMode`, `personsOverride` (только локально) |
| API | — |
| Компоненты | `MenuSettingsPage`, `StickyBottomBar` |
| Изменяет данные | `localStorage.planam_*` |
| Состояния | `personsOverride`, `planMode`, `saved` |
| Модальные | Нет |
| Возврат | Через `ScreenLayout` (back в `/menu`) |
| Дубликат | Дублирует шаги мастера 1–3 |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| Override toggle | top | toggle | inline | — | — |
| Чипы персон | inline | `setPersonsOverride` | `localStorage` | — | — |
| Чипы режимов | inline | `setPlanMode` | `localStorage` | — | — |
| Сохранить | sticky | save to `localStorage` | — | — | — |
| Обновить меню | secondary | navigate | `/menu/generate` | — | — |

---

## 7. Меню → Рецепты (alias) — `/menu/recipes`

| Поле | Значение |
|---|---|
| Тип | route (redirect) |
| Файл | `app/menu/recipes/page.tsx` |
| Назначение | `redirect("/recipes")` для обратной совместимости |
| API | — |
| Кнопки | — |
| Дубликат | Да, существует только для совместимости |

---

## 8. План события — `/menu/event`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/menu/event/page.tsx` |
| Где открывается | В UI ссылок нет (черновик) |
| Назначение | Планирование застолья, экспорт в покупки |
| API | `POST /event-plans`, `POST /event-plans/{id}/shopping` |
| Состояния | поля формы (`guests`, `theme`, `cuisine`, `drink_menu_mode`, `alcohol_enabled`) |
| Возврат | `← Меню` |
| Дубликат | Конкурирует с мастером меню; путь не публиковался |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| ← Меню | header | navigate | `/menu` | — | — |
| Поля формы | inline | local state | — | — | required |
| Сгенерировать план | inline | submit | inline | `POST /event-plans` | 402, 422 |
| Добавить в покупки | inline | sync | `/shopping` | `POST /event-plans/{id}/shopping` | 400 |

---

## 9. Покупки — `/shopping`

| Поле | Значение |
|---|---|
| Тип | route + 3 sheet'а |
| Файл | `app/shopping/page.tsx` → `components/shopping/ShoppingListView.tsx` |
| Где открывается | Нижняя панель, главная, deep-link из бота, после `pending` подтверждений |
| Назначение | Список покупок, категории, синхронизация с пантри |
| Данные | `ShoppingList.items[]`, категории, `updated_at` |
| API | `GET /shopping/list`, `POST /shopping/items`, `PATCH /shopping/items/{id}`, `DELETE /shopping/items/{id}`, `PATCH /shopping/items/{id}/toggle`, `POST /shopping/sync`, `GET/POST /shopping/categories` |
| Компоненты | `ShoppingListView`, `ShoppingCategorySection`, `ShoppingItemSheet`, `ShoppingCategorySheet`, `CategoryPicker`, `ModeBanner`, `BotQuickInputHint` |
| Изменяет данные | `family_shopping_lists`, `shopping_categories`, опосредованно `family_pantry_items` (при `checked`) |
| Состояния | `list`, `loading`, `syncing`, `saving`, `togglingId`, `error`, `search`, `hideChecked`, `expanded`, `itemSheetOpen`, `categorySheetOpen`, `editingItem`, `itemDraft`, `newCategoryName`, `newCategoryIsFood`, `saveSuccess` |
| Модальные | `ShoppingItemSheet`, `ShoppingCategorySheet` |
| Возврат | Системная панель |
| Дубликат | `BotQuickInputHint` повторяется в `/pantry` |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| + Добавить (товар) | header | open sheet | `ShoppingItemSheet` | — | — |
| Категория (выбор) | sheet | `CategoryPicker` | inline | `GET /shopping/categories` | — |
| Сохранить (новый) | sheet | submit | inline | `POST /shopping/items` | 422 |
| Сохранить (правка) | sheet | submit | inline | `PATCH /shopping/items/{id}` | 404 |
| Удалить | sheet | delete | inline | `DELETE /shopping/items/{id}` | 404 |
| Чекбокс товара | section | toggle | inline | `PATCH /shopping/items/{id}/toggle` | сеть |
| + Категория | category sheet | submit | inline | `POST /shopping/categories` | duplicate |
| Синхронизировать с меню | header | sync | inline | `POST /shopping/sync` | 500 |
| Поиск | header | local filter | — | — | — |
| Скрыть купленные | filter | toggle | — | — | — |
| Развернуть/свернуть категорию | section | toggle | — | — | — |

---

## 10. Запасы — `/pantry`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/pantry/page.tsx` → `components/pantry/PantryDashboard.tsx` |
| Где открывается | Нижняя панель, главная, deep-link из бота, после чекбокса в покупках |
| Назначение | Управление запасами, фильтры по сроку и источнику |
| Данные | Список позиций пантри, активные / истёкшие, дни до истечения |
| API | `GET /pantry`, `POST /pantry`, `PATCH /pantry/{id}`, `DELETE /pantry/{id}`, `GET /shopping/categories` (для подсказки) |
| Компоненты | `PantryDashboard`, `PantryCategorySection`, `PantryItemRow`, `PantryItemForm`, `BotQuickInputHint`, `ModeBanner` |
| Изменяет данные | `family_pantry_items` |
| Состояния | `items`, `activeCount`, `filter`, `expanded`, `formOpen`, `editingItem`, `draft`, `categories`, `saveSuccess` |
| Модальные | Inline `PantryItemForm` |
| Возврат | Системная панель |
| Дубликат | Заголовок и `BotQuickInputHint` = `/shopping` |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| + Добавить | header | open form | inline | — | — |
| Фильтры (Все / Скоро / Недавно / Из покупок / Вручную) | tabs | `setFilter` | — | — | — |
| Сохранить | form | submit | inline | `POST /pantry` или `PATCH /pantry/{id}` | 422 |
| Удалить | row | delete | inline | `DELETE /pantry/{id}` | 404 |
| ↑ К покупкам | bottom | navigate | `/shopping` | — | — |

---

## 11. Рецепты (каталог) — `/recipes`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/recipes/page.tsx` → `components/recipes/RecipeCatalog.tsx` + `RecipeCatalogSections.tsx` |
| Где открывается | `/menu`, `/nutritionist`, главная (через advice CTA), `/menu/recipes` (redirect) |
| Назначение | Каталог рецептов с секциями и поиском |
| Данные | Списки по секциям, фильтры по приёму пищи и диете |
| API | `GET /recipes`, `GET /recipes/filters`, `POST /recipes/{id}/favorite` |
| Компоненты | `RecipeCatalog`, `RecipeCatalogSections`, `RecipeCard` |
| Изменяет данные | `recipe_ratings` (favorite toggle) |
| Состояния | `query`, `togglingId`, фильтры |
| Возврат | Системная панель |
| Дубликат | — |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| Поиск | header | debounce | inline | `GET /recipes?q=` | — |
| Чипы (Завтрак/Обед/Ужин/Перекус) | filter | smart-query | inline | `GET /recipes` | — |
| Карточка | card | navigate | `/recipes/[id]` | — | — |
| В избранное | card | toggle | inline | `POST /recipes/{id}/favorite` | — |
| Показать ещё | section | paginate | inline | `GET /recipes` | — |

---

## 12. Карточка рецепта — `/recipes/[id]`

| Поле | Значение |
|---|---|
| Тип | route (без модалки, страница использует `RecipeDetailModal` как фуллскрин) |
| Файл | `app/recipes/[id]/page.tsx` → `components/recipes/RecipeDetailModal.tsx` |
| Где открывается | Карточка из каталога, advice-card в `/menu` |
| Назначение | Детали рецепта, оценка, совместимость с семьёй, добавление в покупки/меню |
| Данные | `RecipeDetail`, `RecipeEvaluation`, `RecipeFamilyFit`, `RecipeImproveSuggestion[]` |
| API | `GET /recipes/{id}`, `POST /recipes/{id}/favorite`, `POST /recipes/{id}/add-to-shopping`, `GET /recipes/{id}/evaluate`, `GET /recipes/{id}/family-compatibility`, `GET /recipes/{id}/improve`, `POST /recipes/{id}/add-to-menu` |
| Компоненты | `RecipeDetailModal` |
| Изменяет данные | `family_shopping_lists`, `family_menu_selections`, `recipe_ratings` |
| Состояния | `recipe`, `evaluation`, `familyFit`, `suggestions`, `adding`, `addingShopping`, `togglingFavorite`, `message` |
| Возврат | `← Каталог` |
| Дубликат | — |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| ← Каталог | header | navigate | `/recipes` | — | — |
| В избранное | header | toggle | inline | `POST /recipes/{id}/favorite` | — |
| В покупки | actions | add | toast | `POST /recipes/{id}/add-to-shopping` | 422 |
| В меню | actions | add (день/приём) | toast | `POST /recipes/{id}/add-to-menu` | 422 |
| Улучшить | analysis | reload | inline | `GET /recipes/{id}/improve` | 402 ams |
| Совместимость | analysis | reload | inline | `GET /recipes/{id}/family-compatibility` | 402 ams |
| Оценить | analysis | reload | inline | `GET /recipes/{id}/evaluate` | 402 ams |

---

## 13. Нутрициолог — `/nutritionist`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/nutritionist/page.tsx` → `components/nutritionist/NutritionistDashboard.tsx` |
| Где открывается | Нижняя панель «🥗 Нутрициолог», CTA с главной/`/menu` |
| Назначение | Дневной статус, прогресс цели, советы, отложенные рекомендации, быстрые действия |
| Данные | `nutrition_profile`, `selected_menu`, `pantry`, `progress_overview`, `subscription_overview`, `deferred_advice`, `suppressed_titles` |
| API | `GET /nutrition/profile`, `GET /menus/selected`, `GET /pantry`, `GET /progress/overview`, `GET /subscription/overview`, `GET /nutritionist/water/today`, `POST /nutritionist/water`, `GET/POST/PATCH/DELETE /nutritionist/deferred-advice`, `GET /nutritionist/deferred-advice/suppressed-titles`, `POST /nutritionist/ask` (через чат) |
| Компоненты | `NutritionistDashboard`, `NutritionistAdviceCard`, `WaterIntakePanel`, `CareTelegramLinkCard` |
| Изменяет данные | `water_intake_logs`, `deferred_nutrition_advice` |
| Состояния | `profile`, `menu`, `pantry`, `progress`, `familySummaryOpen`, `familyProgressOpen`, `deferredAdvice`, `suppressedTitles` |
| Модальные | Аккордеоны «Семейная сводка» и «Прогресс семьи» |
| Возврат | Системная панель |
| Дубликат | Дневной KPI пересекается с `/progress`; совет дублирует `/menu`; advice-deferred мигрируется из `localStorage` |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| Открыть профиль (incomplete) | banner | navigate | `/profile/nutrition?returnTo=/nutritionist` | — | — |
| Отметить, где поели → | KPI | navigate | `/menu/current` | — | — |
| + 100/200/300 мл (вода) | `WaterIntakePanel` | submit | inline | `POST /nutritionist/water` | 422 |
| Не сейчас (advice) | `NutritionistAdviceCard` | defer | inline | `POST /nutritionist/deferred-advice` | 409 dup |
| Добавить в меню (advice CTA) | `NutritionistAdviceCard` | navigate | `/menu/generate?...` | — | — |
| Найти рецепт | `NutritionistAdviceCard` | navigate | `/recipes?...` | — | — |
| Добавить в покупки | `NutritionistAdviceCard` | navigate | `/shopping?...` | — | — |
| Выполнить (deferred) | section | submit | inline | `PATCH /nutritionist/deferred-advice/{id}` | 404 |
| Вернуть (deferred) | section | submit | inline | `DELETE /nutritionist/deferred-advice/{id}` | 404 |
| Удалить (deferred) | section | submit | inline | `PATCH /nutritionist/deferred-advice/{id}` (`dismissed`) | 404 |
| Спросить нутрициолога | quick | navigate | `/nutritionist/chat` | — | — |
| Добавить вес | quick | navigate | `/progress?focus=weight&returnTo=/nutritionist` | — | — |
| Добавить тренировку | quick | navigate | `/progress?focus=training&returnTo=/nutritionist` | — | — |
| Изменить цель | quick | navigate | `/profile/nutrition?returnTo=/nutritionist` | — | — |
| Открыть чат нутрициолога | bottom | navigate | `/nutritionist/chat` | — | — |
| Семейная сводка / Прогресс семьи | accordion | toggle | inline | — | — |
| Подробнее в прогрессе → | family progress | navigate | `/progress` | — | — |

---

## 14. Чат нутрициолога — `/nutritionist/chat`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/nutritionist/chat/page.tsx` |
| Где открывается | `Спросить нутрициолога` из `/nutritionist`, нижний CTA |
| Назначение | Q&A с AI-нутрициологом (Амы) |
| API | `POST /nutritionist/ask`, `GET /subscription/overview` |
| Изменяет данные | `ai_usage_logs`, `ama_transactions` |
| Состояния | `messages`, `pending`, `ams_balance` |
| Возврат | `← Нутрициолог` |
| Дубликат | Действие «вопрос» дублируется через бот (`bot_input` AI) |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| ← Нутрициолог | header | navigate | `/nutritionist` | — | — |
| Спросить | chat | submit | inline | `POST /nutritionist/ask` | 402 ams |
| Перейти к тарифу | error | navigate | `/subscription` | — | — |

---

## 15. Забота (Care) — `/nutritionist/care` (и `/settings/care`)

| Поле | Значение |
|---|---|
| Тип | route, два пути |
| Файлы | `app/nutritionist/care/page.tsx`, `app/settings/care/page.tsx` → `components/care/CareSettingsPanel.tsx` |
| Где открывается | Из шапки `/nutritionist`, из `/settings` |
| Назначение | Управление режимом care-уведомлений |
| API | `GET /care/settings`, `PATCH /care/settings`, `POST /care/settings/test` |
| Изменяет данные | `care_settings` |
| Состояния | `level`, `flags`, `quietHours`, `timezone`, `testing` |
| Возврат | Системная панель |
| Дубликат | **Полный дубль на двух URL** |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| minimal / standard / active | toggle | submit | inline | `PATCH /care/settings` | 422 |
| Переключатели типов | switches | submit | inline | `PATCH /care/settings` | 422 |
| Поля «тихих часов» / timezone | inputs | submit | inline | `PATCH /care/settings` | 422 |
| Отправить тестовое | bottom | trigger | toast | `POST /care/settings/test` | 500 |

---

## 16. Профиль — `/profile`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/profile/page.tsx` → `components/profile/ProfileDashboard.tsx` |
| Где открывается | Иконка в шапке `/`, переход «← Профиль» из подэкранов |
| Назначение | Хаб профиля, переключатель режима, прогресс заполнения |
| API | `GET /nutrition/profile`, `POST /users/app-mode` |
| Компоненты | `ProfileDashboard`, `ProfileModeControl` |
| Изменяет данные | `user_preferences.active_mode` |
| Состояния | `nutrition`, `loadingNutrition`, `modeLoading` |
| Возврат | Иконка-шестерёнка ведёт на `/settings`; на главную — через нижнюю панель |
| Дубликат | Часть пунктов меню дублирует `/settings` (`О приложении`, `Уведомления`) |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| Шестерёнка | header | navigate | `/settings` | — | — |
| Питание | menu | navigate | `/profile/nutrition` | — | — |
| Семья | menu | navigate | `/family` | — | — |
| Подписка | menu | navigate | `/subscription` | — | — |
| Прогресс | menu | navigate | `/progress` | — | — |
| Уведомления | menu | navigate | `/notifications` | — | — |
| О приложении | menu | navigate | `/settings/about` | — | — |
| Переключатель режима | `ProfileModeControl` | submit | inline | `POST /users/app-mode` | 409 |

---

## 17. Профиль питания — `/profile/nutrition`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/profile/nutrition/page.tsx` → `components/nutrition-profile/NutritionProfileForm.tsx` (+ `NutritionSection`, `NutritionGoalDetailsFields`, `MultiSelectField`, `NumberInput`, `ToggleRow`) |
| Где открывается | `/profile`, баннеры в `/nutritionist` и `/menu` |
| Назначение | Заполнение профиля питания (возраст, вес, цели, диеты, аллергии, ограничения, PRO-данные) |
| API | `GET /nutrition/profile`, `POST /nutrition/profile` |
| Изменяет данные | `user_profiles` |
| Состояния | `formState`, `expandedSections`, `saving`, `returnTo` |
| Возврат | По `returnTo` (если задан) или `/profile` |
| Дубликат | — |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| Аккордеоны секций | header | toggle | inline | — | — |
| Чипы (цель, диеты, аллергии, ограничения, любимое/нелюбимое) | `MultiSelectField` | toggle | inline | — | — |
| Поля числовые (возраст, рост, вес, целевой) | `NumberInput` | local | inline | — | required |
| Сложность блюд | `ToggleRow` | toggle | inline | — | — |
| Сохранить | sticky | submit | `returnTo` | `POST /nutrition/profile` | 422 |

---

## 18. Прогресс — `/progress`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/progress/page.tsx` → `components/progress/ProgressDashboard.tsx` |
| Где открывается | `/profile`, `/nutritionist` (deep-link с `focus=weight/training`) |
| Назначение | Вес, замеры, тренировки, прогресс к цели, приватность для семьи |
| API | `GET /progress/overview`, `POST /progress/entries`, `POST /progress/trainings`, `PATCH /progress/privacy` |
| Изменяет данные | `progress_entries`, `training_entries`, `user_profiles.privacy_flags` |
| Состояния | `data`, `showWeightForm`, `showTrainingForm`, поля форм, `saving`, `error` |
| Возврат | `back={ returnTo }` (по умолчанию `/profile`) |
| Дубликат | KPI пересекается с `/nutritionist` (Прогресс к цели) |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| ← Назад | header | navigate | `returnTo` | — | — |
| Добавить вес | top | open form | inline | — | — |
| Добавить тренировку | top | open form | inline | — | — |
| Поля формы | inline | local | — | — | required |
| Сохранить (вес) | form | submit | inline | `POST /progress/entries` | 422 |
| Сохранить (тренировка) | form | submit | inline | `POST /progress/trainings` | 422 |
| Скрыть / Показать (семье) | privacy | submit | inline | `PATCH /progress/privacy` | 403 |
| Отмена | form | close | inline | — | — |

---

## 19. Подписка — `/subscription`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/subscription/page.tsx` → `components/subscription/SubscriptionDashboard.tsx` |
| Где открывается | `/profile`, баннеры лимитов в `/menu/generate`, `/nutritionist/chat`, бот |
| Назначение | Текущий тариф, баланс Амов, история, выбор тарифа, заглушка покупки Амов |
| API | `GET /subscription/overview`, `POST /subscription/select` |
| Изменяет данные | `user_subscriptions`, `ama_transactions` (выбор) |
| Состояния | `data`, `selecting`, `message` |
| Возврат | `back={ label: "Профиль", href: "/profile" }` |
| Дубликат | Кнопка «Купить Амы» — заглушка |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| ← Профиль | header | navigate | `/profile` | — | — |
| Выбрать тариф | plan card | submit | inline | `POST /subscription/select` | 403 (не админ семьи) |
| Купить Амы (заглушка) | bottom | disabled | — | — | — |

---

## 20. Семья — `/family`

| Поле | Значение |
|---|---|
| Тип | route + 4 sheet'а + полноэкранная форма |
| Файл | `app/family/page.tsx` → `components/family/FamilyDashboard.tsx` |
| Где открывается | `/profile`, баннер с главной (если family-режим) |
| Назначение | Создание/управление семьёй, участники, виртуальные участники, приглашения |
| API | `GET /families/me`, `POST /families`, `PATCH /families/{id}`, `POST /families/{id}/members`, `PATCH /families/{id}/members/{member_id}`, `DELETE /families/{id}/members/{member_id}`, `POST /families/{id}/invites`, `POST /families/{id}/virtual-members`, `PATCH /families/me/allow-admin-edit` |
| Компоненты | `FamilyDashboard`, `MemberCard`, `MemberForm`, `AddPersonSheet`, `InviteSheet`, `FamilyManageSheet`, `VirtualMemberNutritionForm`, `RoleBadge` |
| Изменяет данные | `families`, `family_members`, `family_invites` |
| Состояния | `family`, `showAddPerson`, `showInviteSheet`, `showManage`, `editingMember`, `showNutritionForm`, `virtualDraft`, `lastInvite` |
| Модальные | `AddPersonSheet`, `InviteSheet`, `FamilyManageSheet`, полноэкранная форма нутрициологии |
| Возврат | `back={ label: "Профиль", href: "/profile" }` |
| Дубликат | Два пути добавления участника (телеграм-приглашение + виртуальный) |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| Создать семью | empty state | submit | inline | `POST /families` | 422 (имя), 409 (уже в семье) |
| Управление семьёй | header | open `FamilyManageSheet` | sheet | — | — |
| + Добавить человека | top | open `AddPersonSheet` | sheet | — | — |
| Пригласить в Telegram | `AddPersonSheet` | open `InviteSheet` | sheet | `POST /families/{id}/invites` | 422, 409 |
| Виртуальный участник | `AddPersonSheet` | open form | inline | `POST /families/{id}/virtual-members` | 422, plan limit |
| Редактировать (питание) | `MemberCard` | open form | inline | `PATCH /families/{id}/members/{member_id}` | 403 |
| Удалить участника | `MemberCard` | confirm + delete | inline | `DELETE /families/{id}/members/{member_id}` | 403 |
| Передать админа | `FamilyManageSheet` | submit | inline | `PATCH /families/{id}` (admin transfer) | 403, 404 |
| Разрешить админу править | `FamilyManageSheet` | submit | inline | `PATCH /families/me/allow-admin-edit` | 403 |
| Сохранить (форма участника) | `VirtualMemberNutritionForm` | submit | inline | `POST` или `PATCH /families/{id}/members/{member_id}` | 422 |
| Отмена | sticky | close | — | — | — |

---

## 21. Уведомления — `/notifications`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/notifications/page.tsx` → `components/notifications/NotificationSettingsForm.tsx` |
| Где открывается | `/profile`, `/settings/support` |
| Назначение | Настройка времени «куплю», «приготовлю завтрак/обед/ужин», часовой пояс, экспорт в календарь |
| API | `GET /notifications/settings`, `PATCH /notifications/settings` |
| Изменяет данные | `user_notification_settings` |
| Состояния | `settings`, `saving`, `timezone`, `addingToCalendar` |
| Возврат | `back={ label: "Профиль", href: "/profile" }` |
| Дубликат | Конкурирует с `/nutritionist/care` (другая модель уведомлений) |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| Переключатели «Покупки / Завтрак / Обед / Ужин» | switches | toggle | inline | `PATCH /notifications/settings` | 422 |
| Поля времени | time-input | submit | inline | `PATCH /notifications/settings` | 422 |
| Часовой пояс | select | submit | inline | `PATCH /notifications/settings` | 422 |
| Добавить в календарь | reminder | download `.ics` | local | — | — |

---

## 22. Настройки (хаб) — `/settings`

| Поле | Значение |
|---|---|
| Тип | route |
| Файл | `app/settings/page.tsx` |
| Где открывается | Иконка-шестерёнка с `/profile` |
| Назначение | Хаб настроек |
| API | — |
| Изменяет данные | — |
| Возврат | Системная панель |
| Дубликат | Многие пункты также есть в `/profile` |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| Аккаунт | menu | navigate | `/settings/account` | — | — |
| Забота | menu | navigate | `/settings/care` | — | — |
| Единицы измерения | menu | navigate | `/settings/units` | — | — |
| Документы | menu | navigate | `/settings/documents` | — | — |
| Удаление данных | menu | navigate | `/settings/delete-data` | — | — |
| Приватность | menu | navigate | `/settings/privacy` | — | — |
| Язык | menu | navigate | `/settings/language` | — | — |
| Поддержка | menu | navigate | `/settings/support` | — | — |
| О приложении | menu | navigate | `/settings/about` | — | — |

---

## 23. Поднастройки

### 23.1 `/settings/account`

| Поле | Значение |
|---|---|
| Файл | `app/settings/account/page.tsx` |
| Назначение | Информация о Telegram-пользователе, ссылка на бот |
| API | `GET /users/me` |
| Изменяет данные | — |
| Кнопки | «← Профиль», «Открыть бота» |

### 23.2 `/settings/care`

Дублирует `/nutritionist/care`. Те же кнопки и API.

### 23.3 `/settings/units` / `/settings/privacy` / `/settings/language`

`SettingsPlaceholder` — статичная заглушка. Кнопок нет.

### 23.4 `/settings/documents`

| Файл | `app/settings/documents/page.tsx` |
| Назначение | Тексты «Правила/Политика/Согласия» |
| API | `GET /legal/documents` |
| Кнопки | «← Настройки», «Принять/отказаться» (если pending) |

### 23.5 `/settings/delete-data`

| Файл | `app/settings/delete-data/page.tsx` |
| Назначение | Запрос на удаление данных |
| API | `POST /users/delete-data` (через бот/email обращение) |
| Кнопки | «Связаться с поддержкой», «← Настройки» |

### 23.6 `/settings/support`

| Файл | `app/settings/support/page.tsx` |
| Назначение | Контакты и FAQ |
| Кнопки | «Открыть бот», «Уведомления», «← Настройки» |

### 23.7 `/settings/about`

| Файл | `app/settings/about/page.tsx` |
| Назначение | Версия, миссия |
| Кнопки | «← Настройки» |

---

## 24. Онбординг — `/onboarding`

| Поле | Значение |
|---|---|
| Тип | route (вне нижней панели) |
| Файл | `app/onboarding/page.tsx` → `components/onboarding/OnboardingWizard.tsx` |
| Где открывается | Первый запуск после регистрации |
| Назначение | Сбор первичного профиля (9 шагов) |
| API | `GET /onboarding/state`, `POST /onboarding/answers` |
| Компоненты | `OnboardingWizard`, `StepContent`, `StepNavigation`, `ProgressBar`, `OnboardingComplete`, `ChipSelect`, `OptionCards`, `ChipSelectWithCustom`, `TextAreaField` |
| Шаги | `welcome` → `goals` → `diets` → `allergies` → `restrictions` → `favoriteFoods` → `dislikedFoods` → `budget` → `cookingTime` |
| Состояния | `data`, `currentStep`, `saving`, `saveHint`, `completed` |
| Возврат | «Назад» — между шагами; завершение → `/` |
| Дубликат | Часть полей дублирует `/profile/nutrition` (можно отредактировать позже) |

### Кнопки

| Кнопка | Экран | Действие | Куда ведёт | API | Ошибки |
|---|---|---|---|---|---|
| Чипы | each step | toggle | inline | — | required next |
| Поля кастомные | inline | local | — | — | — |
| Назад | nav | step − 1 | inline | — | — |
| Далее | nav | step + 1 | inline | `POST /onboarding/answers` | 422 |
| Завершить | last | submit | `/` | `POST /onboarding/answers` | 422 |
| Пропустить | last | submit (`skip`) | `/` | `POST /onboarding/answers` | 422 |

---

## 25. Админка — `/admin/*`

Доступ — через PIN-сессию (Telegram `/admin`). Layout `AdminShell` показывает табы; нижняя панель отключена.

### 25.1 `/admin`

| Поле | Значение |
|---|---|
| Файл | `app/admin/page.tsx` → `components/admin/AdminDashboard.tsx` |
| Назначение | Сводка, табы: пользователи, семьи, подписки, Амы |
| API | `GET /admin/summary`, `GET /admin/users`, `GET /admin/families`, `GET /admin/subscriptions`, `GET /admin/ams`, `GET /admin/ams/summary`, `GET /admin/plans` |
| Кнопки | переход по табам; «Выдать Амы»/«Выдать подписку»/«Заблокировать» с подтверждением |

### 25.2 `/admin/users` и `/admin/users/[id]`

| Файлы | `components/admin/AdminUsersPage.tsx`, `AdminUserDetailPage.tsx` |
| API | `GET /admin/users`, `POST /admin/users/{id}/block`, `POST /admin/users/{id}/unblock`, `POST /admin/users/{id}/delete`, `POST /admin/users/{id}/grant-subscription`, `POST /admin/users/{id}/grant-ams` |
| Кнопки | Поиск, «Заблокировать», «Разблокировать», «Удалить», «Выдать тариф», «Выдать Амы» |

### 25.3 `/admin/families` и `/admin/families/[id]`

| Файлы | `AdminFamiliesListPage.tsx`, `AdminFamilyDetailPage.tsx` |
| API | `GET /admin/families`, `POST /admin/families/{id}/block`, `POST /admin/families/{id}/grant-ams` |
| Кнопки | Поиск, «Блокировать», «Выдать Амы семье», «Открыть детали» |

### 25.4 `/admin/subscriptions`

| Файл | `components/admin/AdminSubscriptionsPage.tsx` |
| API | `GET /admin/subscriptions`, `GET /admin/plans` |
| Кнопки | Фильтр по статусу, «Открыть пользователя» |

### 25.5 `/admin/ams`

| Файл | `components/admin/AdminAmsPage.tsx` |
| API | `GET /admin/ams`, `GET /admin/ams/summary` |
| Кнопки | Фильтры, экспорт |

### 25.6 `/admin/openai`

| Файл | `components/admin/AdminOpenAiPage.tsx` |
| API | `GET /admin/openai/config`, `PATCH /admin/openai/config`, `GET /admin/openai/usage` |
| Кнопки | «Сохранить», «Сбросить», «Перегрузить» |

### 25.7 `/admin/errors`

| Файл | `components/admin/AdminErrorsPage.tsx` |
| API | `GET /admin/errors` |
| Кнопки | Фильтры (период, endpoint, status) |

---

## 26. Дерево экранов

```
Главная (/)
├── Меню (/menu)
│   ├── Генерация (/menu/generate) ─ модалка preview варианта
│   ├── Текущий план (/menu/current) ─ модалка ReplaceDishModal
│   ├── Остатки блюд (/menu/leftovers)
│   ├── Настройки меню (/menu/settings)
│   ├── Рецепты (/menu/recipes) → редирект → /recipes
│   └── Событие (/menu/event) [скрытый]
│
├── Покупки (/shopping)
│   ├── ShoppingItemSheet (модальный)
│   └── ShoppingCategorySheet (модальный)
│
├── Запасы (/pantry)
│   └── PantryItemForm (inline-модал)
│
├── Нутрициолог (/nutritionist)
│   ├── Чат (/nutritionist/chat)
│   └── Care (/nutritionist/care)
│
├── Рецепты (/recipes)
│   └── Карточка (/recipes/[id])
│
└── Профиль (/profile)
    ├── Питание (/profile/nutrition)
    ├── Семья (/family)
    │   ├── AddPersonSheet
    │   ├── InviteSheet
    │   ├── FamilyManageSheet
    │   └── VirtualMemberNutritionForm
    ├── Подписка (/subscription)
    ├── Прогресс (/progress)
    ├── Уведомления (/notifications)
    └── Настройки (/settings)
        ├── Аккаунт (/settings/account)
        ├── Забота (/settings/care)            [дубль /nutritionist/care]
        ├── Единицы (/settings/units)          [заглушка]
        ├── Документы (/settings/documents)
        ├── Удаление данных (/settings/delete-data)
        ├── Приватность (/settings/privacy)    [заглушка]
        ├── Язык (/settings/language)          [заглушка]
        ├── Поддержка (/settings/support)
        └── О приложении (/settings/about)

Отдельные потоки (вне нижней панели):
/onboarding                  — мастер первичного заполнения
/admin                       — админка
├── /admin/users (+ [id])
├── /admin/families (+ [id])
├── /admin/subscriptions
├── /admin/ams
├── /admin/openai
└── /admin/errors
```

---

## Итого по экранам

- Уникальных пользовательских маршрутов: **41** (`apps/web/app/**/page.tsx`).
- Из них stub-страниц: **3** (`/settings/units`, `/settings/privacy`, `/settings/language`).
- Полных дублей: **1** (`/settings/care` = `/nutritionist/care`).
- Redirect-маршрутов: **1** (`/menu/recipes` → `/recipes`).
- Скрытых от UI: **1** (`/menu/event`).
- Модальных листов / форм поверх: **9** (`ReplaceDishModal`, `ShoppingItemSheet`, `ShoppingCategorySheet`, `CategoryPicker`, `PantryItemForm`, `AddPersonSheet`, `InviteSheet`, `FamilyManageSheet`, `VirtualMemberNutritionForm` + полноэкранный preview варианта меню).
- Админских страниц: **7**.
