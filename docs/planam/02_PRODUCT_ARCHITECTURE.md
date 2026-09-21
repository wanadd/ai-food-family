# 02 Product Architecture

## Product shape

The home route `/` is the central “what matters now” surface, not a dashboard. A dynamic hero presents the most useful next action. Five primary tabs organize the product while keeping PLANAM central:

- PlanAm: current household decision and next action
- Menu: planned meals and recipe execution
- Shopping: unified household purchase center
- Health: person-aware nutrition and safety context
- Profile: who the household is and how it operates

## Domain composition

The product composes these domains:

1. Identity and active profile
2. Food identity and normalized units
3. Evidence and provenance
4. Nutrition and safety facts
5. Recipes and recipe images
6. Menus and meal planning
7. Shopping and pantry
8. Family members and participation
9. Telegram/platform integration

## Ownership boundaries

Evidence services own facts and provenance. Recipe generation may use evidence signals but does not become the authority for safety. Menu planning composes recipes and person policy. Shopping composes planned ingredients with manual household purchases and pantry state. The frontend renders API contracts and does not reimplement safety decisions.

## Reference material

- Domain map: [`../DOMAIN_ARCHITECTURE.md`](../DOMAIN_ARCHITECTURE.md)
- Current state: [`18_CURRENT_STATE.md`](18_CURRENT_STATE.md)
- Data architecture: [`06_DATA_ARCHITECTURE.md`](06_DATA_ARCHITECTURE.md)
