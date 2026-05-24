"""User and system shopping categories."""

from __future__ import annotations

import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.shopping_category import ShoppingCategory
from app.schemas.shopping_category import ShoppingCategoryCreateRequest
from app.services.app_scope import AppScope
from app.services.shopping_categories import NON_FOOD_CATEGORIES, is_food_category, normalize_category

SYSTEM_CATEGORIES: list[tuple[str, str, str | None, bool]] = [
    ("продукты", "Продукты", "🛒", True),
    ("овощи_зелень", "Овощи и зелень", "🥕", True),
    ("фрукты", "Фрукты", "🍎", True),
    ("мясо_птица", "Мясо и птица", "🥩", True),
    ("рыба_морепродукты", "Рыба и морепродукты", "🐟", True),
    ("молочные", "Молочные продукты", "🥛", True),
    ("яйца", "Яйца", "🥚", True),
    ("хлеб_выпечка", "Хлеб и выпечка", "🍞", True),
    ("крупы_макароны", "Крупы и макароны", "🌾", True),
    ("заморозка", "Заморозка", "🧊", True),
    ("напитки", "Напитки", "🥤", True),
    ("сладости", "Сладости", "🍰", True),
    ("бытовые", "Бытовые товары", "🧴", False),
    ("животные", "Для животных", "🐾", False),
    ("другое", "Другое", "📦", False),
    # legacy slugs kept for existing items
    ("овощи", "Овощи", "🥕", True),
    ("мясо", "Мясо", "🥩", True),
    ("рыба", "Рыба", "🐟", True),
    ("молочное", "Молочное", "🥛", True),
    ("крупы", "Крупы", "🌾", True),
    ("хлеб", "Хлеб", "🍞", True),
    ("дом_и_химия", "Дом и химия", "🧴", False),
    ("питомцы", "Питомцы", "🐾", False),
]


def slug_from_display_name(name: str) -> str:
    cleaned = name.strip().lower().replace(" ", "_")
    cleaned = re.sub(r"[^\wа-яё0-9_]+", "", cleaned, flags=re.IGNORECASE)
    return cleaned[:64] or "категория"


def _scope_filters(scope: AppScope):
    if scope.is_family:
        return ShoppingCategory.family_id == scope.family_id
    return ShoppingCategory.user_id == scope.user_id


def ensure_system_categories(db: Session, scope: AppScope) -> None:
    for slug, name, icon, is_food in SYSTEM_CATEGORIES:
        query = db.query(ShoppingCategory).filter(
            _scope_filters(scope),
            ShoppingCategory.slug == slug,
            ShoppingCategory.is_system.is_(True),
        )
        existing = query.one_or_none()
        if existing is None:
            db.add(
                ShoppingCategory(
                    slug=slug,
                    name=name,
                    icon=icon,
                    is_food=is_food,
                    is_system=True,
                    user_id=scope.user_id if scope.is_personal else None,
                    family_id=scope.family_id if scope.is_family else None,
                )
            )
    db.commit()


def list_categories(db: Session, scope: AppScope) -> list[ShoppingCategory]:
    ensure_system_categories(db, scope)
    return (
        db.query(ShoppingCategory)
        .filter(_scope_filters(scope))
        .order_by(ShoppingCategory.is_system.desc(), ShoppingCategory.name.asc())
        .all()
    )


def get_category_by_slug(
    db: Session, scope: AppScope, slug: str
) -> ShoppingCategory | None:
    ensure_system_categories(db, scope)
    normalized = normalize_category(slug)
    cat = (
        db.query(ShoppingCategory)
        .filter(_scope_filters(scope), ShoppingCategory.slug == normalized)
        .one_or_none()
    )
    if cat is not None:
        return cat
    by_name = slug_from_display_name(slug)
    return (
        db.query(ShoppingCategory)
        .filter(_scope_filters(scope), ShoppingCategory.slug == by_name)
        .one_or_none()
    )


def category_is_food(db: Session, scope: AppScope, category_slug: str) -> bool:
    cat = get_category_by_slug(db, scope, category_slug)
    if cat is not None:
        return cat.is_food
    return is_food_category(category_slug)


def create_category(
    db: Session,
    scope: AppScope,
    payload: ShoppingCategoryCreateRequest,
) -> ShoppingCategory:
    ensure_system_categories(db, scope)
    slug = slug_from_display_name(payload.name)
    existing = get_category_by_slug(db, scope, slug)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Категория с таким названием уже есть",
        )
    row = ShoppingCategory(
        slug=slug,
        name=payload.name.strip(),
        icon=payload.icon,
        is_food=payload.is_food,
        is_system=False,
        user_id=scope.user_id if scope.is_personal else None,
        family_id=scope.family_id if scope.is_family else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def resolve_category_for_item(
    db: Session,
    scope: AppScope,
    category_name: str,
    *,
    is_food: bool | None = None,
) -> tuple[str, bool]:
    """Return (slug, is_food) for item; create user category if needed."""
    ensure_system_categories(db, scope)
    slug = slug_from_display_name(category_name)
    cat = get_category_by_slug(db, scope, slug)
    if cat is not None:
        return cat.slug, cat.is_food
    inferred_slug = normalize_category(category_name)
    cat = get_category_by_slug(db, scope, inferred_slug)
    if cat is not None:
        return cat.slug, cat.is_food
    food = is_food if is_food is not None else True
    row = ShoppingCategory(
        slug=slug,
        name=category_name.strip(),
        icon=None,
        is_food=food,
        is_system=False,
        user_id=scope.user_id if scope.is_personal else None,
        family_id=scope.family_id if scope.is_family else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row.slug, row.is_food
