#!/usr/bin/env python3
"""Extract anonymized culinary signals from Povarenok candidates (Stage D).

Signals only — no recipe import, no original titles/steps in output.

Run from repository root:
    python backend/scripts/extract_povarenok_culinary_signals_v3.py \\
        --input exports/povarenok_candidates_100.jsonl \\
        --output exports/povarenok_culinary_signals_v3_100.jsonl \\
        --report reports/povarenok_culinary_signals_v3_report.md \\
        --limit 100 --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.nutrition.restrictions_catalog import list_restrictions  # noqa: E402

DEFAULT_INPUT = ROOT / "exports" / "povarenok_candidates_100.jsonl"
DEFAULT_OUTPUT = ROOT / "exports" / "povarenok_culinary_signals_v3_100.jsonl"
DEFAULT_REPORT = ROOT / "reports" / "povarenok_culinary_signals_v3_report.md"

FORBIDDEN_OUTPUT_KEYS = frozenset(
    {
        "title",
        "original_title",
        "steps",
        "original_steps",
        "source_url",
        "description",
        "original_description",
    }
)

ALCOHOL_PATTERNS = (
    r"\bалкогол",
    r"\bводк",
    r"\bвино\b",
    r"\bконьяк",
    r"\bром\b",
    r"\bликер",
    r"\bликёр",
    r"\bпиво\b",
    r"\bспирт",
    r"\bнастойк",
    r"\bналивк",
)
PRESERVE_PATTERNS = (
    r"на зиму",
    r"\bзаготов",
    r"\bконсерв",
    r"\bмаринад",
    r"\bсолень",
    r"\bваренье",
    r"\bджем\b",
    r"\bкомпот",
)
DESSERT_PATTERNS = (
    r"\bторт",
    r"\bпирожн",
    r"\bдесерт",
    r"\bкекс",
    r"\bмаффин",
    r"\bморожен",
    r"\bшоколад",
)
COMPLEX_BAKING_PATTERNS = (
    r"\bбисквит",
    r"\bслоен",
    r"\bслоён",
    r"\bзаварн",
    r"\bдрожжев",
    r"\bмастик",
)

PRODUCT_GROUP_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("мясо_птица", ("куриц", "курин", "индей", "грудк", "фарш кур", "утк", "гус")),
    ("мясо", ("говядин", "говяж", "телят", "баранин", "баран", "фарш мяс", "телят")),
    ("свинина", ("свинин", "свин", "свиные", "бекон", "ветчин", "ребр", "карбонат", "сало")),
    ("рыба", ("рыб", "лосос", "тунец", "горбуш", "зубатк", "треск", "минтай", "форел", "угр")),
    ("морепродукты", ("кревет", "мидии", "кальмар", "осьминог", "морепродукт")),
    ("молочные продукты", ("молок", "сыр", "творог", "сметан", "сливк", "йогурт", "кефир", "пармезан")),
    ("яйца", ("яйц", "желток", "белок яич")),
    ("крупы", ("рис", "греч", "перлов", "булгур", "овсян", "пшено", "киноа")),
    ("паста", ("макарон", "паста", "спагетти", "лапш")),
    ("овощи", ("картоф", "морков", "капуст", "баклажан", "кабач", "цукини", "свекл", "огурц", "помидор", "перец", "лук", "чеснок", "сельдер", "гриб", "шампиньон")),
    ("фрукты/ягоды", ("яблок", "груш", "банан", "киви", "ягод", "лимон", "апельсин")),
    ("сладкое", ("сахар", "мёд", "мед", "варень", "сироп", "шоколад")),
    ("выпечка/тесто", ("мука", "тесто", "хлеб", "сухар", "дрожж")),
    ("бобовые", ("фасол", "горох", "чечев", "нут", "соя", "тофу")),
    ("орехи", ("орех", "арахис", "миндаль", "кешью", "фундук")),
)

INGREDIENT_LEMMA_RULES: tuple[tuple[str, str], ...] = (
    (r"яйца$", "яйцо"),
    (r"яйцо\b", "яйцо"),
    (r"баклажаны$", "баклажан"),
    (r"помидоры$", "помидор"),
    (r"огурцы$", "огурец"),
    (r"грибы$", "гриб"),
)

ALLERGEN_MARKERS: dict[str, tuple[str, ...]] = {
    "milk": ("молок", "сыр", "творог", "сметан", "сливк", "йогурт", "кефир", "пармезан"),
    "eggs": ("яйц", "желток"),
    "fish": ("рыб", "лосос", "тунец", "горбуш", "зубатк", "угр"),
    "seafood": ("кревет", "мидии", "кальмар", "осьминог"),
    "nuts": ("орех", "арахис", "миндаль", "кешью"),
    "soy": ("соя", "тофу", "соевый соус"),
    "gluten": ("мука", "хлеб", "макарон", "паста", "сухар", "тесто"),
}

RESTRICTION_MARKERS: dict[str, tuple[str, ...]] = {
    key: definition.banned_ingredient_markers
    for key, definition in ((d.key, d) for d in list_restrictions())
    if definition.banned_ingredient_markers
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract Povarenok culinary signals (no recipe import)"
    )
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="When true (default), do not write output JSONL",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write output JSONL and report (local files only, no DB)",
    )
    return parser.parse_args()


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def hash_source_record(record: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "source": record.get("source"),
            "url": record.get("source_url"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ingredient_names(record: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for item in record.get("ingredients") or []:
        if isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            if name:
                names.append(name)
    return names


def normalize_ingredient_name(raw: str) -> str:
    text = normalize_text(raw)
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"[^\wа-яё\s-]", " ", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\b(\d+([.,]\d+)?)\b",
        " ",
        text,
    )
    unit_pattern = re.compile(
        r"\b(?:г|кг|мл|л|шт|ст|ч\.?\s*л\.?|щепот|пуч|зуб|стак|бан|пакет|веточ)\b",
        flags=re.IGNORECASE,
    )
    text = unit_pattern.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    for pattern, lemma in INGREDIENT_LEMMA_RULES:
        text = re.sub(pattern, lemma, text)
    # drop leading adjectives like "крупа гречневая" -> keep meaningful tail
    parts = [p for p in text.split() if len(p) > 2]
    if len(parts) >= 2 and parts[0] in {"крупа", "масло", "фарш", "пюре", "сок"}:
        text = " ".join(parts[1:])
    return text.strip() or normalize_text(raw)[:40]


def detect_product_groups(names: list[str]) -> list[str]:
    combined = " ".join(normalize_ingredient_name(n) for n in names)
    groups: list[str] = []
    for group, patterns in PRODUCT_GROUP_RULES:
        if any(p in combined for p in patterns):
            groups.append(group)
    return groups


def detect_cooking_methods(title_text: str, ingredient_text: str) -> list[str]:
    text = f"{title_text} {ingredient_text}"
    methods: list[str] = []
    rules = (
        ("запекание", (r"запек", r"духовк", r"запеч")),
        ("жарка", (r"жар", r"сковород", r"обжар")),
        ("тушение", (r"туш", r"потуш")),
        ("варка", (r"вар", r"отвар", r"бульон")),
        ("салат/смешивание", (r"салат", r"смеш")),
        ("суп", (r"суп", r"борщ", r"щи\b", r"бульон")),
        ("выпечка", (r"выпеч", r"печь", r"тесто", r"мука")),
        ("маринование", (r"марин", r"замоч")),
        ("котлеты/формование", (r"котлет", r"тефтел", r"фарш", r"форм")),
        ("фаршировка", (r"фаршир", r"начин")),
    )
    for label, patterns in rules:
        if matches_any(text, patterns):
            methods.append(label)
    return methods or ["смешанная техника"]


def detect_dish_family(title_text: str, methods: list[str]) -> str:
    if matches_any(title_text, (r"салат",)):
        return "салат"
    if matches_any(title_text, (r"суп", r"борщ", r"щи\b")):
        return "суп"
    if matches_any(title_text, (r"котлет", r"тефтел")):
        return "котлеты"
    if matches_any(title_text, (r"запеканк",)):
        return "запеканка"
    if matches_any(title_text, (r"каша", r"гречк", r"рис\b")):
        return "гарнир/крупа"
    if matches_any(title_text, (r"омлет", r"яичниц", r"сырник")):
        return "яичное блюдо"
    if matches_any(title_text, (r"паста", r"макарон")):
        return "паста"
    if "суп" in methods:
        return "суп"
    if "салат/смешивание" in methods:
        return "салат"
    return "семейное горячее"


def detect_meal_type_hints(title_text: str, dish_family: str) -> list[str]:
    hints: list[str] = []
    if matches_any(title_text, (r"завтрак", r"омлет", r"каша", r"сырник")):
        hints.append("breakfast")
    if dish_family in {"салат", "суп", "котлеты", "семейное горячее", "паста", "гарнир/крупа"}:
        hints.extend(["lunch", "dinner"])
    if dish_family == "салат":
        hints.append("snack")
    if matches_any(title_text, DESSERT_PATTERNS):
        hints.append("dessert")
    if dish_family == "суп":
        hints.append("soup")
    if dish_family == "салат":
        hints.append("salad")
    # dedupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for h in hints:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out or ["lunch", "dinner"]


def detect_category_hints(dish_family: str, meal_hints: list[str]) -> list[str]:
    if dish_family == "салат":
        return ["side", "salad"]
    if dish_family == "суп":
        return ["main", "soup"]
    if dish_family in {"гарнир/крупа"}:
        return ["side"]
    if "dessert" in meal_hints:
        return ["dessert"]
    return ["main"]


def ingredient_count_bucket(count: int) -> str:
    if count <= 3:
        return "1-3"
    if count <= 7:
        return "4-7"
    if count <= 12:
        return "8-12"
    return "13+"


def detect_complexity(count: int, methods: list[str], flags: list[str]) -> str:
    if "complex_baking" in flags or count > 12:
        return "hard"
    if count <= 5 and len(methods) <= 2:
        return "easy"
    if count <= 10:
        return "medium"
    return "hard"


def detect_time_bucket(title_text: str, complexity: str) -> str:
    if matches_any(title_text, (r"быстр", r"5 мин", r"10 мин", r"15 мин", r"20 мин")):
        return "до 20 минут"
    if matches_any(title_text, (r"духовк", r"запек", r"туш")):
        return "40-60 минут"
    if complexity == "easy":
        return "20-40 минут"
    if complexity == "hard":
        return "60+ минут"
    return "20-40 минут"


def detect_equipment_hints(methods: list[str]) -> list[str]:
    hints: list[str] = []
    if "запекание" in methods:
        hints.append("духовка")
    if any(m in methods for m in ("жарка", "тушение", "котлеты/формование")):
        hints.append("сковорода")
    if any(m in methods for m in ("варка", "суп")):
        hints.append("кастрюля")
    return hints or ["базовая кухня"]


def detect_allergen_hints(names: list[str]) -> list[str]:
    combined = " ".join(normalize_ingredient_name(n) for n in names)
    hints: list[str] = []
    for code, patterns in ALLERGEN_MARKERS.items():
        if any(p in combined for p in patterns):
            hints.append(code)
    return hints


def detect_restriction_hints(names: list[str]) -> list[str]:
    combined = " ".join(normalize_ingredient_name(n) for n in names)
    hints: list[str] = []
    for key, markers in RESTRICTION_MARKERS.items():
        if any(m.lower() in combined for m in markers):
            hints.append(key)
    return sorted(set(hints))


def detect_nutrition_style_hints(groups: list[str], title_text: str) -> list[str]:
    hints: list[str] = []
    if "мясо_птица" in groups or "рыба" in groups:
        hints.append("high_protein")
    if "овощи" in groups and not {"мясо", "мясо_птица", "рыба"} & set(groups):
        hints.append("vegetable_forward")
    if not hints:
        hints.append("balanced")
    return hints


def detect_seasonality_hints(title_text: str, names: list[str]) -> list[str]:
    text = f"{title_text} {' '.join(names)}"
    hints: list[str] = []
    if matches_any(text, (r"летн", r"свеж", r"огурц", r"помидор", r"кабач")):
        hints.append("лето")
    if matches_any(text, (r"осен", r"тыкв", r"гриб")):
        hints.append("осень")
    if matches_any(text, (r"зим", r"согрев")):
        hints.append("зима")
    return hints or ["круглый год"]


def detect_quality_flags(
    title_text: str,
    names: list[str],
    *,
    ingredient_count: int,
    has_steps: bool,
) -> list[str]:
    combined = f"{title_text} {' '.join(normalize_ingredient_name(n) for n in names)}"
    flags: list[str] = []
    if matches_any(combined, (r"свинин", r"бекон", r"ветчин", r"ребр")):
        flags.append("has_pork")
    if matches_any(combined, ALCOHOL_PATTERNS):
        flags.append("has_alcohol")
    if matches_any(title_text, DESSERT_PATTERNS):
        flags.append("likely_dessert")
    if matches_any(combined, PRESERVE_PATTERNS):
        flags.append("likely_preserve")
    if matches_any(title_text, COMPLEX_BAKING_PATTERNS):
        flags.append("complex_baking")
    if ingredient_count < 3:
        flags.append("too_few_ingredients")
    if ingredient_count > 20:
        flags.append("too_many_ingredients")
    if not has_steps:
        flags.append("missing_steps")
    if re.search(r"[«\"“].+[»\"”]", str(title_text)):
        flags.append("high_originality_risk")
    if matches_any(
        title_text,
        (r"\bцезарь\b", r"\bвенеция\b", r"\bфантазия\b", r"«|»|\""),
    ):
        flags.append("high_originality_risk")
    if not flags and ingredient_count >= 4:
        flags.append("good_family_candidate")
    if len(flags) <= 1 and ingredient_count < 4:
        flags.append("weak_signal")
    return sorted(set(flags))


def detect_avoid(
    title_text: str,
    names: list[str],
    flags: list[str],
    *,
    ingredient_count: int,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    combined = f"{title_text} {' '.join(names)}"
    if "has_alcohol" in flags or matches_any(combined, ALCOHOL_PATTERNS):
        reasons.append("alcohol_or_tincture")
    if "likely_preserve" in flags:
        reasons.append("preserves_or_winter")
    if "likely_dessert" in flags:
        reasons.append("dessert_focus")
    if "complex_baking" in flags:
        reasons.append("complex_baking")
    if "too_few_ingredients" in flags:
        reasons.append("too_few_ingredients")
    if "too_many_ingredients" in flags:
        reasons.append("too_many_ingredients")
    if "high_originality_risk" in flags:
        reasons.append("high_originality_risk")
    if matches_any(title_text, (r"\bпаштет\b", r"икра\b", r"экзот")):
        reasons.append("not_everyday_family")
    return bool(reasons), reasons


def family_fit(flags: list[str], avoid: bool) -> str:
    if avoid:
        return "low"
    if "good_family_candidate" in flags:
        return "high"
    if "weak_signal" in flags:
        return "low"
    return "medium"


def build_generation_prompt_hints(
    dish_family: str,
    main_groups: list[str],
    methods: list[str],
) -> list[str]:
    protein = next((g for g in main_groups if g in {"мясо_птица", "рыба", "бобовые"}), None)
    base = ", ".join(main_groups[:3]) or "продуктов"
    hints = [
        f"сделать оригинальное семейное блюдо ({dish_family}) на основе {base}",
        "не использовать оригинальное название и порядок действий источника",
    ]
    if protein:
        hints.append(f"сохранить белковую базу ({protein}), но с новой подачей")
    if methods:
        hints.append(f"техника: {', '.join(methods[:2])}")
    return hints


def extract_signal_from_record(
    record: dict[str, Any],
    *,
    index: int,
) -> tuple[dict[str, Any] | None, str | None]:
    """Return (signal, skip_reason)."""
    names = ingredient_names(record)
    if not names:
        return None, "empty_ingredients"

    title_text = normalize_text(record.get("title"))
    ingredient_text = " ".join(normalize_ingredient_name(n) for n in names)
    normalized_names = sorted(
        {normalize_ingredient_name(n) for n in names if normalize_ingredient_name(n)}
    )[:20]

    groups = detect_product_groups(names)
    main_groups = groups[:3]
    secondary_groups = groups[3:6]
    methods = detect_cooking_methods(title_text, ingredient_text)
    dish_family = detect_dish_family(title_text, methods)
    meal_hints = detect_meal_type_hints(title_text, dish_family)
    category_hints = detect_category_hints(dish_family, meal_hints)
    steps = record.get("steps") or []
    has_steps = bool(steps)
    ingredient_count = len(names)
    flags = detect_quality_flags(
        title_text,
        names,
        ingredient_count=ingredient_count,
        has_steps=has_steps,
    )
    avoid, avoid_reasons = detect_avoid(
        title_text,
        names,
        flags,
        ingredient_count=ingredient_count,
    )
    complexity = detect_complexity(ingredient_count, methods, flags)
    time_bucket = detect_time_bucket(title_text, complexity)
    allergen_hints = detect_allergen_hints(names)
    restriction_hints = detect_restriction_hints(names)
    if "свинина" in groups and "no_pork" not in restriction_hints:
        restriction_hints.append("no_pork")
    if "молочные продукты" in groups and "milk" not in allergen_hints:
        allergen_hints.append("milk")
    if "яйца" in groups and "eggs" not in allergen_hints:
        allergen_hints.append("eggs")
    restriction_hints = sorted(set(restriction_hints))
    allergen_hints = sorted(set(allergen_hints))
    nutrition_hints = detect_nutrition_style_hints(groups, title_text)
    seasonality = detect_seasonality_hints(title_text, names)
    shopping = [g for g in groups if g in {"овощи", "мясо_птица", "мясо", "рыба", "крупы", "молочные продукты"}]

    signal: dict[str, Any] = {
        "signal_id": f"pov_sig_{index:06d}",
        "source_type": "povarenok_signal",
        "source_record_hash": hash_source_record(record),
        "originality_policy": {
            "no_original_title": True,
            "no_original_steps": True,
            "no_direct_import": True,
            "signals_only": True,
        },
        "dish_family": dish_family,
        "meal_type_hints": meal_hints,
        "category_hints": category_hints,
        "main_product_groups": main_groups,
        "secondary_product_groups": secondary_groups,
        "cooking_methods": methods,
        "equipment_hints": detect_equipment_hints(methods),
        "complexity": complexity,
        "family_fit": family_fit(flags, avoid),
        "time_bucket": time_bucket,
        "nutrition_style_hints": nutrition_hints,
        "restriction_hints": restriction_hints,
        "allergen_hints": allergen_hints,
        "shopping_category_hints": shopping or groups[:3],
        "seasonality_hints": seasonality,
        "avoid_for_planam": avoid,
        "avoid_reasons": avoid_reasons,
        "quality_flags": flags,
        "ingredient_count_bucket": ingredient_count_bucket(ingredient_count),
        "raw_ingredient_names_normalized": normalized_names,
        "generation_prompt_hints": build_generation_prompt_hints(
            dish_family,
            main_groups,
            methods,
        ),
    }

    violation = validate_output_signal(signal, source_title=record.get("title"))
    if violation:
        return None, f"originality_violation:{violation}"

    return signal, None


def validate_output_signal(
    signal: dict[str, Any],
    *,
    source_title: str | None = None,
) -> str | None:
    """Return violation reason or None if safe."""
    for key in signal:
        if key in FORBIDDEN_OUTPUT_KEYS:
            return f"forbidden_key:{key}"

    def walk(obj: Any, path: str = "") -> str | None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in FORBIDDEN_OUTPUT_KEYS:
                    return f"forbidden_nested_key:{path}.{k}" if path else f"forbidden_nested_key:{k}"
                err = walk(v, f"{path}.{k}" if path else k)
                if err:
                    return err
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                err = walk(item, f"{path}[{i}]")
                if err:
                    return err
        elif isinstance(obj, str):
            text = obj.strip()
            if "povarenok.ru" in text.lower():
                return "exposed_source_url"
            if source_title:
                title = str(source_title).strip()
                if len(title) >= 8 and title.lower() in text.lower():
                    return "leaked_source_title"
                # long distinctive phrase from title
                quoted = re.findall(r"[«\"“](.+?)[»\"”]", title)
                for part in quoted:
                    if len(part) >= 5 and part.lower() in text.lower():
                        return "leaked_quoted_title"
        return None

    return walk(signal)


def validate_signals_batch(
    signals: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> list[str]:
    violations: list[str] = []
    for signal, record in zip(signals, records, strict=False):
        err = validate_output_signal(signal, source_title=record.get("title"))
        if err:
            violations.append(f"{signal.get('signal_id')}: {err}")
    return violations


def read_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
            if len(rows) >= limit:
                break
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_report_markdown(
    *,
    input_path: Path,
    output_path: Path,
    report_path: Path,
    branch: str,
    commit: str,
    total_read: int,
    signals_written: int,
    skipped: int,
    skip_reasons: Counter[str],
    signals: list[dict[str, Any]],
    originality_ok: bool,
    originality_violations: list[str],
    sample_size: int,
    dry_run: bool,
) -> str:
    avoid_count = sum(1 for s in signals if s.get("avoid_for_planam"))
    flag_counter: Counter[str] = Counter()
    dish_counter: Counter[str] = Counter()
    meal_counter: Counter[str] = Counter()
    group_counter: Counter[str] = Counter()
    restriction_counter: Counter[str] = Counter()
    allergen_counter: Counter[str] = Counter()

    for signal in signals:
        dish_counter[signal.get("dish_family", "unknown")] += 1
        for flag in signal.get("quality_flags") or []:
            flag_counter[flag] += 1
        for meal in signal.get("meal_type_hints") or []:
            meal_counter[meal] += 1
        for group in signal.get("main_product_groups") or []:
            group_counter[group] += 1
        for rh in signal.get("restriction_hints") or []:
            restriction_counter[rh] += 1
        for ah in signal.get("allergen_hints") or []:
            allergen_counter[ah] += 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Povarenok Culinary Signals V3 Report",
        "",
        f"**Generated:** {now}",
        f"**Branch:** `{branch}`",
        f"**Commit:** `{commit}`",
        f"**Mode:** `{'dry-run' if dry_run else 'apply'}`",
        "",
        "## Files",
        "",
        f"- Input: `{input_path}`",
        f"- Output: `{output_path}`",
        f"- Report: `{report_path}`",
        "",
        "## Summary",
        "",
        f"- Records read: `{total_read}`",
        f"- Signals written: `{signals_written}`",
        f"- Skipped: `{skipped}`",
        f"- avoid_for_planam: `{avoid_count}`",
        f"- Originality safety: `{'PASS' if originality_ok else 'FAIL'}`",
        "",
        "## Skip reasons",
        "",
    ]
    if skip_reasons:
        for reason, count in skip_reasons.most_common():
            lines.append(f"- {reason}: `{count}`")
    else:
        lines.append("- none")

    def _dist_section(title: str, counter: Counter[str]) -> None:
        lines.extend(["", f"## {title}", ""])
        if counter:
            for key, count in counter.most_common():
                lines.append(f"- {key}: `{count}`")
        else:
            lines.append("- none")

    _dist_section("Quality flags", flag_counter)
    _dist_section("Dish family", dish_counter)
    _dist_section("Meal type hints", meal_counter)
    _dist_section("Product groups", group_counter)
    _dist_section("Restriction hints", restriction_counter)
    _dist_section("Allergen hints", allergen_counter)

    if originality_violations:
        lines.extend(["", "## Originality violations", ""])
        for v in originality_violations[:20]:
            lines.append(f"- {v}")

    lines.extend(["", f"## Sample signals ({min(sample_size, len(signals))})", ""])
    for signal in signals[:sample_size]:
        lines.append("```json")
        lines.append(json.dumps(signal, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")

    lines.extend(
        [
            "## Not done",
            "",
            "- Recipe import",
            "- Recipe generation",
            "- Photo generation",
            "- DB changes",
            "- Safe reset",
            "",
        ]
    )
    return "\n".join(lines)


def run_extraction(
    *,
    input_path: Path,
    output_path: Path,
    report_path: Path,
    limit: int,
    sample_size: int,
    dry_run: bool,
) -> dict[str, Any]:
    records = read_jsonl(input_path, limit)
    signals: list[dict[str, Any]] = []
    source_records: list[dict[str, Any]] = []
    skip_reasons: Counter[str] = Counter()

    for idx, record in enumerate(records, start=1):
        signal, skip = extract_signal_from_record(record, index=idx)
        if skip:
            skip_reasons[skip] += 1
            continue
        assert signal is not None
        signals.append(signal)
        source_records.append(record)

    originality_violations = validate_signals_batch(signals, source_records)
    originality_ok = not originality_violations

    if not dry_run:
        write_jsonl(output_path, signals)

    return {
        "total_read": len(records),
        "signals_written": len(signals),
        "skipped": len(records) - len(signals),
        "skip_reasons": skip_reasons,
        "signals": signals,
        "originality_ok": originality_ok,
        "originality_violations": originality_violations,
        "dry_run": dry_run,
        "output_path": output_path,
        "report_path": report_path,
        "input_path": input_path,
        "sample_size": sample_size,
    }


def git_meta() -> tuple[str, str]:
    import subprocess

    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=ROOT,
            text=True,
        ).strip()
        commit = subprocess.check_output(
            ["git", "log", "-1", "--oneline"],
            cwd=ROOT,
            text=True,
        ).strip()
        return branch, commit
    except Exception:
        return "unknown", "unknown"


def main() -> int:
    args = parse_args()
    dry_run = args.dry_run and not args.apply

    result = run_extraction(
        input_path=Path(args.input),
        output_path=Path(args.output),
        report_path=Path(args.report),
        limit=args.limit,
        sample_size=args.sample_size,
        dry_run=dry_run,
    )

    branch, commit = git_meta()
    report_md = build_report_markdown(
        input_path=result["input_path"],
        output_path=result["output_path"],
        report_path=result["report_path"],
        branch=branch,
        commit=commit,
        total_read=result["total_read"],
        signals_written=result["signals_written"],
        skipped=result["skipped"],
        skip_reasons=result["skip_reasons"],
        signals=result["signals"],
        originality_ok=result["originality_ok"],
        originality_violations=result["originality_violations"],
        sample_size=result["sample_size"],
        dry_run=result["dry_run"],
    )

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_md, encoding="utf-8")

    print(f"records_read={result['total_read']}")
    print(f"signals_written={result['signals_written']}")
    print(f"skipped={result['skipped']}")
    print(f"originality_ok={result['originality_ok']}")
    print(f"dry_run={result['dry_run']}")
    if result["skip_reasons"]:
        print("skip_reasons=" + json.dumps(dict(result["skip_reasons"]), ensure_ascii=False))

    if not result["originality_ok"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
