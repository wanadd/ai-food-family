import hashlib
import re
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.family import FamilyMember
from app.models.menu_selection import FamilyMenuSelection
from app.models.shopping_list import FamilyShoppingList
from app.models.user import User
from app.schemas.menu import MenuIngredient, MenuVariant
from app.schemas.shopping_list import ShoppingListItem, ShoppingListResponse
from app.services.app_scope import AppScope
from app.services.pantry import delete_item as delete_pantry_item
from app.services.pantry_shopping import add_or_merge_from_shopping
from app.services.shopping_categories import (
    CATEGORY_ORDER,
    infer_category,
    is_food_category,
    normalize_category,
)


def _normalize_name(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", name.strip().lower())
    return cleaned


def _item_id(name: str, category: str) -> str:
    key = f"{category}:{_normalize_name(name)}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _merge_amounts(amounts: list[str]) -> str:
    unique: list[str] = []
    for amount in amounts:
        cleaned = amount.strip()
        if cleaned and cleaned not in unique:
            unique.append(cleaned)
    if len(unique) == 1:
        return unique[0]
    return " + ".join(unique)


def build_items_from_ingredients(
    ingredients: list[MenuIngredient],
    previous: list[ShoppingListItem] | None = None,
) -> list[ShoppingListItem]:
    previous_map: dict[str, ShoppingListItem] = {}
    for raw in previous or []:
        if isinstance(raw, dict):
            item = ShoppingListItem.model_validate(raw)
        elif isinstance(raw, ShoppingListItem):
            item = raw
        else:
            continue
        previous_map[item.id] = item

    merged: dict[str, dict] = {}

    for ingredient in ingredients:
        name = ingredient.name.strip()
        if not name:
            continue
        category = infer_category(name, ingredient.category)
        item_id = _item_id(name, category)
        amount = ingredient.amount.strip()

        if item_id not in merged:
            merged[item_id] = {
                "id": item_id,
                "name": name,
                "category": category,
                "amounts": [],
            }

        entry = merged[item_id]
        if len(name) > len(entry["name"]):
            entry["name"] = name
        if amount and amount not in entry["amounts"]:
            entry["amounts"].append(amount)

    items: list[ShoppingListItem] = []
    for entry in merged.values():
        prev = previous_map.get(entry["id"])
        amounts = entry["amounts"]
        items.append(
            ShoppingListItem(
                id=entry["id"],
                name=entry["name"],
                amount=_merge_amounts(amounts),
                amounts=amounts,
                category=entry["category"],
                checked=prev.checked if prev else False,
                checked_by_user_id=prev.checked_by_user_id if prev else None,
                checked_by_name=prev.checked_by_name if prev else None,
                checked_at=prev.checked_at if prev else None,
                linked_pantry_item_id=prev.linked_pantry_item_id if prev else None,
                added_to_pantry=bool(prev.linked_pantry_item_id) if prev else False,
            )
        )

    return _sort_items(items)


def _sort_items(items: list[ShoppingListItem]) -> list[ShoppingListItem]:
    order_index = {cat: index for index, cat in enumerate(CATEGORY_ORDER)}

    def sort_key(item: ShoppingListItem) -> tuple:
        return (
            order_index.get(item.category, len(CATEGORY_ORDER)),
            item.checked,
            item.name.lower(),
        )

    return sorted(items, key=sort_key)


def _member_names(db: Session, family_id: int) -> dict[int, str]:
    members = (
        db.query(FamilyMember).filter(FamilyMember.family_id == family_id).all()
    )
    return {
        member.user_id: member.display_name
        for member in members
        if member.user_id is not None
    }


def _enrich_items(
    items: list[ShoppingListItem],
    member_names: dict[int, str],
    checker_name: str | None = None,
) -> list[ShoppingListItem]:
    enriched: list[ShoppingListItem] = []
    for item in items:
        name = None
        if item.checked:
            if item.checked_by_user_id and item.checked_by_user_id in member_names:
                name = member_names[item.checked_by_user_id]
            elif checker_name:
                name = checker_name
        enriched.append(item.model_copy(update={"checked_by_name": name}))
    return enriched


def _get_or_create_list(db: Session, scope: AppScope) -> FamilyShoppingList:
    if scope.is_family:
        shopping_list = (
            db.query(FamilyShoppingList)
            .filter(FamilyShoppingList.family_id == scope.family_id)
            .one_or_none()
        )
        if shopping_list is None:
            shopping_list = FamilyShoppingList(family_id=scope.family_id, items=[])
            db.add(shopping_list)
            db.commit()
            db.refresh(shopping_list)
        return shopping_list

    shopping_list = (
        db.query(FamilyShoppingList)
        .filter(FamilyShoppingList.user_id == scope.user_id)
        .one_or_none()
    )
    if shopping_list is None:
        shopping_list = FamilyShoppingList(user_id=scope.user_id, items=[])
        db.add(shopping_list)
        db.commit()
        db.refresh(shopping_list)
    return shopping_list


def _items_from_storage(raw_items: list) -> list[ShoppingListItem]:
    return [ShoppingListItem.model_validate(item) for item in (raw_items or [])]


def _to_response(
    shopping_list: FamilyShoppingList,
    scope: AppScope,
    items: list[ShoppingListItem],
    menu_title: str | None,
) -> ShoppingListResponse:
    checked_count = sum(1 for item in items if item.checked)
    return ShoppingListResponse(
        scope_mode=scope.mode,
        user_id=shopping_list.user_id,
        family_id=shopping_list.family_id,
        menu_title=menu_title,
        items=items,
        total_count=len(items),
        checked_count=checked_count,
        updated_at=shopping_list.updated_at,
    )


def _get_latest_selection(db: Session, scope: AppScope) -> FamilyMenuSelection | None:
    query = db.query(FamilyMenuSelection)
    if scope.is_family:
        query = query.filter(FamilyMenuSelection.family_id == scope.family_id)
    else:
        query = query.filter(
            FamilyMenuSelection.user_id == scope.user_id,
            FamilyMenuSelection.family_id.is_(None),
        )
    return query.order_by(FamilyMenuSelection.selected_at.desc()).first()


def sync_shopping_list_for_scope(db: Session, scope: AppScope) -> ShoppingListResponse:
    selection = _get_latest_selection(db, scope)
    if selection is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала выберите меню на странице AI Меню",
        )
    menu = MenuVariant.model_validate(selection.menu_data)
    return sync_from_menu(db, scope, menu, selection.id)


def sync_from_menu(
    db: Session,
    scope: AppScope,
    menu: MenuVariant,
    menu_selection_id: int | None = None,
) -> ShoppingListResponse:
    shopping_list = _get_or_create_list(db, scope)
    previous = _items_from_storage(shopping_list.items)
    items = build_items_from_ingredients(menu.ingredients, previous)

    shopping_list.items = [item.model_dump(mode="json") for item in items]
    shopping_list.menu_selection_id = menu_selection_id
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(shopping_list)

    member_names = (
        _member_names(db, scope.family_id)
        if scope.is_family and scope.family_id
        else {}
    )
    enriched = _enrich_items(items, member_names)
    return _to_response(shopping_list, scope, enriched, menu.title)


def get_shopping_list(db: Session, user: User, scope: AppScope) -> ShoppingListResponse:
    shopping_list = _get_or_create_list(db, scope)
    items = _items_from_storage(shopping_list.items)
    member_names = (
        _member_names(db, scope.family_id)
        if scope.is_family and scope.family_id
        else {}
    )
    checker = user.first_name or user.username
    items = _enrich_items(items, member_names, checker_name=checker)

    menu_title: str | None = None
    if shopping_list.menu_selection_id:
        selection = db.get(FamilyMenuSelection, shopping_list.menu_selection_id)
        if selection:
            menu_title = MenuVariant.model_validate(selection.menu_data).title

    return _to_response(shopping_list, scope, items, menu_title)


def toggle_item(
    db: Session,
    user: User,
    scope: AppScope,
    item_id: str,
    checked: bool,
    *,
    remove_from_pantry: bool = False,
) -> ShoppingListResponse:
    shopping_list = _get_or_create_list(db, scope)
    items = _items_from_storage(shopping_list.items)

    found = False
    updated: list[ShoppingListItem] = []
    now = datetime.now(timezone.utc)
    display_name = user.first_name or user.username or "Вы"

    for item in items:
        if item.id != item_id:
            updated.append(item)
            continue
        found = True
        if checked:
            linked_id = item.linked_pantry_item_id
            added_to_pantry = False
            if is_food_category(item.category):
                pantry_item = add_or_merge_from_shopping(db, user, scope, item)
                linked_id = pantry_item.id
                added_to_pantry = True
            updated.append(
                item.model_copy(
                    update={
                        "checked": True,
                        "checked_by_user_id": user.id,
                        "checked_by_name": display_name,
                        "checked_at": now,
                        "linked_pantry_item_id": linked_id,
                        "added_to_pantry": added_to_pantry,
                    }
                )
            )
        else:
            linked_id = item.linked_pantry_item_id
            if remove_from_pantry and linked_id:
                try:
                    delete_pantry_item(db, scope, linked_id)
                except HTTPException:
                    pass
                linked_id = None
            updated.append(
                item.model_copy(
                    update={
                        "checked": False,
                        "checked_by_user_id": None,
                        "checked_by_name": None,
                        "checked_at": None,
                        "linked_pantry_item_id": linked_id,
                        "added_to_pantry": bool(linked_id),
                    }
                )
            )

    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Позиция не найдена в списке",
        )

    shopping_list.items = [item.model_dump(mode="json") for item in updated]
    shopping_list.updated_at = now
    db.commit()
    db.refresh(shopping_list)

    member_names = (
        _member_names(db, scope.family_id)
        if scope.is_family and scope.family_id
        else {}
    )
    enriched = _enrich_items(updated, member_names, checker_name=display_name)

    menu_title: str | None = None
    if shopping_list.menu_selection_id:
        selection = db.get(FamilyMenuSelection, shopping_list.menu_selection_id)
        if selection:
            menu_title = MenuVariant.model_validate(selection.menu_data).title

    return _to_response(shopping_list, scope, enriched, menu_title)
