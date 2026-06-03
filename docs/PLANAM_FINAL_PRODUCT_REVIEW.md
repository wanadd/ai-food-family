# PLANAM 2026 — Final Product Review

**Дата:** 2026-06-03  
**Тип:** финальный продуктовый аудит **перед** реализацией UX/UI 2026  
**Режим:** только аудит — код, API, БД, миграции **не изменялись**.

**Ревьюеры (роли):** Product Manager · UX Lead · Tech Lead · Growth Lead · Monetization Lead · Security (advisory)

**Корпус документов:** Blueprint · Master Spec · Design System · Visual Mockups · Recipe Media · Conversion Funnel · Notification System · Domain Architecture · UX Flow Map · UI System Audit · Screen Map · Navigation Graph · Security Audit · Security Fix Roadmap

---

## Executive summary

Концепция PLANAM 2026 **согласована по направлению**: один вопрос дня, фото-ядро, 3 вкладки, AI в действиях, мягкая монетизация. Документы **достаточны для старта дизайна и фронтенд-архитектуры**, но **недостаточны для безусловного GO** в production и платящей воронки без закрытия **критических расхождений** (триал, overview/Home data, оплата, security P0, фото-каталог) и **явного decision log**.

**Вердикт:** **Условный GO** — начинать реализацию UX/UI 2026 **можно**, параллельно с **обязательными исправлениями документов и Phase 0 security**; **нельзя** считать готовым релиз monetization/retention at scale без отдельного gate.

---

## 1. Соответствие миссии продукта

| Миссия | Оценка | Комментарий |
|--------|--------|-------------|
| Освобождение от рутины | **Сильно** | Home Hero + один CTA, автосписок покупок, bot OCR — закрывают цикл |
| Экономия времени | **Сильно** | WOW ≤90 с, ≤5 экранов до плана — измеримо |
| Более здоровое питание | **Средне** | Insight + нутрициолог есть, но **медицинская граница** слабо протестирована на copy во всех touchpoints |
| Польза до оплаты | **Сильно** | Trial-философия non-toxic согласована в funnel |

### Слабые места

1. **«Операционная система питания на годы»** (Blueprint) vs **3-дневный trial** (Funnel) — долгосрочное обещание не стыкуется с коротким пробным окном без явного post-trial habit design в продукте (freemium описан, но не в mockups).
2. **Здоровье** всё ещё рискует стать «вторым приложением» через `/wellness/chat` и deferred-advice — нужна дисциплина «один совет на день» (заявлена, **не enforced** в `GET /menus/overview` schema).
3. **Покупки → запасы** без объяснения остаётся friction #7 в [`UX_FLOW_MAP.md`](UX_FLOW_MAP.md) — в DS есть toast, в mockups **не везде** прописан.

---

## 2. Соответствие аудитории

| Сегмент | Покрытие | Риск смещения |
|---------|----------|---------------|
| Одиночка | Default scope, Home без семейного шума | ✅ Базовый |
| Пара | Chips «Пара», тариф «Совместный» | 🟡 Copy «семья» в G2 chips может сбить пару |
| Семья | Scope chip, family wizard, family plan | 🟡 **Wizard в funnel D0 не обязателен** — хорошо; но G2 «Семья» наравне с «Один» в онбординге **повышает** family-first сигнал |
| Спортсмен | Goal chip, PRO, `suitable_for_sport` | 🟡 PRO teaser без sport UX в mockups (только caption) |
| Молодая мама | Virtual member в architecture | 🔴 **Virtual member UX** не в visual mockups — риск отложить и потерять сегмент |

### Вывод

Одиночка **не подавлена** — OK. **Семья не доминирует в IA**, но **онбординг chips** и **тарифная сетка** визуально тянут к household. **Мама и спортсмен** — слабее одиночки в пакете mockups.

**Рекомендация до кода:** G2 default highlight **«Один»**; «Семья» — второй ряд; мама = подсказка «добавить ребёнка без Telegram» в account sheet, не в D0.

---

## 3. Монетизация

### 3.1 Триал 3 дня · 50 Амов (продукт 2026)

| Источник | Trial | AMS |
|----------|-------|-----|
| [`PLANAM_CONVERSION_FUNNEL_2026.md`](PLANAM_CONVERSION_FUNNEL_2026.md) | **3 дня** | **50** |
| [`subscription_catalog.py`](../apps/api/app/services/subscription_catalog.py) | **14 дней** | **200** |
| [`PLANAM_2026_PRODUCT_BLUEPRINT.md`](PLANAM_2026_PRODUCT_BLUEPRINT.md) | «Free / trial» без фиксации 3d | monthly_ams в seeds |
| [`PLANAM_VISUAL_MOCKUPS_2026.md`](PLANAM_VISUAL_MOCKUPS_2026.md) §8 | Copy **«За 14 дней»** на subscription | **противоречие** |

**Проблемы:**

1. **Документы не могут быть source of truth** для trial, пока не зафиксирован **единый Decision Record** (продукт vs backend).
2. **50 Амов за 3 дня** — агрессивный burn: 1× generate (5) + 3× replace (9) + 2× OCR (8) = 22; ок. Но **20 menu generations** в backend `TRIAL_MENU_GENERATIONS` **не отражены** в UX 50 AMS — скрытый разрыв.
3. **3 дня** vs метрика funnel **«Trial → paid D14–D30»** ([`PLANAM_CONVERSION_FUNNEL_2026.md`](PLANAM_CONVERSION_FUNNEL_2026.md) §1) — **логическая ошибка** в документе.
4. **D3 outcome sheet** при 3-day trial совпадает с end — OK; push «D10 trial» в Blueprint **не применим** к 3d без правки.

### 3.2 Тарифы и PRO

| Тема | Статус | Риск |
|------|--------|------|
| Личный / Совместный / Семейный | В seeds, outcome-copy в mockups | ✅ |
| PRO как layer | Согласован | 🟡 **Paywall server audit P2-1** не выполнен — PRO bypass риск |
| Реальный checkout | **Отсутствует** (Blueprint M1) | 🔴 **Монетизация на бумаге** |
| `select-plan` | Меняет план в БД без оплаты | 🔴 Юридически/продуктово опасно при публичном релизе |
| Family plan без family UX в trial | Feature flags `family_mode: false` в trial seed | 🔴 Upsell «Семейный» до создания семьи — confusion |

### 3.3 Семейные тарифы

Покупка семейного тарифа **до** household setup — слабое место. Нужен gate: «Сначала добавьте участника» или auto-wizard.

---

## 4. Конверсия

### Сильные стороны

- D0 WOW (план + фото + список) — правильная последовательность.
- Non-toxic paywall principles — согласованы.
- PaywallSheet — снижает friction #9.

### Слабые места

| # | Проблема | Severity |
|---|----------|----------|
| C1 | **90 с до WOW** при `POST /menus/generate` p95 до 15s + очередь не в UI v1 — реальность **2–3 мин** | High |
| C2 | **Phone gate** (friction #2) **не снят** в спеках — разрыв TMA/bot остаётся | High |
| C3 | **Онбординг** vs **legal/phone** — порядок в Master Spec «phone после WOW»; AppGate **в коде** может блокировать раньше | Critical (as-is code) |
| C4 | **Нет checkout** — конверсия обрывается на `select-plan` | Critical для revenue |
| C5 | Outcome metrics «сэкономлено 2ч» — **не из API**, риск fake value | Medium |
| C6 | Freemium 1 gen/week **после** 3d full access — резкий cliff без промежуточного «мягкого» tier в коммуникации | Medium |

### WOW-матрица (честная)

| WOW | Достижимость D0 | Зависимость |
|-----|-----------------|-------------|
| W0 план + фото | 🟡 | % `image_url` в каталоге |
| W0b автосписок | ✅ | menu → shopping sync |
| W3 replace | 🟡 | AMS + latency |

---

## 5. Retention

### Сильные стороны

- Notification matrix покрывает 7 обязательных сценариев.
- Deep links 2026 routes — согласованы.
- Care levels (min/balance/active) — понятны.

### Риски

| # | Риск | Detail |
|---|------|--------|
| R1 | **2 push/day** vs **7 сценариев** | Коллизии при активном пользователе — нужен приоритетный scheduler (не описан) |
| R2 | **overview advice + wellness advice** | Дубль friction #15 — retention push может спамить |
| R3 | **3-day trial** → day 4 silence | Если не конвертировался и freemium слаб — **D4 churn cliff** |
| R4 | **72h / 7d inactive** без персонализации фото | Push generic — ниже CTR |
| R5 | Unified notifications UI **без** unified backend | Двойная настройка ломает trust |
| R6 | Bot blocked users | Нет стратегии in-app-only retention |

**Цикл использования** (день): Home → Plan/Shop → Meal outcome — **замкнут в спеках**; **Meal Outcome Sheet** без единого API — риск неполной реализации.

---

## 6. Telegram Mini App

| Критерий | Оценка | Замечание |
|----------|--------|-----------|
| Сложность экранов | 🟡 | Recipe immersive + generate wizard — тяжёлее типичного TMA |
| Глубина навигации | ✅ | 3 tabs + sheets — OK |
| Производительность | 🔴 | Home rail: **N+1** `GET /recipes/{id}` (см. §12) |
| GPU | ✅ | DS запрещает parallax; **Master Spec §5.5 противоречит** DS §10 |
| initData race | 🔴 | Friction #1 — **не решён** в UX пакете, только security roadmap |
| Offline | Не описан | Medium для metro/shops |

**TMA-specific:** центральная вкладка «Дом» — правильно для daily open; **overflow account** скрывает подписку — хорошо для фокуса, **плохо** для trial end discoverability (компенсировать banner D3).

---

## 7. Масштабирование

| Этап | Готовность концепции | Gap |
|------|---------------------|-----|
| **100k MAU** | 🟡 | Monolith OK ([`DOMAIN_ARCHITECTURE.md`](DOMAIN_ARCHITECTURE.md)); CDN для фото **обязателен** |
| **1M MAU** | 🔴 | AI cost, worker queue, catalog replica — заявлены H1/H2, **не в UX scope** |
| **Native app** | 🟡 | 2027 PWA optional — TMA-first согласован; **нет** export auth model (initData-only) |

**Риск:** визуальный пакет предполагает **CDN + batch images** без ops budget и SLA — блокер роста при маркетинге.

---

## 8. Семейный режим

| Тема | Оценка |
|------|--------|
| Роли (admin member) | Backend есть; **UI 2026** — sheet, не `/family` hub — OK |
| Совместное меню / shopping | `X-App-Mode: family` — OK |
| Конфликты | **Два nutrition store** (user vs member) — friction #5 **не снят** в спеках, только «shared fields» обещание |
| Personal vs family toggle | Ошибка scope → wrong list — **meal-checkins IDOR** (security P1) |
| Virtual child | Критично для мам; **нет mockup** |
| Pair without «семья» word | Copy audit не проведён |

**Сценарий конфликта:** муж в personal, жена добавила family menu — два списка покупок в голове пользователя. Спеки не объясняют **чей список на Home** при mixed intent.

---

## 9. Рецепты и фотографии

| Критерий | Оценка |
|----------|--------|
| Стиль v1 | Документирован отлично |
| Масштаб generation | Batch + QA 10% — ops-heavy |
| **L0 ≥85%** target | 🔴 **Нереалистично без аудита** текущего `% image_url IS NULL` |
| CDN | Не в prod — только в architecture doc |
| `image_thumb_url` в RECIPE_ENGINE doc vs `image_url` in model | Потенциальный **schema drift** в головах команды |
| Home today без `recipe_id` в overview | 🔴 **Технический разрыв** (см. §12) |

---

## 10. AI

| Тема | Оценка |
|------|--------|
| Роль (в действиях, не tab) | ✅ Согласовано |
| Стоимость | 50 AMS / 3d — OK при лимитах; **200 AMS / 14d** в backend — другая экономика |
| Safety | Prompt limits P2-3; **не сделано** |
| Medical | Disclaimer в DS — OK |
| Catalog pollution P0-5 | **Блокер prod** до generate at scale |
| Dual advice | overview.nutritionist_advice + wellness — **не исправлено** |
| Queue/async | Spec есть; UI loading — skeleton; **push «готово»** — needs worker |

**OPEX риск:** рост без rate limits (P2-7) — AI margin drain ([`SECURITY_AUDIT.md`](SECURITY_AUDIT.md)).

---

## 11. Безопасность

### Соответствие SECURITY_AUDIT + ROADMAP

| Область | Статус | UX 2026 impact |
|---------|--------|----------------|
| Admin + AppGate P0-1 | **Open** | Не блокирует UX sprint, **блокирует ops** |
| Webhook P0-3 | **Open** | Bot notifications retention **под угрозой** |
| Recipe global write P0-5 | **Open** | AI menu integrity |
| initData replay T-01 | Medium | Долгая сессия TMA |
| Paywall P2-1 | Open | Monetization **небезопасна** |
| Referral REF-* | Not built | OK отложить; **не запускать** referral UI до P3-4 |
| meal-checkins IDOR P1-1 | Open | Family mode **опасен** в beta |

### Telegram auth

UX пакет требует retry initData — **совпадает** с P1-4. **Admin session** в UX не учтён — OK (out of user app).

### Подписки

Client-only PRO gates — **расходится** с Blueprint «server 100%». **NO GO для платного релиза.**

### Вердикт security vs UX start

**UX разработку можно начать** на staging/dev. **Production GO** — **нет** без Phase 0 (минимум P0-1, P0-3, P0-5, P0-6).

---

## 12. Противоречия между документами

| ID | Документ A | Документ B | Суть |
|----|------------|------------|------|
| X1 | Funnel: trial **3d / 50 AMS** | Backend + Blueprint seeds: **14d / 200** | Параметры trial |
| X2 | Funnel: revenue **D14–D30** | Funnel: trial **3 days** | Метрики |
| X3 | Mockups subscription: **«За 14 дней»** | Funnel: **3 дня** | UI copy |
| X4 | Blueprint: trial reminder **D10** | Funnel: trial ends **D3** | Lifecycle |
| X5 | Master Spec: recipe **parallax** | Design System: **запрет parallax** | Motion |
| X6 | Master Spec: `overview` единый совет | `MenuOverviewResponse` + wellness deferred | Dual advice |
| X7 | Master Spec: `next_action` enum в overview | Schema **нет** `next_action` | Home Hero engine |
| X8 | UX: Meal Outcome **один** API | Backend: checkins + leftovers **раздельно** | Integration |
| X9 | UX: unified notifications | Backend: care + notifications **два API** | Settings |
| X10 | Media: CDN derivatives | Model: только `image_url` | Delivery |
| X11 | Funnel: phone **после** WOW | As-is AppGate: phone **до** app | Blocking |
| X12 | Blueprint: Free **1 gen/week** | Funnel: trial **full** then cliff | Monetization narrative |
| X13 | Executive: 14d trial note | Funnel primary: 3d | Package summary |

**`GET /menus/overview`:** endpoint **существует** ([`menus.py`](../apps/api/app/routers/menus.py)) — противоречие X7 не «нет API», а **нет полей** для Hero P0–P5 и **нет `recipe_id` в `today_meals`** ([`meal_attendance.py`](../apps/api/app/services/meal_attendance.py) `extract_today_meals`).

---

## 13. Что исправить ДО начала реализации

### Critical (блокирует согласованность команды)

| ID | Действие | Owner |
|----|----------|-------|
| CR1 | **Decision Record: trial** — 3d/50 vs 14d/200; обновить **все** PLANAM docs + push copy | PM + Monetization |
| CR2 | **API contract doc** (не код в этом аудите): `MenuOverviewResponse` + `today_meals[].recipe_id`, `image_url`, `next_action`, shopping/pantry hints **или** явный BFF spec | Tech Lead |
| CR3 | Согласовать **AppGate order** с onboarding: phone/legal не блокируют WOW **или** изменить WOW definition | PM + UX |
| CR4 | Удалить **parallax** из Master Spec §5.5 / §12.4 OR исключение в DS — одно решение | UX Lead |
| CR5 | **Payment scope** для «конверсия»: MVP checkout vs отложить monetization UI | PM |

### High

| ID | Действие |
|----|----------|
| H1 | Исправить mockups subscription: **3 дня**, не 14 |
| H2 | Исправить funnel metrics D14–D30 → D3–D14 для 3d trial |
| H3 | Аудит % recipes with `image_url` — скорректировать L0 target |
| H4 | Единый **advice ownership** (overview XOR wellness) в docs |
| H5 | Virtual member + pair copy в mockups |
| H6 | **Phase 0 security** в roadmap реализации (параллельный track) |
| H7 | Meal Outcome → mapping table на `meal-checkins` + `meal-leftovers` API |

### Medium

| ID | Действие |
|----|----------|
| M1 | Notification scheduler priorities doc |
| M2 | Shopping→pantry edu toast во всех shopping mock states |
| M3 | Family tariff purchase gate |
| M4 | Lucide icon set — Figma + dependency decision |
| M5 | Dark mode: Figma parity before dev claims «done» |
| M6 | Grace redirect map в один migration checklist |

### Low

| ID | Действие |
|----|----------|
| L1 | Rename «Забота» vs «Здоровье» в bot legacy URLs |
| L2 | Admin UX out of scope statement в package README |
| L3 | Outcome «2h saved» — formula or remove |

---

## 14. Финальный вердикт (0–10)

| Область | Score | Обоснование |
|---------|-------|-------------|
| **Продукт** | **8** | Чёткая миссия, цикл, семья опциональна; trial/doc gaps |
| **UX** | **8** | Home/3-tab/sheets сильные; phone gate, family edge cases |
| **UI** | **7** | DS зрелый на бумаге; dark не в коде; dual palette debt as-is |
| **Growth** | **7** | Funnel + notifications хороши; 3d/14d хаос, нет checkout |
| **Монетизация** | **5** | Outcome-copy есть; **нет оплаты**, trial split, select-plan stub |
| **Безопасность** | **4** | P0 открыт; UX старт не снимает prod risk |
| **Архитектура** | **7** | Domain map силён; overview gap, media CDN, BFF не формализован |

**Среднее (не взвешенное):** ~6.6 — **хорошая концепция, незрелая готовность к платному production.**

---

## 15. GO / NO GO

### Можно ли начинать реализацию PLANAM UX/UI 2026 **прямо сейчас**?

**Ответ: Условный GO (GO-with-gates).**

| Scope | Verdict |
|-------|---------|
| **Design System tokens + Figma** | **GO** |
| **Home + 3-tab + Plan Today + Recipe grid (dev/staging)** | **GO** после CR1–CR4 doc fixes (1–3 дня) |
| **Onboarding WOW flow** | **GO** после CR3 (gate order) |
| **Production release** | **NO GO** без Phase 0 security + checkout + photo L0 audit |
| **Paid acquisition** | **NO GO** |

### Если трактовать как жёсткий NO GO

Только если команда **не готова** за 1 неделю закрыть CR1–CR5 документально и параллельно Phase 0 — тогда **NO GO** до Decision Record.

### Обязательно исправить (минимум)

1. **CR1** — единые параметры trial во всех docs  
2. **CR2** — контракт данных Home Hero + photo rail  
3. **CR3** — порядок gates vs WOW  
4. **CR4** — parallax  
5. **H6** — security Phase 0 в плане спринтов (не откладывать «после UX»)

### Первые 3 спринта после аудита

**Спринт 1 (2 нед): «Truth & Foundation»**

- Decision Record trial + правка docs (CR1, H1, H2)  
- API contract spec для Home/overview (CR2) — review с backend  
- Phase 0 security: P0-1, P0-3, P0-5, P0-6  
- Figma: DS Light/Dark + Home + Plan Today (empty/loading)  
- Deliverable: staging Home **без** production release  

**Спринт 2 (2 нед): «Core Day Loop»**

- Implement: 3-tab nav, Home Hero (client rule engine v1), Today rail with photo prefetch plan  
- `/plan/today`, Meal Outcome Sheet → existing APIs (H7)  
- Onboarding overlay G1–G5 (gates per CR3)  
- `GET /menus/overview` consumer + gap list для backend follow-up  
- Deliverable: D0 WOW path on staging  

**Спринт 3 (2 нед): «Catalog & Commerce Prep»**

- `/plan/recipes` grid + immersive detail (no parallax)  
- `/home/shopping` simplified  
- PaywallSheet UI-only + subscription outcome screen  
- Photo: L1 fallbacks + catalog audit (H3)  
- Decision: checkout provider sprint 4 or defer  
- Deliverable: full day loop demo + notification copy review  

---

## 16. Что команда поймёт из пакета (проверка цели аудита)

| Вопрос | Покрыто? |
|--------|----------|
| Как выглядит продукт | ✅ Mockups + DS |
| Как двигается пользователь | ✅ Master Spec + Funnel |
| Какие экраны нужны | ✅ ~22 routes |
| Что исчезает | ✅ Executive Summary |
| Какие данные | 🟡 **Частично** — overview gap |
| Воронка | 🟡 **Противоречия trial** |
| Фото | ✅ Media architecture |
| Dark mode | ✅ DS §13 |

---

## 17. Заключение

PLANAM 2026 — **редкий случай сильной продуктовой пересборки на бумаге** без немедленного раздувания scope. Главные ошибки сейчас — **не в видении**, а в **синхронизации** (trial, overview contract, gates, payment, security, фото-реальность) и в **остаточном расхождении** UX-обещаний с as-is backend.

**Исправить документы и контракты дешевле, чем переписывать Home через спринт.**

---

*Аудит выполнен без изменений в репозитории (кроме этого файла). Следующий артефакт: `PLANAM_2026_DECISION_RECORD.md` (рекомендуется) для CR1.*
