# PLANAM Recipe Images

This directory is the portable image-policy checkpoint for PLANAM Gold V3 recipes.

## Canonical rules

- One recipe -> one generated master -> `hero`, `card`, and `thumb` variants.
- The master is the visual source of truth; variants are deterministic crops/resizes.
- The style is a bright, believable home kitchen with neutral light ceramic and soft daylight.
- Text, logos, packaging, people, hands, clutter, plastic stock styling, and theatrical fine dining are prohibited.

## Implementation locations

- Primary pipeline: [`../../apps/api/app/recipes/recipe_gold_v3_image_pipeline.py`](../../apps/api/app/recipes/recipe_gold_v3_image_pipeline.py)
- Shared utility: [`../../backend/scripts/recipe_image_utils.py`](../../backend/scripts/recipe_image_utils.py)
- Existing source style docs: [`../PLANAM_RECIPE_IMAGE_MASTER_PROMPT.md`](../PLANAM_RECIPE_IMAGE_MASTER_PROMPT.md), [`../PLANAM_V1_RECIPE_IMAGE_STYLE_SYSTEM.md`](../PLANAM_V1_RECIPE_IMAGE_STYLE_SYSTEM.md)

Read [`MASTER_STYLE.md`](MASTER_STYLE.md), [`IMAGE_CONTRACT.md`](IMAGE_CONTRACT.md), and [`PRESERVATION_MANIFEST.md`](PRESERVATION_MANIFEST.md) as the portable contract.
