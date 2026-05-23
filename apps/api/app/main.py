import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.health import run_health_checks
from app.routers import (
    auth,
    care,
    families,
    menus,
    notifications,
    nutrition_profile,
    nutritionist as nutritionist_router,
    onboarding,
    pantry,
    recipes,
    shopping_categories,
    shopping_lists,
    subscriptions,
    telegram_bot,
    users,
)
from app.services.notification_scheduler import run_notification_scheduler
from app.telegram.bot import setup_menu_button, setup_webhook


async def _startup_telegram() -> None:
    await setup_menu_button()
    await setup_webhook()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    scheduler_task = asyncio.create_task(run_notification_scheduler())
    telegram_task = asyncio.create_task(_startup_telegram())
    try:
        yield
    finally:
        telegram_task.cancel()
        scheduler_task.cancel()
        for task in (telegram_task, scheduler_task):
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)

origins = [
    origin.strip()
    for origin in settings.backend_cors_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(care.router)
app.include_router(users.router)
app.include_router(onboarding.router)
app.include_router(nutrition_profile.router)
app.include_router(nutritionist_router.router)
app.include_router(families.router)
app.include_router(menus.router)
app.include_router(shopping_lists.router)
app.include_router(subscriptions.router)
app.include_router(shopping_categories.router)
app.include_router(notifications.router)
app.include_router(pantry.router)
app.include_router(recipes.router)
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
