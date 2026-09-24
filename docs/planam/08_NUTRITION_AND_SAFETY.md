# 08 Nutrition And Safety

## Nutrition

Recipe nutrition is represented per serving. Missing or unavailable nutrition remains missing or low-confidence; it is never written as zero. Target intervals are resolved read-only unless a separate write operation is authorized.

## Person-aware safety

The safety decision is evaluated for each person and then aggregated for the household. Allergies are hard exclusions. Celiac/gluten, pregnancy, PKU/phenylalanine, age, and process-state facts have distinct evidence contracts and must not be collapsed into one generic label.

## Family aggregation

The family result follows `BLOCK > ESCALATE > UNKNOWN > WARN > SAFE`. Explicit unknown participation or portion means the aggregate is unknown/incomplete, never safe. A personal path must not be forced through mocked family defaults.

## Safety language

User-facing copy should state what is known, what is uncertain, and what action is prudent. PLANAM is not a medical diagnosis service. Health guidance must preserve source and confidence context and escalate where evidence is insufficient.

## Related source

- Menu aggregation: [`../PLANAM_V1_MENU_NUTRITION_AGGREGATION.md`](../PLANAM_V1_MENU_NUTRITION_AGGREGATION.md)
- Family model: [`12_FAMILY_AND_PERSON_MODEL.md`](12_FAMILY_AND_PERSON_MODEL.md)
