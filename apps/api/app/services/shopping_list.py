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
from app.services import family as family_service

CATEGORY_ORDER = [
    "овощи",
    "фрукты",
    "мясо",
    "рыба",
    "молочное",
    "яйца",
    "крупы",
    "бобовые",
    "соусы",
    "прочее",
]

CATEGORY_ALIASES = {
    "vegetables": "овощи",
    "овощи": "овощи",
    "fruit": "фрукты",
    "fruits": "фрукты",
    "фрукты": "фрукты",
    "meat": "мясо",
    "мясо": "мясо",
    "fish": "рыба",
    "seafood": "рыба",
    "рыба": "рыба",
    "dairy": "молочное",
    "молочное": "молочное",
    "eggs": "яйца",
    "яйца": "яйца",
    "grains": "крупы",
    "крупы": "крупы",
    "legumes": "бобовые",
    "бобовые": "бобовые",
    "sauces": "соусы",
    "соусы": "соусы",
    "other": "прочее",
    "прочее": "прочее",
}

CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("овощи", ["морков", "лук", "картоф", "помидор", "огурц", "капуст", "перец", "чеснок", "свекл", "кабач", "брокколи", "цукини", "овощ"]),
    ("фрукты", ["яблок", "банан", "ягод", "груш", "апельсин", "лимон", "фрукт"]),
    ("мясо", ["курин", "говядин", "свинин", "фарш", "индейк", "мяс", "котлет"]),
    ("рыба", ["рыб", "лосос", "треск", "кревет", "морепродукт"]),
    ("молочное", ["молок", "сыр", "творог", "йогурт", "кефир", "сливк", "сметан"]),
    ("яйца", ["яйц"]),
    ("крупы", ["рис", "греч", "овсян", "макарон", "паста", "киноа", "гранол", "мук"]),
    ("бобовые", ["чечевиц", "фасол", "горох", "нут", "тофу"]),
    ("соусы", ["соус", "паста томат", "майонез", "кетчуп", "масло раст"]),
]


def _require_family_membership(db: Session, user: User) -> FamilyMember:
    membership = family_service.get_user_membership(db, user)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Создайте семью для общего списка покупок",
        )
    return membership


def _normalize_name(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", name.strip().lower())
    return cleaned


def _normalize_category(raw: str | None) -> str:
    if not raw:
        return "прочее"
    key = raw.strip().lower()
    return CATEGORY_ALIASES.get(key, key if key in CATEGORY_ORDER else "прочее")


def _infer_category(name: str, hint: str | None) -> str:
    category = _normalize_category(hint)
    if category != "прочее":
        return category
    lowered = name.lower()
    for cat, keywords in CATEGORY_KEYWORDS:
        if any(word in lowered for word in keywords):
            return cat
    return "прочее"


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
    previous_map = {
        item.id: item for item in (previous or []) if isinstance(item, ShoppingListItem)
    }
    if previous and not previous_map:
        for raw in previous:
            if isinstance(raw, dict):
                item = ShoppingListItem.model_validate(raw)
                previous_map[item.id] = item
            elif isinstance(raw, ShoppingListItem):
                previous_map[raw.id] = raw

    merged: dict[str, dict] = {}

    for ingredient in ingredients:
        name = ingredient.name.strip()
        if not name:
            continue
        category = _infer_category(name, ingredient.category)
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
        db.query(FamilyMember)
        .filter(FamilyMember.family_id == family_id)
        .all()
    )
    result: dict[int, str] = {}
    for member in members:
        if member.user_id is not None:
            result[member.user_id] = member.display_name
    return result


def _enrich_items(
    items: list[ShoppingListItem], member_names: dict[int, str]
) -> list[ShoppingListItem]:
    enriched: list[ShoppingListItem] = []
    for item in items:
        name = member_names.get(item.checked_by_user_id) if item.checked_by_user_id else None
        enriched.append(
            item.model_copy(update={"checked_by_name": name if item.checked else None})
        )
    return enriched


def _get_or_create_list(db: Session, family_id: int) -> FamilyShoppingList:
    shopping_list = (
        db.query(FamilyShoppingList)
        .filter(FamilyShoppingList.family_id == family_id)
        .one_or_none()
    )
    if shopping_list is None:
        shopping_list = FamilyShoppingList(family_id=family_id, items=[])
        db.add(shopping_list)
        db.commit()
        db.refresh(shopping_list)
    return shopping_list


def _items_from_storage(raw_items: list) -> list[ShoppingListItem]:
    return [ShoppingListItem.model_validate(item) for item in (raw_items or [])]


def _to_response(
    shopping_list: FamilyShoppingList,
    items: list[ShoppingListItem],
    menu_title: str | None,
) -> ShoppingListResponse:
    checked_count = sum(1 for item in items if item.checked)
    return ShoppingListResponse(
        family_id=shopping_list.family_id,
        menu_title=menu_title,
        items=items,
        total_count=len(items),
        checked_count=checked_count,
        updated_at=shopping_list.updated_at,
    )


def sync_shopping_list_for_user(db: Session, user: User) -> ShoppingListResponse:
    membership = _require_family_membership(db, user)
    result = sync_from_selected_menu(db, membership.family_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала выберите меню на странице AI Меню",
        )
    return result


def sync_from_selected_menu(db: Session, family_id: int) -> ShoppingListResponse | None:
    selection = (
        db.query(FamilyMenuSelection)
        .filter(FamilyMenuSelection.family_id == family_id)
        .order_by(FamilyMenuSelection.selected_at.desc())
        .first()
    )
    if selection is None:
        return None

    menu = MenuVariant.model_validate(selection.menu_data)
    return sync_from_menu(db, family_id, menu, selection.id)


def sync_from_menu(
    db: Session,
    family_id: int,
    menu: MenuVariant,
    menu_selection_id: int | None = None,
) -> ShoppingListResponse:
    shopping_list = _get_or_create_list(db, family_id)
    previous = _items_from_storage(shopping_list.items)
    items = build_items_from_ingredients(menu.ingredients, previous)

    shopping_list.items = [item.model_dump(mode="json") for item in items]
    shopping_list.menu_selection_id = menu_selection_id
    shopping_list.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(shopping_list)

    member_names = _member_names(db, family_id)
    enriched = _enrich_items(items, member_names)
    return _to_response(shopping_list, enriched, menu.title)


def get_shopping_list(db: Session, user: User) -> ShoppingListResponse:
    membership = _require_family_membership(db, user)
    shopping_list = _get_or_create_list(db, membership.family_id)
    items = _items_from_storage(shopping_list.items)
    items = _enrich_items(items, _member_names(db, membership.family_id))

    menu_title: str | None = None
    if shopping_list.menu_selection_id:
        selection = db.get(FamilyMenuSelection, shopping_list.menu_selection_id)
        if selection:
            menu = MenuVariant.model_validate(selection.menu_data)
            menu_title = menu.title

    return _to_response(shopping_list, items, menu_title)


def toggle_item(
    db: Session, user: User, item_id: str, checked: bool
) -> ShoppingListResponse:
    membership = _require_family_membership(db, user)
    shopping_list = _get_or_create_list(db, membership.family_id)
    items = _items_from_storage(shopping_list.items)

    found = False
    updated: list[ShoppingListItem] = []
    now = datetime.now(timezone.utc)
    display_name = membership.display_name

    for item in items:
        if item.id != item_id:
            updated.append(item)
            continue
        found = True
        if checked:
            updated.append(
                item.model_copy(
                    update={
                        "checked": True,
                        "checked_by_user_id": user.id,
                        "checked_by_name": display_name,
                        "checked_at": now,
                    }
                )
            )
        else:
            updated.append(
                item.model_copy(
                    update={
                        "checked": False,
                        "checked_by_user_id": None,
                        "checked_by_name": None,
                        "checked_at": None,
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

    member_names = _member_names(db, membership.family_id)
    enriched = _enrich_items(updated, member_names)

    menu_title: str | None = None
    if shopping_list.menu_selection_id:
        selection = db.get(FamilyMenuSelection, shopping_list.menu_selection_id)
        if selection:
            menu_title = MenuVariant.model_validate(selection.menu_data).title

    return _to_response(shopping_list, enriched, menu_title)
