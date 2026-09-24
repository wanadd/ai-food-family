from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class WriterEntry:
    writer_id: str
    file: str
    function: str
    surface: str
    domain: str
    mode: str
    tables: tuple[str, ...]
    authority_target: str
    pause_guard: str
    authority_guard: str
    async_guard: str
    side_effects: str
    status: str


# The Session before_flush/before_commit boundary is the canonical guard for
# every ORM writer. Keeping the inventory explicit makes coverage auditable.
WRITERS: tuple[WriterEntry, ...] = (
    WriterEntry("api_core", "app/routers/users.py;app/routers/families.py", "user/family mutations", "WEB_API", "CORE", "SYNC", ("users", "families", "family_members"), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "N/A", "database", "GUARDED"),
    WriterEntry("api_profile", "app/routers/onboarding.py;app/routers/nutrition_profile.py", "profile mutations", "WEB_API", "FOOD_PROFILE", "SYNC", ("user_profiles", "food_profiles"), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "N/A", "database", "GUARDED"),
    WriterEntry("api_targets", "app/routers/progress.py;app/services/progress.py", "nutrition target mutations", "WEB_API", "NUTRITION_TARGET", "SYNC", ("nutrition_targets", "nutrition_target_versions"), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "N/A", "database", "GUARDED"),
    WriterEntry("api_recipe", "app/routers/recipes.py;app/services/recipes", "recipe mutations", "WEB_API", "RECIPE", "SYNC", ("recipes", "recipes_v2"), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "N/A", "database", "GUARDED"),
    WriterEntry("api_planning", "app/routers/menus.py;app/routers/event_plans.py", "menu/plan mutations", "WEB_API", "PLANNING", "SYNC", ("family_menu_selections", "event_plans"), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "N/A", "database", "GUARDED"),
    WriterEntry("api_shopping", "app/routers/shopping_lists.py;app/services/shopping_list.py", "shopping mutations", "WEB_API", "SHOPPING", "SYNC", ("family_shopping_lists",), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "N/A", "database", "GUARDED"),
    WriterEntry("api_pantry", "app/routers/pantry.py;app/services/pantry.py", "pantry mutations", "WEB_API", "PANTRY", "SYNC", ("family_pantry_items",), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "N/A", "database", "GUARDED"),
    WriterEntry("api_cooking", "app/routers/leftovers.py;app/services/cooking", "cooking mutations", "WEB_API", "COOKING", "SYNC", ("cooking_batches", "meal_leftovers"), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "N/A", "database", "GUARDED"),
    WriterEntry("api_consumption", "app/routers/meal_consumption.py;app/services/meal_consumption.py", "consumption mutations", "WEB_API", "CONSUMPTION", "SYNC", ("meal_consumption_logs",), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "N/A", "database", "GUARDED"),
    WriterEntry("api_entitlement", "app/routers/subscriptions.py;app/services/subscription.py", "subscription mutations", "WEB_API", "ENTITLEMENT", "SYNC", ("user_subscriptions", "ama_wallets"), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "N/A", "external", "GUARDED"),
    WriterEntry("admin", "app/routers/admin.py;app/services/admin.py;app/services/admin_manage.py", "admin mutations", "ADMIN", "ADMIN", "SYNC", ("admin_actions", "users", "subscriptions"), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "N/A", "audit", "GUARDED"),
    WriterEntry("telegram_bot", "app/services/telegram_bot.py;app/services/bot_input.py", "bot mutations", "TELEGRAM_BOT", "CORE", "ASYNC", ("users", "family_members", "bot_sessions"), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "AsyncContext+SessionBoundary", "telegram", "GUARDED"),
    WriterEntry("scheduler", "app/services/notification_scheduler.py", "scheduled reminders", "SCHEDULED_JOB", "NOTIFICATION", "ASYNC", ("notification_settings", "care_notifications"), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "AsyncContext+SessionBoundary", "telegram", "GUARDED"),
    WriterEntry("menu_worker", "app/services/menu.py;app/services/menu_ai.py", "menu generation", "BACKGROUND_WORKER", "PLANNING", "ASYNC", ("menu_variants", "family_menu_selections"), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "AsyncContext+SessionBoundary", "AI", "GUARDED"),
    WriterEntry("receipt_worker", "app/services/receipt_ocr.py;app/services/bot_pending.py", "receipt proposals", "BACKGROUND_WORKER", "RECEIPT", "ASYNC", ("external_food_logs",), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "AsyncContext+SessionBoundary", "OCR", "GUARDED"),
    WriterEntry("outbox", "app/services/notification_scheduler.py", "notification delivery state", "OUTBOX", "OUTBOX", "ASYNC", ("outbox",), "LEGACY/V2", "SessionBoundary", "SessionBoundary", "AsyncContext+SessionBoundary", "external", "GUARDED"),
)


def writer_inventory() -> list[dict]:
    return [asdict(entry) for entry in WRITERS]


def writer_coverage() -> dict[str, int | float]:
    total = len(WRITERS)
    guarded = sum(entry.status == "GUARDED" for entry in WRITERS)
    return {"total": total, "guarded": guarded, "unclassified": 0, "unguarded": total - guarded, "coverage_percent": (guarded / total * 100) if total else 100.0}
