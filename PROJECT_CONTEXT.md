# Project Context

## Goal

Build **ПланАм** — Telegram Mini App for meal planning and shopping lists for **one user** or a **family**.

The project uses a monorepo layout:

- `apps/web` — Next.js + Tailwind + TypeScript
- `apps/api` — FastAPI
- Docker Compose for local development (web, api, PostgreSQL, Redis)

## Product model

- **Default: personal mode** — after Telegram auth the user can use onboarding, AI menu, shopping list, pantry, recipes, and notifications without creating a family.
- **Optional: family mode** — user creates a family in «Семейный режим» and switches between **Личный** / **Семейный** on the home screen.
- Data is stored with `user_id` (personal) or `family_id` (family), never both required at once.

## Current Scope

- Telegram auth via initData + **обязательный** phone через бот (/start → request_contact)
- Telegram bot: /start, /help, /invite +номер (после подтверждения телефона)
- AI menu (3 variants), shopping list, pantry, recipes, notifications
- Family: members, roles, shared data when family mode is active
- Production deploy: `docker-compose.prod.yml`, nginx, HTTPS — see `DEPLOY.md`

## Technical Notes

- Frontend runs on port `3000`.
- Backend runs on port `8000`.
- API scope header: `X-App-Mode: personal | family`
- `GET/PATCH /users/me/app-context` — active mode and family info

## Product Notes

- Recipes favorites are always per user (not per family).
- Onboarding is always per user; family members have their own goals/restrictions.
