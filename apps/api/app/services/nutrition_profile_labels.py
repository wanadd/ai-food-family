NUTRITION_GOAL_LABELS = {
    "maintain": "поддержание веса",
    "lose": "похудение",
    "gain": "набор массы",
    "healthy": "здоровое питание",
    "sport": "спортивный режим",
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
}
