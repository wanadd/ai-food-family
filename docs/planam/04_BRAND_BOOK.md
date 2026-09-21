# 04 Brand Book

## Brand purpose and positioning

PLANAM is a calm, intelligent household food companion. Its personality is warm, practical, attentive, and quietly competent. It reduces effort without taking agency away from the person making decisions.

## Tone

Use short, human, concrete copy. Prefer confidence calibrated by evidence. Explain a limitation plainly. Avoid medical certainty, excessive cheerleading, shame, food moralism, and technical jargon.

## Visual direction

The source-backed visual system combines a bright food-and-health interface with warm home-kitchen photography, generous white space, saturated green action accents, graphite text, and restrained warm orange emphasis. A historical design freeze also describes warm cream, sage, and graphite; implementation must use the current semantic `pa-*` tokens and must not mix legacy cream tokens into new screens without an explicit migration.

## Current implementation tokens

The current semantic reference is [`../PLANAM_COLOR_SYSTEM_V1.md`](../PLANAM_COLOR_SYSTEM_V1.md): light canvas `#FFFFFF`, elevated surface `#F6FAF6`, primary text `#1A1F1C`, secondary text `#5C665C`, primary green `#2F9E44`, secondary green `#248A38`, accent orange `#E07B39`, and border `#E2E8E0`. Dark mode uses the documented dark semantic equivalents.

## Typography and UI

Manrope is the documented typeface. Use a clear, compact type scale, 44px minimum touch targets, accessible contrast, and light cards with thin borders. New work should follow the semantic token layer rather than inventing page-local colors.

## Food photography

Photography is modern homemade food in one consistent bright home kitchen. The dish is the subject, with light neutral ceramic, light counter or wood/stone, soft daylight, gentle clean shadows, and believable home preparation. No logos, text, packaging, people, hands, clutter, plastic stock look, or theatrical fine-dining styling. See [`../PLANAM_RECIPE_IMAGE_MASTER_PROMPT.md`](../PLANAM_RECIPE_IMAGE_MASTER_PROMPT.md) and the self-contained [`../recipe-images/MASTER_STYLE.md`](../recipe-images/MASTER_STYLE.md).

## Unspecified rules

Exact logo geometry, logo clear-space rules, and final brand lockups are **TO BE FORMALIZED**. Do not invent them in implementation. Final paywall wording is also **TO BE FORMALIZED**; the product boundary is known: PRO belongs inside Health, not as a separate product.
