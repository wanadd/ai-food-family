# Карта кнопок ПланАм

Полный реестр всех видимых пользовательских действий: web (TMA), модальные листы, формы и Telegram-бот. Для каждой кнопки — экран, обработчик, действие, API, результат и ошибки.

> Сокращения: `H` — handler в компоненте; `→` — переход; `T` — toast/inline-сообщение; `M` — открытие модалки/листа.

---

## 1. Глобальная навигация

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| 🥗 Нутрициолог | `BottomNavigation` | `Link` | → `/nutritionist` | — | переход | — |
| 🍽 Меню | `BottomNavigation` | `Link` | → `/menu` | — | переход | — |
| 🏠 ПланАм | `BottomNavigation` | `Link` | → `/` | — | переход | — |
| 🛒 Покупки | `BottomNavigation` | `Link` | → `/shopping` | — | переход | — |
| 📦 Запасы | `BottomNavigation` | `Link` | → `/pantry` | — | переход | — |

---

## 2. Главная (`/`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| Иконка профиля | `/` (header) | `Link` | → `/profile` | — | переход | — |
| Открыть план | `/` | `Link` | → `/menu` | — | переход | — |
| Составить план | `/` (empty plan) | `Link` | → `/menu` | — | переход | — |
| Открыть покупки | `/` | `Link` | → `/shopping` | — | переход | — |
| Открыть (запасы) | `/` | `Link` | → `/pantry` | — | переход | — |

---

## 3. Меню (`/menu`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| Составить меню | `/menu` (empty) | `Link` | → `/menu/generate` | — | переход | — |
| Обновить меню | `/menu` (needs_update) | `Link` | → `/menu/generate` | — | переход | — |
| Сделать дешевле | `/menu` quick | `handleQuickAction("cheaper")` | sync | `POST /menus/overview/quick-action` | T или redirect | 402, 400 |
| Использовать запасы | `/menu` quick | `handleQuickAction("use_pantry")` | sync | `POST /menus/overview/quick-action` | T | 402 |
| Больше белка | `/menu` quick | `handleQuickAction("more_protein")` | sync | `POST /menus/overview/quick-action` | T | 402 |
| Меньше времени на готовку | `/menu` quick | `handleQuickAction("less_time")` | sync | `POST /menus/overview/quick-action` | T | 402 |
| Заменить блюдо | `/menu` quick | `handleQuickAction("replace_dish")` | → `/menu/current?replace=1` | `POST /menus/overview/quick-action` | redirect | 402 |
| Подробнее → | `/menu` | `Link` | → `/menu/current` | — | переход | — |
| Открыть все дни → | `/menu` | `Link` | → `/menu/current` | — | переход | — |
| Изменить на сегодня → | `/menu` | `Link` | → `/menu/settings` | — | переход | — |
| Настройки меню (заголовок) | `/menu` | `toggle` | inline expand | — | UI | — |
| Изменить → (раскрытое) | `/menu` | `Link` | → `/menu/settings` | — | переход | — |
| Остатки блюд | `/menu` | `Link` | → `/menu/leftovers` | — | переход | — |
| Рецепты | `/menu` | `Link` | → `/recipes` | — | переход | — |
| Текущее меню → | `/menu` | `Link` | → `/menu/current` | — | переход | — |
| Повторить (error) | `/menu` | `load()` | refetch | `GET /menus/overview` | reload | сеть |
| На главную (error) | `/menu` | `Link` | → `/` | — | переход | — |

---

## 4. Мастер генерации (`/menu/generate`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| ← Меню | header | `Link` | → `/menu` | — | переход | — |
| ← Назад к настройкам | choose phase | `setPhase("setup")` | inline | — | UI | — |
| Чип цели | step 0 | `setWizardGoal` | inline | — | UI | required |
| Чип персон | step 1 | `setPersonsCount` | inline | — | UI | — |
| Чип дней | step 2 | `setWizardDays` | inline | — | UI | — |
| Чип бюджета | step 3 | `setWizardBudget` | inline | — | UI | — |
| Чип режима плана | step 3 | `changePlanMode` | `localStorage` | — | persist | — |
| Назад (sticky) | wizard | `setWizardStep(s-1)` | inline | — | UI | — |
| Продолжить (sticky) | wizard | `handleWizardContinue` | inline | — | UI | «Выберите цель» |
| Сгенерировать меню (last step) | wizard | `handleGenerate` | sync | `POST /menus/generate` | → choose | 402, сеть |
| Выбрать вариант | `MenuChooseVariants` | `handleSelect` | sync | `POST /menus/select` | → `/menu/current?saved=1` | 422, 500 |
| Тариф и Амы → | error 402 | `Link` | → `/subscription` | — | переход | — |
| Открыть план → | success banner | `Link` | → `/menu/current` | — | переход | — |
| Открыть план → | секция «Текущий план» | `Link` | → `/menu/current` | — | переход | — |
| ← Назад к выбору | preview modal | `setPreviewMenu(null)` | inline | — | UI | — |

---

## 5. Текущий план (`/menu/current`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| ← Меню | header | `Link` | → `/menu` | — | переход | — |
| Настроить план (empty) | content | `Link` | → `/menu` | — | переход | — |
| Чип дня (`MenuDayPicker`) | inline | `setDayIndex` | inline | — | UI | — |
| Заменить блюдо | `MenuVariantCard` | `setReplaceTarget(menu)` | M | — | модал | — |
| Заменить (внутри модалки) | `ReplaceDishModal` | `handleReplace` | sync | `POST /menus/replace-dish`, `POST /menus/select` | reload | 402, 400 |
| Закрыть модалку | `ReplaceDishModal` | `onClose` | inline | — | UI | — |
| Чип статуса (где поели) | `MealCheckinPanel` | `markMeal` | sync | `POST /meal-checkins` | inline | сеть |
| Член семьи (чип) | `MealCheckinPanel` | `setMemberId` | inline | — | UI | — |
| Остатки блюд | bottom | `Link` | → `/menu/leftovers` | — | переход | — |

---

## 6. Остатки блюд (`/menu/leftovers`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| ← Меню | header | `Link` | → `/menu` | — | переход | — |
| Удалить | row | `deleteMealLeftover` | sync | `DELETE /meal-leftovers/{id}` | reload | 404 |
| Чип статуса | row | `setStatus(item, status)` | sync | `PATCH /meal-leftovers/{id}` | reload | 422 |
| Добавить остаток (sticky) | form | `handleAdd` | sync | `POST /meal-leftovers` | reload, focus next | validation |
| Отметить приёмы пищи в меню → | bottom | `Link` | → `/menu/current` | — | переход | — |

---

## 7. Настройки меню (`/menu/settings`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| ← Меню | header | `back` | → `/menu` | — | переход | — |
| Override toggle | inline | `setOverride` | inline | — | UI | — |
| Чип персон | inline | `setPersonsOverride` | `localStorage` | — | persist | — |
| Чип режима | inline | `setPlanMode` | `localStorage` | — | persist | — |
| Сохранить (sticky) | form | `saveSettings` | `localStorage` | — | toast | — |
| Обновить меню | bottom | `Link` | → `/menu/generate` | — | переход | — |

---

## 8. Меню — событие (`/menu/event`, без UI входа)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| Сгенерировать план | inline | `submit` | sync | `POST /event-plans` | inline | 402, 422 |
| Добавить в покупки | inline | `submit` | sync | `POST /event-plans/{id}/shopping` | T | 400 |

---

## 9. Покупки (`/shopping`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| + Добавить | header | `openItemSheet(new)` | M | — | модал | — |
| Поиск (input) | header | `setSearch` | local filter | — | UI | — |
| Скрыть купленные | header | `toggle` | local filter | — | UI | — |
| Синхронизировать с меню | header | `handleSync` | sync | `POST /shopping/sync` | reload | 500 |
| Раскрыть / свернуть категорию | section | `toggleExpand` | inline | — | UI | — |
| Чекбокс товара | row | `handleToggle` | sync | `PATCH /shopping/items/{id}/toggle` | inline + pantry side-effect | сеть |
| Карандаш (редактировать) | row | `openItemSheet(item)` | M | — | модал | — |
| Сохранить (новый) | `ShoppingItemSheet` | `submit` | sync | `POST /shopping/items` | reload | 422 |
| Сохранить (правка) | `ShoppingItemSheet` | `submit` | sync | `PATCH /shopping/items/{id}` | reload | 404 |
| Удалить (в листе) | `ShoppingItemSheet` | `handleDelete` | sync | `DELETE /shopping/items/{id}` | reload | 404 |
| Закрыть лист | `ShoppingItemSheet` | `onClose` | inline | — | UI | — |
| Выбрать категорию | `CategoryPicker` | `onSelect` | inline | — | UI | — |
| Создать категорию | `CategoryPicker` | `openCategorySheet` | M | — | модал | — |
| Сохранить (новая категория) | `ShoppingCategorySheet` | `submit` | sync | `POST /shopping/categories` | reload | duplicate |

---

## 10. Запасы (`/pantry`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| + Добавить | header | `openForm(new)` | inline | — | UI | — |
| Фильтр (Все / Скоро / Недавно / Из покупок / Вручную) | tabs | `setFilter` | local | — | UI | — |
| Сохранить (форма) | `PantryItemForm` | `submit` | sync | `POST /pantry` или `PATCH /pantry/{id}` | reload | 422 |
| Удалить (строка) | `PantryItemRow` | `handleDelete` | sync | `DELETE /pantry/{id}` | reload | 404 |
| Карандаш (редактировать) | `PantryItemRow` | `openForm(item)` | inline | — | UI | — |
| ↑ К покупкам | bottom | `Link` | → `/shopping` | — | переход | — |

---

## 11. Рецепты (`/recipes`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| Поиск | header | `setQuery` | debounce | `GET /recipes?q=` | reload | сеть |
| Чип категории (приёма пищи) | filter | `setMealType` | sync | `GET /recipes?meal_type=` | reload | — |
| Чип диеты | filter | `setDiet` | sync | `GET /recipes?diet=` | reload | — |
| Карточка | card | `onOpen` | → `/recipes/{id}` | — | переход | — |
| В избранное | card | `onToggleFavorite` | sync | `POST /recipes/{id}/favorite` | inline | — |
| Показать ещё | section | `showMore(id)` | local | `GET /recipes` | reload section | — |

---

## 12. Карточка рецепта (`/recipes/[id]`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| ← Каталог | header | `router.push("/recipes")` | переход | — | переход | — |
| В избранное | header | `handleFavorite` | sync | `POST /recipes/{id}/favorite` | inline | — |
| В покупки | actions | `handleAddToShopping` | sync | `POST /recipes/{id}/add-to-shopping` | T | 422 |
| В меню | actions | `handleAddToMenu` | sync | `POST /recipes/{id}/add-to-menu` | T | 422 |
| Оценить | analysis | `evaluateRecipe` | sync | `GET /recipes/{id}/evaluate` | inline | 402 Амов |
| Совместимость | analysis | `fetchRecipeFamilyFit` | sync | `GET /recipes/{id}/family-compatibility` | inline | 402 |
| Улучшить | analysis | `fetchRecipeImproveSuggestions` | sync | `GET /recipes/{id}/improve` | inline | 402 |

---

## 13. Нутрициолог (`/nutritionist`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| Открыть профиль (banner) | top | `Link` | → `/profile/nutrition?returnTo=/nutritionist` | — | переход | — |
| Отметить, где поели → | KPI | `Link` | → `/menu/current` | — | переход | — |
| + 100/200/300 мл (вода) | `WaterIntakePanel` | `addWater` | sync | `POST /nutritionist/water` | reload | 422 |
| Не сейчас (advice) | `NutritionistAdviceCard` | `onDeferred` | sync | `POST /nutritionist/deferred-advice` | reload | 409 |
| Добавить в меню | advice CTA | `Link` | → `/menu/generate?...` | — | переход | — |
| Найти рецепт | advice CTA | `Link` | → `/recipes?search=...` | — | переход | — |
| Добавить в покупки | advice CTA | `Link` | → `/shopping?add=...` | — | переход | — |
| Выполнить (deferred) | section | `completeDeferredAdvice` | sync | `PATCH /nutritionist/deferred-advice/{id}` | reload | 404 |
| Вернуть (deferred) | section | `returnDeferredAdvice` | sync | `DELETE /nutritionist/deferred-advice/{id}` | reload | 404 |
| Удалить (deferred) | section | `dismissDeferredAdvicePermanently` | sync | `PATCH /nutritionist/deferred-advice/{id}` (`dismissed`) | reload | 404 |
| Спросить нутрициолога | quick | `Link` | → `/nutritionist/chat` | — | переход | — |
| Добавить вес | quick | `Link` | → `/progress?focus=weight&returnTo=/nutritionist` | — | переход | — |
| Добавить тренировку | quick | `Link` | → `/progress?focus=training&returnTo=/nutritionist` | — | переход | — |
| Изменить цель | quick | `Link` | → `/profile/nutrition?returnTo=/nutritionist` | — | переход | — |
| Открыть чат нутрициолога | bottom | `Link` | → `/nutritionist/chat` | — | переход | — |
| Семейная сводка (toggle) | accordion | `setFamilySummaryOpen` | inline | — | UI | — |
| Прогресс семьи (toggle) | accordion | `setFamilyProgressOpen` | inline | — | UI | — |
| Подробнее в прогрессе → | family progress | `Link` | → `/progress` | — | переход | — |
| Care: связать Telegram | `CareTelegramLinkCard` | `openBot` | external link | — | переход (бот) | — |

---

## 14. Чат нутрициолога (`/nutritionist/chat`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| ← Нутрициолог | header | `Link` | → `/nutritionist` | — | переход | — |
| Спросить | composer | `submit` | sync | `POST /nutritionist/ask` | inline | 402 Амов |
| Перейти к тарифу | error 402 | `Link` | → `/subscription` | — | переход | — |

---

## 15. Care (`/nutritionist/care`, `/settings/care`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| Уровень (minimal / standard / active) | radio | `setLevel` | sync | `PATCH /care/settings` | inline | 422 |
| Тип уведомления (toggles) | switches | `toggle` | sync | `PATCH /care/settings` | inline | 422 |
| Quiet hours (time) | input | `setQuietHours` | sync | `PATCH /care/settings` | inline | 422 |
| Timezone | select | `setTimezone` | sync | `PATCH /care/settings` | inline | 422 |
| Отправить тестовое | bottom | `runTest` | sync | `POST /care/settings/test` | toast | 500 |

---

## 16. Профиль (`/profile`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| Шестерёнка | header | `Link` | → `/settings` | — | переход | — |
| Питание | menu | `Link` | → `/profile/nutrition` | — | переход | — |
| Семья | menu | `Link` | → `/family` | — | переход | — |
| Подписка | menu | `Link` | → `/subscription` | — | переход | — |
| Прогресс | menu | `Link` | → `/progress` | — | переход | — |
| Уведомления | menu | `Link` | → `/notifications` | — | переход | — |
| О приложении | menu | `Link` | → `/settings/about` | — | переход | — |
| Personal / Family | `ProfileModeControl` | `selectMode` | sync | `POST /users/app-mode` | inline | 409 |

---

## 17. Профиль питания (`/profile/nutrition`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| ← Назад | header | `Link` | → `returnTo` | — | переход | — |
| Аккордеон секции | header | `toggleSection` | inline | — | UI | — |
| Чип (цель / диета / аллергия / ограничение / любимое / нелюбимое) | `MultiSelectField` | `onToggle` | inline | — | UI | — |
| Кастомное значение (input) | `MultiSelectField` | `onAddCustom` | inline | — | UI | dedup |
| Поле числовое (возраст / рост / вес / целевой) | `NumberInput` | `onChange` | inline | — | UI | required |
| Toggle (сложность) | `ToggleRow` | `onChange` | inline | — | UI | — |
| Сохранить (sticky) | bottom | `submit` | sync | `POST /nutrition/profile` | `router.replace(returnTo)` | 422 |

---

## 18. Прогресс (`/progress`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| ← Назад | header | `Link` | → `returnTo` | — | переход | — |
| Добавить вес | top | `setShowWeightForm(true)` | inline | — | UI | — |
| Добавить тренировку | top | `setShowTrainingForm(true)` | inline | — | UI | — |
| Сохранить (вес) | form | `handleAddWeight` | sync | `POST /progress/entries` | reload | 422 |
| Сохранить (тренировка) | form | `handleAddTraining` | sync | `POST /progress/trainings` | reload | 422 |
| Отмена | form | close | inline | — | UI | — |
| Скрыть для семьи (toggle) | privacy | `handlePrivacy` | sync | `PATCH /progress/privacy` | reload | 403 |

---

## 19. Подписка (`/subscription`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| ← Профиль | header | `Link` | → `/profile` | — | переход | — |
| Выбрать тариф | plan card | `handleSelectPlan` | sync | `POST /subscription/select` | toast | 403 |
| Скоро (Купить Амы) | bottom | `disabled` | — | — | — | — |

---

## 20. Семья (`/family`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| ← Профиль | header | `Link` | → `/profile` | — | переход | — |
| Создать семью (empty) | form | `handleCreateFamily` | sync | `POST /families` | reload | 422, 409 |
| Управление семьёй | header | `setShowManage(true)` | M | — | модал | — |
| + Добавить человека | top | `setShowAddPerson(true)` | M | — | модал | — |
| Пригласить в Telegram | `AddPersonSheet` | `setShowInviteSheet(true)` | M | — | модал | — |
| Виртуальный участник | `AddPersonSheet` | `openNewVirtual` | inline | — | inline screen | — |
| Отправить (invite) | `InviteSheet` | `submit` | sync | `POST /families/{id}/invites` | toast | 422, 409, 402 |
| Закрыть лист | sheets | `onClose` | inline | — | UI | — |
| Передать админа | `FamilyManageSheet` | `transferAdmin` | sync | `PATCH /families/{id}` | reload | 403 |
| Разрешить править | `FamilyManageSheet` | `toggleAdminEdit` | sync | `PATCH /families/me/allow-admin-edit` | reload | 403 |
| Удалить семью | `FamilyManageSheet` | `deleteFamily` | sync | `DELETE /families/{id}` | reload | 403 |
| Карандаш (member) | `MemberCard` | `onEditNutrition` | inline | `GET /families/me` (refetch) | UI | — |
| Удалить участника | `MemberCard` | `onDelete` | `confirm() → DELETE` | `DELETE /families/{id}/members/{id}` | reload | 403 |
| Сохранить (форма участника) | `VirtualMemberNutritionForm` | `submit` | sync | `POST` / `PATCH` | reload | 422 |
| Отмена (sticky) | form | `closeMemberForm` | inline | — | UI | — |

---

## 21. Уведомления (`/notifications`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| ← Профиль | header | `Link` | → `/profile` | — | переход | — |
| Toggle покупок / завтрака / обеда / ужина | switches | `togglе(key)` | sync | `PATCH /notifications/settings` | inline | 422 |
| Время | time-input | `setTime` | sync | `PATCH /notifications/settings` | inline | 422 |
| Часовой пояс | select | `setTimezone` | sync | `PATCH /notifications/settings` | inline | 422 |
| Добавить в календарь | reminder | `downloadIcs` | local | — | `.ics` download | iOS WebView |

---

## 22. Настройки (`/settings/*`)

| Кнопка | Экран | Обработчик | Действие | API | Результат |
|---|---|---|---|---|---|
| Аккаунт / Забота / Единицы / Документы / Удаление / Приватность / Язык / Поддержка / О приложении | `/settings` | `Link` | → подэкран | — | переход |
| Открыть бот | `/settings/account` | external link | bot start | — | браузер |
| Принять / Отказаться | `/settings/documents` | `submit` | sync | `POST /legal/accept` | reload |
| Написать в поддержку | `/settings/support` | external link | TG chat | — | переход |
| Связаться по удалению | `/settings/delete-data` | external link | TG / email | — | переход |

---

## 23. Онбординг (`/onboarding`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| Чип (цели / диеты / аллергии / ограничения / бюджет / время) | each step | `setData` | inline | — | UI | required |
| Поля кастомные | inline | `setData` | inline | — | UI | — |
| Назад | nav | `handleBack` | inline | — | UI | — |
| Далее | nav | `handleNext` | sync | `POST /onboarding/answers` | inline | 422 |
| Завершить | last step | `handleFinish` | sync | `POST /onboarding/answers` | → `/` | 422 |
| Пропустить | last step | `handleSkip` | sync | `POST /onboarding/answers` | → `/` | 422 |

---

## 24. Админ-панель (`/admin/*`)

| Кнопка | Экран | Обработчик | Действие | API | Результат | Ошибки |
|---|---|---|---|---|---|---|
| Табы (Дашборд / Пользователи / Семьи / Подписки / Амы / OpenAI / Ошибки) | `AdminShell` | `Link` | → подэкран | — | переход | — |
| Поиск пользователей / семей | list page | `setQuery` | sync | `GET /admin/users?q=` | reload | — |
| Открыть пользователя | row | `Link` | → `/admin/users/[id]` | — | переход | — |
| Открыть семью | row | `Link` | → `/admin/families/[id]` | — | переход | — |
| Заблокировать | `ConfirmButton` | `block` | sync (2-step) | `POST /admin/users/{id}/block` | reload | 403 |
| Разблокировать | `ConfirmButton` | `unblock` | sync (2-step) | `POST /admin/users/{id}/unblock` | reload | 403 |
| Удалить пользователя | `ConfirmButton` (danger) | `delete` | sync (2-step) | `POST /admin/users/{id}/delete` | reload | 403, 409 |
| Выдать Амы | inline form | `submit` | sync | `POST /admin/users/{id}/grant-ams` | reload | 422 |
| Выдать тариф | inline form | `submit` | sync | `POST /admin/users/{id}/grant-subscription` | reload | 422 |
| Заблокировать семью | family row | `block` | sync | `POST /admin/families/{id}/block` | reload | 403 |
| Выдать Амы семье | family detail | `grant` | sync | `POST /admin/families/{id}/grant-ams` | reload | 422 |
| Сохранить OpenAI | `AdminOpenAiPage` | `submit` | sync | `PATCH /admin/openai/config` | inline | 422 |
| Перезагрузить (OpenAI) | `AdminOpenAiPage` | `reload` | sync | `POST /admin/openai/reload` | inline | 500 |
| Фильтры периодов / endpoint / status | `AdminErrorsPage` | `setFilter` | sync | `GET /admin/errors` | reload | — |
| Скопировать (любой row id) | inline | `clipboard` | local | — | T | — |

---

## 25. Telegram Bot — кнопки

### 25.1 Reply-меню (`build_main_menu_keyboard`)

| Кнопка | Обработчик | Действие | API |
|---|---|---|---|
| 🏠 Сегодня | `handle_text_quick_input` (детектор «Сегодня») | `build_today_summary` | внутр. |
| 🍽 Моё меню | `handle_menu_button` | inline «Открыть меню» (web_app) | — |
| 🛒 Покупки | `handle_shopping_button` | inline «Открыть покупки» | — |
| 📦 Запасы | `handle_pantry_button` | inline «Открыть запасы» | — |
| 🥗 Нутрициолог | `handle_nutritionist_button` | inline «Открыть нутрициолога» | — |
| ⚡ Быстро добавить | `handle_quick_add_button` | inline-меню (`quick:*`) | — |
| 👨‍👩‍👧 Семья | `handle_family_button` | inline «Открыть семью» | — |
| ⚙ Настройки | `handle_settings_button` | inline «Открыть настройки», «Документы» | — |
| Пригласить в семью | `handle_invite_family_button` | inline «Создать ссылку» | — |

### 25.2 Quick-add inline (`quick_add_keyboard`)

| callback_data | Обработчик | Действие |
|---|---|---|
| `quick:voice_hint` | подсказка | текст с инструкцией |
| `quick:receipt_hint` | подсказка | текст |
| `quick:leftover` | `start_leftover_flow` | FSM |
| `quick:shopping_hint` | подсказка | текст |
| `quick:pantry_hint` | подсказка | текст |

### 25.3 Legal-callbacks

| callback_data | Обработчик | Действие |
|---|---|---|
| `legal_terms_accept` | `handle_legal_callback` | next доку |
| `legal_terms_decline` | restriction | — |
| `legal_privacy_accept` | next | — |
| `legal_privacy_decline` | restriction | — |
| `legal_personal_accept` | continue | — |
| `legal_personal_decline` | restriction | — |

### 25.4 Семья / приглашения

| callback_data | Обработчик | Действие |
|---|---|---|
| `accept_family_invite:<id>` | `accept_invite` | join family |
| `decline_family_invite:<id>` | `decline_invite` | refuse |
| `create_family_invite_link` | `handle_create_invite_link` | invite link |
| `share_invite_telegram` | `_telegram_share_keyboard` | inline forward |

### 25.5 Pending (text/voice/photo)

| callback_data | Обработчик | Действие |
|---|---|---|
| `pending:confirm` | `handle_pending_callback` | `add_item`/`add_to_pantry`/`add_leftover` для каждой позиции |
| `pending:edit` | `start_pending_edit` | подсказка ввести правки |
| `pending:cancel` | clear FSM | сообщение «отменено» |
| `pending:select:<i>` | toggle item in pending | — |

### 25.6 Регистрация

| Кнопка | Обработчик | Действие |
|---|---|---|
| Поделиться номером | `handle_own_contact` | сохранить телефон |
| Пропустить | `handle_phone_skip` | `phone_skipped=true` |

### 25.7 Админка

| Команда / callback | Обработчик | Действие |
|---|---|---|
| `/admin` | `handle_admin_command` | PIN запрос |
| inline `Открыть админ-панель` | webapp link | `/admin` |

---

## 26. Кнопки без обработчиков / заглушки / частично работающие

| Кнопка | Симптом |
|---|---|
| Купить Амы | `disabled`, нет обработчика |
| Тариф и Амы → | работает только при специфической ошибке 402 |
| `/menu/event` любая | страница не доступна из UI; функция как мёртвая |
| Onboarding `favoriteFoods` / `dislikedFoods` (Далее) | данные сохраняются, но нигде не используются после |
| Чекбокс «подтверждаю» при `Создать семью` | стейт читается только для активации кнопки, не сохраняется в БД |
| «Улучшить / Совместимость / Оценить» в `RecipeDetailModal` | без AI / Амов возвращают пустое значение, без сообщения о причине |
| «Сделать дешевле / Использовать запасы / Больше белка / Меньше времени» | возвращают сообщение, но реального изменения меню не делают (требуют отдельной генерации) |
| `quick:shopping_hint`, `quick:pantry_hint`, `quick:voice_hint`, `quick:receipt_hint` | только текст без CTA |
| «Скоро» (заглушки настроек) | `/settings/units`, `/privacy`, `/language` — без логики |
| Кнопка «Открыть бот» в `/settings/account` | работает, но без deep-link к нужной команде |

---

## 27. Кнопки с дублирующим функционалом

| Группа | Где | Эквивалент |
|---|---|---|
| «Спросить нутрициолога» и «Открыть чат нутрициолога» | `/nutritionist` | оба → `/nutritionist/chat` |
| «Изменить на сегодня →» и «Изменить →» | `/menu` + аккордеон | оба → `/menu/settings` |
| «Подробнее →» и «Открыть все дни →» и «Текущее меню →» | `/menu` | все → `/menu/current` |
| «Заменить блюдо» (карточка `/menu/current`) и quick-action «Заменить блюдо» (`/menu`) | — | один и тот же экшен |
| `/menu/leftovers` ссылка из `/menu`, `/menu/current`, `MealCheckinPanel` | — | один маршрут |
| `/settings/care` и `/nutritionist/care` | — | дубль |
| `/settings/about` и `/profile → О приложении` | — | дубль |
| Onboarding `goals` и `/profile/nutrition.goal` | — | повтор |
| Reply «Семья» и inline `Открыть семью` (bot) | — | повтор |
| `quick:voice_hint` (`bot`) и подсказка `/shopping` (`BotQuickInputHint`) | — | дубль |

---

## 28. Итоги

- Кнопок и интерактивных элементов (web + sheets + bot): **≈360**.
- Из них без обработчиков / disabled: **≈18**.
- Полудлящих кнопок (без CTA / только UI-эффект): **≈20**.
- Дублирующих функционал: **≈22**.
- Самые «нагруженные» экраны: `/nutritionist` (≥22 кнопок), `/menu` (≥17), `/family` (≥15), `/shopping` (≥14).
