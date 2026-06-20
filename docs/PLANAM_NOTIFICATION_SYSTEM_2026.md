# PLANAM Notification System 2026

**Дата:** 2026-06-03  
**Режим:** продуктовая спецификация — код, API, БД не менялись.

**Основа:** [`PLANAM_UX_UI_2026_MASTER_SPEC.md`](PLANAM_UX_UI_2026_MASTER_SPEC.md) §11 · [`PLANAM_CONVERSION_FUNNEL_2026.md`](PLANAM_CONVERSION_FUNNEL_2026.md) · [`UX_FLOW_MAP.md`](UX_FLOW_MAP.md) · [`DOMAIN_ARCHITECTURE.md`](DOMAIN_ARCHITECTURE.md)

**As-is backend:**

| System | API / tables |
|--------|----------------|
| Care scheduler | `GET|PATCH /care/settings`, `care_notifications`, `care_events` |
| User notifications | `GET|PUT /notifications/settings` |
| Bot delivery | Telegram messages via bot webhook |

**2026 UX:** один экран `/account/notifications`; логика может читать оба API до backend merge.

---

## 1. Принципы

| # | Principle |
|---|-----------|
| 1 | Каждое уведомление ведёт к **ценности**, не к «откройте приложение» |
| 2 | Max **2 push / день** (default care level «Баланс») |
| 3 | Quiet hours respected |
| 4 | Meal push → **thumbnail 4:3** если есть `image_url` |
| 5 | Opt-out в 1 tap: «Меньше напоминаний» |
| 6 | Copy: рекомендация, **не** медицинское назначение |

**Главный вопрос push:** *Что пользователь должен сделать дальше?*

---

## 2. Каналы

| Channel | Use |
|---------|-----|
| **Telegram bot message** | Primary retention |
| **Telegram WebApp button** | `web_app` deep link в TMA |
| In-app | Banners on Home (trial, не spam) |

**Не v1:** email, SMS.

---

## 3. Deep link map

| Target | URL |
|--------|-----|
| Home | `/` |
| Today plan | `/plan/today` |
| Shopping | `/home/shopping` |
| Pantry | `/home/pantry` |
| Generate | `/plan/generate` |
| Wellness | `/wellness` |
| Subscription | `/account/subscription` |
| Nutrition | `/account/nutrition` |

Bot `web_app` URLs — без legacy `/nutritionist`, `/menu` chains.

---

## 4. Сценарии (полная матрица)

### 4.1 Новый пользователь

| Field | Value |
|-------|-------|
| **Условие** | `created_at` < 24h, `menus/selected` empty, onboarding incomplete |
| **Когда** | +2h после first open; не ночью |
| **Текст** | «Анна, ваш план почти готов — остался один шаг 🍽» |
| **CTA button** | «Составить план» → `/plan/generate` |
| **Цель** | Activation W0 |
| **Приоритет** | High |

| Field | Value |
|-------|-------|
| **Условие** | Plan selected, same day evening, no meal checkin |
| **Текст** | «Как прошёл ужин? Отметьте за 10 секунд» |
| **CTA** | «Отметить» → `/` + open `MealOutcomeSheet` query |
| **Цель** | Close D0 loop |

---

### 4.2 Нет меню

| Field | Value |
|-------|-------|
| **Условие** | No `GET /menus/selected` · last open > 24h · trial or paid |
| **Когда** | 10:00 local (user TZ from care settings) |
| **Текст** | «На этой неделе ещё нет плана. Подберём блюда с учётом ваших предпочтений» |
| **CTA** | «Составить меню» → `/plan/generate` |
| **Цель** | Reactivation + W0 |
| **Media** | Optional static illustration, not required |

| Field | Value |
|-------|-------|
| **Условие** | Trial D2, still no menu |
| **Текст** | «2 дня пробного доступа — успейте получить персональный план» |
| **CTA** | «Попробовать» → `/plan/generate` |
| **Цель** | Trial value before P3 |
| **Tone** | Soft, no countdown |

---

### 4.3 Нет покупок (пустой / stale list)

| Field | Value |
|-------|-------|
| **Условие** | Menu exists, shopping list empty OR no toggle 48h |
| **Текст** | «Список на сегодня пуст. Добавим продукты из вашего плана?» |
| **CTA** | «Открыть покупки» → `/home/shopping` |
| **Цель** | Complete cycle menu → shop |

| Field | Value |
|-------|-------|
| **Условие** | Shopping has unchecked > 0, evening |
| **Текст** | «Осталось 3 позиции на сегодня — молоко, хлеб, …» |
| **CTA** | «Список покупок» → `/home/shopping` |
| **Цель** | D1 Hero P2 habit |

---

### 4.4 Нет активности

| Field | Value |
|-------|-------|
| **Условие** | Last TMA open > **72h**, had plan before |
| **Когда** | 1 push, not repeated until +72h |
| **Текст** | «Мы сохранили ваш план. Посмотрите, что на ужин сегодня» |
| **CTA** | «Открыть» → `/plan/today` |
| **Media** | **Thumbnail 4:3** tonight dish |
| **Цель** | Return W1 |

| Field | Value |
|-------|-------|
| **Условие** | Last open > **7d** |
| **Текст** | «Добро пожаловать обратно в PLANAM — ваши запасы и план ждут» |
| **CTA** | «Продолжить» → `/` |
| **Цель** | Long reactivation |

---

### 4.5 Окончание триала

| Field | Value |
|-------|-------|
| **Условие** | `plan_code=trial`, `trial_ends_at` in 24h (product: **D3** of 3-day trial) |
| **Текст** | «Завтра пробный период заканчивается. Сохраните свой ритм питания» |
| **CTA** | «Посмотреть итог» → `/account/subscription` |
| **Цель** | P3 outcome conversion |
| **Запрещено** | «Последний шанс!!!», блокировка app |

| Field | Value |
|-------|-------|
| **Условие** | Trial ended, status → freemium |
| **Текст** | «План на неделю доступен с подпиской. Бесплатно — список покупок и запасы» |
| **CTA** | «Выбрать тариф» → `/account/subscription` |
| **Цель** | P4 soft |
| **Tone** | Honest, not punitive |

---

### 4.6 Рекомендации здоровья

| Field | Value |
|-------|-------|
| **Условие** | New `deferred-advice` OR daily insight from overview; user opted in wellness tips |
| **Когда** | Max 1/day; not duplicate menu advice title |
| **Текст** | «Совет дня: {short_advice}» |
| **CTA** | «Подробнее» → `/wellness` |
| **Footer** | «Рекомендация, не назначение» in expanded view, not push |
| **Цель** | Wellness engagement |
| **Emoji** | Допустим 1 в push (💡) |

| Field | Value |
|-------|-------|
| **Условие** | Water < 30% day, afternoon |
| **Текст** | «Выпили 2 стакана? Отметьте воду за 5 секунд» |
| **CTA** | «Открыть Заботу» → `/wellness` |
| **Цель** | Metric habit |

---

### 4.7 Возврат пользователя

| Field | Value |
|-------|-------|
| **Условие** | Opened app after push 4.4 or 4.6 within 1h |
| **In-app** | No extra push; Home Hero personalized «С возвращением» |
| **Цель** | Reinforce success |

| Field | Value |
|-------|-------|
| **Условие** | Paid user inactive 14d |
| **Текст** | «Вы не теряете данные — меню и запасы на месте. Составим план на новую неделю?» |
| **CTA** | «Новый план» → `/plan/generate` |
| **Цель** | Paid retention |

---

## 5. Дополнительные сценарии (операционный цикл)

| Сценарий | Условие | Текст (direction) | CTA | Цель |
|----------|---------|-------------------|-----|------|
| Pantry expiry | item T-1 day | «Используйте {milk} завтра» | `/home/pantry` | Waste reduction |
| Meal reminder | plan today, 1h before usual cook | «Пора {dish}» + thumb | `/plan/today` | Cooking habit |
| Shopping morning | unchecked > 0 | «3 позиции на сегодня» | `/home/shopping` | D1 |
| Family invite accepted | new member | «{name} в вашем плане» | `/` family scope | Household growth |
| AMS low | balance < 10 | «Осталось мало Амов для замен» | `/account/subscription` packs | Revenue soft |

---

## 6. Care levels (user setting)

| Level | Max push/day | Scenarios enabled |
|-------|--------------|-------------------|
| **Минимум** | 1 | Trial end, inactive 7d |
| **Баланс** | 2 | + meal, shopping, expiry |
| **Активно** | 3 | + water, health tips |

Mapping → existing care level selector in unified notifications UI.

---

## 7. Подавление и анти-спам

| Rule | Action |
|------|--------|
| User dismissed advice «Не сейчас» | `deferred-advice` suppress title 7d |
| Quiet hours | Queue to next window |
| Same CTA 2× in 24h | Suppress duplicate |
| Bot blocked | Mark undeliverable, no retry storm |

**API:** `GET …/suppressed-titles`, care events log.

---

## 8. Шаблон сообщения (Telegram)

```
{emoji_optional} {body_one_line}

[ {CTA_label} ]  → web_app URL
```

| Rule | Detail |
|------|--------|
| Length | ≤ 160 chars body |
| CTA | 1 button |
| Photo | attach thumb_400 when meal-related |

---

## 9. In-app vs push

| Type | Where |
|------|-------|
| Trial banner | Home only D3 |
| AMS low | PaywallSheet on action, not push first |
| Outcome | Sheet D3, duplicate push optional |

---

## 10. Метрики

| Metric | Target |
|--------|--------|
| Push → open rate | > 12% |
| Opt-out rate | < 8% monthly |
| Meal reminder → checkin | > 20% |
| Trial end push → subscription view | > 30% |

---

## 11. Связь с воронкой

| Funnel | Notifications |
|--------|---------------|
| D0 W0 | §4.1 plan ready |
| D1 R1 | §4.3 shopping, §5 meal |
| D2 W2 | §5 pantry expiry |
| D3 P3 | §4.5 trial end |
| D7+ | §4.4, §4.7 |

---

*Notification System — часть Visual Product Package 2026. Settings UI: [`PLANAM_VISUAL_MOCKUPS_2026.md`](PLANAM_VISUAL_MOCKUPS_2026.md) §7.*
