# Recipe Image Contract

## Files

For recipe ID `{id}`, the production path is:

`public/recipe-images/{id}/master.png`

Optional normalized master: `master.webp`; required variants: `hero.webp`, `card_800.webp`, `thumb_400.webp`.

## API mapping

- `hero_image_url` -> hero variant
- `image_url` -> card or primary image variant
- `thumbnail_url` -> thumbnail variant

Fallback order is `hero_image_url ?? image_url ?? thumbnail_url ?? fallback`.

## Invariants

- Exactly one master generation per recipe image set.
- Variants are derived from the master.
- Public URLs use `/recipe-images/{id}/...` and must not expose local filesystem paths.
- Missing image state is explicit and may use a product fallback; it is not silently reported as generated.
- Image generation requires explicit approval and a configured secret outside the repository.

