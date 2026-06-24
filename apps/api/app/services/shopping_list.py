from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.family import FamilyMember
from app.models.menu_selection import FamilyMenuSelection
from app.models.shopping_list import FamilyShoppingList
from app.models.user import User
from app.schemas.menu import MenuVariant
from app.schemas.shopping_category import ShoppingCategoryResponse
from app.schemas.shopping_list import (
    ShoppingItemCreateRequest,
    ShoppingItemUpdateRequest,
    ShoppingListItem,
    ShoppingListResponse,
)
from app.services.app_scope import AppScope
from app.services.pantry import delete_item as delete_pantry_item
from app.services.pantry_shopping import add_or_merge_from_shopping
from app.services.shopping_category_service import (
    category_is_food,
    list_categories,
    resolve_category_for_item,
)
from app.services.shopping_item_utils import (
    display_amount,
    item_from_menu_ingredient,
    make_item_id,
    new_manual_item_id,
    normalize_item,
    predict_menu_item_id,
    should_skip_menu_ingredient_for_shopping,
    sum_menu_items,
)
from app.services.shopping_categories import CATEGORY_ORDER


def _sort_items(items: list[ShoppingListItem]) -> list[ShoppingListItem]:
    order_index = {cat: index for index, cat in enumerate(CATEGORY_ORDER)}
    category_names: dict[str, str] = {}

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
    return [normalize_item(item) for item in (raw_items or [])]


def _category_responses(db: Session, scope: AppScope) -> list[ShoppingCategoryResponse]:
    return [
        ShoppingCategoryResponse(
            id=c.id,
            slug=c.slug,
            name=c.name,
            icon=c.icon,
            is_food=c.is_food,
            is_system=c.is_system,
            created_at=c.created_at,
        )
        for c in list_categories(db, scope)
    ]


def _to_response(
    shopping_list: FamilyShoppingList,
    scope: AppScope,
    items: list[ShoppingListItem],
    menu_title: str | None,
    db: Session,
) -> ShoppingListResponse:
    checked_count = sum(1 for item in items if item.checked)
    return ShoppingListResponse(
        scope_mode=scope.mode,
        user_id=shopping_list.user_id,
        family_id=shopping_list.family_id,
        menu_title=menu_title,
        items=items,
        categories=_category_responses(db, scope),
        total_count=len(items),
        checked_count=checked_count,
        updated_at=shopping_list.updated_at,
    )


def _save_items(
    db: Session,
    shopping_list: FamilyShoppingList,
    items: list[ShoppingListItem],
) -> None:
    shopping_list.items = [item.model_dump(mode="json") for item in items]
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(shopping_list)


def build_items_from_ingredients(
    ingredients: list,
    previous: list[ShoppingListItem] | None = None,
) -> list[ShoppingListItem]:
    previous_map: dict[str, ShoppingListItem] = {}
    for raw in previous or []:
        item = normalize_item(raw)
        previous_map[item.id] = item

    by_id: dict[str, ShoppingListItem] = {}

    for ingredient in ingredients:
        name = (ingredient.name or "").strip()
        amount_str = (ingredient.amount or "").strip()
        category_hint = getattr(ingredient, "category", None)
        if should_skip_menu_ingredient_for_shopping(name, amount_str, category_hint):
            continue

        item_id = predict_menu_item_id(name, amount_str, category_hint)
        existing = by_id.get(item_id)
        if existing is not None:
            # Same product+unit in the same menu — sum instead of overwriting.
            fresh = item_from_menu_ingredient(name, amount_str, category_hint, None)
            by_id[item_id] = sum_menu_items(existing, fresh)
        else:
            prev = previous_map.get(item_id)
            by_id[item_id] = item_from_menu_ingredient(
                name, amount_str, category_hint, prev
            )

    return _sort_items(list(by_id.values()))


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
    manual_items = [i for i in previous if i.source == "manual"]
    menu_items = build_items_from_ingredients(menu.ingredients, previous)
    menu_ids = {i.id for i in menu_items}
    merged = menu_items + [i for i in manual_items if i.id not in menu_ids]
    items = _sort_items(merged)

    _save_items(db, shopping_list, items)
    shopping_list.menu_selection_id = menu_selection_id
    db.commit()
    db.refresh(shopping_list)

    member_names = (
        _member_names(db, scope.family_id)
        if scope.is_family and scope.family_id
        else {}
    )
    enriched = _enrich_items(items, member_names)
    return _to_response(shopping_list, scope, enriched, menu.title, db)


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

    return _to_response(shopping_list, scope, items, menu_title, db)


def create_item(
    db: Session,
    user: User,
    scope: AppScope,
    payload: ShoppingItemCreateRequest,
) -> ShoppingListResponse:
    slug, _ = resolve_category_for_item(
        db,
        scope,
        payload.category,
        is_food=payload.is_food,
    )
    unit = payload.unit.strip() or "шт"
    quantity = payload.quantity.strip() or "1"
    item = ShoppingListItem(
        id=new_manual_item_id(),
        name=payload.name.strip(),
        category=slug,
        quantity=quantity,
        unit=unit,
        amount=display_amount(quantity, unit),
        note=payload.note,
        source="manual",
        created_by_user_id=user.id,
    )
    item = normalize_item(
        item.model_copy(update={"id": make_item_id(item.name, slug, unit)})
    )

    shopping_list = _get_or_create_list(db, scope)
    items = _items_from_storage(shopping_list.items)
    if any(
        i.id == item.id or (i.name.lower() == item.name.lower() and i.category == slug)
        for i in items
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Такой товар уже есть в списке",
        )
    items.append(item)
    _save_items(db, shopping_list, _sort_items(items))
    return get_shopping_list(db, user, scope)


def update_item(
    db: Session,
    user: User,
    scope: AppScope,
    item_id: str,
    payload: ShoppingItemUpdateRequest,
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
        name = payload.name.strip() if payload.name else item.name
        category = item.category
        if payload.category:
            category, _ = resolve_category_for_item(db, scope, payload.category)
        quantity = payload.quantity if payload.quantity is not None else item.quantity
        unit = payload.unit if payload.unit is not None else item.unit
        note = payload.note if payload.note is not None else item.note
        checked = item.checked if payload.checked is None else payload.checked

        new_item = normalize_item(
            item.model_copy(
                update={
                    "name": name,
                    "category": category,
                    "quantity": quantity,
                    "unit": unit,
                    "amount": display_amount(quantity, unit),
                    "note": note,
                    "checked": checked,
                }
            )
        )

        if payload.checked is True and not item.checked:
            linked_id = new_item.linked_pantry_item_id
            added = False
            if category_is_food(db, scope, new_item.category):
                pantry_item = add_or_merge_from_shopping(db, user, scope, new_item)
                linked_id = pantry_item.id
                added = True
            new_item = new_item.model_copy(
                update={
                    "checked": True,
                    "checked_by_user_id": user.id,
                    "checked_by_name": display_name,
                    "checked_at": now,
                    "linked_pantry_item_id": linked_id,
                    "added_to_pantry": added,
                }
            )
        elif payload.checked is False and item.checked:
            linked_id = new_item.linked_pantry_item_id
            if payload.remove_from_pantry and linked_id:
                try:
                    delete_pantry_item(db, scope, linked_id)
                except HTTPException:
                    pass
                linked_id = None
            new_item = new_item.model_copy(
                update={
                    "checked": False,
                    "checked_by_user_id": None,
                    "checked_by_name": None,
                    "checked_at": None,
                    "linked_pantry_item_id": linked_id,
                    "added_to_pantry": bool(linked_id),
                }
            )

        updated.append(new_item)

    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Позиция не найдена")

    _save_items(db, shopping_list, updated)
    return get_shopping_list(db, user, scope)


def delete_item(
    db: Session,
    user: User,
    scope: AppScope,
    item_id: str,
) -> ShoppingListResponse:
    shopping_list = _get_or_create_list(db, scope)
    items = _items_from_storage(shopping_list.items)
    if not any(i.id == item_id for i in items):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Позиция не найдена")
    items = [i for i in items if i.id != item_id]
    _save_items(db, shopping_list, items)
    return get_shopping_list(db, user, scope)


def toggle_item(
    db: Session,
    user: User,
    scope: AppScope,
    item_id: str,
    checked: bool,
    *,
    remove_from_pantry: bool = False,
) -> ShoppingListResponse:
    return update_item(
        db,
        user,
        scope,
        item_id,
        ShoppingItemUpdateRequest(checked=checked, remove_from_pantry=remove_from_pantry),
    )
