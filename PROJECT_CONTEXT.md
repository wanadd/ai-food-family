# Project Context

## Goal

Build a Telegram Mini App for AI Food Family.

The project uses a monorepo layout:

- `apps/web` — Next.js + Tailwind + TypeScript
- `apps/api` — FastAPI
- Docker Compose for local development (web, api, PostgreSQL, Redis)

## Current Scope

- Next.js frontend with a home page and live API health status
- FastAPI backend with `/health` (checks PostgreSQL and Redis)
- Docker Compose for the full local stack

## Technical Notes

- Frontend runs on port `3000`.
- Backend runs on port `8000`.
- PostgreSQL: port `5432`, default DB/user/password `aifood`.
- Redis: port `6379`.
- Frontend calls the API via `NEXT_PUBLIC_API_URL`.
- Telegram Web App SDK (`@twa-dev/sdk` + official script)
- Auth via validated `initData` → `POST /auth/telegram` → user in PostgreSQL
- Bot menu button auto-configured when `TELEGRAM_BOT_TOKEN` and `TELEGRAM_WEBAPP_URL` are set

## Product Notes

Clarify before major feature work:

- Who is the first target user?
- What food-related workflow should the Mini App solve first?
- What data should be stored?
- Which AI features are essential for the MVP?
