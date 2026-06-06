# PLANAM V1 — Release Screens

**Версия:** 1.1  
**Дата:** 2026-06-03  
**Обновление покупок:** [PLANAM_V1_SHOPPING_MODEL_UPDATE.md](./PLANAM_V1_SHOPPING_MODEL_UPDATE.md)  
**Источник маршрутов:** [PLANAM_CURRENT_STATE_SCREENS.md](./PLANAM_CURRENT_STATE_SCREENS.md)

---

# Bottom navigation (5 tabs)

| Tab | URL | Статус V1 |
|-----|-----|-----------|
| Сегодня | `/plan/today` | **Обязательный** |
| Покупки | `/home/shopping` | **Обязательный** |
| ПланАм | `/` | **Обязательный** (центр) |
| Здоровье | `/wellness` | **Обязательный** |
| Профиль | `/account` | **Обязательный** |

---

# 1. Обязательные экраны

Пользователь видит в V1. Без них — не релиз.

| URL | Название | Роль |
|-----|----------|------|
| `/` | ПланАм | Центр: hero + статусы + AI entry |
| `/plan/today` | Сегодня | Меню дня |
| `/home/shopping` | Покупки | Единый семейный список: меню + ручные; 14 категорий; «+ Добавить» |
| `/wellness` | Здоровье | Free metrics + PRO block |
| `/account` | Профиль | Hub «Я» |
| `/plan/generate` | Генерация меню | Onboarding + empty states |
| `/plan/recipes/[id]` | Рецепт | Деталь из Сегодня/каталога |
| `/account/nutrition` | Питание | Профиль питания |
| `/account/family` | Семья | Участники, приглашения |
| `/account/notifications` | Уведомления | Настройки push |
| `/account/subscription` | Подписка | Тарифы |
| `/onboarding` (flow) | Онбординг | Первый запуск |

**Sheets (не отдельные routes):** meal outcome, leftovers, «Спросить PlanAm», pantry quick view, **добавить покупку** (ручной ввод с AI-категоризацией).

---

# 2. Желательные экраны (P1)

Улучшают V1, но не блокируют релиз если упрощены.

| URL | Название | Роль |
|-----|----------|------|
| `/plan` | Меню недели | Второй уровень из «Открыть меню» |
| `/plan/recipes` | Каталог | Replace flow, поиск |
| `/home/pantry` | Запасы | Из статуса «Остатки» |
| `/wellness/chat` | AI чат | PRO depth (не tab) |
| `/account/settings` | Настройки | Техника второго уровня |
| `/account/subscription/checkout` | Оплата | Если billing готов |
| `/account/settings/*` | Документы, поддержка | Compliance |

---

# 3. Лишние экраны (не показывать пользователю V1)

Остаются в коде с redirect или feature flag off. **Не в user path.**

| URL / группа | Почему лишний |
|--------------|---------------|
| `/menu/*` (legacy hub) | Заменён `/plan/*` |
| `/profile`, `/settings` (legacy) | Заменён `/account/*` |
| `/family` (legacy) | → `/account/family` |
| `/notifications` (legacy) | → `/account/notifications` |
| `/recipes`, `/menu/recipes` (legacy) | → `/plan/recipes` |
| `/shopping` (legacy) | → `/home/shopping` |
| `/health/*` (legacy) | → `/wellness/*` |
| `/home` | Redirect `/` |
| Quick actions grid как главный UI | Заменён hero + 3 статуса |

---

# 4. Скрытые экраны (второй уровень / admin / stub)

Доступны по ссылке, не в nav.

| URL | Кто видит |
|-----|-----------|
| `/account/ams` | Power users, billing |
| `/account/settings/account` | Настройки аккаунта |
| `/account/settings/documents` | Legal |
| `/account/settings/delete-data` | GDPR |
| `/account/settings/support` | Support |
| `/account/settings/about` | About |
| `/menu/event` | P2 events |
| `/menu/favorites`, `/menu/collections` | P2 |
| `/progress` | P2 |
| Admin / internal routes | Только staff |

---

# 5. Объединения маршрутов

| Было (2 пути) | Станет V1 |
|---------------|-----------|
| `/` + 🏠 header + `/home` | Только `/` как tab ПланАм |
| `/profile` + `/account` | Только `/account` |
| `/settings` + `/account/settings` | Только `/account/settings` |
| `/family` + `/account/family` | Только `/account/family` |
| `/menu/generate` + `/plan/generate` | Только `/plan/generate` |
| `/health/chat` + `/wellness/chat` | Только `/wellness/chat` |
| Replace: каталог + AI sheet (2 UX) | Один flow «Заменить» |

---

# 6. Второй уровень (не tab, не home)

| Экран | Entry points |
|-------|--------------|
| `/plan` | «Открыть меню» с ПланАм |
| `/plan/recipes` | Subtab; replace с Сегодня |
| `/home/pantry` | Статус 📦; ссылка с Покупок |
| `/plan/generate` | Empty today; onboarding |
| `/wellness/chat` | PRO block в Здоровье |
| `/account/*` | Hub Профиль |
| Recipe detail | Карточка блюда |

---

# 7. Subtabs (Сегодня section)

| Subtab | URL | V1 |
|--------|-----|-----|
| Сегодня | `/plan/today` | Tab + default |
| Неделя | `/plan` | P1 второй уровень |
| Рецепты | `/plan/recipes` | P1 второй уровень |

**Не:** отдельная bottom tab «Меню».

---

# 8. Карта переходов (целевая)

```text
[Bottom Nav]
  Сегодня ←→ ПланАм ←→ Покупки ←→ Здоровье ←→ Профиль

ПланАм → Приготовить → Сегодня
ПланАм → 🛒 → Покупки
ПланАм → 📦 → Pantry sheet / /home/pantry
ПланАм → ❤️ → Здоровье
ПланАм → Спросить → Sheet (AI)
Сегодня → Заменить → Каталог (replace mode)
Сегодня → Рецепт → /plan/recipes/[id]
Профиль → Семья / Питание / Подписка / Настройки
```

---

# 9. Сводка

| Категория | Кол-во (ориентир) |
|-----------|-------------------|
| Обязательные | 12 routes + sheets |
| Желательные | 8 routes |
| Лишние (redirect) | 35+ legacy |
| Скрытые | 10+ |

---

*Release Screens не меняет Blueprint. Уточняет маршрутизацию для ТЗ на разработку.*
