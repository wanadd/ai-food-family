# PLANAM Master Knowledge Base

This file is the repository entry point for PLANAM product, domain, architecture, evidence, brand, and delivery decisions. The detailed canonical documents live in [`docs/planam/`](docs/planam/).

## Product identity

PLANAM is a family AI assistant for nutrition, menus, purchases, leftovers, and health context. It removes the daily decision load around family nutrition. It is not a recipe catalog, calorie tracker, shopping list, or generic AI chat; those are supporting tools.

The product answers four practical questions: what to cook, what to buy, what is already at home, and what matters for health. The result is a ready decision, with AI operating in the background and the user seeing an actionable next step.

## Canonical map

- Product and experience: [`00_PROJECT_IDENTITY.md`](docs/planam/00_PROJECT_IDENTITY.md), [`01_PRODUCT_PRINCIPLES.md`](docs/planam/01_PRODUCT_PRINCIPLES.md), [`03_UX_AND_PRODUCT_BEHAVIOR.md`](docs/planam/03_UX_AND_PRODUCT_BEHAVIOR.md)
- Architecture and data: [`02_PRODUCT_ARCHITECTURE.md`](docs/planam/02_PRODUCT_ARCHITECTURE.md), [`05_TECH_ARCHITECTURE.md`](docs/planam/05_TECH_ARCHITECTURE.md), [`06_DATA_ARCHITECTURE.md`](docs/planam/06_DATA_ARCHITECTURE.md)
- Safety and food evidence: [`07_EVIDENCE_ENGINE.md`](docs/planam/07_EVIDENCE_ENGINE.md), [`08_NUTRITION_AND_SAFETY.md`](docs/planam/08_NUTRITION_AND_SAFETY.md)
- Recipe, menu, shopping, family: [`09_RECIPE_GOLD_V3.md`](docs/planam/09_RECIPE_GOLD_V3.md), [`10_MENU_ENGINE.md`](docs/planam/10_MENU_ENGINE.md), [`11_SHOPPING_AND_PANTRY.md`](docs/planam/11_SHOPPING_AND_PANTRY.md), [`12_FAMILY_AND_PERSON_MODEL.md`](docs/planam/12_FAMILY_AND_PERSON_MODEL.md)
- Platform and operations: [`13_TELEGRAM_AND_PLATFORM.md`](docs/planam/13_TELEGRAM_AND_PLATFORM.md), [`14_INFRASTRUCTURE_AND_DEPLOYMENT.md`](docs/planam/14_INFRASTRUCTURE_AND_DEPLOYMENT.md), [`15_TESTING_AND_QA.md`](docs/planam/15_TESTING_AND_QA.md)
- Governance: [`16_DO_NOT_DO.md`](docs/planam/16_DO_NOT_DO.md), [`17_DECISION_LOG.md`](docs/planam/17_DECISION_LOG.md), [`18_CURRENT_STATE.md`](docs/planam/18_CURRENT_STATE.md), [`19_ROADMAP.md`](docs/planam/19_ROADMAP.md)
- Recipe images: [`docs/recipe-images/README.md`](docs/recipe-images/README.md)

## Non-negotiable safety rules

Unknown is not safe and missing data is not zero. Family evaluation uses `BLOCK > ESCALATE > UNKNOWN > WARN > SAFE`. Allergies are hard exclusions. Person identity, participation, portions, provenance, and confidence remain explicit through every aggregation.

## Current checkpoint

The current branch and technical state are recorded in [`18_CURRENT_STATE.md`](docs/planam/18_CURRENT_STATE.md). The immediate next technical stage is `P0-SCHEMA-BOOTSTRAP-ORDER-01`; this checkpoint does not start it. The physical evidence schema is committed, while ORM adoption and bootstrap ordering remain blocked as documented.

## Portability rule

This knowledge base must explain PLANAM from the repository alone. It may link to implementation evidence, but it must not depend on chat history, local notes, external drives, or untracked `.local/` artifacts.
