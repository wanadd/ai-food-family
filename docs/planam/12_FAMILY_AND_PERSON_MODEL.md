# 12 Family And Person Model

## Modes

Personal mode is valid and must work without family defaults. Family mode is optional and shares planning artifacts while preserving person-level safety context.

## Members

A household can contain an administrator/adult, additional adults, children, and virtual children without Telegram accounts. Member identity is stable and must not be replaced with anonymous aggregate rows.

## Shared versus personal

- Shared: menu, shopping list, pantry context, household planning horizon.
- Personal: allergies, restrictions, preferences, age, pregnancy/PKU/celiac context, participation, portion, and consent.

## Aggregation

Evaluate every participating person separately, then aggregate using `BLOCK > ESCALATE > UNKNOWN > WARN > SAFE`. Unknown participation or portion remains unknown/incomplete. Never make a person safe because another person is safe.

## Source

The baseline model is documented in [`../PLANAM_V1_FAMILY_MODEL.md`](../PLANAM_V1_FAMILY_MODEL.md). The production implementation must preserve the active profile policy and explicit person scope.
