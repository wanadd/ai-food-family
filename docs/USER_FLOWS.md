# Карта пользовательских сценариев ПланАм

23 ключевых сценария с пошаговым разбором: цель пользователя, шаги, экраны, данные, API и возможные ошибки. Источник — текущая реализация репозитория.

## Условные обозначения

- `Шаг`: что делает пользователь.
- `Экран / контекст`: где это происходит.
- `Данные`: какие сущности участвуют.
- `API`: какие запросы делает фронт/бот.
- `Ошибки`: реальные ошибки/edge cases, возникающие на текущей реализации.

---

## 1. Первый запуск приложения (TMA)

**Цель**: открыть ПланАм первый раз и попасть в работающее состояние.

| # | Шаг | Экран | Данные | API | Ошибки |
|---|---|---|---|---|---|
| 1 | Открыть мини-приложение по кнопке `Открыть ПланАм` в боте | TMA WebView | — | — | блокировка cookies |
| 2 | `TelegramProvider` парсит `initData` и шлёт `POST /auth/telegram` | техн. | `User` | `POST /auth/telegram` | hashMismatch (403), фолбэк на dev-login |
| 3 | `AppGate` проверяет legal-consent | `LegalConsentScreen` | `users.accepted_*` | `GET /legal/documents` (теоретически) | если отказался — Telegram bot `Доступ временно ограничен` |
| 4 | Проверка наличия `phone_number` | `PhoneRequiredScreen` | `users.phone_number` | — | бот: `Поделиться номером`. Веб: «Откройте бот» |
| 5 | Если есть профиль — переход на `/`, иначе → `/onboarding` | роутер | — | — | `state.completed` отсутствует |
| 6 | Главная отображает «План пока не создан» | `/` | `selected_menu=null` | `GET /menus/selected` | сеть |
| 7 | Нижняя панель и кнопки активны | `/` | — | — | — |

Ключевая ошибка: при отсутствии `NEXT_PUBLIC_API_URL` в проде использовался `localhost:8000` (исправлено через `api-base.ts`).

---

## 2. Регистрация

**Цель**: подтвердить телефон и согласия, чтобы получить доступ к функциям.

| # | Шаг | Экран / контекст | API | Ошибки |
|---|---|---|---|---|
| 1 | Открыть бот → `/start` | Telegram bot | — | блокированный пользователь → отказ |
| 2 | `bot_registration.send_welcome_legal` отправляет 3 документа | Bot | — | TG API failure |
| 3 | Принять «Условия», «Политика», «Согласие на персональные данные» | Bot inline-кнопки | `users.accepted_*`, `legal_accepted_at` | пользователь нажал «Отказаться» → доступ ограничен |
| 4 | Бот: «Поделитесь номером» (`request_contact`) | Bot reply-button | `users.phone_number` | пользователь отправил чужой контакт → `OTHER_PERSON_CONTACT_TEXT` |
| 5 | `handle_own_contact` сохраняет телефон и шлёт invite-список | `upsert_user_from_bot` | — | mismatch с приглашением → `show_invite_mismatch` |
| 6 | `send_registration_complete` → «С возвращением» + кнопка `Открыть ПланАм` | Bot | — | — |

**Альтернативный путь**: «Пропустить» — `phone_skipped=true`, доступ ограничен функциями.

---

## 3. Создание семьи

**Цель**: создать семью и стать её админом.

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/profile` → «Семья» | `/family` (empty) | — | — |
| 2 | Ввести «Семья Ивановых» | input | — | required |
| 3 | Поставить галку «подтверждаю» | checkbox | — | — |
| 4 | tap «Создать семью» | `handleCreateFamily` | `POST /families` | 409 (уже в семье), 422 (имя пустое) |
| 5 | `refreshContext` обновляет `app-context` | `useAppMode` | `GET /users/app-context` | — |
| 6 | Появляется секция «Ваша семья» + «+ Добавить человека» | `/family` | — | — |

---

## 4. Приглашение участника

**Цель**: добавить человека в семью.

**Путь A — по номеру через приложение**:

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/family` → «+ Добавить человека» | `AddPersonSheet` | — | — |
| 2 | «Пригласить в Telegram» | `InviteSheet` | — | — |
| 3 | Ввести `+7…` → «Отправить» | `InviteSheet.submit` | `POST /families/{id}/invites` | 422 (формат), 409 (повторное), 402 (лимит профилей) |
| 4 | Бот приглашаемого: уведомление с кнопками | `notify_invitee_about_invite` | TG API | — |
| 5 | Приглашённый tap «Принять» | bot callback `accept_family_invite:<id>` | `family_invites.accept_invite` | 409 (уже принято) |

**Путь B — invite-link**:

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | Telegram bot: «Пригласить в семью» (reply) | `handle_invite_family_button` | — | не админ |
| 2 | Callback `create_family_invite_link` | `handle_create_invite_link` | `family_invites.create_link_invite` | — |
| 3 | Бот: ссылка + inline «Отправить в Telegram» | `_telegram_share_keyboard` | — | — |
| 4 | Приглашаемый открывает `t.me/<bot>?start=invite_<token>` | bot | — | — |
| 5 | `process_deep_link_invite` → запрос телефона / согласий | bot | — | mismatch |
| 6 | После принятия — добавление в семью | `accept_invite` | — | — |

**Путь C — виртуальный участник**:

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `AddPersonSheet` → «Виртуальный участник» | inline-форма | — | — |
| 2 | Заполнить имя, тип, профиль питания | `VirtualMemberNutritionForm` | — | required |
| 3 | tap «Добавить в семью» | submit | `POST /families/{id}/virtual-members` | 402 (лимит), 422 |

---

## 5. Создание меню

**Цель**: получить три варианта меню и выбрать один.

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/menu` → «Составить меню» | `/menu/generate` (step 0) | `GET /nutrition/profile`, `GET /menus/selected`, `GET /pantry` | сеть |
| 2 | Выбрать цель → «Продолжить» | step 1 (если family) | — | «Выберите цель» |
| 3 | Выбрать персон (family) → «Продолжить» | step 2 | — | — |
| 4 | Выбрать дни → «Продолжить» | step 3 | — | — |
| 5 | Выбрать бюджет и режим → «Продолжить» | step 4 | — | — |
| 6 | Просмотр чеклиста (что учтёт ПланАм) — статусы | inline | — | — |
| 7 | tap «Сгенерировать меню» | `handleGenerate` | `POST /menus/generate` | 402 (trial_expired, menu_generation_limit), сеть |
| 8 | Появляется фаза `choose` с тремя вариантами | `MenuChooseVariants` | — | — |
| 9 | Открыть превью (опционально) | `previewMenu` | — | — |

---

## 6. Выбор варианта меню

**Цель**: сохранить выбранный вариант как активный план.

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | tap «Выбрать вариант» в карточке | `MenuChooseVariants` | — | — |
| 2 | `selectMenu` сохраняет меню | `MenuPlanner.handleSelect` | `POST /menus/select` | 422, 500 |
| 3 | `shopping_list.sync_from_menu` обновляет покупки | сервер | — | — |
| 4 | `care_service.maybe_notify_menu_ready` | сервер | — | — |
| 5 | router.push `/menu/current?saved=1` | client | — | — |
| 6 | Баннер «Меню сохранено» | `/menu/current` | — | — |

---

## 7. Замена блюда

**Цель**: заменить одно блюдо в активном меню.

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/menu/current` → tap «Заменить блюдо» | `MenuVariantCard` | — | — |
| 2 | `ReplaceDishModal` открывается с подсказками | modal | — | — |
| 3 | Ввести хинт → tap «Заменить» | `handleReplace` | `POST /menus/replace-dish` | 402 (trial_expired), 400 (плохой hint), 5 Амов |
| 4 | После — `selectMenu` сохраняет обновлённое меню | client | `POST /menus/select` | — |
| 5 | Закрытие модалки и обновление UI | inline | — | — |

Альтернатива: `/menu` → quick-action `replace_dish` → редирект `/menu/current?replace=1` → модалка.

---

## 8. Просмотр рецепта

**Цель**: открыть карточку рецепта, добавить в покупки / меню / избранное.

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/menu` → «Рецепты» или нутрициолог → «Найти рецепт» | `/recipes` | `GET /recipes`, `GET /recipes/filters` | сеть |
| 2 | tap карточку | `/recipes/[id]` | `GET /recipes/{id}` | 404 |
| 3 | `evaluateRecipe`, `fetchRecipeFamilyFit`, `fetchRecipeImproveSuggestions` | inline | `GET /recipes/{id}/evaluate`, `/family-compatibility`, `/improve` | 402 Амов |
| 4 | tap «В избранное» | header | `POST /recipes/{id}/favorite` | — |
| 5 | tap «В покупки» | actions | `POST /recipes/{id}/add-to-shopping` | 422 |
| 6 | tap «В меню» | actions | `POST /recipes/{id}/add-to-menu` | 422 |

---

## 9. Добавление покупки вручную

**Цель**: добавить новый товар в список покупок.

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/shopping` → tap «+ Добавить» | `ShoppingItemSheet` | — | — |
| 2 | Ввести название, количество, категорию | inline | `GET /shopping/categories` | — |
| 3 | tap «Сохранить» | submit | `POST /shopping/items` | 422 (имя), 500 |
| 4 | Список обновляется (поллинг 4с) | — | `GET /shopping/list` | — |

---

## 10. Голосовое добавление покупки

**Цель**: продиктовать товары боту.

| # | Шаг | Контекст | API | Ошибки |
|---|---|---|---|---|
| 1 | Записать voice в чат бота | bot | — | — |
| 2 | Бот скачивает файл и транскрибирует | `voice_input.transcribe_for_user` | OpenAI Whisper | timeout, недоступен → `VOICE_STUB` |
| 3 | `_parse_with_ai` парсит товары | `bot_input.py` | OpenAI parse | списание Ams `bot_parse_text + voice_command`; нет Амов → подсказка |
| 4 | `bot_pending.store_voice_pending` показывает список | bot inline | — | — |
| 5 | Пользователь tap «Сохранить» (callback) | bot | `shopping.add_item` | 422 (категория) |
| 6 | Бот отвечает «Добавил в покупки» + inline `/shopping` | bot | — | — |

---

## 11. Работа со списком покупок

**Цель**: отметить купленные товары и синхронизировать с запасами.

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/shopping` отображает товары по категориям | `ShoppingCategorySection` | `GET /shopping/list` | — |
| 2 | Поиск / фильтр «Скрыть купленные» | inline | — | — |
| 3 | Чекбокс товара | tap | `PATCH /shopping/items/{id}/toggle` | сеть |
| 4 | На бэке `pantry_shopping.add_or_merge_from_shopping` создаёт позицию в `/pantry` | сервер | — | — |
| 5 | «Синхронизировать с меню» | header | `POST /shopping/sync` | 500 |
| 6 | Поллинг каждые 4 с обновляет `updated_at` | client | `GET /shopping/list` | — |

---

## 12. Работа с запасами

**Цель**: обновить количество, удалить просроченное, добавить вручную.

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/pantry` | `PantryDashboard` | `GET /pantry` | — |
| 2 | Фильтр «Скоро» / «Из покупок» / «Вручную» | tabs | local | — |
| 3 | tap «+ Добавить» | `PantryItemForm` | — | — |
| 4 | Заполнить имя, количество, срок | inline | — | required |
| 5 | tap «Сохранить» | submit | `POST /pantry` | 422 |
| 6 | Удалить позицию | `PantryItemRow` | `DELETE /pantry/{id}` | 404 |

---

## 13. Добавление продукта в запас

**Цель**: положить продукт в запас в момент покупки или OCR чека.

**Способы**:

1. **Вручную** — см. сценарий №12.
2. **Из чекбокса покупок** — см. сценарий №11.
3. **Через фото чека (бот)**:

   | # | Шаг | API | Ошибки |
   |---|---|---|---|
   | 1 | Прислать фото чека в бот | — | — |
   | 2 | `receipt_ocr.parse_receipt_image` | OpenAI Vision | 402 Амов, нет AI → `RECEIPT_STUB_MESSAGE` |
   | 3 | Бот показывает распознанные строки | `bot_pending.store_receipt_pending` | — |
   | 4 | tap «Сохранить в запасы» | `pantry.add_item` | 422 |

4. **Голосом** — аналогично сценарию №10, но с `add_to_pantry` intent.

---

## 14. Работа с остатками блюд

**Цель**: учесть остатки приготовленного блюда.

| # | Шаг | Контекст | API | Ошибки |
|---|---|---|---|---|
| 1 | Открыть `/menu/leftovers` или бот «🍲 Остатки блюда» | UI / bot | — | — |
| 2a | (UI) Ввести «Борщ», «3 порции» → «Добавить остаток» | sticky form | `POST /meal-leftovers` | 422 |
| 2b | (Bot) Ответить на вопрос «Что осталось?» «Борщ» → «3» | FSM `STATE_LEFTOVER_*` | `meal_leftovers.create_leftover` | invalid number |
| 3 | Сменить статус (Доедено / Заморожено / Испорчено) | tap | `PATCH /meal-leftovers/{id}` | 404 |
| 4 | Удалить | tap | `DELETE /meal-leftovers/{id}` | 404 |
| 5 | На следующей генерации меню `expand_variant_to_plan_days` учитывает активные остатки | сервер | — | — |

---

## 15. Работа нутрициолога

**Цель**: получить персональный совет и инструменты.

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/nutritionist` | `NutritionistDashboard` | 5 параллельных GET (`profile`, `menus/selected`, `pantry`, `progress/overview`, `subscription/overview`) | — |
| 2 | Совет выбирается `pickMainAdvice` | client logic | — | — |
| 3 | Кнопки на карточке: «Добавить в меню», «Найти рецепт», «Добавить в покупки», «Не сейчас» | inline / link | `POST /nutritionist/deferred-advice` (defer) | 409 (duplicate) |
| 4 | Отложенные карточки в разделе «Отложенные» | inline | `GET /nutritionist/deferred-advice` + `GET .../suppressed-titles` | — |
| 5 | Чат — `POST /nutritionist/ask` (2 Ама) | `/nutritionist/chat` | — | 402 |

---

## 16. Изменение цели

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/nutritionist` → «Изменить цель» | link с `returnTo` | — | — |
| 2 | Изменить чипы цели в форме | `/profile/nutrition` | — | — |
| 3 | tap «Сохранить» | submit | `POST /nutrition/profile` | 422 |
| 4 | `router.replace(returnTo)` → возврат на `/nutritionist` | — | — | — |
| 5 | `/menu` → banner «Цель изменилась» → «Обновить меню» | `MenuHub` | — | — |
| 6 | Новая генерация — см. сценарий 5 | — | — | — |

---

## 17. Добавление веса

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/nutritionist` → «Добавить вес» | `/progress?focus=weight&returnTo=/nutritionist` | — | — |
| 2 | Форма раскрывается автоматически (focus=weight) | inline | — | — |
| 3 | Заполнить вес, талию, грудь, бёдра, заметку | input | — | required (weight) |
| 4 | tap «Сохранить» | `handleAddWeight` | `POST /progress/entries` | 422 |
| 5 | Обновление KPI + сводки | `/progress` reload | `GET /progress/overview` | — |
| 6 | «← Назад» возвращает в нутрициолог | — | — | — |

---

## 18. Добавление тренировки

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/nutritionist` → «Добавить тренировку» | `/progress?focus=training&returnTo=/nutritionist` | — | — |
| 2 | Выбрать тип, минуты, интенсивность, заметку | input | — | required (тип, минуты) |
| 3 | tap «Сохранить» | submit | `POST /progress/trainings` | 422 |
| 4 | Возврат по `returnTo` | — | — | — |

---

## 19. Работа с уведомлениями

**Цель**: настроить напоминания «куплю» / «приготовлю» / «вода».

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/profile` → «Уведомления» | `/notifications` | `GET /notifications/settings` | — |
| 2 | Переключить «Покупки» / «Завтрак» / «Обед» / «Ужин» | toggle | `PATCH /notifications/settings` | 422 |
| 3 | Изменить время | time-input | `PATCH /notifications/settings` | формат `HH:MM` |
| 4 | Сменить timezone (по `getDeviceTimezone()`) | inline | `PATCH /notifications/settings` | — |
| 5 | Добавить в календарь (`.ics`) | tap | `buildIcsFile` (локально) | — |
| 6 | (Параллельно) `/nutritionist/care` управляет care-уведомлениями | другая модель | `PATCH /care/settings` | — |

---

## 20. Покупка подписки

**Цель**: выбрать тариф (на текущей реализации без оплаты).

| # | Шаг | Экран | API | Ошибки |
|---|---|---|---|---|
| 1 | `/profile` → «Подписка» | `/subscription` | `GET /subscription/overview` | — |
| 2 | Просмотр тарифов и Амов | inline | — | — |
| 3 | tap «Выбрать тариф» | `handleSelectPlan` | `POST /subscription/select` | 403 (не админ семьи для family-billing) |
| 4 | Toast «✓ Тариф сохранён» | — | — | — |
| 5 | (Заглушка) «Купить Амы» — disabled | — | — | — |

---

## 21. Работа администратора

**Цель**: получить доступ к админ-панели, выдать тариф/Амов, заблокировать пользователя.

| # | Шаг | Контекст | API | Ошибки |
|---|---|---|---|---|
| 1 | В боте отправить `/admin` | `admin_bot.handle_admin_command` | проверка `ADMIN_TELEGRAM_IDS` | not allowed |
| 2 | Бот отправляет PIN-код inline | bot | `admin_login_attempts` | rate limit |
| 3 | Подтвердить PIN | bot | создаётся `admin_sessions.session_token` | timeout |
| 4 | Inline «Открыть админ-панель» (web_app) | bot | — | — |
| 5 | `/admin` загружает данные через `AdminShell` (PIN session) | `AdminDashboard` | `GET /admin/summary` + tabs | 403 |
| 6 | Поиск пользователя / семьи | `/admin/users`, `/admin/families` | `GET /admin/users?q=` | — |
| 7 | Действие: блок, выдать тариф, выдать Амов | `ConfirmButton` | `POST /admin/users/{id}/...` | 403, 409 |
| 8 | OpenAI и Errors — для диагностики | `/admin/openai`, `/admin/errors` | `GET /admin/openai/*`, `GET /admin/errors` | — |

---

## 22. Telegram Bot

**Цель**: использовать ПланАм без webapp (только через текст/голос/фото).

**Каналы**:

| Команда / действие | Эффект | API/обработчик |
|---|---|---|
| `/start` | onboarding бота, deep-link приглашений | `handle_start` |
| `/help` | список команд | `BOT_COMMANDS_HELP` |
| `/invite +7…` | пригласить по номеру | `handle_invite_command` |
| `/admin` | PIN-сессия для админки | `admin_bot.handle_admin_command` |
| reply «🏠 Сегодня» | сводка дня | `build_today_summary` |
| reply «🍽 Моё меню» / inline | открыть `/menu` | webapp link |
| reply «🛒 Покупки» / inline | открыть `/shopping` | webapp link |
| reply «📦 Запасы» / inline | открыть `/pantry` | webapp link |
| reply «🥗 Нутрициолог» / inline | открыть `/nutritionist` | webapp link |
| reply «⚡ Быстро добавить» | inline-меню quick | `quick_add_keyboard` |
| `quick:voice_hint` | подсказка | bot text |
| `quick:receipt_hint` | подсказка | bot text |
| `quick:leftover` | FSM остатков (см. №14) | `handle_leftover_flow` |
| reply «👨‍👩‍👧 Семья» | inline «Открыть семью» | webapp link |
| reply «⚙ Настройки» | inline «Открыть настройки», «Документы» | webapp link |
| voice | сценарий №10 | `handle_voice_message` |
| photo | OCR чека | `handle_photo_message` |
| free text | parse → pending | `handle_text_quick_input` |
| inline `accept_family_invite:<id>` | принять приглашение | `family_invites.accept_invite` |
| inline `decline_family_invite:<id>` | отклонить | `decline_invite` |
| inline `create_family_invite_link` | сгенерировать invite-link | `handle_create_invite_link` |
| inline `pending:*` | подтвердить/отредактировать pending-список | `bot_pending.handle_pending_callback` |
| inline `legal_*` | согласия/отказ | `bot_registration.handle_legal_callback` |
| inline `phone:skip` | пропустить телефон | `handle_phone_skip` |

**Ошибки**:

- Бот блокирует ответы заблокированному пользователю.
- При отказе от документов — `Доступ временно ограничен`.
- Webhook secret mismatch → 403.

---

## 23. Telegram Mini App (общий сценарий)

**Цель**: использовать ПланАм через web-app, привязанный к боту.

| # | Шаг | Контекст | API | Ошибки |
|---|---|---|---|---|
| 1 | Open `Открыть ПланАм` в боте | TG webview | — | — |
| 2 | `TelegramProvider` берёт `Telegram.WebApp.initData`, парсит `initDataUnsafe` | client | — | initData пуст в браузере → dev-fallback |
| 3 | `AppGate` проверяет согласия и phone | — | — | редирект на ProtectedScreen |
| 4 | `AppModeProvider` загружает `app-context` | client | `GET /users/app-context` | сеть |
| 5 | `usePathname()` выбирает страницу | — | — | — |
| 6 | Все запросы идут с `X-Telegram-Init-Data` и `X-App-Mode` | `apiFetch` | абсолютные URL через `buildApiUrl` | сеть, 401 (initData expired) |
| 7 | Care и cook/buy reminders приходят через бот, тапнув на них пользователь возвращается в TMA по deep-link | — | — | браузер вне TG → fallback страница |

---

## Итого по сценариям

- Базовых сценариев: **23**.
- Среди них 8 связаны с Telegram (регистрация, бот, голос, фото, приглашения, FSM остатков, care, deep-link).
- Сценариев с AI-списанием Амов: **6** (нутрициолог, замена блюда, бот-парсинг, voice, OCR, recipe-analysis).
- Сценариев с обязательной семейной ролью «админ»: **3** (создать семью, пригласить, выбрать тариф для family-billing).
