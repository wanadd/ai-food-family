#!/usr/bin/env python3
"""Production-safe single-user reset to first-launch Telegram Mini App state.

SAFETY GUARANTEES
-----------------
* Never deletes global recipes, recipe_scenarios, recipe_tags, subscription_plans,
  or any data belonging to other users.
* Never auto-executes: requires --dry-run (preview) or --confirm (interactive prompt).
* All writes run inside a single transaction; any error rolls back everything.
* If the user belongs to a multi-member family only the membership is removed;
  shared family data stays intact for the remaining members.
* If the family has only this one real member (no other non-virtual users) the
  entire family record is removed so no orphaned family data is left behind.

USAGE
-----
    # Preview (read-only, no changes)
    python scripts/reset_user.py --telegram-id 123456789 --dry-run

    # Execute (shows the same preview first, then asks for confirmation)
    python scripts/reset_user.py --telegram-id 123456789 --confirm

    # By internal DB user_id
    python scripts/reset_user.py --user-id 42 --dry-run

ENVIRONMENT
-----------
    Set DATABASE_URL before running, e.g.:
        export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
        python scripts/reset_user.py --telegram-id 123456789 --dry-run

    Or inline:
        DATABASE_URL="..." python scripts/reset_user.py ...
"""

from __future__ import annotations

import argparse
import os
import sys
from textwrap import dedent

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API_ROOT = os.path.join(ROOT, "apps", "api")
sys.path.insert(0, API_ROOT)

from sqlalchemy import create_engine, text  # noqa: E402

# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def _get_engine():
    url = DATABASE_URL
    if not url:
        print("ERROR: DATABASE_URL environment variable is not set.", file=sys.stderr)
        print("       Example: export DATABASE_URL=postgresql://user:pass@host/db", file=sys.stderr)
        sys.exit(1)
    return create_engine(url, pool_pre_ping=True)


# ---------------------------------------------------------------------------
# Tables cleared via CASCADE when users row is deleted
# (listed here only for dry-run counting / documentation)
# ---------------------------------------------------------------------------

_CASCADE_TABLES: list[tuple[str, str, str]] = [
    # (table,                        filter_col,    description)
    ("user_profiles",               "user_id",     "Onboarding / profile data (1:1)"),
    ("user_preferences",            "user_id",     "Active mode preference (1:1)"),
    ("user_notification_settings",  "user_id",     "Notification config (1:1)"),
    ("care_settings",               "user_id",     "Nutritionist / care toggles (1:1)"),
    ("care_notifications",          "user_id",     "Pending care notifications"),
    ("care_events",                 "user_id",     "Care event log"),
    ("recipe_favorites",            "user_id",     "Starred recipes"),
    ("recipe_ratings",              "user_id",     "Ratings & cooked counters"),
    ("recipe_explanations",         "user_id",     "AI explanation cache (personal)"),
    ("family_menu_selections",      "user_id",     "Generated menus"),
    ("family_pantry_items",         "user_id",     "Personal pantry items"),
    ("family_shopping_lists",       "user_id",     "Personal shopping list"),
    ("meal_leftovers",              "user_id",     "Meal leftover records"),
    ("meal_checkins",               "user_id",     "Meal check-in history"),
    ("water_intake_logs",           "user_id",     "Water intake log"),
    ("event_plans",                 "user_id",     "Event / holiday meal plans"),
    ("deferred_nutrition_advice",   "user_id",     "Deferred nutritionist advice"),
    ("progress_entries",            "user_id",     "Weight / body measurements"),
    ("training_entries",            "user_id",     "Training log"),
    ("nutrition_targets",           "user_id",     "Calorie / macro targets"),
    ("user_subscriptions",          "user_id",     "Subscription & billing state"),
    ("ama_wallets",                 "user_id",     "AMA token wallet (+ transactions cascade)"),
    ("ai_usage_logs",               "user_id",     "AI usage / cost log"),
    ("admin_sessions",              "user_id",     "Admin session tokens"),
]

# Tables handled explicitly BEFORE the users row is deleted
_EXPLICIT_TABLES: list[tuple[str, str, str]] = [
    ("telegram_bot_sessions",  "telegram_id",  "Bot FSM state (keyed by telegram_id, no FK)"),
    ("recipe_history",         "user_id",       "Personal cooking history (SET NULL — deleted explicitly)"),
    ("recipe_collections",     "owner_user_id", "Personal collections (non-system, collection_recipes cascade)"),
]

# ---------------------------------------------------------------------------
# Helpers: counting
# ---------------------------------------------------------------------------

def _count(conn, table: str, col: str, value: int) -> int:
    row = conn.execute(
        text(f"SELECT COUNT(*) FROM {table} WHERE {col} = :v"),
        {"v": value},
    ).fetchone()
    return int(row[0]) if row else 0


def _count_ama_transactions(conn, user_id: int) -> int:
    row = conn.execute(
        text("""
            SELECT COUNT(*)
            FROM ama_transactions t
            JOIN ama_wallets w ON w.id = t.wallet_id
            WHERE w.user_id = :uid
        """),
        {"uid": user_id},
    ).fetchone()
    return int(row[0]) if row else 0


# ---------------------------------------------------------------------------
# Helpers: family
# ---------------------------------------------------------------------------

def _get_family_membership(conn, user_id: int):
    """Return (family_member_id, family_id, real_member_count) or None."""
    row = conn.execute(
        text("SELECT id, family_id FROM family_members WHERE user_id = :uid LIMIT 1"),
        {"uid": user_id},
    ).fetchone()
    if not row:
        return None
    fm_id, family_id = int(row[0]), int(row[1])
    count_row = conn.execute(
        text("""
            SELECT COUNT(*)
            FROM family_members
            WHERE family_id = :fid AND user_id IS NOT NULL
        """),
        {"fid": family_id},
    ).fetchone()
    real_count = int(count_row[0]) if count_row else 0
    return fm_id, family_id, real_count


def _count_family_data(conn, family_id: int) -> list[tuple[str, int]]:
    """Rows that cascade-delete when the family is deleted."""
    checks = [
        ("family_members",              "family_id"),
        ("family_menu_selections",      "family_id"),
        ("family_shopping_lists",       "family_id"),
        ("family_pantry_items",         "family_id"),
        ("family_recipe_preferences",   "family_id"),
        ("meal_leftovers",              "family_id"),
        ("meal_checkins",               "family_id"),
        ("meal_eating_schedules",       "family_id"),
        ("recipe_collections",          "owner_family_id"),
        ("recipe_history",              "family_id"),
        ("ama_wallets",                 "family_id"),
    ]
    result = []
    for tbl, col in checks:
        cnt = _count(conn, tbl, col, family_id)
        if cnt:
            result.append((tbl, cnt))
    return result


# ---------------------------------------------------------------------------
# Helpers: user lookup
# ---------------------------------------------------------------------------

def _lookup_user(conn, telegram_id: int | None, user_id: int | None):
    if telegram_id is not None:
        row = conn.execute(
            text("""
                SELECT id, telegram_id, first_name, username, is_deleted, deleted_at
                FROM users WHERE telegram_id = :v
            """),
            {"v": telegram_id},
        ).fetchone()
    else:
        row = conn.execute(
            text("""
                SELECT id, telegram_id, first_name, username, is_deleted, deleted_at
                FROM users WHERE id = :v
            """),
            {"v": user_id},
        ).fetchone()
    return row


# ---------------------------------------------------------------------------
# Dry-run report
# ---------------------------------------------------------------------------

_SEP = "=" * 68
_LINE = "-" * 68


def _dry_run_report(conn, user_row) -> int:
    """Print a detailed preview; return estimated total rows affected."""
    uid        = int(user_row[0])
    tid        = int(user_row[1])
    name       = user_row[2] or user_row[3] or "(unknown)"
    is_deleted = bool(user_row[4])
    deleted_at = user_row[5]

    print()
    print(_SEP)
    print("  DRY RUN — User reset preview (NO CHANGES MADE)")
    print(_SEP)
    print(f"  user_id      : {uid}")
    print(f"  telegram_id  : {tid}")
    print(f"  name         : {name}")
    if is_deleted:
        print(f"  ⚠  already soft-deleted at {deleted_at} (reset still possible)")
    print()

    total = 0

    # --- Explicit pre-delete steps ---
    print("STEP 1 — Explicit deletes (before user row removal)")
    print(_LINE)

    bot_cnt = _count(conn, "telegram_bot_sessions", "telegram_id", tid)
    _report_row("telegram_bot_sessions", bot_cnt, "Bot FSM state")
    total += bot_cnt

    hist_cnt = _count(conn, "recipe_history", "user_id", uid)
    _report_row("recipe_history", hist_cnt, "Personal cooking history")
    total += hist_cnt

    col_cnt = _count_personal_collections(conn, uid)
    _report_row("recipe_collections (personal)", col_cnt, "Personal collections")
    total += col_cnt

    # --- Family ---
    print()
    print("STEP 2 — Family membership")
    print(_LINE)
    membership = _get_family_membership(conn, uid)
    if membership:
        fm_id, family_id, real_count = membership
        print(f"  family_id        : {family_id}")
        print(f"  family_member_id : {fm_id}")
        print(f"  real members     : {real_count}")
        if real_count <= 1:
            print("  ACTION           : SOLO family → entire family will be DELETED")
            fam_rows = _count_family_data(conn, family_id)
            for tbl, cnt in fam_rows:
                print(f"    ↳ {tbl:<42} {cnt:>5} rows")
                total += cnt
        else:
            print(f"  ACTION           : SHARED family ({real_count} real members)")
            print(f"    ↳ only family_member row id={fm_id} will be removed")
            print(f"    ↳ shared family data is NOT touched")
    else:
        print("  No family membership found")

    # --- CASCADE from users ---
    print()
    print("STEP 3 — Cascade-deleted when users row is removed")
    print(_LINE)
    for tbl, col, desc in _CASCADE_TABLES:
        cnt = _count(conn, tbl, col, uid)
        if tbl == "ama_wallets" and cnt:
            tx_cnt = _count_ama_transactions(conn, uid)
            _report_row(tbl, cnt, desc + f" (+{tx_cnt} transactions)")
            total += cnt + tx_cnt
        else:
            _report_row(tbl, cnt, desc)
            total += cnt

    # --- users row itself ---
    print()
    print("STEP 4 — User row deleted")
    print(_LINE)
    _report_row("users", 1, "The user record itself")
    total += 1

    # --- Protected tables ---
    print()
    print("PROTECTED (never touched)")
    print(_LINE)
    protected = [
        "recipes",
        "recipe_tags / recipe_ingredients / recipe_steps / recipe_allergens",
        "recipe_scenarios",
        "recipe_import_jobs",
        "subscription_plans",
        "shopping_categories (is_system=true)",
        "admin_actions / admin_error_logs / admin_login_attempts",
        "All other users' data",
    ]
    for item in protected:
        print(f"  ✓  {item}")

    print()
    print(f"  ESTIMATED TOTAL ROWS AFFECTED: {total}")
    print()
    print("  To execute: re-run with --confirm instead of --dry-run")
    print(_SEP)
    print()
    return total


def _report_row(label: str, count: int, desc: str = "") -> None:
    if count == 0:
        return
    suffix = f"  [{desc}]" if desc else ""
    print(f"  {label:<48} {count:>5} rows{suffix}")


def _count_personal_collections(conn, user_id: int) -> int:
    row = conn.execute(
        text("""
            SELECT COUNT(*)
            FROM recipe_collections
            WHERE owner_user_id = :uid AND visibility != 'system'
        """),
        {"uid": user_id},
    ).fetchone()
    return int(row[0]) if row else 0


# ---------------------------------------------------------------------------
# Execution (inside a transaction)
# ---------------------------------------------------------------------------

def _execute_reset(conn, user_row) -> None:
    uid  = int(user_row[0])
    tid  = int(user_row[1])
    name = user_row[2] or user_row[3] or "(unknown)"

    print()
    print(_SEP)
    print(f"  EXECUTING RESET  user_id={uid}  telegram_id={tid}  name={name}")
    print(_SEP)

    # 1. Telegram bot session (no FK to users — must delete manually)
    r = conn.execute(
        text("DELETE FROM telegram_bot_sessions WHERE telegram_id = :tid"),
        {"tid": tid},
    )
    _ok("telegram_bot_sessions", r.rowcount, "bot FSM state cleared")

    # 2. Recipe history (FK is SET NULL — delete explicitly to clear history)
    r = conn.execute(
        text("DELETE FROM recipe_history WHERE user_id = :uid"),
        {"uid": uid},
    )
    _ok("recipe_history", r.rowcount, "personal cooking history cleared")

    # 3. Personal recipe collections (visibility != 'system')
    #    collection_recipes cascade automatically
    r = conn.execute(
        text("""
            DELETE FROM recipe_collections
            WHERE owner_user_id = :uid AND visibility != 'system'
        """),
        {"uid": uid},
    )
    _ok("recipe_collections", r.rowcount, "personal collections + items cascade-deleted")

    # 4. Family membership
    membership = _get_family_membership(conn, uid)
    if membership:
        fm_id, family_id, real_count = membership
        if real_count <= 1:
            # Solo family: delete the family; everything cascade-deletes
            r = conn.execute(
                text("DELETE FROM families WHERE id = :fid"),
                {"fid": family_id},
            )
            _ok("families", r.rowcount, f"solo family_id={family_id} deleted (all family data cascades)")
        else:
            # Shared family: remove only this user's membership
            # meal_eating_schedules and family_recipe_preferences cascade from family_member
            r = conn.execute(
                text("DELETE FROM family_members WHERE id = :fm_id"),
                {"fm_id": fm_id},
            )
            _ok(
                "family_members",
                r.rowcount,
                f"membership removed; family_id={family_id} kept ({real_count - 1} members remain)",
            )
    else:
        print("  --  No family membership found — skipping family step")

    # 5. Delete the user row
    #    ON DELETE CASCADE covers: user_profiles, user_preferences,
    #    user_notification_settings, care_*, recipe_favorites, recipe_ratings,
    #    recipe_explanations, family_menu_selections, family_shopping_lists (personal),
    #    family_pantry_items (personal), meal_leftovers (personal), meal_checkins,
    #    water_intake_logs, event_plans, deferred_nutrition_advice, progress_entries,
    #    training_entries, nutrition_targets, user_subscriptions, ama_wallets →
    #    ama_transactions, ai_usage_logs, admin_sessions,
    #    family_invites (invited_by_user_id CASCADE)
    #
    #    ON DELETE SET NULL (rows remain, user_id becomes NULL):
    #    family_members.user_id (if not already deleted above),
    #    family_invites.invited_user_id, collection_recipes.added_by_user_id,
    #    family_pantry_items.added_by_user_id, meal_leftovers.added_by_user_id,
    #    admin_actions.admin_user_id, admin_error_logs.user_id
    r = conn.execute(
        text("DELETE FROM users WHERE id = :uid"),
        {"uid": uid},
    )
    _ok("users", r.rowcount, "user row deleted — CASCADE cleaned all dependent data")

    print()
    print(f"  RESET COMPLETE for user_id={uid} (telegram_id={tid})")
    print("  The user can now re-register and go through onboarding from scratch.")
    print(_SEP)
    print()


def _ok(table: str, rowcount: int, note: str) -> None:
    print(f"  [OK] {table:<48} {rowcount:>4} rows  — {note}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="reset_user.py",
        description="Reset a single user to first-launch state (production-safe).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""\
            Examples:
              # Safe preview — no writes to the database
              python scripts/reset_user.py --telegram-id 123456789 --dry-run

              # Full reset with interactive confirmation prompt
              python scripts/reset_user.py --telegram-id 123456789 --confirm

              # Using internal user_id instead
              python scripts/reset_user.py --user-id 42 --dry-run
              python scripts/reset_user.py --user-id 42 --confirm

            Set DATABASE_URL before running:
              export DATABASE_URL="postgresql://user:pass@localhost:5432/food_family"
        """),
    )

    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument("--telegram-id", type=int, metavar="TID",
                          help="User's Telegram ID (bigint)")
    id_group.add_argument("--user-id", type=int, metavar="UID",
                          help="Internal database users.id")

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--dry-run", action="store_true",
                            help="Show what would be deleted — no changes made")
    mode_group.add_argument("--confirm", action="store_true",
                            help="Perform the reset (shows preview, then asks for 'YES')")

    args = parser.parse_args()

    engine = _get_engine()

    with engine.connect() as conn:
        user_row = _lookup_user(
            conn,
            telegram_id=args.telegram_id,
            user_id=args.user_id,
        )
        if not user_row:
            ident = (
                f"telegram_id={args.telegram_id}"
                if args.telegram_id is not None
                else f"user_id={args.user_id}"
            )
            print(f"ERROR: User not found ({ident})", file=sys.stderr)
            sys.exit(1)

        if args.dry_run:
            _dry_run_report(conn, user_row)
            return

        # --confirm: show preview, require explicit "YES"
        _dry_run_report(conn, user_row)

        uid = int(user_row[0])
        tid = int(user_row[1])
        print(f"WARNING: This will PERMANENTLY DELETE all data for")
        print(f"         user_id={uid}  telegram_id={tid}")
        print()
        print("This action is IRREVERSIBLE. Make a database backup first.")
        print()
        answer = input("Type  YES  (all caps) to confirm: ").strip()
        if answer != "YES":
            print("\nAborted — no changes were made.")
            sys.exit(0)

        with conn.begin():
            _execute_reset(conn, user_row)


if __name__ == "__main__":
    main()
