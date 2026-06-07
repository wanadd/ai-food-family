#!/usr/bin/env python3
"""Read-only audit of recipe ingredient quality (PLANAM V1).

STRICTLY READ-ONLY: runs SELECT queries only. It NEVER updates, inserts,
deletes, alters, migrates, or normalizes anything. It only reads the DB and
writes report files under ``reports/``.

Purpose: measure how ready the ingredient base is for future normalization,
canonical products, shopping-list grouping, KБЖУ (nutrition) and the photo
prompt pipeline.

Run from the repository root (or inside the api container):
    python backend/scripts/audit_recipe_ingredients.py
    python backend/scripts/audit_recipe_ingredients.py --database-url postgresql://...

Requires DATABASE_URL (or --database-url).
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
DEFAULT_MD_REPORT = ROOT / "reports" / "planam_v1_ingredient_quality_report.md"
DEFAULT_JSON_REPORT = ROOT / "reports" / "planam_v1_ingredient_quality.json"

# ---------------------------------------------------------------------------
# Vocabularies (audit heuristics — NOT applied to the DB)
# ---------------------------------------------------------------------------

# Names too generic to map to a single canonical product / nutrition profile.
GENERIC_NAMES = frozenset(
    {
        "овощи",
        "зелень",
        "специи",
        "приправы",
        "приправа",
        "мясо",
        "рыба",
        "сыр",
        "фрукты",
        "ягоды",
        "грибы",
        "орехи",
        "крупа",
        "крупы",
        "соус",
        "соусы",
        "бульон",
        "масло",
        "мука",
        "сахар",
        "молоко",
        "морепродукты",
        "колбаса",
        "консервы",
        "начинка",
        "украшение",
        "ингредиенты",
        "продукты",
    }
)

# Canonical units we want long term.
CANONICAL_UNITS = frozenset(
    {"г", "кг", "мл", "л", "шт", "ст.л.", "ч.л.", "стакан", "зубчик", "щепотка", "упаковка"}
)

# Dirty unit spelling -> canonical suggestion (audit-only mapping).
UNIT_ALIASES: dict[str, str] = {
    "гр": "г",
    "гр.": "г",
    "г.": "г",
    "грамм": "г",
    "граммов": "г",
    "грамма": "г",
    "килограмм": "кг",
    "кг.": "кг",
    "мл.": "мл",
    "л.": "л",
    "литр": "л",
    "литра": "л",
    "ст.л": "ст.л.",
    "ст. л.": "ст.л.",
    "стл": "ст.л.",
    "столовая ложка": "ст.л.",
    "столовых ложек": "ст.л.",
    "ст.ложка": "ст.л.",
    "ч.л": "ч.л.",
    "ч. л.": "ч.л.",
    "чайная ложка": "ч.л.",
    "чл": "ч.л.",
    "ложка": "ст.л.",
    "ложки": "ст.л.",
    "шт.": "шт",
    "штук": "шт",
    "штука": "шт",
    "штуки": "шт",
    "зуб.": "зубчик",
    "зубчика": "зубчик",
    "зубчиков": "зубчик",
    "пакетик": "упаковка",
    "пакет": "упаковка",
    "пач.": "упаковка",
    "пачка": "упаковка",
    "банка": "упаковка",
    "стак.": "стакан",
}

# Quantity tokens that are not real numbers.
NON_NUMERIC_QUANTITY = frozenset(
    {
        "",
        "0",
        "по вкусу",
        "немного",
        "щепотка",
        "щепотку",
        "пара",
        "несколько",
        "горсть",
        "на глаз",
        "чуть",
        "капля",
        "по желанию",
    }
)

# Ambiguous head nouns: same first word, but different products underneath.
AMBIGUOUS_HEADS = frozenset(
    {"перец", "масло", "лук", "уксус", "мука", "сахар", "соус", "сыр", "капуста", "фасоль"}
)

_QUANTITY_RE = re.compile(r"^\d+([.,]\d+)?([/-]\d+([.,]\d+)?)?$")


def normalize_key(name: str) -> str:
    """Spelling/word-order-insensitive key for duplicate detection."""
    value = (name or "").strip().lower().replace("ё", "е")
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    tokens = [t for t in value.split() if t]
    return " ".join(sorted(tokens))


def head_noun(name: str) -> str:
    value = (name or "").strip().lower().replace("ё", "е")
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    tokens = [t for t in value.split() if t]
    return tokens[0] if tokens else ""


def is_generic(name: str) -> bool:
    return (name or "").strip().lower().replace("ё", "е") in GENERIC_NAMES


def is_valid_quantity(quantity: str) -> bool:
    value = (quantity or "").strip().lower().replace("ё", "е")
    if value in NON_NUMERIC_QUANTITY:
        return False
    return bool(_QUANTITY_RE.match(value))


def canonical_unit(unit: str) -> tuple[str, bool]:
    """Return (canonical_unit, is_clean). is_clean=False means needs fixing."""
    value = (unit or "").strip().lower().replace("ё", "е")
    if value in CANONICAL_UNITS:
        return value, True
    if value in UNIT_ALIASES:
        return UNIT_ALIASES[value], False
    return value, False


@dataclass
class IngredientRow:
    recipe_id: int
    name: str
    quantity: str
    unit: str
    category: str


@dataclass
class AuditResult:
    recipe_count: int = 0
    ingredient_count: int = 0
    distinct_raw_names: int = 0
    distinct_norm_keys: int = 0
    variant_groups: dict[str, list[str]] = field(default_factory=dict)
    ambiguous_families: dict[str, list[str]] = field(default_factory=dict)
    generic_names: Counter = field(default_factory=Counter)
    bad_quantities: list[dict[str, Any]] = field(default_factory=list)
    dirty_units: Counter = field(default_factory=Counter)
    unit_suggestions: dict[str, str] = field(default_factory=dict)
    category_coverage: Counter = field(default_factory=Counter)
    readiness: dict[str, float] = field(default_factory=dict)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit recipe ingredient quality (read-only)")
    parser.add_argument(
        "--database-url", default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    )
    parser.add_argument("--md", default=str(DEFAULT_MD_REPORT))
    parser.add_argument("--json", default=str(DEFAULT_JSON_REPORT))
    parser.add_argument(
        "--source-type",
        default="v1_import",
        help="Restrict to this source_type (default v1_import)",
    )
    return parser.parse_args()


def load_rows(database_url: str, source_type: str) -> tuple[list[IngredientRow], int]:
    engine = create_engine(database_url)
    rows_query = text(
        """
        SELECT ri.recipe_id, ri.name, ri.quantity, ri.unit, ri.category
        FROM recipe_ingredients ri
        JOIN recipes r ON r.id = ri.recipe_id
        WHERE r.is_active = TRUE AND r.source_type = :source_type
        ORDER BY ri.recipe_id, ri.id
        """
    )
    count_query = text(
        "SELECT COUNT(*) FROM recipes WHERE is_active = TRUE AND source_type = :source_type"
    )
    with engine.connect() as conn:
        rows = [
            IngredientRow(
                recipe_id=r[0],
                name=r[1] or "",
                quantity=r[2] or "",
                unit=r[3] or "",
                category=r[4] or "other",
            )
            for r in conn.execute(rows_query, {"source_type": source_type})
        ]
        recipe_count = conn.execute(count_query, {"source_type": source_type}).scalar() or 0
    return rows, int(recipe_count)


def analyze(rows: list[IngredientRow], recipe_count: int) -> AuditResult:
    result = AuditResult(recipe_count=recipe_count, ingredient_count=len(rows))

    raw_names = {r.name.strip() for r in rows if r.name.strip()}
    result.distinct_raw_names = len(raw_names)

    # Spelling/word-order duplicate variant groups.
    key_to_names: dict[str, set[str]] = defaultdict(set)
    head_to_names: dict[str, set[str]] = defaultdict(set)
    for name in raw_names:
        key_to_names[normalize_key(name)].add(name)
        head_to_names[head_noun(name)].add(name)
    result.distinct_norm_keys = len(key_to_names)
    result.variant_groups = {
        key: sorted(names) for key, names in key_to_names.items() if len(names) > 1
    }
    result.ambiguous_families = {
        head: sorted(names)
        for head, names in head_to_names.items()
        if head in AMBIGUOUS_HEADS and len(names) > 1
    }

    clean_name_count = 0
    nutrition_ready = 0
    for row in rows:
        name = row.name.strip()
        if is_generic(name):
            result.generic_names[name.lower()] += 1

        if not is_valid_quantity(row.quantity):
            result.bad_quantities.append(
                {
                    "recipe_id": row.recipe_id,
                    "name": name,
                    "quantity": row.quantity,
                    "unit": row.unit,
                }
            )
        unit_canon, unit_clean = canonical_unit(row.unit)
        if not unit_clean:
            result.dirty_units[row.unit.strip().lower()] += 1
            if unit_canon and unit_canon != row.unit.strip().lower():
                result.unit_suggestions[row.unit.strip().lower()] = unit_canon

        result.category_coverage[(row.category or "other").lower()] += 1

        name_clean = bool(name) and not is_generic(name)
        if name_clean:
            clean_name_count += 1
        if name_clean and is_valid_quantity(row.quantity) and unit_clean:
            nutrition_ready += 1

    total = max(len(rows), 1)
    categorized = sum(
        count for cat, count in result.category_coverage.items() if cat not in ("other", "")
    )
    distinct = max(result.distinct_raw_names, 1)

    # Distinct names affected by each issue (sets, so overlaps don't double-count).
    variant_names: set[str] = {n for names in result.variant_groups.values() for n in names}
    ambiguous_names: set[str] = {
        n for names in result.ambiguous_families.values() for n in names
    }
    generic_distinct: set[str] = {
        n for n in raw_names if is_generic(n)
    }
    problem_names = variant_names | ambiguous_names | generic_distinct

    def pct(value: float) -> float:
        return round(max(0.0, min(100.0, value)), 1)

    result.readiness = {
        "normalization_pct": pct(100.0 * (distinct - len(variant_names)) / distinct),
        "canonical_products_pct": pct(100.0 * (distinct - len(problem_names)) / distinct),
        "shopping_grouping_pct": pct(100.0 * categorized / total),
        "nutrition_pct": pct(100.0 * nutrition_ready / total),
        "photo_prompt_pct": pct(100.0 * clean_name_count / total),
    }
    return result


def render_markdown(result: AuditResult, source_type: str) -> str:
    lines: list[str] = []
    a = lines.append
    a("# PLANAM V1 — Ingredient Quality Audit (read-only)")
    a("")
    a(f"**source_type:** `{source_type}` · **режим:** строго read-only (только SELECT)")
    a("")
    a("## 1. Сводка")
    a("")
    a("| Метрика | Значение |")
    a("|---------|----------|")
    a(f"| Активных рецептов | {result.recipe_count} |")
    a(f"| Всего строк-ингредиентов | {result.ingredient_count} |")
    a(f"| Уникальных названий (raw) | {result.distinct_raw_names} |")
    a(f"| Уникальных norm-ключей | {result.distinct_norm_keys} |")
    a(f"| Групп вариантов написания | {len(result.variant_groups)} |")
    a(f"| Неоднозначных семейств (перец/масло/…) | {len(result.ambiguous_families)} |")
    a(f"| Слишком общих названий (видов) | {len(result.generic_names)} |")
    a(f"| Строк с плохим количеством | {len(result.bad_quantities)} |")
    a(f"| Грязных единиц (видов) | {len(result.dirty_units)} |")
    a("")

    a("## 2. Готовность (scorecard)")
    a("")
    a("| Направление | Готовность |")
    a("|-------------|-----------|")
    a(f"| Нормализация названий | {result.readiness.get('normalization_pct', 0)}% |")
    a(f"| Canonical products | {result.readiness.get('canonical_products_pct', 0)}% |")
    a(f"| Shopping list grouping | {result.readiness.get('shopping_grouping_pct', 0)}% |")
    a(f"| Nutrition (КБЖУ) | {result.readiness.get('nutrition_pct', 0)}% |")
    a(f"| Photo prompt pipeline | {result.readiness.get('photo_prompt_pct', 0)}% |")
    a("")

    a("## 3. Варианты написания / порядка слов (дубли)")
    a("")
    if result.variant_groups:
        a("| norm-ключ | варианты |")
        a("|-----------|----------|")
        for key, names in sorted(
            result.variant_groups.items(), key=lambda kv: -len(kv[1])
        )[:50]:
            a(f"| `{key}` | {', '.join(names)} |")
    else:
        a("_Не найдено._")
    a("")

    a("## 4. Неоднозначные семейства (разные продукты под одним словом)")
    a("")
    if result.ambiguous_families:
        a("| головное слово | названия |")
        a("|----------------|----------|")
        for head, names in sorted(result.ambiguous_families.items()):
            a(f"| `{head}` | {', '.join(names)} |")
    else:
        a("_Не найдено._")
    a("")

    a("## 5. Слишком общие названия")
    a("")
    if result.generic_names:
        a("| название | вхождений |")
        a("|----------|-----------|")
        for name, count in result.generic_names.most_common():
            a(f"| {name} | {count} |")
    else:
        a("_Не найдено._")
    a("")

    a("## 6. Некорректные количества")
    a("")
    a(f"Всего: **{len(result.bad_quantities)}**. Примеры (до 40):")
    a("")
    if result.bad_quantities:
        a("| recipe_id | название | quantity | unit |")
        a("|-----------|----------|----------|------|")
        for item in result.bad_quantities[:40]:
            a(
                f"| {item['recipe_id']} | {item['name']} | "
                f"`{item['quantity']}` | `{item['unit']}` |"
            )
    else:
        a("_Не найдено._")
    a("")

    a("## 7. Грязные единицы измерения")
    a("")
    if result.dirty_units:
        a("| единица (как в БД) | вхождений | предлагаемый canonical |")
        a("|--------------------|-----------|------------------------|")
        for unit, count in result.dirty_units.most_common():
            suggestion = result.unit_suggestions.get(unit, "— (нужно решение)")
            a(f"| `{unit}` | {count} | `{suggestion}` |")
    else:
        a("_Не найдено._")
    a("")

    a("## 8. Покрытие категориями (shopping grouping)")
    a("")
    a("| категория | вхождений |")
    a("|-----------|-----------|")
    for cat, count in result.category_coverage.most_common():
        a(f"| {cat} | {count} |")
    a("")

    a("## 9. Рекомендации (следующий этап — НЕ в этом read-only прогоне)")
    a("")
    a("1. Завести canonical products + alias-таблицу (варианты написания → один продукт).")
    a("2. Разнести неоднозначные семейства (перец чёрный/душистый/болгарский/чили — разные продукты).")
    a("3. Заменить общие названия конкретными или пометить как нерасчётные для КБЖУ.")
    a("4. Нормализовать единицы по таблице aliases; ввести canonical unit set.")
    a("5. Перевести `по вкусу`/`немного` в флаг `to_taste`, а не в quantity.")
    a("6. Проставить shopping-категории строкам с `other`.")
    a("")
    a("> Этот отчёт получен строго read-only. Никакие изменения в БД не вносились.")
    a("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    rows, recipe_count = load_rows(args.database_url, args.source_type)
    result = analyze(rows, recipe_count)

    md_path = Path(args.md).resolve()
    json_path = Path(args.json).resolve()
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    md_path.write_text(render_markdown(result, args.source_type), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "source_type": args.source_type,
                "recipe_count": result.recipe_count,
                "ingredient_count": result.ingredient_count,
                "distinct_raw_names": result.distinct_raw_names,
                "distinct_norm_keys": result.distinct_norm_keys,
                "variant_groups": result.variant_groups,
                "ambiguous_families": result.ambiguous_families,
                "generic_names": dict(result.generic_names),
                "bad_quantities_count": len(result.bad_quantities),
                "bad_quantities_sample": result.bad_quantities[:100],
                "dirty_units": dict(result.dirty_units),
                "unit_suggestions": result.unit_suggestions,
                "category_coverage": dict(result.category_coverage),
                "readiness": result.readiness,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"Audited {result.ingredient_count} ingredients across "
        f"{result.recipe_count} recipes ({args.source_type})."
    )
    print(f"Variant groups: {len(result.variant_groups)}; "
          f"generic: {len(result.generic_names)}; "
          f"bad quantities: {len(result.bad_quantities)}; "
          f"dirty units: {len(result.dirty_units)}")
    print("Readiness:", result.readiness)
    print(f"MD:   {md_path}")
    print(f"JSON: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
