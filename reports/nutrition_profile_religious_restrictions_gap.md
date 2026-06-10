# Nutrition Profile — Religious / Cultural Restrictions Gap

## Current backend

`UserProfile` (`apps/api/app/models/user_profile.py`):

- `diets: JSONB list` — generic diet tags
- `restrictions: JSONB list` — exists but not exposed in nutrition profile API schema
- `medical_restrictions: text`
- `banned_foods: text`

`NutritionProfileData` (`apps/api/app/schemas/nutrition_profile.py`):

- `allergies`, `diets`, `medical_restrictions`, `banned_foods`
- **No dedicated fields** for halal, kosher, no_pork, lent, no_alcohol, no_gelatin, no_beef, no_seafood, vegetarian, vegan

## Current UI

`NutritionProfileForm.tsx` — section `allergies_restrictions` with allergies + free-text medical/banned foods. No checkbox group for religious/cultural tags.

## Recommendation (Stage 1 — no breaking changes)

1. **Short term:** map new UI checkboxes → `UserProfile.restrictions` list using stable slugs:
   - `no_pork`, `halal`, `kosher`, `lent`, `no_alcohol`, `no_gelatin`, `no_beef`, `no_seafood`, `vegetarian`, `vegan`
2. **API:** extend `NutritionProfileData` with optional `cultural_restrictions: list[str]` reading/writing `restrictions` subset (additive schema).
3. **Menu AI:** read `restrictions` + `diets` when scoring Recipe V2 `religious_tags` / `excludes`.

## Stage 1 action taken

- Gap documented; backend **not modified** to avoid breaking existing clients.
- Recipe V2 gold set includes `religious_tags` / `excludes` for menu filtering once profile UI is extended.

## UI mock (P1)

Section title: **Культурные и религиозные ограничения**

Checkboxes: Без свинины, Халяль, Кошерное, Постное питание, Без алкоголя, Без желатина, Без говядины, Без морепродуктов, Вегетарианство, Веганство.
