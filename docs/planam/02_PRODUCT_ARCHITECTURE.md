# Product Architecture

PLANAM is a safety-oriented family food product organized as a modular monolith. Product behavior is expressed through contracts owned by Core, Food Profile and Evidence, Recipe and Menu, Shopping and Pantry, Health, AI, Notifications, and integrations.

The active UI may focus on one household, while the canonical model supports multiple households and scoped relationships. The product resolves the person and active policy before household aggregation. Planned, cooked, and consumed states remain separate. Product architecture follows [20_CORE_CONTRACT.md](20_CORE_CONTRACT.md) and [21_FOOD_PROFILE_AND_FACTS.md](21_FOOD_PROFILE_AND_FACTS.md).
