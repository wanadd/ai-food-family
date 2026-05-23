"""Structured recipe catalog for PlanAm (food, drinks, events)."""

from __future__ import annotations

from typing import Any


def _ing(name: str, qty: str, unit: str, cat: str = "other") -> dict[str, Any]:
    return {"name": name, "quantity": qty, "unit": unit, "category": cat}


def _r(
    title: str,
    meal_type: str,
    *,
    description: str = "",
    category: str = "main",
    cooking_time: int = 30,
    servings: int = 4,
    difficulty: str = "easy",
    ingredients: list[dict],
    steps: list[str],
    tags: list[str] | None = None,
    diets: list[str] | None = None,
    allergens: list[str] | None = None,
    calories: float | None = None,
    protein: float | None = None,
    is_drink: bool = False,
    is_alcoholic: bool = False,
    alcohol_percent: float | None = None,
    caffeine_mg: float | None = None,
    sugar_g: float | None = None,
    suitable_children: bool = True,
    suitable_sport: bool = False,
    suitable_event: bool = False,
    restrictions: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "title": title,
        "description": description,
        "meal_type": meal_type,
        "category": category,
        "cooking_time_minutes": cooking_time,
        "prep_time_minutes": cooking_time,
        "servings": servings,
        "difficulty": difficulty,
        "ingredients": ingredients,
        "steps": steps,
        "tags": tags or [],
        "diets": diets or [],
        "allergens": allergens or [],
        "restrictions": restrictions or diets or [],
        "calories_per_serving": calories,
        "protein_g": protein,
        "is_drink": is_drink,
        "is_alcoholic": is_alcoholic,
        "alcohol_percent": alcohol_percent,
        "caffeine_mg": caffeine_mg,
        "sugar_g": sugar_g,
        "suitable_for_children": suitable_children,
        "suitable_for_sport": suitable_sport,
        "suitable_for_event": suitable_event,
        "source_type": "import",
    }


FOOD_TITLES = [
    ("Гречка с курицей", "lunch", "main", 35, [_ing("Гречка", "200", "г"), _ing("Куриное филе", "400", "г", "meat")]),
    ("Паста с томатным соусом", "dinner", "main", 25, [_ing("Паста", "300", "г"), _ing("Помидоры", "400", "г", "vegetables")]),
    ("Рыба запечённая с лимоном", "dinner", "main", 40, [_ing("Филе белой рыбы", "500", "г", "fish"), _ing("Лимон", "1", "шт")]),
    ("Куриный суп с лапшой", "lunch", "soup", 45, [_ing("Курица", "300", "г", "meat"), _ing("Лапша", "150", "г")]),
    ("Салат Цезарь", "lunch", "salad", 20, [_ing("Салат романо", "1", "шт"), _ing("Курица", "200", "г", "meat")]),
    ("Плов узбекский", "dinner", "main", 90, [_ing("Рис", "400", "г"), _ing("Баранина", "500", "г", "meat")]),
    ("Тушёная капуста", "lunch", "main", 40, [_ing("Капуста", "600", "г", "vegetables"), _ing("Морковь", "150", "г", "vegetables")]),
    ("Котлеты из индейки", "dinner", "main", 35, [_ing("Фарш индейки", "600", "г", "meat"), _ing("Лук", "1", "шт")]),
    ("Запечённые овощи", "dinner", "main", 50, [_ing("Кабачок", "1", "шт"), _ing("Баклажан", "1", "шт")]),
    ("Блины тонкие", "breakfast", "quick", 30, [_ing("Молоко", "500", "мл", "dairy"), _ing("Яйца", "3", "шт"), _ing("Мука", "200", "г")]),
    ("Сырники", "breakfast", "main", 25, [_ing("Творог", "400", "г", "dairy"), _ing("Яйца", "2", "шт")]),
    ("Греческий салат", "lunch", "salad", 15, [_ing("Огурцы", "2", "шт"), _ing("Помидоры", "3", "шт"), _ing("Сыр фета", "150", "г", "dairy")]),
    ("Рагу из овощей", "lunch", "main", 40, [_ing("Картофель", "3", "шт"), _ing("Морковь", "200", "г", "vegetables")]),
    ("Тефтели в сметанном соусе", "dinner", "main", 50, [_ing("Фарш говяжий", "500", "г", "meat"), _ing("Сметана", "200", "г", "dairy")]),
    ("Каша пшённая", "breakfast", "quick", 25, [_ing("Пшено", "200", "г"), _ing("Молоко", "400", "мл", "dairy")]),
    ("Шакшука", "breakfast", "main", 20, [_ing("Яйца", "4", "шт"), _ing("Помидоры", "400", "г", "vegetables")]),
    ("Лазанья", "dinner", "main", 75, [_ing("Листы лазаньи", "250", "г"), _ing("Фарш", "400", "г", "meat")]),
    ("Уха домашняя", "lunch", "soup", 50, [_ing("Рыба", "600", "г", "fish"), _ing("Картофель", "3", "шт")]),
    ("Фрикасе из курицы", "dinner", "main", 45, [_ing("Курица", "600", "г", "meat"), _ing("Сливки", "200", "мл", "dairy")]),
    ("Овощное рагу с нутом", "lunch", "main", 40, [_ing("Нут", "200", "г"), _ing("Морковь", "150", "г", "vegetables")]),
]

DRINK_SPECS = [
    ("Лимонад домашний", "drink", False, 5, 40, False, False, False),
    ("Морс клюквенный", "drink", False, 5, 35, True, False, False),
    ("Компот из сухофруктов", "drink", False, 5, 30, True, False, False),
    ("Мятный лимонад", "drink", False, 5, 10, True, False, False),
    ("Апельсиновый фреш", "drink", False, 5, 45, True, False, False),
    ("Смузи ягодный", "smoothie", False, 5, 55, True, True, False),
    ("Смузи зелёный", "smoothie", False, 5, 50, True, True, False),
    ("Смузи манго-банан", "smoothie", False, 5, 60, True, False, False),
    ("Смузи клубничный", "smoothie", False, 5, 55, True, False, False),
    ("Смузи овсяно-ягодный", "smoothie", False, 5, 65, True, True, False),
    ("Протеиновый коктейль ваниль", "protein_shake", False, 5, 120, False, True, False),
    ("Протеин шоколад-банан", "protein_shake", False, 5, 140, False, True, False),
    ("Изотоник домашний", "drink", False, 5, 25, False, True, False),
    ("Коктейль после тренировки", "protein_shake", False, 5, 150, False, True, False),
    ("Протеиновый смузи ягоды", "protein_shake", False, 5, 130, False, True, False),
    ("Латте домашний", "coffee", False, 5, 80, False, False, False),
    ("Капучино", "coffee", False, 5, 75, False, False, False),
    ("Чай имбирный", "tea", False, 5, 5, True, False, False),
    ("Молочный коктейль детский", "drink", False, 5, 90, True, False, True),
    ("Какао на молоке детское", "drink", False, 5, 85, True, False, True),
    ("Фруктовый пунш детский", "drink", False, 5, 50, True, False, True),
    ("Мохито безалкогольный", "cocktail", False, 5, 35, True, False, True),
    ("Клубничный лимонад праздничный", "cocktail", False, 5, 45, True, False, True),
    ("Имбирный эль домашний", "cocktail", False, 5, 40, True, False, True),
    ("Мохито классический", "cocktail", True, 5, 120, False, False, True),
    ("Джин-тоник", "cocktail", True, 5, 110, False, False, True),
    ("Апероль-спритц лайт", "cocktail", True, 5, 115, False, False, True),
]

EVENT_SPECS = [
    ("Утка с яблоками праздничная", "dinner", True, False),
    ("Салат оливье праздничный", "lunch", True, False),
    ("Канапе ассорти", "snack", True, False),
    ("Торт медовый домашний", "dessert", True, False),
    ("Глинтвейн безалкогольный", "drink", True, False),
    ("Постный суп грибной", "lunch", False, True),
    ("Постная запеканка овощная", "dinner", False, True),
    ("Постные котлеты из гречки", "lunch", False, True),
    ("Постный салат винегрет", "lunch", False, True),
    ("Постный компот", "drink", False, True),
    ("Мини-пицца детская", "lunch", False, False, True),
    ("Фруктовая тарелка детская", "snack", False, False, True),
    ("Сосиски в тесте детские", "snack", False, False, True),
    ("Шашлык из свинины", "dinner", True, False, False, True),
    ("Кукуруза на гриле", "snack", True, False, False, True),
    ("Маринованные овощи к мясу", "snack", True, False, False, True),
]


def build_catalog_recipes() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for title, meal, cat, mins, ings in FOOD_TITLES:
        out.append(
            _r(
                title,
                meal,
                category=cat,
                cooking_time=mins,
                ingredients=ings,
                steps=[f"Подготовьте продукты для «{title}».", "Приготовьте по классическому рецепту.", "Подавайте тёплым."],
                tags=[meal, cat],
                diets=["kids_friendly"],
                calories=350,
                protein=18,
            )
        )

    for spec in DRINK_SPECS:
        title, mtype, alc, servings, cal, kids, sport, event = spec
        out.append(
            _r(
                title,
                mtype,
                category="drink",
                cooking_time=5,
                servings=servings,
                ingredients=[
                    _ing("Вода", "200", "мл", "drinks"),
                    _ing("Основа напитка", "1", "порция", "drinks"),
                ],
                steps=[f"Смешайте ингредиенты для «{title}».", "Охладите и подавайте."],
                tags=[mtype, "напиток"],
                is_drink=True,
                is_alcoholic=alc,
                alcohol_percent=12.0 if alc else None,
                caffeine_mg=80.0 if mtype == "coffee" else None,
                suitable_children=kids,
                suitable_sport=sport,
                suitable_event=event,
                calories=cal,
            )
        )

    for spec in EVENT_SPECS:
        title, meal = spec[0], spec[1]
        event = bool(spec[2]) if len(spec) > 2 else False
        fasting = bool(spec[3]) if len(spec) > 3 else False
        kids = bool(spec[4]) if len(spec) > 4 else False
        bbq = bool(spec[5]) if len(spec) > 5 else False
        restrictions = ["fasting"] if fasting else []
        out.append(
            _r(
                title,
                meal,
                category="event" if event else ("bbq" if bbq else "main"),
                cooking_time=60 if bbq else 45,
                ingredients=[
                    _ing("Основной продукт", "500", "г"),
                    _ing("Специи", "1", "ч.л."),
                ],
                steps=[f"Подготовьте «{title}» для гостей.", "Подавайте на стол."],
                tags=["праздник" if event else "пост" if fasting else "дети" if kids else "барбекю"],
                suitable_event=event,
                suitable_children=kids or not event,
                restrictions=restrictions,
                calories=400,
            )
        )

    return out


CATALOG_RECIPES = build_catalog_recipes()
