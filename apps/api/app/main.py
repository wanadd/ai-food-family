import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.health import run_health_checks
from app.routers import auth, families, menus, notifications, onboarding, pantry, recipes, shopping_lists
from app.services.notification_scheduler import run_notification_scheduler
from app.telegram.bot import setup_menu_button


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    await setup_menu_button()
    scheduler_task = asyncio.create_task(run_notification_scheduler())
    try:
        yield
    finally:
        scheduler_task.cancel()
        try:
            await scheduler_task
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
app.include_router(onboarding.router)
app.include_router(families.router)
app.include_router(menus.router)
app.include_router(shopping_lists.router)
app.include_router(notifications.router)
app.include_router(pantry.router)
app.include_router(recipes.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "AI Food Family API is running"}


@app.get("/health")
def health_check() -> dict:
    return run_health_checks()
