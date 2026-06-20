# PLANAM V1 — Profile / Account / Health consolidation audit

Deep-dive into everything related to the user profile, account hub, nutrition
profile, family member nutrition, and the care/notifications split. Companion to
`reports/planam_project_consolidation_audit.md`.

---

## 1. Единая страница профиля V1 — Account Hub

Canonical: **`/account` (`AccountHub2026`)**. Это hub, а не свалка настроек.
Пункты хаба (`ACCOUNT_HUB_ITEMS_2026` в `nav-config-2026.ts`):

| блок | href | назначение |
|------|------|------------|
| Тема приложения | `/account` (inline) | светлая/тёмная/системная |
| Питание | `/account/nutrition` | цели, диеты, аллергии, ограничения (`NutritionProfileForm`) |
| Семья | `/account/family` | участники, роли, member nutrition (`FamilyDashboard`) |
| Подписка | `/account/subscription` | тариф и срок (`SubscriptionHub2026`) |
| Амы | `/account/ams` | баланс и история (`AmsHub2026`) |
| Уведомления | `/account/notifications` | напоминания и каналы (`NotificationsView`) |
| Настройки | `/account/settings` | аккаунт/документы/удаление/поддержка/о приложении |

«Мои данные» (имя/телефон) живут в `/account/settings/account`; «Безопасность/
данные» — `/account/settings/delete-data` + `/account/settings/documents`;
«Помощь» — `/account/settings/support`. Это покрывает требуемый hub-формат:
Мои данные · Цели и питание · Семья · Уведомления · Подписка · Безопасность/данные
· Помощь.

---

## 2. Profile / account / nutrition routes — что оставить / redirect / legacy

| route | компонент | статус | действие |
|-------|-----------|--------|----------|
| `/account` | `AccountHub2026` | ACTIVE_2026 | canonical hub |
| `/account/nutrition` | `NutritionProfileForm` | ACTIVE_2026 | оставить |
| `/account/family` | `FamilyDashboard` (shared) | ACTIVE_2026 | оставить |
| `/account/notifications` | `NotificationsView` (shared) | ACTIVE_2026 | оставить |
| `/account/subscription`, `/account/subscription/checkout` | `SubscriptionHub2026`, `PaymentStub2026` | ACTIVE_2026 | оставить |
| `/account/ams` | `AmsHub2026` | ACTIVE_2026 | оставить |
| `/account/settings` | `SettingsHub` (2026 hrefs) | ACTIVE_2026 | оставить |
| `/account/settings/{account,documents,delete-data,support,about}` | re-export из `/settings/*` | ACTIVE_2026 | контент один раз в `/settings/*` |
| `/profile` | `ProfileDashboard` (legacy) | DEPRECATED_REDIRECT | redirect → `/account` (есть) |
| `/profile/nutrition` | `NutritionProfileForm` (legacy layout) | DEPRECATED_REDIRECT | redirect → `/account/nutrition` (есть) |
| `/family` | `FamilyDashboard` | DEPRECATED_REDIRECT | redirect → `/account/family` (есть) |
| `/notifications` | `NotificationsView` | DEPRECATED_REDIRECT | redirect → `/account/notifications` (есть) |
| `/settings`, `/settings/*` | `SettingsHub` / `SettingsScaffold` | LEGACY_KEEP_TEMPORARY | контент-источник; redirect hub → `/account/settings` |
| `/subscription` | `SubscriptionDashboard` (legacy) | DEPRECATED_REDIRECT | redirect → `/account/subscription` (есть) |
| `/wellness`, `/wellness/chat` | `WellnessHome2026`, `WellnessChat2026` | ACTIVE_2026 | health/nutritionist цель |
| `/health*`, `/nutritionist*` | legacy dashboards | DEPRECATED_REDIRECT | redirect → `/wellness*` (есть) |
| `/nutritionist/care`, `/health/care` | — | DEPRECATED_REDIRECT | → `/notifications` (есть) |

Дубли убраны через redirect: `/settings/care` отсутствует; `/nutritionist/care`
→ `/health/care` → `/notifications`; пустых settings-страниц нет (все
`SettingsScaffold` имеют контент).

---

## 3. API write-paths профиля и source of truth

| endpoint | сервис | пишет | SoT | нормализация |
|----------|--------|-------|-----|--------------|
| `PUT /nutrition-profile/me` | `nutrition_profile.save_nutrition_profile` | `user_profiles` | `user_profiles.*` | **`normalization.profile.normalize_profile_payload`** (подключено) |
| `PUT /onboarding/me` | `onboarding.save_profile` | `user_profiles` | `user_profiles.*` | через тот же профиль; объединить с nutrition_profile (V2) |
| `PUT /families/{fid}/members/{mid}/nutrition` (virtual) | `family.update_member_nutrition` → `family_member_nutrition.apply_virtual_nutrition_to_member` | `family_members.nutrition_profile` | member dict | **`normalization.profile.normalize_member_nutrition`** (подключено) |
| `PUT /families/{fid}/members/{mid}/nutrition` (linked user) | `family.update_member_nutrition` → `save_nutrition_profile` | `user_profiles` | `user_profiles.*` | через `normalize_profile_payload` (подключено) |
| `PATCH /users/me/app-context` | `app_scope` | `user_preferences` | mode | — |

**Source of truth полей:**
- цели/диеты/аллергии/ограничения/любимое/нелюбимое → `user_profiles`
  (`nutrition_goal`, `diets`, `allergies`, `medical_restrictions`,
  `banned_foods`, `favorite_foods`, `disliked_foods`).
- legacy `user_profiles.goals` (JSONB список) синхронизируется из
  `nutrition_goal` через `sync_legacy_menu_fields` (для меню-AI).
- virtual member nutrition → `family_members.nutrition_profile` (JSONB).

**Что делают normalizers на write-path:**
- пустые строки удаляются из списков аллергий/диет;
- дубли аллергий/диет/ограничений удаляются без учёта регистра (порядок и
  оригинальный регистр первого вхождения сохраняются);
- текстовые поля (`medical_restrictions`, `banned_foods`, `favorite_foods`,
  `disliked_foods`) триммятся;
- неизвестные-но-непустые значения НЕ отбрасываются (нет закрытого словаря).

---

## 4. Legacy / drift риски профиля (для health-audit)

`backend/scripts/audit_project_health.py` (раздел Profile) флагует:
- `users_without_profile` — пользователи без `user_profiles`;
- `dirty_profiles` — профили с пустыми/дублирующимися `goals`/`diets`/`allergies`;
- `legacy_field_drift` — `goals` заполнены, но `nutrition_goal` пуст (не мигрирован);
- `members_without_nutrition` — virtual members без `nutrition_profile`,
  real members без целей и nutrition.

---

## 5. Выводы

1. Профиль приведён к hub-формату на `/account/*`; старые `/profile`, `/family`,
   `/notifications`, `/subscription` — redirect.
2. Все write-paths профиля (личный + member nutrition) проходят через единый
   `normalization.profile`.
3. `/settings/*` остаётся единственным контент-источником, переиспользуется в
   `/account/settings/*` через re-export (не дубль).
4. care/notifications не дублируются в UI: единый `/notifications` /
   `/account/notifications`; `*/care` → redirect.
5. Объединение `onboarding/me` и `nutrition-profile/me` в один сервис — кандидат
   Legacy Cleanup V2 (сейчас оба пишут один `UserProfile`, риск низкий).
