#!/usr/bin/env python3
"""Nutrition facts (per 100 g) + unit conversion for PLANAM V1.

Pure data + pure functions (no DB). Used to estimate KБЖУ per ingredient row and
to refine nutrition_precision. Values are approximate reference values per 100 g
and are intentionally conservative — coverage and precision are surfaced in the
reports, never silently trusted.

Key principles:
* Never invent grams for to_taste / generic / unknown-unit rows.
* Volume->mass uses a density map (default 1.0 g/ml).
* Piece (шт) needs a per-product average weight; otherwise grams are unknown.
"""

from __future__ import annotations

from dataclasses import dataclass


def _norm(value: str) -> str:
    return (value or "").strip().lower().replace("ё", "е")


@dataclass(frozen=True)
class Facts:
    kcal: float
    protein: float
    fat: float
    carbs: float


# Per 100 g reference values (approximate). name (normalized) -> Facts.
NUTRITION_FACTS: dict[str, Facts] = {
    "соль": Facts(0, 0, 0, 0),
    "сахар": Facts(399, 0, 0, 99.7),
    "сахар коричневый": Facts(380, 0, 0, 98),
    "вода": Facts(0, 0, 0, 0),
    "лук репчатый": Facts(41, 1.4, 0, 8.2),
    "лук красный": Facts(42, 1.4, 0, 9),
    "лук белый": Facts(41, 1.4, 0, 8.2),
    "лук зеленый": Facts(20, 1.3, 0, 4.6),
    "лук-порей": Facts(36, 2, 0.2, 7.3),
    "масло растительное": Facts(884, 0, 99.9, 0),
    "масло подсолнечное": Facts(884, 0, 99.9, 0),
    "масло оливковое": Facts(898, 0, 99.8, 0),
    "масло сливочное": Facts(748, 0.5, 82.5, 0.8),
    "масло кунжутное": Facts(884, 0, 99.9, 0),
    "картофель": Facts(77, 2, 0.4, 16.3),
    "пюре картофельное": Facts(88, 2, 1.5, 15),
    "яйцо куриное": Facts(157, 12.7, 11.5, 0.7),
    "яйцо перепелиное": Facts(168, 11.9, 13.1, 0.6),
    "желток яичный": Facts(352, 16.2, 31.2, 1),
    "белок яичный": Facts(44, 11.1, 0, 0),
    "чеснок": Facts(143, 6.5, 0.5, 30),
    "морковь": Facts(35, 1.3, 0.1, 6.9),
    "майонез": Facts(627, 0.3, 67, 2.6),
    "перец болгарский": Facts(27, 1.3, 0, 5.3),
    "перец сладкий": Facts(27, 1.3, 0, 5.3),
    "помидор": Facts(20, 1.1, 0.2, 3.7),
    "помидоры черри": Facts(18, 0.9, 0.2, 3.9),
    "томатная паста": Facts(82, 4.3, 0.5, 19),
    "томаты в собственном соку": Facts(21, 1.1, 0.1, 4),
    "сыр твердый": Facts(364, 24, 30, 0),
    "сыр голландский": Facts(352, 26, 26.8, 0),
    "сыр полутвердый": Facts(350, 25, 27, 0),
    "пармезан": Facts(392, 38, 28, 0),
    "сыр плавленый": Facts(257, 16, 21, 2),
    "сыр творожный": Facts(253, 11, 22, 3),
    "сыр мягкий": Facts(290, 18, 24, 1),
    "сыр сулугуни": Facts(286, 20, 24, 0),
    "масло оливковое extra": Facts(898, 0, 99.8, 0),
    "соевый соус": Facts(50, 6, 0, 6),
    "петрушка": Facts(49, 3.7, 0.4, 7.6),
    "укроп": Facts(40, 2.5, 0.5, 6.3),
    "кинза": Facts(23, 2.1, 0.5, 3.7),
    "базилик": Facts(27, 3.2, 0.6, 4.3),
    "зелень": Facts(36, 2.8, 0.4, 5.8),
    "мука пшеничная": Facts(364, 10.3, 1.1, 76),
    "мука гречневая": Facts(353, 13, 1.2, 72),
    "огурец": Facts(15, 0.8, 0.1, 2.5),
    "огурец соленый": Facts(11, 0.8, 0.1, 1.7),
    "рис": Facts(344, 6.7, 0.7, 78),
    "сметана": Facts(206, 2.8, 20, 3.2),
    "сливки": Facts(206, 2.8, 20, 3.2),
    "молоко": Facts(60, 3, 3.2, 4.7),
    "молоко кокосовое": Facts(230, 2.3, 24, 6),
    "творог": Facts(121, 18, 5, 3),
    "йогурт": Facts(60, 5, 1.5, 7),
    "напиток кисломолочный": Facts(53, 2.9, 2.5, 4),
    "филе куриное": Facts(110, 23, 1.2, 0),
    "грудка куриная": Facts(113, 23.6, 1.9, 0.4),
    "курица": Facts(190, 18.2, 12.5, 0),
    "бедро куриное": Facts(185, 16, 14, 0),
    "голень куриная": Facts(158, 18, 9, 0),
    "окорочок куриный": Facts(185, 16, 14, 0),
    "крылья куриные": Facts(186, 19, 12, 0),
    "печень куриная": Facts(137, 19, 6, 0.7),
    "фарш мясной": Facts(254, 17, 20, 0),
    "фарш куриный": Facts(143, 17, 8, 0),
    "свинина": Facts(259, 16, 21, 0),
    "говядина": Facts(187, 18.9, 12.4, 0),
    "баранина": Facts(209, 16, 16, 0),
    "сало": Facts(797, 2.4, 89, 0),
    "бекон": Facts(500, 12, 50, 0),
    "ветчина": Facts(270, 14, 24, 0),
    "колбаса": Facts(301, 13, 27, 0),
    "сосиска": Facts(266, 11, 24, 1.5),
    "ребра свиные": Facts(277, 15, 24, 0),
    "сельдь": Facts(161, 16, 11, 0),
    "семга": Facts(208, 20, 13, 0),
    "лосось": Facts(208, 20, 13, 0),
    "горбуша": Facts(140, 21, 6, 0),
    "кета": Facts(127, 19, 5.6, 0),
    "треска": Facts(78, 17.7, 0.7, 0),
    "тунец": Facts(96, 22, 1, 0),
    "филе рыбное": Facts(100, 18, 3, 0),
    "рыба": Facts(120, 18, 5, 0),
    "креветки": Facts(95, 19, 2, 0),
    "кальмар": Facts(92, 18, 2.2, 0),
    "крабовые палочки": Facts(94, 6, 1, 15),
    "шпроты": Facts(363, 17, 32, 0),
    "хлеб": Facts(242, 8, 3, 48),
    "сухари панировочные": Facts(347, 11, 2, 72),
    "макаронные изделия": Facts(338, 10.4, 1.1, 71),
    "спагетти": Facts(338, 10.4, 1.1, 71),
    "вермишель": Facts(338, 10.4, 1.1, 71),
    "лапша": Facts(338, 10.4, 1.1, 71),
    "крупа гречневая": Facts(343, 12.6, 3.3, 62),
    "крупа перловая": Facts(320, 9.3, 1.1, 67),
    "крупа манная": Facts(333, 10.3, 1, 67),
    "пшено": Facts(348, 11.5, 3.3, 67),
    "хлопья овсяные": Facts(366, 11.9, 7.2, 62),
    "нут": Facts(364, 19, 6, 61),
    "фасоль": Facts(333, 21, 2, 54),
    "фасоль стручковая": Facts(24, 2, 0.2, 3.6),
    "кукуруза": Facts(86, 3.3, 1.2, 19),
    "горошек зеленый": Facts(81, 5, 0.4, 14),
    "грибы": Facts(22, 3.1, 0.3, 3.3),
    "шампиньоны": Facts(22, 4.3, 1, 0.1),
    "опята": Facts(22, 2.2, 1.2, 0.5),
    "вешенки": Facts(33, 3.3, 0.4, 6),
    "капуста белокочанная": Facts(28, 1.8, 0.1, 4.7),
    "капуста пекинская": Facts(16, 1.2, 0.2, 2),
    "капуста цветная": Facts(30, 2.5, 0.3, 4.2),
    "капуста брюссельская": Facts(43, 3.4, 0.3, 9),
    "брокколи": Facts(34, 2.8, 0.4, 7),
    "свекла": Facts(43, 1.6, 0.2, 9.6),
    "баклажан": Facts(24, 1, 0.1, 5.9),
    "кабачок": Facts(24, 0.6, 0.3, 4.6),
    "тыква": Facts(26, 1, 0.1, 4.4),
    "шпинат": Facts(23, 2.9, 0.4, 3.6),
    "листья салата": Facts(15, 1.4, 0.2, 2.9),
    "руккола": Facts(25, 2.6, 0.7, 3.7),
    "сельдерей черешковый": Facts(16, 0.7, 0.2, 3),
    "редька": Facts(36, 1.9, 0.2, 6.7),
    "репа": Facts(28, 1.5, 0.1, 6.2),
    "авокадо": Facts(160, 2, 15, 9),
    "яблоко": Facts(52, 0.4, 0.4, 14),
    "груша": Facts(57, 0.4, 0.3, 15),
    "банан": Facts(89, 1.1, 0.3, 23),
    "апельсин": Facts(47, 0.9, 0.2, 12),
    "лимон": Facts(29, 1.1, 0.3, 9),
    "виноград": Facts(69, 0.6, 0.2, 18),
    "киви": Facts(61, 1.1, 0.5, 15),
    "ананас": Facts(50, 0.5, 0.1, 13),
    "клубника": Facts(33, 0.7, 0.3, 8),
    "малина": Facts(52, 1.2, 0.7, 12),
    "гранат": Facts(83, 1.7, 1.2, 19),
    "абрикос": Facts(48, 1.4, 0.4, 11),
    "изюм": Facts(299, 3, 0.5, 79),
    "чернослив": Facts(231, 2.2, 0.4, 57),
    "финик": Facts(277, 1.8, 0.2, 75),
    "курага": Facts(241, 3.4, 0.5, 63),
    "орехи грецкие": Facts(654, 15, 65, 14),
    "арахис": Facts(567, 26, 49, 16),
    "кунжут": Facts(573, 18, 50, 23),
    "мед": Facts(304, 0.3, 0, 82),
    "уксус": Facts(18, 0, 0, 0.6),
    "горчица": Facts(143, 9.9, 4, 5),
    "кетчуп": Facts(112, 1.8, 0.5, 26),
    "соус": Facts(120, 2, 8, 9),
    "какао-порошок": Facts(289, 24, 15, 28),
    "крахмал картофельный": Facts(381, 0.1, 0, 91),
    "крахмал кукурузный": Facts(381, 0.3, 0, 91),
    "дрожжи": Facts(75, 12, 1.5, 9),
    "маслины": Facts(115, 0.8, 10.7, 6),
    "оливки зеленые": Facts(145, 1, 15, 4),
    "тофу": Facts(76, 8, 4.8, 1.9),
    # Spices / seasonings (ground); mostly used to_taste but support numeric rows.
    "перец черный": Facts(251, 10, 3.3, 38),
    "перец красный жгучий": Facts(318, 12, 17, 57),
    "перец чили": Facts(40, 1.9, 0.4, 9),
    "перец душистый": Facts(263, 6, 8.7, 50),
    "перец белый": Facts(296, 10.4, 2.1, 69),
    "паприка сладкая": Facts(282, 14, 13, 54),
    "куркума": Facts(354, 8, 10, 65),
    "кориандр": Facts(298, 12, 18, 55),
    "кумин": Facts(375, 18, 22, 44),
    "зира": Facts(375, 18, 22, 44),
    "корица": Facts(247, 4, 1.2, 81),
    "смесь перцев": Facts(255, 10, 3.3, 39),
    "сок лимонный": Facts(22, 0.4, 0.2, 6.9),
    "капуста морская": Facts(25, 0.9, 0.2, 3),
    "приправа": Facts(150, 9, 4, 20),
    "специи": Facts(150, 9, 4, 20),
}


# Volume unit -> millilitres.
VOLUME_UNIT_ML: dict[str, float] = {
    "мл": 1.0,
    "л": 1000.0,
    "ст.л.": 15.0,
    "ч.л.": 5.0,
    "стакан": 200.0,
}

# Density g/ml (default 1.0).
DENSITY: dict[str, float] = {
    "масло растительное": 0.92,
    "масло подсолнечное": 0.92,
    "масло оливковое": 0.92,
    "масло кунжутное": 0.92,
    "мед": 1.42,
    "молоко": 1.03,
    "соевый соус": 1.1,
    "сметана": 1.0,
}

# Average grams per piece (шт).
PIECE_WEIGHTS: dict[str, float] = {
    "яйцо куриное": 55,
    "яйцо перепелиное": 12,
    "картофель": 100,
    "лук репчатый": 75,
    "лук красный": 75,
    "лук белый": 75,
    "морковь": 75,
    "помидор": 120,
    "помидоры черри": 15,
    "огурец": 100,
    "перец болгарский": 150,
    "перец сладкий": 150,
    "баклажан": 250,
    "кабачок": 300,
    "яблоко": 180,
    "груша": 180,
    "банан": 120,
    "апельсин": 180,
    "лимон": 100,
    "киви": 75,
    "свекла": 150,
    "авокадо": 200,
    "капуста белокочанная": 1200,
    "капуста пекинская": 800,
    "хлеб": 500,
    "крабовые палочки": 17,
}

SPECIAL_UNIT_G: dict[str, float] = {
    "зубчик": 5.0,
    "пучок": 50.0,
}


def lookup_facts(name: str) -> Facts | None:
    return NUTRITION_FACTS.get(_norm(name))


def has_facts(name: str) -> bool:
    return _norm(name) in NUTRITION_FACTS


def _density(name: str) -> float:
    return DENSITY.get(_norm(name), 1.0)


def _to_float(quantity: str) -> float | None:
    value = (quantity or "").strip().replace(",", ".")
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def grams_for(name: str, quantity: str, unit: str) -> tuple[float | None, str]:
    """Return (grams, hint) where hint in exact|estimated|low_confidence|unavailable.

    grams is None when the quantity/unit can't be converted (never invented).
    """
    q = _to_float(quantity)
    u = (unit or "").strip().lower().replace("ё", "е")

    if u in {"г"} and q is not None:
        return q, "exact"
    if u in {"кг"} and q is not None:
        return q * 1000, "exact"
    if u in {"мл", "л"} and q is not None:
        return q * VOLUME_UNIT_ML[u] * _density(name), "exact"
    if u in {"ст.л.", "ч.л.", "стакан"} and q is not None:
        return q * VOLUME_UNIT_ML[u] * _density(name), "estimated"
    if u == "шт" and q is not None:
        weight = PIECE_WEIGHTS.get(_norm(name))
        if weight:
            return q * weight, "estimated"
        return None, "low_confidence"
    if u in SPECIAL_UNIT_G and q is not None:
        return q * SPECIAL_UNIT_G[u], "estimated"
    if u in {"щепотка"}:
        return 0.5, "low_confidence"
    if u in {"упаковка"}:
        return None, "low_confidence"
    return None, "unavailable"


@dataclass
class RowNutrition:
    grams: float | None
    kcal: float
    protein: float
    fat: float
    carbs: float
    precision: str
    has_facts: bool


def compute_row_nutrition(
    name: str,
    quantity: str,
    unit: str,
    *,
    category: str,
    generic: bool,
    is_to_taste: bool,
) -> RowNutrition:
    facts = lookup_facts(name)
    if generic or is_to_taste:
        return RowNutrition(None, 0, 0, 0, 0, "low_confidence", facts is not None)
    if facts is None:
        return RowNutrition(None, 0, 0, 0, 0, "unavailable", False)
    grams, hint = grams_for(name, quantity, unit)
    if grams is None:
        return RowNutrition(None, 0, 0, 0, 0, "low_confidence", True)
    factor = grams / 100.0
    return RowNutrition(
        grams=round(grams, 1),
        kcal=round(facts.kcal * factor, 1),
        protein=round(facts.protein * factor, 1),
        fat=round(facts.fat * factor, 1),
        carbs=round(facts.carbs * factor, 1),
        precision=hint,
        has_facts=True,
    )
