# PLANAM 2026 — Decision Record

**Дата:** 2026-06-03  
**Статус:** утверждено для Sprint 0  
**Владелец:** Product + Monetization

---

## DR-001 — Параметры пробного периода (CR1)

| Параметр | Решение 2026 | As-is (до Sprint 0) |
|----------|--------------|---------------------|
| Длительность trial | **3 календарных дня** | 14 дней |
| Стартовые Амы | **50** | 200 |
| Генераций меню в trial | **5** (достаточно для WOW + 1 пересборка) | 20 |
| После trial | Freemium: shopping/pantry + **1 gen/неделю** | без изменений в DR |

**Обоснование:** короткий trial создаёт urgency без toxic paywall; 50 Амов ≈ 10–15 AI-действий ([`PLANAM_CONVERSION_FUNNEL_2026.md`](PLANAM_CONVERSION_FUNNEL_2026.md)).

**Реализация:** [`subscription_catalog.py`](../apps/api/app/services/subscription_catalog.py) — `TRIAL_DAYS`, `TRIAL_MENU_GENERATIONS`, `monthly_ams` plan `trial`.

**Миграция существующих пользователей:** активные trial с `trial_ends_at` в будущем **не пересчитываются** автоматически; только новые `ensure_user_billing`. Ops: опциональный admin extend.

---

## DR-002 — Home API contract (CR2)

| Поле | Решение |
|------|---------|
| `today_meals[].recipe_id` | Обязательно, если есть в `menu_data` |
| `today_meals[].image_url` | Из `recipes.image_url` |
| `next_action` | Enum + `cta_label` + `redirect_path` |
| `shopping_unchecked_count` | В overview |
| `pantry_expiring_preview` | Первый продукт с expiry ≤ 48h |

**Реализация:** [`menu_overview.py` schema](../apps/api/app/schemas/menu_overview.py), [`home_next_action.py`](../apps/api/app/services/home_next_action.py).

---

## DR-003 — AppGate и WOW (CR3)

| Решение |
|---------|
| Legal **до** доступа к приложению (без изменений) |
| Телефон **после** WOW: `NEXT_PUBLIC_PLANAM_DEFER_PHONE_GATE=true` |
| Флаг завершения WOW: `sessionStorage.planam_wow_complete=1` |
| Маршрут `/admin` **обходит** phone/legal gate (собственная auth в AdminShell) |

---

## DR-004 — Motion (CR4)

| Решение |
|---------|
| **Без parallax** на recipe detail; статичный hero 16:9 |
| Master Spec обновлён |

---

## DR-005 — Payment scope (CR5)

| Фаза | Scope |
|------|-------|
| Sprint 0–8 | UI subscription + `select-plan` (staging) |
| Post-Sprint 8 | Checkout adapter — см. [`PLANAM_PAYMENT_ARCHITECTURE_2026.md`](PLANAM_PAYMENT_ARCHITECTURE_2026.md) |
| Marketing paid | **Запрещён** без Phase B checkout |

---

## DR-006 — Feature flag UI 2026

| Env | Значение |
|-----|----------|
| `NEXT_PUBLIC_PLANAM_UI_2026` | `false` default до Sprint 2 |
| `NEXT_PUBLIC_PLANAM_DEFER_PHONE_GATE` | `true` default |

---

*При изменении DR — обновлять этот файл и [`SPRINT_0_COMPLETION_REPORT.md`](SPRINT_0_COMPLETION_REPORT.md).*
