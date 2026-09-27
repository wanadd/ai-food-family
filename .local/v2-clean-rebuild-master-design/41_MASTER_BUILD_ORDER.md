# Master Build Order

1. Freeze `PLANAM V2 UX/PRODUCT BASELINE v1.0`; OD-01..OD-15 accepted, including person-or-household planning ownership.
2. Implement W0 Core/Identity/API/Platform contracts and negative harness.
3. Implement W1 Core household scope and effective entitlements.
4. Implement W2 FoodProfile/Evidence/Safety with fail-closed import.
5. Implement W3 Recipe Gold V3 and canonical MediaAsset.
6. Implement W4 Planning, explicit empty, portions and replacement.
7. Implement W5 Shopping/Pantry/Receipt atomic and proposal flows.
8. Implement W6 Cooking/Consumption/Health separation.
9. Implement W7 Outbox/Jobs/Notification intents and Telegram adapter.
10. Implement W8 AppShell and client-neutral frontend behavior.
11. Implement W9 Admin/Analytics/Operations least privilege.
12. Execute W10 selective import only after backup/rehearsal acceptance.
13. Execute W11 full acceptance; require zero contradictions and F01-F20 coverage.
14. W12 maintenance-window replacement using measured thresholds; no dual writer.
15. W13 stabilization, then W14 archive/removal under explicit retirement gates.

Each step exits only when its wave's schema, API, frontend, security, safety, regression and recovery gates are green. Future MAX/Android/iOS work starts with provider/platform adapters and never forks this build order into client-owned business domains.
