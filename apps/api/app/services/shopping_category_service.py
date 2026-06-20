"""User and system shopping categories."""

from __future__ import annotations

import logging
import re

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from app.models.shopping_category import ShoppingCategory
from app.schemas.shopping_category import ShoppingCategoryCreateRequest
from app.services.app_scope import AppScope
from app.services.categories_v1 import SYSTEM_CATEGORIES_V1
from app.services.shopping_categories import is_food_category, normalize_category

logger = logging.getLogger(__name__)

SYSTEM_CATEGORIES: list[tuple[str, str, str | None, bool]] = [
    (slug, label, icon, is_food) for slug, label, icon, is_food in SYSTEM_CATEGORIES_V1
]


def slug_from_display_name(name: str) -> str:
    cleaned = name.strip().lower().replace(" ", "_")
    cleaned = re.sub(r"[^\wа-яё0-9_]+", "", cleaned, flags=re.IGNORECASE)
    return cleaned[:64] or "категория"


def _scope_filters(scope: AppScope):
    if scope.is_family:
        return ShoppingCategory.family_id == scope.family_id
    return ShoppingCategory.user_id == scope.user_id


def _one_category_or_first(
    query: Query[ShoppingCategory],
    *,
    context: str,
) -> ShoppingCategory | None:
    """Return the oldest row; log and tolerate duplicate legacy rows."""
    rows = query.order_by(ShoppingCategory.id.asc()).all()
    if not rows:
        return None
    if len(rows) > 1:
        logger.warning(
            "Duplicate shopping categories for %s (ids=%s), using id=%s",
            context,
            [row.id for row in rows],
            rows[0].id,
        )
    return rows[0]


def _find_system_category(
    db: Session,
    scope: AppScope,
    *,
    slug: str,
    name: str,
) -> ShoppingCategory | None:
    """Find an existing system category for this scope by slug, then by display name."""
    base = db.query(ShoppingCategory).filter(
        _scope_filters(scope),
        ShoppingCategory.is_system.is_(True),
    )
    scope_label = f"{scope.mode} user={scope.user_id} family={scope.family_id}"
    by_slug = _one_category_or_first(
        base.filter(ShoppingCategory.slug == slug),
        context=f"system slug={slug} {scope_label}",
    )
    if by_slug is not None:
        return by_slug
    return _one_category_or_first(
        base.filter(ShoppingCategory.name == name),
        context=f"system name={name!r} {scope_label}",
    )


def ensure_system_categories(db: Session, scope: AppScope) -> None:
    for slug, name, icon, is_food in SYSTEM_CATEGORIES:
        existing = _find_system_category(db, scope, slug=slug, name=name)
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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning(
            "Concurrent system category seed for scope=%s user=%s family=%s; "
            "unique constraint prevented duplicate insert",
            scope.mode,
            scope.user_id,
            scope.family_id,
        )


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
    cat = _one_category_or_first(
        db.query(ShoppingCategory).filter(
            _scope_filters(scope), ShoppingCategory.slug == normalized
        ),
        context=f"slug={normalized} scope={scope.mode}",
    )
    if cat is not None:
        return cat
    by_name = slug_from_display_name(slug)
    return _one_category_or_first(
        db.query(ShoppingCategory).filter(
            _scope_filters(scope), ShoppingCategory.slug == by_name
        ),
        context=f"slug={by_name} scope={scope.mode}",
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
