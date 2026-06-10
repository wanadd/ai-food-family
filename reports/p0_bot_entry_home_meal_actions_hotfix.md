# PLANAM — P0 Bot Entry + Home/Menu Meal Actions Hotfix

**Branch:** `fix/p0-bot-entry-home-meal-actions`  
**Base:** `rebuild/consumer-ui-reference-v2` @ `9880c7c`  
**Date:** 2026-06-10

---

## Git (pre-work)

```
fix/p0-bot-entry-home-meal-actions
9880c7c
9880c7c feat(ui): rebuild consumer v2 screens from visual reference
b853c9e feat(ui): align planam 2026 screens with visual reference
17e833c fix(ui): canonicalize 2026 deep links and remove orphan components
60731d6 fix(ui): address visual qa home and unit display issues
d5fc187 docs(ui): add full visual qa walkthrough audit
```

---

## 1. Что исправлено в боте

| Файл | Изменение |
|------|-----------|
| `apps/api/app/telegram/messaging.py` | `entry_inline_keyboard()` — три кнопки входа; `PHONE_CONFIRM_CALLBACK`, `HELP_CALLBACK`, `BOT_HELP_TEXT` |
| `apps/api/app/telegram/bot.py` | `setup_bot_commands()` — регистрация `/start`, `/help`, `/invite` через `setMyCommands` |
| `apps/api/app/main.py` | Вызов `setup_bot_commands()` при старте API |
| `apps/api/app/services/bot_registration.py` | После регистрации / возврата — `entry_inline_keyboard` вместо отдельных сообщений |
| `apps/api/app/services/telegram_bot.py` | Обработка `phone:request` и `help:show`; убран тупик «отправь /start» в callback; invite + phone flow с кнопкой Mini App |

---

## 2. Как теперь работает `/start`

1. Пользователь отправляет `/start`.
2. `handle_start` → `upsert_user_from_bot` → маршрутизация:
   - **Deep-link invite** (`/start invite_<token>`) — сохраняем token в сессии; если нет телефона → `send_phone_required` + кнопка «Открыть PLANAM»; если есть → показываем accept/decline.
   - **Обычный старт** → `route_after_start`:
     - Нет legal consent → экран согласий (как было).
     - Нет телефона → `send_phone_request` с `request_contact` (как было).
     - Полный доступ → главное reply-меню + inline-кнопки входа.

---

## 3. Кнопки в боте после `/start` (зарегистрированный пользователь)

| Кнопка | Тип | Действие |
|--------|-----|----------|
| **Открыть PLANAM** | `web_app` inline | Открывает Mini App (`TELEGRAM_WEBAPP_URL` или `https://planam.ru`) |
| **Подтвердить телефон** | `callback_data: phone:request` | Показывает reply-клавиатуру «Поделиться номером» (`request_contact: true`) |
| **Помощь** | `callback_data: help:show` | Текст справки + снова кнопки входа |

Дополнительно: reply-меню «Главное меню ПланАм» (Сегодня, Моё меню, Покупки, Запасы и т.д.) — без изменений.

Bot commands (меню команд Telegram): `/start`, `/help`, `/invite`.

---

## 4. Phone confirmation

**Реализовано (MVP, без нового backend):**

- Кнопка «Подтвердить телефон» → callback `phone:request` → сообщение с инструкцией + reply-клавиатура `request_contact`.
- Пользователь **не** вводит номер текстом в чат.
- Если номер уже подтверждён → «Номер уже подтверждён ✅» + кнопка Mini App.
- При invite без телефона: `send_phone_required` + дополнительное сообщение с кнопкой «Открыть PLANAM».

**Не меняли:** логику `upsert_user_from_bot`, `user_can_access_app`, legal consent, `phone:skip`.

---

## 5. Invite flow

| Сценарий | Было | Стало |
|----------|------|-------|
| Callback без регистрации | `answerCallbackQuery("Сначала завершите регистрацию: /start")` — тупик | Инструкция + `request_contact` + `entry_inline_keyboard` |
| Deep-link invite, нет телефона | Только phone keyboard | Phone keyboard + «Открыть PLANAM» |
| Deep-link invite, есть доступ | Accept/decline | Без изменений |

---

## 6. Home hero

**Новый компонент:** `apps/web/components/planam-v2/home/HomeHeroV2.tsx`

| Требование | Реализация |
|------------|------------|
| Фото ~1/3 экрана, без тяжёлого градиента | Блок `h-[30vh]`, лёгкий градиент только снизу (`h-10 from-black/20`) |
| Название ≤2 строк, без кавычек | `line-clamp-2` + `cleanMealTitle()` в `planam-hero-2026.ts` |
| CTA «Готовить» | Primary green button |
| Secondary «Ел другое» / «Пропустил» | Две secondary-кнопки (тонируемый sage, не белые на белом) |
| «Заменить» убран с hero | Убран из `HomeHeroV2`; остаётся в Menu «Ещё» |
| «Дальше сегодня» | Блок 1–2 следующих приёмов в `HomeV2.tsx` |
| Нет TodayDishRail | Не возвращали |

Non-meal hero (no menu, pantry, wellness) — по-прежнему через `PlanAmHero2026`.

---

## 7. Meal actions (общая логика)

**Новый компонент:** `apps/web/components/planam-v2/menu/MealEatenSheetV2.tsx`

События:

| Действие UI | `actual_status` API | КБЖУ |
|-------------|---------------------|------|
| Съел сейчас | `ate_home` | ✅ учитывается |
| Съем позже | `cooked` | ❌ не в `EATEN_STATUSES` |
| Ел другое | `ate_other` | ✅ учитывается |
| Пропустил | `skipped` | ❌ не учитывается |

**Где применено:**

- `RecipeDetail2026.tsx` — кнопка «Готово» после шагов → `MealEatenSheetV2`
- `HomeHeroV2.tsx` — «Ел другое» / «Пропустил»
- `MenuTodayV2.tsx` — sheet «Ещё» → Ел другое, Пропустил

**Backend:** используется существующий `POST /meal-checkins`. Статусы `cooked` / `skipped` записываются в БД, но `meal_daily_nutrition.EATEN_STATUSES` их не включает — КБЖУ не начисляются автоматически после «Готово».

### Phase 2 backend (если нужен явный трекинг)

```
POST /meal-events
{
  meal_type, recipe_id?, event: "started_cooking" | "finished_cooking" | "ate_now" | "ate_later" | "skipped" | "ate_other",
  planned_date, description?, portion_size?
}
```

Сейчас MVP через `meal-checkins` достаточен для UI-safe flow.

---

## 8. MenuTodayV2: «Ещё» вместо «+»

- Кнопка `+` заменена на pill **«Ещё»** (sage border/accent).
- Bottom sheet заголовок: **«Что сделать с блюдом?»**
- Действия: Открыть рецепт, Заменить, Ел другое, Пропустил, Добавить в покупки (если есть `recipe_id`).

---

## 9. Покупки / Запасы

**Новый компонент:** `apps/web/components/planam-v2/home-domain/HomeDomainSegmentV2.tsx`

| Вкладка | Route | Экран |
|---------|-------|-------|
| Покупки | `/shopping` | `ShoppingV2` |
| Запасы | `/home/pantry` | `PantryV2` |

- Segment на обоих экранах.
- Убрана отдельная текстовая ссылка «Запасы дома →» с Shopping.
- В Pantry: CTA **«Приготовить из того, что есть»** → `/home/leftovers`.
- Bottom nav **не меняли**.

---

## 10. «Совет PLANAM» → контекст дня

**Новый модуль:** `apps/web/lib/home/home-day-context.ts`

| Режим | Блок |
|-------|------|
| Обычный | «Сегодня всё по плану» / «План на день» / «Не забудьте воду» |
| Pro / health signal | `V2AiTip` tone=`ai` с текстом нутрициолога |

`shouldShowAiTip()` — только при `is_pro` + body или `isWellnessHeroPriority()`.

---

## 11. Цветовая система

**`apps/web/tailwind.config.ts`** — семантические акценты:

| Token | Назначение |
|-------|------------|
| `sage` (existing) | primary / planam-green |
| `food` | food-orange — еда |
| `water` | water-blue — вода |
| `danger` | danger-red — ошибки / просрочено |
| `ai` | ai-indigo — Pro/AI |
| `energy` | energy-yellow — активность |

**Применение:**

- `Button2026` secondary — `bg-sage-50 border-sage-300` (light theme fix)
- `V2ProgressBar` — tone `water` для воды в Wellness
- `V2AiTip` — tone `ai` для AI-советов

---

## 12. Demo 3 дня (UX only)

Существующие компоненты не меняли:

- `lib/monetization/trial-config.ts` — `PLANAM_TRIAL_DAYS = 3`
- `components/monetization-2026/TrialStatus2026.tsx` — «Пробный период · N дней»

**Phase 2:** backend entitlement для автоматического старта Demo при первом `/start` (subscription service).

### Будущие тарифы (зафиксировано)

| Тариф | Описание |
|-------|----------|
| Demo | 3 дня полного доступа |
| Basic | Базовый режим |
| Plus | AI меню, покупки, запасы, семья |
| Pro | Спорт/диета/здоровье, 5–6 приёмов, тренировки, точный КБЖУ, AI-нутрициолог |

---

## 13. Что не трогали

- Bottom nav (5 вкладок)
- Recipe DB / import pipeline / удаление рецептов
- Payment backend
- Canonical routes / legacy redirects
- DB migrations
- Физическое удаление старых 2026-компонентов
- `backend/scripts/resync_recipe_ingredients_jsonb.py` (unrelated local change — не в коммит)

---

## 14. Phase 2 (осталось)

1. Явный `POST /meal-events` для started_cooking / finished_cooking
2. Demo entitlement на backend при первом входе
3. «Следующий приём пищи в 13:30» — нужны meal-time preferences в профиле
4. Recipe Rebuild V2 — см. `reports/recipe_rebuild_v2_requirements_notes.md`
5. E2E тест бота в staging (webhook + реальный Telegram)

---

## 15. Build / test result

| Check | Result |
|-------|--------|
| `npx vitest run` | ✅ **37/37 passed** |
| `python -m py_compile` (bot files) | ✅ OK |
| `npm run build` (local) | ⚠️ **OOM** — нехватка RAM/commit charge на dev-машине (~500 MB free virtual). Не ошибка TypeScript. |
| `npx tsc --noEmit` | ⚠️ Только pre-existing ошибки `vitest` types в `*.test.ts` (4 файла) |

**Workaround для локальной сборки:**

```bash
# apps/web
NEXT_BUILD_LOW_MEM=1 NODE_OPTIONS="--max-old-space-size=2560" npm run build
```

`next.config.mjs` поддерживает `NEXT_BUILD_LOW_MEM=1` (1 CPU worker) — опционально для VPS/CI.

**Рекомендация:** прогнать `npm run build` на VPS/CI с ≥4 GB RAM.

---

## Manual QA checklist (Telegram / mobile)

- [ ] `/start` → кнопки Открыть PLANAM / Подтвердить телефон / Помощь
- [ ] Mini App открывается из бота
- [ ] Invite deep-link без телефона → инструкция + кнопки (не «отправь start»)
- [ ] Home hero: фото, без кавычек, Готовить / Ел другое / Пропустил
- [ ] Light/dark theme кнопки читаемые
- [ ] Menu «Ещё» → sheet с действиями
- [ ] Recipe «Готово» → sheet Съел/Позже/Другое/Пропустил
- [ ] Shopping ↔ Pantry segment
- [ ] Pantry → «Приготовить из того, что есть»
- [ ] Home контекст дня (не generic «добавьте белок»)
