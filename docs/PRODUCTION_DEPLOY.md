# Production Deploy Guide

Операционное руководство по деплою и устранению проблем nginx на production.  
Работает совместно с [DEPLOY_SAFE.md](DEPLOY_SAFE.md) (порядок обновления, backup/restore).

---

## Архитектура nginx в Docker

```
Internet → nginx:80/443 → web:3000   (Next.js)
                        → api:8000   (FastAPI)
```

nginx запускается из `deploy/nginx/docker-entrypoint.sh`, который:

1. Определяет нужный шаблон (`app-init.conf.template` или `app-ssl.conf.template`).
2. Прогоняет его через `envsubst '$DOMAIN'` → `/etc/nginx/conf.d/default.conf`.
3. Запускает `nginx -g 'daemon off;'`.

---

## Почему нужен `resolver 127.0.0.11`

### Проблема (до фикса)

Раньше шаблоны использовали `upstream`-блоки:

```nginx
upstream web_upstream {
    server web:3000;          # resolved ONCE at nginx startup
}
```

nginx резолвит DNS-имя **один раз при старте** и кэширует IP навсегда.  
После `docker compose up -d --build web` контейнер получает новый IP  
(например `172.18.0.7` → `172.18.0.9`), а nginx продолжает стучаться в старый → **502**.

Симптом в логах:

```
[error] connect() failed (111: Connection refused)
upstream: "http://172.18.0.7:3000/"
```

Временный обходной путь — `docker compose restart nginx` — помогал, потому что nginx
заново резолвил DNS при старте.

### Решение (текущее)

В `nginx.conf` добавлен:

```nginx
resolver 127.0.0.11 valid=10s ipv6=off;
```

`127.0.0.11` — встроенный DNS Docker (работает во всех bridge/overlay сетях).  
`valid=10s` — nginx кэширует разрешённый IP 10 секунд, затем переспрашивает DNS.

В шаблонах убраны `upstream`-блоки; адрес передаётся через переменную:

```nginx
location /api/ {
    set $api_upstream http://api:8000;
    rewrite ^/api/(.*) /$1 break;
    proxy_pass $api_upstream;          # nginx re-resolves via resolver
}

location / {
    set $web_upstream http://web:3000;
    proxy_pass $web_upstream;          # nginx re-resolves via resolver
}
```

Когда `proxy_pass` получает **переменную** (а не литеральный адрес), nginx обязан
использовать `resolver` для каждого разрешения — статический кэш больше не применяется.

После перезапуска `web` или `api` новый IP будет подхвачен в течение 10 секунд  
без каких-либо действий с nginx.

---

## Стандартный деплой

```bash
# 1. Получить код
git pull

# 2. Backup (обязательно перед каждым деплоем)
./scripts/backup.sh

# 3. Пересобрать и запустить всё
docker compose -f docker-compose.prod.yml up -d --build

# 4. Проверить health
curl -s https://YOUR_DOMAIN/api/health
curl -s https://YOUR_DOMAIN/api/health/live
```

### Пересборка только одного сервиса

```bash
# Пересобрать и перезапустить web (nginx не трогаем)
docker compose -f docker-compose.prod.yml up -d --build web

# Пересобрать api
docker compose -f docker-compose.prod.yml up -d --build api

# Обновить nginx (конфиг изменился)
docker compose -f docker-compose.prod.yml up -d --build nginx
```

После пересборки `web` или `api` nginx подхватит новый IP в течение 10 секунд.  
Рестартовать nginx вручную **не нужно**.

---

## Диагностика 502

### 1. Проверить логи nginx

```bash
docker compose -f docker-compose.prod.yml logs --tail=120 nginx
```

Ключевые строки:

| Строка в логах | Причина | Действие |
|----------------|---------|----------|
| `connect() failed (111: Connection refused)` | upstream ещё стартует | Подождать 15–30 сек |
| `no resolver defined to resolve web` | resolver не задан в nginx.conf | Обновить nginx.conf и пересобрать nginx |
| `upstream timed out` | backend завис | Проверить `docker compose logs web` |

### 2. Проверить статус контейнеров

```bash
docker compose -f docker-compose.prod.yml ps
```

Все сервисы должны быть `healthy`.

### 3. Проверить, что upstream доступен изнутри nginx

```bash
docker compose -f docker-compose.prod.yml exec nginx \
  sh -c "wget -qO- http://web:3000/api/health"

docker compose -f docker-compose.prod.yml exec nginx \
  sh -c "wget -qO- http://api:8000/health/live"
```

### 4. Принудительный сброс кэша resolver (экстренный)

Если после rebuild IP всё ещё не подхватывается:

```bash
docker compose -f docker-compose.prod.yml restart nginx
```

С текущим фиксом это должно требоваться не чаще раза — как правило проблема
исчезает сама в течение 10 секунд.

---

## Шаблоны nginx

| Шаблон | Когда используется |
|--------|--------------------|
| `app-init.conf.template` | До получения Let's Encrypt сертификата (только HTTP) |
| `app-ssl.conf.template` | После получения сертификата (HTTP → HTTPS + SSL) |

Выбор шаблона происходит автоматически в `docker-entrypoint.sh`:
- Если файл `/etc/letsencrypt/live/$DOMAIN/fullchain.pem` существует → `app-ssl`.
- Иначе → `app-init`.
- Можно переопределить: `NGINX_TEMPLATE=app-ssl.conf.template` в `.env`.

---

## SSL / Let's Encrypt

Первичная выдача сертификата (один раз):

```bash
chmod +x deploy/init-letsencrypt.sh
DOMAIN=your.domain EMAIL=you@example.com ./deploy/init-letsencrypt.sh
```

Продление — автоматически через certbot-контейнер (`sleep 12h` loop).

---

## Полезные команды

```bash
# Статус всех сервисов
docker compose -f docker-compose.prod.yml ps

# Логи nginx (последние 100 строк)
docker compose -f docker-compose.prod.yml logs --tail=100 nginx

# Логи web
docker compose -f docker-compose.prod.yml logs --tail=100 web

# Логи api
docker compose -f docker-compose.prod.yml logs --tail=100 api

# Проверить конфиг compose на синтаксические ошибки
docker compose -f docker-compose.prod.yml config --quiet

# Проверить, что nginx принял конфиг без ошибок
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# Health-эндпоинты
curl -s https://YOUR_DOMAIN/api/health
curl -s https://YOUR_DOMAIN/api/health/live
```
