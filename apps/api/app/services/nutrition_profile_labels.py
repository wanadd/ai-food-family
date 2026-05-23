NUTRITION_GOAL_LABELS = {
    "maintain": "Поддержание веса",
    "lose": "Похудение",
    "gain": "Набор массы",
    "healthy": "Здоровое питание",
    "sport": "Спортивный режим",
    "child": "Детское питание",
    "gentle": "Щадящее питание",
    "therapeutic": "Лечебное питание",
    "other": "Другое",
}

ACTIVITY_LABELS = {
    "low": "низкая активность",
    "medium": "средняя активность",
    "high": "высокая активность",
    "training": "регулярные тренировки",
}

GENDER_LABELS = {
    "male": "мужской",
    "female": "женский",
    "other": "другой",
    "prefer_not": "не указывать",
}

DISH_COMPLEXITY_LABELS = {
    "simple": "простые блюда",
    "medium": "средняя сложность",
    "advanced": "сложные блюда",
}

# Maps nutrition goal to legacy menu goal codes
NUTRITION_GOAL_TO_LEGACY_GOALS: dict[str, list[str]] = {
    "maintain": ["weight"],
    "lose": ["weight"],
    "gain": ["health"],
    "healthy": ["health"],
    "sport": ["health"],
    "child": ["family"],
    "gentle": ["health"],
    "therapeutic": ["health"],
    "other": ["health"],
}
