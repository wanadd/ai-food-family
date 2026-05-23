from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.family import Family, FamilyMember
from app.models.progress import NutritionTarget, ProgressEntry, TrainingEntry
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.progress import (
    FamilyMemberProgressCard,
    NutritionTargetsResponse,
    NutritionTargetsUpdate,
    ProgressEntryCreate,
    ProgressEntryResponse,
    ProgressOverviewResponse,
    TrainingEntryCreate,
    TrainingEntryResponse,
)
from app.services import family as family_service
from app.services import family_member_nutrition as member_nutrition
from app.services import subscription as subscription_service
from app.services.app_scope import AppScope
from app.services.onboarding import get_or_create_profile

GOAL_LABELS: dict[str, str] = {
    "maintain": "Поддержание веса",
    "lose": "Похудение",
    "gain": "Набор массы",
    "healthy": "Здоровое питание",
    "sport": "Спорт",
    "kids": "Детское питание",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def user_has_pro(db: Session, user: User) -> bool:
    try:
        sub, plan, _ = subscription_service.get_current_subscription(db, user)
        if sub.plan_code == "pro":
            return True
        return bool((plan.features or {}).get("macros"))
    except Exception:
        return False


def require_pro(db: Session, user: User) -> None:
    if not user_has_pro(db, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступно в ПланАм PRO",
        )


def get_show_progress_to_family(profile: UserProfile) -> bool:
    pro_data = profile.pro_data or {}
    if "show_progress_to_family" in pro_data:
        return bool(pro_data["show_progress_to_family"])
    return True


def set_show_progress_to_family(
    db: Session, user: User, value: bool
) -> bool:
    profile = get_or_create_profile(db, user)
    data = dict(profile.pro_data or {})
    data["show_progress_to_family"] = value
    profile.pro_data = data
    db.commit()
    return value


def _scope_ids(user: User, scope: AppScope) -> tuple[int | None, int | None]:
    family_id = scope.family_id if scope.is_family else None
    return user.id, family_id


def create_progress_entry(
    db: Session,
    user: User,
    scope: AppScope,
    payload: ProgressEntryCreate,
) -> ProgressEntryResponse:
    require_pro(db, user)
    user_id, family_id = _scope_ids(user, scope)
    recorded_at = payload.recorded_at or _now()

    entry = ProgressEntry(
        user_id=user_id,
        family_id=family_id,
        weight_kg=payload.weight_kg,
        body_fat_percent=payload.body_fat_percent,
        waist_cm=payload.waist_cm,
        chest_cm=payload.chest_cm,
        hips_cm=payload.hips_cm,
        notes=payload.notes,
        recorded_at=recorded_at,
    )
    db.add(entry)

    if payload.weight_kg is not None:
        profile = get_or_create_profile(db, user)
        profile.weight_kg = payload.weight_kg

    db.commit()
    db.refresh(entry)
    return _entry_response(entry)


def get_latest_progress(
    db: Session,
    user: User,
    scope: AppScope,
    *,
    person_id: int | None = None,
) -> ProgressEntry | None:
    user_id, family_id = _scope_ids(user, scope)
    query = db.query(ProgressEntry)
    if person_id is not None:
        query = query.filter(ProgressEntry.person_id == person_id)
    else:
        query = query.filter(ProgressEntry.user_id == user_id)
        if family_id:
            query = query.filter(
                (ProgressEntry.family_id == family_id)
                | (ProgressEntry.family_id.is_(None))
            )
    return query.order_by(desc(ProgressEntry.recorded_at)).first()


def get_progress_history(
    db: Session,
    user: User,
    scope: AppScope,
    *,
    limit: int = 30,
) -> list[ProgressEntryResponse]:
    require_pro(db, user)
    user_id, family_id = _scope_ids(user, scope)
    query = db.query(ProgressEntry).filter(ProgressEntry.user_id == user_id)
    if family_id:
        query = query.filter(
            (ProgressEntry.family_id == family_id)
            | (ProgressEntry.family_id.is_(None))
        )
    rows = query.order_by(desc(ProgressEntry.recorded_at)).limit(limit).all()
    return [_entry_response(row) for row in rows]


def create_training_entry(
    db: Session,
    user: User,
    scope: AppScope,
    payload: TrainingEntryCreate,
) -> TrainingEntryResponse:
    require_pro(db, user)
    user_id, family_id = _scope_ids(user, scope)
    entry = TrainingEntry(
        user_id=user_id,
        family_id=family_id,
        training_type=payload.training_type.strip(),
        duration_minutes=payload.duration_minutes,
        intensity=payload.intensity,
        calories_burned=payload.calories_burned,
        notes=payload.notes,
        training_date=payload.training_date or date.today(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _training_response(entry)


def get_training_history(
    db: Session,
    user: User,
    scope: AppScope,
    *,
    limit: int = 30,
) -> list[TrainingEntryResponse]:
    require_pro(db, user)
    user_id, family_id = _scope_ids(user, scope)
    query = db.query(TrainingEntry).filter(TrainingEntry.user_id == user_id)
    if family_id:
        query = query.filter(
            (TrainingEntry.family_id == family_id)
            | (TrainingEntry.family_id.is_(None))
        )
    rows = query.order_by(desc(TrainingEntry.training_date)).limit(limit).all()
    return [_training_response(row) for row in rows]


def _estimate_targets(profile: UserProfile) -> NutritionTarget:
    weight = profile.weight_kg or 70.0
    goal = profile.nutrition_goal or "maintain"
    calories = int(weight * 24)
    protein_g = int(weight * 1.2)
    if goal == "lose":
        calories = int(calories * 0.88)
        protein_g = int(weight * 1.3)
    elif goal == "gain":
        calories = int(calories * 1.12)
        protein_g = int(weight * 1.5)
    elif goal == "sport":
        calories = int(calories * 1.15)
        protein_g = int(weight * 1.6)
    fat_g = int(calories * 0.28 / 9)
    carbs_g = int((calories - protein_g * 4 - fat_g * 9) / 4)
    water_ml = int(weight * 33)
    return NutritionTarget(
        calories_target=calories,
        protein_target_g=protein_g,
        fat_target_g=fat_g,
        carbs_target_g=max(carbs_g, 0),
        fiber_target_g=25,
        water_target_ml=water_ml,
        goal_type=goal,
    )


def get_nutrition_targets(
    db: Session, user: User, scope: AppScope
) -> NutritionTargetsResponse:
    user_id, family_id = _scope_ids(user, scope)
    row = (
        db.query(NutritionTarget)
        .filter(NutritionTarget.user_id == user_id)
        .order_by(desc(NutritionTarget.updated_at))
        .first()
    )
    if row is None:
        profile = get_or_create_profile(db, user)
        estimated = _estimate_targets(profile)
        row = NutritionTarget(
            user_id=user_id,
            family_id=family_id,
            calories_target=estimated.calories_target,
            protein_target_g=estimated.protein_target_g,
            fat_target_g=estimated.fat_target_g,
            carbs_target_g=estimated.carbs_target_g,
            fiber_target_g=estimated.fiber_target_g,
            water_target_ml=estimated.water_target_ml,
            goal_type=estimated.goal_type,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return _targets_response(row)


def update_nutrition_targets(
    db: Session,
    user: User,
    scope: AppScope,
    payload: NutritionTargetsUpdate,
) -> NutritionTargetsResponse:
    require_pro(db, user)
    user_id, family_id = _scope_ids(user, scope)
    row = (
        db.query(NutritionTarget)
        .filter(NutritionTarget.user_id == user_id)
        .order_by(desc(NutritionTarget.updated_at))
        .first()
    )
    if row is None:
        profile = get_or_create_profile(db, user)
        row = _estimate_targets(profile)
        row.user_id = user_id
        row.family_id = family_id
        db.add(row)

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)

    db.commit()
    db.refresh(row)
    return _targets_response(row)


def _weight_week_ago(
    db: Session, user_id: int, family_id: int | None
) -> float | None:
    week_ago = _now() - timedelta(days=7)
    row = (
        db.query(ProgressEntry)
        .filter(
            ProgressEntry.user_id == user_id,
            ProgressEntry.weight_kg.isnot(None),
            ProgressEntry.recorded_at <= week_ago,
        )
        .order_by(desc(ProgressEntry.recorded_at))
        .first()
    )
    if row and row.weight_kg is not None:
        return row.weight_kg
    return None


def calculate_goal_progress(
    goal_type: str | None,
    current_weight: float | None,
    start_weight: float | None,
    target_delta_kg: float | None = None,
) -> int | None:
    if current_weight is None:
        return None
    goal = goal_type or "maintain"
    if start_weight is None:
        start_weight = current_weight

    if goal == "lose":
        target = target_delta_kg if target_delta_kg else 3.0
        lost = start_weight - current_weight
        if target <= 0:
            return 0
        return min(100, max(0, int((lost / target) * 100)))
    if goal == "gain":
        target = target_delta_kg if target_delta_kg else 2.0
        gained = current_weight - start_weight
        if target <= 0:
            return 0
        return min(100, max(0, int((gained / target) * 100)))
    if goal == "sport":
        return min(100, max(0, 40 + int((current_weight - start_weight) * 5)))
    return min(100, max(0, 50 + int((start_weight - current_weight) * 10)))


def _member_status(goal: str | None, delta_week: float | None) -> str:
    if delta_week is None:
        return "stable"
    goal = goal or "maintain"
    if goal == "lose":
        if delta_week <= -0.2:
            return "improving"
        if delta_week >= 0.3:
            return "attention"
        return "stable"
    if goal == "gain":
        if delta_week >= 0.2:
            return "improving"
        if delta_week <= -0.3:
            return "attention"
        return "stable"
    if abs(delta_week) < 0.3:
        return "stable"
    return "improving" if delta_week < 0 else "attention"


def _build_pro_recommendation(
    goal: str | None,
    delta_week: float | None,
    trainings_week: int,
) -> str:
    goal = goal or "maintain"
    parts: list[str] = []
    if goal == "lose" and delta_week is not None:
        if delta_week < -0.2:
            parts.append("Вес снижается в хорошем темпе — сохраняйте белок и режим сна.")
        elif delta_week > 0.2:
            parts.append("За неделю вес немного вырос — проверьте порции и перекусы.")
    elif goal == "gain" and delta_week is not None and delta_week < 0.1:
        parts.append("Для набора массы добавьте калорийности к ужину и белка после тренировки.")
    if trainings_week < 2 and goal == "sport":
        parts.append("Добавьте 1–2 тренировки на неделю — это поддержит цель.")
    if not parts:
        parts.append("Продолжайте отмечать вес и тренировки — ПланАм точнее подстроит план.")
    return " ".join(parts)


def _family_progress_cards(
    db: Session, viewer: User, family_id: int
) -> list[FamilyMemberProgressCard]:
    family = db.query(Family).filter(Family.id == family_id).one_or_none()
    if family is None:
        return []

    cards: list[FamilyMemberProgressCard] = []
    for member in family.members:
        is_you = member.user_id == viewer.id
        if member.user_id:
            member_user = db.query(User).filter(User.id == member.user_id).one_or_none()
            if member_user and member_user.id != viewer.id:
                profile = get_or_create_profile(db, member_user)
                if not get_show_progress_to_family(profile):
                    cards.append(
                        FamilyMemberProgressCard(
                            member_id=member.id,
                            name=member.display_name,
                            goal_label=None,
                            progress_summary="Прогресс скрыт пользователем",
                            status="hidden",
                            is_you=False,
                        )
                    )
                    continue
                latest = (
                    db.query(ProgressEntry)
                    .filter(ProgressEntry.user_id == member_user.id)
                    .order_by(desc(ProgressEntry.recorded_at))
                    .first()
                )
                goal = profile.nutrition_goal
                week_ago_w = _weight_week_ago(db, member_user.id, family_id)
                current = latest.weight_kg if latest else profile.weight_kg
                delta = None
                if current is not None and week_ago_w is not None:
                    delta = round(current - week_ago_w, 1)
                status = _member_status(goal, delta)
                summary = GOAL_LABELS.get(goal or "", "Цель не задана")
                if delta is not None:
                    sign = "+" if delta > 0 else ""
                    summary = f"{summary} · {sign}{delta} кг за неделю"
                cards.append(
                    FamilyMemberProgressCard(
                        member_id=member.id,
                        name=member.display_name,
                        goal_label=GOAL_LABELS.get(goal or "", None),
                        progress_summary=summary,
                        status=status,  # type: ignore[arg-type]
                        is_you=is_you,
                    )
                )
                continue

        goal_label = member_nutrition.nutrition_goal_label_for_member(db, member)
        cards.append(
            FamilyMemberProgressCard(
                member_id=member.id,
                name=member.display_name,
                goal_label=goal_label,
                progress_summary="Нет данных о прогрессе",
                status="stable",
                is_you=is_you,
            )
        )
    return cards


def get_progress_overview(
    db: Session, user: User, scope: AppScope
) -> ProgressOverviewResponse:
    profile = get_or_create_profile(db, user)
    is_pro = user_has_pro(db, user)
    goal_type = profile.nutrition_goal
    goal_label = GOAL_LABELS.get(goal_type or "", None)

    latest = get_latest_progress(db, user, scope)
    current_weight = None
    if latest and latest.weight_kg is not None:
        current_weight = latest.weight_kg
    elif profile.weight_kg is not None:
        current_weight = profile.weight_kg

    user_id, family_id = _scope_ids(user, scope)
    week_ago_w = _weight_week_ago(db, user_id, family_id) if user_id else None
    weight_change = None
    if current_weight is not None and week_ago_w is not None:
        weight_change = round(current_weight - week_ago_w, 1)

    first_entry = None
    if user_id:
        first_entry = (
            db.query(ProgressEntry)
            .filter(
                ProgressEntry.user_id == user_id,
                ProgressEntry.weight_kg.isnot(None),
            )
            .order_by(ProgressEntry.recorded_at.asc())
            .first()
        )
    start_weight = first_entry.weight_kg if first_entry else current_weight
    goal_pct = None
    trainings_week = 0
    minutes_week = 0
    targets = None
    recommendation = None
    family_progress: list[FamilyMemberProgressCard] = []

    if is_pro:
        goal_pct = calculate_goal_progress(goal_type, current_weight, start_weight)
        targets = get_nutrition_targets(db, user, scope)
        week_start = date.today() - timedelta(days=7)
        if user_id:
            training_rows = (
                db.query(TrainingEntry)
                .filter(
                    TrainingEntry.user_id == user_id,
                    TrainingEntry.training_date >= week_start,
                )
                .all()
            )
            trainings_week = len(training_rows)
            minutes_week = sum(r.duration_minutes or 0 for r in training_rows)
        recommendation = _build_pro_recommendation(
            goal_type, weight_change, trainings_week
        )
        if is_pro and scope.is_family and family_id:
            family_progress = _family_progress_cards(db, user, family_id)

    return ProgressOverviewResponse(
        is_pro=is_pro,
        goal_label=goal_label,
        goal_type=goal_type,
        current_weight_kg=current_weight,
        weight_change_week_kg=weight_change,
        goal_progress_percent=goal_pct,
        targets=targets,
        trainings_this_week=trainings_week,
        training_minutes_week=minutes_week,
        show_progress_to_family=get_show_progress_to_family(profile),
        family_progress=family_progress,
        pro_recommendation=recommendation if is_pro else None,
        latest_entry=_entry_response(latest) if latest and is_pro else None,
    )


def _entry_response(entry: ProgressEntry) -> ProgressEntryResponse:
    return ProgressEntryResponse(
        id=entry.id,
        weight_kg=entry.weight_kg,
        body_fat_percent=entry.body_fat_percent,
        waist_cm=entry.waist_cm,
        chest_cm=entry.chest_cm,
        hips_cm=entry.hips_cm,
        notes=entry.notes,
        recorded_at=entry.recorded_at,
    )


def _training_response(entry: TrainingEntry) -> TrainingEntryResponse:
    return TrainingEntryResponse(
        id=entry.id,
        training_type=entry.training_type,
        duration_minutes=entry.duration_minutes,
        intensity=entry.intensity,
        calories_burned=entry.calories_burned,
        notes=entry.notes,
        training_date=entry.training_date,
    )


def _targets_response(row: NutritionTarget) -> NutritionTargetsResponse:
    return NutritionTargetsResponse(
        calories_target=row.calories_target,
        protein_target_g=row.protein_target_g,
        fat_target_g=row.fat_target_g,
        carbs_target_g=row.carbs_target_g,
        fiber_target_g=row.fiber_target_g,
        water_target_ml=row.water_target_ml,
        goal_type=row.goal_type,
    )
