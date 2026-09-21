# 10 Menu Engine

## Role

The menu engine turns household context, recipe candidates, person policy, pantry state, and planning horizon into a practical menu. It is a composer, not an authority for raw food facts.

## Inputs

- Active personal or family profile
- Allergies, restrictions, preferences, age-sensitive policy
- Recipe Gold V3 candidates and evidence confidence
- Pantry and planned purchases
- Meal timing, servings, and participation

## Behavior

The engine must exclude hard conflicts, surface uncertain candidates for review, and preserve the reason for each choice. Nutrition totals use recipe nutrition per serving and explicit portions. Missing nutrition lowers confidence and is not silently imputed as zero.

## Output

The result is a menu that can be cooked, understood, and converted into a unified shopping view. The home screen should show the next action rather than exposing all planning machinery.

## Constraints

Planning must support a single-person path. Family aggregation must preserve the strictest person-level state. Delivery integrations remain downstream adapters.
