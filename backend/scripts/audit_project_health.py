#!/usr/bin/env python3
"""PLANAM V1 — project-wide health audit (read-only).

Cross-domain sanity check used after the architecture consolidation and for
regular monitoring. NEVER writes the database; only reads + scans the repo.

Checks:
1. Food data   — suspicious recipe / menu / shopping amounts, deprecated
   shopping/pantry categories.
2. Profile     — users without a profile, profiles with empty/duplicated
   goals/allergies/diets, family members without nutrition, legacy<->new
   profile field drift.
3. Notifications — invalid quiet hours, invalid reminder times, fake/test
   telegram chat ids (999999999).
4. Subscription — invalid plan codes / statuses.
5. UI / routes  — deprecated route folders + legacy service files still present.

Usage (server):
    PYTHONPATH=/app:/app/apps/api python backend/scripts/audit_project_health.py

Reports: reports/project_health_audit.md / .json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
OUT_MD = REPORTS / "project_health_audit.md"
OUT_JSON = REPORTS / "project_health_audit.json"
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"

TEST_TELEGRAM_ID = 999999999

# Deprecated frontend route folders (relative to apps/web/app). Mirrors
# DEPRECATED_REDIRECT_ROUTES in apps/web/lib/planam/routes.ts.
DEPRECATED_ROUTE_DIRS = [
    "menu",
    "recipes",
    "pantry",
    "health",
    "nutritionist",
    "progress",
    "profile",
    "family",
    "notifications",
    "settings",
    "subscription",
    "home",
]

# Known legacy backend service files (kept for compatibility, frozen for V2).
LEGACY_SERVICE_FILES = [
    "apps/api/app/services/menu_ai_legacy.py",
    "apps/api/app/services/shopping_category_migration.py",
    "apps/api/app/services/admin_errors.py",
]

# ---- normalization helpers (degrade gracefully if app import unavailable) ----
try:
    sys.path.insert(0, str(ROOT / "apps" / "api"))
    from app.services.normalization import categories as norm_categories
    from app.services.normalization import ingredients as norm_ingredients
    from app.services.normalization import notifications as norm_notifications
    from app.services.normalization import profile as norm_profile
    from app.services.normalization import subscription as norm_subscription

    HAVE_NORM = True
except Exception as exc:  # pragma: no cover - fallback path
    HAVE_NORM = False
    _NORM_ERROR = str(exc)

_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")
_REDUNDANT_PIECE_RE = re.compile(r".+\s+(шт\.?|штук[аи]?)$", re.IGNORECASE)


def _is_suspicious_amount(amount: str | None) -> bool:
    raw = (amount or "").strip()
    if not raw:
        return False
    if HAVE_NORM:
        return norm_ingredients.is_suspicious_amount(raw)
    low = raw.lower()
    if "по вкусу" in low and low.endswith("шт"):
        return True
    return bool(_REDUNDANT_PIECE_RE.match(raw)) and not low.replace(" шт", "").strip().isdigit()


def _is_valid_time(value: str | None) -> bool:
    if HAVE_NORM:
        return norm_notifications.is_valid_time(value)
    return bool(value) and bool(_TIME_RE.match(value.strip()))


def _is_canonical_category(slug: str | None) -> bool:
    if HAVE_NORM:
        return norm_categories.is_valid_category(slug)
    return bool(slug)


def _has_dirty_list(values) -> bool:
    """True if a tag list contains empties or case-insensitive duplicates."""
    if not values:
        return False
    if HAVE_NORM:
        cleaned = norm_profile.normalize_string_list(values)
        return len(cleaned) != len([v for v in values if str(v).strip()]) or any(
            not str(v).strip() for v in values
        )
    seen, has_dirty = set(), False
    for v in values:
        s = str(v).strip()
        if not s:
            has_dirty = True
            continue
        if s.lower() in seen:
            has_dirty = True
        seen.add(s.lower())
    return has_dirty


def _is_valid_plan(code: str | None) -> bool:
    if HAVE_NORM:
        return norm_subscription.is_valid_plan_code(code)
    return bool(code)


def _is_valid_status(status: str | None) -> bool:
    if HAVE_NORM:
        return norm_subscription.is_valid_status(status)
    return bool(status)


def _load_json(value):
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return None
    return None


def _iter_menu_ingredients(menu_data):
    """Yield ingredient amount strings from a menu_data blob (best-effort)."""
    data = _load_json(menu_data)
    if not isinstance(data, dict):
        return
    containers = []
    if isinstance(data.get("days"), list):
        for day in data["days"]:
            if isinstance(day, dict):
                containers.extend(day.get("meals", []) or [])
    containers.extend(data.get("meals", []) or [])
    for meal in containers:
        if not isinstance(meal, dict):
            continue
        for ing in meal.get("ingredients", []) or []:
            if isinstance(ing, dict):
                yield ing.get("amount") or ing.get("display_amount") or ""


# --------------------------------- checks ----------------------------------


def _scalar(conn, sql: str) -> int:
    from sqlalchemy import text

    try:
        return int(conn.execute(text(sql)).scalar() or 0)
    except Exception:
        return 0


def run_db_checks(database_url: str) -> dict:
    from sqlalchemy import create_engine, text

    report: dict = {"db_connected": False, "errors": []}
    try:
        engine = create_engine(database_url)
        conn = engine.connect()
    except Exception as exc:
        report["errors"].append(f"db_connect: {exc}")
        return report

    report["db_connected"] = True
    with conn:
        # ---- Food ----
        food = {"recipe_suspicious": 0, "menu_suspicious": 0,
                "shopping_suspicious": 0, "pantry_suspicious": 0,
                "samples": []}
        try:
            for row in conn.execute(text("SELECT id, ingredients FROM recipes")).mappings():
                ings = _load_json(row["ingredients"]) or []
                for ing in ings if isinstance(ings, list) else []:
                    amount = ing.get("amount") if isinstance(ing, dict) else None
                    if _is_suspicious_amount(amount):
                        food["recipe_suspicious"] += 1
                        if len(food["samples"]) < 15:
                            food["samples"].append(f"recipe {row['id']}: {amount!r}")
        except Exception as exc:
            report["errors"].append(f"recipes: {exc}")
        try:
            for row in conn.execute(
                text("SELECT id, menu_data FROM family_menu_selections")
            ).mappings():
                for amount in _iter_menu_ingredients(row["menu_data"]):
                    if _is_suspicious_amount(amount):
                        food["menu_suspicious"] += 1
        except Exception as exc:
            report["errors"].append(f"menu: {exc}")
        try:
            for row in conn.execute(
                text("SELECT id, items FROM family_shopping_lists")
            ).mappings():
                items = _load_json(row["items"]) or []
                for it in items if isinstance(items, list) else []:
                    if not isinstance(it, dict):
                        continue
                    if _is_suspicious_amount(it.get("amount")):
                        food["shopping_suspicious"] += 1
                    elif not _is_canonical_category(it.get("category")):
                        food["shopping_suspicious"] += 1
        except Exception as exc:
            report["errors"].append(f"shopping: {exc}")
        try:
            for row in conn.execute(
                text("SELECT id, category, unit FROM family_pantry_items")
            ).mappings():
                if not _is_canonical_category(row["category"]):
                    food["pantry_suspicious"] += 1
        except Exception as exc:
            report["errors"].append(f"pantry: {exc}")
        report["food"] = food

        # ---- Profile ----
        profile = {}
        profile["users_without_profile"] = _scalar(
            conn,
            "SELECT count(*) FROM users u "
            "LEFT JOIN user_profiles p ON p.user_id = u.id "
            "WHERE p.id IS NULL AND coalesce(u.is_deleted, false) = false",
        )
        dirty_profiles = 0
        legacy_drift = 0
        try:
            for row in conn.execute(
                text(
                    "SELECT id, goals, diets, allergies, nutrition_goal "
                    "FROM user_profiles"
                )
            ).mappings():
                if (
                    _has_dirty_list(_load_json(row["goals"]))
                    or _has_dirty_list(_load_json(row["diets"]))
                    or _has_dirty_list(_load_json(row["allergies"]))
                ):
                    dirty_profiles += 1
                goals = _load_json(row["goals"]) or []
                if goals and not row["nutrition_goal"]:
                    legacy_drift += 1
        except Exception as exc:
            report["errors"].append(f"user_profiles: {exc}")
        profile["dirty_profiles"] = dirty_profiles
        profile["legacy_field_drift"] = legacy_drift
        members_without_nutrition = 0
        try:
            for row in conn.execute(
                text(
                    "SELECT id, is_virtual, nutrition_profile, goals "
                    "FROM family_members"
                )
            ).mappings():
                np = _load_json(row["nutrition_profile"]) or {}
                goals = _load_json(row["goals"]) or []
                if row["is_virtual"] and not np:
                    members_without_nutrition += 1
                elif not row["is_virtual"] and not goals and not np:
                    members_without_nutrition += 1
        except Exception as exc:
            report["errors"].append(f"family_members: {exc}")
        profile["members_without_nutrition"] = members_without_nutrition
        report["profile"] = profile

        # ---- Notifications ----
        notif = {"invalid_quiet_hours": 0, "invalid_reminder_times": 0,
                 "test_telegram_chats": 0}
        try:
            for row in conn.execute(
                text(
                    "SELECT quiet_hours_start, quiet_hours_end FROM care_settings"
                )
            ).mappings():
                s, e = row["quiet_hours_start"], row["quiet_hours_end"]
                if s is None and e is None:
                    continue
                if not _is_valid_time(s) or not _is_valid_time(e):
                    notif["invalid_quiet_hours"] += 1
        except Exception as exc:
            report["errors"].append(f"care_settings: {exc}")
        try:
            for row in conn.execute(
                text(
                    "SELECT buy_reminder_time, cook_reminder_time, "
                    "cook_breakfast_time, cook_lunch_time, cook_dinner_time "
                    "FROM user_notification_settings"
                )
            ).mappings():
                if any(
                    not _is_valid_time(row[k])
                    for k in (
                        "buy_reminder_time", "cook_reminder_time",
                        "cook_breakfast_time", "cook_lunch_time", "cook_dinner_time",
                    )
                ):
                    notif["invalid_reminder_times"] += 1
        except Exception as exc:
            report["errors"].append(f"notification_settings: {exc}")
        notif["test_telegram_chats"] = _scalar(
            conn, f"SELECT count(*) FROM users WHERE telegram_id = {TEST_TELEGRAM_ID}"
        )
        report["notifications"] = notif

        # ---- Subscription ----
        sub = {"invalid_plan": 0, "invalid_status": 0}
        try:
            for row in conn.execute(
                text("SELECT plan_code, status FROM user_subscriptions")
            ).mappings():
                if not _is_valid_plan(row["plan_code"]):
                    sub["invalid_plan"] += 1
                if not _is_valid_status(row["status"]):
                    sub["invalid_status"] += 1
        except Exception as exc:
            report["errors"].append(f"user_subscriptions: {exc}")
        report["subscription"] = sub

    return report


def run_static_checks() -> dict:
    app_dir = ROOT / "apps" / "web" / "app"
    deprecated_present = [
        d for d in DEPRECATED_ROUTE_DIRS if (app_dir / d).is_dir()
    ]
    legacy_services_present = [
        f for f in LEGACY_SERVICE_FILES if (ROOT / f).is_file()
    ]
    return {
        "deprecated_route_dirs_present": deprecated_present,
        "legacy_service_files_present": legacy_services_present,
    }


def build_metrics(db: dict, static: dict) -> dict:
    food = db.get("food", {})
    profile = db.get("profile", {})
    notif = db.get("notifications", {})
    sub = db.get("subscription", {})
    return {
        "suspicious_food_count": (
            food.get("recipe_suspicious", 0)
            + food.get("menu_suspicious", 0)
            + food.get("shopping_suspicious", 0)
            + food.get("pantry_suspicious", 0)
        ),
        "suspicious_profile_count": (
            profile.get("users_without_profile", 0)
            + profile.get("dirty_profiles", 0)
            + profile.get("legacy_field_drift", 0)
            + profile.get("members_without_nutrition", 0)
        ),
        "suspicious_notification_count": (
            notif.get("invalid_quiet_hours", 0)
            + notif.get("invalid_reminder_times", 0)
            + notif.get("test_telegram_chats", 0)
        ),
        "suspicious_subscription_count": (
            sub.get("invalid_plan", 0) + sub.get("invalid_status", 0)
        ),
        "deprecated_routes_count": len(static["deprecated_route_dirs_present"]),
        "legacy_services_count": len(static["legacy_service_files_present"]),
    }


def render_md(db: dict, static: dict, metrics: dict) -> str:
    lines: list[str] = []
    a = lines.append
    a("# PLANAM V1 — Project health audit (read-only)")
    a("")
    a(f"- normalization layer importable: **{HAVE_NORM}**")
    a(f"- database connected: **{db.get('db_connected', False)}**")
    a("")
    a("## Metrics")
    a("")
    a("| metric | value |")
    a("|--------|-------|")
    for key, value in metrics.items():
        a(f"| {key} | {value} |")
    a("")
    if db.get("db_connected"):
        food = db.get("food", {})
        a("## Food data")
        a("")
        a("| check | count |")
        a("|-------|-------|")
        a(f"| recipe suspicious amounts | {food.get('recipe_suspicious', 0)} |")
        a(f"| menu suspicious amounts | {food.get('menu_suspicious', 0)} |")
        a(f"| shopping suspicious items | {food.get('shopping_suspicious', 0)} |")
        a(f"| pantry suspicious categories | {food.get('pantry_suspicious', 0)} |")
        a("")
        if food.get("samples"):
            a("Samples:")
            a("")
            for s in food["samples"]:
                a(f"- `{s}`")
            a("")
        profile = db.get("profile", {})
        a("## Profile data")
        a("")
        a("| check | count |")
        a("|-------|-------|")
        a(f"| users without profile | {profile.get('users_without_profile', 0)} |")
        a(f"| profiles with empty/duplicated tags | {profile.get('dirty_profiles', 0)} |")
        a(f"| legacy<->new field drift | {profile.get('legacy_field_drift', 0)} |")
        a(f"| members without nutrition | {profile.get('members_without_nutrition', 0)} |")
        a("")
        notif = db.get("notifications", {})
        a("## Notifications")
        a("")
        a("| check | count |")
        a("|-------|-------|")
        a(f"| invalid quiet hours | {notif.get('invalid_quiet_hours', 0)} |")
        a(f"| invalid reminder times | {notif.get('invalid_reminder_times', 0)} |")
        a(f"| test telegram chats (999999999) | {notif.get('test_telegram_chats', 0)} |")
        a("")
        sub = db.get("subscription", {})
        a("## Subscription")
        a("")
        a("| check | count |")
        a("|-------|-------|")
        a(f"| invalid plan codes | {sub.get('invalid_plan', 0)} |")
        a(f"| invalid statuses | {sub.get('invalid_status', 0)} |")
        a("")
    else:
        a("> Database not reachable — only static checks were run. "
          "Run this on the server/VPS where Postgres is available.")
        a("")
    a("## UI / routes (static)")
    a("")
    a("Deprecated route folders still present (redirect-only, Legacy Cleanup V2):")
    a("")
    for d in static["deprecated_route_dirs_present"]:
        a(f"- `apps/web/app/{d}`")
    a("")
    a("Legacy service files still present (frozen, Legacy Cleanup V2):")
    a("")
    for f in static["legacy_service_files_present"]:
        a(f"- `{f}`")
    a("")
    if db.get("errors"):
        a("## Errors / skipped checks")
        a("")
        for e in db["errors"]:
            a(f"- {e}")
        a("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PLANAM project health audit (read-only)")
    parser.add_argument(
        "--database-url", default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    )
    parser.add_argument("--no-db", action="store_true", help="static checks only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db = {"db_connected": False, "errors": []} if args.no_db else run_db_checks(args.database_url)
    static = run_static_checks()
    metrics = build_metrics(db, static)

    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_md(db, static, metrics), encoding="utf-8")
    OUT_JSON.write_text(
        json.dumps(
            {"metrics": metrics, "db": db, "static": static,
             "normalization_importable": HAVE_NORM},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("PLANAM project health audit")
    for key, value in metrics.items():
        print(f"  {key} = {value}")
    print(f"MD:   {OUT_MD}")
    print(f"JSON: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
