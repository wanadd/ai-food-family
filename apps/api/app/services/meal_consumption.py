"""Personal meal consumption logs (Phase 2A) — separate from legacy meal_checkins."""

from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.family import FamilyMember, FamilyRole
from app.models.meal_consumption_log import MealConsumptionLog
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.meal_consumption import (
    VALID_PORTIONS,
    VALID_STATUSES,
    MealConsumptionBulkIn,
    MealConsumptionEntryIn,
    MealConsumptionEntryOut,
)
from app.services import family as family_service
from app.services.meal_nutrition import _macros_from_calories


PERMISSION_DENIED = "Нет прав отмечать питание за этого участника"
FAMILY_ACCESS_DENIED = "Нет доступа к отметкам этой семьи"


def _caller_membership(db: Session, user: User) -> FamilyMember | None:
    return family_service.get_user_membership(db, user)


def _is_family_admin(membership: FamilyMember | None) -> bool:
    return membership is not None and membership.role == FamilyRole.ADMIN.value


def _is_virtual_member(member: FamilyMember) -> bool:
    return bool(member.is_virtual) and member.user_id is None


def can_log_for_member(
    db: Session,
    *,
    caller: User,
    family_id: int | None,
    target_user_id: int | None,
    target_family_member_id: int | None,
) -> bool:
    if family_id is None:
        if target_family_member_id is not None:
            return False
        return target_user_id == caller.id

    membership = _caller_membership(db, caller)
    if membership is None or membership.family_id != family_id:
        return False

    if target_family_member_id is not None:
        if not _is_family_admin(membership):
            return False
        member = db.get(FamilyMember, target_family_member_id)
        return (
            member is not None
            and member.family_id == family_id
            and _is_virtual_member(member)
        )

    if target_user_id is not None:
        return target_user_id == caller.id

    return False


def _resolve_subject(
    db: Session,
    *,
    family_id: int | None,
    entry: MealConsumptionEntryIn,
    caller: User,
) -> tuple[int | None, int | None]:
    user_id = entry.user_id
    family_member_id = entry.family_member_id

    if family_id is None:
        if family_member_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=PERMISSION_DENIED,
            )
        if user_id is not None and user_id != caller.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=PERMISSION_DENIED,
            )
        return caller.id, None

    if family_member_id is not None:
        member = db.get(FamilyMember, family_member_id)
        if member is None or member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=PERMISSION_DENIED,
            )
        if _is_virtual_member(member):
            user_id = None
        elif member.user_id == caller.id:
            user_id = caller.id
            family_member_id = None
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=PERMISSION_DENIED,
            )
    else:
        if user_id is None:
            user_id = caller.id
        elif user_id != caller.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=PERMISSION_DENIED,
            )
        family_member_id = None

    if not can_log_for_member(
        db,
        caller=caller,
        family_id=family_id,
        target_user_id=user_id,
        target_family_member_id=family_member_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=PERMISSION_DENIED,
        )

    return user_id, family_member_id


def _normalize_portion(status: str, portion: float) -> float:
    if status == "ate_out":
        return 0.0
    if portion not in VALID_PORTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимая порция: {portion}",
        )
    return portion


def _estimate_nutrition(
    db: Session,
    *,
    status: str,
    portion: float,
    recipe_id: int | None,
) -> tuple[float | None, float | None, float | None, float | None]:
    if status in ("skipped", "ate_out"):
        return None, None, None, None

    cal: float | None = None
    protein: float | None = None
    fat: float | None = None
    carbs: float | None = None

    if recipe_id:
        recipe = db.get(Recipe, recipe_id)
        if recipe and recipe.calories_per_serving:
            cal = float(recipe.calories_per_serving) * portion
            if recipe.protein_g and recipe.protein_g > 0:
                protein = float(recipe.protein_g) * portion
                fat = float(recipe.fat_g) * portion if recipe.fat_g else None
                carbs = float(recipe.carbs_g) * portion if recipe.carbs_g else None
            else:
                p, f, c = _macros_from_calories(cal)
                protein, fat, carbs = p, f, c

    return cal, protein, fat, carbs


def _find_existing(
    db: Session,
    *,
    family_id: int | None,
    user_id: int | None,
    family_member_id: int | None,
    menu_selection_id: int | None,
    day_index: int | None,
    meal_type: str,
    recipe_id: int | None,
    planned_date: date | None,
    recipe_title: str | None,
) -> MealConsumptionLog | None:
    q = db.query(MealConsumptionLog).filter(
        MealConsumptionLog.meal_type == meal_type,
    )
    if family_id is None:
        q = q.filter(MealConsumptionLog.family_id.is_(None))
    else:
        q = q.filter(MealConsumptionLog.family_id == family_id)

    if user_id is not None:
        q = q.filter(MealConsumptionLog.user_id == user_id)
    elif family_member_id is not None:
        q = q.filter(MealConsumptionLog.family_member_id == family_member_id)
    else:
        return None

    if menu_selection_id is not None and recipe_id is not None:
        q = q.filter(
            MealConsumptionLog.menu_selection_id == menu_selection_id,
            MealConsumptionLog.day_index == day_index,
            MealConsumptionLog.recipe_id == recipe_id,
        )
    else:
        q = q.filter(
            MealConsumptionLog.planned_date == planned_date,
            MealConsumptionLog.recipe_title == recipe_title,
        )

    return q.order_by(MealConsumptionLog.id.desc()).first()


def _entry_to_out(row: MealConsumptionLog) -> MealConsumptionEntryOut:
    return MealConsumptionEntryOut(
        id=row.id,
        user_id=row.user_id,
        family_member_id=row.family_member_id,
        meal_type=row.meal_type,
        recipe_id=row.recipe_id,
        recipe_title=row.recipe_title,
        status=row.status,
        portion_multiplier=row.portion_multiplier,
    )


def _validate_family_access(
    db: Session,
    caller: User,
    family_id: int | None,
) -> None:
    if family_id is None:
        return
    membership = _caller_membership(db, caller)
    if membership is None or membership.family_id != family_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=FAMILY_ACCESS_DENIED,
        )


def save_meal_consumption_logs(
    db: Session,
    *,
    caller: User,
    payload: MealConsumptionBulkIn,
) -> list[MealConsumptionLog]:
    _validate_family_access(db, caller, payload.family_id)

    saved: list[MealConsumptionLog] = []

    for entry in payload.entries:
        if entry.status not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый статус: {entry.status}",
            )

        user_id, family_member_id = _resolve_subject(
            db,
            family_id=payload.family_id,
            entry=entry,
            caller=caller,
        )
        portion = _normalize_portion(entry.status, entry.portion_multiplier)
        cal, protein, fat, carbs = _estimate_nutrition(
            db,
            status=entry.status,
            portion=portion,
            recipe_id=entry.recipe_id,
        )

        existing = _find_existing(
            db,
            family_id=payload.family_id,
            user_id=user_id,
            family_member_id=family_member_id,
            menu_selection_id=payload.menu_selection_id,
            day_index=payload.day_index,
            meal_type=entry.meal_type,
            recipe_id=entry.recipe_id,
            planned_date=payload.planned_date,
            recipe_title=entry.recipe_title,
        )

        if existing:
            existing.status = entry.status
            existing.portion_multiplier = portion
            existing.recipe_title = entry.recipe_title
            existing.logged_by_user_id = caller.id
            existing.note = entry.note
            existing.calories_estimated = cal
            existing.protein_estimated = protein
            existing.fat_estimated = fat
            existing.carbs_estimated = carbs
            existing.planned_date = payload.planned_date
            existing.menu_selection_id = payload.menu_selection_id
            existing.day_index = payload.day_index
            row = existing
        else:
            row = MealConsumptionLog(
                family_id=payload.family_id,
                user_id=user_id,
                family_member_id=family_member_id,
                logged_by_user_id=caller.id,
                menu_selection_id=payload.menu_selection_id,
                day_index=payload.day_index,
                planned_date=payload.planned_date,
                meal_type=entry.meal_type,
                recipe_id=entry.recipe_id,
                recipe_title=entry.recipe_title,
                status=entry.status,
                portion_multiplier=portion,
                note=entry.note,
                calories_estimated=cal,
                protein_estimated=protein,
                fat_estimated=fat,
                carbs_estimated=carbs,
            )
            db.add(row)

        saved.append(row)

    db.commit()
    for row in saved:
        db.refresh(row)
    return saved


def get_meal_consumption_logs(
    db: Session,
    *,
    caller: User,
    family_id: int | None = None,
    family_member_id: int | None = None,
    menu_selection_id: int | None = None,
    day_index: int | None = None,
    planned_date: date | None = None,
) -> list[MealConsumptionLog]:
    _validate_family_access(db, caller, family_id)

    q = db.query(MealConsumptionLog)
    if family_id is None:
        q = q.filter(MealConsumptionLog.family_id.is_(None))
    else:
        q = q.filter(MealConsumptionLog.family_id == family_id)

    if family_member_id is not None:
        membership = _caller_membership(db, caller)
        if not _is_family_admin(membership):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=PERMISSION_DENIED,
            )
        member = db.get(FamilyMember, family_member_id)
        if member is None or member.family_id != family_id or not _is_virtual_member(
            member
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=PERMISSION_DENIED,
            )
        q = q.filter(MealConsumptionLog.family_member_id == family_member_id)
    else:
        q = q.filter(MealConsumptionLog.user_id == caller.id)

    if menu_selection_id is not None:
        q = q.filter(MealConsumptionLog.menu_selection_id == menu_selection_id)
    if day_index is not None:
        q = q.filter(MealConsumptionLog.day_index == day_index)
    if planned_date is not None:
        q = q.filter(MealConsumptionLog.planned_date == planned_date)

    return q.order_by(MealConsumptionLog.id.asc()).all()


def logs_to_entries(rows: list[MealConsumptionLog]) -> list[MealConsumptionEntryOut]:
    return [_entry_to_out(row) for row in rows]
