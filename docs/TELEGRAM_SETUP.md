# Telegram Mini App Setup

## 1. BotFather

1. Create a bot: `/newbot`
2. Create Mini App: `/newapp` → choose bot → set title and **HTTPS URL**
3. Note **bot username** and optional **short name** for direct link

For local development use a public HTTPS tunnel (ngrok, cloudflared):

```bash
ngrok http 3000
```

Use the HTTPS URL as Web App URL in BotFather and in `.env`:

```env
TELEGRAM_WEBAPP_URL=https://xxxx.ngrok-free.app
BACKEND_CORS_ORIGINS=http://localhost:3000,https://xxxx.ngrok-free.app
NEXT_PUBLIC_API_URL=https://xxxx.ngrok-free.app:8000
```

Telegram opens the frontend URL; the frontend calls the API URL from `NEXT_PUBLIC_API_URL`.

## 2. Environment

```env
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_WEBAPP_URL=https://your-public-url
NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_bot_username
NEXT_PUBLIC_TELEGRAM_APP_SHORT_NAME=app
```

On API startup, `setChatMenuButton` configures the bot menu button **«Открыть приложение»**.

## 3. Open Mini App

- Menu button in bot chat (after API startup with token + URL)
- Link on the website: **«Открыть Mini App в Telegram»**
- Direct link: `https://t.me/<bot_username>/<short_name>`

## 4. Verify auth

Inside Mini App you should see green **Авторизация OK** with Telegram ID and DB user id.

API check:

```bash
curl -X POST http://localhost:8000/auth/telegram \
  -H "Content-Type: application/json" \
  -d "{\"init_data\":\"<paste from WebApp.initData>\"}"
```

Database:

```bash
docker compose exec postgres psql -U aifood -d aifood -c "SELECT id, telegram_id, username, first_name FROM users;"
```

## 5. Уведомления

1. Пользователь должен **нажать Start** в чате с ботом — иначе Telegram не примет `sendMessage`.
2. В Mini App откройте **Уведомления** (`/notifications`) и задайте время.
3. API раз в 30 секунд проверяет настройки и отправляет напоминания в выбранный часовой пояс:
   - **Купить** — неотмеченные позиции из списка покупок
   - **Готовить** — блюда из выбранного семейного меню
4. В сообщении есть кнопка Web App (список покупок или меню).

По умолчанию: покупки в **09:00**, готовка в **17:30**, часовой пояс **Europe/Moscow**.
