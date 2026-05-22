GOAL_LABELS = {
    "health": "здоровье",
    "weight": "контроль веса",
    "time": "экономия времени",
    "family": "семейные обеды",
    "variety": "разнообразие",
    "budget": "экономия бюджета",
}

DIET_LABELS = {
    "none": "без особенностей",
    "vegetarian": "вегетарианство",
    "vegan": "веганство",
    "keto": "кето",
    "paleo": "палео",
    "halal": "халяль",
    "kosher": "кошер",
    "pescatarian": "пескетарианство",
}

ALLERGY_LABELS = {
    "none": "нет аллергий",
    "nuts": "орехи",
    "dairy": "молочные",
    "gluten": "глютен",
    "eggs": "яйца",
    "seafood": "морепродукты",
    "soy": "соя",
    "honey": "мёд",
}

RESTRICTION_LABELS = {
    "none": "без ограничений",
    "low_sugar": "меньше сахара",
    "low_salt": "меньше соли",
    "no_pork": "без свинины",
    "organic": "органические продукты",
    "no_spicy": "без острого",
    "kids_friendly": "подходит детям",
}

# Member restrictions may include allergy codes; merge for label lookup.
MEMBER_RESTRICTION_LABELS = {**RESTRICTION_LABELS, **ALLERGY_LABELS}

BUDGET_LABELS = {
    "economy": "эконом (до 500 ₽/день)",
    "medium": "средний (500–900 ₽/день)",
    "premium": "премиум (900+ ₽/день)",
}

COOKING_TIME_LABELS = {
    "15": "до 15 минут",
    "30": "до 30 минут",
    "45": "до 45 минут",
    "60": "до 60 минут",
    "60plus": "60+ минут",
}

VARIANT_META = {
    "quick": {
        "title": "Быстрое меню",
        "tagline": "Минимум времени у плиты",
    },
    "economy": {
        "title": "Экономное меню",
        "tagline": "Выгодные продукты на всю семью",
    },
    "balanced": {
        "title": "Сбалансированное меню",
        "tagline": "Баланс питательности и вкуса",
    },
}


def label_map(values: list[str], mapping: dict[str, str]) -> list[str]:
    return [mapping.get(value, value) for value in values if value and value != "none"]
