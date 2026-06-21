"""Canonical PLANAM nutrition restrictions catalog — single source of truth."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

Severity = Literal["hard", "soft"]
RestrictionGroup = Literal[
    "religious_cultural",
    "medical_safety",
    "dietary",
    "allergen_bridge",
    "goal",
]


@dataclass(frozen=True)
class RestrictionDefinition:
    key: str
    label_ru: str
    group: str
    severity: Severity
    description_ru: str
    aliases: tuple[str, ...]
    banned_ingredient_markers: tuple[str, ...]
    warning_ingredient_markers: tuple[str, ...]


def _def(
    key: str,
    label_ru: str,
    group: str,
    severity: Severity,
    description_ru: str,
    *,
    aliases: tuple[str, ...] = (),
    banned: tuple[str, ...] = (),
    warning: tuple[str, ...] = (),
) -> RestrictionDefinition:
    return RestrictionDefinition(
        key=key,
        label_ru=label_ru,
        group=group,
        severity=severity,
        description_ru=description_ru,
        aliases=aliases,
        banned_ingredient_markers=banned,
        warning_ingredient_markers=warning,
    )


# Stable declaration order — used by list_restrictions().
_RESTRICTION_DEFINITIONS: tuple[RestrictionDefinition, ...] = (
    # --- religious_cultural ---
    _def(
        "no_pork",
        "Без свинины",
        "religious_cultural",
        "hard",
        "Исключение свинины и продуктов из неё.",
        aliases=(
            "без свинины",
            "свинина нельзя",
            "не ем свинину",
            "pork_free",
            "no pork",
            "no_pork",
        ),
        banned=(
            "свинина",
            "свиной",
            "свиная",
            "свиное",
            "бекон",
            "ветчина",
            "сало",
            "карбонат",
            "грудинка свиная",
            "корейка свиная",
            "колбаса свиная",
            "хамон",
            "прошутто",
        ),
    ),
    _def(
        "no_beef",
        "Без говядины",
        "religious_cultural",
        "hard",
        "Исключение говядины и телятины.",
        aliases=("без говядины", "no beef", "no_beef", "beef_free"),
        banned=("говядина", "говяжий", "телятина", "телячий"),
    ),
    _def(
        "halal",
        "Халяль",
        "religious_cultural",
        "hard",
        "Халяльное питание: без свинины, алкоголя и нехаляльных компонентов.",
        aliases=("халяль", "халал", "halal"),
        banned=(
            "свинина",
            "свиной",
            "бекон",
            "ветчина",
            "алкоголь",
            "вино",
            "пиво",
            "водка",
            "коньяк",
            "желатин",
        ),
    ),
    _def(
        "kosher",
        "Кошерное питание",
        "religious_cultural",
        "hard",
        "Кошерное питание: без свинины и не-кошерных морепродуктов.",
        aliases=("кошер", "кошерное", "kosher"),
        banned=(
            "свинина",
            "свиной",
            "бекон",
            "креветки",
            "мидии",
            "кальмар",
            "осьминог",
            "морепродукты",
        ),
        warning=("сыр", "молоко", "мясо"),
    ),
    _def(
        "no_alcohol",
        "Без алкоголя",
        "religious_cultural",
        "hard",
        "Исключение алкоголя и алкогольных ингредиентов.",
        aliases=(
            "без алкоголя",
            "alcohol_free",
            "no alcohol",
            "не употребляю алкоголь",
            "no_alcohol",
        ),
        banned=(
            "алкоголь",
            "вино",
            "пиво",
            "коньяк",
            "ром",
            "ликер",
            "ликёр",
            "водка",
            "виски",
            "бренди",
            "мартини",
        ),
    ),
    # --- medical_safety ---
    _def(
        "diabetes_friendly",
        "При диабете",
        "medical_safety",
        "soft",
        "Осторожность с сахаром и быстрыми углеводами.",
        aliases=("диабет", "при диабете", "diabetes", "diabetic", "diabetes_friendly"),
        warning=("сахар", "мёд", "мед", "сироп", "глюкоза", "сгущёнка", "варенье"),
    ),
    _def(
        "low_salt",
        "Меньше соли",
        "medical_safety",
        "soft",
        "Ограничение соли и очень солёных продуктов.",
        aliases=("мало соли", "без соли", "low salt", "low_salt", "малосольное"),
        warning=("соль", "соевый соус", "копчёный", "копченый", "солёная", "соленая"),
    ),
    _def(
        "low_sugar",
        "Меньше сахара",
        "medical_safety",
        "soft",
        "Ограничение добавленного сахара и сладостей.",
        aliases=("мало сахара", "без сахара", "low sugar", "low_sugar"),
        warning=("сахар", "мёд", "мед", "сироп", "глюкоза", "сгущёнка", "варенье", "конфитюр"),
    ),
    _def(
        "lactose_free",
        "Без лактозы",
        "medical_safety",
        "hard",
        "Исключение молочных продуктов с лактозой.",
        aliases=("без лактозы", "lactose free", "lactose_free", "lactose-free"),
        banned=(
            "молоко",
            "сливки",
            "сыр",
            "творог",
            "йогурт",
            "кефир",
            "сметана",
            "масло сливочное",
        ),
    ),
    _def(
        "gluten_free",
        "Без глютена",
        "medical_safety",
        "hard",
        "Исключение пшеницы и глютенсодержащих продуктов.",
        aliases=("без глютена", "gluten free", "gluten_free", "gluten-free"),
        banned=(
            "пшеница",
            "мука пшеничная",
            "хлеб",
            "батон",
            "булка",
            "сухари",
            "макароны",
            "паста",
            "лаваш",
            "панировка",
        ),
    ),
    _def(
        "pregnancy_safe",
        "Для беременности",
        "medical_safety",
        "soft",
        "Осторожность с сырыми/недостаточно термически обработанными продуктами.",
        aliases=("беременность", "для беременных", "pregnancy", "pregnancy_safe"),
        warning=("сырой", "сашими", "суши", "икра", "паштет", "субпродукты"),
    ),
    _def(
        "child_safe",
        "Подходит детям",
        "medical_safety",
        "soft",
        "Осторожность с острым, алкоголем и тяжёлыми добавками.",
        aliases=("детское", "для детей", "child safe", "child_safe"),
        warning=("острый", "чили", "перец чили", "алкоголь", "кофеин"),
    ),
    # --- dietary ---
    _def(
        "vegetarian",
        "Вегетарианское",
        "dietary",
        "hard",
        "Без мяса, птицы и рыбы.",
        aliases=("вегетарианство", "vegetarian", "veggie", "вегетарианское"),
        banned=(
            "мясо",
            "курица",
            "курин",
            "индейка",
            "говядина",
            "свинина",
            "баранина",
            "бекон",
            "ветчина",
            "рыба",
            "лосось",
            "тунец",
            "креветки",
            "морепродукты",
        ),
    ),
    _def(
        "vegan",
        "Веганское",
        "dietary",
        "hard",
        "Без продуктов животного происхождения.",
        aliases=("веган", "веганство", "vegan", "веганское"),
        banned=(
            "мясо",
            "курица",
            "курин",
            "индейка",
            "говядина",
            "свинина",
            "баранина",
            "бекон",
            "ветчина",
            "рыба",
            "лосось",
            "тунец",
            "креветки",
            "морепродукты",
            "молоко",
            "сливки",
            "сыр",
            "творог",
            "йогурт",
            "яйцо",
            "яйца",
            "мед",
            "мёд",
            "масло сливочное",
        ),
    ),
    _def(
        "pescatarian",
        "Пескетарианское",
        "dietary",
        "hard",
        "Без мяса и птицы; рыба и морепродукты допустимы.",
        aliases=("пескетарианство", "pescatarian", "пескетарианское"),
        banned=(
            "курица",
            "курин",
            "индейка",
            "говядина",
            "свинина",
            "баранина",
            "бекон",
            "ветчина",
        ),
    ),
    _def(
        "keto",
        "Кето",
        "dietary",
        "soft",
        "Низкоуглеводный режим; осторожность с сахаром и мукой.",
        aliases=("кето", "keto", "кетогенное"),
        warning=("сахар", "мука", "хлеб", "макароны", "рис", "картофель", "батон"),
    ),
    _def(
        "low_carb",
        "Низкоуглеводное",
        "dietary",
        "soft",
        "Ограничение быстрых углеводов.",
        aliases=("низкоуглеводное", "low carb", "low_carb", "low-carb"),
        warning=("сахар", "мука", "хлеб", "макароны", "рис", "картофель"),
    ),
    _def(
        "high_protein",
        "Высокобелковое",
        "dietary",
        "soft",
        "Акцент на белке; без жёстких запретов на Stage B.",
        aliases=("высокобелковое", "high protein", "high_protein", "много белка"),
    ),
    # --- goal ---
    _def(
        "weight_loss",
        "Похудение",
        "goal",
        "soft",
        "Цель похудения; без жёстких запретов на Stage B.",
        aliases=("похудение", "снижение веса", "weight loss", "weight_loss"),
    ),
    _def(
        "mass_gain",
        "Набор массы",
        "goal",
        "soft",
        "Цель набора массы; без жёстких запретов на Stage B.",
        aliases=("набор массы", "mass gain", "mass_gain", "набор веса"),
    ),
    _def(
        "healthy_eating",
        "Здоровое питание",
        "goal",
        "soft",
        "Общая цель здорового питания.",
        aliases=("здоровое питание", "healthy eating", "healthy_eating", "здоровье"),
    ),
    # --- allergen_bridge ---
    _def(
        "no_nuts",
        "Без орехов",
        "allergen_bridge",
        "hard",
        "Исключение орехов.",
        aliases=("без орехов", "no nuts", "no_nuts", "nut_free"),
        banned=("орех", "орехи", "миндаль", "фундук", "кешью", "грецкий орех", "арахис"),
    ),
    _def(
        "no_peanuts",
        "Без арахиса",
        "allergen_bridge",
        "hard",
        "Исключение арахиса.",
        aliases=("без арахиса", "no peanuts", "no_peanuts", "peanut_free"),
        banned=("арахис", "арахисовый"),
    ),
    _def(
        "no_eggs",
        "Без яиц",
        "allergen_bridge",
        "hard",
        "Исключение яиц и яичных продуктов.",
        aliases=("без яиц", "no eggs", "no_eggs", "egg_free"),
        banned=("яйцо", "яйца", "белок", "желток"),
    ),
    _def(
        "no_fish",
        "Без рыбы",
        "allergen_bridge",
        "hard",
        "Исключение рыбы.",
        aliases=("без рыбы", "no fish", "no_fish", "fish_free"),
        banned=("рыба", "лосось", "тунец", "треска", "хек", "минтай", "форель"),
    ),
    _def(
        "no_seafood",
        "Без морепродуктов",
        "allergen_bridge",
        "hard",
        "Исключение морепродуктов.",
        aliases=("без морепродуктов", "no seafood", "no_seafood", "seafood_free"),
        banned=("креветки", "мидии", "кальмар", "осьминог", "морепродукты"),
    ),
    _def(
        "no_soy",
        "Без сои",
        "allergen_bridge",
        "hard",
        "Исключение сои и соевых продуктов.",
        aliases=("без сои", "no soy", "no_soy", "soy_free"),
        banned=("соя", "соевый соус", "тофу"),
    ),
    _def(
        "no_milk",
        "Без молока",
        "allergen_bridge",
        "hard",
        "Исключение молока и молочных продуктов.",
        aliases=("без молока", "no milk", "no_milk", "milk_free"),
        banned=(
            "молоко",
            "сливки",
            "сыр",
            "творог",
            "йогурт",
            "кефир",
            "сметана",
            "масло сливочное",
        ),
    ),
)

_BY_KEY: dict[str, RestrictionDefinition] = {d.key: d for d in _RESTRICTION_DEFINITIONS}

_ALIAS_TO_KEY: dict[str, str] = {}
for _definition in _RESTRICTION_DEFINITIONS:
    _ALIAS_TO_KEY[_definition.key] = _definition.key
    _ALIAS_TO_KEY[_definition.key.lower()] = _definition.key
    for _alias in _definition.aliases:
        _ALIAS_TO_KEY[_alias.strip().lower()] = _definition.key


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().lower()
    return cleaned or None


def normalize_restriction_key(value: str | None) -> str | None:
    """Map alias or key to canonical restriction key; unknown values return None."""
    cleaned = _clean(value)
    if cleaned is None:
        return None
    return _ALIAS_TO_KEY.get(cleaned)


def normalize_restrictions(values: Iterable[str] | None) -> list[str]:
    """Normalize, dedupe, preserve first-seen stable order."""
    if not values:
        return []
    seen: set[str] = set()
    result: list[str] = []
    for raw in values:
        key = normalize_restriction_key(raw)
        if key is None or key in seen:
            continue
        seen.add(key)
        result.append(key)
    return result


def get_unknown_restrictions(values: Iterable[str] | None) -> list[str]:
    """Return raw values that could not be mapped to canonical keys."""
    if not values:
        return []
    unknown: list[str] = []
    seen: set[str] = set()
    for raw in values:
        if raw is None:
            continue
        text = str(raw).strip()
        if not text:
            continue
        if normalize_restriction_key(text) is not None:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unknown.append(text)
    return unknown


def get_restriction_definition(key: str) -> RestrictionDefinition | None:
    return _BY_KEY.get(key)


def list_restrictions() -> list[RestrictionDefinition]:
    return list(_RESTRICTION_DEFINITIONS)


def list_restrictions_for_ui() -> list[dict]:
    return [
        {
            "key": d.key,
            "label_ru": d.label_ru,
            "group": d.group,
            "severity": d.severity,
            "description_ru": d.description_ru,
        }
        for d in _RESTRICTION_DEFINITIONS
    ]
