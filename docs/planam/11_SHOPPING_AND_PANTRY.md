# 11 Shopping And Pantry

## Unified shopping center

Shopping is the household purchase center, not merely a list of menu ingredients. It can include planned ingredients, manual purchases, pantry items, children, pets, and household needs across 14 categories.

The generic category name `Продукты` is forbidden because it hides useful distinctions.

## Data behavior

Ingredient rows must retain normalized identity, unit, quantity, source (menu/manual/pantry), and uncertainty. Unknown quantity is not zero. Recomputing quantities must use current servings and participation rather than stale display values.

## Pantry relationship

Pantry state can reduce a purchase need but cannot erase a safety or evidence requirement. A substitution must be evaluated against the same person-level restrictions and evidence rules as the original item.

## Delivery boundary

The V1 shopping experience is provider-neutral. A later delivery adapter may consume a validated purchase intent; it must not become the source of truth for household inventory or health policy.
