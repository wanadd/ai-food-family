# Безопасный деплой ПланАм

Порядок обновления production с возможностью отката.

## Перед деплоем

1. Убедитесь, что в `.env` на сервере задан `ADMIN_TELEGRAM_IDS` (ваш Telegram ID).
2. Проверьте, что на сервере достаточно места для дампа БД (`backups/`).

## Порядок обновления

### 1. Получить код

```bash
cd /path/to/ai-food-family
git pull
```

### 2. Создать резервную копию

**На хосте (рекомендуется):**

```bash
chmod +x scripts/backup.sh scripts/restore.sh
./scripts/backup.sh
```

Скрипт создаст каталог `backups/YYYY-MM-DD_HH-MM/` с:

- `database.sql` — дамп PostgreSQL;
- `env.backup` — копия `.env`;
- `timestamp.txt` — время создания.

**Через админ-панель** (Mini App → `/admin` → «Резервные копии» → «Создать backup») — если в контейнере API установлен `postgresql-client` и смонтирован том `./backups:/app/backups`.

### 3. Собрать и запустить

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### 4. Проверить health

```bash
curl -s https://YOUR_DOMAIN/api/health
curl -s https://YOUR_DOMAIN/api/health/live
```

Ожидается `"status":"ok"` (или `"degraded"` только при проблемах Redis/Postgres).

Проверьте в Telegram: Mini App открывается, бот отвечает на `/start`.

### 5. Если что-то пошло не так — откат

```bash
./scripts/restore.sh backups/YYYY-MM-DD_HH-MM
```

Скрипт:

1. остановит `web`, `api`, `nginx`;
2. восстановит базу из `database.sql`;
3. по запросу восстановит `.env` из `env.backup`;
4. поднимет все сервисы снова.

После отката снова проверьте `/api/health`.

## Переменные окружения (админ)

```env
ADMIN_TELEGRAM_IDS=123456789
BACKUP_ROOT=backups
```

Несколько админов: `ADMIN_TELEGRAM_IDS=111,222,333`

## Важно

- Не коммитьте `.env` и каталог `backups/` в git.
- Опасные действия в админке (начисление Амов, выдача тарифа, создание backup) требуют подтверждения в UI.
- Платёжные интеграции на MVP не подключены — тарифы выдаются вручную через админку.
