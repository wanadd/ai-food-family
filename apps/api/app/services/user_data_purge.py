"""Purge user-owned app data (keep or remove user row)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.admin import AdminSession
from app.models.care import CareEvent, CareNotification, CareSettings
from app.models.cooking_batch import CookingBatch, CookingBatchEvent
from app.models.deferred_advice import DeferredNutritionAdvice
from app.models.event_plan import EventPlan
from app.models.external_food_log import ExternalFoodLog
from app.models.family import FamilyMember
from app.models.family_invite import FamilyInvite
from app.models.meal_checkin import MealCheckin
from app.models.meal_consumption_log import MealConsumptionLog
from app.models.meal_consumption_reminder_event import MealConsumptionReminderEvent
from app.models.meal_leftover import MealLeftover
from app.models.menu_selection import FamilyMenuSelection
from app.models.notification_settings import UserNotificationSettings
from app.models.pantry import FamilyPantryItem
from app.models.progress import NutritionTarget, ProgressEntry, TrainingEntry
from app.models.recipe import Recipe, RecipeFavorite
from app.models.shopping_category import ShoppingCategory
from app.models.shopping_list import FamilyShoppingList
from app.models.subscription import AiUsageLog, AmaTransaction, AmaWallet, UserSubscription
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.models.user_profile import UserProfile
from app.models.water_intake import WaterIntakeLog


def _delete_by_user_id(db: Session, model: Any, user_id: int, *, column: str = "user_id") -> int:
    return (
        db.query(model)
        .filter(getattr(model, column) == user_id)
        .delete(synchronize_session=False)
    )


def purge_user_data(db: Session, user_id: int, *, include_subscriptions: bool = True) -> dict[str, int]:
    """Remove user-owned rows; keep users row."""
    stats: dict[str, int] = {}

    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.user_id == user_id)
        .one_or_none()
    )
    if member:
        db.delete(member)
        stats["family_members"] = 1

    stats["family_invites"] = (
        db.query(FamilyInvite)
        .filter(
            (FamilyInvite.invited_by_user_id == user_id)
            | (FamilyInvite.invited_user_id == user_id)
        )
        .delete(synchronize_session=False)
    )

    stats["menu_selections"] = _delete_by_user_id(db, FamilyMenuSelection, user_id)

    shopping = (
        db.query(FamilyShoppingList)
        .filter(FamilyShoppingList.user_id == user_id)
        .one_or_none()
    )
    if shopping:
        shopping.items = []
        stats["shopping_lists"] = 1

    stats["pantry_items"] = (
        db.query(FamilyPantryItem)
        .filter(FamilyPantryItem.user_id == user_id)
        .delete(synchronize_session=False)
    )

    stats["shopping_categories"] = _delete_by_user_id(db, ShoppingCategory, user_id)
    stats["meal_consumption_logs"] = _delete_by_user_id(db, MealConsumptionLog, user_id)
    stats["meal_checkins"] = _delete_by_user_id(db, MealCheckin, user_id)
    stats["meal_leftovers"] = _delete_by_user_id(db, MealLeftover, user_id)
    stats["cooking_batches"] = _delete_by_user_id(db, CookingBatch, user_id)
    stats["cooking_batch_events"] = (
        db.query(CookingBatchEvent)
        .filter(CookingBatchEvent.actor_user_id == user_id)
        .delete(synchronize_session=False)
    )
    stats["water_intake"] = _delete_by_user_id(db, WaterIntakeLog, user_id)
    stats["external_food_logs"] = _delete_by_user_id(db, ExternalFoodLog, user_id)
    stats["deferred_advice"] = _delete_by_user_id(db, DeferredNutritionAdvice, user_id)
    stats["event_plans"] = _delete_by_user_id(db, EventPlan, user_id)
    stats["ai_usage"] = _delete_by_user_id(db, AiUsageLog, user_id)
    stats["recipe_favorites"] = _delete_by_user_id(db, RecipeFavorite, user_id)
    stats["user_recipes"] = _delete_by_user_id(db, Recipe, user_id)
    stats["progress_entries"] = _delete_by_user_id(db, ProgressEntry, user_id)
    stats["training_entries"] = _delete_by_user_id(db, TrainingEntry, user_id)
    stats["nutrition_targets"] = _delete_by_user_id(db, NutritionTarget, user_id)
    stats["care_settings"] = _delete_by_user_id(db, CareSettings, user_id)
    stats["care_notifications"] = _delete_by_user_id(db, CareNotification, user_id)
    stats["care_events"] = _delete_by_user_id(db, CareEvent, user_id)
    stats["reminder_events"] = _delete_by_user_id(
        db, MealConsumptionReminderEvent, user_id
    )

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).one_or_none()
    if profile:
        profile.current_step = 0
        profile.completed = False
        profile.goals = []
        profile.diets = []
        profile.allergies = []
        profile.restrictions = []
        stats["user_profile"] = 1

    prefs = (
        db.query(UserPreferences)
        .filter(UserPreferences.user_id == user_id)
        .one_or_none()
    )
    if prefs:
        db.delete(prefs)
        stats["user_preferences"] = 1

    notif = (
        db.query(UserNotificationSettings)
        .filter(UserNotificationSettings.user_id == user_id)
        .one_or_none()
    )
    if notif:
        db.delete(notif)
        stats["notification_settings"] = 1

    wallet = db.query(AmaWallet).filter(AmaWallet.user_id == user_id).one_or_none()
    if wallet:
        stats["ama_transactions"] = (
            db.query(AmaTransaction)
            .filter(AmaTransaction.wallet_id == wallet.id)
            .delete(synchronize_session=False)
        )
        wallet.balance = 0

    if include_subscriptions:
        stats["subscriptions"] = (
            db.query(UserSubscription)
            .filter(UserSubscription.user_id == user_id)
            .delete(synchronize_session=False)
        )

    db.query(AdminSession).filter(AdminSession.user_id == user_id).update(
        {"is_active": False}
    )

    return stats


def hard_delete_user_row(db: Session, user: User) -> None:
    """Delete user row; DB cascades handle remaining FK children."""
    db.delete(user)


def snapshot_user_for_backup(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_blocked": user.is_blocked,
        "is_deleted": user.is_deleted,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
