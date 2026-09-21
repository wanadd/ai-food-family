# 13 Telegram And Platform

## Host

PLANAM is a Telegram Mini App with Telegram authentication and a web application experience optimized for compact mobile interaction. The product should remain usable on desktop-sized Telegram surfaces as well.

## Integration principles

- Telegram identity establishes the user account; it does not replace household member identity.
- Platform data is an integration input, not a safety authority.
- Secrets and bot credentials stay in environment configuration and are never written to docs or logs.
- API contracts must work in personal mode before optional family features are enabled.

## Monetization boundary

Health is free at a useful baseline, with PRO depth inside the Health experience. The exact paywall copy and entitlements are **TO BE FORMALIZED**; no UI should invent medical promises.

## Future platform adapters

Delivery providers, notifications, and other integrations should sit behind explicit adapters. Provider-specific behavior must not leak into the canonical menu, shopping, or evidence contracts.
