# Deploy на Timeweb Cloud (Docker Compose)

Инструкция для VPS в Timeweb Cloud: один сервер, Docker Compose, **nginx** как reverse proxy, **HTTPS** через Let's Encrypt.

## Архитектура

```text
Internet :443 / :80
    │
    ▼
  nginx ──► web:3000   (Next.js)
    │
    └── /api/* ──► api:8000   (FastAPI)
              │
              ├── postgres:5432
              └── redis:6379
```

- Публичный URL фронтенда: `https://ВАШ_ДОМЕН`
- API для Mini App: `https://ВАШ_ДОМЕН/api` (проксируется nginx)
- PostgreSQL и Redis **не** публикуются наружу

## Требования

| Параметр | Значение |
|----------|----------|
| Timeweb Cloud | VPS (Ubuntu 22.04/24.04 рекомендуется) |
| RAM | минимум 2 GB (лучше 4 GB) |
| Диск | от 20 GB |
| Домен | A-запись `@` → IP сервера |
| Порты | 80, 443 открыты в firewall Timeweb |

## 1. Подготовка сервера

Подключитесь по SSH:

```bash
ssh root@ВАШ_IP
```

Установите Docker (если ещё нет):

```bash
apt update && apt upgrade -y
apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sh
```

Проверка:

```bash
docker --version
docker compose version
```

### Firewall в панели Timeweb

В разделе **Сеть / Firewall** разрешите входящие:

- TCP **22** (SSH)
- TCP **80** (HTTP, ACME + редирект)
- TCP **443** (HTTPS)

## 2. Клонирование проекта

```bash
cd /opt
git clone https://github.com/ВАШ_ОРГАНИЗАЦИЯ/ai-food-family.git
cd ai-food-family
```

## 3. Production-конфигурация

Скопируйте и отредактируйте переменные:

```bash
cp .env.production.example .env
nano .env
```

Обязательно замените:

| Переменная | Пример |
|------------|--------|
| `DOMAIN` | `food.example.com` |
| `CERTBOT_EMAIL` | email для Let's Encrypt |
| `POSTGRES_PASSWORD` | длинный случайный пароль |
| `TELEGRAM_BOT_TOKEN` | токен от @BotFather |
| `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` | username бота |
| `NEXT_PUBLIC_API_URL` | `https://food.example.com/api` |
| `TELEGRAM_WEBAPP_URL` | `https://food.example.com` |
| `BACKEND_CORS_ORIGINS` | `https://food.example.com` |

Убедитесь, что `DATABASE_URL` содержит тот же пароль, что и `POSTGRES_PASSWORD`.

### BotFather

1. `/newapp` → Web App URL: `https://ВАШ_ДОМЕН`
2. Тот же домен в `TELEGRAM_WEBAPP_URL`
3. `TELEGRAM_MENU_BUTTON_TEXT=Открыть ПланАм`

### Webhook бота (/start и номер телефона)

После HTTPS зарегистрируйте webhook (API доступен по префиксу `/api`):

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://ВАШ_ДОМЕН/api/telegram/webhook"
```

Проверка:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

Пользователь пишет `/start` в боте → создаётся запись в `users` → при отсутствии телефона запрашивается contact → кнопка «Открыть ПланАм».

## 4. Первый запуск (HTTP)

Соберите и запустите стек (без SSL, для получения сертификата):

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Проверьте:

```bash
docker compose -f docker-compose.prod.yml ps
curl -s http://127.0.0.1/api/health
```

С внешней машины (после DNS):

- `http://ВАШ_ДОМЕН` — открывается сайт
- `http://ВАШ_ДОМЕН/api/health` — `postgres` и `redis` в статусе ok

## 5. HTTPS (Let's Encrypt)

На сервере:

```bash
chmod +x deploy/init-letsencrypt.sh
export DOMAIN=food.example.com
export CERTBOT_EMAIL=admin@example.com
./deploy/init-letsencrypt.sh
```

Скрипт:

1. Запрашивает сертификат через webroot (`/.well-known/acme-challenge/`)
2. Переключает nginx на шаблон `app-ssl.conf.template`
3. Перезагружает nginx

Проверка:

```bash
curl -I https://ВАШ_ДОМЕН
curl -s https://ВАШ_ДОМЕН/api/health
```

Контейнер **certbot** в `docker-compose.prod.yml` автоматически обновляет сертификат каждые 12 часов.

### Ручной выпуск сертификата (альтернатива)

```bash
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  --email admin@example.com \
  --agree-tos --no-eff-email \
  -d food.example.com

docker compose -f docker-compose.prod.yml restart nginx
```

После появления файлов в volume `certbot_certs` nginx при старте сам выберет HTTPS-шаблон (если есть `fullchain.pem`).

## 6. Обновление приложения

```bash
cd /opt/ai-food-family
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Только API:

```bash
docker compose -f docker-compose.prod.yml up -d --build api
```

Только фронтенд (пересборка с `NEXT_PUBLIC_*`):

```bash
docker compose -f docker-compose.prod.yml up -d --build web
```

## 7. Полезные команды

```bash
# Логи
docker compose -f docker-compose.prod.yml logs -f nginx
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f web

# Статус
docker compose -f docker-compose.prod.yml ps

# Остановка
docker compose -f docker-compose.prod.yml down

# Остановка с удалением volumes (ОСТОРОЖНО: удалит БД)
docker compose -f docker-compose.prod.yml down -v
```

### Бэкап PostgreSQL

```bash
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U aifood aifood > backup_$(date +%F).sql
```

Восстановление:

```bash
cat backup.sql | docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U aifood -d aifood
```

## 8. Файлы деплоя в репозитории

| Файл | Назначение |
|------|------------|
| `docker-compose.prod.yml` | Production Compose |
| `apps/web/Dockerfile.prod` | Next.js standalone build |
| `apps/api/Dockerfile.prod` | FastAPI без reload, 2 workers |
| `deploy/nginx/nginx.conf` | Главный конфиг nginx |
| `deploy/nginx/templates/app-init.conf.template` | HTTP до сертификата |
| `deploy/nginx/templates/app-ssl.conf.template` | HTTPS + редирект с 80 |
| `deploy/nginx/docker-entrypoint.sh` | Выбор шаблона по наличию сертификата |
| `deploy/init-letsencrypt.sh` | Первичный выпуск SSL |
| `.env.production.example` | Пример production `.env` |

## 9. Локальная разработка vs production

| | Development | Production |
|---|-------------|------------|
| Compose | `docker-compose.yml` | `docker-compose.prod.yml` |
| Web | `npm run dev` + volume | `Dockerfile.prod`, standalone |
| API | `--reload` + volume | 2 workers, без volume |
| Порты | 3000, 8000 наружу | только 80/443 через nginx |
| API URL | `http://localhost:8000` | `https://домен/api` |

## 10. Troubleshooting

### DNS не резолвится

Подождите распространения A-записи (до 24 ч). Проверка: `dig +short ВАШ_ДОМЕН`.

### Certbot: connection refused

- Порт 80 открыт в Timeweb Firewall
- `DOMAIN` в `.env` совпадает с реальным доменом
- nginx запущен: `docker compose -f docker-compose.prod.yml ps nginx`

### 502 Bad Gateway

```bash
docker compose -f docker-compose.prod.yml logs api web
docker compose -f docker-compose.prod.yml ps
```

Дождитесь `healthy` у `api` и `postgres`.

### Telegram: авторизация не работает

- `TELEGRAM_WEBAPP_URL` = `https://ВАШ_ДОМЕН` (без слэша в конце)
- `NEXT_PUBLIC_API_URL` = `https://ВАШ_ДОМЕН/api`
- Mini App открывается только по HTTPS

### CORS ошибки

`BACKEND_CORS_ORIGINS` должен быть ровно `https://ВАШ_ДОМЕН` (тот же origin, что у фронта).

### Слабый сервер (1 GB RAM)

Сборка Next.js может упасть по OOM. Временно добавьте swap:

```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

## 11. Чеклист перед продакшеном

- [ ] Сильный `POSTGRES_PASSWORD`
- [ ] `.env` не коммитится в git
- [ ] DNS A-запись на IP VPS
- [ ] HTTPS работает
- [ ] `https://домен/api/health` — ok
- [ ] BotFather Web App URL обновлён
- [ ] Пользователь нажал Start у бота (для уведомлений)
- [ ] Настроен бэкап `postgres_data`
