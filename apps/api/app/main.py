import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.services import admin_errors
from app.database import init_db
from app.health import run_health_checks
from app.routers import (
    admin,
    auth,
    care,
    collections,
    families,
    meal_checkins,
    meal_consumption,
    meal_leftovers,
    leftovers,
    legal,
    health_intelligence,
    menus,
    notifications,
    nutrition_profile,
    nutritionist as nutritionist_router,
    onboarding,
    pantry,
    progress,
    event_plans,
    recipes,
    shopping_categories,
    shopping_lists,
    subscriptions,
    telegram_bot,
    users,
)
from app.services.notification_scheduler import run_notification_scheduler
from app.telegram.bot import setup_bot_commands, setup_menu_button, setup_webhook


async def _startup_telegram() -> None:
    if not settings.telegram_outbound_allowed:
        return
    await setup_menu_button()
    await setup_bot_commands()
    await setup_webhook()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    scheduler_task = (
        asyncio.create_task(run_notification_scheduler())
        if settings.notification_scheduler_allowed
        else None
    )
    telegram_task = (
        asyncio.create_task(_startup_telegram())
        if settings.telegram_outbound_allowed
        else None
    )
    try:
        yield
    finally:
        for task in (telegram_task, scheduler_task):
            if task is None:
                continue
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)


class AdminErrorLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            if response.status_code >= 500:
                admin_errors.record_error(
                    path=str(request.url.path),
                    status_code=response.status_code,
                )
            return response
        except Exception as exc:
            admin_errors.record_error(
                path=str(request.url.path),
                status_code=500,
                detail=str(exc),
            )
            raise


app.add_middleware(AdminErrorLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.effective_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(legal.router)
app.include_router(care.router)
app.include_router(collections.router)
app.include_router(users.router)
app.include_router(onboarding.router)
app.include_router(nutrition_profile.router)
app.include_router(nutritionist_router.router)
app.include_router(families.router)
app.include_router(menus.router)
app.include_router(meal_checkins.router)
app.include_router(meal_consumption.router)
app.include_router(meal_leftovers.router)
app.include_router(leftovers.router)
app.include_router(health_intelligence.router)
app.include_router(shopping_lists.router)
app.include_router(subscriptions.router)
app.include_router(shopping_categories.router)
app.include_router(notifications.router)
app.include_router(pantry.router)
app.include_router(progress.router)
app.include_router(recipes.router)
app.include_router(event_plans.router)
app.include_router(telegram_bot.router)
app.include_router(telegram_bot.bot_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "ПланАм API is running"}


@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
def health_check() -> dict:
    return run_health_checks()
