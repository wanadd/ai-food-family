#!/usr/bin/env python3
"""Seed audit personas for local UX audit harness.

Safe: only runs when PLANAM_AUDIT_MODE=true and environment=development.
Creates/updates audit_* users only (telegram_id 900_000_xxx).

Usage:
    cd C:\\Projects\\ai-food-family
    $env:PYTHONPATH="apps/api"
    $env:PLANAM_AUDIT_MODE="true"
    $env:environment="development"
    python backend/scripts/seed_audit_personas.py
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql://aifood:aifood@localhost:5432/aifood")

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.family import Family, FamilyMember, FamilyRole  # noqa: E402
from app.models.meal_consumption_log import MealConsumptionLog  # noqa: E402
from app.models.pantry import FamilyPantryItem  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.audit_auth import (  # noqa: E402
    AUDIT_PERSONA_TELEGRAM_IDS,
    get_or_create_audit_user,
    is_audit_mode_enabled,
)
from app.services.leftovers import create_or_get_cooking_batch  # noqa: E402
from app.services.subscription import (  # noqa: E402
    ensure_user_billing,
    seed_subscription_plans,
    select_plan_stub,
)
from app.schemas.leftovers import CookingBatchCreateIn  # noqa: E402
from app.services.app_scope import AppScope  # noqa: E402


def _guard() -> None:
    if not is_audit_mode_enabled():
        print("ERROR: PLANAM_AUDIT_MODE must be true and environment=development")
        sys.exit(1)
    if not settings.is_development:
        print("ERROR: refusing to seed in non-development environment")
        sys.exit(1)


def _user_by_persona(db, persona: str) -> User:
    user, _ = get_or_create_audit_user(db, persona)
    return user


def _set_trial(user: User, db) -> None:
    ensure_user_billing(db, user)


def _set_plan(user: User, db, plan_code: str) -> None:
    ensure_user_billing(db, user)
    select_plan_stub(db, user, plan_code)


def _clear_personal_pantry(db, user: User) -> None:
    db.query(FamilyPantryItem).filter(FamilyPantryItem.user_id == user.id).delete()
    db.commit()


def _add_pantry_items(db, user: User, *, family_id: int | None = None) -> None:
    today = date.today()
    items = [
        ("Молоко", "1 л", today + timedelta(days=2)),
        ("Яйца", "10 шт", today + timedelta(days=14)),
        ("Помидоры", "4 шт", today + timedelta(days=1)),
        ("Курица", "800 г", today + timedelta(days=3)),
    ]
    for name, qty, exp in items:
        db.add(
            FamilyPantryItem(
                user_id=user.id if family_id is None else None,
                family_id=family_id,
                name=name,
                quantity=qty.split()[0],
                unit=qty.split()[1] if " " in qty else "",
                expires_at=exp,
                added_by_user_id=user.id,
                source="manual",
            )
        )
    db.commit()


def _seed_consumption_marks(db, user: User) -> None:
    today = date.today()
    for meal_type, status in [
        ("breakfast", "eaten"),
        ("lunch", "skipped"),
        ("dinner", None),
    ]:
        if status is None:
            continue
        existing = (
            db.query(MealConsumptionLog)
            .filter(
                MealConsumptionLog.user_id == user.id,
                MealConsumptionLog.planned_date == today,
                MealConsumptionLog.meal_type == meal_type,
            )
            .one_or_none()
        )
        if existing:
            existing.status = status
        else:
            db.add(
                MealConsumptionLog(
                    user_id=user.id,
                    family_id=None,
                    meal_type=meal_type,
                    recipe_title=f"Audit {meal_type}",
                    status=status,
                    portion_multiplier=1.0,
                    planned_date=today,
                    day_index=4,
                )
            )
    db.add(
        MealConsumptionLog(
            user_id=user.id,
            family_id=None,
            meal_type="snack",
            recipe_title="Кофе с печеньем",
            status="ate_out",
            portion_multiplier=0.0,
            planned_date=today,
            day_index=4,
        )
    )
    db.commit()


def _seed_prepared_dish(db, user: User, *, family_id: int | None = None) -> None:
    scope = AppScope(
        mode="family" if family_id else "personal",
        user_id=user.id,
        family_id=family_id,
    )
    payload = CookingBatchCreateIn(
        family_id=family_id,
        recipe_id=None,
        recipe_title="Борщ домашний (audit)",
        menu_selection_id=None,
        day_index=4,
        meal_type="lunch",
        planned_date=date.today(),
        total_servings=4,
        serving_unit="порция",
        total_amount_value=2.0,
        total_amount_unit="л",
        remaining_amount_value=1.0,
        remaining_amount_unit="л",
    )
    create_or_get_cooking_batch(db, caller=user, scope=scope, payload=payload)


def _ensure_audit_family(db) -> tuple[Family, User, User]:
    admin = _user_by_persona(db, "audit_family_admin")
    adult = _user_by_persona(db, "audit_family_adult")
    child_user = _user_by_persona(db, "audit_family_child")

    admin_membership = (
        db.query(FamilyMember)
        .filter(FamilyMember.user_id == admin.id)
        .one_or_none()
    )
    if admin_membership is None:
        family = Family(name="Audit Family")
        db.add(family)
        db.flush()
        db.add(
            FamilyMember(
                family_id=family.id,
                user_id=admin.id,
                display_name="Admin",
                role=FamilyRole.ADMIN.value,
            )
        )
        db.add(
            FamilyMember(
                family_id=family.id,
                user_id=adult.id,
                display_name="Adult",
                role=FamilyRole.ADULT.value,
            )
        )
        child_membership = (
            db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == family.id,
                FamilyMember.user_id == child_user.id,
            )
            .one_or_none()
        )
        if child_membership is None:
            db.add(
                FamilyMember(
                    family_id=family.id,
                    user_id=child_user.id,
                    display_name="Ребёнок",
                    role=FamilyRole.CHILD.value,
                )
            )
        db.add(
            FamilyMember(
                family_id=family.id,
                user_id=None,
                display_name="Ребёнок",
                role=FamilyRole.CHILD.value,
                is_virtual=True,
                virtual_kind="child",
            )
        )
        db.commit()
        db.refresh(family)
    else:
        family = admin_membership.family

    _set_plan(admin, db, "family")
    _set_plan(adult, db, "family")
    _set_plan(child_user, db, "family")
    _clear_personal_pantry(db, admin)
    _add_pantry_items(db, admin, family_id=family.id)
    try:
        _seed_prepared_dish(db, admin, family_id=family.id)
    except Exception as exc:  # noqa: BLE001
        print(f"  warn: family prepared dish: {exc}")
    return family, admin, adult


def seed_all() -> dict[str, int]:
    _guard()
    db = SessionLocal()
    counts: dict[str, int] = {}
    try:
        seed_subscription_plans(db)

        # 4.1 New user — empty state
        _user_by_persona(db, "audit_new_user")
        _set_trial(_user_by_persona(db, "audit_new_user"), db)
        counts["audit_new_user"] = 1

        # 4.2 Personal day 5
        day5 = _user_by_persona(db, "audit_personal_day5")
        _set_plan(day5, db, "personal")
        _clear_personal_pantry(db, day5)
        _add_pantry_items(db, day5)
        _seed_consumption_marks(db, day5)
        try:
            _seed_prepared_dish(db, day5)
        except Exception as exc:  # noqa: BLE001
            print(f"  warn: personal prepared dish: {exc}")
        counts["audit_personal_day5"] = 1

        # 4.3–4.4 Family
        _ensure_audit_family(db)
        counts["audit_family_admin"] = 1
        counts["audit_family_adult"] = 1
        counts["audit_family_child"] = 1

        # 4.5 Athlete
        athlete = _user_by_persona(db, "audit_athlete")
        _set_plan(athlete, db, "pro")
        counts["audit_athlete"] = 1

        # 4.6 Strict diet
        strict = _user_by_persona(db, "audit_strict_diet")
        _set_plan(strict, db, "pro")
        counts["audit_strict_diet"] = 1

        # 4.7 Healthy eating
        healthy = _user_by_persona(db, "audit_healthy_eating")
        _set_plan(healthy, db, "personal")
        _add_pantry_items(db, healthy)
        counts["audit_healthy_eating"] = 1

        # 4.8 Tariff personas
        tariff_map = {
            "audit_start_trial": "trial",
            "audit_personal_plus": "personal",
            "audit_pair": "shared",
            "audit_family": "family",
            "audit_family_pro": "pro",
        }
        for persona, plan in tariff_map.items():
            u = _user_by_persona(db, persona)
            if plan == "trial":
                _set_trial(u, db)
            else:
                _set_plan(u, db, plan)
            counts[persona] = 1

        print(f"Seeded {len(AUDIT_PERSONA_TELEGRAM_IDS)} audit personas.")
        for persona, n in counts.items():
            print(f"  - {persona}: ok ({n})")
        return counts
    finally:
        db.close()


def main() -> int:
    seed_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
