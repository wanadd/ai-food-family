# Sprint 9 — Completion Report (Монетизация UX 2026)

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Спринт:** Subscription Hub · Plans config · AMS · PaywallSheet · Trial · Upgrade stub · Home · Account

**Эталоны:** [`PLANAM_CONVERSION_FUNNEL_2026.md`](PLANAM_CONVERSION_FUNNEL_2026.md) · [`PLANAM_PAYMENT_ARCHITECTURE_2026.md`](PLANAM_PAYMENT_ARCHITECTURE_2026.md) · [`PLANAM_UX_UI_2026_MASTER_SPEC.md`](PLANAM_UX_UI_2026_MASTER_SPEC.md) · [`SPRINT_8_COMPLETION_REPORT.md`](SPRINT_8_COMPLETION_REPORT.md)

**Условие:** `NEXT_PUBLIC_PLANAM_UI_2026=true`. Реальных платежей и PSP **нет** — только UX и `POST /subscriptions/select-plan` (staging).

---

## Executive summary

Реализован **готовый пользовательский опыт монетизации**: хаб подписки (`/account/subscription`), баланс Амов (`/account/ams`), единый **PaywallSheet2026**, мягкий trial (3 дня / 50 Амов), upgrade flow до **заглушки оплаты**, интеграция Home и Account. Тарифы в UI: **Старт · Пара · Семья · PRO** из SSOT `plan-catalog-2026.ts` (коды API: `personal · shared · family · pro`). Legacy `/subscription` редиректит на 2026.

---

## Части спринта

| # | Требование | Статус | Реализация |
|---|------------|--------|------------|
| 1 | `/account/subscription` — не legacy | ✅ | `SubscriptionHub2026` |
| 2 | Тарифы из Blueprint, единый config | ✅ | `lib/monetization/plan-catalog-2026.ts` |
| 3 | `/account/ams` — баланс, история, расход | ✅ | `AmsHub2026` |
| 4 | PaywallSheet — no_amas / pro / trial | ✅ | `PaywallSheet2026` + `PaywallProvider` |
| 5 | Trial 3д / 50 Амов, мягко | ✅ | `trial-config.ts`, `TrialStatus2026`, banner |
| 6 | Upgrade → paywall → тариф → stub | ✅ | `PaymentStub2026` + checkout route |
| 7 | Home: trial / мало Амов / конец периода | ✅ | `HomeMonetizationBanner2026` |
| 8 | Account hub: подписка + Амы | ✅ | `nav-config` + `AccountHub2026` |
| 9 | Dark mode | ✅ | `pa-*` / `dark:` |

---

## Новые маршруты

| Маршрут | Экран | Legacy (flag off) |
|---------|--------|-------------------|
| `/account/subscription` | Тариф, Амы, планы, PRO | `/subscription` → redirect при flag on |
| `/account/ams` | Баланс, на что тратятся, история | `/subscription` (частично) |
| `/account/subscription/checkout?plan=` | Заглушка оплаты | `/subscription` |

---

## Конфигурация тарифов (SSOT)

**Файл:** `apps/web/lib/monetization/plan-catalog-2026.ts`

| UI (Blueprint) | API `plan_code` | Цена (из API) |
|--------------|-----------------|---------------|
| Старт | `personal` | 249 ₽/мес |
| Пара | `shared` | 399 ₽/мес |
| Семья | `family` | 599 ₽/мес |
| PRO | `pro` | 999 ₽/мес |

**Trial:** `lib/monetization/trial-config.ts` — `PLANAM_TRIAL_DAYS = 3`, `PLANAM_TRIAL_AMS = 50` (re-export в onboarding config).

**Пути:** `lib/monetization/paths.ts` — `MONETIZATION_PATHS`.

---

## PaywallSheet2026

| Reason | Сценарий |
|--------|----------|
| `no_amas` | Не хватает Амов на действие |
| `low_amas` | Мягкое предупреждение (Home banner) |
| `pro_feature` | PRO-функция |
| `trial_ended` | Конец пробного |
| `trial_ending` | Скоро конец trial |

**Поток:** Sheet → «Перейти к оплате» → `/account/subscription/checkout?plan=` или «Сравнить тарифы» → hub.

**Интеграция:** `PaywallProvider` в `AppProviders`; `AmaConfirmDialog` при нехватке Амов открывает paywall (2026).

---

## API (без новых endpoint)

| Endpoint | Использование |
|----------|----------------|
| `GET /subscriptions/me` | Hub, AMS, Home banner, Provider |
| `POST /subscriptions/select-plan` | Checkout stub (тест без оплаты) |

---

## Интеграция Home

| Сигнал | UI |
|--------|-----|
| Trial ≤1 день | `HomeMonetizationBanner2026` — мягкий текст |
| Trial ended | Banner → subscription |
| Амы ≤5 | Banner → `/account/ams` |
| Период ≤3 дня | Banner → subscription |

`buildHomeMonetizationBanner` в `lib/monetization/billing-status.ts`.

Redirect map: `/subscription` → `/account/subscription` в `redirect-path-2026.ts`.

---

## Account Hub

| Пункт | href |
|-------|------|
| Подписка | `/account/subscription` |
| Амы | `/account/ams` |

---

## QA

| Проверка | Результат |
|----------|-----------|
| `npx tsc --noEmit` | ✅ |
| `npm run lint` | ✅ |
| `npm run build` | ✅ |

### Ручной сценарий

1. `NEXT_PUBLIC_PLANAM_UI_2026=true`
2. Account → Подписка — текущий тариф, trial badge, 4 плана
3. Account → Амы — баланс, costs, история
4. AI replace при 0 Амов → PaywallSheet → checkout stub
5. Home — banner при малом балансе / конце trial
6. `/subscription` → redirect `/account/subscription`

---

## Блокеры до реальных платежей

| Блокер | Документ / Phase |
|--------|------------------|
| `POST /subscriptions/checkout-session` | PAYMENT_ARCHITECTURE Phase B |
| Webhook `POST /webhooks/payment/{provider}` | Phase B |
| `PaymentProvider` (YooKassa / Telegram Stars) | Phase B |
| AMS packs purchase UI | «Скоро» в AmsHub |
| Production disable `select-plan` без webhook | PAYMENT_ARCHITECTURE §9 |
| P2-1 server audit всех PRO gates | Blueprint §8.2 |

---

## Критерии готовности Sprint 9

| Критерий | ✓ |
|----------|---|
| Видеть тариф | ✅ |
| Видеть Амы | ✅ |
| Понимать ограничения | ✅ Paywall + copy |
| Видеть преимущества PRO | ✅ блок в hub |
| Пройти upgrade flow | ✅ до checkout stub |
| Без legacy подписок на основном пути | ✅ redirect `/subscription` |

---

## Gaps (следующие спринты)

| Gap | Примечание |
|-----|------------|
| Замена всех legacy paywall entry points | Часть экранов всё ещё `AmaConfirmDialog` only |
| Outcome sheet D3 (funnel) | Отдельный sheet «за 3 дня вы…» |
| AMS packs S/M/L | Ghost в UI |
| Единый BFF billing | Опционально aggregate endpoint |

---

*Следующий epic: Payment Phase B (checkout-session + webhook) без ломки PaywallSheet API.*
