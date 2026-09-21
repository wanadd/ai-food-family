# Recipe Image Preservation Manifest

## DO NOT DELETE DURING RECIPE LIBRARY RESET

- The canonical image contract in this directory.
- `master.png`, `master.webp`, `hero.webp`, `card_800.webp`, and `thumb_400.webp` when they belong to a valid Gold V3 recipe.
- Recipe-to-image URL fields and their provenance.
- Style profile/version metadata and manual review outcomes.
- Image generation audit fields such as recipe ID, duration, cost estimate, and provider usage ID.

## Safe handling

Do not delete or overwrite image assets as a side effect of recipe reset, source cleanup, or evidence backfill. A cleanup operation must enumerate exact recipe IDs, produce a reversible manifest, and receive explicit authorization.

## Current inventory note

The repository inventory recorded one public recipe-image file and no complete Gold V3 image set at the last audit. This is an inventory statement, not permission to generate or delete assets. See the existing image inventory report for the dated evidence.
