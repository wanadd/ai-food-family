# Povarenok Culinary Signals V3 Report

**Generated:** 2026-06-12 09:39 UTC
**Branch:** `feat/recipe-gold-v3-original-planam-library`
**Commit:** `2d6d8e8 feat(recipes): wire restriction safety into menu generation`
**Mode:** `apply`

## Files

- Input: `exports\povarenok_candidates_100.jsonl`
- Output: `exports\povarenok_culinary_signals_v3_100.jsonl`
- Report: `reports\povarenok_culinary_signals_v3_report.md`

## Summary

- Records read: `100`
- Signals written: `99`
- Skipped: `1`
- avoid_for_planam: `38`
- Originality safety: `PASS`

## Skip reasons

- originality_violation:leaked_quoted_title: `1`

## Quality flags

- missing_steps: `99`
- high_originality_risk: `37`
- has_pork: `9`

## Dish family

- салат: `35`
- семейное горячее: `24`
- суп: `22`
- запеканка: `7`
- котлеты: `6`
- гарнир/крупа: `4`
- яичное блюдо: `1`

## Meal type hints

- lunch: `98`
- dinner: `98`
- snack: `35`
- salad: `35`
- soup: `22`
- breakfast: `4`

## Product groups

- овощи: `70`
- мясо_птица: `46`
- молочные продукты: `37`
- яйца: `31`
- крупы: `14`
- свинина: `9`
- бобовые: `8`
- рыба: `6`
- фрукты/ягоды: `6`
- сладкое: `5`
- мясо: `4`
- паста: `3`
- морепродукты: `2`
- выпечка/тесто: `2`
- орехи: `2`

## Restriction hints

- vegan: `65`
- lactose_free: `36`
- no_milk: `36`
- no_eggs: `34`
- no_soy: `20`
- vegetarian: `19`
- gluten_free: `16`
- pescatarian: `15`
- halal: `9`
- no_pork: `9`
- kosher: `7`
- no_nuts: `5`
- no_fish: `4`
- no_seafood: `2`
- no_beef: `2`
- no_alcohol: `2`

## Allergen hints

- milk: `37`
- eggs: `33`
- soy: `20`
- gluten: `17`
- fish: `6`
- nuts: `5`
- seafood: `2`

## Sample signals (10)

```json
{
  "signal_id": "pov_sig_000001",
  "source_type": "povarenok_signal",
  "source_record_hash": "1e647813c3e4df2b23c9dd151ac66baf7e28cd857ed5d4ff5752336b7b44e753",
  "originality_policy": {
    "no_original_title": true,
    "no_original_steps": true,
    "no_direct_import": true,
    "signals_only": true
  },
  "dish_family": "салат",
  "meal_type_hints": [
    "lunch",
    "dinner",
    "snack",
    "salad"
  ],
  "category_hints": [
    "side",
    "salad"
  ],
  "main_product_groups": [
    "овощи"
  ],
  "secondary_product_groups": [],
  "cooking_methods": [
    "салат/смешивание"
  ],
  "equipment_hints": [
    "базовая кухня"
  ],
  "complexity": "medium",
  "family_fit": "low",
  "time_bucket": "20-40 минут",
  "nutrition_style_hints": [
    "vegetable_forward"
  ],
  "restriction_hints": [],
  "allergen_hints": [],
  "shopping_category_hints": [
    "овощи"
  ],
  "seasonality_hints": [
    "лето"
  ],
  "avoid_for_planam": true,
  "avoid_reasons": [
    "high_originality_risk"
  ],
  "quality_flags": [
    "high_originality_risk",
    "missing_steps"
  ],
  "ingredient_count_bucket": "4-7",
  "raw_ingredient_names_normalized": [
    "баклажан",
    "лук репчатый",
    "майонез",
    "перец черный",
    "помидор",
    "соль",
    "чеснок"
  ],
  "generation_prompt_hints": [
    "сделать оригинальное семейное блюдо (салат) на основе овощи",
    "не использовать оригинальное название и порядок действий источника",
    "техника: салат/смешивание"
  ]
}
```

```json
{
  "signal_id": "pov_sig_000002",
  "source_type": "povarenok_signal",
  "source_record_hash": "247da1d46a60d21b9086d9c253c721b689bdb696a7a3c31fb9641ab63fac6083",
  "originality_policy": {
    "no_original_title": true,
    "no_original_steps": true,
    "no_direct_import": true,
    "signals_only": true
  },
  "dish_family": "котлеты",
  "meal_type_hints": [
    "lunch",
    "dinner"
  ],
  "category_hints": [
    "main"
  ],
  "main_product_groups": [
    "мясо_птица",
    "молочные продукты",
    "яйца"
  ],
  "secondary_product_groups": [
    "овощи"
  ],
  "cooking_methods": [
    "запекание",
    "котлеты/формование"
  ],
  "equipment_hints": [
    "духовка",
    "сковорода"
  ],
  "complexity": "medium",
  "family_fit": "medium",
  "time_bucket": "40-60 минут",
  "nutrition_style_hints": [
    "high_protein"
  ],
  "restriction_hints": [
    "lactose_free",
    "no_eggs",
    "no_milk",
    "vegan"
  ],
  "allergen_hints": [
    "eggs",
    "milk"
  ],
  "shopping_category_hints": [
    "мясо_птица",
    "молочные продукты",
    "овощи"
  ],
  "seasonality_hints": [
    "круглый год"
  ],
  "avoid_for_planam": false,
  "avoid_reasons": [],
  "quality_flags": [
    "missing_steps"
  ],
  "ingredient_count_bucket": "8-12",
  "raw_ingredient_names_normalized": [
    "желток яичный",
    "зелень",
    "картофельное",
    "куриный",
    "лук репчатый",
    "молоко",
    "приправа",
    "растительное",
    "сливочное",
    "сыр твердый"
  ],
  "generation_prompt_hints": [
    "сделать оригинальное семейное блюдо (котлеты) на основе мясо_птица, молочные продукты, яйца",
    "не использовать оригинальное название и порядок действий источника",
    "сохранить белковую базу (мясо_птица), но с новой подачей",
    "техника: запекание, котлеты/формование"
  ]
}
```

```json
{
  "signal_id": "pov_sig_000003",
  "source_type": "povarenok_signal",
  "source_record_hash": "9ae76eb2d375d196bf4303a01f2c020e149d3a305367c4e535a513e5862bc5c5",
  "originality_policy": {
    "no_original_title": true,
    "no_original_steps": true,
    "no_direct_import": true,
    "signals_only": true
  },
  "dish_family": "семейное горячее",
  "meal_type_hints": [
    "lunch",
    "dinner"
  ],
  "category_hints": [
    "main"
  ],
  "main_product_groups": [
    "рыба",
    "овощи"
  ],
  "secondary_product_groups": [],
  "cooking_methods": [
    "смешанная техника"
  ],
  "equipment_hints": [
    "базовая кухня"
  ],
  "complexity": "medium",
  "family_fit": "low",
  "time_bucket": "20-40 минут",
  "nutrition_style_hints": [
    "high_protein"
  ],
  "restriction_hints": [
    "no_soy"
  ],
  "allergen_hints": [
    "fish",
    "soy"
  ],
  "shopping_category_hints": [
    "рыба",
    "овощи"
  ],
  "seasonality_hints": [
    "круглый год"
  ],
  "avoid_for_planam": true,
  "avoid_reasons": [
    "high_originality_risk"
  ],
  "quality_flags": [
    "high_originality_risk",
    "missing_steps"
  ],
  "ingredient_count_bucket": "8-12",
  "raw_ingredient_names_normalized": [
    "горбуша",
    "зубатка",
    "лук репчатый",
    "мак",
    "перец болгарский",
    "растительное",
    "соевый соус",
    "специи",
    "чеснок"
  ],
  "generation_prompt_hints": [
    "сделать оригинальное семейное блюдо (семейное горячее) на основе рыба, овощи",
    "не использовать оригинальное название и порядок действий источника",
    "сохранить белковую базу (рыба), но с новой подачей",
    "техника: смешанная техника"
  ]
}
```

```json
{
  "signal_id": "pov_sig_000004",
  "source_type": "povarenok_signal",
  "source_record_hash": "a4354f7223fb474f7876bcbce9b1d954f2cda823a968ef45a9176f70746cb597",
  "originality_policy": {
    "no_original_title": true,
    "no_original_steps": true,
    "no_direct_import": true,
    "signals_only": true
  },
  "dish_family": "салат",
  "meal_type_hints": [
    "lunch",
    "dinner",
    "snack",
    "salad"
  ],
  "category_hints": [
    "side",
    "salad"
  ],
  "main_product_groups": [
    "овощи",
    "бобовые"
  ],
  "secondary_product_groups": [],
  "cooking_methods": [
    "салат/смешивание"
  ],
  "equipment_hints": [
    "базовая кухня"
  ],
  "complexity": "medium",
  "family_fit": "low",
  "time_bucket": "20-40 минут",
  "nutrition_style_hints": [
    "vegetable_forward"
  ],
  "restriction_hints": [],
  "allergen_hints": [],
  "shopping_category_hints": [
    "овощи"
  ],
  "seasonality_hints": [
    "круглый год"
  ],
  "avoid_for_planam": true,
  "avoid_reasons": [
    "high_originality_risk"
  ],
  "quality_flags": [
    "high_originality_risk",
    "missing_steps"
  ],
  "ingredient_count_bucket": "8-12",
  "raw_ingredient_names_normalized": [
    "горчица",
    "картофель",
    "лук репчатый",
    "майонез",
    "морковь",
    "огурец",
    "свекла",
    "фасоль"
  ],
  "generation_prompt_hints": [
    "сделать оригинальное семейное блюдо (салат) на основе овощи, бобовые",
    "не использовать оригинальное название и порядок действий источника",
    "сохранить белковую базу (бобовые), но с новой подачей",
    "техника: салат/смешивание"
  ]
}
```

```json
{
  "signal_id": "pov_sig_000005",
  "source_type": "povarenok_signal",
  "source_record_hash": "94c09ae7e69da6f5cbf84bd66dedcfc992a39d454a073d9b73840976da8d6958",
  "originality_policy": {
    "no_original_title": true,
    "no_original_steps": true,
    "no_direct_import": true,
    "signals_only": true
  },
  "dish_family": "гарнир/крупа",
  "meal_type_hints": [
    "lunch",
    "dinner"
  ],
  "category_hints": [
    "side"
  ],
  "main_product_groups": [
    "крупы",
    "овощи"
  ],
  "secondary_product_groups": [],
  "cooking_methods": [
    "смешанная техника"
  ],
  "equipment_hints": [
    "базовая кухня"
  ],
  "complexity": "medium",
  "family_fit": "medium",
  "time_bucket": "20-40 минут",
  "nutrition_style_hints": [
    "vegetable_forward"
  ],
  "restriction_hints": [],
  "allergen_hints": [],
  "shopping_category_hints": [
    "крупы",
    "овощи"
  ],
  "seasonality_hints": [
    "осень"
  ],
  "avoid_for_planam": false,
  "avoid_reasons": [],
  "quality_flags": [
    "missing_steps"
  ],
  "ingredient_count_bucket": "4-7",
  "raw_ingredient_names_normalized": [
    "гречневая",
    "лук репчатый",
    "оливковое",
    "перец красный жгучий",
    "соль",
    "тимьян",
    "шампиньоны"
  ],
  "generation_prompt_hints": [
    "сделать оригинальное семейное блюдо (гарнир/крупа) на основе крупы, овощи",
    "не использовать оригинальное название и порядок действий источника",
    "техника: смешанная техника"
  ]
}
```

```json
{
  "signal_id": "pov_sig_000006",
  "source_type": "povarenok_signal",
  "source_record_hash": "e00cb6fa7ea6cb3a6d94a889855c189bfb4e16ac1520df2da236d7e22a4079a1",
  "originality_policy": {
    "no_original_title": true,
    "no_original_steps": true,
    "no_direct_import": true,
    "signals_only": true
  },
  "dish_family": "суп",
  "meal_type_hints": [
    "lunch",
    "dinner",
    "soup"
  ],
  "category_hints": [
    "main",
    "soup"
  ],
  "main_product_groups": [
    "мясо_птица",
    "яйца",
    "овощи"
  ],
  "secondary_product_groups": [
    "выпечка/тесто"
  ],
  "cooking_methods": [
    "суп",
    "выпечка"
  ],
  "equipment_hints": [
    "кастрюля"
  ],
  "complexity": "medium",
  "family_fit": "medium",
  "time_bucket": "20-40 минут",
  "nutrition_style_hints": [
    "high_protein"
  ],
  "restriction_hints": [
    "gluten_free",
    "no_eggs",
    "vegan"
  ],
  "allergen_hints": [
    "eggs",
    "gluten"
  ],
  "shopping_category_hints": [
    "мясо_птица",
    "овощи"
  ],
  "seasonality_hints": [
    "круглый год"
  ],
  "avoid_for_planam": false,
  "avoid_reasons": [],
  "quality_flags": [
    "missing_steps"
  ],
  "ingredient_count_bucket": "4-7",
  "raw_ingredient_names_normalized": [
    "вода",
    "грудка куриная",
    "лук репчатый",
    "морковь",
    "мука пшеничная",
    "соль",
    "яйцо куриное"
  ],
  "generation_prompt_hints": [
    "сделать оригинальное семейное блюдо (суп) на основе мясо_птица, яйца, овощи",
    "не использовать оригинальное название и порядок действий источника",
    "сохранить белковую базу (мясо_птица), но с новой подачей",
    "техника: суп, выпечка"
  ]
}
```

```json
{
  "signal_id": "pov_sig_000007",
  "source_type": "povarenok_signal",
  "source_record_hash": "91c3233f89ffb88ce88b2e5032b86c63bc6760ce0fa1d95bed531c7763c80f3a",
  "originality_policy": {
    "no_original_title": true,
    "no_original_steps": true,
    "no_direct_import": true,
    "signals_only": true
  },
  "dish_family": "семейное горячее",
  "meal_type_hints": [
    "lunch",
    "dinner"
  ],
  "category_hints": [
    "main"
  ],
  "main_product_groups": [
    "мясо_птица",
    "овощи",
    "фрукты/ягоды"
  ],
  "secondary_product_groups": [],
  "cooking_methods": [
    "смешанная техника"
  ],
  "equipment_hints": [
    "базовая кухня"
  ],
  "complexity": "medium",
  "family_fit": "medium",
  "time_bucket": "20-40 минут",
  "nutrition_style_hints": [
    "high_protein"
  ],
  "restriction_hints": [
    "no_soy"
  ],
  "allergen_hints": [
    "soy"
  ],
  "shopping_category_hints": [
    "мясо_птица",
    "овощи"
  ],
  "seasonality_hints": [
    "круглый год"
  ],
  "avoid_for_planam": false,
  "avoid_reasons": [],
  "quality_flags": [
    "missing_steps"
  ],
  "ingredient_count_bucket": "8-12",
  "raw_ingredient_names_normalized": [
    "голень куриная",
    "майонез",
    "смесь перцев",
    "соевый соус",
    "соль",
    "специи",
    "чернослив",
    "чеснок",
    "яблоко"
  ],
  "generation_prompt_hints": [
    "сделать оригинальное семейное блюдо (семейное горячее) на основе мясо_птица, овощи, фрукты/ягоды",
    "не использовать оригинальное название и порядок действий источника",
    "сохранить белковую базу (мясо_птица), но с новой подачей",
    "техника: смешанная техника"
  ]
}
```

```json
{
  "signal_id": "pov_sig_000008",
  "source_type": "povarenok_signal",
  "source_record_hash": "d522939e9d8be63119089f2bb61292386336283d3883e2e9ad85e0d9ed421104",
  "originality_policy": {
    "no_original_title": true,
    "no_original_steps": true,
    "no_direct_import": true,
    "signals_only": true
  },
  "dish_family": "семейное горячее",
  "meal_type_hints": [
    "lunch",
    "dinner"
  ],
  "category_hints": [
    "main"
  ],
  "main_product_groups": [
    "мясо_птица",
    "молочные продукты",
    "овощи"
  ],
  "secondary_product_groups": [],
  "cooking_methods": [
    "смешанная техника"
  ],
  "equipment_hints": [
    "базовая кухня"
  ],
  "complexity": "medium",
  "family_fit": "low",
  "time_bucket": "20-40 минут",
  "nutrition_style_hints": [
    "high_protein"
  ],
  "restriction_hints": [
    "lactose_free",
    "no_milk",
    "vegan"
  ],
  "allergen_hints": [
    "milk"
  ],
  "shopping_category_hints": [
    "мясо_птица",
    "молочные продукты",
    "овощи"
  ],
  "seasonality_hints": [
    "лето"
  ],
  "avoid_for_planam": true,
  "avoid_reasons": [
    "high_originality_risk"
  ],
  "quality_flags": [
    "high_originality_risk",
    "missing_steps"
  ],
  "ingredient_count_bucket": "4-7",
  "raw_ingredient_names_normalized": [
    "бедро куриное",
    "горчица",
    "помидор",
    "растительное",
    "специи",
    "сыр твердый",
    "шампиньоны"
  ],
  "generation_prompt_hints": [
    "сделать оригинальное семейное блюдо (семейное горячее) на основе мясо_птица, молочные продукты, овощи",
    "не использовать оригинальное название и порядок действий источника",
    "сохранить белковую базу (мясо_птица), но с новой подачей",
    "техника: смешанная техника"
  ]
}
```

```json
{
  "signal_id": "pov_sig_000009",
  "source_type": "povarenok_signal",
  "source_record_hash": "f3df219aafc3ecbfad28bb0539231d65dd5cd2b052cd3e64f8527b2f766fc2c5",
  "originality_policy": {
    "no_original_title": true,
    "no_original_steps": true,
    "no_direct_import": true,
    "signals_only": true
  },
  "dish_family": "запеканка",
  "meal_type_hints": [
    "lunch",
    "dinner"
  ],
  "category_hints": [
    "main"
  ],
  "main_product_groups": [
    "мясо_птица",
    "яйца",
    "овощи"
  ],
  "secondary_product_groups": [],
  "cooking_methods": [
    "запекание"
  ],
  "equipment_hints": [
    "духовка"
  ],
  "complexity": "medium",
  "family_fit": "medium",
  "time_bucket": "40-60 минут",
  "nutrition_style_hints": [
    "high_protein"
  ],
  "restriction_hints": [
    "no_eggs",
    "vegan"
  ],
  "allergen_hints": [
    "eggs"
  ],
  "shopping_category_hints": [
    "мясо_птица",
    "овощи"
  ],
  "seasonality_hints": [
    "осень"
  ],
  "avoid_for_planam": false,
  "avoid_reasons": [],
  "quality_flags": [
    "missing_steps"
  ],
  "ingredient_count_bucket": "4-7",
  "raw_ingredient_names_normalized": [
    "лук репчатый",
    "маца",
    "морковь",
    "растительное",
    "сливочное",
    "шампиньоны",
    "яйцо куриное"
  ],
  "generation_prompt_hints": [
    "сделать оригинальное семейное блюдо (запеканка) на основе мясо_птица, яйца, овощи",
    "не использовать оригинальное название и порядок действий источника",
    "сохранить белковую базу (мясо_птица), но с новой подачей",
    "техника: запекание"
  ]
}
```

```json
{
  "signal_id": "pov_sig_000010",
  "source_type": "povarenok_signal",
  "source_record_hash": "efbf570def5693bcaa5152c9262d4faa74ac58c8009ae20e8387b0c17950cc45",
  "originality_policy": {
    "no_original_title": true,
    "no_original_steps": true,
    "no_direct_import": true,
    "signals_only": true
  },
  "dish_family": "суп",
  "meal_type_hints": [
    "lunch",
    "dinner",
    "soup"
  ],
  "category_hints": [
    "main",
    "soup"
  ],
  "main_product_groups": [
    "свинина",
    "молочные продукты",
    "овощи"
  ],
  "secondary_product_groups": [
    "фрукты/ягоды"
  ],
  "cooking_methods": [
    "суп",
    "фаршировка"
  ],
  "equipment_hints": [
    "кастрюля"
  ],
  "complexity": "medium",
  "family_fit": "medium",
  "time_bucket": "20-40 минут",
  "nutrition_style_hints": [
    "vegetable_forward"
  ],
  "restriction_hints": [
    "halal",
    "kosher",
    "lactose_free",
    "no_milk",
    "no_pork",
    "pescatarian",
    "vegan",
    "vegetarian"
  ],
  "allergen_hints": [
    "milk"
  ],
  "shopping_category_hints": [
    "молочные продукты",
    "овощи"
  ],
  "seasonality_hints": [
    "круглый год"
  ],
  "avoid_for_planam": false,
  "avoid_reasons": [],
  "quality_flags": [
    "has_pork",
    "missing_steps"
  ],
  "ingredient_count_bucket": "8-12",
  "raw_ingredient_names_normalized": [
    "авокадо",
    "бекон",
    "вода",
    "кукуруза",
    "лимонный",
    "лук репчатый",
    "оливковое",
    "петрушка",
    "сметана",
    "соль"
  ],
  "generation_prompt_hints": [
    "сделать оригинальное семейное блюдо (суп) на основе свинина, молочные продукты, овощи",
    "не использовать оригинальное название и порядок действий источника",
    "техника: суп, фаршировка"
  ]
}
```

## Not done

- Recipe import
- Recipe generation
- Photo generation
- DB changes
- Safe reset
