# Recipe Engine API

Sprint 3 exposes the Recipe Engine foundation through HTTP APIs. These endpoints
are deterministic, do not call AI, and do not spend Ama.

## Feature Flags

All Recipe Engine feature flags are off by default and are read from environment
variables:

- `RECIPE_EXPLAINABILITY=true` for `GET /recipes/{id}/why`
- `RECIPE_HISTORY=true` for cooking history endpoints
- `RECIPE_COLLECTIONS=true` for `/collections`
- `FAMILY_RECIPE_PREFERENCES=true` for `POST /recipes/{id}/rate`
- `RECIPE_SCENARIOS=true` for `GET /recipes/scenarios` and `GET /recipes?scenario=...`

`GET /recipes/from-pantry` uses the existing pantry scope and does not require a
new flag.

## Recommendation Explanation

`GET /recipes/{id}/why`

Returns deterministic recommendation reasons:

- `IN_PANTRY`
- `KIDS_LIKE`
- `GOAL_MATCH`
- `QUICK_COOKING`
- `BUDGET_FRIENDLY`
- `HIGH_PROTEIN`
- `LOW_CALORIE`
- `FAMILY_APPROVED`

Example response:

```json
{
  "recipe_id": 42,
  "summary": "Быстро и подходит семье",
  "positives": [
    { "code": "QUICK_COOKING", "label": "Быстро готовится", "kind": "positive", "weight": 1.0 }
  ],
  "warnings": [],
  "hard_blocks": [],
  "score_total": 1.0,
  "uses_ai": false,
  "uses_ama": false
}
```

## Cooking History

`POST /recipes/{id}/cooked`

```json
{
  "cooked_on": "2026-05-27",
  "servings": 4,
  "notes": "Дети попросили повторить",
  "family_member_id": 7,
  "source": "manual"
}
```

`GET /recipes/{id}/history?limit=20`

Returns recent cooked events for one recipe plus `stats` with `cooked_count` and
`last_cooked_on`.

`GET /recipes/history?limit=50`

Returns the recent cooking journal for the active app scope.

## Collections

`GET /collections`

Lists visible system, personal, and family collections.

`POST /collections`

```json
{
  "name": "Любимые завтраки",
  "visibility": "personal",
  "description": "То, что хочется повторять",
  "emoji": "🥞",
  "color": "#F4B400"
}
```

`GET /collections/{id}`

Returns collection metadata and `recipe_ids`.

`PATCH /collections/{id}`

```json
{
  "name": "Быстрые завтраки",
  "is_pinned": true
}
```

`DELETE /collections/{id}`

Deletes a writable personal or family collection.

`POST /collections/{id}/recipes`

```json
{
  "recipe_ids": [12, 42, 77]
}
```

`DELETE /collections/{id}/recipes/{recipe_id}`

Removes one recipe from a writable collection.

## Family Preferences

`POST /recipes/{id}/rate`

Requires family scope and stores one preference per family member + recipe.

```json
{
  "family_member_id": 7,
  "rating": "loved",
  "note": "Просит на выходные"
}
```

Alternative boolean fields are also supported:

```json
{
  "family_member_id": 7,
  "liked": true,
  "disliked": false,
  "is_loved": false,
  "note": "Ок для будней"
}
```

## Scenarios

`GET /recipes/scenarios`

Returns active scenario filters with approximate recipe counts.

Supported `scenario` values:

- `quick`
- `ultra_quick`
- `cheap`
- `kids_loved`
- `from_pantry`
- `lose_weight`
- `gain_weight`
- `work_lunch`
- `travel`
- `guests`
- `holiday`
- `almost_no_cooking`

`GET /recipes?scenario=quick`

Filters the existing recipe list using deterministic scenario rules. This does
not enable full-text search.

## From Pantry

`GET /recipes/from-pantry?max_missing=3&limit=30`

Looks at current pantry items in the active app scope and returns recipes with
ingredient coverage:

```json
{
  "items": [
    {
      "recipe_id": 42,
      "title": "Омлет с сыром",
      "have": 3,
      "total": 4,
      "missing_ingredients": ["сыр"],
      "coverage_ratio": 0.75,
      "summary": {
        "id": 42,
        "title": "Омлет с сыром",
        "meal_type": "breakfast",
        "category": "main",
        "cooking_time_minutes": 15
      }
    }
  ],
  "total": 1,
  "uses_ai": false,
  "uses_ama": false
}
```

## Cost And AI

All endpoints in this document are free for the user:

- no OpenAI calls;
- no Ama transactions;
- no OCR;
- no import of a large recipe database;
- no subscription or tariff changes.
