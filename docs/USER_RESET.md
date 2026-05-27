# User Reset — Production Guide

Сброс одного пользователя до состояния первого запуска Telegram Mini App.

> **Скрипт не запускается автоматически.** Только ручной запуск с явным подтверждением.

---

## Содержание

1. [Что делает скрипт](#что-делает-скрипт)
2. [Что НЕ трогает](#что-не-трогает)
3. [Затрагиваемые таблицы](#затрагиваемые-таблицы)
4. [Логика семьи](#логика-семьи)
5. [Требования](#требования)
6. [Примеры запуска](#примеры-запуска)
7. [Порядок действий перед сбросом](#порядок-действий-перед-сбросом)
8. [Риски](#риски)
9. [Что происходит после сброса](#что-происходит-после-сброса)

---

## Что делает скрипт

`scripts/reset_user.py` выполняет полный сброс одного пользователя:

- удаляет onboarding / профиль
- удаляет сгенерированные меню
- удаляет списки покупок (личные)
- удаляет продукты в кладовой (личные)
- удаляет избранное и рейтинги рецептов
- удаляет коллекции пользователя
- удаляет историю приготовлений
- удаляет настройки уведомлений
- удаляет подписку / биллинг
- удаляет AMA-кошелёк и транзакции
- удаляет care-настройки / нутрициолог
- удаляет прогресс, тренировки, цели по нутриентам
- удаляет состояние бота в FSM (telegram_bot_sessions)
- удаляет личный AI-кэш (recipe_explanations)
- обрабатывает семью (см. [Логика семьи](#логика-семьи))
- удаляет запись пользователя из `users`

После сброса пользователь может заново зайти в Mini App и пройти онбординг с нуля.

---

## Что НЕ трогает

| Объект | Причина |
|--------|---------|
| `recipes` — глобальный каталог рецептов | Системные данные |
| `recipe_ingredients`, `recipe_steps`, `recipe_tags`, `recipe_allergens`, `recipe_restrictions` | Дочерние таблицы глобального каталога |
| `recipe_scenarios` | Системный scoring рецептов |
| `recipe_import_jobs` | Служебные операции импорта |
| `subscription_plans` | Глобальный каталог тарифов |
| `shopping_categories` с `is_system = true` | Системные категории |
| `recipe_collections` с `visibility = 'system'` | Системные коллекции |
| `admin_actions`, `admin_error_logs` | Аудит-лог (user_id → SET NULL, строки остаются) |
| `admin_login_attempts` | Лог безопасности (keyed by telegram_id, не FK) |
| Данные других пользователей | Изолированы через WHERE user_id = ? |
| Общие данные семьи (при мульти-пользовательской семье) | Остальные члены не затрагиваются |

---

## Затрагиваемые таблицы

### Шаг 1 — Явное удаление до удаления строки `users`

Эти таблицы не имеют FK с CASCADE на `users` или используют SET NULL,
поэтому удаляются явно до удаления пользователя.

| Таблица | Условие | Примечание |
|---------|---------|------------|
| `telegram_bot_sessions` | `telegram_id = ?` | Нет FK на users; удаляется по telegram_id |
| `recipe_history` | `user_id = ?` | FK SET NULL — удаляем явно, чтобы не осталось анонимных строк |
| `recipe_collections` | `owner_user_id = ? AND visibility != 'system'` | `collection_recipes` каскадно удаляются |

### Шаг 2 — Семья

См. [Логика семьи](#логика-семьи).

### Шаг 3 — Каскадное удаление через `DELETE FROM users WHERE id = ?`

Все строки ниже удаляются **автоматически** через `ON DELETE CASCADE`.

| Таблица | Описание |
|---------|----------|
| `user_profiles` | Данные онбординга, предпочтения, цели |
| `user_preferences` | Активный режим (personal/family) |
| `user_notification_settings` | Настройки уведомлений и напоминаний |
| `care_settings` | Настройки нутрициолога (1:1) |
| `care_notifications` | Отложенные уведомления Care |
| `care_events` | Лог событий Care |
| `recipe_favorites` | Избранные рецепты |
| `recipe_ratings` | Рейтинги и счётчики приготовлений |
| `recipe_explanations` | AI-кэш объяснений рецептов |
| `family_menu_selections` | Сгенерированные меню (личные) |
| `family_shopping_lists` | Список покупок (личный) |
| `family_pantry_items` | Кладовая (личные позиции) |
| `meal_leftovers` | Остатки блюд (личные) |
| `meal_checkins` | Отметки о приёме пищи |
| `water_intake_logs` | Журнал потребления воды |
| `event_plans` | Планы праздничных блюд |
| `deferred_nutrition_advice` | Отложенные советы нутрициолога |
| `progress_entries` | Замеры веса и тела |
| `training_entries` | Тренировки |
| `nutrition_targets` | Цели по КБЖУ |
| `user_subscriptions` | Подписка и счётчики использования |
| `ama_wallets` + `ama_transactions` | AMA-токены (кошелёк + транзакции через каскад) |
| `ai_usage_logs` | Лог AI-запросов и стоимости |
| `admin_sessions` | Сессии панели администратора |
| `family_invites` (invited_by_user_id) | Приглашения, отправленные этим пользователем |

### Строки с SET NULL (остаются с user_id = NULL)

Эти строки **не удаляются** — `user_id` обнуляется:

| Таблица | Колонка | Значение |
|---------|---------|----------|
| `family_members` | `user_id` | Строка участника остаётся (виртуальный след) |
| `family_invites` | `invited_user_id` | Приглашение остаётся (принятые факты) |
| `collection_recipes` | `added_by_user_id` | Рецепт в коллекции другого пользователя сохраняется |
| `family_pantry_items` | `added_by_user_id` | Добавленный в семейную кладовую остаётся |
| `meal_leftovers` | `added_by_user_id` | Остатки, добавленные в семейный контекст |
| `admin_actions` | `admin_user_id` | Аудит сохраняется с обнулённым user_id |
| `admin_error_logs` | `user_id` | Лог ошибок сохраняется |

---

## Логика семьи

### Случай A: пользователь — единственный реальный член семьи

```
family_members WHERE family_id = ? AND user_id IS NOT NULL → 1 строка
```

**Действие:** удалить запись `families`. Каскадно удалятся:
- все `family_members` (включая виртуальных)
- `family_menu_selections` (семейные)
- `family_shopping_lists` (семейные)
- `family_pantry_items` (семейные)
- `family_recipe_preferences`
- `meal_eating_schedules`
- `recipe_collections` (family-owned)
- `recipe_history` (с family_id)
- `ama_wallets` (семейный кошелёк)

### Случай B: в семье есть другие реальные пользователи

```
family_members WHERE family_id = ? AND user_id IS NOT NULL → > 1 строк
```

**Действие:** удалить только строку `family_members` этого пользователя.  
Каскадно удалятся только данные этого участника:
- `meal_eating_schedules` (schedule этого family_member)
- `family_recipe_preferences` (предпочтения этого family_member)
- `progress_entries`, `training_entries`, `nutrition_targets` (если были через person_id)

Семья, общее меню, общий список покупок, другие участники — **не затрагиваются**.

---

## Требования

- Python 3.11+
- Пакет `sqlalchemy` (`pip install sqlalchemy psycopg2-binary`)
- Переменная окружения `DATABASE_URL`
- Доступ к production PostgreSQL (прямой или через SSH-туннель)
- **Резервная копия базы перед запуском** (см. `scripts/backup.sh`)

---

## Примеры запуска

### 1. Превью (безопасный режим, нет изменений)

```bash
export DATABASE_URL="postgresql://user:pass@db-host:5432/food_family"

# По Telegram ID
python scripts/reset_user.py --telegram-id 123456789 --dry-run

# По внутреннему user_id
python scripts/reset_user.py --user-id 42 --dry-run
```

Скрипт выведет:
- сколько строк будет удалено в каждой таблице
- что произойдёт с семьёй
- список защищённых таблиц

**Никаких изменений в БД не производится.**

### 2. Реальный сброс

```bash
export DATABASE_URL="postgresql://user:pass@db-host:5432/food_family"

python scripts/reset_user.py --telegram-id 123456789 --confirm
```

Скрипт:
1. Показывает тот же превью, что и `--dry-run`
2. Предупреждает, что действие необратимо
3. Ждёт ввода `YES` (строго, с учётом регистра)
4. Выполняет всё в одной транзакции
5. При любой ошибке — откат транзакции, БД не изменится

### 3. Через SSH-туннель к production

```bash
# Открыть туннель в отдельном терминале
ssh -L 15432:db-internal-host:5432 deploy@prod-server

# Запустить скрипт
DATABASE_URL="postgresql://app_user:secret@localhost:15432/food_family" \
  python scripts/reset_user.py --telegram-id 123456789 --dry-run
```

---

## Порядок действий перед сбросом

```
1. Сделать резервную копию
   bash scripts/backup.sh

2. Проверить dry-run
   python scripts/reset_user.py --telegram-id TID --dry-run

3. Убедиться, что в отчёте нет неожиданных строк

4. Запустить с --confirm
   python scripts/reset_user.py --telegram-id TID --confirm

5. Ввести YES

6. Проверить вывод скрипта (все шаги OK)

7. При необходимости — проверить в psql:
   SELECT * FROM users WHERE telegram_id = TID;
   -- Должно вернуть 0 строк
```

---

## Риски

| Риск | Степень | Митигация |
|------|---------|-----------|
| Случайный сброс не того пользователя | Высокая | Всегда запускать `--dry-run` первым; подтверждение `YES` |
| Потеря биллинговых данных | Средняя | `user_subscriptions` удаляется; резервная копия обязательна |
| Потеря данных семьи при solo-сбросе | Средняя | dry-run явно показывает "SOLO family → DELETE"; проверить до запуска |
| Остаточные SET NULL строки в audit-таблицах | Низкая | `admin_actions.admin_user_id` обнуляется — это корректно для аудита |
| Скрипт не найдёт пользователя | Низкая | Явная ошибка с exit code 1 |
| Ошибка в середине транзакции | Низкая | Вся транзакция откатится, БД не изменится |
| Пользователь был admin — сессии остаются | Низкая | `admin_sessions` каскадно удаляются вместе с users |
| `telegram_bot_sessions` не удалится (telegram_id не совпадает) | Низкая | Скрипт выводит rowcount; при 0 — сессии не было |

### Что НЕ восстанавливается без backup

- История приготовлений пользователя
- Данные онбординга (цели, диеты, ограничения)
- Подписка и баланс AMA-токенов
- Личные коллекции рецептов
- Прогресс и замеры тела
- Настройки уведомлений

**Всегда делайте `pg_dump` перед запуском `--confirm`.**

---

## Технические детали

### Порядок удаления

```
1. telegram_bot_sessions        (DELETE WHERE telegram_id = ?)
2. recipe_history               (DELETE WHERE user_id = ?)
3. recipe_collections           (DELETE WHERE owner_user_id = ? AND visibility != 'system')
   └─ collection_recipes        (CASCADE)
4a. [solo family]  families     (DELETE WHERE id = ?)  → всё каскадно
4b. [multi family] family_members (DELETE WHERE id = fm_id) → member-data каскадно
5. users                        (DELETE WHERE id = ?)  → всё остальное каскадно
```

### Транзакционность и изоляция соединений

Скрипт использует **два независимых соединения**:

| Фаза | Соединение | Цель |
|------|-----------|------|
| Preview (lookup + dry-run counts) | `engine.connect()` | Только SELECT; закрывается до промпта |
| Writes (шаги 1–5) | `engine.begin()` | Явная транзакция; commit при успехе, rollback при любом исключении |

Промпт `YES` запрашивается **между** фазами, когда ни одно соединение не открыто.

Это исключает ошибку `InvalidRequestError: This connection has already initialized
a SQLAlchemy Transaction() via autobegin; can't call begin() here`, которая
возникает если SELECT и DELETE делить одно соединение с `engine.connect()`.

### Идентификаторы

| Аргумент | Источник |
|----------|----------|
| `--telegram-id` | `users.telegram_id` (BIGINT) — видимый в Telegram |
| `--user-id` | `users.id` (INTEGER) — внутренний первичный ключ |

Если нужен `telegram_id` по `user_id`:
```sql
SELECT telegram_id FROM users WHERE id = 42;
```

---

*Скрипт: `scripts/reset_user.py`*  
*Последнее обновление: 2026-05-28*
