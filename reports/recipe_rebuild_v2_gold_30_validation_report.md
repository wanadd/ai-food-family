# Gold 30 — Validation Report

- File: `data/recipe_v2/gold_recipes_30.jsonl`
- Generated: Stage 1 local validation
- **Total: 30**
- **Valid: 30**
- **Invalid: 0**

## Coverage

| Segment | Count |
|---------|------:|
| Breakfast | 6 |
| Lunch | 8 |
| Dinner | 8 |
| Snack | 5 |
| Pro / sport / health | 3 |

## Checks passed

- All recipes have title, servings, structured ingredients and steps
- All units in whitelist (г, мл, шт, ст.л., ч.л., зубчик, пучок)
- All have `nutrition_summary` with `confidence: estimated`
- Each ingredient has `shopping_category_slug` (explicit or inferred)
- No alcohol, no complex conservation, no dubious units in names
- Halal / no_pork / lent / vegetarian variants included

## Command

```bash
python backend/scripts/validate_recipe_v2.py --file data/recipe_v2/gold_recipes_30.jsonl
```

Rebuild source (regenerate JSONL):

```bash
python data/recipe_v2/build_gold_recipes_30.py
```
