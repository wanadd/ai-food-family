# 09 Recipe Gold V3

## Contract

Gold V3 is the production-ready recipe contract: Russian title and description, structured ingredients and steps, nutrition per serving, restrictions/allergens/diet metadata, shopping-safe rows, image prompt metadata, source trace IDs, originality flags, schema version, and status `gold`.

The canonical source is [`../PLANAM_RECIPE_GOLD_V3_GENERATION_CONTRACT.md`](../PLANAM_RECIPE_GOLD_V3_GENERATION_CONTRACT.md).

## Generation rules

Stage F uses source signals only as hints and creates an original title, description, steps, and proportions. A valid recipe has at least four steps, meaningful step text, complete serving/time/difficulty fields, and validated nutrition and shopping fields. The validator target is at least 85.

Stage E defines schema and validation. Stage F generates originals in dry-run. Stage R imports in dry-run or apply mode. Stage N maps to runtime fields. Photo generation is not part of E/F without explicit approval.

## Prohibitions

Do not preserve an original source title, description, or step structure. Do not expose a source URL as the user-facing recipe. Do not add English prefixes, technical categories, or “bowl” to Russian titles unless the content genuinely requires it.

## Image relationship

One recipe produces one image master and derived variants. The image contract is in [`../recipe-images/IMAGE_CONTRACT.md`](../recipe-images/IMAGE_CONTRACT.md).
