# 05 Technical Architecture

## Runtime

The repository contains a Next.js frontend and FastAPI backend, with PostgreSQL and Redis supplied through Docker-oriented development and deployment flows. Telegram is the primary host integration.

## Backend boundaries

FastAPI routes validate transport input and call domain services. Domain services own food identity, evidence, nutrition, safety, recipes, menu planning, shopping, family policy, and platform concerns. Persistence adapters own database access. Safety decisions must not be duplicated in frontend code.

## Frontend boundaries

The Next.js app renders API contracts, owns local interaction state, and preserves accessible responsive behavior. It should not infer an absent fact as zero or safe, nor reconstruct person-level safety from display labels.

## Migration authority

The physical evidence schema is custom-SQL-owned. Alembic is not the authority for these tables. Bootstrap ordering is the current dependency blocker and must be resolved before ORM adoption or data backfill. See [`06_DATA_ARCHITECTURE.md`](06_DATA_ARCHITECTURE.md) and [`18_CURRENT_STATE.md`](18_CURRENT_STATE.md).

## Operations references

- Repository quickstart: [`../../README.md`](../../README.md)
- Deployment and environment docs: [`../PRODUCTION_DEPLOY.md`](../PRODUCTION_DEPLOY.md)
- Recipe image implementation: [`../../apps/api/app/recipes/recipe_gold_v3_image_pipeline.py`](../../apps/api/app/recipes/recipe_gold_v3_image_pipeline.py)
