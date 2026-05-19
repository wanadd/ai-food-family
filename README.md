# AI Food Family

Telegram Mini App project with a Next.js frontend and a FastAPI backend.

## Project Structure

```text
.
├── apps/
│   ├── web/              # Next.js + Tailwind + TypeScript
│   └── api/              # FastAPI
├── docker-compose.yml    # web, api, PostgreSQL, Redis
├── .env.example
├── PROJECT_CONTEXT.md
└── TASKS.md
```

## Quick Start

1. Copy environment examples:

```bash
cp .env.example .env
cp apps/web/.env.example apps/web/.env.local
cp apps/api/.env.example apps/api/.env
```

2. Start the stack:

```bash
docker compose up --build
```

3. Open:

- Frontend: http://localhost:3000
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

## Local Development Without Docker

### Web

```bash
cd apps/web
npm install
npm run dev
```

### API

```bash
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run PostgreSQL and Redis locally (or via `docker compose up postgres redis`) and set `DATABASE_URL` / `REDIS_URL` in `apps/api/.env`.
