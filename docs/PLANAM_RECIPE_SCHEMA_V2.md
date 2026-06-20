# PLANAM Recipe Schema V2

Target structure for the recipe rebuild. Stage 1 stores `recipe_schema_version` and
`status` in `recipes.tags` until a DB migration adds dedicated columns.

## Core fields

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | DB primary key |
| `title` | string | Display title |
| `normalized_title` | string | Lowercase, dedupe key |
| `description` | string | Short summary |
| `meal_types[]` | string[] | `breakfast`, `lunch`, `dinner`, `snack`, `drink` |
| `servings` | int | Required |
| `prep_time_minutes` | int | |
| `cook_time_minutes` | int | |
| `total_time_minutes` | int | prep + cook |
| `difficulty` | enum | `easy`, `medium`, `hard` |
| `image_url` | string? | |
| `source_type` | enum | `seed`, `import`, `manual` |
| `recipe_schema_version` | int | `2` |
| `status` | enum | `draft`, `gold`, `published`, `archived` |

## Nutrition (`nutrition_summary`)

```json
{
  "calories": 420,
  "protein_g": 32,
  "fat_g": 14,
  "carbs_g": 38,
  "fiber_g": 4,
  "sugar_g": 6,
  "salt_g": 1.2,
  "confidence": "verified"
}
```

`confidence`: `verified` | `estimated` | `unavailable`

Maps to legacy columns: `calories_per_serving`, `protein_g`, `fat_g`, `carbs_g`,
`nutrition_confidence`.

## Ingredients (structured)

Each ingredient is a JSON object (stored in `recipe_ingredients` rows + JSONB mirror):

```json
{
  "display_name": "Куриное филе",
  "canonical_name": "куриное филе",
  "canonical_slug": "chicken_fillet",
  "amount": 400,
  "unit": "г",
  "amount_grams": 400,
  "shopping_category_slug": "meat_poultry",
  "pantry_category_slug": "meat_poultry",
  "allergens": [],
  "diet_flags": ["halal_possible"],
  "is_optional": false,
  "preparation_note": "нарезать кубиками"
}
```

### Allowed units

`г`, `кг`, `мл`, `л`, `шт`, `ст.л.`, `ч.л.`, `по вкусу`, `щепотка`, `зубчик`, `пучок`

### Shopping categories (V2 slugs)

See `apps/api/app/recipes/product_taxonomy.py`. Legacy Russian slugs map via
`legacy_shopping_slug()`.

## Steps (structured)

Not a plain text blob:

```json
{
  "order": 1,
  "title": "Подготовка",
  "instruction": "Нарезать овощи.",
  "duration_minutes": 5,
  "tips": "можно использовать замороженные овощи"
}
```

Legacy `recipes.steps` JSONB stores instruction strings; structured steps live in
`recipe_steps` when imported via V2 pipeline.

## Dietary / cultural / religious

```json
{
  "diet_tags": ["vegetarian", "sport"],
  "excludes": ["no_pork"],
  "allergens": ["gluten", "dairy"],
  "religious_tags": ["halal", "lent"]
}
```

Supported tags:

- `halal`, `kosher`, `no_pork`, `lent`, `vegetarian`, `vegan`
- `no_alcohol`, `no_gelatin`, `no_beef`, `no_seafood`
- `dairy_free`, `gluten_free`

## Meal frequency / Pro

Recipe-level tags (optional):

- `3_meals`, `4_meals`, `5_meals`, `6_meals`
- `sport`, `weight_loss`, `muscle_gain`, `medical_diet`, `small_portions`

## Validation

`apps/api/app/recipes/recipe_v2_validation.py` — used by import dry-run and gold seed QA.

## Import tags convention

Until migration:

- `recipe_schema_v2` in `recipes.tags`
- `status:gold` in `recipes.tags`
