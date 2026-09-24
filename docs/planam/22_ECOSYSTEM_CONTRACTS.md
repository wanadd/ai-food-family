# Ecosystem Contracts

## Domain modules

The accepted target modular monolith separates logical ownership for Core, Food Profile and Evidence, Recipe and Menu, Shopping and Pantry, Receipt/OCR, Voice, Cooking, Consumption, Health, AI and Memory, Notifications, Subscriptions/Entitlements, Admin, Analytics, Media, API/Mobile, Jobs/Integrations, and Schema/Testing.

These are architecture boundaries first. They do not create separate services or databases in this checkpoint.

## Cross-domain access

Direct cross-domain database reads are prohibited by default. Cross-domain interaction uses application contracts, projections, events, ports, or authorized APIs/services. Same `person_id` across domains does not grant universal data access.

API and mobile clients consume versioned contracts and do not become persistence owners. UI workflow is not the domain model.

## AI boundary

PLANAM AI is not identity authority, evidence authority, entitlement/payment authority, or an unrestricted database reader. Persistent AI memory must distinguish canonical structured Core facts, ImportantDate/PersonalEvent, explicit user preferences, domain-owned memories/facts, and ephemeral conversation context.

## Notifications and entitlements

Telegram is the current delivery channel, not the notification architecture. Domain triggers create NotificationIntent, notification orchestration and preferences select delivery, and adapters deliver through Telegram now or other channels later.

Entitlements are namespaced, for example `food.*`, `money.*`, `wellbeing.*`, and `planner.*`. Domains consume entitlement decisions/contracts rather than owning payment truth independently.

## Async jobs and raw data

DB-backed durable jobs/outbox are accepted first. Jobs must be durable, retryable, observable, idempotent, and ownership-explicit. Kafka or RabbitMQ is not introduced solely for appearance.

Sensitive/raw artifacts such as receipt images, OCR payloads, voice, temporary AI extraction artifacts, and sensitive intermediate data follow data minimization. Architecture must support purpose, retention policy, provenance, deletion, and derived-data handling.

## Portability tail

The accepted original P0_NOW portability tails are 22/22: profile/onboarding, family/personal scope, targets, evidence/ontology, recipe/library, planning, shopping, pantry/product, receipt/OCR, voice, cooking, consumption, health, AI, notifications, subscriptions/entitlements, admin, analytics, media, API/mobile, jobs/integrations, and schema/testing.

Retailer and Money remain future-compatible P1 areas. Shared conversation and physical Core service are P2. D17 adds an additional future Core tail for ImportantDate/PersonalEvent plus structured AI memory.
