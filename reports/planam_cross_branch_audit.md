# PLANAM Cross-Branch Audit

Gate report for **PLANAM Project-Wide Architecture Consolidation V1**.
Generated per cross-branch audit spec (read-only git inspection).

## Current branch

`sprint-0/planam-2026-foundation` (HEAD = `7523c0c`).

## All branches

```
audit/planam-master-audit
  main
  planam-recipe-engine-v1
  recipe-engine-v1
  recipe-import-broken-backup
  recipe-import-clean
  recipe-import-pipeline-v1
  release-candidate-ux
* sprint-0/planam-2026-foundation
  ux-foundation-v1
  ux-ui-refinement-v1
  remotes/origin/HEAD -> origin/main
  remotes/origin/main
  remotes/origin/recipe-engine-v1
  remotes/origin/recipe-import-clean
  remotes/origin/recipe-import-pipeline-v1
  remotes/origin/release-candidate-ux
  remotes/origin/sprint-0/planam-2026-foundation
  remotes/origin/ux-foundation-v1
  remotes/origin/ux-ui-refinement-v1
```

## Recent commits current branch

```
7523c0c (HEAD -> sprint-0/planam-2026-foundation) refactor(core): consolidate project-wide data and route architecture
fbc0177 (origin/sprint-0/planam-2026-foundation) fix(shopping): clean up menu generated shopping list
1190639 fix(recipes): render ingredient amounts with correct units
781589c feat(nutrition): aggregate menu nutrition and expose daily summary
98c88ae feat(recipes): persist nutrition summary and expose in UI
cd7f497 feat(recipes): add nutrition (КБЖУ), shopping grouping and photo readiness pipeline
7d32f06 feat(recipes): add to-taste ingredient model and readiness reports
d8adc43 feat(recipes): add safe ingredient commit and jsonb resync
2813678 feat(v1): canonical products + unit normalization + dry-run normalizer
2edbbf6 feat(v1): read-only recipe ingredient quality audit
ae431eb hotfix(infra): persist recipe images on server
2b27681 fix(v1): relocate pilot image files to correct recipe folders, avoid 404
0af763c fix(v1): resolve recipe image pilot ids by title not batch index
dccd388 feat(v1): add recipe image pilot pipeline
34bb96e fix(v1): show full recipe catalog
cc91e48 fix(v1): make shopping category migration conflict-safe
5e3d30c feat(v1): recipe foundation and image pipeline
e4a006d feat(v1): recipe foundation
8da98b3 refactor(v1): clean foundation and align shopping model
dc72454 feat(v1): sprint 1.5 polish and stabilization
```

## Diff summary: sprint-0/planam-2026-foundation vs origin/main

```
.env.production.example                            |     9 -
 .gitignore                                         |    33 -
 MASTER.md                                          |    56 -
 PROJECT_CONTEXT.md                                 |     8 -
 TASKS.md                                           |     2 -
 apps/api/.env.example                              |     8 -
 apps/api/app/config.py                             |    22 -
 apps/api/app/database.py                           |     7 +-
 apps/api/app/database_migrations.py                |   333 +-
 apps/api/app/main.py                               |     2 -
 apps/api/app/models/pantry.py                      |     2 +-
 apps/api/app/models/recipe.py                      |    39 -
 apps/api/app/models/recipe_engine.py               |   202 -
 apps/api/app/routers/collections.py                |   212 -
 apps/api/app/routers/menus.py                      |   144 +-
 apps/api/app/routers/recipe_engine_common.py       |    11 -
 apps/api/app/routers/recipes.py                    |   383 +-
 apps/api/app/routers/telegram_bot.py               |    29 +-
 apps/api/app/schemas/menu.py                       |     3 -
 apps/api/app/schemas/menu_nutrition.py             |    75 -
 apps/api/app/schemas/menu_overview.py              |    65 -
 apps/api/app/schemas/pantry.py                     |     4 +-
 apps/api/app/schemas/recipe.py                     |    27 -
 apps/api/app/schemas/recipe_collection.py          |    62 -
 apps/api/app/schemas/recipe_engine_api.py          |   122 -
 apps/api/app/schemas/recipe_search.py              |    64 -
 apps/api/app/services/admin_auth.py                |     2 +-
 apps/api/app/services/bot_menu.py                  |     3 +-
 apps/api/app/services/categories_v1.py             |   122 -
 apps/api/app/services/family_member_nutrition.py   |     4 +-
 apps/api/app/services/home_next_action.py          |   132 -
 apps/api/app/services/ingredient_format.py         |   129 -
 apps/api/app/services/meal_attendance.py           |    27 -
 apps/api/app/services/menu.py                      |    26 -
 apps/api/app/services/menu_ai.py                   |    10 +-
 apps/api/app/services/menu_ai_legacy.py            |    70 +-
 apps/api/app/services/menu_ai_parsing.py           |   168 -
 apps/api/app/services/menu_overview.py             |    19 +-
 apps/api/app/services/menu_recipe_plan.py          |   438 -
 apps/api/app/services/normalization/__init__.py    |    47 -
 apps/api/app/services/normalization/amounts.py     |    43 -
 apps/api/app/services/normalization/categories.py  |    55 -
 apps/api/app/services/normalization/ingredients.py |    48 -
 apps/api/app/services/normalization/menu.py        |    23 -
 .../app/services/normalization/notifications.py    |    99 -
 apps/api/app/services/normalization/profile.py     |   121 -
 apps/api/app/services/normalization/shopping.py    |    23 -
 .../api/app/services/normalization/subscription.py |    72 -
 apps/api/app/services/notifications.py             |    24 +-
 apps/api/app/services/nutrition/__init__.py        |     1 -
 apps/api/app/services/nutrition/plan_aggregator.py |   395 -
 apps/api/app/services/nutrition_profile.py         |     3 -
 apps/api/app/services/pantry.py                    |     2 +-
 apps/api/app/services/recipe_storage.py            |    44 +-
 apps/api/app/services/recipes.py                   |   479 +
 apps/api/app/services/recipes/__init__.py          |   107 -
 apps/api/app/services/recipes/access.py            |    59 -
 apps/api/app/services/recipes/authoring.py         |   173 -
 apps/api/app/services/recipes/catalog.py           |   290 -
 apps/api/app/services/recipes/collections.py       |   364 -
 apps/api/app/services/recipes/cooking_history.py   |   180 -
 apps/api/app/services/recipes/explainability.py    |   245 -
 .../api/app/services/recipes/family_preferences.py |   183 -
 apps/api/app/services/recipes/mapper.py            |   134 -
 apps/api/app/services/recipes/recommendations.py   |    62 -
 .../app/services/recipes/repositories/__init__.py  |    17 -
 .../services/recipes/repositories/collections.py   |   100 -
 .../services/recipes/repositories/explanations.py  |    57 -
 .../app/services/recipes/repositories/history.py   |    90 -
 .../services/recipes/repositories/preferences.py   |    60 -
 .../app/services/recipes/repositories/scenarios.py |    60 -
 apps/api/app/services/recipes/repository.py        |   136 -
 apps/api/app/services/recipes/scenarios.py         |   203 -
 apps/api/app/services/recipes/search.py            |    99 -
 apps/api/app/services/recipes/title_normalize.py   |    55 -
 apps/api/app/services/recipes/types.py             |    69 -
 apps/api/app/services/shopping_categories.py       |   239 +-
 .../app/services/shopping_category_migration.py    |   274 -
 apps/api/app/services/shopping_category_service.py |   115 +-
 apps/api/app/services/shopping_item_utils.py       |   202 +-
 apps/api/app/services/shopping_list.py             |    31 +-
 apps/api/app/services/subscription.py              |     4 +-
 apps/api/app/services/subscription_catalog.py      |     8 +-
 apps/api/requirements.txt                          |     1 -
 apps/api/tests/test_categories_v1.py               |    45 -
 apps/api/tests/test_home_next_action.py            |    72 -
 apps/api/tests/test_ingredient_display_amounts.py  |   116 -
 apps/api/tests/test_ingredient_normalization.py    |   230 -
 apps/api/tests/test_menu_ai_parsing.py             |    97 -
 apps/api/tests/test_menu_nutrition_aggregation.py  |   183 -
 apps/api/tests/test_menu_recipe_plan.py            |   225 -
 apps/api/tests/test_menu_replace.py                |   176 -
 apps/api/tests/test_normalization_amounts.py       |    57 -
 apps/api/tests/test_normalization_categories.py    |    46 -
 .../tests/test_normalization_menu_ingredients.py   |    58 -
 .../test_notification_settings_normalization.py    |    59 -
 apps/api/tests/test_nutrition_pipeline.py          |   193 -
 apps/api/tests/test_profile_normalization.py       |    67 -
 apps/api/tests/test_project_health_audit.py        |    96 -
 apps/api/tests/test_recipe_image_resolver.py       |   116 -
 apps/api/tests/test_recipe_ingredient_audit.py     |   100 -
 apps/api/tests/test_recipe_nutrition_summary.py    |   228 -
 apps/api/tests/test_recipe_write_access.py         |   102 -
 apps/api/tests/test_recipes_catalog.py             |   203 -
 apps/api/tests/test_repair_image_files.py          |    59 -
 apps/api/tests/test_shopping_category_migration.py |   200 -
 apps/api/tests/test_shopping_category_service.py   |   171 -
 apps/api/tests/test_shopping_infer_category.py     |    70 -
 apps/api/tests/test_shopping_list_cleanup.py       |   177 -
 apps/api/tests/test_subscription_normalization.py  |    47 -
 apps/api/tests/test_telegram_webhook_security.py   |    57 -
 apps/api/tests/test_to_taste_migration.py          |   204 -
 apps/web/.env.example                              |     7 -
 apps/web/Dockerfile.prod                           |     2 -
 apps/web/app/account/ams/page.tsx                  |     8 -
 apps/web/app/account/family/page.tsx               |     8 -
 apps/web/app/account/notifications/page.tsx        |     8 -
 apps/web/app/account/nutrition/page.tsx            |    21 -
 apps/web/app/account/page.tsx                      |     8 -
 apps/web/app/account/settings/about/page.tsx       |     1 -
 apps/web/app/account/settings/account/page.tsx     |     1 -
 apps/web/app/account/settings/delete-data/page.tsx |     1 -
 apps/web/app/account/settings/documents/page.tsx   |     1 -
 apps/web/app/account/settings/page.tsx             |    39 -
 apps/web/app/account/settings/support/page.tsx     |     1 -
 .../web/app/account/subscription/checkout/page.tsx |    14 -
 apps/web/app/account/subscription/page.tsx         |    14 -
 apps/web/app/dev/planam-2026/page.tsx              |   150 -
 apps/web/app/family/page.tsx                       |     2 -
 apps/web/app/globals.css                           |   150 -
 apps/web/app/health/care/page.tsx                  |     7 -
 apps/web/app/health/chat/HealthChatPageClient.tsx  |    98 -
 apps/web/app/health/chat/page.tsx                  |    11 -
 apps/web/app/health/page.tsx                       |    11 -
 apps/web/app/health/today/page.tsx                 |    11 -
 apps/web/app/home/page.tsx                         |     9 -
 apps/web/app/home/pantry/page.tsx                  |     8 -
 apps/web/app/home/shopping/page.tsx                |    13 -
 apps/web/app/layout.tsx                            |    17 +-
 apps/web/app/menu/collections/[id]/page.tsx        |     6 -
 apps/web/app/menu/collections/page.tsx             |    11 -
 apps/web/app/menu/current/page.tsx                 |     7 -
 apps/web/app/menu/event/page.tsx                   |    38 +-
 apps/web/app/menu/favorites/page.tsx               |    11 -
 apps/web/app/menu/generate/page.tsx                |     7 -
 apps/web/app/menu/leftovers/page.tsx               |     7 +-
 apps/web/app/menu/loading.tsx                      |     9 +-
 apps/web/app/menu/page.tsx                         |     7 -
 apps/web/app/menu/recipes/page.tsx                 |    25 -
 apps/web/app/menu/scenarios/page.tsx               |     8 -
 apps/web/app/notifications/page.tsx                |    48 +-
 apps/web/app/nutritionist/care/page.tsx            |     3 +-
 apps/web/app/nutritionist/chat/page.tsx            |    92 +-
 apps/web/app/nutritionist/page.tsx                 |     8 +-
 apps/web/app/onboarding/page.tsx                   |     7 -
 apps/web/app/page.tsx                              |    12 -
 apps/web/app/pantry/loading.tsx                    |     9 +-
 apps/web/app/pantry/page.tsx                       |     7 +-
 apps/web/app/plan/generate/page.tsx                |     8 -
 apps/web/app/plan/page.tsx                         |     8 -
 apps/web/app/plan/recipes/[id]/page.tsx            |    17 -
 apps/web/app/plan/recipes/page.tsx                 |     8 -
 apps/web/app/plan/today/page.tsx                   |    14 -
 apps/web/app/profile/nutrition/page.tsx            |    14 +-
 apps/web/app/profile/page.tsx                      |     2 -
 apps/web/app/progress/page.tsx                     |    14 +-
 apps/web/app/recipes/[id]/RecipeDetailLegacy.tsx   |    85 -
 apps/web/app/recipes/[id]/page.tsx                 |    86 +-
 apps/web/app/recipes/page.tsx                      |     7 +-
 apps/web/app/settings/page.tsx                     |     2 -
 apps/web/app/shopping/leftovers/page.tsx           |    11 -
 apps/web/app/shopping/loading.tsx                  |     9 +-
 apps/web/app/shopping/page.tsx                     |    16 +-
 apps/web/app/shopping/pantry/page.tsx              |    12 -
 apps/web/app/subscription/page.tsx                 |     7 -
 apps/web/app/wellness/chat/page.tsx                |     8 -
 apps/web/app/wellness/page.tsx                     |     8 -
 apps/web/components/AppProviders.tsx               |    27 +-
 apps/web/components/TelegramProvider.tsx           |    76 +-
 apps/web/components/app-mode/ModeSwitcher.tsx      |    22 +-
 apps/web/components/auth/AppGate.tsx               |    31 +-
 apps/web/components/care/CareSettingsPanel.tsx     |   148 +-
 apps/web/components/care/CareTelegramLinkCard.tsx  |     8 +-
 apps/web/components/dom-2026/Leftovers2026.tsx     |   254 -
 .../web/components/dom-2026/LeftoversSheet2026.tsx |   228 -
 .../components/dom-2026/MealOutcomeSheet2026.tsx   |   235 -
 apps/web/components/dom-2026/Pantry2026.tsx        |   243 -
 apps/web/components/dom-2026/Shopping2026.tsx      |   390 -
 apps/web/components/dom-2026/index.ts              |     5 -
 apps/web/components/family/AddPersonSheet.tsx      |    22 +-
 apps/web/components/family/FamilyDashboard.tsx     |   110 +-
 apps/web/components/family/FamilyManageSheet.tsx   |    35 +-
 apps/web/components/family/InviteSheet.tsx         |    33 +-
 apps/web/components/family/MemberCard.tsx          |    38 +-
 apps/web/components/family/MemberForm.tsx          |    25 +-
 apps/web/components/family/RoleBadge.tsx           |     8 +-
 .../family/VirtualMemberNutritionForm.tsx          |    68 +-
 apps/web/components/home-2026/Home2026.tsx         |   193 -
 .../components/home-2026/MealFallbackPlate2026.tsx |    42 -
 apps/web/components/home-2026/PlanAmHero2026.tsx   |   138 -
 .../components/home-2026/PlanAmStatusRows2026.tsx  |    83 -
 apps/web/components/home-2026/index.ts             |     2 -
 apps/web/components/home/PlanAmHome.tsx            |   424 +-
 apps/web/components/layout/AppShell.tsx            |     5 +-
 apps/web/components/layout/AppShellBridge.tsx      |    46 -
 apps/web/components/layout/BottomBackButton.tsx    |    37 +
 apps/web/components/layout/BottomNav.tsx           |     1 +
 apps/web/components/layout/BottomNavigation.tsx    |    40 +-
 apps/web/components/layout/ScreenBackNav.tsx       |     4 +-
 apps/web/components/layout/ScreenLayout.tsx        |     8 +-
 apps/web/components/layout/SectionHub.tsx          |    68 -
 apps/web/components/layout/SegmentedTabs.tsx       |    53 -
 apps/web/components/layout/StickyBottomBar.tsx     |     2 +-
 apps/web/components/layout/TopBackLink.tsx         |     3 +
 apps/web/components/menu/MealCheckinPanel.tsx      |    24 +-
 apps/web/components/menu/MealLeftoversPage.tsx     |    46 +-
 apps/web/components/menu/MenuChooseVariants.tsx    |    19 +-
 apps/web/components/menu/MenuCurrentView.tsx       |   254 +-
 apps/web/components/menu/MenuDayOverview.tsx       |   247 -
 apps/web/components/menu/MenuDayPicker.tsx         |     6 +-
 apps/web/components/menu/MenuHub.tsx               |   498 +-
 apps/web/components/menu/MenuPlanner.tsx           |   110 +-
 apps/web/components/menu/MenuPlannerSection.tsx    |     4 +-
 apps/web/components/menu/MenuQuickActionsSheet.tsx |    52 -
 apps/web/components/menu/MenuSectionLayout.tsx     |    29 -
 apps/web/components/menu/MenuSettingsPage.tsx      |    27 +-
 apps/web/components/menu/MenuSubTabs.tsx           |    19 -
 apps/web/components/menu/MenuVariantCard.tsx       |    44 +-
 apps/web/components/menu/ReplaceDishModal.tsx      |    26 +-
 .../components/monetization-2026/AmsHub2026.tsx    |   128 -
 .../HomeMonetizationBanner2026.tsx                 |    45 -
 .../monetization-2026/PaymentStub2026.tsx          |   111 -
 .../monetization-2026/PaywallProvider.tsx          |    61 -
 .../monetization-2026/PaywallSheet2026.tsx         |    94 -
 .../components/monetization-2026/PlanCard2026.tsx  |    79 -
 .../monetization-2026/SubscriptionHub2026.tsx      |   206 -
 .../monetization-2026/SubscriptionOffline2026.tsx  |    83 -
 .../monetization-2026/TrialStatus2026.tsx          |    33 -
 apps/web/components/monetization-2026/index.ts     |     5 -
 .../notifications/NotificationSettingsForm.tsx     |    88 +-
 .../components/notifications/NotificationsView.tsx |    83 -
 .../components/nutrition-profile/NumberInput.tsx   |     6 +-
 .../NutritionGoalDetailsFields.tsx                 |    20 +-
 .../nutrition-profile/NutritionProfileForm.tsx     |   108 +-
 .../nutrition-profile/NutritionSection.tsx         |    14 +-
 .../web/components/nutrition-profile/ToggleRow.tsx |     8 +-
 .../components/nutritionist/HealthTodayView.tsx    |   382 -
 .../nutritionist/NutritionistAdviceCard.tsx        |    20 +-
 .../components/nutritionist/NutritionistChat.tsx   |    35 +-
 .../nutritionist/NutritionistDashboard.tsx         |   520 +-
 .../components/nutritionist/WaterIntakePanel.tsx   |    14 +-
 .../onboarding-2026/Onboarding2026Flow.tsx         |   309 -
 .../onboarding-2026/Onboarding2026Redirect.tsx     |    36 -
 .../onboarding-2026/OnboardingChipGrid2026.tsx     |    91 -
 .../onboarding-2026/OnboardingGenerateStep2026.tsx |    79 -
 .../onboarding-2026/OnboardingProgress2026.tsx     |    26 -
 .../onboarding-2026/OnboardingWowReveal2026.tsx    |    63 -
 .../onboarding-2026/TrialWelcomeCard2026.tsx       |    31 -
 apps/web/components/onboarding-2026/index.ts       |     2 -
 .../components/onboarding/ChipSelectWithCustom.tsx |    99 +
 .../components/onboarding/OnboardingComplete.tsx   |    94 +
 .../web/components/onboarding/OnboardingWizard.tsx |   222 +
 apps/web/components/onboarding/ProgressBar.tsx     |    25 +
 apps/web/components/onboarding/StepContent.tsx     |   111 +
 apps/web/components/onboarding/StepNavigation.tsx  |    50 +
 .../components/pantry/PantryCategorySection.tsx    |     8 +-
 apps/web/components/pantry/PantryDashboard.tsx     |   132 +-
 apps/web/components/pantry/PantryItemCard.tsx      |    22 +-
 apps/web/components/pantry/PantryItemForm.tsx      |    29 +-
 apps/web/components/pantry/PantryItemRow.tsx       |    16 +-
 .../components/plan-2026/DayNutritionCard2026.tsx  |   126 -
 apps/web/components/plan-2026/PlanGenerate2026.tsx |   288 -
 apps/web/components/plan-2026/PlanMealCard2026.tsx |   138 -
 .../plan-2026/PlanTimelineSection2026.tsx          |    46 -
 apps/web/components/plan-2026/PlanToday2026.tsx    |   316 -
 apps/web/components/plan-2026/PlanWeek2026.tsx     |   131 -
 .../components/plan-2026/ReplaceDishSheet2026.tsx  |   188 -
 apps/web/components/plan-2026/index.ts             |     5 -
 .../planam-2026/account/AccountHub2026.tsx         |   110 -
 .../planam-2026/cards/ActionCard2026.tsx           |    80 -
 .../components/planam-2026/cards/HeroCard2026.tsx  |   103 -
 .../planam-2026/cards/InsightCard2026.tsx          |    47 -
 .../planam-2026/cards/MetricCard2026.tsx           |    44 -
 apps/web/components/planam-2026/index.ts           |    15 -
 .../components/planam-2026/layout/AppShell2026.tsx |    26 -
 .../planam-2026/layout/ShellHeader2026.tsx         |    40 -
 .../navigation/BottomNavigation2026.tsx            |    85 -
 .../planam-2026/navigation/NavIcon2026.tsx         |   170 -
 .../planam-2026/navigation/ScreenBack2026.tsx      |    42 -
 .../planam-2026/navigation/SectionSubTabs2026.tsx  |    54 -
 .../navigation/TelegramBackBridge2026.tsx          |    12 -
 .../navigation/useTelegramBackButton2026.ts        |    64 -
 .../planam-2026/screens/RoutePlaceholder2026.tsx   |    25 -
 .../components/planam-2026/theme/ThemeProvider.tsx |   134 -
 .../planam-2026/theme/ThemeToggle2026.tsx          |    50 -
 .../components/planam-2026/ui/BottomSheet2026.tsx  |    62 -
 apps/web/components/planam-2026/ui/Button2026.tsx  |    58 -
 apps/web/components/planam-2026/ui/Card2026.tsx    |    34 -
 .../components/planam-2026/ui/EmptyState2026.tsx   |    46 -
 .../web/components/planam-2026/ui/Skeleton2026.tsx |    30 -
 apps/web/components/profile/ProfileDashboard.tsx   |    44 +-
 apps/web/components/profile/ProfileModeControl.tsx |    18 +-
 apps/web/components/progress/ProgressDashboard.tsx |   124 +-
 apps/web/components/progress/ProgressProLocked.tsx |    25 +-
 .../components/recipes-2026/MenuSlotSheet2026.tsx  |   195 -
 .../components/recipes-2026/RecipeCatalog2026.tsx  |   366 -
 .../components/recipes-2026/RecipeDetail2026.tsx   |   439 -
 .../components/recipes-2026/RecipeGridCard2026.tsx |   112 -
 .../components/recipes-2026/RecipeImage2026.tsx    |    61 -
 apps/web/components/recipes-2026/index.ts          |     4 -
 .../components/recipes/CollectionDetailView.tsx    |   162 -
 apps/web/components/recipes/CollectionsView.tsx    |   169 -
 apps/web/components/recipes/FavoritesView.tsx      |   132 -
 apps/web/components/recipes/FilterChip.tsx         |    25 -
 apps/web/components/recipes/FromPantrySection.tsx  |   158 -
 apps/web/components/recipes/RecipeCard.tsx         |    38 +-
 apps/web/components/recipes/RecipeCatalog.tsx      |   378 +
 .../components/recipes/RecipeCatalogSections.tsx   |    62 +-
 apps/web/components/recipes/RecipeDetailModal.tsx  |   560 +-
 .../components/recipes/RecipeDetailMorePanel.tsx   |   352 -
 apps/web/components/recipes/RecipeFiltersSheet.tsx |   186 -
 apps/web/components/recipes/RecipeListSkeleton.tsx |    23 -
 apps/web/components/recipes/RecipeResultsList.tsx  |    33 -
 apps/web/components/recipes/RecipesView.tsx        |   365 -
 apps/web/components/recipes/ScenarioChips.tsx      |    84 -
 apps/web/components/settings/SettingsScaffold.tsx  |    49 +-
 apps/web/components/shopping/CategoryPicker.tsx    |    30 +-
 .../shopping/ShoppingCategorySection.tsx           |    10 +-
 .../components/shopping/ShoppingCategorySheet.tsx  |    15 +-
 apps/web/components/shopping/ShoppingItemRow.tsx   |    18 +-
 apps/web/components/shopping/ShoppingItemSheet.tsx |    25 +-
 apps/web/components/shopping/ShoppingListView.tsx  |   114 +-
 .../components/shopping/ShoppingSectionLayout.tsx  |    54 -
 apps/web/components/shopping/ShoppingSubTabs.tsx   |    18 -
 .../components/subscription/AmaConfirmDialog.tsx   |    93 +-
 .../subscription/SubscriptionDashboard.tsx         |   139 +-
 .../subscription/SubscriptionProvider.tsx          |   137 -
 apps/web/components/ui/HubTile.tsx                 |   101 -
 apps/web/components/ui/Sheet.tsx                   |    10 +-
 apps/web/components/ui/Skeleton.tsx                |   111 -
 apps/web/components/ui/ToastProvider.tsx           |    11 +-
 .../components/wellness-2026/WaterIntake2026.tsx   |   121 -
 .../components/wellness-2026/WellnessChat2026.tsx  |   100 -
 .../components/wellness-2026/WellnessChip2026.tsx  |    76 -
 .../wellness-2026/WellnessDayRing2026.tsx          |    39 -
 .../wellness-2026/WellnessGoalCard2026.tsx         |    62 -
 .../components/wellness-2026/WellnessHome2026.tsx  |   274 -
 .../wellness-2026/WellnessInsight2026.tsx          |    34 -
 .../wellness-2026/WellnessTodayCard2026.tsx        |    28 -
 .../wellness-2026/WellnessWeekStrip2026.tsx        |    42 -
 apps/web/components/wellness-2026/index.ts         |     3 -
 apps/web/lib/api-client.ts                         |    69 +-
 apps/web/lib/app-mode/api.ts                       |    64 +-
 apps/web/lib/cache/session-cache.ts                |   108 -
 apps/web/lib/cache/use-cached-query.ts             |   105 -
 apps/web/lib/dom/pantry-sections.ts                |    44 -
 apps/web/lib/dom/shopping-groups.ts                |    49 -
 apps/web/lib/home/home-2026-data.ts                |   181 -
 apps/web/lib/home/planam-hero-2026.test.ts         |   153 -
 apps/web/lib/home/planam-hero-2026.ts              |   233 -
 apps/web/lib/home/redirect-path-2026.ts            |    42 -
 apps/web/lib/home/use-compact-viewport.ts          |    21 -
 apps/web/lib/meal-checkins/api.ts                  |     4 +-
 apps/web/lib/menu/api.ts                           |   167 +-
 apps/web/lib/menu/labels.ts                        |     6 +-
 apps/web/lib/menu/menu-days.ts                     |    33 -
 apps/web/lib/menu/overview-types.ts                |    32 +-
 apps/web/lib/menu/planner-options.ts               |     4 +-
 apps/web/lib/menu/quick-actions.ts                 |    52 -
 apps/web/lib/menu/replace-slot.ts                  |    52 -
 apps/web/lib/menu/types.ts                         |     2 -
 apps/web/lib/monetization/billing-status.ts        |   162 -
 apps/web/lib/monetization/paths.ts                 |    10 -
 apps/web/lib/monetization/paywall.ts               |    82 -
 apps/web/lib/monetization/plan-catalog-2026.ts     |   127 -
 apps/web/lib/monetization/trial-config.ts          |    11 -
 apps/web/lib/navigation/back-navigation-2026.ts    |    74 -
 apps/web/lib/navigation/nav-config-2026.ts         |   356 -
 apps/web/lib/navigation/nav-config.ts              |   124 -
 apps/web/lib/navigation/return-to.ts               |    66 +-
 apps/web/lib/navigation/route-migration-2026.ts    |    61 -
 apps/web/lib/nutritionist/family-insights.ts       |    12 +-
 apps/web/lib/onboarding-2026/config.ts             |   151 -
 apps/web/lib/pantry/api.ts                         |     2 +-
 apps/web/lib/pantry/types.ts                       |     2 +-
 apps/web/lib/plan/add-to-shopping.ts               |    21 -
 apps/web/lib/plan/plan-paths.ts                    |    46 -
 apps/web/lib/plan/plan-today.ts                    |   162 -
 apps/web/lib/planam/cn.ts                          |     6 -
 apps/web/lib/planam/embedded-2026.ts               |    15 -
 apps/web/lib/planam/feature-flags.ts               |    21 -
 apps/web/lib/planam/layout-constants-2026.ts       |     3 -
 apps/web/lib/planam/onboarding-gate.ts             |    34 -
 apps/web/lib/planam/planam-2026-page.ts            |    19 -
 apps/web/lib/planam/routes.ts                      |    91 -
 apps/web/lib/planam/theme-document.ts              |    81 -
 apps/web/lib/planam/theme.ts                       |    52 -
 apps/web/lib/planam/ui-scope.ts                    |    21 -
 apps/web/lib/progress/api.ts                       |     8 -
 apps/web/lib/recipes/analysis-api.ts               |    54 +-
 apps/web/lib/recipes/api.ts                        |   143 -
 apps/web/lib/recipes/catalog-sections.ts           |    11 -
 apps/web/lib/recipes/ingredient-amount.ts          |    36 -
 apps/web/lib/recipes/menu-from-recipe.ts           |    61 -
 apps/web/lib/recipes/nutrition.ts                  |    90 -
 apps/web/lib/recipes/recipe-media.ts               |   102 -
 apps/web/lib/recipes/types.ts                      |   158 -
 apps/web/lib/shopping/categories-v1.ts             |    92 -
 apps/web/lib/shopping/category-suggest.test.ts     |    38 -
 apps/web/lib/shopping/category-suggest.ts          |    71 +-
 apps/web/lib/shopping/labels.ts                    |    31 +-
 apps/web/lib/shopping/types.ts                     |     4 +-
 apps/web/lib/subscription/ama.ts                   |     2 -
 apps/web/lib/telegram-webapp.ts                    |   203 +-
 apps/web/lib/wellness/goal-labels.ts               |    27 -
 apps/web/lib/wellness/home-wellness.ts             |    67 -
 apps/web/lib/wellness/week-strip.ts                |    57 -
 apps/web/lib/wellness/wellness-insight.ts          |    88 -
 apps/web/lib/wellness/wellness-status.ts           |   155 -
 apps/web/middleware.ts                             |    61 -
 apps/web/package-lock.json                         |    19 +
 apps/web/package.json                              |     1 +
 apps/web/public/brand/planam-icon.svg              |     5 -
 apps/web/public/brand/planam-mark.svg              |     4 -
 apps/web/public/recipe-images/.gitkeep             |     0
 apps/web/tailwind.config.ts                        |    89 +-
 apps/web/tsconfig.tsbuildinfo                      |     1 -
 backend/data/nutrition_reference_seed.json         |  1105 --
 backend/pytest.ini                                 |     3 -
 backend/scripts/_image_paths.py                    |    85 -
 backend/scripts/analyze_povarenok_dataset.py       |   466 -
 backend/scripts/analyze_recipe_dataset.py          |   340 -
 .../scripts/apply_calculated_nutrition_updates.py  |   466 -
 backend/scripts/apply_nutrition_backfill.py        |   489 -
 backend/scripts/apply_recipe_images.py             |   232 -
 backend/scripts/apply_recipe_steps_updates.py      |   375 -
 backend/scripts/archive_placeholder_recipes.py     |    92 -
 .../scripts/audit_beverage_nutrition_strategy.py   |   395 -
 backend/scripts/audit_menu_nutrition_readiness.py  |   220 -
 backend/scripts/audit_nutrition_update_deltas.py   |   506 -
 backend/scripts/audit_povarenok_jsonl.py           |   365 -
 backend/scripts/audit_project_health.py            |   513 -
 backend/scripts/audit_recipe_catalog.py            |   331 -
 backend/scripts/audit_recipe_duplicates.py         |   230 -
 backend/scripts/audit_recipe_images.py             |   104 -
 .../audit_recipe_ingredient_display_amounts.py     |   209 -
 backend/scripts/audit_recipe_ingredients.py        |   503 -
 backend/scripts/audit_recipe_steps_after_update.py |   141 -
 backend/scripts/audit_recipe_steps_quality.py      |   341 -
 backend/scripts/audit_recipe_steps_v2.py           |   231 -
 backend/scripts/audit_remaining_nutrition_gaps.py  |   470 -
 backend/scripts/audit_weak_steps_remediation.py    |   340 -
 backend/scripts/build_enrichment_batch.py          |   200 -
 backend/scripts/build_holiday_kids_steps_batch.py  |   263 -
 backend/scripts/build_holiday_kids_steps_update.py |   312 -
 backend/scripts/build_planam_v1_catalog.py         |   361 -
 backend/scripts/build_recipe_image_prompts.py      |   118 -
 backend/scripts/build_remaining_weak_groups.py     |   356 -
 backend/scripts/build_simple_beverage_updates.py   |   354 -
 .../scripts/build_steps_update_from_enrichment.py  |   299 -
 .../scripts/build_verified_nutrition_updates.py    |   281 -
 backend/scripts/calculate_nutrition.py             |   275 -
 .../scripts/calculate_recipe_nutrition_preview.py  |   530 -
 .../scripts/calculate_recipe_nutrition_summary.py  |   436 -
 backend/scripts/canonical_products.py              |   426 -
 backend/scripts/convert_enriched_to_import_json.py |   330 -
 .../convert_nutrition_backfill_to_update_json.py   |   231 -
 backend/scripts/convert_povarenok.py               |   425 -
 backend/scripts/evaluate_photo_prompt_readiness.py |   151 -
 .../scripts/export_calculated_nutrition_updates.py |   356 -
 backend/scripts/generate_shopping_list_groups.py   |   174 -
 backend/scripts/import_recipes.py                  |   549 -
 backend/scripts/migrate_to_taste_ingredients.py    |   452 -
 backend/scripts/normalize_ingredient_amounts.py    |   689 -
 backend/scripts/normalize_recipe_ingredients.py    |   573 -
 backend/scripts/nutrition_data.py                  |   353 -
 .../scripts/nutrition_shopping_photo_pipeline.py   |   236 -
 backend/scripts/openai_recipe_image_client.py      |   219 -
 backend/scripts/plan_nutrition_backfill.py         |   357 -
 backend/scripts/plan_recipe_dedup.py               |   215 -
 .../scripts/prepare_povarenok_enrichment_input.py  |   256 -
 backend/scripts/process_recipe_images.py           |   143 -
 backend/scripts/recipe_id_resolver.py              |    60 -
 backend/scripts/recipe_image_utils.py              |   252 -
 backend/scripts/recipe_nutrition_calculator.py     |   211 -
 backend/scripts/repair_recipe_image_assignments.py |   219 -
 backend/scripts/report_recipe_readiness.py         |   221 -
 backend/scripts/resync_recipe_ingredients_jsonb.py |   269 -
 backend/scripts/run_enrichment_pilot.py            |   444 -
 backend/scripts/run_nutrition_backfill.py          |   437 -
 backend/scripts/run_recipe_image_pilot.py          |   295 -
 backend/scripts/run_steps_enrichment.py            |   965 --
 backend/scripts/select_povarenok_candidates.py     |   370 -
 backup_before_import_10.sql                        |   Bin 512178 -> 0 bytes
 backup_before_import_100.sql                       |   Bin 771986 -> 0 bytes
 data/planam_v1_canonical_products.json             |  1487 --
 data/planam_v1_image_pilot_batch.json              |   192 -
 data/planam_v1_nutrition_facts.json                |  1083 --
 data/planam_v1_recipes.json                        | 16189 -------------------
 deploy/nginx/nginx.conf                            |     5 -
 deploy/nginx/templates/app-init.conf.template      |    58 +-
 deploy/nginx/templates/app-ssl.conf.template       |    68 +-
 docker-compose.prod.yml                            |    16 -
 docker-compose.yml                                 |    10 -
 docs/ADMIN_PANEL_INCIDENT_AUDIT.md                 |   569 -
 docs/BETA_HARDENING_REPORT.md                      |   106 -
 docs/BETA_READINESS_AUDIT.md                       |   322 -
 docs/CODEBASE_INDEX.md                             |   930 --
 docs/DOMAIN_ARCHITECTURE.md                        |   697 -
 docs/NAVIGATION_GRAPH.md                           |   517 -
 docs/NAVIGATION_MAP.md                             |    66 -
 docs/PLANAM_2026_COLOR_FIX_REPORT.md               |    83 -
 docs/PLANAM_2026_DECISION_RECORD.md                |    79 -
 docs/PLANAM_2026_FINAL_UX_QA_REPORT.md             |   136 -
 docs/PLANAM_2026_IMPLEMENTATION_ROADMAP.md         |   712 -
 docs/PLANAM_2026_PRODUCT_BLUEPRINT.md              |   757 -
 docs/PLANAM_COLOR_SYSTEM_V1.md                     |    42 -
 docs/PLANAM_CONVERSION_FUNNEL_2026.md              |   316 -
 docs/PLANAM_CURRENT_STATE_ACTIONS.md               |   248 -
 docs/PLANAM_CURRENT_STATE_COMPONENTS.md            |   149 -
 docs/PLANAM_CURRENT_STATE_DATA.md                  |   250 -
 docs/PLANAM_CURRENT_STATE_LAYOUTS.md               |   179 -
 docs/PLANAM_CURRENT_STATE_MASTER.md                |   229 -
 docs/PLANAM_CURRENT_STATE_NAVIGATION.md            |   218 -
 docs/PLANAM_CURRENT_STATE_OVERLAYS.md              |    89 -
 docs/PLANAM_CURRENT_STATE_SCREENS.md               |   337 -
 docs/PLANAM_CURRENT_STATE_USER_FLOWS.md            |   310 -
 docs/PLANAM_DESIGN_SYSTEM_2026.md                  |   769 -
 docs/PLANAM_FINAL_PRODUCT_REVIEW.md                |   402 -
 ...AM_HOTFIX_SHOPPING_CATEGORY_MIGRATION_REPORT.md |   164 -
 docs/PLANAM_LEGACY_DECOMMISSION_AUDIT.md           |   686 -
 docs/PLANAM_LEGACY_REMOVAL_BACKLOG.md              |   115 -
 docs/PLANAM_NAVIGATION_LEGACY_AUDIT.md             |   327 -
 docs/PLANAM_NOTIFICATION_SYSTEM_2026.md            |   289 -
 docs/PLANAM_PAYMENT_ARCHITECTURE_2026.md           |   114 -
 docs/PLANAM_PRODUCTION_UX_POLISH_V1_REPORT.md      |   127 -
 docs/PLANAM_RECIPES_CATALOG_AUDIT_AND_FIX.md       |   111 -
 docs/PLANAM_RECIPE_CATALOG_QUALITY_V1_REPORT.md    |   125 -
 docs/PLANAM_RECIPE_DB_GO_REPORT.md                 |   159 -
 docs/PLANAM_RECIPE_MEDIA_ARCHITECTURE.md           |   265 -
 docs/PLANAM_RECIPE_MENU_INTEGRATION_V1_REPORT.md   |   103 -
 docs/PLANAM_RECIPE_REPLACE_FLOW_V1_REPORT.md       |   106 -
 docs/PLANAM_UX_POLISH_V2_REPORT.md                 |   147 -
 docs/PLANAM_UX_UI_2026_MASTER_SPEC.md              |  1202 --
 docs/PLANAM_V1_AI_JOURNEY.md                       |   163 -
 docs/PLANAM_V1_CANONICAL_PRODUCTS.md               |   154 -
 docs/PLANAM_V1_CLEAN_FOUNDATION_REPORT.md          |   260 -
 docs/PLANAM_V1_DOCUMENTATION_FREEZE_REPORT.md      |   162 -
 docs/PLANAM_V1_FAMILY_MODEL.md                     |   226 -
 docs/PLANAM_V1_FINAL_VISION.md                     |   459 -
 docs/PLANAM_V1_GROWTH_MODEL.md                     |   142 -
 docs/PLANAM_V1_HOME_STATES.md                      |   247 -
 docs/PLANAM_V1_IMAGE_STRATEGY.md                   |   171 -
 docs/PLANAM_V1_INGREDIENT_QUALITY_AUDIT.md         |    90 -
 ...M_V1_INGREDIENT_SAFE_COMMIT_AND_JSONB_RESYNC.md |   146 -
 docs/PLANAM_V1_LIFE_SCENARIOS.md                   |   174 -
 docs/PLANAM_V1_MENU_NUTRITION_AGGREGATION.md       |   150 -
 docs/PLANAM_V1_NUTRITION_SHOPPING_PHOTO.md         |   106 -
 docs/PLANAM_V1_PRODUCT_BACKLOG.md                  |   223 -
 docs/PLANAM_V1_PRODUCT_MASTER.md                   |   257 -
 docs/PLANAM_V1_RECIPE_FOUNDATION_REPORT.md         |   142 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_BUDGET.md           |    88 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_PILOT.md            |    92 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_PROMPTS.md          |   115 -
 docs/PLANAM_V1_RECIPE_IMAGE_PILOT_BUDGET_REPORT.md |    75 -
 docs/PLANAM_V1_RECIPE_IMAGE_PILOT_REPORT.md        |   137 -
 docs/PLANAM_V1_RECIPE_IMAGE_PLAN.md                |    90 -
 docs/PLANAM_V1_RECIPE_IMAGE_STYLE_SYSTEM.md        |   157 -
 docs/PLANAM_V1_RECIPE_IMAGE_TOKEN_SETUP.md         |    88 -
 docs/PLANAM_V1_RECIPE_IMPORT_PIPELINE.md           |   116 -
 docs/PLANAM_V1_RECIPE_NUTRITION_SUMMARY.md         |   127 -
 docs/PLANAM_V1_RECIPE_QUALITY_REPORT.md            |    88 -
 docs/PLANAM_V1_RELEASE_BLUEPRINT.md                |   588 -
 docs/PLANAM_V1_RELEASE_SCREENS.md                  |   167 -
 docs/PLANAM_V1_SHOPPING_MODEL_UPDATE.md            |   177 -
 docs/PLANAM_V1_SPRINT1_5_REPORT.md                 |   178 -
 docs/PLANAM_V1_SPRINT1_DESIGN_REVIEW.md            |   135 -
 docs/PLANAM_V1_SPRINT1_DESIGN_SPEC.md              |   466 -
 docs/PLANAM_V1_SPRINT1_IMPLEMENTATION_REPORT.md    |   148 -
 docs/PLANAM_V1_TO_TASTE_AND_READINESS.md           |   117 -
 docs/PLANAM_V1_TO_V2_STRATEGY.md                   |   143 -
 docs/PLANAM_VISUAL_MOCKUPS_2026.md                 |   564 -
 ...PLANAM_VISUAL_PACKAGE_2026_EXECUTIVE_SUMMARY.md |   199 -
 docs/PRODUCTION_DEPLOY.md                          |   280 -
 docs/RECIPE_ENGINE_API.md                          |   214 -
 docs/RECIPE_ENGINE_ENV.md                          |    35 -
 docs/RECIPE_ENGINE_V1.md                           |  1004 --
 docs/RECIPE_IMPORT_PIPELINE.md                     |   157 -
 docs/SCREEN_MAP.md                                 |   982 +-
 docs/SECURITY_AUDIT.md                             |   417 -
 docs/SECURITY_FIX_ROADMAP.md                       |   135 -
 docs/SPRINT_0_6_AUDIT.md                           |   378 -
 docs/SPRINT_0_COMPLETION_REPORT.md                 |   300 -
 docs/SPRINT_1_COMPLETION_REPORT.md                 |   194 -
 docs/SPRINT_2_COMPLETION_REPORT.md                 |   221 -
 docs/SPRINT_3_COMPLETION_REPORT.md                 |   185 -
 docs/SPRINT_4_COMPLETION_REPORT.md                 |   190 -
 docs/SPRINT_5_COMPLETION_REPORT.md                 |   241 -
 docs/SPRINT_6_COMPLETION_REPORT.md                 |   187 -
 docs/SPRINT_7_COMPLETION_REPORT.md                 |   216 -
 docs/SPRINT_8_COMPLETION_REPORT.md                 |   190 -
 docs/SPRINT_9_COMPLETION_REPORT.md                 |   167 -
 docs/UI_SYSTEM_AUDIT.md                            |   602 -
 docs/USER_RESET.md                                 |   320 -
 docs/UX_FLOW_MAP.md                                |   537 -
 docs/sql/shopping_categories_find_duplicates.sql   |    46 -
 nav-calls.txt                                      |     0
 pages.txt                                          |   Bin 10254 -> 0 bytes
 project-tree.txt                                   |   Bin 2035782 -> 0 bytes
 reports/dataset_analysis.md                        |   145 -
 reports/planam_cross_branch_audit.md               |    97 -
 reports/planam_project_consolidation_audit.md      |   262 -
 reports/planam_v1_hero_top50.json                  |   302 -
 reports/planam_v1_recipe_image_pilot_results.json  |    22 -
 reports/povarenok_analysis.md                      |   139 -
 reports/povarenok_conversion_report.md             |   141 -
 reports/profile_account_consolidation_audit.md     |   110 -
 reports/ui_2026_consolidation_audit.md             |   113 -
 sample_recipes.json                                |   589 -
 scripts/dedupe_shopping_categories.py              |   116 -
 scripts/reset_user.py                              |   534 -
 621 files changed, 5242 insertions(+), 100088 deletions(-)
```

### Unique commits in origin/main not in sprint-0/planam-2026-foundation

*(none — branch has no commits ahead of current)*

## Diff summary: sprint-0/planam-2026-foundation vs origin/ux-foundation-v1

```
.env.production.example                            |     9 -
 .gitignore                                         |    33 -
 MASTER.md                                          |    56 -
 PROJECT_CONTEXT.md                                 |     8 -
 TASKS.md                                           |     2 -
 apps/api/.env.example                              |     8 -
 apps/api/app/config.py                             |    22 -
 apps/api/app/database.py                           |     7 +-
 apps/api/app/database_migrations.py                |   333 +-
 apps/api/app/main.py                               |     2 -
 apps/api/app/models/pantry.py                      |     2 +-
 apps/api/app/models/recipe.py                      |    39 -
 apps/api/app/models/recipe_engine.py               |   202 -
 apps/api/app/routers/collections.py                |   212 -
 apps/api/app/routers/menus.py                      |   144 +-
 apps/api/app/routers/recipe_engine_common.py       |    11 -
 apps/api/app/routers/recipes.py                    |   383 +-
 apps/api/app/routers/telegram_bot.py               |    29 +-
 apps/api/app/schemas/menu.py                       |     3 -
 apps/api/app/schemas/menu_nutrition.py             |    75 -
 apps/api/app/schemas/menu_overview.py              |    65 -
 apps/api/app/schemas/pantry.py                     |     4 +-
 apps/api/app/schemas/recipe.py                     |    27 -
 apps/api/app/schemas/recipe_collection.py          |    62 -
 apps/api/app/schemas/recipe_engine_api.py          |   122 -
 apps/api/app/schemas/recipe_search.py              |    64 -
 apps/api/app/services/admin_auth.py                |     2 +-
 apps/api/app/services/bot_menu.py                  |     3 +-
 apps/api/app/services/categories_v1.py             |   122 -
 apps/api/app/services/family_member_nutrition.py   |     4 +-
 apps/api/app/services/home_next_action.py          |   132 -
 apps/api/app/services/ingredient_format.py         |   129 -
 apps/api/app/services/meal_attendance.py           |    27 -
 apps/api/app/services/menu.py                      |    26 -
 apps/api/app/services/menu_ai.py                   |    10 +-
 apps/api/app/services/menu_ai_legacy.py            |    70 +-
 apps/api/app/services/menu_ai_parsing.py           |   168 -
 apps/api/app/services/menu_overview.py             |    19 +-
 apps/api/app/services/menu_recipe_plan.py          |   438 -
 apps/api/app/services/normalization/__init__.py    |    47 -
 apps/api/app/services/normalization/amounts.py     |    43 -
 apps/api/app/services/normalization/categories.py  |    55 -
 apps/api/app/services/normalization/ingredients.py |    48 -
 apps/api/app/services/normalization/menu.py        |    23 -
 .../app/services/normalization/notifications.py    |    99 -
 apps/api/app/services/normalization/profile.py     |   121 -
 apps/api/app/services/normalization/shopping.py    |    23 -
 .../api/app/services/normalization/subscription.py |    72 -
 apps/api/app/services/notifications.py             |    24 +-
 apps/api/app/services/nutrition/__init__.py        |     1 -
 apps/api/app/services/nutrition/plan_aggregator.py |   395 -
 apps/api/app/services/nutrition_profile.py         |     3 -
 apps/api/app/services/pantry.py                    |     2 +-
 apps/api/app/services/recipe_storage.py            |    44 +-
 apps/api/app/services/recipes.py                   |   479 +
 apps/api/app/services/recipes/__init__.py          |   107 -
 apps/api/app/services/recipes/access.py            |    59 -
 apps/api/app/services/recipes/authoring.py         |   173 -
 apps/api/app/services/recipes/catalog.py           |   290 -
 apps/api/app/services/recipes/collections.py       |   364 -
 apps/api/app/services/recipes/cooking_history.py   |   180 -
 apps/api/app/services/recipes/explainability.py    |   245 -
 .../api/app/services/recipes/family_preferences.py |   183 -
 apps/api/app/services/recipes/mapper.py            |   134 -
 apps/api/app/services/recipes/recommendations.py   |    62 -
 .../app/services/recipes/repositories/__init__.py  |    17 -
 .../services/recipes/repositories/collections.py   |   100 -
 .../services/recipes/repositories/explanations.py  |    57 -
 .../app/services/recipes/repositories/history.py   |    90 -
 .../services/recipes/repositories/preferences.py   |    60 -
 .../app/services/recipes/repositories/scenarios.py |    60 -
 apps/api/app/services/recipes/repository.py        |   136 -
 apps/api/app/services/recipes/scenarios.py         |   203 -
 apps/api/app/services/recipes/search.py            |    99 -
 apps/api/app/services/recipes/title_normalize.py   |    55 -
 apps/api/app/services/recipes/types.py             |    69 -
 apps/api/app/services/shopping_categories.py       |   239 +-
 .../app/services/shopping_category_migration.py    |   274 -
 apps/api/app/services/shopping_category_service.py |   115 +-
 apps/api/app/services/shopping_item_utils.py       |   202 +-
 apps/api/app/services/shopping_list.py             |    31 +-
 apps/api/app/services/subscription.py              |     4 +-
 apps/api/app/services/subscription_catalog.py      |     8 +-
 apps/api/requirements.txt                          |     1 -
 apps/api/tests/test_categories_v1.py               |    45 -
 apps/api/tests/test_home_next_action.py            |    72 -
 apps/api/tests/test_ingredient_display_amounts.py  |   116 -
 apps/api/tests/test_ingredient_normalization.py    |   230 -
 apps/api/tests/test_menu_ai_parsing.py             |    97 -
 apps/api/tests/test_menu_nutrition_aggregation.py  |   183 -
 apps/api/tests/test_menu_recipe_plan.py            |   225 -
 apps/api/tests/test_menu_replace.py                |   176 -
 apps/api/tests/test_normalization_amounts.py       |    57 -
 apps/api/tests/test_normalization_categories.py    |    46 -
 .../tests/test_normalization_menu_ingredients.py   |    58 -
 .../test_notification_settings_normalization.py    |    59 -
 apps/api/tests/test_nutrition_pipeline.py          |   193 -
 apps/api/tests/test_profile_normalization.py       |    67 -
 apps/api/tests/test_project_health_audit.py        |    96 -
 apps/api/tests/test_recipe_image_resolver.py       |   116 -
 apps/api/tests/test_recipe_ingredient_audit.py     |   100 -
 apps/api/tests/test_recipe_nutrition_summary.py    |   228 -
 apps/api/tests/test_recipe_write_access.py         |   102 -
 apps/api/tests/test_recipes_catalog.py             |   203 -
 apps/api/tests/test_repair_image_files.py          |    59 -
 apps/api/tests/test_shopping_category_migration.py |   200 -
 apps/api/tests/test_shopping_category_service.py   |   171 -
 apps/api/tests/test_shopping_infer_category.py     |    70 -
 apps/api/tests/test_shopping_list_cleanup.py       |   177 -
 apps/api/tests/test_subscription_normalization.py  |    47 -
 apps/api/tests/test_telegram_webhook_security.py   |    57 -
 apps/api/tests/test_to_taste_migration.py          |   204 -
 apps/web/.env.example                              |     7 -
 apps/web/Dockerfile.prod                           |     2 -
 apps/web/app/account/ams/page.tsx                  |     8 -
 apps/web/app/account/family/page.tsx               |     8 -
 apps/web/app/account/notifications/page.tsx        |     8 -
 apps/web/app/account/nutrition/page.tsx            |    21 -
 apps/web/app/account/page.tsx                      |     8 -
 apps/web/app/account/settings/about/page.tsx       |     1 -
 apps/web/app/account/settings/account/page.tsx     |     1 -
 apps/web/app/account/settings/delete-data/page.tsx |     1 -
 apps/web/app/account/settings/documents/page.tsx   |     1 -
 apps/web/app/account/settings/page.tsx             |    39 -
 apps/web/app/account/settings/support/page.tsx     |     1 -
 .../web/app/account/subscription/checkout/page.tsx |    14 -
 apps/web/app/account/subscription/page.tsx         |    14 -
 apps/web/app/dev/planam-2026/page.tsx              |   150 -
 apps/web/app/family/page.tsx                       |     2 -
 apps/web/app/globals.css                           |   150 -
 apps/web/app/health/care/page.tsx                  |     7 -
 apps/web/app/health/chat/HealthChatPageClient.tsx  |    98 -
 apps/web/app/health/chat/page.tsx                  |    11 -
 apps/web/app/health/page.tsx                       |    11 -
 apps/web/app/health/today/page.tsx                 |    11 -
 apps/web/app/home/page.tsx                         |     9 -
 apps/web/app/home/pantry/page.tsx                  |     8 -
 apps/web/app/home/shopping/page.tsx                |    13 -
 apps/web/app/layout.tsx                            |    12 +-
 apps/web/app/menu/collections/[id]/page.tsx        |     6 -
 apps/web/app/menu/collections/page.tsx             |    11 -
 apps/web/app/menu/current/page.tsx                 |     7 -
 apps/web/app/menu/event/page.tsx                   |    38 +-
 apps/web/app/menu/favorites/page.tsx               |    11 -
 apps/web/app/menu/generate/page.tsx                |     7 -
 apps/web/app/menu/leftovers/page.tsx               |     7 +-
 apps/web/app/menu/page.tsx                         |     7 -
 apps/web/app/menu/recipes/page.tsx                 |    25 -
 apps/web/app/menu/scenarios/page.tsx               |     8 -
 apps/web/app/notifications/page.tsx                |    48 +-
 apps/web/app/nutritionist/care/page.tsx            |     3 +-
 apps/web/app/nutritionist/chat/page.tsx            |    99 +-
 apps/web/app/nutritionist/page.tsx                 |     8 +-
 apps/web/app/onboarding/page.tsx                   |     7 -
 apps/web/app/page.tsx                              |    12 -
 apps/web/app/pantry/page.tsx                       |     7 +-
 apps/web/app/plan/generate/page.tsx                |     8 -
 apps/web/app/plan/page.tsx                         |     8 -
 apps/web/app/plan/recipes/[id]/page.tsx            |    17 -
 apps/web/app/plan/recipes/page.tsx                 |     8 -
 apps/web/app/plan/today/page.tsx                   |    14 -
 apps/web/app/profile/nutrition/page.tsx            |     2 -
 apps/web/app/profile/page.tsx                      |     2 -
 apps/web/app/progress/page.tsx                     |     5 -
 apps/web/app/recipes/[id]/RecipeDetailLegacy.tsx   |    85 -
 apps/web/app/recipes/[id]/page.tsx                 |    86 +-
 apps/web/app/recipes/page.tsx                      |     7 +-
 apps/web/app/settings/page.tsx                     |     2 -
 apps/web/app/shopping/leftovers/page.tsx           |    11 -
 apps/web/app/shopping/page.tsx                     |    13 +-
 apps/web/app/shopping/pantry/page.tsx              |    12 -
 apps/web/app/subscription/page.tsx                 |     7 -
 apps/web/app/wellness/chat/page.tsx                |     8 -
 apps/web/app/wellness/page.tsx                     |     8 -
 apps/web/components/AppProviders.tsx               |    28 +-
 apps/web/components/TelegramProvider.tsx           |     4 +-
 apps/web/components/app-mode/ModeSwitcher.tsx      |    22 +-
 apps/web/components/auth/AppGate.tsx               |    31 +-
 apps/web/components/care/CareSettingsPanel.tsx     |    82 +-
 apps/web/components/care/CareTelegramLinkCard.tsx  |     8 +-
 apps/web/components/dom-2026/Leftovers2026.tsx     |   254 -
 .../web/components/dom-2026/LeftoversSheet2026.tsx |   228 -
 .../components/dom-2026/MealOutcomeSheet2026.tsx   |   235 -
 apps/web/components/dom-2026/Pantry2026.tsx        |   243 -
 apps/web/components/dom-2026/Shopping2026.tsx      |   390 -
 apps/web/components/dom-2026/index.ts              |     5 -
 apps/web/components/family/AddPersonSheet.tsx      |    22 +-
 apps/web/components/family/FamilyDashboard.tsx     |   110 +-
 apps/web/components/family/FamilyManageSheet.tsx   |    35 +-
 apps/web/components/family/InviteSheet.tsx         |    33 +-
 apps/web/components/family/MemberCard.tsx          |    38 +-
 apps/web/components/family/MemberForm.tsx          |    25 +-
 apps/web/components/family/RoleBadge.tsx           |     8 +-
 .../family/VirtualMemberNutritionForm.tsx          |    68 +-
 apps/web/components/home-2026/Home2026.tsx         |   193 -
 .../components/home-2026/MealFallbackPlate2026.tsx |    42 -
 apps/web/components/home-2026/PlanAmHero2026.tsx   |   138 -
 .../components/home-2026/PlanAmStatusRows2026.tsx  |    83 -
 apps/web/components/home-2026/index.ts             |     2 -
 apps/web/components/home/PlanAmHome.tsx            |   434 +-
 apps/web/components/layout/AppShell.tsx            |     5 +-
 apps/web/components/layout/AppShellBridge.tsx      |    46 -
 apps/web/components/layout/BottomBackButton.tsx    |    37 +
 apps/web/components/layout/BottomNav.tsx           |     1 +
 apps/web/components/layout/BottomNavigation.tsx    |    40 +-
 apps/web/components/layout/ScreenBackNav.tsx       |     4 +-
 apps/web/components/layout/ScreenLayout.tsx        |     8 +-
 apps/web/components/layout/SectionHub.tsx          |    68 -
 apps/web/components/layout/SegmentedTabs.tsx       |    53 -
 apps/web/components/layout/StickyBottomBar.tsx     |     2 +-
 apps/web/components/layout/TopBackLink.tsx         |     3 +
 apps/web/components/menu/MealCheckinPanel.tsx      |    24 +-
 apps/web/components/menu/MealLeftoversPage.tsx     |    46 +-
 apps/web/components/menu/MenuChooseVariants.tsx    |    19 +-
 apps/web/components/menu/MenuCurrentView.tsx       |   179 +-
 apps/web/components/menu/MenuDayOverview.tsx       |   247 -
 apps/web/components/menu/MenuDayPicker.tsx         |     6 +-
 apps/web/components/menu/MenuHub.tsx               |   346 +-
 apps/web/components/menu/MenuPlanner.tsx           |   110 +-
 apps/web/components/menu/MenuPlannerSection.tsx    |     4 +-
 apps/web/components/menu/MenuQuickActionsSheet.tsx |    52 -
 apps/web/components/menu/MenuSectionLayout.tsx     |    29 -
 apps/web/components/menu/MenuSettingsPage.tsx      |    27 +-
 apps/web/components/menu/MenuSubTabs.tsx           |    19 -
 apps/web/components/menu/MenuVariantCard.tsx       |    44 +-
 apps/web/components/menu/ReplaceDishModal.tsx      |    28 +-
 .../components/monetization-2026/AmsHub2026.tsx    |   128 -
 .../HomeMonetizationBanner2026.tsx                 |    45 -
 .../monetization-2026/PaymentStub2026.tsx          |   111 -
 .../monetization-2026/PaywallProvider.tsx          |    61 -
 .../monetization-2026/PaywallSheet2026.tsx         |    94 -
 .../components/monetization-2026/PlanCard2026.tsx  |    79 -
 .../monetization-2026/SubscriptionHub2026.tsx      |   206 -
 .../monetization-2026/SubscriptionOffline2026.tsx  |    83 -
 .../monetization-2026/TrialStatus2026.tsx          |    33 -
 apps/web/components/monetization-2026/index.ts     |     5 -
 .../notifications/NotificationSettingsForm.tsx     |    44 +-
 .../components/notifications/NotificationsView.tsx |    83 -
 .../components/nutrition-profile/NumberInput.tsx   |     6 +-
 .../NutritionGoalDetailsFields.tsx                 |    20 +-
 .../nutrition-profile/NutritionProfileForm.tsx     |   104 +-
 .../nutrition-profile/NutritionSection.tsx         |    14 +-
 .../web/components/nutrition-profile/ToggleRow.tsx |     8 +-
 .../components/nutritionist/HealthTodayView.tsx    |   382 -
 .../nutritionist/NutritionistAdviceCard.tsx        |    20 +-
 .../components/nutritionist/NutritionistChat.tsx   |    24 +-
 .../nutritionist/NutritionistDashboard.tsx         |   572 +-
 .../components/nutritionist/WaterIntakePanel.tsx   |    14 +-
 .../onboarding-2026/Onboarding2026Flow.tsx         |   309 -
 .../onboarding-2026/Onboarding2026Redirect.tsx     |    36 -
 .../onboarding-2026/OnboardingChipGrid2026.tsx     |    91 -
 .../onboarding-2026/OnboardingGenerateStep2026.tsx |    79 -
 .../onboarding-2026/OnboardingProgress2026.tsx     |    26 -
 .../onboarding-2026/OnboardingWowReveal2026.tsx    |    63 -
 .../onboarding-2026/TrialWelcomeCard2026.tsx       |    31 -
 apps/web/components/onboarding-2026/index.ts       |     2 -
 .../components/onboarding/ChipSelectWithCustom.tsx |    99 +
 .../components/onboarding/OnboardingComplete.tsx   |    94 +
 .../web/components/onboarding/OnboardingWizard.tsx |   222 +
 apps/web/components/onboarding/ProgressBar.tsx     |    25 +
 apps/web/components/onboarding/StepContent.tsx     |   111 +
 apps/web/components/onboarding/StepNavigation.tsx  |    50 +
 .../components/pantry/PantryCategorySection.tsx    |     8 +-
 apps/web/components/pantry/PantryDashboard.tsx     |    71 +-
 apps/web/components/pantry/PantryItemCard.tsx      |    22 +-
 apps/web/components/pantry/PantryItemForm.tsx      |    29 +-
 apps/web/components/pantry/PantryItemRow.tsx       |    16 +-
 .../components/plan-2026/DayNutritionCard2026.tsx  |   126 -
 apps/web/components/plan-2026/PlanGenerate2026.tsx |   288 -
 apps/web/components/plan-2026/PlanMealCard2026.tsx |   138 -
 .../plan-2026/PlanTimelineSection2026.tsx          |    46 -
 apps/web/components/plan-2026/PlanToday2026.tsx    |   316 -
 apps/web/components/plan-2026/PlanWeek2026.tsx     |   131 -
 .../components/plan-2026/ReplaceDishSheet2026.tsx  |   188 -
 apps/web/components/plan-2026/index.ts             |     5 -
 .../planam-2026/account/AccountHub2026.tsx         |   110 -
 .../planam-2026/cards/ActionCard2026.tsx           |    80 -
 .../components/planam-2026/cards/HeroCard2026.tsx  |   103 -
 .../planam-2026/cards/InsightCard2026.tsx          |    47 -
 .../planam-2026/cards/MetricCard2026.tsx           |    44 -
 apps/web/components/planam-2026/index.ts           |    15 -
 .../components/planam-2026/layout/AppShell2026.tsx |    26 -
 .../planam-2026/layout/ShellHeader2026.tsx         |    40 -
 .../navigation/BottomNavigation2026.tsx            |    85 -
 .../planam-2026/navigation/NavIcon2026.tsx         |   170 -
 .../planam-2026/navigation/ScreenBack2026.tsx      |    42 -
 .../planam-2026/navigation/SectionSubTabs2026.tsx  |    54 -
 .../navigation/TelegramBackBridge2026.tsx          |    12 -
 .../navigation/useTelegramBackButton2026.ts        |    64 -
 .../planam-2026/screens/RoutePlaceholder2026.tsx   |    25 -
 .../components/planam-2026/theme/ThemeProvider.tsx |   134 -
 .../planam-2026/theme/ThemeToggle2026.tsx          |    50 -
 .../components/planam-2026/ui/BottomSheet2026.tsx  |    62 -
 apps/web/components/planam-2026/ui/Button2026.tsx  |    58 -
 apps/web/components/planam-2026/ui/Card2026.tsx    |    34 -
 .../components/planam-2026/ui/EmptyState2026.tsx   |    46 -
 .../web/components/planam-2026/ui/Skeleton2026.tsx |    30 -
 apps/web/components/profile/ProfileDashboard.tsx   |    44 +-
 apps/web/components/profile/ProfileModeControl.tsx |    18 +-
 apps/web/components/progress/ProgressDashboard.tsx |   116 +-
 apps/web/components/progress/ProgressProLocked.tsx |    25 +-
 .../components/recipes-2026/MenuSlotSheet2026.tsx  |   195 -
 .../components/recipes-2026/RecipeCatalog2026.tsx  |   366 -
 .../components/recipes-2026/RecipeDetail2026.tsx   |   439 -
 .../components/recipes-2026/RecipeGridCard2026.tsx |   112 -
 .../components/recipes-2026/RecipeImage2026.tsx    |    61 -
 apps/web/components/recipes-2026/index.ts          |     4 -
 .../components/recipes/CollectionDetailView.tsx    |   162 -
 apps/web/components/recipes/CollectionsView.tsx    |   169 -
 apps/web/components/recipes/FavoritesView.tsx      |   132 -
 apps/web/components/recipes/FilterChip.tsx         |    25 -
 apps/web/components/recipes/FromPantrySection.tsx  |   158 -
 apps/web/components/recipes/RecipeCard.tsx         |    38 +-
 apps/web/components/recipes/RecipeCatalog.tsx      |   378 +
 .../components/recipes/RecipeCatalogSections.tsx   |    62 +-
 apps/web/components/recipes/RecipeDetailModal.tsx  |   519 +-
 .../components/recipes/RecipeDetailMorePanel.tsx   |   352 -
 apps/web/components/recipes/RecipeFiltersSheet.tsx |   186 -
 apps/web/components/recipes/RecipeListSkeleton.tsx |    23 -
 apps/web/components/recipes/RecipeResultsList.tsx  |    33 -
 apps/web/components/recipes/RecipesView.tsx        |   365 -
 apps/web/components/recipes/ScenarioChips.tsx      |    84 -
 apps/web/components/settings/SettingsScaffold.tsx  |    49 +-
 apps/web/components/shopping/CategoryPicker.tsx    |    30 +-
 .../shopping/ShoppingCategorySection.tsx           |    10 +-
 .../components/shopping/ShoppingCategorySheet.tsx  |    15 +-
 apps/web/components/shopping/ShoppingItemRow.tsx   |    18 +-
 apps/web/components/shopping/ShoppingItemSheet.tsx |    25 +-
 apps/web/components/shopping/ShoppingListView.tsx  |    79 +-
 .../components/shopping/ShoppingSectionLayout.tsx  |    54 -
 apps/web/components/shopping/ShoppingSubTabs.tsx   |    18 -
 .../components/subscription/AmaConfirmDialog.tsx   |    60 +-
 .../subscription/SubscriptionDashboard.tsx         |    82 +-
 apps/web/components/ui/HubTile.tsx                 |   101 -
 apps/web/components/ui/Sheet.tsx                   |    10 +-
 apps/web/components/ui/Skeleton.tsx                |     4 +-
 apps/web/components/ui/ToastProvider.tsx           |    11 +-
 .../components/wellness-2026/WaterIntake2026.tsx   |   121 -
 .../components/wellness-2026/WellnessChat2026.tsx  |   100 -
 .../components/wellness-2026/WellnessChip2026.tsx  |    76 -
 .../wellness-2026/WellnessDayRing2026.tsx          |    39 -
 .../wellness-2026/WellnessGoalCard2026.tsx         |    62 -
 .../components/wellness-2026/WellnessHome2026.tsx  |   274 -
 .../wellness-2026/WellnessInsight2026.tsx          |    34 -
 .../wellness-2026/WellnessTodayCard2026.tsx        |    28 -
 .../wellness-2026/WellnessWeekStrip2026.tsx        |    42 -
 apps/web/components/wellness-2026/index.ts         |     3 -
 apps/web/lib/api-client.ts                         |    25 +-
 apps/web/lib/dom/pantry-sections.ts                |    44 -
 apps/web/lib/dom/shopping-groups.ts                |    49 -
 apps/web/lib/home/home-2026-data.ts                |   181 -
 apps/web/lib/home/planam-hero-2026.test.ts         |   153 -
 apps/web/lib/home/planam-hero-2026.ts              |   233 -
 apps/web/lib/home/redirect-path-2026.ts            |    42 -
 apps/web/lib/home/use-compact-viewport.ts          |    21 -
 apps/web/lib/meal-checkins/api.ts                  |     4 +-
 apps/web/lib/menu/api.ts                           |   167 +-
 apps/web/lib/menu/labels.ts                        |     6 +-
 apps/web/lib/menu/menu-days.ts                     |    33 -
 apps/web/lib/menu/overview-types.ts                |    32 +-
 apps/web/lib/menu/planner-options.ts               |     4 +-
 apps/web/lib/menu/quick-actions.ts                 |    52 -
 apps/web/lib/menu/replace-slot.ts                  |    52 -
 apps/web/lib/menu/types.ts                         |     2 -
 apps/web/lib/monetization/billing-status.ts        |   162 -
 apps/web/lib/monetization/paths.ts                 |    10 -
 apps/web/lib/monetization/paywall.ts               |    82 -
 apps/web/lib/monetization/plan-catalog-2026.ts     |   127 -
 apps/web/lib/monetization/trial-config.ts          |    11 -
 apps/web/lib/navigation/back-navigation-2026.ts    |    74 -
 apps/web/lib/navigation/nav-config-2026.ts         |   356 -
 apps/web/lib/navigation/nav-config.ts              |   124 -
 apps/web/lib/navigation/return-to.ts               |    66 +-
 apps/web/lib/navigation/route-migration-2026.ts    |    61 -
 apps/web/lib/onboarding-2026/config.ts             |   151 -
 apps/web/lib/pantry/api.ts                         |     2 +-
 apps/web/lib/pantry/types.ts                       |     2 +-
 apps/web/lib/plan/add-to-shopping.ts               |    21 -
 apps/web/lib/plan/plan-paths.ts                    |    46 -
 apps/web/lib/plan/plan-today.ts                    |   162 -
 apps/web/lib/planam/cn.ts                          |     6 -
 apps/web/lib/planam/embedded-2026.ts               |    15 -
 apps/web/lib/planam/feature-flags.ts               |    21 -
 apps/web/lib/planam/layout-constants-2026.ts       |     3 -
 apps/web/lib/planam/onboarding-gate.ts             |    34 -
 apps/web/lib/planam/planam-2026-page.ts            |    19 -
 apps/web/lib/planam/routes.ts                      |    91 -
 apps/web/lib/planam/theme-document.ts              |    81 -
 apps/web/lib/planam/theme.ts                       |    52 -
 apps/web/lib/planam/ui-scope.ts                    |    21 -
 apps/web/lib/progress/api.ts                       |     8 -
 apps/web/lib/recipes/analysis-api.ts               |    26 +-
 apps/web/lib/recipes/api.ts                        |   143 -
 apps/web/lib/recipes/catalog-sections.ts           |    11 -
 apps/web/lib/recipes/ingredient-amount.ts          |    36 -
 apps/web/lib/recipes/menu-from-recipe.ts           |    61 -
 apps/web/lib/recipes/nutrition.ts                  |    90 -
 apps/web/lib/recipes/recipe-media.ts               |   102 -
 apps/web/lib/recipes/types.ts                      |   158 -
 apps/web/lib/shopping/categories-v1.ts             |    92 -
 apps/web/lib/shopping/category-suggest.test.ts     |    38 -
 apps/web/lib/shopping/category-suggest.ts          |    71 +-
 apps/web/lib/shopping/labels.ts                    |    31 +-
 apps/web/lib/shopping/types.ts                     |     4 +-
 apps/web/lib/wellness/goal-labels.ts               |    27 -
 apps/web/lib/wellness/home-wellness.ts             |    67 -
 apps/web/lib/wellness/week-strip.ts                |    57 -
 apps/web/lib/wellness/wellness-insight.ts          |    88 -
 apps/web/lib/wellness/wellness-status.ts           |   155 -
 apps/web/middleware.ts                             |    61 -
 apps/web/public/brand/planam-icon.svg              |     5 -
 apps/web/public/brand/planam-mark.svg              |     4 -
 apps/web/public/recipe-images/.gitkeep             |     0
 apps/web/tailwind.config.ts                        |    89 +-
 apps/web/tsconfig.tsbuildinfo                      |     1 -
 backend/data/nutrition_reference_seed.json         |  1105 --
 backend/pytest.ini                                 |     3 -
 backend/scripts/_image_paths.py                    |    85 -
 backend/scripts/analyze_povarenok_dataset.py       |   466 -
 backend/scripts/analyze_recipe_dataset.py          |   340 -
 .../scripts/apply_calculated_nutrition_updates.py  |   466 -
 backend/scripts/apply_nutrition_backfill.py        |   489 -
 backend/scripts/apply_recipe_images.py             |   232 -
 backend/scripts/apply_recipe_steps_updates.py      |   375 -
 backend/scripts/archive_placeholder_recipes.py     |    92 -
 .../scripts/audit_beverage_nutrition_strategy.py   |   395 -
 backend/scripts/audit_menu_nutrition_readiness.py  |   220 -
 backend/scripts/audit_nutrition_update_deltas.py   |   506 -
 backend/scripts/audit_povarenok_jsonl.py           |   365 -
 backend/scripts/audit_project_health.py            |   513 -
 backend/scripts/audit_recipe_catalog.py            |   331 -
 backend/scripts/audit_recipe_duplicates.py         |   230 -
 backend/scripts/audit_recipe_images.py             |   104 -
 .../audit_recipe_ingredient_display_amounts.py     |   209 -
 backend/scripts/audit_recipe_ingredients.py        |   503 -
 backend/scripts/audit_recipe_steps_after_update.py |   141 -
 backend/scripts/audit_recipe_steps_quality.py      |   341 -
 backend/scripts/audit_recipe_steps_v2.py           |   231 -
 backend/scripts/audit_remaining_nutrition_gaps.py  |   470 -
 backend/scripts/audit_weak_steps_remediation.py    |   340 -
 backend/scripts/build_enrichment_batch.py          |   200 -
 backend/scripts/build_holiday_kids_steps_batch.py  |   263 -
 backend/scripts/build_holiday_kids_steps_update.py |   312 -
 backend/scripts/build_planam_v1_catalog.py         |   361 -
 backend/scripts/build_recipe_image_prompts.py      |   118 -
 backend/scripts/build_remaining_weak_groups.py     |   356 -
 backend/scripts/build_simple_beverage_updates.py   |   354 -
 .../scripts/build_steps_update_from_enrichment.py  |   299 -
 .../scripts/build_verified_nutrition_updates.py    |   281 -
 backend/scripts/calculate_nutrition.py             |   275 -
 .../scripts/calculate_recipe_nutrition_preview.py  |   530 -
 .../scripts/calculate_recipe_nutrition_summary.py  |   436 -
 backend/scripts/canonical_products.py              |   426 -
 backend/scripts/convert_enriched_to_import_json.py |   330 -
 .../convert_nutrition_backfill_to_update_json.py   |   231 -
 backend/scripts/convert_povarenok.py               |   425 -
 backend/scripts/evaluate_photo_prompt_readiness.py |   151 -
 .../scripts/export_calculated_nutrition_updates.py |   356 -
 backend/scripts/generate_shopping_list_groups.py   |   174 -
 backend/scripts/import_recipes.py                  |   549 -
 backend/scripts/migrate_to_taste_ingredients.py    |   452 -
 backend/scripts/normalize_ingredient_amounts.py    |   689 -
 backend/scripts/normalize_recipe_ingredients.py    |   573 -
 backend/scripts/nutrition_data.py                  |   353 -
 .../scripts/nutrition_shopping_photo_pipeline.py   |   236 -
 backend/scripts/openai_recipe_image_client.py      |   219 -
 backend/scripts/plan_nutrition_backfill.py         |   357 -
 backend/scripts/plan_recipe_dedup.py               |   215 -
 .../scripts/prepare_povarenok_enrichment_input.py  |   256 -
 backend/scripts/process_recipe_images.py           |   143 -
 backend/scripts/recipe_id_resolver.py              |    60 -
 backend/scripts/recipe_image_utils.py              |   252 -
 backend/scripts/recipe_nutrition_calculator.py     |   211 -
 backend/scripts/repair_recipe_image_assignments.py |   219 -
 backend/scripts/report_recipe_readiness.py         |   221 -
 backend/scripts/resync_recipe_ingredients_jsonb.py |   269 -
 backend/scripts/run_enrichment_pilot.py            |   444 -
 backend/scripts/run_nutrition_backfill.py          |   437 -
 backend/scripts/run_recipe_image_pilot.py          |   295 -
 backend/scripts/run_steps_enrichment.py            |   965 --
 backend/scripts/select_povarenok_candidates.py     |   370 -
 backup_before_import_10.sql                        |   Bin 512178 -> 0 bytes
 backup_before_import_100.sql                       |   Bin 771986 -> 0 bytes
 data/planam_v1_canonical_products.json             |  1487 --
 data/planam_v1_image_pilot_batch.json              |   192 -
 data/planam_v1_nutrition_facts.json                |  1083 --
 data/planam_v1_recipes.json                        | 16189 -------------------
 deploy/nginx/nginx.conf                            |     5 -
 deploy/nginx/templates/app-init.conf.template      |    58 +-
 deploy/nginx/templates/app-ssl.conf.template       |    68 +-
 docker-compose.prod.yml                            |    16 -
 docker-compose.yml                                 |    10 -
 docs/ADMIN_PANEL_INCIDENT_AUDIT.md                 |   569 -
 docs/BETA_HARDENING_REPORT.md                      |   106 -
 docs/BETA_READINESS_AUDIT.md                       |   322 -
 docs/CODEBASE_INDEX.md                             |   930 --
 docs/DOMAIN_ARCHITECTURE.md                        |   697 -
 docs/NAVIGATION_GRAPH.md                           |   517 -
 docs/NAVIGATION_MAP.md                             |    66 -
 docs/PLANAM_2026_COLOR_FIX_REPORT.md               |    83 -
 docs/PLANAM_2026_DECISION_RECORD.md                |    79 -
 docs/PLANAM_2026_FINAL_UX_QA_REPORT.md             |   136 -
 docs/PLANAM_2026_IMPLEMENTATION_ROADMAP.md         |   712 -
 docs/PLANAM_2026_PRODUCT_BLUEPRINT.md              |   757 -
 docs/PLANAM_COLOR_SYSTEM_V1.md                     |    42 -
 docs/PLANAM_CONVERSION_FUNNEL_2026.md              |   316 -
 docs/PLANAM_CURRENT_STATE_ACTIONS.md               |   248 -
 docs/PLANAM_CURRENT_STATE_COMPONENTS.md            |   149 -
 docs/PLANAM_CURRENT_STATE_DATA.md                  |   250 -
 docs/PLANAM_CURRENT_STATE_LAYOUTS.md               |   179 -
 docs/PLANAM_CURRENT_STATE_MASTER.md                |   229 -
 docs/PLANAM_CURRENT_STATE_NAVIGATION.md            |   218 -
 docs/PLANAM_CURRENT_STATE_OVERLAYS.md              |    89 -
 docs/PLANAM_CURRENT_STATE_SCREENS.md               |   337 -
 docs/PLANAM_CURRENT_STATE_USER_FLOWS.md            |   310 -
 docs/PLANAM_DESIGN_SYSTEM_2026.md                  |   769 -
 docs/PLANAM_FINAL_PRODUCT_REVIEW.md                |   402 -
 ...AM_HOTFIX_SHOPPING_CATEGORY_MIGRATION_REPORT.md |   164 -
 docs/PLANAM_LEGACY_DECOMMISSION_AUDIT.md           |   686 -
 docs/PLANAM_LEGACY_REMOVAL_BACKLOG.md              |   115 -
 docs/PLANAM_NAVIGATION_LEGACY_AUDIT.md             |   327 -
 docs/PLANAM_NOTIFICATION_SYSTEM_2026.md            |   289 -
 docs/PLANAM_PAYMENT_ARCHITECTURE_2026.md           |   114 -
 docs/PLANAM_PRODUCTION_UX_POLISH_V1_REPORT.md      |   127 -
 docs/PLANAM_RECIPES_CATALOG_AUDIT_AND_FIX.md       |   111 -
 docs/PLANAM_RECIPE_CATALOG_QUALITY_V1_REPORT.md    |   125 -
 docs/PLANAM_RECIPE_DB_GO_REPORT.md                 |   159 -
 docs/PLANAM_RECIPE_MEDIA_ARCHITECTURE.md           |   265 -
 docs/PLANAM_RECIPE_MENU_INTEGRATION_V1_REPORT.md   |   103 -
 docs/PLANAM_RECIPE_REPLACE_FLOW_V1_REPORT.md       |   106 -
 docs/PLANAM_UX_POLISH_V2_REPORT.md                 |   147 -
 docs/PLANAM_UX_UI_2026_MASTER_SPEC.md              |  1202 --
 docs/PLANAM_V1_AI_JOURNEY.md                       |   163 -
 docs/PLANAM_V1_CANONICAL_PRODUCTS.md               |   154 -
 docs/PLANAM_V1_CLEAN_FOUNDATION_REPORT.md          |   260 -
 docs/PLANAM_V1_DOCUMENTATION_FREEZE_REPORT.md      |   162 -
 docs/PLANAM_V1_FAMILY_MODEL.md                     |   226 -
 docs/PLANAM_V1_FINAL_VISION.md                     |   459 -
 docs/PLANAM_V1_GROWTH_MODEL.md                     |   142 -
 docs/PLANAM_V1_HOME_STATES.md                      |   247 -
 docs/PLANAM_V1_IMAGE_STRATEGY.md                   |   171 -
 docs/PLANAM_V1_INGREDIENT_QUALITY_AUDIT.md         |    90 -
 ...M_V1_INGREDIENT_SAFE_COMMIT_AND_JSONB_RESYNC.md |   146 -
 docs/PLANAM_V1_LIFE_SCENARIOS.md                   |   174 -
 docs/PLANAM_V1_MENU_NUTRITION_AGGREGATION.md       |   150 -
 docs/PLANAM_V1_NUTRITION_SHOPPING_PHOTO.md         |   106 -
 docs/PLANAM_V1_PRODUCT_BACKLOG.md                  |   223 -
 docs/PLANAM_V1_PRODUCT_MASTER.md                   |   257 -
 docs/PLANAM_V1_RECIPE_FOUNDATION_REPORT.md         |   142 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_BUDGET.md           |    88 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_PILOT.md            |    92 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_PROMPTS.md          |   115 -
 docs/PLANAM_V1_RECIPE_IMAGE_PILOT_BUDGET_REPORT.md |    75 -
 docs/PLANAM_V1_RECIPE_IMAGE_PILOT_REPORT.md        |   137 -
 docs/PLANAM_V1_RECIPE_IMAGE_PLAN.md                |    90 -
 docs/PLANAM_V1_RECIPE_IMAGE_STYLE_SYSTEM.md        |   157 -
 docs/PLANAM_V1_RECIPE_IMAGE_TOKEN_SETUP.md         |    88 -
 docs/PLANAM_V1_RECIPE_IMPORT_PIPELINE.md           |   116 -
 docs/PLANAM_V1_RECIPE_NUTRITION_SUMMARY.md         |   127 -
 docs/PLANAM_V1_RECIPE_QUALITY_REPORT.md            |    88 -
 docs/PLANAM_V1_RELEASE_BLUEPRINT.md                |   588 -
 docs/PLANAM_V1_RELEASE_SCREENS.md                  |   167 -
 docs/PLANAM_V1_SHOPPING_MODEL_UPDATE.md            |   177 -
 docs/PLANAM_V1_SPRINT1_5_REPORT.md                 |   178 -
 docs/PLANAM_V1_SPRINT1_DESIGN_REVIEW.md            |   135 -
 docs/PLANAM_V1_SPRINT1_DESIGN_SPEC.md              |   466 -
 docs/PLANAM_V1_SPRINT1_IMPLEMENTATION_REPORT.md    |   148 -
 docs/PLANAM_V1_TO_TASTE_AND_READINESS.md           |   117 -
 docs/PLANAM_V1_TO_V2_STRATEGY.md                   |   143 -
 docs/PLANAM_VISUAL_MOCKUPS_2026.md                 |   564 -
 ...PLANAM_VISUAL_PACKAGE_2026_EXECUTIVE_SUMMARY.md |   199 -
 docs/PRODUCTION_DEPLOY.md                          |   280 -
 docs/RECIPE_ENGINE_API.md                          |   214 -
 docs/RECIPE_ENGINE_ENV.md                          |    35 -
 docs/RECIPE_ENGINE_V1.md                           |  1004 --
 docs/RECIPE_IMPORT_PIPELINE.md                     |   157 -
 docs/SCREEN_MAP.md                                 |   982 +-
 docs/SECURITY_AUDIT.md                             |   417 -
 docs/SECURITY_FIX_ROADMAP.md                       |   135 -
 docs/SPRINT_0_6_AUDIT.md                           |   378 -
 docs/SPRINT_0_COMPLETION_REPORT.md                 |   300 -
 docs/SPRINT_1_COMPLETION_REPORT.md                 |   194 -
 docs/SPRINT_2_COMPLETION_REPORT.md                 |   221 -
 docs/SPRINT_3_COMPLETION_REPORT.md                 |   185 -
 docs/SPRINT_4_COMPLETION_REPORT.md                 |   190 -
 docs/SPRINT_5_COMPLETION_REPORT.md                 |   241 -
 docs/SPRINT_6_COMPLETION_REPORT.md                 |   187 -
 docs/SPRINT_7_COMPLETION_REPORT.md                 |   216 -
 docs/SPRINT_8_COMPLETION_REPORT.md                 |   190 -
 docs/SPRINT_9_COMPLETION_REPORT.md                 |   167 -
 docs/UI_SYSTEM_AUDIT.md                            |   602 -
 docs/USER_RESET.md                                 |   320 -
 docs/UX_FLOW_MAP.md                                |   537 -
 docs/sql/shopping_categories_find_duplicates.sql   |    46 -
 nav-calls.txt                                      |     0
 pages.txt                                          |   Bin 10254 -> 0 bytes
 project-tree.txt                                   |   Bin 2035782 -> 0 bytes
 reports/dataset_analysis.md                        |   145 -
 reports/planam_cross_branch_audit.md               |    97 -
 reports/planam_project_consolidation_audit.md      |   262 -
 reports/planam_v1_hero_top50.json                  |   302 -
 reports/planam_v1_recipe_image_pilot_results.json  |    22 -
 reports/povarenok_analysis.md                      |   139 -
 reports/povarenok_conversion_report.md             |   141 -
 reports/profile_account_consolidation_audit.md     |   110 -
 reports/ui_2026_consolidation_audit.md             |   113 -
 sample_recipes.json                                |   589 -
 scripts/dedupe_shopping_categories.py              |   116 -
 scripts/reset_user.py                              |   534 -
 609 files changed, 5187 insertions(+), 98670 deletions(-)
```

### Unique commits in origin/ux-foundation-v1 not in sprint-0/planam-2026-foundation

*(none — branch has no commits ahead of current)*

## Diff summary: sprint-0/planam-2026-foundation vs origin/release-candidate-ux

```
.env.production.example                            |     9 -
 .gitignore                                         |    33 -
 MASTER.md                                          |    56 -
 PROJECT_CONTEXT.md                                 |     8 -
 TASKS.md                                           |     2 -
 apps/api/.env.example                              |     8 -
 apps/api/app/config.py                             |    22 -
 apps/api/app/database.py                           |     7 +-
 apps/api/app/database_migrations.py                |   333 +-
 apps/api/app/main.py                               |     2 -
 apps/api/app/models/pantry.py                      |     2 +-
 apps/api/app/models/recipe.py                      |    39 -
 apps/api/app/models/recipe_engine.py               |   202 -
 apps/api/app/routers/collections.py                |   212 -
 apps/api/app/routers/menus.py                      |   144 +-
 apps/api/app/routers/recipe_engine_common.py       |    11 -
 apps/api/app/routers/recipes.py                    |   383 +-
 apps/api/app/routers/telegram_bot.py               |    29 +-
 apps/api/app/schemas/menu.py                       |     3 -
 apps/api/app/schemas/menu_nutrition.py             |    75 -
 apps/api/app/schemas/menu_overview.py              |    65 -
 apps/api/app/schemas/pantry.py                     |     4 +-
 apps/api/app/schemas/recipe.py                     |    27 -
 apps/api/app/schemas/recipe_collection.py          |    62 -
 apps/api/app/schemas/recipe_engine_api.py          |   122 -
 apps/api/app/schemas/recipe_search.py              |    64 -
 apps/api/app/services/admin_auth.py                |     2 +-
 apps/api/app/services/bot_menu.py                  |     3 +-
 apps/api/app/services/categories_v1.py             |   122 -
 apps/api/app/services/family_member_nutrition.py   |     4 +-
 apps/api/app/services/home_next_action.py          |   132 -
 apps/api/app/services/ingredient_format.py         |   129 -
 apps/api/app/services/meal_attendance.py           |    27 -
 apps/api/app/services/menu.py                      |    26 -
 apps/api/app/services/menu_ai.py                   |    10 +-
 apps/api/app/services/menu_ai_legacy.py            |    70 +-
 apps/api/app/services/menu_ai_parsing.py           |   168 -
 apps/api/app/services/menu_overview.py             |    19 +-
 apps/api/app/services/menu_recipe_plan.py          |   438 -
 apps/api/app/services/normalization/__init__.py    |    47 -
 apps/api/app/services/normalization/amounts.py     |    43 -
 apps/api/app/services/normalization/categories.py  |    55 -
 apps/api/app/services/normalization/ingredients.py |    48 -
 apps/api/app/services/normalization/menu.py        |    23 -
 .../app/services/normalization/notifications.py    |    99 -
 apps/api/app/services/normalization/profile.py     |   121 -
 apps/api/app/services/normalization/shopping.py    |    23 -
 .../api/app/services/normalization/subscription.py |    72 -
 apps/api/app/services/notifications.py             |    24 +-
 apps/api/app/services/nutrition/__init__.py        |     1 -
 apps/api/app/services/nutrition/plan_aggregator.py |   395 -
 apps/api/app/services/nutrition_profile.py         |     3 -
 apps/api/app/services/pantry.py                    |     2 +-
 apps/api/app/services/recipe_storage.py            |    44 +-
 apps/api/app/services/recipes.py                   |   479 +
 apps/api/app/services/recipes/__init__.py          |   107 -
 apps/api/app/services/recipes/access.py            |    59 -
 apps/api/app/services/recipes/authoring.py         |   173 -
 apps/api/app/services/recipes/catalog.py           |   290 -
 apps/api/app/services/recipes/collections.py       |   364 -
 apps/api/app/services/recipes/cooking_history.py   |   180 -
 apps/api/app/services/recipes/explainability.py    |   245 -
 .../api/app/services/recipes/family_preferences.py |   183 -
 apps/api/app/services/recipes/mapper.py            |   134 -
 apps/api/app/services/recipes/recommendations.py   |    62 -
 .../app/services/recipes/repositories/__init__.py  |    17 -
 .../services/recipes/repositories/collections.py   |   100 -
 .../services/recipes/repositories/explanations.py  |    57 -
 .../app/services/recipes/repositories/history.py   |    90 -
 .../services/recipes/repositories/preferences.py   |    60 -
 .../app/services/recipes/repositories/scenarios.py |    60 -
 apps/api/app/services/recipes/repository.py        |   136 -
 apps/api/app/services/recipes/scenarios.py         |   203 -
 apps/api/app/services/recipes/search.py            |    99 -
 apps/api/app/services/recipes/title_normalize.py   |    55 -
 apps/api/app/services/recipes/types.py             |    69 -
 apps/api/app/services/shopping_categories.py       |   239 +-
 .../app/services/shopping_category_migration.py    |   274 -
 apps/api/app/services/shopping_category_service.py |   115 +-
 apps/api/app/services/shopping_item_utils.py       |   202 +-
 apps/api/app/services/shopping_list.py             |    31 +-
 apps/api/app/services/subscription.py              |     4 +-
 apps/api/app/services/subscription_catalog.py      |     8 +-
 apps/api/requirements.txt                          |     1 -
 apps/api/tests/test_categories_v1.py               |    45 -
 apps/api/tests/test_home_next_action.py            |    72 -
 apps/api/tests/test_ingredient_display_amounts.py  |   116 -
 apps/api/tests/test_ingredient_normalization.py    |   230 -
 apps/api/tests/test_menu_ai_parsing.py             |    97 -
 apps/api/tests/test_menu_nutrition_aggregation.py  |   183 -
 apps/api/tests/test_menu_recipe_plan.py            |   225 -
 apps/api/tests/test_menu_replace.py                |   176 -
 apps/api/tests/test_normalization_amounts.py       |    57 -
 apps/api/tests/test_normalization_categories.py    |    46 -
 .../tests/test_normalization_menu_ingredients.py   |    58 -
 .../test_notification_settings_normalization.py    |    59 -
 apps/api/tests/test_nutrition_pipeline.py          |   193 -
 apps/api/tests/test_profile_normalization.py       |    67 -
 apps/api/tests/test_project_health_audit.py        |    96 -
 apps/api/tests/test_recipe_image_resolver.py       |   116 -
 apps/api/tests/test_recipe_ingredient_audit.py     |   100 -
 apps/api/tests/test_recipe_nutrition_summary.py    |   228 -
 apps/api/tests/test_recipe_write_access.py         |   102 -
 apps/api/tests/test_recipes_catalog.py             |   203 -
 apps/api/tests/test_repair_image_files.py          |    59 -
 apps/api/tests/test_shopping_category_migration.py |   200 -
 apps/api/tests/test_shopping_category_service.py   |   171 -
 apps/api/tests/test_shopping_infer_category.py     |    70 -
 apps/api/tests/test_shopping_list_cleanup.py       |   177 -
 apps/api/tests/test_subscription_normalization.py  |    47 -
 apps/api/tests/test_telegram_webhook_security.py   |    57 -
 apps/api/tests/test_to_taste_migration.py          |   204 -
 apps/web/.env.example                              |     7 -
 apps/web/Dockerfile.prod                           |     2 -
 apps/web/app/account/ams/page.tsx                  |     8 -
 apps/web/app/account/family/page.tsx               |     8 -
 apps/web/app/account/notifications/page.tsx        |     8 -
 apps/web/app/account/nutrition/page.tsx            |    21 -
 apps/web/app/account/page.tsx                      |     8 -
 apps/web/app/account/settings/about/page.tsx       |     1 -
 apps/web/app/account/settings/account/page.tsx     |     1 -
 apps/web/app/account/settings/delete-data/page.tsx |     1 -
 apps/web/app/account/settings/documents/page.tsx   |     1 -
 apps/web/app/account/settings/page.tsx             |    39 -
 apps/web/app/account/settings/support/page.tsx     |     1 -
 .../web/app/account/subscription/checkout/page.tsx |    14 -
 apps/web/app/account/subscription/page.tsx         |    14 -
 apps/web/app/dev/planam-2026/page.tsx              |   150 -
 apps/web/app/family/page.tsx                       |     2 -
 apps/web/app/globals.css                           |   150 -
 apps/web/app/health/care/page.tsx                  |     7 -
 apps/web/app/health/chat/HealthChatPageClient.tsx  |    98 -
 apps/web/app/health/chat/page.tsx                  |    11 -
 apps/web/app/health/page.tsx                       |    11 -
 apps/web/app/health/today/page.tsx                 |    11 -
 apps/web/app/home/page.tsx                         |     9 -
 apps/web/app/home/pantry/page.tsx                  |     8 -
 apps/web/app/home/shopping/page.tsx                |    13 -
 apps/web/app/layout.tsx                            |    12 +-
 apps/web/app/menu/collections/[id]/page.tsx        |     6 -
 apps/web/app/menu/collections/page.tsx             |    11 -
 apps/web/app/menu/current/page.tsx                 |     7 -
 apps/web/app/menu/event/page.tsx                   |    38 +-
 apps/web/app/menu/favorites/page.tsx               |    11 -
 apps/web/app/menu/generate/page.tsx                |     7 -
 apps/web/app/menu/leftovers/page.tsx               |     7 +-
 apps/web/app/menu/page.tsx                         |     7 -
 apps/web/app/menu/recipes/page.tsx                 |    25 -
 apps/web/app/menu/scenarios/page.tsx               |     8 -
 apps/web/app/notifications/page.tsx                |    48 +-
 apps/web/app/nutritionist/care/page.tsx            |     3 +-
 apps/web/app/nutritionist/chat/page.tsx            |    99 +-
 apps/web/app/nutritionist/page.tsx                 |     8 +-
 apps/web/app/onboarding/page.tsx                   |     7 -
 apps/web/app/page.tsx                              |    12 -
 apps/web/app/pantry/page.tsx                       |     7 +-
 apps/web/app/plan/generate/page.tsx                |     8 -
 apps/web/app/plan/page.tsx                         |     8 -
 apps/web/app/plan/recipes/[id]/page.tsx            |    17 -
 apps/web/app/plan/recipes/page.tsx                 |     8 -
 apps/web/app/plan/today/page.tsx                   |    14 -
 apps/web/app/profile/nutrition/page.tsx            |     2 -
 apps/web/app/profile/page.tsx                      |     2 -
 apps/web/app/progress/page.tsx                     |     5 -
 apps/web/app/recipes/[id]/RecipeDetailLegacy.tsx   |    85 -
 apps/web/app/recipes/[id]/page.tsx                 |    86 +-
 apps/web/app/recipes/page.tsx                      |     7 +-
 apps/web/app/settings/page.tsx                     |     2 -
 apps/web/app/shopping/leftovers/page.tsx           |    11 -
 apps/web/app/shopping/page.tsx                     |    13 +-
 apps/web/app/shopping/pantry/page.tsx              |    12 -
 apps/web/app/subscription/page.tsx                 |     7 -
 apps/web/app/wellness/chat/page.tsx                |     8 -
 apps/web/app/wellness/page.tsx                     |     8 -
 apps/web/components/AppProviders.tsx               |    28 +-
 apps/web/components/TelegramProvider.tsx           |     4 +-
 apps/web/components/app-mode/ModeSwitcher.tsx      |    22 +-
 apps/web/components/auth/AppGate.tsx               |    31 +-
 apps/web/components/care/CareSettingsPanel.tsx     |    82 +-
 apps/web/components/care/CareTelegramLinkCard.tsx  |     8 +-
 apps/web/components/dom-2026/Leftovers2026.tsx     |   254 -
 .../web/components/dom-2026/LeftoversSheet2026.tsx |   228 -
 .../components/dom-2026/MealOutcomeSheet2026.tsx   |   235 -
 apps/web/components/dom-2026/Pantry2026.tsx        |   243 -
 apps/web/components/dom-2026/Shopping2026.tsx      |   390 -
 apps/web/components/dom-2026/index.ts              |     5 -
 apps/web/components/family/AddPersonSheet.tsx      |    22 +-
 apps/web/components/family/FamilyDashboard.tsx     |   110 +-
 apps/web/components/family/FamilyManageSheet.tsx   |    35 +-
 apps/web/components/family/InviteSheet.tsx         |    33 +-
 apps/web/components/family/MemberCard.tsx          |    38 +-
 apps/web/components/family/MemberForm.tsx          |    25 +-
 apps/web/components/family/RoleBadge.tsx           |     8 +-
 .../family/VirtualMemberNutritionForm.tsx          |    68 +-
 apps/web/components/home-2026/Home2026.tsx         |   193 -
 .../components/home-2026/MealFallbackPlate2026.tsx |    42 -
 apps/web/components/home-2026/PlanAmHero2026.tsx   |   138 -
 .../components/home-2026/PlanAmStatusRows2026.tsx  |    83 -
 apps/web/components/home-2026/index.ts             |     2 -
 apps/web/components/home/PlanAmHome.tsx            |   434 +-
 apps/web/components/layout/AppShell.tsx            |     5 +-
 apps/web/components/layout/AppShellBridge.tsx      |    46 -
 apps/web/components/layout/BottomBackButton.tsx    |    37 +
 apps/web/components/layout/BottomNav.tsx           |     1 +
 apps/web/components/layout/BottomNavigation.tsx    |    40 +-
 apps/web/components/layout/ScreenBackNav.tsx       |     4 +-
 apps/web/components/layout/ScreenLayout.tsx        |     8 +-
 apps/web/components/layout/SectionHub.tsx          |    68 -
 apps/web/components/layout/SegmentedTabs.tsx       |    53 -
 apps/web/components/layout/StickyBottomBar.tsx     |     2 +-
 apps/web/components/layout/TopBackLink.tsx         |     3 +
 apps/web/components/menu/MealCheckinPanel.tsx      |    24 +-
 apps/web/components/menu/MealLeftoversPage.tsx     |    46 +-
 apps/web/components/menu/MenuChooseVariants.tsx    |    19 +-
 apps/web/components/menu/MenuCurrentView.tsx       |   179 +-
 apps/web/components/menu/MenuDayOverview.tsx       |   247 -
 apps/web/components/menu/MenuDayPicker.tsx         |     6 +-
 apps/web/components/menu/MenuHub.tsx               |   346 +-
 apps/web/components/menu/MenuPlanner.tsx           |   110 +-
 apps/web/components/menu/MenuPlannerSection.tsx    |     4 +-
 apps/web/components/menu/MenuQuickActionsSheet.tsx |    52 -
 apps/web/components/menu/MenuSectionLayout.tsx     |    29 -
 apps/web/components/menu/MenuSettingsPage.tsx      |    27 +-
 apps/web/components/menu/MenuSubTabs.tsx           |    19 -
 apps/web/components/menu/MenuVariantCard.tsx       |    44 +-
 apps/web/components/menu/ReplaceDishModal.tsx      |    28 +-
 .../components/monetization-2026/AmsHub2026.tsx    |   128 -
 .../HomeMonetizationBanner2026.tsx                 |    45 -
 .../monetization-2026/PaymentStub2026.tsx          |   111 -
 .../monetization-2026/PaywallProvider.tsx          |    61 -
 .../monetization-2026/PaywallSheet2026.tsx         |    94 -
 .../components/monetization-2026/PlanCard2026.tsx  |    79 -
 .../monetization-2026/SubscriptionHub2026.tsx      |   206 -
 .../monetization-2026/SubscriptionOffline2026.tsx  |    83 -
 .../monetization-2026/TrialStatus2026.tsx          |    33 -
 apps/web/components/monetization-2026/index.ts     |     5 -
 .../notifications/NotificationSettingsForm.tsx     |    44 +-
 .../components/notifications/NotificationsView.tsx |    83 -
 .../components/nutrition-profile/NumberInput.tsx   |     6 +-
 .../NutritionGoalDetailsFields.tsx                 |    20 +-
 .../nutrition-profile/NutritionProfileForm.tsx     |   104 +-
 .../nutrition-profile/NutritionSection.tsx         |    14 +-
 .../web/components/nutrition-profile/ToggleRow.tsx |     8 +-
 .../components/nutritionist/HealthTodayView.tsx    |   382 -
 .../nutritionist/NutritionistAdviceCard.tsx        |    20 +-
 .../components/nutritionist/NutritionistChat.tsx   |    24 +-
 .../nutritionist/NutritionistDashboard.tsx         |   572 +-
 .../components/nutritionist/WaterIntakePanel.tsx   |    14 +-
 .../onboarding-2026/Onboarding2026Flow.tsx         |   309 -
 .../onboarding-2026/Onboarding2026Redirect.tsx     |    36 -
 .../onboarding-2026/OnboardingChipGrid2026.tsx     |    91 -
 .../onboarding-2026/OnboardingGenerateStep2026.tsx |    79 -
 .../onboarding-2026/OnboardingProgress2026.tsx     |    26 -
 .../onboarding-2026/OnboardingWowReveal2026.tsx    |    63 -
 .../onboarding-2026/TrialWelcomeCard2026.tsx       |    31 -
 apps/web/components/onboarding-2026/index.ts       |     2 -
 .../components/onboarding/ChipSelectWithCustom.tsx |    99 +
 .../components/onboarding/OnboardingComplete.tsx   |    94 +
 .../web/components/onboarding/OnboardingWizard.tsx |   222 +
 apps/web/components/onboarding/ProgressBar.tsx     |    25 +
 apps/web/components/onboarding/StepContent.tsx     |   111 +
 apps/web/components/onboarding/StepNavigation.tsx  |    50 +
 .../components/pantry/PantryCategorySection.tsx    |     8 +-
 apps/web/components/pantry/PantryDashboard.tsx     |    71 +-
 apps/web/components/pantry/PantryItemCard.tsx      |    22 +-
 apps/web/components/pantry/PantryItemForm.tsx      |    29 +-
 apps/web/components/pantry/PantryItemRow.tsx       |    16 +-
 .../components/plan-2026/DayNutritionCard2026.tsx  |   126 -
 apps/web/components/plan-2026/PlanGenerate2026.tsx |   288 -
 apps/web/components/plan-2026/PlanMealCard2026.tsx |   138 -
 .../plan-2026/PlanTimelineSection2026.tsx          |    46 -
 apps/web/components/plan-2026/PlanToday2026.tsx    |   316 -
 apps/web/components/plan-2026/PlanWeek2026.tsx     |   131 -
 .../components/plan-2026/ReplaceDishSheet2026.tsx  |   188 -
 apps/web/components/plan-2026/index.ts             |     5 -
 .../planam-2026/account/AccountHub2026.tsx         |   110 -
 .../planam-2026/cards/ActionCard2026.tsx           |    80 -
 .../components/planam-2026/cards/HeroCard2026.tsx  |   103 -
 .../planam-2026/cards/InsightCard2026.tsx          |    47 -
 .../planam-2026/cards/MetricCard2026.tsx           |    44 -
 apps/web/components/planam-2026/index.ts           |    15 -
 .../components/planam-2026/layout/AppShell2026.tsx |    26 -
 .../planam-2026/layout/ShellHeader2026.tsx         |    40 -
 .../navigation/BottomNavigation2026.tsx            |    85 -
 .../planam-2026/navigation/NavIcon2026.tsx         |   170 -
 .../planam-2026/navigation/ScreenBack2026.tsx      |    42 -
 .../planam-2026/navigation/SectionSubTabs2026.tsx  |    54 -
 .../navigation/TelegramBackBridge2026.tsx          |    12 -
 .../navigation/useTelegramBackButton2026.ts        |    64 -
 .../planam-2026/screens/RoutePlaceholder2026.tsx   |    25 -
 .../components/planam-2026/theme/ThemeProvider.tsx |   134 -
 .../planam-2026/theme/ThemeToggle2026.tsx          |    50 -
 .../components/planam-2026/ui/BottomSheet2026.tsx  |    62 -
 apps/web/components/planam-2026/ui/Button2026.tsx  |    58 -
 apps/web/components/planam-2026/ui/Card2026.tsx    |    34 -
 .../components/planam-2026/ui/EmptyState2026.tsx   |    46 -
 .../web/components/planam-2026/ui/Skeleton2026.tsx |    30 -
 apps/web/components/profile/ProfileDashboard.tsx   |    44 +-
 apps/web/components/profile/ProfileModeControl.tsx |    18 +-
 apps/web/components/progress/ProgressDashboard.tsx |   116 +-
 apps/web/components/progress/ProgressProLocked.tsx |    25 +-
 .../components/recipes-2026/MenuSlotSheet2026.tsx  |   195 -
 .../components/recipes-2026/RecipeCatalog2026.tsx  |   366 -
 .../components/recipes-2026/RecipeDetail2026.tsx   |   439 -
 .../components/recipes-2026/RecipeGridCard2026.tsx |   112 -
 .../components/recipes-2026/RecipeImage2026.tsx    |    61 -
 apps/web/components/recipes-2026/index.ts          |     4 -
 .../components/recipes/CollectionDetailView.tsx    |   162 -
 apps/web/components/recipes/CollectionsView.tsx    |   169 -
 apps/web/components/recipes/FavoritesView.tsx      |   132 -
 apps/web/components/recipes/FilterChip.tsx         |    25 -
 apps/web/components/recipes/FromPantrySection.tsx  |   158 -
 apps/web/components/recipes/RecipeCard.tsx         |    38 +-
 apps/web/components/recipes/RecipeCatalog.tsx      |   378 +
 .../components/recipes/RecipeCatalogSections.tsx   |    62 +-
 apps/web/components/recipes/RecipeDetailModal.tsx  |   519 +-
 .../components/recipes/RecipeDetailMorePanel.tsx   |   352 -
 apps/web/components/recipes/RecipeFiltersSheet.tsx |   186 -
 apps/web/components/recipes/RecipeListSkeleton.tsx |    23 -
 apps/web/components/recipes/RecipeResultsList.tsx  |    33 -
 apps/web/components/recipes/RecipesView.tsx        |   365 -
 apps/web/components/recipes/ScenarioChips.tsx      |    84 -
 apps/web/components/settings/SettingsScaffold.tsx  |    49 +-
 apps/web/components/shopping/CategoryPicker.tsx    |    30 +-
 .../shopping/ShoppingCategorySection.tsx           |    10 +-
 .../components/shopping/ShoppingCategorySheet.tsx  |    15 +-
 apps/web/components/shopping/ShoppingItemRow.tsx   |    18 +-
 apps/web/components/shopping/ShoppingItemSheet.tsx |    25 +-
 apps/web/components/shopping/ShoppingListView.tsx  |    79 +-
 .../components/shopping/ShoppingSectionLayout.tsx  |    54 -
 apps/web/components/shopping/ShoppingSubTabs.tsx   |    18 -
 .../components/subscription/AmaConfirmDialog.tsx   |    60 +-
 .../subscription/SubscriptionDashboard.tsx         |    82 +-
 apps/web/components/ui/HubTile.tsx                 |   101 -
 apps/web/components/ui/Sheet.tsx                   |    10 +-
 apps/web/components/ui/Skeleton.tsx                |     4 +-
 apps/web/components/ui/ToastProvider.tsx           |    11 +-
 .../components/wellness-2026/WaterIntake2026.tsx   |   121 -
 .../components/wellness-2026/WellnessChat2026.tsx  |   100 -
 .../components/wellness-2026/WellnessChip2026.tsx  |    76 -
 .../wellness-2026/WellnessDayRing2026.tsx          |    39 -
 .../wellness-2026/WellnessGoalCard2026.tsx         |    62 -
 .../components/wellness-2026/WellnessHome2026.tsx  |   274 -
 .../wellness-2026/WellnessInsight2026.tsx          |    34 -
 .../wellness-2026/WellnessTodayCard2026.tsx        |    28 -
 .../wellness-2026/WellnessWeekStrip2026.tsx        |    42 -
 apps/web/components/wellness-2026/index.ts         |     3 -
 apps/web/lib/api-client.ts                         |    25 +-
 apps/web/lib/dom/pantry-sections.ts                |    44 -
 apps/web/lib/dom/shopping-groups.ts                |    49 -
 apps/web/lib/home/home-2026-data.ts                |   181 -
 apps/web/lib/home/planam-hero-2026.test.ts         |   153 -
 apps/web/lib/home/planam-hero-2026.ts              |   233 -
 apps/web/lib/home/redirect-path-2026.ts            |    42 -
 apps/web/lib/home/use-compact-viewport.ts          |    21 -
 apps/web/lib/meal-checkins/api.ts                  |     4 +-
 apps/web/lib/menu/api.ts                           |   167 +-
 apps/web/lib/menu/labels.ts                        |     6 +-
 apps/web/lib/menu/menu-days.ts                     |    33 -
 apps/web/lib/menu/overview-types.ts                |    32 +-
 apps/web/lib/menu/planner-options.ts               |     4 +-
 apps/web/lib/menu/quick-actions.ts                 |    52 -
 apps/web/lib/menu/replace-slot.ts                  |    52 -
 apps/web/lib/menu/types.ts                         |     2 -
 apps/web/lib/monetization/billing-status.ts        |   162 -
 apps/web/lib/monetization/paths.ts                 |    10 -
 apps/web/lib/monetization/paywall.ts               |    82 -
 apps/web/lib/monetization/plan-catalog-2026.ts     |   127 -
 apps/web/lib/monetization/trial-config.ts          |    11 -
 apps/web/lib/navigation/back-navigation-2026.ts    |    74 -
 apps/web/lib/navigation/nav-config-2026.ts         |   356 -
 apps/web/lib/navigation/nav-config.ts              |   124 -
 apps/web/lib/navigation/return-to.ts               |    66 +-
 apps/web/lib/navigation/route-migration-2026.ts    |    61 -
 apps/web/lib/onboarding-2026/config.ts             |   151 -
 apps/web/lib/pantry/api.ts                         |     2 +-
 apps/web/lib/pantry/types.ts                       |     2 +-
 apps/web/lib/plan/add-to-shopping.ts               |    21 -
 apps/web/lib/plan/plan-paths.ts                    |    46 -
 apps/web/lib/plan/plan-today.ts                    |   162 -
 apps/web/lib/planam/cn.ts                          |     6 -
 apps/web/lib/planam/embedded-2026.ts               |    15 -
 apps/web/lib/planam/feature-flags.ts               |    21 -
 apps/web/lib/planam/layout-constants-2026.ts       |     3 -
 apps/web/lib/planam/onboarding-gate.ts             |    34 -
 apps/web/lib/planam/planam-2026-page.ts            |    19 -
 apps/web/lib/planam/routes.ts                      |    91 -
 apps/web/lib/planam/theme-document.ts              |    81 -
 apps/web/lib/planam/theme.ts                       |    52 -
 apps/web/lib/planam/ui-scope.ts                    |    21 -
 apps/web/lib/progress/api.ts                       |     8 -
 apps/web/lib/recipes/analysis-api.ts               |    26 +-
 apps/web/lib/recipes/api.ts                        |   143 -
 apps/web/lib/recipes/catalog-sections.ts           |    11 -
 apps/web/lib/recipes/ingredient-amount.ts          |    36 -
 apps/web/lib/recipes/menu-from-recipe.ts           |    61 -
 apps/web/lib/recipes/nutrition.ts                  |    90 -
 apps/web/lib/recipes/recipe-media.ts               |   102 -
 apps/web/lib/recipes/types.ts                      |   158 -
 apps/web/lib/shopping/categories-v1.ts             |    92 -
 apps/web/lib/shopping/category-suggest.test.ts     |    38 -
 apps/web/lib/shopping/category-suggest.ts          |    71 +-
 apps/web/lib/shopping/labels.ts                    |    31 +-
 apps/web/lib/shopping/types.ts                     |     4 +-
 apps/web/lib/wellness/goal-labels.ts               |    27 -
 apps/web/lib/wellness/home-wellness.ts             |    67 -
 apps/web/lib/wellness/week-strip.ts                |    57 -
 apps/web/lib/wellness/wellness-insight.ts          |    88 -
 apps/web/lib/wellness/wellness-status.ts           |   155 -
 apps/web/middleware.ts                             |    61 -
 apps/web/public/brand/planam-icon.svg              |     5 -
 apps/web/public/brand/planam-mark.svg              |     4 -
 apps/web/public/recipe-images/.gitkeep             |     0
 apps/web/tailwind.config.ts                        |    89 +-
 apps/web/tsconfig.tsbuildinfo                      |     1 -
 backend/data/nutrition_reference_seed.json         |  1105 --
 backend/pytest.ini                                 |     3 -
 backend/scripts/_image_paths.py                    |    85 -
 backend/scripts/analyze_povarenok_dataset.py       |   466 -
 backend/scripts/analyze_recipe_dataset.py          |   340 -
 .../scripts/apply_calculated_nutrition_updates.py  |   466 -
 backend/scripts/apply_nutrition_backfill.py        |   489 -
 backend/scripts/apply_recipe_images.py             |   232 -
 backend/scripts/apply_recipe_steps_updates.py      |   375 -
 backend/scripts/archive_placeholder_recipes.py     |    92 -
 .../scripts/audit_beverage_nutrition_strategy.py   |   395 -
 backend/scripts/audit_menu_nutrition_readiness.py  |   220 -
 backend/scripts/audit_nutrition_update_deltas.py   |   506 -
 backend/scripts/audit_povarenok_jsonl.py           |   365 -
 backend/scripts/audit_project_health.py            |   513 -
 backend/scripts/audit_recipe_catalog.py            |   331 -
 backend/scripts/audit_recipe_duplicates.py         |   230 -
 backend/scripts/audit_recipe_images.py             |   104 -
 .../audit_recipe_ingredient_display_amounts.py     |   209 -
 backend/scripts/audit_recipe_ingredients.py        |   503 -
 backend/scripts/audit_recipe_steps_after_update.py |   141 -
 backend/scripts/audit_recipe_steps_quality.py      |   341 -
 backend/scripts/audit_recipe_steps_v2.py           |   231 -
 backend/scripts/audit_remaining_nutrition_gaps.py  |   470 -
 backend/scripts/audit_weak_steps_remediation.py    |   340 -
 backend/scripts/build_enrichment_batch.py          |   200 -
 backend/scripts/build_holiday_kids_steps_batch.py  |   263 -
 backend/scripts/build_holiday_kids_steps_update.py |   312 -
 backend/scripts/build_planam_v1_catalog.py         |   361 -
 backend/scripts/build_recipe_image_prompts.py      |   118 -
 backend/scripts/build_remaining_weak_groups.py     |   356 -
 backend/scripts/build_simple_beverage_updates.py   |   354 -
 .../scripts/build_steps_update_from_enrichment.py  |   299 -
 .../scripts/build_verified_nutrition_updates.py    |   281 -
 backend/scripts/calculate_nutrition.py             |   275 -
 .../scripts/calculate_recipe_nutrition_preview.py  |   530 -
 .../scripts/calculate_recipe_nutrition_summary.py  |   436 -
 backend/scripts/canonical_products.py              |   426 -
 backend/scripts/convert_enriched_to_import_json.py |   330 -
 .../convert_nutrition_backfill_to_update_json.py   |   231 -
 backend/scripts/convert_povarenok.py               |   425 -
 backend/scripts/evaluate_photo_prompt_readiness.py |   151 -
 .../scripts/export_calculated_nutrition_updates.py |   356 -
 backend/scripts/generate_shopping_list_groups.py   |   174 -
 backend/scripts/import_recipes.py                  |   549 -
 backend/scripts/migrate_to_taste_ingredients.py    |   452 -
 backend/scripts/normalize_ingredient_amounts.py    |   689 -
 backend/scripts/normalize_recipe_ingredients.py    |   573 -
 backend/scripts/nutrition_data.py                  |   353 -
 .../scripts/nutrition_shopping_photo_pipeline.py   |   236 -
 backend/scripts/openai_recipe_image_client.py      |   219 -
 backend/scripts/plan_nutrition_backfill.py         |   357 -
 backend/scripts/plan_recipe_dedup.py               |   215 -
 .../scripts/prepare_povarenok_enrichment_input.py  |   256 -
 backend/scripts/process_recipe_images.py           |   143 -
 backend/scripts/recipe_id_resolver.py              |    60 -
 backend/scripts/recipe_image_utils.py              |   252 -
 backend/scripts/recipe_nutrition_calculator.py     |   211 -
 backend/scripts/repair_recipe_image_assignments.py |   219 -
 backend/scripts/report_recipe_readiness.py         |   221 -
 backend/scripts/resync_recipe_ingredients_jsonb.py |   269 -
 backend/scripts/run_enrichment_pilot.py            |   444 -
 backend/scripts/run_nutrition_backfill.py          |   437 -
 backend/scripts/run_recipe_image_pilot.py          |   295 -
 backend/scripts/run_steps_enrichment.py            |   965 --
 backend/scripts/select_povarenok_candidates.py     |   370 -
 backup_before_import_10.sql                        |   Bin 512178 -> 0 bytes
 backup_before_import_100.sql                       |   Bin 771986 -> 0 bytes
 data/planam_v1_canonical_products.json             |  1487 --
 data/planam_v1_image_pilot_batch.json              |   192 -
 data/planam_v1_nutrition_facts.json                |  1083 --
 data/planam_v1_recipes.json                        | 16189 -------------------
 deploy/nginx/nginx.conf                            |     5 -
 deploy/nginx/templates/app-init.conf.template      |    58 +-
 deploy/nginx/templates/app-ssl.conf.template       |    68 +-
 docker-compose.prod.yml                            |    16 -
 docker-compose.yml                                 |    10 -
 docs/ADMIN_PANEL_INCIDENT_AUDIT.md                 |   569 -
 docs/BETA_HARDENING_REPORT.md                      |   106 -
 docs/BETA_READINESS_AUDIT.md                       |   322 -
 docs/CODEBASE_INDEX.md                             |   930 --
 docs/DOMAIN_ARCHITECTURE.md                        |   697 -
 docs/NAVIGATION_GRAPH.md                           |   517 -
 docs/NAVIGATION_MAP.md                             |    66 -
 docs/PLANAM_2026_COLOR_FIX_REPORT.md               |    83 -
 docs/PLANAM_2026_DECISION_RECORD.md                |    79 -
 docs/PLANAM_2026_FINAL_UX_QA_REPORT.md             |   136 -
 docs/PLANAM_2026_IMPLEMENTATION_ROADMAP.md         |   712 -
 docs/PLANAM_2026_PRODUCT_BLUEPRINT.md              |   757 -
 docs/PLANAM_COLOR_SYSTEM_V1.md                     |    42 -
 docs/PLANAM_CONVERSION_FUNNEL_2026.md              |   316 -
 docs/PLANAM_CURRENT_STATE_ACTIONS.md               |   248 -
 docs/PLANAM_CURRENT_STATE_COMPONENTS.md            |   149 -
 docs/PLANAM_CURRENT_STATE_DATA.md                  |   250 -
 docs/PLANAM_CURRENT_STATE_LAYOUTS.md               |   179 -
 docs/PLANAM_CURRENT_STATE_MASTER.md                |   229 -
 docs/PLANAM_CURRENT_STATE_NAVIGATION.md            |   218 -
 docs/PLANAM_CURRENT_STATE_OVERLAYS.md              |    89 -
 docs/PLANAM_CURRENT_STATE_SCREENS.md               |   337 -
 docs/PLANAM_CURRENT_STATE_USER_FLOWS.md            |   310 -
 docs/PLANAM_DESIGN_SYSTEM_2026.md                  |   769 -
 docs/PLANAM_FINAL_PRODUCT_REVIEW.md                |   402 -
 ...AM_HOTFIX_SHOPPING_CATEGORY_MIGRATION_REPORT.md |   164 -
 docs/PLANAM_LEGACY_DECOMMISSION_AUDIT.md           |   686 -
 docs/PLANAM_LEGACY_REMOVAL_BACKLOG.md              |   115 -
 docs/PLANAM_NAVIGATION_LEGACY_AUDIT.md             |   327 -
 docs/PLANAM_NOTIFICATION_SYSTEM_2026.md            |   289 -
 docs/PLANAM_PAYMENT_ARCHITECTURE_2026.md           |   114 -
 docs/PLANAM_PRODUCTION_UX_POLISH_V1_REPORT.md      |   127 -
 docs/PLANAM_RECIPES_CATALOG_AUDIT_AND_FIX.md       |   111 -
 docs/PLANAM_RECIPE_CATALOG_QUALITY_V1_REPORT.md    |   125 -
 docs/PLANAM_RECIPE_DB_GO_REPORT.md                 |   159 -
 docs/PLANAM_RECIPE_MEDIA_ARCHITECTURE.md           |   265 -
 docs/PLANAM_RECIPE_MENU_INTEGRATION_V1_REPORT.md   |   103 -
 docs/PLANAM_RECIPE_REPLACE_FLOW_V1_REPORT.md       |   106 -
 docs/PLANAM_UX_POLISH_V2_REPORT.md                 |   147 -
 docs/PLANAM_UX_UI_2026_MASTER_SPEC.md              |  1202 --
 docs/PLANAM_V1_AI_JOURNEY.md                       |   163 -
 docs/PLANAM_V1_CANONICAL_PRODUCTS.md               |   154 -
 docs/PLANAM_V1_CLEAN_FOUNDATION_REPORT.md          |   260 -
 docs/PLANAM_V1_DOCUMENTATION_FREEZE_REPORT.md      |   162 -
 docs/PLANAM_V1_FAMILY_MODEL.md                     |   226 -
 docs/PLANAM_V1_FINAL_VISION.md                     |   459 -
 docs/PLANAM_V1_GROWTH_MODEL.md                     |   142 -
 docs/PLANAM_V1_HOME_STATES.md                      |   247 -
 docs/PLANAM_V1_IMAGE_STRATEGY.md                   |   171 -
 docs/PLANAM_V1_INGREDIENT_QUALITY_AUDIT.md         |    90 -
 ...M_V1_INGREDIENT_SAFE_COMMIT_AND_JSONB_RESYNC.md |   146 -
 docs/PLANAM_V1_LIFE_SCENARIOS.md                   |   174 -
 docs/PLANAM_V1_MENU_NUTRITION_AGGREGATION.md       |   150 -
 docs/PLANAM_V1_NUTRITION_SHOPPING_PHOTO.md         |   106 -
 docs/PLANAM_V1_PRODUCT_BACKLOG.md                  |   223 -
 docs/PLANAM_V1_PRODUCT_MASTER.md                   |   257 -
 docs/PLANAM_V1_RECIPE_FOUNDATION_REPORT.md         |   142 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_BUDGET.md           |    88 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_PILOT.md            |    92 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_PROMPTS.md          |   115 -
 docs/PLANAM_V1_RECIPE_IMAGE_PILOT_BUDGET_REPORT.md |    75 -
 docs/PLANAM_V1_RECIPE_IMAGE_PILOT_REPORT.md        |   137 -
 docs/PLANAM_V1_RECIPE_IMAGE_PLAN.md                |    90 -
 docs/PLANAM_V1_RECIPE_IMAGE_STYLE_SYSTEM.md        |   157 -
 docs/PLANAM_V1_RECIPE_IMAGE_TOKEN_SETUP.md         |    88 -
 docs/PLANAM_V1_RECIPE_IMPORT_PIPELINE.md           |   116 -
 docs/PLANAM_V1_RECIPE_NUTRITION_SUMMARY.md         |   127 -
 docs/PLANAM_V1_RECIPE_QUALITY_REPORT.md            |    88 -
 docs/PLANAM_V1_RELEASE_BLUEPRINT.md                |   588 -
 docs/PLANAM_V1_RELEASE_SCREENS.md                  |   167 -
 docs/PLANAM_V1_SHOPPING_MODEL_UPDATE.md            |   177 -
 docs/PLANAM_V1_SPRINT1_5_REPORT.md                 |   178 -
 docs/PLANAM_V1_SPRINT1_DESIGN_REVIEW.md            |   135 -
 docs/PLANAM_V1_SPRINT1_DESIGN_SPEC.md              |   466 -
 docs/PLANAM_V1_SPRINT1_IMPLEMENTATION_REPORT.md    |   148 -
 docs/PLANAM_V1_TO_TASTE_AND_READINESS.md           |   117 -
 docs/PLANAM_V1_TO_V2_STRATEGY.md                   |   143 -
 docs/PLANAM_VISUAL_MOCKUPS_2026.md                 |   564 -
 ...PLANAM_VISUAL_PACKAGE_2026_EXECUTIVE_SUMMARY.md |   199 -
 docs/PRODUCTION_DEPLOY.md                          |   280 -
 docs/RECIPE_ENGINE_API.md                          |   214 -
 docs/RECIPE_ENGINE_ENV.md                          |    35 -
 docs/RECIPE_ENGINE_V1.md                           |  1004 --
 docs/RECIPE_IMPORT_PIPELINE.md                     |   157 -
 docs/SCREEN_MAP.md                                 |   982 +-
 docs/SECURITY_AUDIT.md                             |   417 -
 docs/SECURITY_FIX_ROADMAP.md                       |   135 -
 docs/SPRINT_0_6_AUDIT.md                           |   378 -
 docs/SPRINT_0_COMPLETION_REPORT.md                 |   300 -
 docs/SPRINT_1_COMPLETION_REPORT.md                 |   194 -
 docs/SPRINT_2_COMPLETION_REPORT.md                 |   221 -
 docs/SPRINT_3_COMPLETION_REPORT.md                 |   185 -
 docs/SPRINT_4_COMPLETION_REPORT.md                 |   190 -
 docs/SPRINT_5_COMPLETION_REPORT.md                 |   241 -
 docs/SPRINT_6_COMPLETION_REPORT.md                 |   187 -
 docs/SPRINT_7_COMPLETION_REPORT.md                 |   216 -
 docs/SPRINT_8_COMPLETION_REPORT.md                 |   190 -
 docs/SPRINT_9_COMPLETION_REPORT.md                 |   167 -
 docs/UI_SYSTEM_AUDIT.md                            |   602 -
 docs/USER_RESET.md                                 |   320 -
 docs/UX_FLOW_MAP.md                                |   537 -
 docs/sql/shopping_categories_find_duplicates.sql   |    46 -
 nav-calls.txt                                      |     0
 pages.txt                                          |   Bin 10254 -> 0 bytes
 project-tree.txt                                   |   Bin 2035782 -> 0 bytes
 reports/dataset_analysis.md                        |   145 -
 reports/planam_cross_branch_audit.md               |    97 -
 reports/planam_project_consolidation_audit.md      |   262 -
 reports/planam_v1_hero_top50.json                  |   302 -
 reports/planam_v1_recipe_image_pilot_results.json  |    22 -
 reports/povarenok_analysis.md                      |   139 -
 reports/povarenok_conversion_report.md             |   141 -
 reports/profile_account_consolidation_audit.md     |   110 -
 reports/ui_2026_consolidation_audit.md             |   113 -
 sample_recipes.json                                |   589 -
 scripts/dedupe_shopping_categories.py              |   116 -
 scripts/reset_user.py                              |   534 -
 609 files changed, 5187 insertions(+), 98670 deletions(-)
```

### Unique commits in origin/release-candidate-ux not in sprint-0/planam-2026-foundation

*(none — branch has no commits ahead of current)*

## Diff summary: sprint-0/planam-2026-foundation vs origin/recipe-engine-v1

```
.env.production.example                            |     9 -
 .gitignore                                         |    33 -
 apps/api/.env.example                              |     8 -
 apps/api/app/config.py                             |    28 +-
 apps/api/app/database_migrations.py                |   139 +-
 apps/api/app/models/pantry.py                      |     2 +-
 apps/api/app/models/recipe.py                      |    39 -
 apps/api/app/routers/menus.py                      |   144 +-
 apps/api/app/routers/recipes.py                    |    58 +-
 apps/api/app/routers/telegram_bot.py               |    29 +-
 apps/api/app/schemas/menu.py                       |     3 -
 apps/api/app/schemas/menu_nutrition.py             |    75 -
 apps/api/app/schemas/menu_overview.py              |    65 -
 apps/api/app/schemas/pantry.py                     |     4 +-
 apps/api/app/schemas/recipe.py                     |    27 -
 apps/api/app/services/admin_auth.py                |     2 +-
 apps/api/app/services/bot_menu.py                  |     3 +-
 apps/api/app/services/categories_v1.py             |   122 -
 apps/api/app/services/family_member_nutrition.py   |     4 +-
 apps/api/app/services/home_next_action.py          |   132 -
 apps/api/app/services/ingredient_format.py         |   129 -
 apps/api/app/services/meal_attendance.py           |    27 -
 apps/api/app/services/menu.py                      |    26 -
 apps/api/app/services/menu_ai.py                   |    10 +-
 apps/api/app/services/menu_ai_legacy.py            |    70 +-
 apps/api/app/services/menu_ai_parsing.py           |   168 -
 apps/api/app/services/menu_overview.py             |    19 +-
 apps/api/app/services/menu_recipe_plan.py          |   438 -
 apps/api/app/services/normalization/__init__.py    |    47 -
 apps/api/app/services/normalization/amounts.py     |    43 -
 apps/api/app/services/normalization/categories.py  |    55 -
 apps/api/app/services/normalization/ingredients.py |    48 -
 apps/api/app/services/normalization/menu.py        |    23 -
 .../app/services/normalization/notifications.py    |    99 -
 apps/api/app/services/normalization/profile.py     |   121 -
 apps/api/app/services/normalization/shopping.py    |    23 -
 .../api/app/services/normalization/subscription.py |    72 -
 apps/api/app/services/notifications.py             |    24 +-
 apps/api/app/services/nutrition/__init__.py        |     1 -
 apps/api/app/services/nutrition/plan_aggregator.py |   395 -
 apps/api/app/services/nutrition_profile.py         |     3 -
 apps/api/app/services/pantry.py                    |     2 +-
 apps/api/app/services/recipe_storage.py            |    44 +-
 apps/api/app/services/recipes/access.py            |    59 -
 apps/api/app/services/recipes/authoring.py         |    46 +-
 apps/api/app/services/recipes/catalog.py           |    71 +-
 apps/api/app/services/recipes/mapper.py            |    57 +-
 apps/api/app/services/recipes/repository.py        |    13 +-
 apps/api/app/services/recipes/title_normalize.py   |    55 -
 apps/api/app/services/recipes/types.py             |     2 -
 apps/api/app/services/shopping_categories.py       |   239 +-
 .../app/services/shopping_category_migration.py    |   274 -
 apps/api/app/services/shopping_category_service.py |   115 +-
 apps/api/app/services/shopping_item_utils.py       |   202 +-
 apps/api/app/services/shopping_list.py             |    31 +-
 apps/api/app/services/subscription.py              |     4 +-
 apps/api/app/services/subscription_catalog.py      |     8 +-
 apps/api/requirements.txt                          |     1 -
 apps/api/tests/test_categories_v1.py               |    45 -
 apps/api/tests/test_home_next_action.py            |    72 -
 apps/api/tests/test_ingredient_display_amounts.py  |   116 -
 apps/api/tests/test_ingredient_normalization.py    |   230 -
 apps/api/tests/test_menu_ai_parsing.py             |    97 -
 apps/api/tests/test_menu_nutrition_aggregation.py  |   183 -
 apps/api/tests/test_menu_recipe_plan.py            |   225 -
 apps/api/tests/test_menu_replace.py                |   176 -
 apps/api/tests/test_normalization_amounts.py       |    57 -
 apps/api/tests/test_normalization_categories.py    |    46 -
 .../tests/test_normalization_menu_ingredients.py   |    58 -
 .../test_notification_settings_normalization.py    |    59 -
 apps/api/tests/test_nutrition_pipeline.py          |   193 -
 apps/api/tests/test_profile_normalization.py       |    67 -
 apps/api/tests/test_project_health_audit.py        |    96 -
 apps/api/tests/test_recipe_image_resolver.py       |   116 -
 apps/api/tests/test_recipe_ingredient_audit.py     |   100 -
 apps/api/tests/test_recipe_nutrition_summary.py    |   228 -
 apps/api/tests/test_recipe_write_access.py         |   102 -
 apps/api/tests/test_recipes_catalog.py             |   203 -
 apps/api/tests/test_repair_image_files.py          |    59 -
 apps/api/tests/test_shopping_category_migration.py |   200 -
 apps/api/tests/test_shopping_category_service.py   |   171 -
 apps/api/tests/test_shopping_infer_category.py     |    70 -
 apps/api/tests/test_shopping_list_cleanup.py       |   177 -
 apps/api/tests/test_subscription_normalization.py  |    47 -
 apps/api/tests/test_telegram_webhook_security.py   |    57 -
 apps/api/tests/test_to_taste_migration.py          |   204 -
 apps/web/.env.example                              |     7 -
 apps/web/Dockerfile.prod                           |     2 -
 apps/web/app/account/ams/page.tsx                  |     8 -
 apps/web/app/account/family/page.tsx               |     8 -
 apps/web/app/account/notifications/page.tsx        |     8 -
 apps/web/app/account/nutrition/page.tsx            |    21 -
 apps/web/app/account/page.tsx                      |     8 -
 apps/web/app/account/settings/about/page.tsx       |     1 -
 apps/web/app/account/settings/account/page.tsx     |     1 -
 apps/web/app/account/settings/delete-data/page.tsx |     1 -
 apps/web/app/account/settings/documents/page.tsx   |     1 -
 apps/web/app/account/settings/page.tsx             |    39 -
 apps/web/app/account/settings/support/page.tsx     |     1 -
 .../web/app/account/subscription/checkout/page.tsx |    14 -
 apps/web/app/account/subscription/page.tsx         |    14 -
 apps/web/app/dev/planam-2026/page.tsx              |   150 -
 apps/web/app/family/page.tsx                       |     2 -
 apps/web/app/globals.css                           |   150 -
 apps/web/app/health/care/page.tsx                  |     7 -
 apps/web/app/health/chat/HealthChatPageClient.tsx  |    98 -
 apps/web/app/health/chat/page.tsx                  |    11 -
 apps/web/app/health/page.tsx                       |    11 -
 apps/web/app/health/today/page.tsx                 |    11 -
 apps/web/app/home/page.tsx                         |     9 -
 apps/web/app/home/pantry/page.tsx                  |     8 -
 apps/web/app/home/shopping/page.tsx                |    13 -
 apps/web/app/layout.tsx                            |    12 +-
 apps/web/app/menu/collections/[id]/page.tsx        |     6 -
 apps/web/app/menu/collections/page.tsx             |    11 -
 apps/web/app/menu/current/page.tsx                 |     7 -
 apps/web/app/menu/event/page.tsx                   |    38 +-
 apps/web/app/menu/favorites/page.tsx               |    11 -
 apps/web/app/menu/generate/page.tsx                |     7 -
 apps/web/app/menu/leftovers/page.tsx               |     7 +-
 apps/web/app/menu/page.tsx                         |     7 -
 apps/web/app/menu/recipes/page.tsx                 |    25 -
 apps/web/app/menu/scenarios/page.tsx               |     8 -
 apps/web/app/notifications/page.tsx                |    48 +-
 apps/web/app/nutritionist/care/page.tsx            |     3 +-
 apps/web/app/nutritionist/chat/page.tsx            |    99 +-
 apps/web/app/nutritionist/page.tsx                 |     8 +-
 apps/web/app/onboarding/page.tsx                   |     7 -
 apps/web/app/page.tsx                              |    12 -
 apps/web/app/pantry/page.tsx                       |     7 +-
 apps/web/app/plan/generate/page.tsx                |     8 -
 apps/web/app/plan/page.tsx                         |     8 -
 apps/web/app/plan/recipes/[id]/page.tsx            |    17 -
 apps/web/app/plan/recipes/page.tsx                 |     8 -
 apps/web/app/plan/today/page.tsx                   |    14 -
 apps/web/app/profile/nutrition/page.tsx            |     2 -
 apps/web/app/profile/page.tsx                      |     2 -
 apps/web/app/progress/page.tsx                     |     5 -
 apps/web/app/recipes/[id]/RecipeDetailLegacy.tsx   |    85 -
 apps/web/app/recipes/[id]/page.tsx                 |    86 +-
 apps/web/app/recipes/page.tsx                      |     7 +-
 apps/web/app/settings/page.tsx                     |     2 -
 apps/web/app/shopping/leftovers/page.tsx           |    11 -
 apps/web/app/shopping/page.tsx                     |    13 +-
 apps/web/app/shopping/pantry/page.tsx              |    12 -
 apps/web/app/subscription/page.tsx                 |     7 -
 apps/web/app/wellness/chat/page.tsx                |     8 -
 apps/web/app/wellness/page.tsx                     |     8 -
 apps/web/components/AppProviders.tsx               |    28 +-
 apps/web/components/TelegramProvider.tsx           |     4 +-
 apps/web/components/app-mode/ModeSwitcher.tsx      |    22 +-
 apps/web/components/auth/AppGate.tsx               |    31 +-
 apps/web/components/care/CareSettingsPanel.tsx     |    82 +-
 apps/web/components/care/CareTelegramLinkCard.tsx  |     8 +-
 apps/web/components/dom-2026/Leftovers2026.tsx     |   254 -
 .../web/components/dom-2026/LeftoversSheet2026.tsx |   228 -
 .../components/dom-2026/MealOutcomeSheet2026.tsx   |   235 -
 apps/web/components/dom-2026/Pantry2026.tsx        |   243 -
 apps/web/components/dom-2026/Shopping2026.tsx      |   390 -
 apps/web/components/dom-2026/index.ts              |     5 -
 apps/web/components/family/AddPersonSheet.tsx      |    22 +-
 apps/web/components/family/FamilyDashboard.tsx     |   110 +-
 apps/web/components/family/FamilyManageSheet.tsx   |    35 +-
 apps/web/components/family/InviteSheet.tsx         |    33 +-
 apps/web/components/family/MemberCard.tsx          |    38 +-
 apps/web/components/family/MemberForm.tsx          |    25 +-
 apps/web/components/family/RoleBadge.tsx           |     8 +-
 .../family/VirtualMemberNutritionForm.tsx          |    68 +-
 apps/web/components/home-2026/Home2026.tsx         |   193 -
 .../components/home-2026/MealFallbackPlate2026.tsx |    42 -
 apps/web/components/home-2026/PlanAmHero2026.tsx   |   138 -
 .../components/home-2026/PlanAmStatusRows2026.tsx  |    83 -
 apps/web/components/home-2026/index.ts             |     2 -
 apps/web/components/home/PlanAmHome.tsx            |   434 +-
 apps/web/components/layout/AppShell.tsx            |     5 +-
 apps/web/components/layout/AppShellBridge.tsx      |    46 -
 apps/web/components/layout/BottomBackButton.tsx    |    37 +
 apps/web/components/layout/BottomNav.tsx           |     1 +
 apps/web/components/layout/BottomNavigation.tsx    |    40 +-
 apps/web/components/layout/ScreenBackNav.tsx       |     4 +-
 apps/web/components/layout/ScreenLayout.tsx        |     8 +-
 apps/web/components/layout/SectionHub.tsx          |    68 -
 apps/web/components/layout/SegmentedTabs.tsx       |    53 -
 apps/web/components/layout/StickyBottomBar.tsx     |     2 +-
 apps/web/components/layout/TopBackLink.tsx         |     3 +
 apps/web/components/menu/MealCheckinPanel.tsx      |    24 +-
 apps/web/components/menu/MealLeftoversPage.tsx     |    46 +-
 apps/web/components/menu/MenuChooseVariants.tsx    |    19 +-
 apps/web/components/menu/MenuCurrentView.tsx       |   179 +-
 apps/web/components/menu/MenuDayOverview.tsx       |   247 -
 apps/web/components/menu/MenuDayPicker.tsx         |     6 +-
 apps/web/components/menu/MenuHub.tsx               |   346 +-
 apps/web/components/menu/MenuPlanner.tsx           |   110 +-
 apps/web/components/menu/MenuPlannerSection.tsx    |     4 +-
 apps/web/components/menu/MenuQuickActionsSheet.tsx |    52 -
 apps/web/components/menu/MenuSectionLayout.tsx     |    29 -
 apps/web/components/menu/MenuSettingsPage.tsx      |    27 +-
 apps/web/components/menu/MenuSubTabs.tsx           |    19 -
 apps/web/components/menu/MenuVariantCard.tsx       |    44 +-
 apps/web/components/menu/ReplaceDishModal.tsx      |    28 +-
 .../components/monetization-2026/AmsHub2026.tsx    |   128 -
 .../HomeMonetizationBanner2026.tsx                 |    45 -
 .../monetization-2026/PaymentStub2026.tsx          |   111 -
 .../monetization-2026/PaywallProvider.tsx          |    61 -
 .../monetization-2026/PaywallSheet2026.tsx         |    94 -
 .../components/monetization-2026/PlanCard2026.tsx  |    79 -
 .../monetization-2026/SubscriptionHub2026.tsx      |   206 -
 .../monetization-2026/SubscriptionOffline2026.tsx  |    83 -
 .../monetization-2026/TrialStatus2026.tsx          |    33 -
 apps/web/components/monetization-2026/index.ts     |     5 -
 .../notifications/NotificationSettingsForm.tsx     |    44 +-
 .../components/notifications/NotificationsView.tsx |    83 -
 .../components/nutrition-profile/NumberInput.tsx   |     6 +-
 .../NutritionGoalDetailsFields.tsx                 |    20 +-
 .../nutrition-profile/NutritionProfileForm.tsx     |   104 +-
 .../nutrition-profile/NutritionSection.tsx         |    14 +-
 .../web/components/nutrition-profile/ToggleRow.tsx |     8 +-
 .../components/nutritionist/HealthTodayView.tsx    |   382 -
 .../nutritionist/NutritionistAdviceCard.tsx        |    20 +-
 .../components/nutritionist/NutritionistChat.tsx   |    24 +-
 .../nutritionist/NutritionistDashboard.tsx         |   572 +-
 .../components/nutritionist/WaterIntakePanel.tsx   |    14 +-
 .../onboarding-2026/Onboarding2026Flow.tsx         |   309 -
 .../onboarding-2026/Onboarding2026Redirect.tsx     |    36 -
 .../onboarding-2026/OnboardingChipGrid2026.tsx     |    91 -
 .../onboarding-2026/OnboardingGenerateStep2026.tsx |    79 -
 .../onboarding-2026/OnboardingProgress2026.tsx     |    26 -
 .../onboarding-2026/OnboardingWowReveal2026.tsx    |    63 -
 .../onboarding-2026/TrialWelcomeCard2026.tsx       |    31 -
 apps/web/components/onboarding-2026/index.ts       |     2 -
 .../components/onboarding/ChipSelectWithCustom.tsx |    99 +
 .../components/onboarding/OnboardingComplete.tsx   |    94 +
 .../web/components/onboarding/OnboardingWizard.tsx |   222 +
 apps/web/components/onboarding/ProgressBar.tsx     |    25 +
 apps/web/components/onboarding/StepContent.tsx     |   111 +
 apps/web/components/onboarding/StepNavigation.tsx  |    50 +
 .../components/pantry/PantryCategorySection.tsx    |     8 +-
 apps/web/components/pantry/PantryDashboard.tsx     |    71 +-
 apps/web/components/pantry/PantryItemCard.tsx      |    22 +-
 apps/web/components/pantry/PantryItemForm.tsx      |    29 +-
 apps/web/components/pantry/PantryItemRow.tsx       |    16 +-
 .../components/plan-2026/DayNutritionCard2026.tsx  |   126 -
 apps/web/components/plan-2026/PlanGenerate2026.tsx |   288 -
 apps/web/components/plan-2026/PlanMealCard2026.tsx |   138 -
 .../plan-2026/PlanTimelineSection2026.tsx          |    46 -
 apps/web/components/plan-2026/PlanToday2026.tsx    |   316 -
 apps/web/components/plan-2026/PlanWeek2026.tsx     |   131 -
 .../components/plan-2026/ReplaceDishSheet2026.tsx  |   188 -
 apps/web/components/plan-2026/index.ts             |     5 -
 .../planam-2026/account/AccountHub2026.tsx         |   110 -
 .../planam-2026/cards/ActionCard2026.tsx           |    80 -
 .../components/planam-2026/cards/HeroCard2026.tsx  |   103 -
 .../planam-2026/cards/InsightCard2026.tsx          |    47 -
 .../planam-2026/cards/MetricCard2026.tsx           |    44 -
 apps/web/components/planam-2026/index.ts           |    15 -
 .../components/planam-2026/layout/AppShell2026.tsx |    26 -
 .../planam-2026/layout/ShellHeader2026.tsx         |    40 -
 .../navigation/BottomNavigation2026.tsx            |    85 -
 .../planam-2026/navigation/NavIcon2026.tsx         |   170 -
 .../planam-2026/navigation/ScreenBack2026.tsx      |    42 -
 .../planam-2026/navigation/SectionSubTabs2026.tsx  |    54 -
 .../navigation/TelegramBackBridge2026.tsx          |    12 -
 .../navigation/useTelegramBackButton2026.ts        |    64 -
 .../planam-2026/screens/RoutePlaceholder2026.tsx   |    25 -
 .../components/planam-2026/theme/ThemeProvider.tsx |   134 -
 .../planam-2026/theme/ThemeToggle2026.tsx          |    50 -
 .../components/planam-2026/ui/BottomSheet2026.tsx  |    62 -
 apps/web/components/planam-2026/ui/Button2026.tsx  |    58 -
 apps/web/components/planam-2026/ui/Card2026.tsx    |    34 -
 .../components/planam-2026/ui/EmptyState2026.tsx   |    46 -
 .../web/components/planam-2026/ui/Skeleton2026.tsx |    30 -
 apps/web/components/profile/ProfileDashboard.tsx   |    44 +-
 apps/web/components/profile/ProfileModeControl.tsx |    18 +-
 apps/web/components/progress/ProgressDashboard.tsx |   116 +-
 apps/web/components/progress/ProgressProLocked.tsx |    25 +-
 .../components/recipes-2026/MenuSlotSheet2026.tsx  |   195 -
 .../components/recipes-2026/RecipeCatalog2026.tsx  |   366 -
 .../components/recipes-2026/RecipeDetail2026.tsx   |   439 -
 .../components/recipes-2026/RecipeGridCard2026.tsx |   112 -
 .../components/recipes-2026/RecipeImage2026.tsx    |    61 -
 apps/web/components/recipes-2026/index.ts          |     4 -
 .../components/recipes/CollectionDetailView.tsx    |   162 -
 apps/web/components/recipes/CollectionsView.tsx    |   169 -
 apps/web/components/recipes/FavoritesView.tsx      |   132 -
 apps/web/components/recipes/FilterChip.tsx         |    25 -
 apps/web/components/recipes/FromPantrySection.tsx  |   158 -
 apps/web/components/recipes/RecipeCard.tsx         |    38 +-
 apps/web/components/recipes/RecipeCatalog.tsx      |   572 +
 .../components/recipes/RecipeCatalogSections.tsx   |    62 +-
 apps/web/components/recipes/RecipeDetailModal.tsx  |   558 +-
 .../components/recipes/RecipeDetailMorePanel.tsx   |   352 -
 apps/web/components/recipes/RecipeFiltersSheet.tsx |   186 -
 apps/web/components/recipes/RecipeListSkeleton.tsx |    23 -
 apps/web/components/recipes/RecipeResultsList.tsx  |    33 -
 apps/web/components/recipes/RecipesView.tsx        |   365 -
 apps/web/components/recipes/ScenarioChips.tsx      |    84 -
 apps/web/components/settings/SettingsScaffold.tsx  |    49 +-
 apps/web/components/shopping/CategoryPicker.tsx    |    30 +-
 .../shopping/ShoppingCategorySection.tsx           |    10 +-
 .../components/shopping/ShoppingCategorySheet.tsx  |    15 +-
 apps/web/components/shopping/ShoppingItemRow.tsx   |    18 +-
 apps/web/components/shopping/ShoppingItemSheet.tsx |    25 +-
 apps/web/components/shopping/ShoppingListView.tsx  |    79 +-
 .../components/shopping/ShoppingSectionLayout.tsx  |    54 -
 apps/web/components/shopping/ShoppingSubTabs.tsx   |    18 -
 .../components/subscription/AmaConfirmDialog.tsx   |    60 +-
 .../subscription/SubscriptionDashboard.tsx         |    82 +-
 apps/web/components/ui/HubTile.tsx                 |   101 -
 apps/web/components/ui/Sheet.tsx                   |    10 +-
 apps/web/components/ui/Skeleton.tsx                |     4 +-
 apps/web/components/ui/ToastProvider.tsx           |    11 +-
 .../components/wellness-2026/WaterIntake2026.tsx   |   121 -
 .../components/wellness-2026/WellnessChat2026.tsx  |   100 -
 .../components/wellness-2026/WellnessChip2026.tsx  |    76 -
 .../wellness-2026/WellnessDayRing2026.tsx          |    39 -
 .../wellness-2026/WellnessGoalCard2026.tsx         |    62 -
 .../components/wellness-2026/WellnessHome2026.tsx  |   274 -
 .../wellness-2026/WellnessInsight2026.tsx          |    34 -
 .../wellness-2026/WellnessTodayCard2026.tsx        |    28 -
 .../wellness-2026/WellnessWeekStrip2026.tsx        |    42 -
 apps/web/components/wellness-2026/index.ts         |     3 -
 apps/web/lib/api-client.ts                         |    25 +-
 apps/web/lib/dom/pantry-sections.ts                |    44 -
 apps/web/lib/dom/shopping-groups.ts                |    49 -
 apps/web/lib/home/home-2026-data.ts                |   181 -
 apps/web/lib/home/planam-hero-2026.test.ts         |   153 -
 apps/web/lib/home/planam-hero-2026.ts              |   233 -
 apps/web/lib/home/redirect-path-2026.ts            |    42 -
 apps/web/lib/home/use-compact-viewport.ts          |    21 -
 apps/web/lib/meal-checkins/api.ts                  |     4 +-
 apps/web/lib/menu/api.ts                           |   167 +-
 apps/web/lib/menu/labels.ts                        |     6 +-
 apps/web/lib/menu/menu-days.ts                     |    33 -
 apps/web/lib/menu/overview-types.ts                |    32 +-
 apps/web/lib/menu/planner-options.ts               |     4 +-
 apps/web/lib/menu/quick-actions.ts                 |    52 -
 apps/web/lib/menu/replace-slot.ts                  |    52 -
 apps/web/lib/menu/types.ts                         |     2 -
 apps/web/lib/monetization/billing-status.ts        |   162 -
 apps/web/lib/monetization/paths.ts                 |    10 -
 apps/web/lib/monetization/paywall.ts               |    82 -
 apps/web/lib/monetization/plan-catalog-2026.ts     |   127 -
 apps/web/lib/monetization/trial-config.ts          |    11 -
 apps/web/lib/navigation/back-navigation-2026.ts    |    74 -
 apps/web/lib/navigation/nav-config-2026.ts         |   356 -
 apps/web/lib/navigation/nav-config.ts              |   124 -
 apps/web/lib/navigation/return-to.ts               |    66 +-
 apps/web/lib/navigation/route-migration-2026.ts    |    61 -
 apps/web/lib/onboarding-2026/config.ts             |   151 -
 apps/web/lib/pantry/api.ts                         |     2 +-
 apps/web/lib/pantry/types.ts                       |     2 +-
 apps/web/lib/plan/add-to-shopping.ts               |    21 -
 apps/web/lib/plan/plan-paths.ts                    |    46 -
 apps/web/lib/plan/plan-today.ts                    |   162 -
 apps/web/lib/planam/cn.ts                          |     6 -
 apps/web/lib/planam/embedded-2026.ts               |    15 -
 apps/web/lib/planam/feature-flags.ts               |    21 -
 apps/web/lib/planam/layout-constants-2026.ts       |     3 -
 apps/web/lib/planam/onboarding-gate.ts             |    34 -
 apps/web/lib/planam/planam-2026-page.ts            |    19 -
 apps/web/lib/planam/routes.ts                      |    91 -
 apps/web/lib/planam/theme-document.ts              |    81 -
 apps/web/lib/planam/theme.ts                       |    52 -
 apps/web/lib/planam/ui-scope.ts                    |    21 -
 apps/web/lib/progress/api.ts                       |     8 -
 apps/web/lib/recipes/analysis-api.ts               |    26 +-
 apps/web/lib/recipes/api.ts                        |    26 -
 apps/web/lib/recipes/catalog-sections.ts           |    11 -
 apps/web/lib/recipes/ingredient-amount.ts          |    36 -
 apps/web/lib/recipes/menu-from-recipe.ts           |    61 -
 apps/web/lib/recipes/nutrition.ts                  |    90 -
 apps/web/lib/recipes/recipe-media.ts               |   102 -
 apps/web/lib/recipes/types.ts                      |    36 -
 apps/web/lib/shopping/categories-v1.ts             |    92 -
 apps/web/lib/shopping/category-suggest.test.ts     |    38 -
 apps/web/lib/shopping/category-suggest.ts          |    71 +-
 apps/web/lib/shopping/labels.ts                    |    31 +-
 apps/web/lib/shopping/types.ts                     |     4 +-
 apps/web/lib/wellness/goal-labels.ts               |    27 -
 apps/web/lib/wellness/home-wellness.ts             |    67 -
 apps/web/lib/wellness/week-strip.ts                |    57 -
 apps/web/lib/wellness/wellness-insight.ts          |    88 -
 apps/web/lib/wellness/wellness-status.ts           |   155 -
 apps/web/middleware.ts                             |    61 -
 apps/web/public/brand/planam-icon.svg              |     5 -
 apps/web/public/brand/planam-mark.svg              |     4 -
 apps/web/public/recipe-images/.gitkeep             |     0
 apps/web/tailwind.config.ts                        |    89 +-
 apps/web/tsconfig.tsbuildinfo                      |     1 -
 backend/data/nutrition_reference_seed.json         |  1105 --
 backend/pytest.ini                                 |     3 -
 backend/scripts/_image_paths.py                    |    85 -
 backend/scripts/analyze_povarenok_dataset.py       |   466 -
 backend/scripts/analyze_recipe_dataset.py          |   340 -
 .../scripts/apply_calculated_nutrition_updates.py  |   466 -
 backend/scripts/apply_nutrition_backfill.py        |   489 -
 backend/scripts/apply_recipe_images.py             |   232 -
 backend/scripts/apply_recipe_steps_updates.py      |   375 -
 backend/scripts/archive_placeholder_recipes.py     |    92 -
 .../scripts/audit_beverage_nutrition_strategy.py   |   395 -
 backend/scripts/audit_menu_nutrition_readiness.py  |   220 -
 backend/scripts/audit_nutrition_update_deltas.py   |   506 -
 backend/scripts/audit_povarenok_jsonl.py           |   365 -
 backend/scripts/audit_project_health.py            |   513 -
 backend/scripts/audit_recipe_catalog.py            |   331 -
 backend/scripts/audit_recipe_duplicates.py         |   230 -
 backend/scripts/audit_recipe_images.py             |   104 -
 .../audit_recipe_ingredient_display_amounts.py     |   209 -
 backend/scripts/audit_recipe_ingredients.py        |   503 -
 backend/scripts/audit_recipe_steps_after_update.py |   141 -
 backend/scripts/audit_recipe_steps_quality.py      |   341 -
 backend/scripts/audit_recipe_steps_v2.py           |   231 -
 backend/scripts/audit_remaining_nutrition_gaps.py  |   470 -
 backend/scripts/audit_weak_steps_remediation.py    |   340 -
 backend/scripts/build_enrichment_batch.py          |   200 -
 backend/scripts/build_holiday_kids_steps_batch.py  |   263 -
 backend/scripts/build_holiday_kids_steps_update.py |   312 -
 backend/scripts/build_planam_v1_catalog.py         |   361 -
 backend/scripts/build_recipe_image_prompts.py      |   118 -
 backend/scripts/build_remaining_weak_groups.py     |   356 -
 backend/scripts/build_simple_beverage_updates.py   |   354 -
 .../scripts/build_steps_update_from_enrichment.py  |   299 -
 .../scripts/build_verified_nutrition_updates.py    |   281 -
 backend/scripts/calculate_nutrition.py             |   275 -
 .../scripts/calculate_recipe_nutrition_preview.py  |   530 -
 .../scripts/calculate_recipe_nutrition_summary.py  |   436 -
 backend/scripts/canonical_products.py              |   426 -
 backend/scripts/convert_enriched_to_import_json.py |   330 -
 .../convert_nutrition_backfill_to_update_json.py   |   231 -
 backend/scripts/convert_povarenok.py               |   425 -
 backend/scripts/evaluate_photo_prompt_readiness.py |   151 -
 .../scripts/export_calculated_nutrition_updates.py |   356 -
 backend/scripts/generate_shopping_list_groups.py   |   174 -
 backend/scripts/import_recipes.py                  |   549 -
 backend/scripts/migrate_to_taste_ingredients.py    |   452 -
 backend/scripts/normalize_ingredient_amounts.py    |   689 -
 backend/scripts/normalize_recipe_ingredients.py    |   573 -
 backend/scripts/nutrition_data.py                  |   353 -
 .../scripts/nutrition_shopping_photo_pipeline.py   |   236 -
 backend/scripts/openai_recipe_image_client.py      |   219 -
 backend/scripts/plan_nutrition_backfill.py         |   357 -
 backend/scripts/plan_recipe_dedup.py               |   215 -
 .../scripts/prepare_povarenok_enrichment_input.py  |   256 -
 backend/scripts/process_recipe_images.py           |   143 -
 backend/scripts/recipe_id_resolver.py              |    60 -
 backend/scripts/recipe_image_utils.py              |   252 -
 backend/scripts/recipe_nutrition_calculator.py     |   211 -
 backend/scripts/repair_recipe_image_assignments.py |   219 -
 backend/scripts/report_recipe_readiness.py         |   221 -
 backend/scripts/resync_recipe_ingredients_jsonb.py |   269 -
 backend/scripts/run_enrichment_pilot.py            |   444 -
 backend/scripts/run_nutrition_backfill.py          |   437 -
 backend/scripts/run_recipe_image_pilot.py          |   295 -
 backend/scripts/run_steps_enrichment.py            |   965 --
 backend/scripts/select_povarenok_candidates.py     |   370 -
 backup_before_import_10.sql                        |   Bin 512178 -> 0 bytes
 backup_before_import_100.sql                       |   Bin 771986 -> 0 bytes
 data/planam_v1_canonical_products.json             |  1487 --
 data/planam_v1_image_pilot_batch.json              |   192 -
 data/planam_v1_nutrition_facts.json                |  1083 --
 data/planam_v1_recipes.json                        | 16189 -------------------
 docker-compose.prod.yml                            |    16 -
 docker-compose.yml                                 |    10 -
 docs/ADMIN_PANEL_INCIDENT_AUDIT.md                 |   569 -
 docs/BETA_HARDENING_REPORT.md                      |   106 -
 docs/BETA_READINESS_AUDIT.md                       |   322 -
 docs/CODEBASE_INDEX.md                             |   930 --
 docs/DOMAIN_ARCHITECTURE.md                        |   697 -
 docs/NAVIGATION_GRAPH.md                           |   517 -
 docs/NAVIGATION_MAP.md                             |    66 -
 docs/PLANAM_2026_COLOR_FIX_REPORT.md               |    83 -
 docs/PLANAM_2026_DECISION_RECORD.md                |    79 -
 docs/PLANAM_2026_FINAL_UX_QA_REPORT.md             |   136 -
 docs/PLANAM_2026_IMPLEMENTATION_ROADMAP.md         |   712 -
 docs/PLANAM_2026_PRODUCT_BLUEPRINT.md              |   757 -
 docs/PLANAM_COLOR_SYSTEM_V1.md                     |    42 -
 docs/PLANAM_CONVERSION_FUNNEL_2026.md              |   316 -
 docs/PLANAM_CURRENT_STATE_ACTIONS.md               |   248 -
 docs/PLANAM_CURRENT_STATE_COMPONENTS.md            |   149 -
 docs/PLANAM_CURRENT_STATE_DATA.md                  |   250 -
 docs/PLANAM_CURRENT_STATE_LAYOUTS.md               |   179 -
 docs/PLANAM_CURRENT_STATE_MASTER.md                |   229 -
 docs/PLANAM_CURRENT_STATE_NAVIGATION.md            |   218 -
 docs/PLANAM_CURRENT_STATE_OVERLAYS.md              |    89 -
 docs/PLANAM_CURRENT_STATE_SCREENS.md               |   337 -
 docs/PLANAM_CURRENT_STATE_USER_FLOWS.md            |   310 -
 docs/PLANAM_DESIGN_SYSTEM_2026.md                  |   769 -
 docs/PLANAM_FINAL_PRODUCT_REVIEW.md                |   402 -
 ...AM_HOTFIX_SHOPPING_CATEGORY_MIGRATION_REPORT.md |   164 -
 docs/PLANAM_LEGACY_DECOMMISSION_AUDIT.md           |   686 -
 docs/PLANAM_LEGACY_REMOVAL_BACKLOG.md              |   115 -
 docs/PLANAM_NAVIGATION_LEGACY_AUDIT.md             |   327 -
 docs/PLANAM_NOTIFICATION_SYSTEM_2026.md            |   289 -
 docs/PLANAM_PAYMENT_ARCHITECTURE_2026.md           |   114 -
 docs/PLANAM_PRODUCTION_UX_POLISH_V1_REPORT.md      |   127 -
 docs/PLANAM_RECIPES_CATALOG_AUDIT_AND_FIX.md       |   111 -
 docs/PLANAM_RECIPE_CATALOG_QUALITY_V1_REPORT.md    |   125 -
 docs/PLANAM_RECIPE_DB_GO_REPORT.md                 |   159 -
 docs/PLANAM_RECIPE_MEDIA_ARCHITECTURE.md           |   265 -
 docs/PLANAM_RECIPE_MENU_INTEGRATION_V1_REPORT.md   |   103 -
 docs/PLANAM_RECIPE_REPLACE_FLOW_V1_REPORT.md       |   106 -
 docs/PLANAM_UX_POLISH_V2_REPORT.md                 |   147 -
 docs/PLANAM_UX_UI_2026_MASTER_SPEC.md              |  1202 --
 docs/PLANAM_V1_AI_JOURNEY.md                       |   163 -
 docs/PLANAM_V1_CANONICAL_PRODUCTS.md               |   154 -
 docs/PLANAM_V1_CLEAN_FOUNDATION_REPORT.md          |   260 -
 docs/PLANAM_V1_DOCUMENTATION_FREEZE_REPORT.md      |   162 -
 docs/PLANAM_V1_FAMILY_MODEL.md                     |   226 -
 docs/PLANAM_V1_FINAL_VISION.md                     |   459 -
 docs/PLANAM_V1_GROWTH_MODEL.md                     |   142 -
 docs/PLANAM_V1_HOME_STATES.md                      |   247 -
 docs/PLANAM_V1_IMAGE_STRATEGY.md                   |   171 -
 docs/PLANAM_V1_INGREDIENT_QUALITY_AUDIT.md         |    90 -
 ...M_V1_INGREDIENT_SAFE_COMMIT_AND_JSONB_RESYNC.md |   146 -
 docs/PLANAM_V1_LIFE_SCENARIOS.md                   |   174 -
 docs/PLANAM_V1_MENU_NUTRITION_AGGREGATION.md       |   150 -
 docs/PLANAM_V1_NUTRITION_SHOPPING_PHOTO.md         |   106 -
 docs/PLANAM_V1_PRODUCT_BACKLOG.md                  |   223 -
 docs/PLANAM_V1_PRODUCT_MASTER.md                   |   257 -
 docs/PLANAM_V1_RECIPE_FOUNDATION_REPORT.md         |   142 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_BUDGET.md           |    88 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_PILOT.md            |    92 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_PROMPTS.md          |   115 -
 docs/PLANAM_V1_RECIPE_IMAGE_PILOT_BUDGET_REPORT.md |    75 -
 docs/PLANAM_V1_RECIPE_IMAGE_PILOT_REPORT.md        |   137 -
 docs/PLANAM_V1_RECIPE_IMAGE_PLAN.md                |    90 -
 docs/PLANAM_V1_RECIPE_IMAGE_STYLE_SYSTEM.md        |   157 -
 docs/PLANAM_V1_RECIPE_IMAGE_TOKEN_SETUP.md         |    88 -
 docs/PLANAM_V1_RECIPE_IMPORT_PIPELINE.md           |   116 -
 docs/PLANAM_V1_RECIPE_NUTRITION_SUMMARY.md         |   127 -
 docs/PLANAM_V1_RECIPE_QUALITY_REPORT.md            |    88 -
 docs/PLANAM_V1_RELEASE_BLUEPRINT.md                |   588 -
 docs/PLANAM_V1_RELEASE_SCREENS.md                  |   167 -
 docs/PLANAM_V1_SHOPPING_MODEL_UPDATE.md            |   177 -
 docs/PLANAM_V1_SPRINT1_5_REPORT.md                 |   178 -
 docs/PLANAM_V1_SPRINT1_DESIGN_REVIEW.md            |   135 -
 docs/PLANAM_V1_SPRINT1_DESIGN_SPEC.md              |   466 -
 docs/PLANAM_V1_SPRINT1_IMPLEMENTATION_REPORT.md    |   148 -
 docs/PLANAM_V1_TO_TASTE_AND_READINESS.md           |   117 -
 docs/PLANAM_V1_TO_V2_STRATEGY.md                   |   143 -
 docs/PLANAM_VISUAL_MOCKUPS_2026.md                 |   564 -
 ...PLANAM_VISUAL_PACKAGE_2026_EXECUTIVE_SUMMARY.md |   199 -
 docs/PRODUCTION_DEPLOY.md                          |    64 -
 docs/RECIPE_ENGINE_ENV.md                          |    35 -
 docs/RECIPE_IMPORT_PIPELINE.md                     |   157 -
 docs/SCREEN_MAP.md                                 |   982 +-
 docs/SECURITY_AUDIT.md                             |   417 -
 docs/SECURITY_FIX_ROADMAP.md                       |   135 -
 docs/SPRINT_0_6_AUDIT.md                           |   378 -
 docs/SPRINT_0_COMPLETION_REPORT.md                 |   300 -
 docs/SPRINT_1_COMPLETION_REPORT.md                 |   194 -
 docs/SPRINT_2_COMPLETION_REPORT.md                 |   221 -
 docs/SPRINT_3_COMPLETION_REPORT.md                 |   185 -
 docs/SPRINT_4_COMPLETION_REPORT.md                 |   190 -
 docs/SPRINT_5_COMPLETION_REPORT.md                 |   241 -
 docs/SPRINT_6_COMPLETION_REPORT.md                 |   187 -
 docs/SPRINT_7_COMPLETION_REPORT.md                 |   216 -
 docs/SPRINT_8_COMPLETION_REPORT.md                 |   190 -
 docs/SPRINT_9_COMPLETION_REPORT.md                 |   167 -
 docs/UI_SYSTEM_AUDIT.md                            |   602 -
 docs/UX_FLOW_MAP.md                                |   537 -
 docs/sql/shopping_categories_find_duplicates.sql   |    46 -
 nav-calls.txt                                      |     0
 pages.txt                                          |   Bin 10254 -> 0 bytes
 project-tree.txt                                   |   Bin 2035782 -> 0 bytes
 reports/dataset_analysis.md                        |   145 -
 reports/planam_cross_branch_audit.md               |    97 -
 reports/planam_project_consolidation_audit.md      |   262 -
 reports/planam_v1_hero_top50.json                  |   302 -
 reports/planam_v1_recipe_image_pilot_results.json  |    22 -
 reports/povarenok_analysis.md                      |   139 -
 reports/povarenok_conversion_report.md             |   141 -
 reports/profile_account_consolidation_audit.md     |   110 -
 reports/ui_2026_consolidation_audit.md             |   113 -
 sample_recipes.json                                |   589 -
 scripts/dedupe_shopping_categories.py              |   116 -
 576 files changed, 5090 insertions(+), 92162 deletions(-)
```

### Unique commits in origin/recipe-engine-v1 not in sprint-0/planam-2026-foundation

*(none — branch has no commits ahead of current)*

## Diff summary: sprint-0/planam-2026-foundation vs origin/recipe-import-pipeline-v1

```
.env.production.example                            |     2 -
 .gitignore                                         |    33 -
 apps/api/app/config.py                             |    13 -
 apps/api/app/database_migrations.py                |    48 +-
 apps/api/app/models/pantry.py                      |     2 +-
 apps/api/app/models/recipe.py                      |    39 -
 apps/api/app/routers/menus.py                      |   138 +-
 apps/api/app/routers/recipes.py                    |    41 +-
 apps/api/app/routers/telegram_bot.py               |    29 +-
 apps/api/app/schemas/menu.py                       |     2 -
 apps/api/app/schemas/menu_nutrition.py             |    75 -
 apps/api/app/schemas/menu_overview.py              |    65 -
 apps/api/app/schemas/pantry.py                     |     4 +-
 apps/api/app/schemas/recipe.py                     |    27 -
 apps/api/app/services/admin_auth.py                |     2 +-
 apps/api/app/services/bot_menu.py                  |     3 +-
 apps/api/app/services/categories_v1.py             |   122 -
 apps/api/app/services/family_member_nutrition.py   |     4 +-
 apps/api/app/services/home_next_action.py          |   132 -
 apps/api/app/services/ingredient_format.py         |   129 -
 apps/api/app/services/meal_attendance.py           |    27 -
 apps/api/app/services/menu_overview.py             |    19 +-
 apps/api/app/services/menu_recipe_plan.py          |   438 -
 apps/api/app/services/normalization/__init__.py    |    47 -
 apps/api/app/services/normalization/amounts.py     |    43 -
 apps/api/app/services/normalization/categories.py  |    55 -
 apps/api/app/services/normalization/ingredients.py |    48 -
 apps/api/app/services/normalization/menu.py        |    23 -
 .../app/services/normalization/notifications.py    |    99 -
 apps/api/app/services/normalization/profile.py     |   121 -
 apps/api/app/services/normalization/shopping.py    |    23 -
 .../api/app/services/normalization/subscription.py |    72 -
 apps/api/app/services/notifications.py             |    24 +-
 apps/api/app/services/nutrition/__init__.py        |     1 -
 apps/api/app/services/nutrition/plan_aggregator.py |   395 -
 apps/api/app/services/nutrition_profile.py         |     3 -
 apps/api/app/services/pantry.py                    |     2 +-
 apps/api/app/services/recipe_storage.py            |    44 +-
 apps/api/app/services/recipes/access.py            |    59 -
 apps/api/app/services/recipes/authoring.py         |    46 +-
 apps/api/app/services/recipes/catalog.py           |    31 +-
 apps/api/app/services/recipes/mapper.py            |    57 +-
 apps/api/app/services/recipes/repository.py        |    11 +-
 apps/api/app/services/recipes/title_normalize.py   |    55 -
 apps/api/app/services/recipes/types.py             |     2 -
 apps/api/app/services/shopping_categories.py       |   239 +-
 .../app/services/shopping_category_migration.py    |   274 -
 apps/api/app/services/shopping_category_service.py |    28 +-
 apps/api/app/services/shopping_item_utils.py       |   202 +-
 apps/api/app/services/shopping_list.py             |    31 +-
 apps/api/app/services/subscription.py              |     4 +-
 apps/api/app/services/subscription_catalog.py      |     8 +-
 apps/api/requirements.txt                          |     1 -
 apps/api/tests/test_categories_v1.py               |    45 -
 apps/api/tests/test_home_next_action.py            |    72 -
 apps/api/tests/test_ingredient_display_amounts.py  |   116 -
 apps/api/tests/test_ingredient_normalization.py    |   230 -
 apps/api/tests/test_menu_nutrition_aggregation.py  |   183 -
 apps/api/tests/test_menu_recipe_plan.py            |   225 -
 apps/api/tests/test_normalization_amounts.py       |    57 -
 apps/api/tests/test_normalization_categories.py    |    46 -
 .../tests/test_normalization_menu_ingredients.py   |    58 -
 .../test_notification_settings_normalization.py    |    59 -
 apps/api/tests/test_nutrition_pipeline.py          |   193 -
 apps/api/tests/test_profile_normalization.py       |    67 -
 apps/api/tests/test_project_health_audit.py        |    96 -
 apps/api/tests/test_recipe_image_resolver.py       |   116 -
 apps/api/tests/test_recipe_ingredient_audit.py     |   100 -
 apps/api/tests/test_recipe_nutrition_summary.py    |   228 -
 apps/api/tests/test_recipe_write_access.py         |   102 -
 apps/api/tests/test_recipes_catalog.py             |    40 -
 apps/api/tests/test_repair_image_files.py          |    59 -
 apps/api/tests/test_shopping_category_migration.py |   200 -
 apps/api/tests/test_shopping_category_service.py   |    86 +-
 apps/api/tests/test_shopping_infer_category.py     |    70 -
 apps/api/tests/test_shopping_list_cleanup.py       |   177 -
 apps/api/tests/test_subscription_normalization.py  |    47 -
 apps/api/tests/test_telegram_webhook_security.py   |    57 -
 apps/api/tests/test_to_taste_migration.py          |   204 -
 apps/web/.env.example                              |     7 -
 apps/web/Dockerfile.prod                           |     2 -
 apps/web/app/account/ams/page.tsx                  |     8 -
 apps/web/app/account/family/page.tsx               |     8 -
 apps/web/app/account/notifications/page.tsx        |     8 -
 apps/web/app/account/nutrition/page.tsx            |    21 -
 apps/web/app/account/page.tsx                      |     8 -
 apps/web/app/account/settings/about/page.tsx       |     1 -
 apps/web/app/account/settings/account/page.tsx     |     1 -
 apps/web/app/account/settings/delete-data/page.tsx |     1 -
 apps/web/app/account/settings/documents/page.tsx   |     1 -
 apps/web/app/account/settings/page.tsx             |    39 -
 apps/web/app/account/settings/support/page.tsx     |     1 -
 .../web/app/account/subscription/checkout/page.tsx |    14 -
 apps/web/app/account/subscription/page.tsx         |    14 -
 apps/web/app/dev/planam-2026/page.tsx              |   150 -
 apps/web/app/family/page.tsx                       |     2 -
 apps/web/app/globals.css                           |   118 +-
 apps/web/app/health/chat/HealthChatPageClient.tsx  |    98 -
 apps/web/app/health/chat/page.tsx                  |    98 +-
 apps/web/app/health/page.tsx                       |     8 +-
 apps/web/app/health/today/page.tsx                 |     7 +-
 apps/web/app/home/page.tsx                         |     9 -
 apps/web/app/home/pantry/page.tsx                  |     8 -
 apps/web/app/home/shopping/page.tsx                |    13 -
 apps/web/app/layout.tsx                            |     4 +-
 apps/web/app/menu/current/page.tsx                 |     7 -
 apps/web/app/menu/generate/page.tsx                |     7 -
 apps/web/app/menu/page.tsx                         |     7 -
 apps/web/app/menu/recipes/page.tsx                 |     5 -
 apps/web/app/notifications/page.tsx                |    48 +-
 apps/web/app/onboarding/page.tsx                   |     7 -
 apps/web/app/page.tsx                              |    12 -
 apps/web/app/plan/generate/page.tsx                |     8 -
 apps/web/app/plan/page.tsx                         |     8 -
 apps/web/app/plan/recipes/[id]/page.tsx            |    17 -
 apps/web/app/plan/recipes/page.tsx                 |     8 -
 apps/web/app/plan/today/page.tsx                   |    14 -
 apps/web/app/profile/nutrition/page.tsx            |     2 -
 apps/web/app/profile/page.tsx                      |     2 -
 apps/web/app/progress/page.tsx                     |     5 -
 apps/web/app/recipes/[id]/RecipeDetailLegacy.tsx   |    85 -
 apps/web/app/recipes/[id]/page.tsx                 |    89 +-
 apps/web/app/recipes/page.tsx                      |     7 +-
 apps/web/app/settings/page.tsx                     |     2 -
 apps/web/app/shopping/leftovers/page.tsx           |     5 -
 apps/web/app/shopping/page.tsx                     |     7 -
 apps/web/app/shopping/pantry/page.tsx              |     6 -
 apps/web/app/subscription/page.tsx                 |     7 -
 apps/web/app/wellness/chat/page.tsx                |     8 -
 apps/web/app/wellness/page.tsx                     |     8 -
 apps/web/components/AppProviders.tsx               |    28 +-
 apps/web/components/TelegramProvider.tsx           |     4 +-
 apps/web/components/auth/AppGate.tsx               |    31 +-
 apps/web/components/dom-2026/Leftovers2026.tsx     |   254 -
 .../web/components/dom-2026/LeftoversSheet2026.tsx |   228 -
 .../components/dom-2026/MealOutcomeSheet2026.tsx   |   235 -
 apps/web/components/dom-2026/Pantry2026.tsx        |   243 -
 apps/web/components/dom-2026/Shopping2026.tsx      |   390 -
 apps/web/components/dom-2026/index.ts              |     5 -
 apps/web/components/family/FamilyDashboard.tsx     |    54 +-
 apps/web/components/home-2026/Home2026.tsx         |   193 -
 .../components/home-2026/MealFallbackPlate2026.tsx |    42 -
 apps/web/components/home-2026/PlanAmHero2026.tsx   |   138 -
 .../components/home-2026/PlanAmStatusRows2026.tsx  |    83 -
 apps/web/components/home-2026/index.ts             |     2 -
 apps/web/components/home/HomeAskPlanAm.tsx         |    57 +
 apps/web/components/home/HomeFamilySummary.tsx     |    66 +
 apps/web/components/home/HomeQuickActions.tsx      |   149 +
 apps/web/components/home/HomeRecommendations.tsx   |   115 +
 apps/web/components/home/HomeShoppingCard.tsx      |    78 +
 apps/web/components/home/HomeTodayCard.tsx         |   124 +
 apps/web/components/layout/AppShell.tsx            |     5 +-
 apps/web/components/layout/AppShellBridge.tsx      |    46 -
 apps/web/components/layout/BottomBackButton.tsx    |    37 +
 apps/web/components/layout/BottomNav.tsx           |     1 +
 apps/web/components/layout/TopBackLink.tsx         |     3 +
 .../components/monetization-2026/AmsHub2026.tsx    |   128 -
 .../HomeMonetizationBanner2026.tsx                 |    45 -
 .../monetization-2026/PaymentStub2026.tsx          |   111 -
 .../monetization-2026/PaywallProvider.tsx          |    61 -
 .../monetization-2026/PaywallSheet2026.tsx         |    94 -
 .../components/monetization-2026/PlanCard2026.tsx  |    79 -
 .../monetization-2026/SubscriptionHub2026.tsx      |   206 -
 .../monetization-2026/SubscriptionOffline2026.tsx  |    83 -
 .../monetization-2026/TrialStatus2026.tsx          |    33 -
 apps/web/components/monetization-2026/index.ts     |     5 -
 .../components/notifications/NotificationsView.tsx |    83 -
 .../nutrition-profile/NutritionProfileForm.tsx     |    62 +-
 .../onboarding-2026/Onboarding2026Flow.tsx         |   309 -
 .../onboarding-2026/Onboarding2026Redirect.tsx     |    36 -
 .../onboarding-2026/OnboardingChipGrid2026.tsx     |    91 -
 .../onboarding-2026/OnboardingGenerateStep2026.tsx |    79 -
 .../onboarding-2026/OnboardingProgress2026.tsx     |    26 -
 .../onboarding-2026/OnboardingWowReveal2026.tsx    |    63 -
 .../onboarding-2026/TrialWelcomeCard2026.tsx       |    31 -
 apps/web/components/onboarding-2026/index.ts       |     2 -
 .../components/onboarding/ChipSelectWithCustom.tsx |    99 +
 .../components/onboarding/OnboardingComplete.tsx   |    94 +
 .../web/components/onboarding/OnboardingWizard.tsx |   222 +
 apps/web/components/onboarding/ProgressBar.tsx     |    25 +
 apps/web/components/onboarding/StepContent.tsx     |   111 +
 apps/web/components/onboarding/StepNavigation.tsx  |    50 +
 apps/web/components/pantry/PantryDashboard.tsx     |     6 +-
 apps/web/components/pantry/PantryItemForm.tsx      |     2 +-
 .../components/plan-2026/DayNutritionCard2026.tsx  |   126 -
 apps/web/components/plan-2026/PlanGenerate2026.tsx |   288 -
 apps/web/components/plan-2026/PlanMealCard2026.tsx |   138 -
 .../plan-2026/PlanTimelineSection2026.tsx          |    46 -
 apps/web/components/plan-2026/PlanToday2026.tsx    |   316 -
 apps/web/components/plan-2026/PlanWeek2026.tsx     |   131 -
 .../components/plan-2026/ReplaceDishSheet2026.tsx  |   188 -
 apps/web/components/plan-2026/index.ts             |     5 -
 .../planam-2026/account/AccountHub2026.tsx         |   110 -
 .../planam-2026/cards/ActionCard2026.tsx           |    80 -
 .../components/planam-2026/cards/HeroCard2026.tsx  |   103 -
 .../planam-2026/cards/InsightCard2026.tsx          |    47 -
 .../planam-2026/cards/MetricCard2026.tsx           |    44 -
 apps/web/components/planam-2026/index.ts           |    15 -
 .../components/planam-2026/layout/AppShell2026.tsx |    26 -
 .../planam-2026/layout/ShellHeader2026.tsx         |    40 -
 .../navigation/BottomNavigation2026.tsx            |    85 -
 .../planam-2026/navigation/NavIcon2026.tsx         |   170 -
 .../planam-2026/navigation/ScreenBack2026.tsx      |    42 -
 .../planam-2026/navigation/SectionSubTabs2026.tsx  |    54 -
 .../navigation/TelegramBackBridge2026.tsx          |    12 -
 .../navigation/useTelegramBackButton2026.ts        |    64 -
 .../planam-2026/screens/RoutePlaceholder2026.tsx   |    25 -
 .../components/planam-2026/theme/ThemeProvider.tsx |   134 -
 .../planam-2026/theme/ThemeToggle2026.tsx          |    50 -
 .../components/planam-2026/ui/BottomSheet2026.tsx  |    62 -
 apps/web/components/planam-2026/ui/Button2026.tsx  |    58 -
 apps/web/components/planam-2026/ui/Card2026.tsx    |    34 -
 .../components/planam-2026/ui/EmptyState2026.tsx   |    46 -
 .../web/components/planam-2026/ui/Skeleton2026.tsx |    30 -
 apps/web/components/progress/ProgressProLocked.tsx |    12 +-
 .../components/recipes-2026/MenuSlotSheet2026.tsx  |   195 -
 .../components/recipes-2026/RecipeCatalog2026.tsx  |   366 -
 .../components/recipes-2026/RecipeDetail2026.tsx   |   439 -
 .../components/recipes-2026/RecipeGridCard2026.tsx |   112 -
 .../components/recipes-2026/RecipeImage2026.tsx    |    61 -
 apps/web/components/recipes-2026/index.ts          |     4 -
 apps/web/components/recipes/RecipeCard.tsx         |    20 -
 apps/web/components/recipes/RecipeDetailModal.tsx  |    56 +-
 .../components/recipes/RecipeDetailMorePanel.tsx   |    32 +-
 apps/web/components/settings/SettingsScaffold.tsx  |    49 +-
 apps/web/components/shopping/CategoryPicker.tsx    |     3 +-
 apps/web/components/shopping/ShoppingItemSheet.tsx |     2 +-
 apps/web/components/shopping/ShoppingListView.tsx  |     4 +-
 .../components/subscription/AmaConfirmDialog.tsx   |    19 +-
 apps/web/components/ui/ToastProvider.tsx           |    11 +-
 .../components/wellness-2026/WaterIntake2026.tsx   |   121 -
 .../components/wellness-2026/WellnessChat2026.tsx  |   100 -
 .../components/wellness-2026/WellnessChip2026.tsx  |    76 -
 .../wellness-2026/WellnessDayRing2026.tsx          |    39 -
 .../wellness-2026/WellnessGoalCard2026.tsx         |    62 -
 .../components/wellness-2026/WellnessHome2026.tsx  |   274 -
 .../wellness-2026/WellnessInsight2026.tsx          |    34 -
 .../wellness-2026/WellnessTodayCard2026.tsx        |    28 -
 .../wellness-2026/WellnessWeekStrip2026.tsx        |    42 -
 apps/web/components/wellness-2026/index.ts         |     3 -
 apps/web/lib/api-client.ts                         |    25 +-
 apps/web/lib/dom/pantry-sections.ts                |    44 -
 apps/web/lib/dom/shopping-groups.ts                |    49 -
 apps/web/lib/home/home-2026-data.ts                |   181 -
 apps/web/lib/home/planam-hero-2026.test.ts         |   153 -
 apps/web/lib/home/planam-hero-2026.ts              |   233 -
 apps/web/lib/home/redirect-path-2026.ts            |    42 -
 apps/web/lib/home/use-compact-viewport.ts          |    21 -
 apps/web/lib/meal-checkins/api.ts                  |     4 +-
 apps/web/lib/menu/api.ts                           |   159 -
 apps/web/lib/menu/overview-types.ts                |    32 +-
 apps/web/lib/menu/replace-slot.ts                  |    52 -
 apps/web/lib/menu/types.ts                         |     2 -
 apps/web/lib/monetization/billing-status.ts        |   162 -
 apps/web/lib/monetization/paths.ts                 |    10 -
 apps/web/lib/monetization/paywall.ts               |    82 -
 apps/web/lib/monetization/plan-catalog-2026.ts     |   127 -
 apps/web/lib/monetization/trial-config.ts          |    11 -
 apps/web/lib/navigation/back-navigation-2026.ts    |    74 -
 apps/web/lib/navigation/nav-config-2026.ts         |   356 -
 apps/web/lib/navigation/return-to.ts               |    62 +-
 apps/web/lib/navigation/route-migration-2026.ts    |    61 -
 apps/web/lib/onboarding-2026/config.ts             |   151 -
 apps/web/lib/pantry/api.ts                         |     2 +-
 apps/web/lib/pantry/types.ts                       |     2 +-
 apps/web/lib/plan/add-to-shopping.ts               |    21 -
 apps/web/lib/plan/plan-paths.ts                    |    46 -
 apps/web/lib/plan/plan-today.ts                    |   162 -
 apps/web/lib/planam/cn.ts                          |     6 -
 apps/web/lib/planam/embedded-2026.ts               |    15 -
 apps/web/lib/planam/feature-flags.ts               |    21 -
 apps/web/lib/planam/layout-constants-2026.ts       |     3 -
 apps/web/lib/planam/onboarding-gate.ts             |    34 -
 apps/web/lib/planam/planam-2026-page.ts            |    19 -
 apps/web/lib/planam/routes.ts                      |    91 -
 apps/web/lib/planam/theme-document.ts              |    81 -
 apps/web/lib/planam/theme.ts                       |    52 -
 apps/web/lib/planam/ui-scope.ts                    |    21 -
 apps/web/lib/progress/api.ts                       |     8 -
 apps/web/lib/recipes/analysis-api.ts               |    26 +-
 apps/web/lib/recipes/api.ts                        |     9 -
 apps/web/lib/recipes/ingredient-amount.ts          |    36 -
 apps/web/lib/recipes/menu-from-recipe.ts           |    61 -
 apps/web/lib/recipes/nutrition.ts                  |    90 -
 apps/web/lib/recipes/recipe-media.ts               |   102 -
 apps/web/lib/recipes/types.ts                      |    36 -
 apps/web/lib/shopping/categories-v1.ts             |    92 -
 apps/web/lib/shopping/category-suggest.test.ts     |    38 -
 apps/web/lib/shopping/category-suggest.ts          |    71 +-
 apps/web/lib/shopping/labels.ts                    |    31 +-
 apps/web/lib/shopping/types.ts                     |     4 +-
 apps/web/lib/wellness/goal-labels.ts               |    27 -
 apps/web/lib/wellness/home-wellness.ts             |    67 -
 apps/web/lib/wellness/week-strip.ts                |    57 -
 apps/web/lib/wellness/wellness-insight.ts          |    88 -
 apps/web/lib/wellness/wellness-status.ts           |   155 -
 apps/web/middleware.ts                             |    61 -
 apps/web/public/recipe-images/.gitkeep             |     0
 apps/web/tailwind.config.ts                        |    45 +-
 apps/web/tsconfig.tsbuildinfo                      |     1 -
 backend/data/nutrition_reference_seed.json         |  1105 --
 backend/pytest.ini                                 |     3 -
 backend/scripts/_image_paths.py                    |    85 -
 .../scripts/apply_calculated_nutrition_updates.py  |   466 -
 backend/scripts/apply_nutrition_backfill.py        |   489 -
 backend/scripts/apply_recipe_images.py             |   232 -
 backend/scripts/apply_recipe_steps_updates.py      |   375 -
 backend/scripts/archive_placeholder_recipes.py     |    92 -
 .../scripts/audit_beverage_nutrition_strategy.py   |   395 -
 backend/scripts/audit_menu_nutrition_readiness.py  |   220 -
 backend/scripts/audit_nutrition_update_deltas.py   |   506 -
 backend/scripts/audit_povarenok_jsonl.py           |   365 -
 backend/scripts/audit_project_health.py            |   513 -
 backend/scripts/audit_recipe_catalog.py            |   331 -
 backend/scripts/audit_recipe_duplicates.py         |   230 -
 backend/scripts/audit_recipe_images.py             |   104 -
 .../audit_recipe_ingredient_display_amounts.py     |   209 -
 backend/scripts/audit_recipe_ingredients.py        |   503 -
 backend/scripts/audit_recipe_steps_after_update.py |   141 -
 backend/scripts/audit_recipe_steps_quality.py      |   341 -
 backend/scripts/audit_recipe_steps_v2.py           |   231 -
 backend/scripts/audit_remaining_nutrition_gaps.py  |   470 -
 backend/scripts/audit_weak_steps_remediation.py    |   340 -
 backend/scripts/build_enrichment_batch.py          |   200 -
 backend/scripts/build_holiday_kids_steps_batch.py  |   263 -
 backend/scripts/build_holiday_kids_steps_update.py |   312 -
 backend/scripts/build_planam_v1_catalog.py         |   361 -
 backend/scripts/build_recipe_image_prompts.py      |   118 -
 backend/scripts/build_remaining_weak_groups.py     |   356 -
 backend/scripts/build_simple_beverage_updates.py   |   354 -
 .../scripts/build_steps_update_from_enrichment.py  |   299 -
 .../scripts/build_verified_nutrition_updates.py    |   281 -
 backend/scripts/calculate_nutrition.py             |   275 -
 .../scripts/calculate_recipe_nutrition_preview.py  |   530 -
 .../scripts/calculate_recipe_nutrition_summary.py  |   436 -
 backend/scripts/canonical_products.py              |   426 -
 backend/scripts/convert_enriched_to_import_json.py |   330 -
 .../convert_nutrition_backfill_to_update_json.py   |   231 -
 backend/scripts/evaluate_photo_prompt_readiness.py |   151 -
 .../scripts/export_calculated_nutrition_updates.py |   356 -
 backend/scripts/generate_shopping_list_groups.py   |   174 -
 backend/scripts/import_recipes.py                  |    43 +-
 backend/scripts/migrate_to_taste_ingredients.py    |   452 -
 backend/scripts/normalize_ingredient_amounts.py    |   689 -
 backend/scripts/normalize_recipe_ingredients.py    |   573 -
 backend/scripts/nutrition_data.py                  |   353 -
 .../scripts/nutrition_shopping_photo_pipeline.py   |   236 -
 backend/scripts/openai_recipe_image_client.py      |   219 -
 backend/scripts/plan_nutrition_backfill.py         |   357 -
 backend/scripts/plan_recipe_dedup.py               |   215 -
 .../scripts/prepare_povarenok_enrichment_input.py  |   256 -
 backend/scripts/process_recipe_images.py           |   143 -
 backend/scripts/recipe_id_resolver.py              |    60 -
 backend/scripts/recipe_image_utils.py              |   252 -
 backend/scripts/recipe_nutrition_calculator.py     |   211 -
 backend/scripts/repair_recipe_image_assignments.py |   219 -
 backend/scripts/report_recipe_readiness.py         |   221 -
 backend/scripts/resync_recipe_ingredients_jsonb.py |   269 -
 backend/scripts/run_enrichment_pilot.py            |   444 -
 backend/scripts/run_nutrition_backfill.py          |   437 -
 backend/scripts/run_recipe_image_pilot.py          |   295 -
 backend/scripts/run_steps_enrichment.py            |   965 --
 backend/scripts/select_povarenok_candidates.py     |   370 -
 backup_before_import_10.sql                        |   Bin 512178 -> 0 bytes
 backup_before_import_100.sql                       |   Bin 771986 -> 0 bytes
 data/planam_v1_canonical_products.json             |  1487 --
 data/planam_v1_image_pilot_batch.json              |   192 -
 data/planam_v1_nutrition_facts.json                |  1083 --
 data/planam_v1_recipes.json                        | 16189 -------------------
 docker-compose.prod.yml                            |    16 -
 docker-compose.yml                                 |    10 -
 docs/ADMIN_PANEL_INCIDENT_AUDIT.md                 |   569 -
 docs/BETA_HARDENING_REPORT.md                      |   106 -
 docs/BETA_READINESS_AUDIT.md                       |   322 -
 docs/CODEBASE_INDEX.md                             |   930 --
 docs/DOMAIN_ARCHITECTURE.md                        |   697 -
 docs/NAVIGATION_GRAPH.md                           |   517 -
 docs/PLANAM_2026_COLOR_FIX_REPORT.md               |    83 -
 docs/PLANAM_2026_DECISION_RECORD.md                |    79 -
 docs/PLANAM_2026_FINAL_UX_QA_REPORT.md             |   136 -
 docs/PLANAM_2026_IMPLEMENTATION_ROADMAP.md         |   712 -
 docs/PLANAM_2026_PRODUCT_BLUEPRINT.md              |   757 -
 docs/PLANAM_COLOR_SYSTEM_V1.md                     |    42 -
 docs/PLANAM_CONVERSION_FUNNEL_2026.md              |   316 -
 docs/PLANAM_CURRENT_STATE_ACTIONS.md               |   248 -
 docs/PLANAM_CURRENT_STATE_COMPONENTS.md            |   149 -
 docs/PLANAM_CURRENT_STATE_DATA.md                  |   250 -
 docs/PLANAM_CURRENT_STATE_LAYOUTS.md               |   179 -
 docs/PLANAM_CURRENT_STATE_MASTER.md                |   229 -
 docs/PLANAM_CURRENT_STATE_NAVIGATION.md            |   218 -
 docs/PLANAM_CURRENT_STATE_OVERLAYS.md              |    89 -
 docs/PLANAM_CURRENT_STATE_SCREENS.md               |   337 -
 docs/PLANAM_CURRENT_STATE_USER_FLOWS.md            |   310 -
 docs/PLANAM_DESIGN_SYSTEM_2026.md                  |   769 -
 docs/PLANAM_FINAL_PRODUCT_REVIEW.md                |   402 -
 ...AM_HOTFIX_SHOPPING_CATEGORY_MIGRATION_REPORT.md |   164 -
 docs/PLANAM_LEGACY_DECOMMISSION_AUDIT.md           |   686 -
 docs/PLANAM_LEGACY_REMOVAL_BACKLOG.md              |   115 -
 docs/PLANAM_NAVIGATION_LEGACY_AUDIT.md             |   327 -
 docs/PLANAM_NOTIFICATION_SYSTEM_2026.md            |   289 -
 docs/PLANAM_PAYMENT_ARCHITECTURE_2026.md           |   114 -
 docs/PLANAM_PRODUCTION_UX_POLISH_V1_REPORT.md      |   127 -
 docs/PLANAM_RECIPES_CATALOG_AUDIT_AND_FIX.md       |   111 -
 docs/PLANAM_RECIPE_CATALOG_QUALITY_V1_REPORT.md    |   125 -
 docs/PLANAM_RECIPE_DB_GO_REPORT.md                 |   159 -
 docs/PLANAM_RECIPE_MEDIA_ARCHITECTURE.md           |   265 -
 docs/PLANAM_RECIPE_MENU_INTEGRATION_V1_REPORT.md   |   103 -
 docs/PLANAM_RECIPE_REPLACE_FLOW_V1_REPORT.md       |   106 -
 docs/PLANAM_UX_POLISH_V2_REPORT.md                 |   147 -
 docs/PLANAM_UX_UI_2026_MASTER_SPEC.md              |  1202 --
 docs/PLANAM_V1_AI_JOURNEY.md                       |   163 -
 docs/PLANAM_V1_CANONICAL_PRODUCTS.md               |   154 -
 docs/PLANAM_V1_CLEAN_FOUNDATION_REPORT.md          |   260 -
 docs/PLANAM_V1_DOCUMENTATION_FREEZE_REPORT.md      |   162 -
 docs/PLANAM_V1_FAMILY_MODEL.md                     |   226 -
 docs/PLANAM_V1_FINAL_VISION.md                     |   459 -
 docs/PLANAM_V1_GROWTH_MODEL.md                     |   142 -
 docs/PLANAM_V1_HOME_STATES.md                      |   247 -
 docs/PLANAM_V1_IMAGE_STRATEGY.md                   |   171 -
 docs/PLANAM_V1_INGREDIENT_QUALITY_AUDIT.md         |    90 -
 ...M_V1_INGREDIENT_SAFE_COMMIT_AND_JSONB_RESYNC.md |   146 -
 docs/PLANAM_V1_LIFE_SCENARIOS.md                   |   174 -
 docs/PLANAM_V1_MENU_NUTRITION_AGGREGATION.md       |   150 -
 docs/PLANAM_V1_NUTRITION_SHOPPING_PHOTO.md         |   106 -
 docs/PLANAM_V1_PRODUCT_BACKLOG.md                  |   223 -
 docs/PLANAM_V1_PRODUCT_MASTER.md                   |   257 -
 docs/PLANAM_V1_RECIPE_FOUNDATION_REPORT.md         |   142 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_BUDGET.md           |    88 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_PILOT.md            |    92 -
 docs/PLANAM_V1_RECIPE_IMAGE_AI_PROMPTS.md          |   115 -
 docs/PLANAM_V1_RECIPE_IMAGE_PILOT_BUDGET_REPORT.md |    75 -
 docs/PLANAM_V1_RECIPE_IMAGE_PILOT_REPORT.md        |   137 -
 docs/PLANAM_V1_RECIPE_IMAGE_PLAN.md                |    90 -
 docs/PLANAM_V1_RECIPE_IMAGE_STYLE_SYSTEM.md        |   157 -
 docs/PLANAM_V1_RECIPE_IMAGE_TOKEN_SETUP.md         |    88 -
 docs/PLANAM_V1_RECIPE_IMPORT_PIPELINE.md           |   116 -
 docs/PLANAM_V1_RECIPE_NUTRITION_SUMMARY.md         |   127 -
 docs/PLANAM_V1_RECIPE_QUALITY_REPORT.md            |    88 -
 docs/PLANAM_V1_RELEASE_BLUEPRINT.md                |   588 -
 docs/PLANAM_V1_RELEASE_SCREENS.md                  |   167 -
 docs/PLANAM_V1_SHOPPING_MODEL_UPDATE.md            |   177 -
 docs/PLANAM_V1_SPRINT1_5_REPORT.md                 |   178 -
 docs/PLANAM_V1_SPRINT1_DESIGN_REVIEW.md            |   135 -
 docs/PLANAM_V1_SPRINT1_DESIGN_SPEC.md              |   466 -
 docs/PLANAM_V1_SPRINT1_IMPLEMENTATION_REPORT.md    |   148 -
 docs/PLANAM_V1_TO_TASTE_AND_READINESS.md           |   117 -
 docs/PLANAM_V1_TO_V2_STRATEGY.md                   |   143 -
 docs/PLANAM_VISUAL_MOCKUPS_2026.md                 |   564 -
 ...PLANAM_VISUAL_PACKAGE_2026_EXECUTIVE_SUMMARY.md |   199 -
 docs/PRODUCTION_DEPLOY.md                          |    64 -
 docs/SCREEN_MAP.md                                 |  1016 +-
 docs/SECURITY_AUDIT.md                             |   417 -
 docs/SECURITY_FIX_ROADMAP.md                       |   135 -
 docs/SPRINT_0_6_AUDIT.md                           |   378 -
 docs/SPRINT_0_COMPLETION_REPORT.md                 |   300 -
 docs/SPRINT_1_COMPLETION_REPORT.md                 |   194 -
 docs/SPRINT_2_COMPLETION_REPORT.md                 |   221 -
 docs/SPRINT_3_COMPLETION_REPORT.md                 |   185 -
 docs/SPRINT_4_COMPLETION_REPORT.md                 |   190 -
 docs/SPRINT_5_COMPLETION_REPORT.md                 |   241 -
 docs/SPRINT_6_COMPLETION_REPORT.md                 |   187 -
 docs/SPRINT_7_COMPLETION_REPORT.md                 |   216 -
 docs/SPRINT_8_COMPLETION_REPORT.md                 |   190 -
 docs/SPRINT_9_COMPLETION_REPORT.md                 |   167 -
 docs/UI_SYSTEM_AUDIT.md                            |   602 -
 docs/UX_FLOW_MAP.md                                |   537 -
 nav-calls.txt                                      |     0
 pages.txt                                          |   Bin 10254 -> 0 bytes
 project-tree.txt                                   |   Bin 2035782 -> 0 bytes
 reports/planam_cross_branch_audit.md               |    97 -
 reports/planam_project_consolidation_audit.md      |   262 -
 reports/planam_v1_hero_top50.json                  |   302 -
 reports/planam_v1_recipe_image_pilot_results.json  |    22 -
 reports/povarenok_conversion_report.md             |    54 +-
 reports/profile_account_consolidation_audit.md     |   110 -
 reports/ui_2026_consolidation_audit.md             |   113 -
 476 files changed, 2737 insertions(+), 83490 deletions(-)
```

### Unique commits in origin/recipe-import-pipeline-v1 not in sprint-0/planam-2026-foundation

*(none — branch has no commits ahead of current)*

## Diff summary: sprint-0/planam-2026-foundation vs origin/sprint-0/planam-2026-foundation

```
.gitignore                                         |   7 -
 apps/api/app/services/family_member_nutrition.py   |   4 +-
 apps/api/app/services/normalization/__init__.py    |  47 --
 apps/api/app/services/normalization/amounts.py     |  43 --
 apps/api/app/services/normalization/categories.py  |  55 ---
 apps/api/app/services/normalization/ingredients.py |  48 --
 apps/api/app/services/normalization/menu.py        |  23 -
 .../app/services/normalization/notifications.py    |  99 ----
 apps/api/app/services/normalization/profile.py     | 121 -----
 apps/api/app/services/normalization/shopping.py    |  23 -
 .../api/app/services/normalization/subscription.py |  72 ---
 apps/api/app/services/notifications.py             |  24 +-
 apps/api/app/services/nutrition_profile.py         |   3 -
 apps/api/tests/test_normalization_amounts.py       |  57 ---
 apps/api/tests/test_normalization_categories.py    |  46 --
 .../tests/test_normalization_menu_ingredients.py   |  58 ---
 .../test_notification_settings_normalization.py    |  59 ---
 apps/api/tests/test_profile_normalization.py       |  67 ---
 apps/api/tests/test_project_health_audit.py        |  96 ----
 apps/api/tests/test_subscription_normalization.py  |  47 --
 apps/web/lib/planam/routes.ts                      |  91 ----
 backend/scripts/audit_project_health.py            | 513 ---------------------
 reports/planam_cross_branch_audit.md               |  97 ----
 reports/planam_project_consolidation_audit.md      | 262 -----------
 reports/profile_account_consolidation_audit.md     | 110 -----
 reports/ui_2026_consolidation_audit.md             | 113 -----
 26 files changed, 7 insertions(+), 2178 deletions(-)
```

### Unique commits in origin/sprint-0/planam-2026-foundation not in sprint-0/planam-2026-foundation

*(none — branch has no commits ahead of current)*

## Important files in origin/main

Total matching paths: **394**

```
apps/api/app/models/__init__.py
apps/api/app/models/admin.py
apps/api/app/models/bot_session.py
apps/api/app/models/care.py
apps/api/app/models/deferred_advice.py
apps/api/app/models/event_plan.py
apps/api/app/models/family.py
apps/api/app/models/family_invite.py
apps/api/app/models/meal_checkin.py
apps/api/app/models/meal_eating_schedule.py
apps/api/app/models/meal_leftover.py
apps/api/app/models/menu_selection.py
apps/api/app/models/notification_settings.py
apps/api/app/models/pantry.py
apps/api/app/models/progress.py
apps/api/app/models/recipe.py
apps/api/app/models/shopping_category.py
apps/api/app/models/shopping_list.py
apps/api/app/models/subscription.py
apps/api/app/models/user.py
apps/api/app/models/user_preferences.py
apps/api/app/models/user_profile.py
apps/api/app/models/water_intake.py
apps/api/app/routers/__init__.py
apps/api/app/routers/admin.py
apps/api/app/routers/auth.py
apps/api/app/routers/care.py
apps/api/app/routers/event_plans.py
apps/api/app/routers/families.py
apps/api/app/routers/legal.py
apps/api/app/routers/meal_checkins.py
apps/api/app/routers/meal_leftovers.py
apps/api/app/routers/menus.py
apps/api/app/routers/notifications.py
apps/api/app/routers/nutrition_profile.py
apps/api/app/routers/nutritionist.py
apps/api/app/routers/onboarding.py
apps/api/app/routers/pantry.py
apps/api/app/routers/progress.py
apps/api/app/routers/recipes.py
apps/api/app/routers/shopping_categories.py
apps/api/app/routers/shopping_lists.py
apps/api/app/routers/subscriptions.py
apps/api/app/routers/telegram_bot.py
apps/api/app/routers/users.py
apps/api/app/schemas/__init__.py
apps/api/app/schemas/admin.py
apps/api/app/schemas/app_context.py
apps/api/app/schemas/auth.py
apps/api/app/schemas/care.py
apps/api/app/schemas/deferred_advice.py
apps/api/app/schemas/event_plan.py
apps/api/app/schemas/family.py
apps/api/app/schemas/family_invite.py
apps/api/app/schemas/family_member_nutrition.py
apps/api/app/schemas/goal_details.py
apps/api/app/schemas/legal.py
apps/api/app/schemas/meal_checkin.py
apps/api/app/schemas/meal_leftover.py
apps/api/app/schemas/menu.py
apps/api/app/schemas/menu_overview.py
apps/api/app/schemas/notifications.py
apps/api/app/schemas/nutrition_profile.py
apps/api/app/schemas/nutritionist.py
apps/api/app/schemas/onboarding.py
apps/api/app/schemas/pantry.py
apps/api/app/schemas/progress.py
apps/api/app/schemas/recipe.py
apps/api/app/schemas/shopping_category.py
apps/api/app/schemas/shopping_list.py
apps/api/app/schemas/subscription.py
apps/api/app/schemas/water_intake.py
apps/api/app/services/__init__.py
apps/api/app/services/admin.py
apps/api/app/services/admin_audit.py
apps/api/app/services/admin_auth.py
apps/api/app/services/admin_bot.py
apps/api/app/services/admin_errors.py
apps/api/app/services/admin_manage.py
apps/api/app/services/ai.py
```
*(… truncated, 314 more)*

## Important files in origin/ux-foundation-v1

Total matching paths: **398**

```
apps/api/app/models/__init__.py
apps/api/app/models/admin.py
apps/api/app/models/bot_session.py
apps/api/app/models/care.py
apps/api/app/models/deferred_advice.py
apps/api/app/models/event_plan.py
apps/api/app/models/family.py
apps/api/app/models/family_invite.py
apps/api/app/models/meal_checkin.py
apps/api/app/models/meal_eating_schedule.py
apps/api/app/models/meal_leftover.py
apps/api/app/models/menu_selection.py
apps/api/app/models/notification_settings.py
apps/api/app/models/pantry.py
apps/api/app/models/progress.py
apps/api/app/models/recipe.py
apps/api/app/models/shopping_category.py
apps/api/app/models/shopping_list.py
apps/api/app/models/subscription.py
apps/api/app/models/user.py
apps/api/app/models/user_preferences.py
apps/api/app/models/user_profile.py
apps/api/app/models/water_intake.py
apps/api/app/routers/__init__.py
apps/api/app/routers/admin.py
apps/api/app/routers/auth.py
apps/api/app/routers/care.py
apps/api/app/routers/event_plans.py
apps/api/app/routers/families.py
apps/api/app/routers/legal.py
apps/api/app/routers/meal_checkins.py
apps/api/app/routers/meal_leftovers.py
apps/api/app/routers/menus.py
apps/api/app/routers/notifications.py
apps/api/app/routers/nutrition_profile.py
apps/api/app/routers/nutritionist.py
apps/api/app/routers/onboarding.py
apps/api/app/routers/pantry.py
apps/api/app/routers/progress.py
apps/api/app/routers/recipes.py
apps/api/app/routers/shopping_categories.py
apps/api/app/routers/shopping_lists.py
apps/api/app/routers/subscriptions.py
apps/api/app/routers/telegram_bot.py
apps/api/app/routers/users.py
apps/api/app/schemas/__init__.py
apps/api/app/schemas/admin.py
apps/api/app/schemas/app_context.py
apps/api/app/schemas/auth.py
apps/api/app/schemas/care.py
apps/api/app/schemas/deferred_advice.py
apps/api/app/schemas/event_plan.py
apps/api/app/schemas/family.py
apps/api/app/schemas/family_invite.py
apps/api/app/schemas/family_member_nutrition.py
apps/api/app/schemas/goal_details.py
apps/api/app/schemas/legal.py
apps/api/app/schemas/meal_checkin.py
apps/api/app/schemas/meal_leftover.py
apps/api/app/schemas/menu.py
apps/api/app/schemas/menu_overview.py
apps/api/app/schemas/notifications.py
apps/api/app/schemas/nutrition_profile.py
apps/api/app/schemas/nutritionist.py
apps/api/app/schemas/onboarding.py
apps/api/app/schemas/pantry.py
apps/api/app/schemas/progress.py
apps/api/app/schemas/recipe.py
apps/api/app/schemas/shopping_category.py
apps/api/app/schemas/shopping_list.py
apps/api/app/schemas/subscription.py
apps/api/app/schemas/water_intake.py
apps/api/app/services/__init__.py
apps/api/app/services/admin.py
apps/api/app/services/admin_audit.py
apps/api/app/services/admin_auth.py
apps/api/app/services/admin_bot.py
apps/api/app/services/admin_errors.py
apps/api/app/services/admin_manage.py
apps/api/app/services/ai.py
```
*(… truncated, 318 more)*

## Important files in origin/release-candidate-ux

Total matching paths: **398**

```
apps/api/app/models/__init__.py
apps/api/app/models/admin.py
apps/api/app/models/bot_session.py
apps/api/app/models/care.py
apps/api/app/models/deferred_advice.py
apps/api/app/models/event_plan.py
apps/api/app/models/family.py
apps/api/app/models/family_invite.py
apps/api/app/models/meal_checkin.py
apps/api/app/models/meal_eating_schedule.py
apps/api/app/models/meal_leftover.py
apps/api/app/models/menu_selection.py
apps/api/app/models/notification_settings.py
apps/api/app/models/pantry.py
apps/api/app/models/progress.py
apps/api/app/models/recipe.py
apps/api/app/models/shopping_category.py
apps/api/app/models/shopping_list.py
apps/api/app/models/subscription.py
apps/api/app/models/user.py
apps/api/app/models/user_preferences.py
apps/api/app/models/user_profile.py
apps/api/app/models/water_intake.py
apps/api/app/routers/__init__.py
apps/api/app/routers/admin.py
apps/api/app/routers/auth.py
apps/api/app/routers/care.py
apps/api/app/routers/event_plans.py
apps/api/app/routers/families.py
apps/api/app/routers/legal.py
apps/api/app/routers/meal_checkins.py
apps/api/app/routers/meal_leftovers.py
apps/api/app/routers/menus.py
apps/api/app/routers/notifications.py
apps/api/app/routers/nutrition_profile.py
apps/api/app/routers/nutritionist.py
apps/api/app/routers/onboarding.py
apps/api/app/routers/pantry.py
apps/api/app/routers/progress.py
apps/api/app/routers/recipes.py
apps/api/app/routers/shopping_categories.py
apps/api/app/routers/shopping_lists.py
apps/api/app/routers/subscriptions.py
apps/api/app/routers/telegram_bot.py
apps/api/app/routers/users.py
apps/api/app/schemas/__init__.py
apps/api/app/schemas/admin.py
apps/api/app/schemas/app_context.py
apps/api/app/schemas/auth.py
apps/api/app/schemas/care.py
apps/api/app/schemas/deferred_advice.py
apps/api/app/schemas/event_plan.py
apps/api/app/schemas/family.py
apps/api/app/schemas/family_invite.py
apps/api/app/schemas/family_member_nutrition.py
apps/api/app/schemas/goal_details.py
apps/api/app/schemas/legal.py
apps/api/app/schemas/meal_checkin.py
apps/api/app/schemas/meal_leftover.py
apps/api/app/schemas/menu.py
apps/api/app/schemas/menu_overview.py
apps/api/app/schemas/notifications.py
apps/api/app/schemas/nutrition_profile.py
apps/api/app/schemas/nutritionist.py
apps/api/app/schemas/onboarding.py
apps/api/app/schemas/pantry.py
apps/api/app/schemas/progress.py
apps/api/app/schemas/recipe.py
apps/api/app/schemas/shopping_category.py
apps/api/app/schemas/shopping_list.py
apps/api/app/schemas/subscription.py
apps/api/app/schemas/water_intake.py
apps/api/app/services/__init__.py
apps/api/app/services/admin.py
apps/api/app/services/admin_audit.py
apps/api/app/services/admin_auth.py
apps/api/app/services/admin_bot.py
apps/api/app/services/admin_errors.py
apps/api/app/services/admin_manage.py
apps/api/app/services/ai.py
```
*(… truncated, 318 more)*

## Important files in origin/recipe-engine-v1

Total matching paths: **426**

```
apps/api/app/models/__init__.py
apps/api/app/models/admin.py
apps/api/app/models/bot_session.py
apps/api/app/models/care.py
apps/api/app/models/deferred_advice.py
apps/api/app/models/event_plan.py
apps/api/app/models/family.py
apps/api/app/models/family_invite.py
apps/api/app/models/meal_checkin.py
apps/api/app/models/meal_eating_schedule.py
apps/api/app/models/meal_leftover.py
apps/api/app/models/menu_selection.py
apps/api/app/models/notification_settings.py
apps/api/app/models/pantry.py
apps/api/app/models/progress.py
apps/api/app/models/recipe.py
apps/api/app/models/recipe_engine.py
apps/api/app/models/shopping_category.py
apps/api/app/models/shopping_list.py
apps/api/app/models/subscription.py
apps/api/app/models/user.py
apps/api/app/models/user_preferences.py
apps/api/app/models/user_profile.py
apps/api/app/models/water_intake.py
apps/api/app/routers/__init__.py
apps/api/app/routers/admin.py
apps/api/app/routers/auth.py
apps/api/app/routers/care.py
apps/api/app/routers/collections.py
apps/api/app/routers/event_plans.py
apps/api/app/routers/families.py
apps/api/app/routers/legal.py
apps/api/app/routers/meal_checkins.py
apps/api/app/routers/meal_leftovers.py
apps/api/app/routers/menus.py
apps/api/app/routers/notifications.py
apps/api/app/routers/nutrition_profile.py
apps/api/app/routers/nutritionist.py
apps/api/app/routers/onboarding.py
apps/api/app/routers/pantry.py
apps/api/app/routers/progress.py
apps/api/app/routers/recipe_engine_common.py
apps/api/app/routers/recipes.py
apps/api/app/routers/shopping_categories.py
apps/api/app/routers/shopping_lists.py
apps/api/app/routers/subscriptions.py
apps/api/app/routers/telegram_bot.py
apps/api/app/routers/users.py
apps/api/app/schemas/__init__.py
apps/api/app/schemas/admin.py
apps/api/app/schemas/app_context.py
apps/api/app/schemas/auth.py
apps/api/app/schemas/care.py
apps/api/app/schemas/deferred_advice.py
apps/api/app/schemas/event_plan.py
apps/api/app/schemas/family.py
apps/api/app/schemas/family_invite.py
apps/api/app/schemas/family_member_nutrition.py
apps/api/app/schemas/goal_details.py
apps/api/app/schemas/legal.py
apps/api/app/schemas/meal_checkin.py
apps/api/app/schemas/meal_leftover.py
apps/api/app/schemas/menu.py
apps/api/app/schemas/menu_overview.py
apps/api/app/schemas/notifications.py
apps/api/app/schemas/nutrition_profile.py
apps/api/app/schemas/nutritionist.py
apps/api/app/schemas/onboarding.py
apps/api/app/schemas/pantry.py
apps/api/app/schemas/progress.py
apps/api/app/schemas/recipe.py
apps/api/app/schemas/recipe_collection.py
apps/api/app/schemas/recipe_engine_api.py
apps/api/app/schemas/recipe_search.py
apps/api/app/schemas/shopping_category.py
apps/api/app/schemas/shopping_list.py
apps/api/app/schemas/subscription.py
apps/api/app/schemas/water_intake.py
apps/api/app/services/__init__.py
apps/api/app/services/admin.py
```
*(… truncated, 346 more)*

## Important files in origin/recipe-import-pipeline-v1

Total matching paths: **476**

```
apps/api/app/models/__init__.py
apps/api/app/models/admin.py
apps/api/app/models/bot_session.py
apps/api/app/models/care.py
apps/api/app/models/deferred_advice.py
apps/api/app/models/event_plan.py
apps/api/app/models/family.py
apps/api/app/models/family_invite.py
apps/api/app/models/meal_checkin.py
apps/api/app/models/meal_eating_schedule.py
apps/api/app/models/meal_leftover.py
apps/api/app/models/menu_selection.py
apps/api/app/models/notification_settings.py
apps/api/app/models/pantry.py
apps/api/app/models/progress.py
apps/api/app/models/recipe.py
apps/api/app/models/recipe_engine.py
apps/api/app/models/shopping_category.py
apps/api/app/models/shopping_list.py
apps/api/app/models/subscription.py
apps/api/app/models/user.py
apps/api/app/models/user_preferences.py
apps/api/app/models/user_profile.py
apps/api/app/models/water_intake.py
apps/api/app/routers/__init__.py
apps/api/app/routers/admin.py
apps/api/app/routers/auth.py
apps/api/app/routers/care.py
apps/api/app/routers/collections.py
apps/api/app/routers/event_plans.py
apps/api/app/routers/families.py
apps/api/app/routers/legal.py
apps/api/app/routers/meal_checkins.py
apps/api/app/routers/meal_leftovers.py
apps/api/app/routers/menus.py
apps/api/app/routers/notifications.py
apps/api/app/routers/nutrition_profile.py
apps/api/app/routers/nutritionist.py
apps/api/app/routers/onboarding.py
apps/api/app/routers/pantry.py
apps/api/app/routers/progress.py
apps/api/app/routers/recipe_engine_common.py
apps/api/app/routers/recipes.py
apps/api/app/routers/shopping_categories.py
apps/api/app/routers/shopping_lists.py
apps/api/app/routers/subscriptions.py
apps/api/app/routers/telegram_bot.py
apps/api/app/routers/users.py
apps/api/app/schemas/__init__.py
apps/api/app/schemas/admin.py
apps/api/app/schemas/app_context.py
apps/api/app/schemas/auth.py
apps/api/app/schemas/care.py
apps/api/app/schemas/deferred_advice.py
apps/api/app/schemas/event_plan.py
apps/api/app/schemas/family.py
apps/api/app/schemas/family_invite.py
apps/api/app/schemas/family_member_nutrition.py
apps/api/app/schemas/goal_details.py
apps/api/app/schemas/legal.py
apps/api/app/schemas/meal_checkin.py
apps/api/app/schemas/meal_leftover.py
apps/api/app/schemas/menu.py
apps/api/app/schemas/menu_overview.py
apps/api/app/schemas/notifications.py
apps/api/app/schemas/nutrition_profile.py
apps/api/app/schemas/nutritionist.py
apps/api/app/schemas/onboarding.py
apps/api/app/schemas/pantry.py
apps/api/app/schemas/progress.py
apps/api/app/schemas/recipe.py
apps/api/app/schemas/recipe_collection.py
apps/api/app/schemas/recipe_engine_api.py
apps/api/app/schemas/recipe_search.py
apps/api/app/schemas/shopping_category.py
apps/api/app/schemas/shopping_list.py
apps/api/app/schemas/subscription.py
apps/api/app/schemas/water_intake.py
apps/api/app/services/__init__.py
apps/api/app/services/admin.py
```
*(… truncated, 396 more)*

## Files only in origin/main compared to sprint-0/planam-2026-foundation

Total paths only in `origin/main`: **11** (of 11 total)

```
apps/api/app/services/recipes.py
apps/web/components/layout/BottomBackButton.tsx
apps/web/components/layout/BottomNav.tsx
apps/web/components/layout/TopBackLink.tsx
apps/web/components/onboarding/ChipSelectWithCustom.tsx
apps/web/components/onboarding/OnboardingComplete.tsx
apps/web/components/onboarding/OnboardingWizard.tsx
apps/web/components/onboarding/ProgressBar.tsx
apps/web/components/onboarding/StepContent.tsx
apps/web/components/onboarding/StepNavigation.tsx
apps/web/components/recipes/RecipeCatalog.tsx
```

## Files only in origin/ux-foundation-v1 compared to sprint-0/planam-2026-foundation

Total paths only in `origin/ux-foundation-v1`: **11** (of 11 total)

```
apps/api/app/services/recipes.py
apps/web/components/layout/BottomBackButton.tsx
apps/web/components/layout/BottomNav.tsx
apps/web/components/layout/TopBackLink.tsx
apps/web/components/onboarding/ChipSelectWithCustom.tsx
apps/web/components/onboarding/OnboardingComplete.tsx
apps/web/components/onboarding/OnboardingWizard.tsx
apps/web/components/onboarding/ProgressBar.tsx
apps/web/components/onboarding/StepContent.tsx
apps/web/components/onboarding/StepNavigation.tsx
apps/web/components/recipes/RecipeCatalog.tsx
```

## Files only in origin/release-candidate-ux compared to sprint-0/planam-2026-foundation

Total paths only in `origin/release-candidate-ux`: **11** (of 11 total)

```
apps/api/app/services/recipes.py
apps/web/components/layout/BottomBackButton.tsx
apps/web/components/layout/BottomNav.tsx
apps/web/components/layout/TopBackLink.tsx
apps/web/components/onboarding/ChipSelectWithCustom.tsx
apps/web/components/onboarding/OnboardingComplete.tsx
apps/web/components/onboarding/OnboardingWizard.tsx
apps/web/components/onboarding/ProgressBar.tsx
apps/web/components/onboarding/StepContent.tsx
apps/web/components/onboarding/StepNavigation.tsx
apps/web/components/recipes/RecipeCatalog.tsx
```

## Files only in origin/recipe-engine-v1 compared to sprint-0/planam-2026-foundation

Total paths only in `origin/recipe-engine-v1`: **10** (of 10 total)

```
apps/web/components/layout/BottomBackButton.tsx
apps/web/components/layout/BottomNav.tsx
apps/web/components/layout/TopBackLink.tsx
apps/web/components/onboarding/ChipSelectWithCustom.tsx
apps/web/components/onboarding/OnboardingComplete.tsx
apps/web/components/onboarding/OnboardingWizard.tsx
apps/web/components/onboarding/ProgressBar.tsx
apps/web/components/onboarding/StepContent.tsx
apps/web/components/onboarding/StepNavigation.tsx
apps/web/components/recipes/RecipeCatalog.tsx
```

## Files only in origin/recipe-import-pipeline-v1 compared to sprint-0/planam-2026-foundation

Total paths only in `origin/recipe-import-pipeline-v1`: **15** (of 15 total)

```
apps/web/components/home/HomeAskPlanAm.tsx
apps/web/components/home/HomeFamilySummary.tsx
apps/web/components/home/HomeQuickActions.tsx
apps/web/components/home/HomeRecommendations.tsx
apps/web/components/home/HomeShoppingCard.tsx
apps/web/components/home/HomeTodayCard.tsx
apps/web/components/layout/BottomBackButton.tsx
apps/web/components/layout/BottomNav.tsx
apps/web/components/layout/TopBackLink.tsx
apps/web/components/onboarding/ChipSelectWithCustom.tsx
apps/web/components/onboarding/OnboardingComplete.tsx
apps/web/components/onboarding/OnboardingWizard.tsx
apps/web/components/onboarding/ProgressBar.tsx
apps/web/components/onboarding/StepContent.tsx
apps/web/components/onboarding/StepNavigation.tsx
```

## Keyword scan in origin/main

Hits (max 300): **300**

```
origin/main:apps/api/app/database.py:36:        shopping_list,
origin/main:apps/api/app/database.py:42:    from app.models import care as care_models  # noqa: F401
origin/main:apps/api/app/database_migrations.py:26:        "ALTER TABLE family_shopping_lists ADD COLUMN IF NOT EXISTS user_id INTEGER",
origin/main:apps/api/app/database_migrations.py:32:                WHERE conname = 'family_shopping_lists_user_id_fkey'
origin/main:apps/api/app/database_migrations.py:34:                ALTER TABLE family_shopping_lists
origin/main:apps/api/app/database_migrations.py:35:                ADD CONSTRAINT family_shopping_lists_user_id_fkey
origin/main:apps/api/app/database_migrations.py:40:        "ALTER TABLE family_shopping_lists ALTER COLUMN family_id DROP NOT NULL",
origin/main:apps/api/app/database_migrations.py:41:        "CREATE UNIQUE INDEX IF NOT EXISTS ix_family_shopping_lists_user_id ON family_shopping_lists (user_id)",
origin/main:apps/api/app/database_migrations.py:76:            invited_phone_normalized VARCHAR(32) NOT NULL,
origin/main:apps/api/app/database_migrations.py:88:        ON family_invites (family_id, invited_phone_normalized)
origin/main:apps/api/app/database_migrations.py:94:        ON family_invites (family_id, invited_phone_normalized)
origin/main:apps/api/app/database_migrations.py:95:        WHERE status = 'pending' AND invited_phone_normalized != '__link__';
origin/main:apps/api/app/database_migrations.py:139:        "ALTER TABLE family_members ADD COLUMN IF NOT EXISTS nutrition_profile JSONB NOT NULL DEFAULT '{}'",
origin/main:apps/api/app/database_migrations.py:214:        # AI Care System (stage 8)
origin/main:apps/api/app/database_migrations.py:216:        CREATE TABLE IF NOT EXISTS care_settings (
origin/main:apps/api/app/database_migrations.py:227:            care_level VARCHAR(16) NOT NULL DEFAULT 'standard',
origin/main:apps/api/app/database_migrations.py:236:        CREATE TABLE IF NOT EXISTS care_notifications (
origin/main:apps/api/app/database_migrations.py:250:        "CREATE INDEX IF NOT EXISTS ix_care_notifications_user_id ON care_notifications (user_id);",
origin/main:apps/api/app/database_migrations.py:252:        CREATE TABLE IF NOT EXISTS care_events (
origin/main:apps/api/app/database_migrations.py:257:            source VARCHAR(64) NOT NULL DEFAULT 'care',
origin/main:apps/api/app/database_migrations.py:262:        "CREATE INDEX IF NOT EXISTS ix_care_events_user_id ON care_events (user_id);",
origin/main:apps/api/app/main.py:17:    care,
origin/main:apps/api/app/main.py:23:    notifications,
origin/main:apps/api/app/main.py:24:    nutrition_profile,
origin/main:apps/api/app/main.py:32:    shopping_lists,
origin/main:apps/api/app/main.py:104:app.include_router(care.router)
origin/main:apps/api/app/main.py:107:app.include_router(nutrition_profile.router)
origin/main:apps/api/app/main.py:113:app.include_router(shopping_lists.router)
origin/main:apps/api/app/main.py:116:app.include_router(notifications.router)
origin/main:apps/api/app/models/__init__.py:2:from app.models.care import CareEvent, CareNotification, CareSettings
origin/main:apps/api/app/models/__init__.py:7:from app.models.notification_settings import UserNotificationSettings
origin/main:apps/api/app/models/__init__.py:11:from app.models.shopping_list import FamilyShoppingList
origin/main:apps/api/app/models/__init__.py:36:    "UserNotificationSettings",
origin/main:apps/api/app/models/__init__.py:45:    "CareSettings",
origin/main:apps/api/app/models/__init__.py:46:    "CareNotification",
origin/main:apps/api/app/models/__init__.py:47:    "CareEvent",
origin/main:apps/api/app/models/care.py:11:class CareSettings(Base):
origin/main:apps/api/app/models/care.py:12:    __tablename__ = "care_settings"
origin/main:apps/api/app/models/care.py:26:    care_level: Mapped[str] = mapped_column(String(16), default="standard")
origin/main:apps/api/app/models/care.py:37:    user = relationship("User", backref="care_settings")
origin/main:apps/api/app/models/care.py:40:class CareNotification(Base):
origin/main:apps/api/app/models/care.py:41:    __tablename__ = "care_notifications"
origin/main:apps/api/app/models/care.py:66:class CareEvent(Base):
origin/main:apps/api/app/models/care.py:67:    __tablename__ = "care_events"
origin/main:apps/api/app/models/care.py:77:    source: Mapped[str] = mapped_column(String(64), default="care")
origin/main:apps/api/app/models/family.py:60:    nutrition_profile: Mapped[dict] = mapped_column(JSONB, default=dict)
origin/main:apps/api/app/models/family_invite.py:24:    invited_phone_normalized: Mapped[str] = mapped_column(String(32), index=True)
origin/main:apps/api/app/models/notification_settings.py:9:class UserNotificationSettings(Base):
origin/main:apps/api/app/models/shopping_list.py:11:    __tablename__ = "family_shopping_lists"
origin/main:apps/api/app/models/user.py:64:        "UserNotificationSettings",
origin/main:apps/api/app/routers/care.py:7:from app.schemas.care import (
origin/main:apps/api/app/routers/care.py:8:    CareNotificationResponse,
origin/main:apps/api/app/routers/care.py:9:    CareSettingsResponse,
origin/main:apps/api/app/routers/care.py:10:    CareSettingsUpdate,
origin/main:apps/api/app/routers/care.py:11:    CareTipsResponse,
origin/main:apps/api/app/routers/care.py:12:    TestCareNotificationRequest,
origin/main:apps/api/app/routers/care.py:13:    TestCareNotificationResponse,
origin/main:apps/api/app/routers/care.py:15:from app.services import care as care_service
origin/main:apps/api/app/routers/care.py:17:router = APIRouter(prefix="/care", tags=["care"])
origin/main:apps/api/app/routers/care.py:20:@router.get("/settings", response_model=CareSettingsResponse)
origin/main:apps/api/app/routers/care.py:21:def get_care_settings(
origin/main:apps/api/app/routers/care.py:24:) -> CareSettingsResponse:
origin/main:apps/api/app/routers/care.py:25:    return care_service.get_care_settings(db, user)
origin/main:apps/api/app/routers/care.py:28:@router.patch("/settings", response_model=CareSettingsResponse)
origin/main:apps/api/app/routers/care.py:29:def patch_care_settings(
origin/main:apps/api/app/routers/care.py:30:    payload: CareSettingsUpdate,
origin/main:apps/api/app/routers/care.py:33:) -> CareSettingsResponse:
origin/main:apps/api/app/routers/care.py:34:    return care_service.update_care_settings(db, user, payload)
origin/main:apps/api/app/routers/care.py:37:@router.get("/notifications", response_model=list[CareNotificationResponse])
origin/main:apps/api/app/routers/care.py:38:def list_care_notifications(
origin/main:apps/api/app/routers/care.py:41:) -> list[CareNotificationResponse]:
origin/main:apps/api/app/routers/care.py:42:    return care_service.list_care_notifications(db, user)
origin/main:apps/api/app/routers/care.py:45:@router.get("/tips", response_model=CareTipsResponse)
origin/main:apps/api/app/routers/care.py:46:def preview_care_tips(
origin/main:apps/api/app/routers/care.py:49:) -> CareTipsResponse:
origin/main:apps/api/app/routers/care.py:50:    ctx = care_service.build_care_context(db, user)
origin/main:apps/api/app/routers/care.py:51:    return CareTipsResponse(tips=care_service.generate_basic_care_tips(db, user, ctx))
origin/main:apps/api/app/routers/care.py:54:@router.post("/test-notification", response_model=TestCareNotificationResponse)
origin/main:apps/api/app/routers/care.py:56:    payload: TestCareNotificationRequest,
origin/main:apps/api/app/routers/care.py:59:) -> TestCareNotificationResponse:
origin/main:apps/api/app/routers/care.py:60:    ok, message, notification = await care_service.send_care_notification_by_type(
origin/main:apps/api/app/routers/care.py:67:    return TestCareNotificationResponse(
origin/main:apps/api/app/routers/event_plans.py:50:def create_event_shopping_list(
origin/main:apps/api/app/routers/families.py:53:        invited_phone_masked=mask_phone(invite.invited_phone_normalized),
origin/main:apps/api/app/routers/families.py:188:            invited_phone_masked=mask_phone(inv.invited_phone_normalized),
origin/main:apps/api/app/routers/menus.py:13:    MenuVariant,
origin/main:apps/api/app/routers/menus.py:25:from app.services import care as care_service
origin/main:apps/api/app/routers/menus.py:32:async def _send_menu_care_notification(user_id: int) -> None:
origin/main:apps/api/app/routers/menus.py:37:            await care_service.maybe_notify_menu_ready(db, user)
origin/main:apps/api/app/routers/menus.py:39:        logger.exception("Menu care notification failed for user %s", user_id)
origin/main:apps/api/app/routers/menus.py:56:@router.post("/replace-dish", response_model=MenuVariant)
origin/main:apps/api/app/routers/menus.py:62:) -> MenuVariant:
origin/main:apps/api/app/routers/menus.py:75:    background_tasks.add_task(_send_menu_care_notification, user.id)
origin/main:apps/api/app/routers/notifications.py:7:from app.schemas.notifications import (
origin/main:apps/api/app/routers/notifications.py:8:    NotificationSettingsResponse,
origin/main:apps/api/app/routers/notifications.py:9:    NotificationSettingsUpdate,
origin/main:apps/api/app/routers/notifications.py:11:from app.services import notifications as notifications_service
origin/main:apps/api/app/routers/notifications.py:13:router = APIRouter(prefix="/notifications", tags=["notifications"])
origin/main:apps/api/app/routers/notifications.py:16:@router.get("/settings", response_model=NotificationSettingsResponse)
origin/main:apps/api/app/routers/notifications.py:20:) -> NotificationSettingsResponse:
origin/main:apps/api/app/routers/notifications.py:21:    return notifications_service.get_settings(db, user)
origin/main:apps/api/app/routers/notifications.py:24:@router.put("/settings", response_model=NotificationSettingsResponse)
origin/main:apps/api/app/routers/notifications.py:26:    payload: NotificationSettingsUpdate,
origin/main:apps/api/app/routers/notifications.py:29:) -> NotificationSettingsResponse:
origin/main:apps/api/app/routers/notifications.py:30:    return notifications_service.update_settings(db, user, payload)
origin/main:apps/api/app/routers/nutrition_profile.py:7:from app.schemas.nutrition_profile import NutritionProfileData, NutritionProfileResponse
origin/main:apps/api/app/routers/nutrition_profile.py:8:from app.services.nutrition_profile import (
origin/main:apps/api/app/routers/nutrition_profile.py:9:    migrate_legacy_profile,
origin/main:apps/api/app/routers/nutrition_profile.py:12:    save_nutrition_profile,
origin/main:apps/api/app/routers/nutrition_profile.py:32:def get_nutrition_profile(
origin/main:apps/api/app/routers/nutrition_profile.py:37:    migrate_legacy_profile(db, profile)
origin/main:apps/api/app/routers/nutrition_profile.py:43:def save_nutrition_profile_endpoint(
origin/main:apps/api/app/routers/nutrition_profile.py:54:    profile = save_nutrition_profile(db, user, payload)
origin/main:apps/api/app/routers/recipes.py:15:from app.schemas.menu import MenuVariant
origin/main:apps/api/app/routers/recipes.py:217:@router.post("/{recipe_id}/add-to-menu", response_model=MenuVariant)
origin/main:apps/api/app/routers/recipes.py:224:) -> MenuVariant:
origin/main:apps/api/app/routers/shopping_lists.py:9:from app.schemas.shopping_list import (
origin/main:apps/api/app/routers/shopping_lists.py:16:from app.services import shopping_list as shopping_list_service
origin/main:apps/api/app/routers/shopping_lists.py:23:def get_my_shopping_list(
origin/main:apps/api/app/routers/shopping_lists.py:28:    result = shopping_list_service.get_shopping_list(db, user, scope)
origin/main:apps/api/app/routers/shopping_lists.py:38:def sync_shopping_list(
origin/main:apps/api/app/routers/shopping_lists.py:42:    return shopping_list_service.sync_shopping_list_for_scope(db, scope)
origin/main:apps/api/app/routers/shopping_lists.py:56:    return shopping_list_service.create_item(db, user, scope, payload)
origin/main:apps/api/app/routers/shopping_lists.py:68:        return shopping_list_service.toggle_item(
origin/main:apps/api/app/routers/shopping_lists.py:76:    return shopping_list_service.update_item(db, user, scope, item_id, payload)
origin/main:apps/api/app/routers/shopping_lists.py:86:    return shopping_list_service.delete_item(db, user, scope, item_id)
origin/main:apps/api/app/routers/shopping_lists.py:97:    return shopping_list_service.toggle_item(
origin/main:apps/api/app/schemas/care.py:6:CareLevel = Literal["minimal", "standard", "active"]
origin/main:apps/api/app/schemas/care.py:7:CareNotificationType = Literal[
origin/main:apps/api/app/schemas/care.py:19:class CareSettingsResponse(BaseModel):
origin/main:apps/api/app/schemas/care.py:28:    care_level: CareLevel
origin/main:apps/api/app/schemas/care.py:36:class CareSettingsUpdate(BaseModel):
origin/main:apps/api/app/schemas/care.py:45:    care_level: CareLevel | None = None
origin/main:apps/api/app/schemas/care.py:51:class CareNotificationResponse(BaseModel):
origin/main:apps/api/app/schemas/care.py:61:class TestCareNotificationRequest(BaseModel):
origin/main:apps/api/app/schemas/care.py:62:    notification_type: CareNotificationType = "water"
origin/main:apps/api/app/schemas/care.py:65:class TestCareNotificationResponse(BaseModel):
origin/main:apps/api/app/schemas/care.py:71:class CareTipPreview(BaseModel):
origin/main:apps/api/app/schemas/care.py:77:class CareTipsResponse(BaseModel):
origin/main:apps/api/app/schemas/care.py:78:    tips: list[CareTipPreview]
origin/main:apps/api/app/schemas/family.py:56:    nutrition_profile_complete: bool = False
origin/main:apps/api/app/schemas/family_member_nutrition.py:5:from app.services.member_age import MAX_AGE_MONTHS, normalize_age_months, validate_age_months
origin/main:apps/api/app/schemas/family_member_nutrition.py:9:    """Stored in family_members.nutrition_profile JSON."""
origin/main:apps/api/app/schemas/family_member_nutrition.py:22:    # Legacy fields (read/write compat)
origin/main:apps/api/app/schemas/family_member_nutrition.py:29:    def migrate_legacy_age(cls, data):
origin/main:apps/api/app/schemas/family_member_nutrition.py:33:            resolved = normalize_age_months(
origin/main:apps/api/app/schemas/menu.py:6:MenuVariantType = Literal["quick", "economy", "balanced"]
origin/main:apps/api/app/schemas/menu.py:26:class MenuIngredient(BaseModel):
origin/main:apps/api/app/schemas/menu.py:32:class MenuVariant(BaseModel):
origin/main:apps/api/app/schemas/menu.py:33:    variant: MenuVariantType
origin/main:apps/api/app/schemas/menu.py:40:    ingredients: list[MenuIngredient] = Field(min_length=1)
origin/main:apps/api/app/schemas/menu.py:46:    menus: list[MenuVariant] = Field(min_length=3, max_length=3)
origin/main:apps/api/app/schemas/menu.py:55:    menu: MenuVariant
origin/main:apps/api/app/schemas/menu.py:80:    menu: MenuVariant
origin/main:apps/api/app/schemas/menu.py:88:    variant: MenuVariantType
origin/main:apps/api/app/schemas/menu.py:89:    menu: MenuVariant
origin/main:apps/api/app/schemas/menu_overview.py:6:from app.schemas.menu import MenuVariant, SelectedMenuResponse
origin/main:apps/api/app/schemas/notifications.py:10:class NotificationSettingsResponse(BaseModel):
origin/main:apps/api/app/schemas/notifications.py:25:class NotificationSettingsUpdate(BaseModel):
origin/main:apps/api/app/schemas/subscription.py:10:    notifications: bool = True
origin/main:apps/api/app/schemas/subscription.py:11:    nutrition_profile: bool = True
origin/main:apps/api/app/schemas/subscription.py:18:    ai_care: bool = False
origin/main:apps/api/app/services/admin_errors.py:1:"""Admin error logging to database (and legacy file fallback)."""
origin/main:apps/api/app/services/ai.py:20:    MenuIngredient,
origin/main:apps/api/app/services/ai.py:22:    MenuVariant,
origin/main:apps/api/app/services/ai.py:23:    MenuVariantType,
origin/main:apps/api/app/services/ai.py:52:MenuVariantKey = Literal["quick", "economy", "balanced"]
origin/main:apps/api/app/services/ai.py:131:    menus: list[MenuVariant]
origin/main:apps/api/app/services/ai.py:204:def _menu_variants_from_ai(data: dict[str, Any]) -> list[MenuVariant]:
origin/main:apps/api/app/services/ai.py:224:    menus: list[MenuVariant] = []
origin/main:apps/api/app/services/ai.py:260:                MenuVariant(
origin/main:apps/api/app/services/ai.py:273:                        MenuIngredient(name="Вода", amount="1 л", category="drinks")
origin/main:apps/api/app/services/ai.py:343:def _ingredients_from_ai_rows(rows: list[dict]) -> list[MenuIngredient]:
origin/main:apps/api/app/services/ai.py:364:        MenuIngredient(
origin/main:apps/api/app/services/amount_parser.py:29:def normalize_unit(raw: str) -> str:
origin/main:apps/api/app/services/amount_parser.py:47:        return None, normalize_unit(text)
origin/main:apps/api/app/services/amount_parser.py:53:        return None, normalize_unit(text)
origin/main:apps/api/app/services/amount_parser.py:55:    unit = normalize_unit(unit_raw) if unit_raw else "шт"
origin/main:apps/api/app/services/bot_input.py:14:from app.schemas.shopping_list import ShoppingItemCreateRequest, ShoppingItemUpdateRequest
origin/main:apps/api/app/services/bot_input.py:16:from app.services import shopping_list as shopping_service
origin/main:apps/api/app/services/bot_input.py:62:def _normalize_match(name: str) -> str:
origin/main:apps/api/app/services/bot_input.py:169:    listing = shopping_service.get_shopping_list(db, user, scope)
origin/main:apps/api/app/services/bot_input.py:170:    key = _normalize_match(name)
origin/main:apps/api/app/services/bot_input.py:172:        if _normalize_match(item.name) == key and not item.checked:
origin/main:apps/api/app/services/bot_today.py:10:from app.services import shopping_list as shopping_service
origin/main:apps/api/app/services/bot_today.py:22:    shopping = shopping_service.get_shopping_list(db, user, scope)
origin/main:apps/api/app/services/care.py:13:from app.models.care import CareEvent, CareNotification, CareSettings
origin/main:apps/api/app/services/care.py:15:from app.schemas.care import (
origin/main:apps/api/app/services/care.py:16:    CareNotificationResponse,
origin/main:apps/api/app/services/care.py:17:    CareSettingsResponse,
origin/main:apps/api/app/services/care.py:18:    CareSettingsUpdate,
origin/main:apps/api/app/services/care.py:19:    CareTipPreview,
origin/main:apps/api/app/services/care.py:24:from app.services.notifications import get_or_create_settings as get_notif_settings_row
origin/main:apps/api/app/services/care.py:27:from app.services import shopping_list as shopping_list_service
origin/main:apps/api/app/services/care.py:32:CareLevel = str
origin/main:apps/api/app/services/care.py:40:COOLDOWN_HOURS: dict[str, dict[CareLevel, int]] = {
origin/main:apps/api/app/services/care.py:51:CARE_TEMPLATES: dict[str, dict[str, str]] = {
origin/main:apps/api/app/services/care.py:104:class CareContext:
origin/main:apps/api/app/services/care.py:116:def _user_timezone(settings_row: CareSettings, user: User, db: Session) -> str:
origin/main:apps/api/app/services/care.py:130:def _is_quiet_hours(settings_row: CareSettings, user: User, db: Session) -> bool:
origin/main:apps/api/app/services/care.py:148:        return bool(features.get("ai_care"))
origin/main:apps/api/app/services/care.py:153:def get_or_create_care_settings(db: Session, user: User) -> CareSettings:
origin/main:apps/api/app/services/care.py:155:        db.query(CareSettings).filter(CareSettings.user_id == user.id).one_or_none()
origin/main:apps/api/app/services/care.py:159:        row = CareSettings(
origin/main:apps/api/app/services/care.py:165:            care_level="standard",
origin/main:apps/api/app/services/care.py:174:    row: CareSettings, *, has_pro: bool
origin/main:apps/api/app/services/care.py:175:) -> CareSettingsResponse:
origin/main:apps/api/app/services/care.py:176:    return CareSettingsResponse(
origin/main:apps/api/app/services/care.py:185:        care_level=row.care_level,  # type: ignore[arg-type]
origin/main:apps/api/app/services/care.py:194:def get_care_settings(db: Session, user: User) -> CareSettingsResponse:
origin/main:apps/api/app/services/care.py:195:    row = get_or_create_care_settings(db, user)
origin/main:apps/api/app/services/care.py:199:def update_care_settings(
origin/main:apps/api/app/services/care.py:200:    db: Session, user: User, payload: CareSettingsUpdate
origin/main:apps/api/app/services/care.py:201:) -> CareSettingsResponse:
origin/main:apps/api/app/services/care.py:202:    row = get_or_create_care_settings(db, user)
origin/main:apps/api/app/services/care.py:204:    previous_level = row.care_level
origin/main:apps/api/app/services/care.py:208:    if data.get("care_level") == "minimal" and previous_level != "minimal":
origin/main:apps/api/app/services/care.py:224:def list_care_notifications(
origin/main:apps/api/app/services/care.py:226:) -> list[CareNotificationResponse]:
origin/main:apps/api/app/services/care.py:228:        db.query(CareNotification)
origin/main:apps/api/app/services/care.py:229:        .filter(CareNotification.user_id == user.id)
origin/main:apps/api/app/services/care.py:230:        .order_by(desc(CareNotification.created_at))
origin/main:apps/api/app/services/care.py:235:        CareNotificationResponse(
origin/main:apps/api/app/services/care.py:248:def _type_enabled(settings_row: CareSettings, notification_type: str) -> bool:
origin/main:apps/api/app/services/care.py:261:def _level_allows_type(care_level: str, notification_type: str) -> bool:
origin/main:apps/api/app/services/care.py:262:    if care_level == "minimal":
origin/main:apps/api/app/services/care.py:264:    if care_level == "standard":
origin/main:apps/api/app/services/care.py:269:def _cooldown_hours(care_level: str, notification_type: str) -> int:
origin/main:apps/api/app/services/care.py:271:    return by_type.get(care_level, 24)
origin/main:apps/api/app/services/care.py:278:        db.query(CareNotification)
origin/main:apps/api/app/services/care.py:280:            CareNotification.user_id == user_id,
origin/main:apps/api/app/services/care.py:281:            CareNotification.type == notification_type,
origin/main:apps/api/app/services/care.py:282:            CareNotification.status == "sent",
origin/main:apps/api/app/services/care.py:284:        .order_by(desc(CareNotification.sent_at))
origin/main:apps/api/app/services/care.py:298:    settings_row = get_or_create_care_settings(db, user)
origin/main:apps/api/app/services/care.py:302:    if not _level_allows_type(settings_row.care_level, notification_type):
origin/main:apps/api/app/services/care.py:312:            hours = _cooldown_hours(settings_row.care_level, notification_type)
origin/main:apps/api/app/services/care.py:319:def create_care_notification(
origin/main:apps/api/app/services/care.py:329:) -> CareNotification:
origin/main:apps/api/app/services/care.py:330:    template = CARE_TEMPLATES.get(notification_type, CARE_TEMPLATES["water"])
origin/main:apps/api/app/services/care.py:331:    row = CareNotification(
origin/main:apps/api/app/services/care.py:347:def log_care_event(
origin/main:apps/api/app/services/care.py:352:    source: str = "care",
origin/main:apps/api/app/services/care.py:355:) -> CareEvent:
origin/main:apps/api/app/services/care.py:356:    event = CareEvent(
origin/main:apps/api/app/services/care.py:369:async def send_telegram_care_notification(
origin/main:apps/api/app/services/care.py:371:    notification: CareNotification,
origin/main:apps/api/app/services/care.py:377:        logger.info("Care notification skipped: no telegram_id for user %s", user.id)
origin/main:apps/api/app/services/care.py:380:    template = CARE_TEMPLATES.get(notification.type, {})
origin/main:apps/api/app/services/care.py:400:    log_care_event(
origin/main:apps/api/app/services/care.py:403:        f"care_{notification.type}_{'sent' if sent else 'failed'}",
origin/main:apps/api/app/services/care.py:409:def build_care_context(db: Session, user: User) -> CareContext:
origin/main:apps/api/app/services/care.py:412:    shopping = shopping_list_service.get_shopping_list(db, user, scope)
origin/main:apps/api/app/services/care.py:428:    return CareContext(
origin/main:apps/api/app/services/care.py:441:def generate_basic_care_tips(
origin/main:apps/api/app/services/care.py:442:    db: Session, user: User, context: CareContext | None = None
origin/main:apps/api/app/services/care.py:443:) -> list[CareTipPreview]:
origin/main:apps/api/app/services/care.py:444:    ctx = context or build_care_context(db, user)
origin/main:apps/api/app/services/care.py:445:    tips: list[CareTipPreview] = []
origin/main:apps/api/app/services/care.py:448:        t = CARE_TEMPLATES["shopping"]
origin/main:apps/api/app/services/care.py:450:            CareTipPreview(type="shopping", title=t["title"], message=t["message"])
origin/main:apps/api/app/services/care.py:453:        t = CARE_TEMPLATES["pantry"]
origin/main:apps/api/app/services/care.py:460:        tips.append(CareTipPreview(type="pantry", title=t["title"], message=msg))
origin/main:apps/api/app/services/care.py:462:        t = CARE_TEMPLATES["menu"]
origin/main:apps/api/app/services/care.py:463:        tips.append(CareTipPreview(type="menu", title=t["title"], message=t["message"]))
origin/main:apps/api/app/services/care.py:465:        t = CARE_TEMPLATES["protein"]
origin/main:apps/api/app/services/care.py:467:            CareTipPreview(type="protein", title=t["title"], message=t["message"])
origin/main:apps/api/app/services/care.py:469:    t = CARE_TEMPLATES["water"]
origin/main:apps/api/app/services/care.py:470:    tips.append(CareTipPreview(type="water", title=t["title"], message=t["message"]))
origin/main:apps/api/app/services/care.py:472:        t = CARE_TEMPLATES["family"]
origin/main:apps/api/app/services/care.py:473:        tips.append(CareTipPreview(type="family", title=t["title"], message=t["message"]))
origin/main:apps/api/app/services/care.py:475:        t = CARE_TEMPLATES["pro"]
origin/main:apps/api/app/services/care.py:476:        tips.append(CareTipPreview(type="pro", title=t["title"], message=t["message"]))
origin/main:apps/api/app/services/care.py:481:async def send_care_notification_by_type(
origin/main:apps/api/app/services/care.py:489:) -> tuple[bool, str, CareNotification | None]:
origin/main:apps/api/app/services/care.py:499:    template = CARE_TEMPLATES[notification_type]
origin/main:apps/api/app/services/care.py:500:    notification = create_care_notification(
origin/main:apps/api/app/services/care.py:510:    sent = await send_telegram_care_notification(db, notification, user)
origin/main:apps/api/app/services/care.py:527:    ctx = build_care_context(db, user)
origin/main:apps/api/app/services/care.py:530:    await send_care_notification_by_type(db, user, "menu")
origin/main:apps/api/app/services/care.py:533:async def process_care_reminders_for_user(db: Session, user: User) -> None:
origin/main:apps/api/app/services/care.py:534:    """Send at most one contextual care tip per scheduler tick."""
origin/main:apps/api/app/services/care.py:535:    settings_row = get_or_create_care_settings(db, user)
origin/main:apps/api/app/services/care.py:536:    if settings_row.care_level == "minimal" and not any(
origin/main:apps/api/app/services/care.py:545:    ctx = build_care_context(db, user)
origin/main:apps/api/app/services/care.py:546:    tips = generate_basic_care_tips(db, user, ctx)
origin/main:apps/api/app/services/care.py:550:            await send_care_notification_by_type(db, user, tip.type)
origin/main:apps/api/app/services/care.py:554:async def process_all_care_reminders(db: Session) -> None:
origin/main:apps/api/app/services/care.py:560:            await process_care_reminders_for_user(db, user)
origin/main:apps/api/app/services/care.py:562:            logger.exception("Care reminder failed for user %s", user.id)
origin/main:apps/api/app/services/event_plan.py:19:from app.schemas.menu import MenuIngredient
origin/main:apps/api/app/services/event_plan.py:27:from app.services import shopping_list as shopping_list_service
origin/main:apps/api/app/services/event_plan.py:194:    from app.schemas.menu import MenuVariant
origin/main:apps/api/app/services/event_plan.py:197:        MenuIngredient(
origin/main:apps/api/app/services/event_plan.py:205:    menu = MenuVariant(
origin/main:apps/api/app/services/event_plan.py:213:    shopping_list_service.sync_from_menu(db, scope, menu, None)
origin/main:apps/api/app/services/family.py:21:from app.schemas.nutrition_profile import NutritionProfileData, NutritionProData
origin/main:apps/api/app/services/family.py:23:from app.services.nutrition_profile import save_nutrition_profile
origin/main:apps/api/app/services/family.py:99:        nutrition_profile_complete=complete,
origin/main:apps/api/app/services/family.py:226:        invited_phone_masked=mask_phone(invite.invited_phone_normalized),
```

## Keyword scan in origin/ux-foundation-v1

Hits (max 300): **300**

```
origin/ux-foundation-v1:apps/api/app/database.py:36:        shopping_list,
origin/ux-foundation-v1:apps/api/app/database.py:42:    from app.models import care as care_models  # noqa: F401
origin/ux-foundation-v1:apps/api/app/database_migrations.py:26:        "ALTER TABLE family_shopping_lists ADD COLUMN IF NOT EXISTS user_id INTEGER",
origin/ux-foundation-v1:apps/api/app/database_migrations.py:32:                WHERE conname = 'family_shopping_lists_user_id_fkey'
origin/ux-foundation-v1:apps/api/app/database_migrations.py:34:                ALTER TABLE family_shopping_lists
origin/ux-foundation-v1:apps/api/app/database_migrations.py:35:                ADD CONSTRAINT family_shopping_lists_user_id_fkey
origin/ux-foundation-v1:apps/api/app/database_migrations.py:40:        "ALTER TABLE family_shopping_lists ALTER COLUMN family_id DROP NOT NULL",
origin/ux-foundation-v1:apps/api/app/database_migrations.py:41:        "CREATE UNIQUE INDEX IF NOT EXISTS ix_family_shopping_lists_user_id ON family_shopping_lists (user_id)",
origin/ux-foundation-v1:apps/api/app/database_migrations.py:76:            invited_phone_normalized VARCHAR(32) NOT NULL,
origin/ux-foundation-v1:apps/api/app/database_migrations.py:88:        ON family_invites (family_id, invited_phone_normalized)
origin/ux-foundation-v1:apps/api/app/database_migrations.py:94:        ON family_invites (family_id, invited_phone_normalized)
origin/ux-foundation-v1:apps/api/app/database_migrations.py:95:        WHERE status = 'pending' AND invited_phone_normalized != '__link__';
origin/ux-foundation-v1:apps/api/app/database_migrations.py:139:        "ALTER TABLE family_members ADD COLUMN IF NOT EXISTS nutrition_profile JSONB NOT NULL DEFAULT '{}'",
origin/ux-foundation-v1:apps/api/app/database_migrations.py:214:        # AI Care System (stage 8)
origin/ux-foundation-v1:apps/api/app/database_migrations.py:216:        CREATE TABLE IF NOT EXISTS care_settings (
origin/ux-foundation-v1:apps/api/app/database_migrations.py:227:            care_level VARCHAR(16) NOT NULL DEFAULT 'standard',
origin/ux-foundation-v1:apps/api/app/database_migrations.py:236:        CREATE TABLE IF NOT EXISTS care_notifications (
origin/ux-foundation-v1:apps/api/app/database_migrations.py:250:        "CREATE INDEX IF NOT EXISTS ix_care_notifications_user_id ON care_notifications (user_id);",
origin/ux-foundation-v1:apps/api/app/database_migrations.py:252:        CREATE TABLE IF NOT EXISTS care_events (
origin/ux-foundation-v1:apps/api/app/database_migrations.py:257:            source VARCHAR(64) NOT NULL DEFAULT 'care',
origin/ux-foundation-v1:apps/api/app/database_migrations.py:262:        "CREATE INDEX IF NOT EXISTS ix_care_events_user_id ON care_events (user_id);",
origin/ux-foundation-v1:apps/api/app/main.py:17:    care,
origin/ux-foundation-v1:apps/api/app/main.py:23:    notifications,
origin/ux-foundation-v1:apps/api/app/main.py:24:    nutrition_profile,
origin/ux-foundation-v1:apps/api/app/main.py:32:    shopping_lists,
origin/ux-foundation-v1:apps/api/app/main.py:104:app.include_router(care.router)
origin/ux-foundation-v1:apps/api/app/main.py:107:app.include_router(nutrition_profile.router)
origin/ux-foundation-v1:apps/api/app/main.py:113:app.include_router(shopping_lists.router)
origin/ux-foundation-v1:apps/api/app/main.py:116:app.include_router(notifications.router)
origin/ux-foundation-v1:apps/api/app/models/__init__.py:2:from app.models.care import CareEvent, CareNotification, CareSettings
origin/ux-foundation-v1:apps/api/app/models/__init__.py:7:from app.models.notification_settings import UserNotificationSettings
origin/ux-foundation-v1:apps/api/app/models/__init__.py:11:from app.models.shopping_list import FamilyShoppingList
origin/ux-foundation-v1:apps/api/app/models/__init__.py:36:    "UserNotificationSettings",
origin/ux-foundation-v1:apps/api/app/models/__init__.py:45:    "CareSettings",
origin/ux-foundation-v1:apps/api/app/models/__init__.py:46:    "CareNotification",
origin/ux-foundation-v1:apps/api/app/models/__init__.py:47:    "CareEvent",
origin/ux-foundation-v1:apps/api/app/models/care.py:11:class CareSettings(Base):
origin/ux-foundation-v1:apps/api/app/models/care.py:12:    __tablename__ = "care_settings"
origin/ux-foundation-v1:apps/api/app/models/care.py:26:    care_level: Mapped[str] = mapped_column(String(16), default="standard")
origin/ux-foundation-v1:apps/api/app/models/care.py:37:    user = relationship("User", backref="care_settings")
origin/ux-foundation-v1:apps/api/app/models/care.py:40:class CareNotification(Base):
origin/ux-foundation-v1:apps/api/app/models/care.py:41:    __tablename__ = "care_notifications"
origin/ux-foundation-v1:apps/api/app/models/care.py:66:class CareEvent(Base):
origin/ux-foundation-v1:apps/api/app/models/care.py:67:    __tablename__ = "care_events"
origin/ux-foundation-v1:apps/api/app/models/care.py:77:    source: Mapped[str] = mapped_column(String(64), default="care")
origin/ux-foundation-v1:apps/api/app/models/family.py:60:    nutrition_profile: Mapped[dict] = mapped_column(JSONB, default=dict)
origin/ux-foundation-v1:apps/api/app/models/family_invite.py:24:    invited_phone_normalized: Mapped[str] = mapped_column(String(32), index=True)
origin/ux-foundation-v1:apps/api/app/models/notification_settings.py:9:class UserNotificationSettings(Base):
origin/ux-foundation-v1:apps/api/app/models/shopping_list.py:11:    __tablename__ = "family_shopping_lists"
origin/ux-foundation-v1:apps/api/app/models/user.py:64:        "UserNotificationSettings",
origin/ux-foundation-v1:apps/api/app/routers/care.py:7:from app.schemas.care import (
origin/ux-foundation-v1:apps/api/app/routers/care.py:8:    CareNotificationResponse,
origin/ux-foundation-v1:apps/api/app/routers/care.py:9:    CareSettingsResponse,
origin/ux-foundation-v1:apps/api/app/routers/care.py:10:    CareSettingsUpdate,
origin/ux-foundation-v1:apps/api/app/routers/care.py:11:    CareTipsResponse,
origin/ux-foundation-v1:apps/api/app/routers/care.py:12:    TestCareNotificationRequest,
origin/ux-foundation-v1:apps/api/app/routers/care.py:13:    TestCareNotificationResponse,
origin/ux-foundation-v1:apps/api/app/routers/care.py:15:from app.services import care as care_service
origin/ux-foundation-v1:apps/api/app/routers/care.py:17:router = APIRouter(prefix="/care", tags=["care"])
origin/ux-foundation-v1:apps/api/app/routers/care.py:20:@router.get("/settings", response_model=CareSettingsResponse)
origin/ux-foundation-v1:apps/api/app/routers/care.py:21:def get_care_settings(
origin/ux-foundation-v1:apps/api/app/routers/care.py:24:) -> CareSettingsResponse:
origin/ux-foundation-v1:apps/api/app/routers/care.py:25:    return care_service.get_care_settings(db, user)
origin/ux-foundation-v1:apps/api/app/routers/care.py:28:@router.patch("/settings", response_model=CareSettingsResponse)
origin/ux-foundation-v1:apps/api/app/routers/care.py:29:def patch_care_settings(
origin/ux-foundation-v1:apps/api/app/routers/care.py:30:    payload: CareSettingsUpdate,
origin/ux-foundation-v1:apps/api/app/routers/care.py:33:) -> CareSettingsResponse:
origin/ux-foundation-v1:apps/api/app/routers/care.py:34:    return care_service.update_care_settings(db, user, payload)
origin/ux-foundation-v1:apps/api/app/routers/care.py:37:@router.get("/notifications", response_model=list[CareNotificationResponse])
origin/ux-foundation-v1:apps/api/app/routers/care.py:38:def list_care_notifications(
origin/ux-foundation-v1:apps/api/app/routers/care.py:41:) -> list[CareNotificationResponse]:
origin/ux-foundation-v1:apps/api/app/routers/care.py:42:    return care_service.list_care_notifications(db, user)
origin/ux-foundation-v1:apps/api/app/routers/care.py:45:@router.get("/tips", response_model=CareTipsResponse)
origin/ux-foundation-v1:apps/api/app/routers/care.py:46:def preview_care_tips(
origin/ux-foundation-v1:apps/api/app/routers/care.py:49:) -> CareTipsResponse:
origin/ux-foundation-v1:apps/api/app/routers/care.py:50:    ctx = care_service.build_care_context(db, user)
origin/ux-foundation-v1:apps/api/app/routers/care.py:51:    return CareTipsResponse(tips=care_service.generate_basic_care_tips(db, user, ctx))
origin/ux-foundation-v1:apps/api/app/routers/care.py:54:@router.post("/test-notification", response_model=TestCareNotificationResponse)
origin/ux-foundation-v1:apps/api/app/routers/care.py:56:    payload: TestCareNotificationRequest,
origin/ux-foundation-v1:apps/api/app/routers/care.py:59:) -> TestCareNotificationResponse:
origin/ux-foundation-v1:apps/api/app/routers/care.py:60:    ok, message, notification = await care_service.send_care_notification_by_type(
origin/ux-foundation-v1:apps/api/app/routers/care.py:67:    return TestCareNotificationResponse(
origin/ux-foundation-v1:apps/api/app/routers/event_plans.py:50:def create_event_shopping_list(
origin/ux-foundation-v1:apps/api/app/routers/families.py:53:        invited_phone_masked=mask_phone(invite.invited_phone_normalized),
origin/ux-foundation-v1:apps/api/app/routers/families.py:188:            invited_phone_masked=mask_phone(inv.invited_phone_normalized),
origin/ux-foundation-v1:apps/api/app/routers/menus.py:13:    MenuVariant,
origin/ux-foundation-v1:apps/api/app/routers/menus.py:25:from app.services import care as care_service
origin/ux-foundation-v1:apps/api/app/routers/menus.py:32:async def _send_menu_care_notification(user_id: int) -> None:
origin/ux-foundation-v1:apps/api/app/routers/menus.py:37:            await care_service.maybe_notify_menu_ready(db, user)
origin/ux-foundation-v1:apps/api/app/routers/menus.py:39:        logger.exception("Menu care notification failed for user %s", user_id)
origin/ux-foundation-v1:apps/api/app/routers/menus.py:56:@router.post("/replace-dish", response_model=MenuVariant)
origin/ux-foundation-v1:apps/api/app/routers/menus.py:62:) -> MenuVariant:
origin/ux-foundation-v1:apps/api/app/routers/menus.py:75:    background_tasks.add_task(_send_menu_care_notification, user.id)
origin/ux-foundation-v1:apps/api/app/routers/notifications.py:7:from app.schemas.notifications import (
origin/ux-foundation-v1:apps/api/app/routers/notifications.py:8:    NotificationSettingsResponse,
origin/ux-foundation-v1:apps/api/app/routers/notifications.py:9:    NotificationSettingsUpdate,
origin/ux-foundation-v1:apps/api/app/routers/notifications.py:11:from app.services import notifications as notifications_service
origin/ux-foundation-v1:apps/api/app/routers/notifications.py:13:router = APIRouter(prefix="/notifications", tags=["notifications"])
origin/ux-foundation-v1:apps/api/app/routers/notifications.py:16:@router.get("/settings", response_model=NotificationSettingsResponse)
origin/ux-foundation-v1:apps/api/app/routers/notifications.py:20:) -> NotificationSettingsResponse:
origin/ux-foundation-v1:apps/api/app/routers/notifications.py:21:    return notifications_service.get_settings(db, user)
origin/ux-foundation-v1:apps/api/app/routers/notifications.py:24:@router.put("/settings", response_model=NotificationSettingsResponse)
origin/ux-foundation-v1:apps/api/app/routers/notifications.py:26:    payload: NotificationSettingsUpdate,
origin/ux-foundation-v1:apps/api/app/routers/notifications.py:29:) -> NotificationSettingsResponse:
origin/ux-foundation-v1:apps/api/app/routers/notifications.py:30:    return notifications_service.update_settings(db, user, payload)
origin/ux-foundation-v1:apps/api/app/routers/nutrition_profile.py:7:from app.schemas.nutrition_profile import NutritionProfileData, NutritionProfileResponse
origin/ux-foundation-v1:apps/api/app/routers/nutrition_profile.py:8:from app.services.nutrition_profile import (
origin/ux-foundation-v1:apps/api/app/routers/nutrition_profile.py:9:    migrate_legacy_profile,
origin/ux-foundation-v1:apps/api/app/routers/nutrition_profile.py:12:    save_nutrition_profile,
origin/ux-foundation-v1:apps/api/app/routers/nutrition_profile.py:32:def get_nutrition_profile(
origin/ux-foundation-v1:apps/api/app/routers/nutrition_profile.py:37:    migrate_legacy_profile(db, profile)
origin/ux-foundation-v1:apps/api/app/routers/nutrition_profile.py:43:def save_nutrition_profile_endpoint(
origin/ux-foundation-v1:apps/api/app/routers/nutrition_profile.py:54:    profile = save_nutrition_profile(db, user, payload)
origin/ux-foundation-v1:apps/api/app/routers/recipes.py:15:from app.schemas.menu import MenuVariant
origin/ux-foundation-v1:apps/api/app/routers/recipes.py:217:@router.post("/{recipe_id}/add-to-menu", response_model=MenuVariant)
origin/ux-foundation-v1:apps/api/app/routers/recipes.py:224:) -> MenuVariant:
origin/ux-foundation-v1:apps/api/app/routers/shopping_lists.py:9:from app.schemas.shopping_list import (
origin/ux-foundation-v1:apps/api/app/routers/shopping_lists.py:16:from app.services import shopping_list as shopping_list_service
origin/ux-foundation-v1:apps/api/app/routers/shopping_lists.py:23:def get_my_shopping_list(
origin/ux-foundation-v1:apps/api/app/routers/shopping_lists.py:28:    result = shopping_list_service.get_shopping_list(db, user, scope)
origin/ux-foundation-v1:apps/api/app/routers/shopping_lists.py:38:def sync_shopping_list(
origin/ux-foundation-v1:apps/api/app/routers/shopping_lists.py:42:    return shopping_list_service.sync_shopping_list_for_scope(db, scope)
origin/ux-foundation-v1:apps/api/app/routers/shopping_lists.py:56:    return shopping_list_service.create_item(db, user, scope, payload)
origin/ux-foundation-v1:apps/api/app/routers/shopping_lists.py:68:        return shopping_list_service.toggle_item(
origin/ux-foundation-v1:apps/api/app/routers/shopping_lists.py:76:    return shopping_list_service.update_item(db, user, scope, item_id, payload)
origin/ux-foundation-v1:apps/api/app/routers/shopping_lists.py:86:    return shopping_list_service.delete_item(db, user, scope, item_id)
origin/ux-foundation-v1:apps/api/app/routers/shopping_lists.py:97:    return shopping_list_service.toggle_item(
origin/ux-foundation-v1:apps/api/app/schemas/care.py:6:CareLevel = Literal["minimal", "standard", "active"]
origin/ux-foundation-v1:apps/api/app/schemas/care.py:7:CareNotificationType = Literal[
origin/ux-foundation-v1:apps/api/app/schemas/care.py:19:class CareSettingsResponse(BaseModel):
origin/ux-foundation-v1:apps/api/app/schemas/care.py:28:    care_level: CareLevel
origin/ux-foundation-v1:apps/api/app/schemas/care.py:36:class CareSettingsUpdate(BaseModel):
origin/ux-foundation-v1:apps/api/app/schemas/care.py:45:    care_level: CareLevel | None = None
origin/ux-foundation-v1:apps/api/app/schemas/care.py:51:class CareNotificationResponse(BaseModel):
origin/ux-foundation-v1:apps/api/app/schemas/care.py:61:class TestCareNotificationRequest(BaseModel):
origin/ux-foundation-v1:apps/api/app/schemas/care.py:62:    notification_type: CareNotificationType = "water"
origin/ux-foundation-v1:apps/api/app/schemas/care.py:65:class TestCareNotificationResponse(BaseModel):
origin/ux-foundation-v1:apps/api/app/schemas/care.py:71:class CareTipPreview(BaseModel):
origin/ux-foundation-v1:apps/api/app/schemas/care.py:77:class CareTipsResponse(BaseModel):
origin/ux-foundation-v1:apps/api/app/schemas/care.py:78:    tips: list[CareTipPreview]
origin/ux-foundation-v1:apps/api/app/schemas/family.py:56:    nutrition_profile_complete: bool = False
origin/ux-foundation-v1:apps/api/app/schemas/family_member_nutrition.py:5:from app.services.member_age import MAX_AGE_MONTHS, normalize_age_months, validate_age_months
origin/ux-foundation-v1:apps/api/app/schemas/family_member_nutrition.py:9:    """Stored in family_members.nutrition_profile JSON."""
origin/ux-foundation-v1:apps/api/app/schemas/family_member_nutrition.py:22:    # Legacy fields (read/write compat)
origin/ux-foundation-v1:apps/api/app/schemas/family_member_nutrition.py:29:    def migrate_legacy_age(cls, data):
origin/ux-foundation-v1:apps/api/app/schemas/family_member_nutrition.py:33:            resolved = normalize_age_months(
origin/ux-foundation-v1:apps/api/app/schemas/menu.py:6:MenuVariantType = Literal["quick", "economy", "balanced"]
origin/ux-foundation-v1:apps/api/app/schemas/menu.py:26:class MenuIngredient(BaseModel):
origin/ux-foundation-v1:apps/api/app/schemas/menu.py:32:class MenuVariant(BaseModel):
origin/ux-foundation-v1:apps/api/app/schemas/menu.py:33:    variant: MenuVariantType
origin/ux-foundation-v1:apps/api/app/schemas/menu.py:40:    ingredients: list[MenuIngredient] = Field(min_length=1)
origin/ux-foundation-v1:apps/api/app/schemas/menu.py:46:    menus: list[MenuVariant] = Field(min_length=3, max_length=3)
origin/ux-foundation-v1:apps/api/app/schemas/menu.py:55:    menu: MenuVariant
origin/ux-foundation-v1:apps/api/app/schemas/menu.py:80:    menu: MenuVariant
origin/ux-foundation-v1:apps/api/app/schemas/menu.py:88:    variant: MenuVariantType
origin/ux-foundation-v1:apps/api/app/schemas/menu.py:89:    menu: MenuVariant
origin/ux-foundation-v1:apps/api/app/schemas/menu_overview.py:6:from app.schemas.menu import MenuVariant, SelectedMenuResponse
origin/ux-foundation-v1:apps/api/app/schemas/notifications.py:10:class NotificationSettingsResponse(BaseModel):
origin/ux-foundation-v1:apps/api/app/schemas/notifications.py:25:class NotificationSettingsUpdate(BaseModel):
origin/ux-foundation-v1:apps/api/app/schemas/subscription.py:10:    notifications: bool = True
origin/ux-foundation-v1:apps/api/app/schemas/subscription.py:11:    nutrition_profile: bool = True
origin/ux-foundation-v1:apps/api/app/schemas/subscription.py:18:    ai_care: bool = False
origin/ux-foundation-v1:apps/api/app/services/admin_errors.py:1:"""Admin error logging to database (and legacy file fallback)."""
origin/ux-foundation-v1:apps/api/app/services/ai.py:20:    MenuIngredient,
origin/ux-foundation-v1:apps/api/app/services/ai.py:22:    MenuVariant,
origin/ux-foundation-v1:apps/api/app/services/ai.py:23:    MenuVariantType,
origin/ux-foundation-v1:apps/api/app/services/ai.py:52:MenuVariantKey = Literal["quick", "economy", "balanced"]
origin/ux-foundation-v1:apps/api/app/services/ai.py:131:    menus: list[MenuVariant]
origin/ux-foundation-v1:apps/api/app/services/ai.py:204:def _menu_variants_from_ai(data: dict[str, Any]) -> list[MenuVariant]:
origin/ux-foundation-v1:apps/api/app/services/ai.py:224:    menus: list[MenuVariant] = []
origin/ux-foundation-v1:apps/api/app/services/ai.py:260:                MenuVariant(
origin/ux-foundation-v1:apps/api/app/services/ai.py:273:                        MenuIngredient(name="Вода", amount="1 л", category="drinks")
origin/ux-foundation-v1:apps/api/app/services/ai.py:343:def _ingredients_from_ai_rows(rows: list[dict]) -> list[MenuIngredient]:
origin/ux-foundation-v1:apps/api/app/services/ai.py:364:        MenuIngredient(
origin/ux-foundation-v1:apps/api/app/services/amount_parser.py:29:def normalize_unit(raw: str) -> str:
origin/ux-foundation-v1:apps/api/app/services/amount_parser.py:47:        return None, normalize_unit(text)
origin/ux-foundation-v1:apps/api/app/services/amount_parser.py:53:        return None, normalize_unit(text)
origin/ux-foundation-v1:apps/api/app/services/amount_parser.py:55:    unit = normalize_unit(unit_raw) if unit_raw else "шт"
origin/ux-foundation-v1:apps/api/app/services/bot_input.py:14:from app.schemas.shopping_list import ShoppingItemCreateRequest, ShoppingItemUpdateRequest
origin/ux-foundation-v1:apps/api/app/services/bot_input.py:16:from app.services import shopping_list as shopping_service
origin/ux-foundation-v1:apps/api/app/services/bot_input.py:62:def _normalize_match(name: str) -> str:
origin/ux-foundation-v1:apps/api/app/services/bot_input.py:169:    listing = shopping_service.get_shopping_list(db, user, scope)
origin/ux-foundation-v1:apps/api/app/services/bot_input.py:170:    key = _normalize_match(name)
origin/ux-foundation-v1:apps/api/app/services/bot_input.py:172:        if _normalize_match(item.name) == key and not item.checked:
origin/ux-foundation-v1:apps/api/app/services/bot_today.py:10:from app.services import shopping_list as shopping_service
origin/ux-foundation-v1:apps/api/app/services/bot_today.py:22:    shopping = shopping_service.get_shopping_list(db, user, scope)
origin/ux-foundation-v1:apps/api/app/services/care.py:13:from app.models.care import CareEvent, CareNotification, CareSettings
origin/ux-foundation-v1:apps/api/app/services/care.py:15:from app.schemas.care import (
origin/ux-foundation-v1:apps/api/app/services/care.py:16:    CareNotificationResponse,
origin/ux-foundation-v1:apps/api/app/services/care.py:17:    CareSettingsResponse,
origin/ux-foundation-v1:apps/api/app/services/care.py:18:    CareSettingsUpdate,
origin/ux-foundation-v1:apps/api/app/services/care.py:19:    CareTipPreview,
origin/ux-foundation-v1:apps/api/app/services/care.py:24:from app.services.notifications import get_or_create_settings as get_notif_settings_row
origin/ux-foundation-v1:apps/api/app/services/care.py:27:from app.services import shopping_list as shopping_list_service
origin/ux-foundation-v1:apps/api/app/services/care.py:32:CareLevel = str
origin/ux-foundation-v1:apps/api/app/services/care.py:40:COOLDOWN_HOURS: dict[str, dict[CareLevel, int]] = {
origin/ux-foundation-v1:apps/api/app/services/care.py:51:CARE_TEMPLATES: dict[str, dict[str, str]] = {
origin/ux-foundation-v1:apps/api/app/services/care.py:104:class CareContext:
origin/ux-foundation-v1:apps/api/app/services/care.py:116:def _user_timezone(settings_row: CareSettings, user: User, db: Session) -> str:
origin/ux-foundation-v1:apps/api/app/services/care.py:130:def _is_quiet_hours(settings_row: CareSettings, user: User, db: Session) -> bool:
origin/ux-foundation-v1:apps/api/app/services/care.py:148:        return bool(features.get("ai_care"))
origin/ux-foundation-v1:apps/api/app/services/care.py:153:def get_or_create_care_settings(db: Session, user: User) -> CareSettings:
origin/ux-foundation-v1:apps/api/app/services/care.py:155:        db.query(CareSettings).filter(CareSettings.user_id == user.id).one_or_none()
origin/ux-foundation-v1:apps/api/app/services/care.py:159:        row = CareSettings(
origin/ux-foundation-v1:apps/api/app/services/care.py:165:            care_level="standard",
origin/ux-foundation-v1:apps/api/app/services/care.py:174:    row: CareSettings, *, has_pro: bool
origin/ux-foundation-v1:apps/api/app/services/care.py:175:) -> CareSettingsResponse:
origin/ux-foundation-v1:apps/api/app/services/care.py:176:    return CareSettingsResponse(
origin/ux-foundation-v1:apps/api/app/services/care.py:185:        care_level=row.care_level,  # type: ignore[arg-type]
origin/ux-foundation-v1:apps/api/app/services/care.py:194:def get_care_settings(db: Session, user: User) -> CareSettingsResponse:
origin/ux-foundation-v1:apps/api/app/services/care.py:195:    row = get_or_create_care_settings(db, user)
origin/ux-foundation-v1:apps/api/app/services/care.py:199:def update_care_settings(
origin/ux-foundation-v1:apps/api/app/services/care.py:200:    db: Session, user: User, payload: CareSettingsUpdate
origin/ux-foundation-v1:apps/api/app/services/care.py:201:) -> CareSettingsResponse:
origin/ux-foundation-v1:apps/api/app/services/care.py:202:    row = get_or_create_care_settings(db, user)
origin/ux-foundation-v1:apps/api/app/services/care.py:204:    previous_level = row.care_level
origin/ux-foundation-v1:apps/api/app/services/care.py:208:    if data.get("care_level") == "minimal" and previous_level != "minimal":
origin/ux-foundation-v1:apps/api/app/services/care.py:224:def list_care_notifications(
origin/ux-foundation-v1:apps/api/app/services/care.py:226:) -> list[CareNotificationResponse]:
origin/ux-foundation-v1:apps/api/app/services/care.py:228:        db.query(CareNotification)
origin/ux-foundation-v1:apps/api/app/services/care.py:229:        .filter(CareNotification.user_id == user.id)
origin/ux-foundation-v1:apps/api/app/services/care.py:230:        .order_by(desc(CareNotification.created_at))
origin/ux-foundation-v1:apps/api/app/services/care.py:235:        CareNotificationResponse(
origin/ux-foundation-v1:apps/api/app/services/care.py:248:def _type_enabled(settings_row: CareSettings, notification_type: str) -> bool:
origin/ux-foundation-v1:apps/api/app/services/care.py:261:def _level_allows_type(care_level: str, notification_type: str) -> bool:
origin/ux-foundation-v1:apps/api/app/services/care.py:262:    if care_level == "minimal":
origin/ux-foundation-v1:apps/api/app/services/care.py:264:    if care_level == "standard":
origin/ux-foundation-v1:apps/api/app/services/care.py:269:def _cooldown_hours(care_level: str, notification_type: str) -> int:
origin/ux-foundation-v1:apps/api/app/services/care.py:271:    return by_type.get(care_level, 24)
origin/ux-foundation-v1:apps/api/app/services/care.py:278:        db.query(CareNotification)
origin/ux-foundation-v1:apps/api/app/services/care.py:280:            CareNotification.user_id == user_id,
origin/ux-foundation-v1:apps/api/app/services/care.py:281:            CareNotification.type == notification_type,
origin/ux-foundation-v1:apps/api/app/services/care.py:282:            CareNotification.status == "sent",
origin/ux-foundation-v1:apps/api/app/services/care.py:284:        .order_by(desc(CareNotification.sent_at))
origin/ux-foundation-v1:apps/api/app/services/care.py:298:    settings_row = get_or_create_care_settings(db, user)
origin/ux-foundation-v1:apps/api/app/services/care.py:302:    if not _level_allows_type(settings_row.care_level, notification_type):
origin/ux-foundation-v1:apps/api/app/services/care.py:312:            hours = _cooldown_hours(settings_row.care_level, notification_type)
origin/ux-foundation-v1:apps/api/app/services/care.py:319:def create_care_notification(
origin/ux-foundation-v1:apps/api/app/services/care.py:329:) -> CareNotification:
origin/ux-foundation-v1:apps/api/app/services/care.py:330:    template = CARE_TEMPLATES.get(notification_type, CARE_TEMPLATES["water"])
origin/ux-foundation-v1:apps/api/app/services/care.py:331:    row = CareNotification(
origin/ux-foundation-v1:apps/api/app/services/care.py:347:def log_care_event(
origin/ux-foundation-v1:apps/api/app/services/care.py:352:    source: str = "care",
origin/ux-foundation-v1:apps/api/app/services/care.py:355:) -> CareEvent:
origin/ux-foundation-v1:apps/api/app/services/care.py:356:    event = CareEvent(
origin/ux-foundation-v1:apps/api/app/services/care.py:369:async def send_telegram_care_notification(
origin/ux-foundation-v1:apps/api/app/services/care.py:371:    notification: CareNotification,
origin/ux-foundation-v1:apps/api/app/services/care.py:377:        logger.info("Care notification skipped: no telegram_id for user %s", user.id)
origin/ux-foundation-v1:apps/api/app/services/care.py:380:    template = CARE_TEMPLATES.get(notification.type, {})
origin/ux-foundation-v1:apps/api/app/services/care.py:400:    log_care_event(
origin/ux-foundation-v1:apps/api/app/services/care.py:403:        f"care_{notification.type}_{'sent' if sent else 'failed'}",
origin/ux-foundation-v1:apps/api/app/services/care.py:409:def build_care_context(db: Session, user: User) -> CareContext:
origin/ux-foundation-v1:apps/api/app/services/care.py:412:    shopping = shopping_list_service.get_shopping_list(db, user, scope)
origin/ux-foundation-v1:apps/api/app/services/care.py:428:    return CareContext(
origin/ux-foundation-v1:apps/api/app/services/care.py:441:def generate_basic_care_tips(
origin/ux-foundation-v1:apps/api/app/services/care.py:442:    db: Session, user: User, context: CareContext | None = None
origin/ux-foundation-v1:apps/api/app/services/care.py:443:) -> list[CareTipPreview]:
origin/ux-foundation-v1:apps/api/app/services/care.py:444:    ctx = context or build_care_context(db, user)
origin/ux-foundation-v1:apps/api/app/services/care.py:445:    tips: list[CareTipPreview] = []
origin/ux-foundation-v1:apps/api/app/services/care.py:448:        t = CARE_TEMPLATES["shopping"]
origin/ux-foundation-v1:apps/api/app/services/care.py:450:            CareTipPreview(type="shopping", title=t["title"], message=t["message"])
origin/ux-foundation-v1:apps/api/app/services/care.py:453:        t = CARE_TEMPLATES["pantry"]
origin/ux-foundation-v1:apps/api/app/services/care.py:460:        tips.append(CareTipPreview(type="pantry", title=t["title"], message=msg))
origin/ux-foundation-v1:apps/api/app/services/care.py:462:        t = CARE_TEMPLATES["menu"]
origin/ux-foundation-v1:apps/api/app/services/care.py:463:        tips.append(CareTipPreview(type="menu", title=t["title"], message=t["message"]))
origin/ux-foundation-v1:apps/api/app/services/care.py:465:        t = CARE_TEMPLATES["protein"]
origin/ux-foundation-v1:apps/api/app/services/care.py:467:            CareTipPreview(type="protein", title=t["title"], message=t["message"])
origin/ux-foundation-v1:apps/api/app/services/care.py:469:    t = CARE_TEMPLATES["water"]
origin/ux-foundation-v1:apps/api/app/services/care.py:470:    tips.append(CareTipPreview(type="water", title=t["title"], message=t["message"]))
origin/ux-foundation-v1:apps/api/app/services/care.py:472:        t = CARE_TEMPLATES["family"]
origin/ux-foundation-v1:apps/api/app/services/care.py:473:        tips.append(CareTipPreview(type="family", title=t["title"], message=t["message"]))
origin/ux-foundation-v1:apps/api/app/services/care.py:475:        t = CARE_TEMPLATES["pro"]
origin/ux-foundation-v1:apps/api/app/services/care.py:476:        tips.append(CareTipPreview(type="pro", title=t["title"], message=t["message"]))
origin/ux-foundation-v1:apps/api/app/services/care.py:481:async def send_care_notification_by_type(
origin/ux-foundation-v1:apps/api/app/services/care.py:489:) -> tuple[bool, str, CareNotification | None]:
origin/ux-foundation-v1:apps/api/app/services/care.py:499:    template = CARE_TEMPLATES[notification_type]
origin/ux-foundation-v1:apps/api/app/services/care.py:500:    notification = create_care_notification(
origin/ux-foundation-v1:apps/api/app/services/care.py:510:    sent = await send_telegram_care_notification(db, notification, user)
origin/ux-foundation-v1:apps/api/app/services/care.py:527:    ctx = build_care_context(db, user)
origin/ux-foundation-v1:apps/api/app/services/care.py:530:    await send_care_notification_by_type(db, user, "menu")
origin/ux-foundation-v1:apps/api/app/services/care.py:533:async def process_care_reminders_for_user(db: Session, user: User) -> None:
origin/ux-foundation-v1:apps/api/app/services/care.py:534:    """Send at most one contextual care tip per scheduler tick."""
origin/ux-foundation-v1:apps/api/app/services/care.py:535:    settings_row = get_or_create_care_settings(db, user)
origin/ux-foundation-v1:apps/api/app/services/care.py:536:    if settings_row.care_level == "minimal" and not any(
origin/ux-foundation-v1:apps/api/app/services/care.py:545:    ctx = build_care_context(db, user)
origin/ux-foundation-v1:apps/api/app/services/care.py:546:    tips = generate_basic_care_tips(db, user, ctx)
origin/ux-foundation-v1:apps/api/app/services/care.py:550:            await send_care_notification_by_type(db, user, tip.type)
origin/ux-foundation-v1:apps/api/app/services/care.py:554:async def process_all_care_reminders(db: Session) -> None:
origin/ux-foundation-v1:apps/api/app/services/care.py:560:            await process_care_reminders_for_user(db, user)
origin/ux-foundation-v1:apps/api/app/services/care.py:562:            logger.exception("Care reminder failed for user %s", user.id)
origin/ux-foundation-v1:apps/api/app/services/event_plan.py:19:from app.schemas.menu import MenuIngredient
origin/ux-foundation-v1:apps/api/app/services/event_plan.py:27:from app.services import shopping_list as shopping_list_service
origin/ux-foundation-v1:apps/api/app/services/event_plan.py:194:    from app.schemas.menu import MenuVariant
origin/ux-foundation-v1:apps/api/app/services/event_plan.py:197:        MenuIngredient(
origin/ux-foundation-v1:apps/api/app/services/event_plan.py:205:    menu = MenuVariant(
origin/ux-foundation-v1:apps/api/app/services/event_plan.py:213:    shopping_list_service.sync_from_menu(db, scope, menu, None)
origin/ux-foundation-v1:apps/api/app/services/family.py:21:from app.schemas.nutrition_profile import NutritionProfileData, NutritionProData
origin/ux-foundation-v1:apps/api/app/services/family.py:23:from app.services.nutrition_profile import save_nutrition_profile
origin/ux-foundation-v1:apps/api/app/services/family.py:99:        nutrition_profile_complete=complete,
origin/ux-foundation-v1:apps/api/app/services/family.py:226:        invited_phone_masked=mask_phone(invite.invited_phone_normalized),
```

## Keyword scan in origin/release-candidate-ux

Hits (max 300): **300**

```
origin/release-candidate-ux:apps/api/app/database.py:36:        shopping_list,
origin/release-candidate-ux:apps/api/app/database.py:42:    from app.models import care as care_models  # noqa: F401
origin/release-candidate-ux:apps/api/app/database_migrations.py:26:        "ALTER TABLE family_shopping_lists ADD COLUMN IF NOT EXISTS user_id INTEGER",
origin/release-candidate-ux:apps/api/app/database_migrations.py:32:                WHERE conname = 'family_shopping_lists_user_id_fkey'
origin/release-candidate-ux:apps/api/app/database_migrations.py:34:                ALTER TABLE family_shopping_lists
origin/release-candidate-ux:apps/api/app/database_migrations.py:35:                ADD CONSTRAINT family_shopping_lists_user_id_fkey
origin/release-candidate-ux:apps/api/app/database_migrations.py:40:        "ALTER TABLE family_shopping_lists ALTER COLUMN family_id DROP NOT NULL",
origin/release-candidate-ux:apps/api/app/database_migrations.py:41:        "CREATE UNIQUE INDEX IF NOT EXISTS ix_family_shopping_lists_user_id ON family_shopping_lists (user_id)",
origin/release-candidate-ux:apps/api/app/database_migrations.py:76:            invited_phone_normalized VARCHAR(32) NOT NULL,
origin/release-candidate-ux:apps/api/app/database_migrations.py:88:        ON family_invites (family_id, invited_phone_normalized)
origin/release-candidate-ux:apps/api/app/database_migrations.py:94:        ON family_invites (family_id, invited_phone_normalized)
origin/release-candidate-ux:apps/api/app/database_migrations.py:95:        WHERE status = 'pending' AND invited_phone_normalized != '__link__';
origin/release-candidate-ux:apps/api/app/database_migrations.py:139:        "ALTER TABLE family_members ADD COLUMN IF NOT EXISTS nutrition_profile JSONB NOT NULL DEFAULT '{}'",
origin/release-candidate-ux:apps/api/app/database_migrations.py:214:        # AI Care System (stage 8)
origin/release-candidate-ux:apps/api/app/database_migrations.py:216:        CREATE TABLE IF NOT EXISTS care_settings (
origin/release-candidate-ux:apps/api/app/database_migrations.py:227:            care_level VARCHAR(16) NOT NULL DEFAULT 'standard',
origin/release-candidate-ux:apps/api/app/database_migrations.py:236:        CREATE TABLE IF NOT EXISTS care_notifications (
origin/release-candidate-ux:apps/api/app/database_migrations.py:250:        "CREATE INDEX IF NOT EXISTS ix_care_notifications_user_id ON care_notifications (user_id);",
origin/release-candidate-ux:apps/api/app/database_migrations.py:252:        CREATE TABLE IF NOT EXISTS care_events (
origin/release-candidate-ux:apps/api/app/database_migrations.py:257:            source VARCHAR(64) NOT NULL DEFAULT 'care',
origin/release-candidate-ux:apps/api/app/database_migrations.py:262:        "CREATE INDEX IF NOT EXISTS ix_care_events_user_id ON care_events (user_id);",
origin/release-candidate-ux:apps/api/app/main.py:17:    care,
origin/release-candidate-ux:apps/api/app/main.py:23:    notifications,
origin/release-candidate-ux:apps/api/app/main.py:24:    nutrition_profile,
origin/release-candidate-ux:apps/api/app/main.py:32:    shopping_lists,
origin/release-candidate-ux:apps/api/app/main.py:104:app.include_router(care.router)
origin/release-candidate-ux:apps/api/app/main.py:107:app.include_router(nutrition_profile.router)
origin/release-candidate-ux:apps/api/app/main.py:113:app.include_router(shopping_lists.router)
origin/release-candidate-ux:apps/api/app/main.py:116:app.include_router(notifications.router)
origin/release-candidate-ux:apps/api/app/models/__init__.py:2:from app.models.care import CareEvent, CareNotification, CareSettings
origin/release-candidate-ux:apps/api/app/models/__init__.py:7:from app.models.notification_settings import UserNotificationSettings
origin/release-candidate-ux:apps/api/app/models/__init__.py:11:from app.models.shopping_list import FamilyShoppingList
origin/release-candidate-ux:apps/api/app/models/__init__.py:36:    "UserNotificationSettings",
origin/release-candidate-ux:apps/api/app/models/__init__.py:45:    "CareSettings",
origin/release-candidate-ux:apps/api/app/models/__init__.py:46:    "CareNotification",
origin/release-candidate-ux:apps/api/app/models/__init__.py:47:    "CareEvent",
origin/release-candidate-ux:apps/api/app/models/care.py:11:class CareSettings(Base):
origin/release-candidate-ux:apps/api/app/models/care.py:12:    __tablename__ = "care_settings"
origin/release-candidate-ux:apps/api/app/models/care.py:26:    care_level: Mapped[str] = mapped_column(String(16), default="standard")
origin/release-candidate-ux:apps/api/app/models/care.py:37:    user = relationship("User", backref="care_settings")
origin/release-candidate-ux:apps/api/app/models/care.py:40:class CareNotification(Base):
origin/release-candidate-ux:apps/api/app/models/care.py:41:    __tablename__ = "care_notifications"
origin/release-candidate-ux:apps/api/app/models/care.py:66:class CareEvent(Base):
origin/release-candidate-ux:apps/api/app/models/care.py:67:    __tablename__ = "care_events"
origin/release-candidate-ux:apps/api/app/models/care.py:77:    source: Mapped[str] = mapped_column(String(64), default="care")
origin/release-candidate-ux:apps/api/app/models/family.py:60:    nutrition_profile: Mapped[dict] = mapped_column(JSONB, default=dict)
origin/release-candidate-ux:apps/api/app/models/family_invite.py:24:    invited_phone_normalized: Mapped[str] = mapped_column(String(32), index=True)
origin/release-candidate-ux:apps/api/app/models/notification_settings.py:9:class UserNotificationSettings(Base):
origin/release-candidate-ux:apps/api/app/models/shopping_list.py:11:    __tablename__ = "family_shopping_lists"
origin/release-candidate-ux:apps/api/app/models/user.py:64:        "UserNotificationSettings",
origin/release-candidate-ux:apps/api/app/routers/care.py:7:from app.schemas.care import (
origin/release-candidate-ux:apps/api/app/routers/care.py:8:    CareNotificationResponse,
origin/release-candidate-ux:apps/api/app/routers/care.py:9:    CareSettingsResponse,
origin/release-candidate-ux:apps/api/app/routers/care.py:10:    CareSettingsUpdate,
origin/release-candidate-ux:apps/api/app/routers/care.py:11:    CareTipsResponse,
origin/release-candidate-ux:apps/api/app/routers/care.py:12:    TestCareNotificationRequest,
origin/release-candidate-ux:apps/api/app/routers/care.py:13:    TestCareNotificationResponse,
origin/release-candidate-ux:apps/api/app/routers/care.py:15:from app.services import care as care_service
origin/release-candidate-ux:apps/api/app/routers/care.py:17:router = APIRouter(prefix="/care", tags=["care"])
origin/release-candidate-ux:apps/api/app/routers/care.py:20:@router.get("/settings", response_model=CareSettingsResponse)
origin/release-candidate-ux:apps/api/app/routers/care.py:21:def get_care_settings(
origin/release-candidate-ux:apps/api/app/routers/care.py:24:) -> CareSettingsResponse:
origin/release-candidate-ux:apps/api/app/routers/care.py:25:    return care_service.get_care_settings(db, user)
origin/release-candidate-ux:apps/api/app/routers/care.py:28:@router.patch("/settings", response_model=CareSettingsResponse)
origin/release-candidate-ux:apps/api/app/routers/care.py:29:def patch_care_settings(
origin/release-candidate-ux:apps/api/app/routers/care.py:30:    payload: CareSettingsUpdate,
origin/release-candidate-ux:apps/api/app/routers/care.py:33:) -> CareSettingsResponse:
origin/release-candidate-ux:apps/api/app/routers/care.py:34:    return care_service.update_care_settings(db, user, payload)
origin/release-candidate-ux:apps/api/app/routers/care.py:37:@router.get("/notifications", response_model=list[CareNotificationResponse])
origin/release-candidate-ux:apps/api/app/routers/care.py:38:def list_care_notifications(
origin/release-candidate-ux:apps/api/app/routers/care.py:41:) -> list[CareNotificationResponse]:
origin/release-candidate-ux:apps/api/app/routers/care.py:42:    return care_service.list_care_notifications(db, user)
origin/release-candidate-ux:apps/api/app/routers/care.py:45:@router.get("/tips", response_model=CareTipsResponse)
origin/release-candidate-ux:apps/api/app/routers/care.py:46:def preview_care_tips(
origin/release-candidate-ux:apps/api/app/routers/care.py:49:) -> CareTipsResponse:
origin/release-candidate-ux:apps/api/app/routers/care.py:50:    ctx = care_service.build_care_context(db, user)
origin/release-candidate-ux:apps/api/app/routers/care.py:51:    return CareTipsResponse(tips=care_service.generate_basic_care_tips(db, user, ctx))
origin/release-candidate-ux:apps/api/app/routers/care.py:54:@router.post("/test-notification", response_model=TestCareNotificationResponse)
origin/release-candidate-ux:apps/api/app/routers/care.py:56:    payload: TestCareNotificationRequest,
origin/release-candidate-ux:apps/api/app/routers/care.py:59:) -> TestCareNotificationResponse:
origin/release-candidate-ux:apps/api/app/routers/care.py:60:    ok, message, notification = await care_service.send_care_notification_by_type(
origin/release-candidate-ux:apps/api/app/routers/care.py:67:    return TestCareNotificationResponse(
origin/release-candidate-ux:apps/api/app/routers/event_plans.py:50:def create_event_shopping_list(
origin/release-candidate-ux:apps/api/app/routers/families.py:53:        invited_phone_masked=mask_phone(invite.invited_phone_normalized),
origin/release-candidate-ux:apps/api/app/routers/families.py:188:            invited_phone_masked=mask_phone(inv.invited_phone_normalized),
origin/release-candidate-ux:apps/api/app/routers/menus.py:13:    MenuVariant,
origin/release-candidate-ux:apps/api/app/routers/menus.py:25:from app.services import care as care_service
origin/release-candidate-ux:apps/api/app/routers/menus.py:32:async def _send_menu_care_notification(user_id: int) -> None:
origin/release-candidate-ux:apps/api/app/routers/menus.py:37:            await care_service.maybe_notify_menu_ready(db, user)
origin/release-candidate-ux:apps/api/app/routers/menus.py:39:        logger.exception("Menu care notification failed for user %s", user_id)
origin/release-candidate-ux:apps/api/app/routers/menus.py:56:@router.post("/replace-dish", response_model=MenuVariant)
origin/release-candidate-ux:apps/api/app/routers/menus.py:62:) -> MenuVariant:
origin/release-candidate-ux:apps/api/app/routers/menus.py:75:    background_tasks.add_task(_send_menu_care_notification, user.id)
origin/release-candidate-ux:apps/api/app/routers/notifications.py:7:from app.schemas.notifications import (
origin/release-candidate-ux:apps/api/app/routers/notifications.py:8:    NotificationSettingsResponse,
origin/release-candidate-ux:apps/api/app/routers/notifications.py:9:    NotificationSettingsUpdate,
origin/release-candidate-ux:apps/api/app/routers/notifications.py:11:from app.services import notifications as notifications_service
origin/release-candidate-ux:apps/api/app/routers/notifications.py:13:router = APIRouter(prefix="/notifications", tags=["notifications"])
origin/release-candidate-ux:apps/api/app/routers/notifications.py:16:@router.get("/settings", response_model=NotificationSettingsResponse)
origin/release-candidate-ux:apps/api/app/routers/notifications.py:20:) -> NotificationSettingsResponse:
origin/release-candidate-ux:apps/api/app/routers/notifications.py:21:    return notifications_service.get_settings(db, user)
origin/release-candidate-ux:apps/api/app/routers/notifications.py:24:@router.put("/settings", response_model=NotificationSettingsResponse)
origin/release-candidate-ux:apps/api/app/routers/notifications.py:26:    payload: NotificationSettingsUpdate,
origin/release-candidate-ux:apps/api/app/routers/notifications.py:29:) -> NotificationSettingsResponse:
origin/release-candidate-ux:apps/api/app/routers/notifications.py:30:    return notifications_service.update_settings(db, user, payload)
origin/release-candidate-ux:apps/api/app/routers/nutrition_profile.py:7:from app.schemas.nutrition_profile import NutritionProfileData, NutritionProfileResponse
origin/release-candidate-ux:apps/api/app/routers/nutrition_profile.py:8:from app.services.nutrition_profile import (
origin/release-candidate-ux:apps/api/app/routers/nutrition_profile.py:9:    migrate_legacy_profile,
origin/release-candidate-ux:apps/api/app/routers/nutrition_profile.py:12:    save_nutrition_profile,
origin/release-candidate-ux:apps/api/app/routers/nutrition_profile.py:32:def get_nutrition_profile(
origin/release-candidate-ux:apps/api/app/routers/nutrition_profile.py:37:    migrate_legacy_profile(db, profile)
origin/release-candidate-ux:apps/api/app/routers/nutrition_profile.py:43:def save_nutrition_profile_endpoint(
origin/release-candidate-ux:apps/api/app/routers/nutrition_profile.py:54:    profile = save_nutrition_profile(db, user, payload)
origin/release-candidate-ux:apps/api/app/routers/recipes.py:15:from app.schemas.menu import MenuVariant
origin/release-candidate-ux:apps/api/app/routers/recipes.py:217:@router.post("/{recipe_id}/add-to-menu", response_model=MenuVariant)
origin/release-candidate-ux:apps/api/app/routers/recipes.py:224:) -> MenuVariant:
origin/release-candidate-ux:apps/api/app/routers/shopping_lists.py:9:from app.schemas.shopping_list import (
origin/release-candidate-ux:apps/api/app/routers/shopping_lists.py:16:from app.services import shopping_list as shopping_list_service
origin/release-candidate-ux:apps/api/app/routers/shopping_lists.py:23:def get_my_shopping_list(
origin/release-candidate-ux:apps/api/app/routers/shopping_lists.py:28:    result = shopping_list_service.get_shopping_list(db, user, scope)
origin/release-candidate-ux:apps/api/app/routers/shopping_lists.py:38:def sync_shopping_list(
origin/release-candidate-ux:apps/api/app/routers/shopping_lists.py:42:    return shopping_list_service.sync_shopping_list_for_scope(db, scope)
origin/release-candidate-ux:apps/api/app/routers/shopping_lists.py:56:    return shopping_list_service.create_item(db, user, scope, payload)
origin/release-candidate-ux:apps/api/app/routers/shopping_lists.py:68:        return shopping_list_service.toggle_item(
origin/release-candidate-ux:apps/api/app/routers/shopping_lists.py:76:    return shopping_list_service.update_item(db, user, scope, item_id, payload)
origin/release-candidate-ux:apps/api/app/routers/shopping_lists.py:86:    return shopping_list_service.delete_item(db, user, scope, item_id)
origin/release-candidate-ux:apps/api/app/routers/shopping_lists.py:97:    return shopping_list_service.toggle_item(
origin/release-candidate-ux:apps/api/app/schemas/care.py:6:CareLevel = Literal["minimal", "standard", "active"]
origin/release-candidate-ux:apps/api/app/schemas/care.py:7:CareNotificationType = Literal[
origin/release-candidate-ux:apps/api/app/schemas/care.py:19:class CareSettingsResponse(BaseModel):
origin/release-candidate-ux:apps/api/app/schemas/care.py:28:    care_level: CareLevel
origin/release-candidate-ux:apps/api/app/schemas/care.py:36:class CareSettingsUpdate(BaseModel):
origin/release-candidate-ux:apps/api/app/schemas/care.py:45:    care_level: CareLevel | None = None
origin/release-candidate-ux:apps/api/app/schemas/care.py:51:class CareNotificationResponse(BaseModel):
origin/release-candidate-ux:apps/api/app/schemas/care.py:61:class TestCareNotificationRequest(BaseModel):
origin/release-candidate-ux:apps/api/app/schemas/care.py:62:    notification_type: CareNotificationType = "water"
origin/release-candidate-ux:apps/api/app/schemas/care.py:65:class TestCareNotificationResponse(BaseModel):
origin/release-candidate-ux:apps/api/app/schemas/care.py:71:class CareTipPreview(BaseModel):
origin/release-candidate-ux:apps/api/app/schemas/care.py:77:class CareTipsResponse(BaseModel):
origin/release-candidate-ux:apps/api/app/schemas/care.py:78:    tips: list[CareTipPreview]
origin/release-candidate-ux:apps/api/app/schemas/family.py:56:    nutrition_profile_complete: bool = False
origin/release-candidate-ux:apps/api/app/schemas/family_member_nutrition.py:5:from app.services.member_age import MAX_AGE_MONTHS, normalize_age_months, validate_age_months
origin/release-candidate-ux:apps/api/app/schemas/family_member_nutrition.py:9:    """Stored in family_members.nutrition_profile JSON."""
origin/release-candidate-ux:apps/api/app/schemas/family_member_nutrition.py:22:    # Legacy fields (read/write compat)
origin/release-candidate-ux:apps/api/app/schemas/family_member_nutrition.py:29:    def migrate_legacy_age(cls, data):
origin/release-candidate-ux:apps/api/app/schemas/family_member_nutrition.py:33:            resolved = normalize_age_months(
origin/release-candidate-ux:apps/api/app/schemas/menu.py:6:MenuVariantType = Literal["quick", "economy", "balanced"]
origin/release-candidate-ux:apps/api/app/schemas/menu.py:26:class MenuIngredient(BaseModel):
origin/release-candidate-ux:apps/api/app/schemas/menu.py:32:class MenuVariant(BaseModel):
origin/release-candidate-ux:apps/api/app/schemas/menu.py:33:    variant: MenuVariantType
origin/release-candidate-ux:apps/api/app/schemas/menu.py:40:    ingredients: list[MenuIngredient] = Field(min_length=1)
origin/release-candidate-ux:apps/api/app/schemas/menu.py:46:    menus: list[MenuVariant] = Field(min_length=3, max_length=3)
origin/release-candidate-ux:apps/api/app/schemas/menu.py:55:    menu: MenuVariant
origin/release-candidate-ux:apps/api/app/schemas/menu.py:80:    menu: MenuVariant
origin/release-candidate-ux:apps/api/app/schemas/menu.py:88:    variant: MenuVariantType
origin/release-candidate-ux:apps/api/app/schemas/menu.py:89:    menu: MenuVariant
origin/release-candidate-ux:apps/api/app/schemas/menu_overview.py:6:from app.schemas.menu import MenuVariant, SelectedMenuResponse
origin/release-candidate-ux:apps/api/app/schemas/notifications.py:10:class NotificationSettingsResponse(BaseModel):
origin/release-candidate-ux:apps/api/app/schemas/notifications.py:25:class NotificationSettingsUpdate(BaseModel):
origin/release-candidate-ux:apps/api/app/schemas/subscription.py:10:    notifications: bool = True
origin/release-candidate-ux:apps/api/app/schemas/subscription.py:11:    nutrition_profile: bool = True
origin/release-candidate-ux:apps/api/app/schemas/subscription.py:18:    ai_care: bool = False
origin/release-candidate-ux:apps/api/app/services/admin_errors.py:1:"""Admin error logging to database (and legacy file fallback)."""
origin/release-candidate-ux:apps/api/app/services/ai.py:20:    MenuIngredient,
origin/release-candidate-ux:apps/api/app/services/ai.py:22:    MenuVariant,
origin/release-candidate-ux:apps/api/app/services/ai.py:23:    MenuVariantType,
origin/release-candidate-ux:apps/api/app/services/ai.py:52:MenuVariantKey = Literal["quick", "economy", "balanced"]
origin/release-candidate-ux:apps/api/app/services/ai.py:131:    menus: list[MenuVariant]
origin/release-candidate-ux:apps/api/app/services/ai.py:204:def _menu_variants_from_ai(data: dict[str, Any]) -> list[MenuVariant]:
origin/release-candidate-ux:apps/api/app/services/ai.py:224:    menus: list[MenuVariant] = []
origin/release-candidate-ux:apps/api/app/services/ai.py:260:                MenuVariant(
origin/release-candidate-ux:apps/api/app/services/ai.py:273:                        MenuIngredient(name="Вода", amount="1 л", category="drinks")
origin/release-candidate-ux:apps/api/app/services/ai.py:343:def _ingredients_from_ai_rows(rows: list[dict]) -> list[MenuIngredient]:
origin/release-candidate-ux:apps/api/app/services/ai.py:364:        MenuIngredient(
origin/release-candidate-ux:apps/api/app/services/amount_parser.py:29:def normalize_unit(raw: str) -> str:
origin/release-candidate-ux:apps/api/app/services/amount_parser.py:47:        return None, normalize_unit(text)
origin/release-candidate-ux:apps/api/app/services/amount_parser.py:53:        return None, normalize_unit(text)
origin/release-candidate-ux:apps/api/app/services/amount_parser.py:55:    unit = normalize_unit(unit_raw) if unit_raw else "шт"
origin/release-candidate-ux:apps/api/app/services/bot_input.py:14:from app.schemas.shopping_list import ShoppingItemCreateRequest, ShoppingItemUpdateRequest
origin/release-candidate-ux:apps/api/app/services/bot_input.py:16:from app.services import shopping_list as shopping_service
origin/release-candidate-ux:apps/api/app/services/bot_input.py:62:def _normalize_match(name: str) -> str:
origin/release-candidate-ux:apps/api/app/services/bot_input.py:169:    listing = shopping_service.get_shopping_list(db, user, scope)
origin/release-candidate-ux:apps/api/app/services/bot_input.py:170:    key = _normalize_match(name)
origin/release-candidate-ux:apps/api/app/services/bot_input.py:172:        if _normalize_match(item.name) == key and not item.checked:
origin/release-candidate-ux:apps/api/app/services/bot_today.py:10:from app.services import shopping_list as shopping_service
origin/release-candidate-ux:apps/api/app/services/bot_today.py:22:    shopping = shopping_service.get_shopping_list(db, user, scope)
origin/release-candidate-ux:apps/api/app/services/care.py:13:from app.models.care import CareEvent, CareNotification, CareSettings
origin/release-candidate-ux:apps/api/app/services/care.py:15:from app.schemas.care import (
origin/release-candidate-ux:apps/api/app/services/care.py:16:    CareNotificationResponse,
origin/release-candidate-ux:apps/api/app/services/care.py:17:    CareSettingsResponse,
origin/release-candidate-ux:apps/api/app/services/care.py:18:    CareSettingsUpdate,
origin/release-candidate-ux:apps/api/app/services/care.py:19:    CareTipPreview,
origin/release-candidate-ux:apps/api/app/services/care.py:24:from app.services.notifications import get_or_create_settings as get_notif_settings_row
origin/release-candidate-ux:apps/api/app/services/care.py:27:from app.services import shopping_list as shopping_list_service
origin/release-candidate-ux:apps/api/app/services/care.py:32:CareLevel = str
origin/release-candidate-ux:apps/api/app/services/care.py:40:COOLDOWN_HOURS: dict[str, dict[CareLevel, int]] = {
origin/release-candidate-ux:apps/api/app/services/care.py:51:CARE_TEMPLATES: dict[str, dict[str, str]] = {
origin/release-candidate-ux:apps/api/app/services/care.py:104:class CareContext:
origin/release-candidate-ux:apps/api/app/services/care.py:116:def _user_timezone(settings_row: CareSettings, user: User, db: Session) -> str:
origin/release-candidate-ux:apps/api/app/services/care.py:130:def _is_quiet_hours(settings_row: CareSettings, user: User, db: Session) -> bool:
origin/release-candidate-ux:apps/api/app/services/care.py:148:        return bool(features.get("ai_care"))
origin/release-candidate-ux:apps/api/app/services/care.py:153:def get_or_create_care_settings(db: Session, user: User) -> CareSettings:
origin/release-candidate-ux:apps/api/app/services/care.py:155:        db.query(CareSettings).filter(CareSettings.user_id == user.id).one_or_none()
origin/release-candidate-ux:apps/api/app/services/care.py:159:        row = CareSettings(
origin/release-candidate-ux:apps/api/app/services/care.py:165:            care_level="standard",
origin/release-candidate-ux:apps/api/app/services/care.py:174:    row: CareSettings, *, has_pro: bool
origin/release-candidate-ux:apps/api/app/services/care.py:175:) -> CareSettingsResponse:
origin/release-candidate-ux:apps/api/app/services/care.py:176:    return CareSettingsResponse(
origin/release-candidate-ux:apps/api/app/services/care.py:185:        care_level=row.care_level,  # type: ignore[arg-type]
origin/release-candidate-ux:apps/api/app/services/care.py:194:def get_care_settings(db: Session, user: User) -> CareSettingsResponse:
origin/release-candidate-ux:apps/api/app/services/care.py:195:    row = get_or_create_care_settings(db, user)
origin/release-candidate-ux:apps/api/app/services/care.py:199:def update_care_settings(
origin/release-candidate-ux:apps/api/app/services/care.py:200:    db: Session, user: User, payload: CareSettingsUpdate
origin/release-candidate-ux:apps/api/app/services/care.py:201:) -> CareSettingsResponse:
origin/release-candidate-ux:apps/api/app/services/care.py:202:    row = get_or_create_care_settings(db, user)
origin/release-candidate-ux:apps/api/app/services/care.py:204:    previous_level = row.care_level
origin/release-candidate-ux:apps/api/app/services/care.py:208:    if data.get("care_level") == "minimal" and previous_level != "minimal":
origin/release-candidate-ux:apps/api/app/services/care.py:224:def list_care_notifications(
origin/release-candidate-ux:apps/api/app/services/care.py:226:) -> list[CareNotificationResponse]:
origin/release-candidate-ux:apps/api/app/services/care.py:228:        db.query(CareNotification)
origin/release-candidate-ux:apps/api/app/services/care.py:229:        .filter(CareNotification.user_id == user.id)
origin/release-candidate-ux:apps/api/app/services/care.py:230:        .order_by(desc(CareNotification.created_at))
origin/release-candidate-ux:apps/api/app/services/care.py:235:        CareNotificationResponse(
origin/release-candidate-ux:apps/api/app/services/care.py:248:def _type_enabled(settings_row: CareSettings, notification_type: str) -> bool:
origin/release-candidate-ux:apps/api/app/services/care.py:261:def _level_allows_type(care_level: str, notification_type: str) -> bool:
origin/release-candidate-ux:apps/api/app/services/care.py:262:    if care_level == "minimal":
origin/release-candidate-ux:apps/api/app/services/care.py:264:    if care_level == "standard":
origin/release-candidate-ux:apps/api/app/services/care.py:269:def _cooldown_hours(care_level: str, notification_type: str) -> int:
origin/release-candidate-ux:apps/api/app/services/care.py:271:    return by_type.get(care_level, 24)
origin/release-candidate-ux:apps/api/app/services/care.py:278:        db.query(CareNotification)
origin/release-candidate-ux:apps/api/app/services/care.py:280:            CareNotification.user_id == user_id,
origin/release-candidate-ux:apps/api/app/services/care.py:281:            CareNotification.type == notification_type,
origin/release-candidate-ux:apps/api/app/services/care.py:282:            CareNotification.status == "sent",
origin/release-candidate-ux:apps/api/app/services/care.py:284:        .order_by(desc(CareNotification.sent_at))
origin/release-candidate-ux:apps/api/app/services/care.py:298:    settings_row = get_or_create_care_settings(db, user)
origin/release-candidate-ux:apps/api/app/services/care.py:302:    if not _level_allows_type(settings_row.care_level, notification_type):
origin/release-candidate-ux:apps/api/app/services/care.py:312:            hours = _cooldown_hours(settings_row.care_level, notification_type)
origin/release-candidate-ux:apps/api/app/services/care.py:319:def create_care_notification(
origin/release-candidate-ux:apps/api/app/services/care.py:329:) -> CareNotification:
origin/release-candidate-ux:apps/api/app/services/care.py:330:    template = CARE_TEMPLATES.get(notification_type, CARE_TEMPLATES["water"])
origin/release-candidate-ux:apps/api/app/services/care.py:331:    row = CareNotification(
origin/release-candidate-ux:apps/api/app/services/care.py:347:def log_care_event(
origin/release-candidate-ux:apps/api/app/services/care.py:352:    source: str = "care",
origin/release-candidate-ux:apps/api/app/services/care.py:355:) -> CareEvent:
origin/release-candidate-ux:apps/api/app/services/care.py:356:    event = CareEvent(
origin/release-candidate-ux:apps/api/app/services/care.py:369:async def send_telegram_care_notification(
origin/release-candidate-ux:apps/api/app/services/care.py:371:    notification: CareNotification,
origin/release-candidate-ux:apps/api/app/services/care.py:377:        logger.info("Care notification skipped: no telegram_id for user %s", user.id)
origin/release-candidate-ux:apps/api/app/services/care.py:380:    template = CARE_TEMPLATES.get(notification.type, {})
origin/release-candidate-ux:apps/api/app/services/care.py:400:    log_care_event(
origin/release-candidate-ux:apps/api/app/services/care.py:403:        f"care_{notification.type}_{'sent' if sent else 'failed'}",
origin/release-candidate-ux:apps/api/app/services/care.py:409:def build_care_context(db: Session, user: User) -> CareContext:
origin/release-candidate-ux:apps/api/app/services/care.py:412:    shopping = shopping_list_service.get_shopping_list(db, user, scope)
origin/release-candidate-ux:apps/api/app/services/care.py:428:    return CareContext(
origin/release-candidate-ux:apps/api/app/services/care.py:441:def generate_basic_care_tips(
origin/release-candidate-ux:apps/api/app/services/care.py:442:    db: Session, user: User, context: CareContext | None = None
origin/release-candidate-ux:apps/api/app/services/care.py:443:) -> list[CareTipPreview]:
origin/release-candidate-ux:apps/api/app/services/care.py:444:    ctx = context or build_care_context(db, user)
origin/release-candidate-ux:apps/api/app/services/care.py:445:    tips: list[CareTipPreview] = []
origin/release-candidate-ux:apps/api/app/services/care.py:448:        t = CARE_TEMPLATES["shopping"]
origin/release-candidate-ux:apps/api/app/services/care.py:450:            CareTipPreview(type="shopping", title=t["title"], message=t["message"])
origin/release-candidate-ux:apps/api/app/services/care.py:453:        t = CARE_TEMPLATES["pantry"]
origin/release-candidate-ux:apps/api/app/services/care.py:460:        tips.append(CareTipPreview(type="pantry", title=t["title"], message=msg))
origin/release-candidate-ux:apps/api/app/services/care.py:462:        t = CARE_TEMPLATES["menu"]
origin/release-candidate-ux:apps/api/app/services/care.py:463:        tips.append(CareTipPreview(type="menu", title=t["title"], message=t["message"]))
origin/release-candidate-ux:apps/api/app/services/care.py:465:        t = CARE_TEMPLATES["protein"]
origin/release-candidate-ux:apps/api/app/services/care.py:467:            CareTipPreview(type="protein", title=t["title"], message=t["message"])
origin/release-candidate-ux:apps/api/app/services/care.py:469:    t = CARE_TEMPLATES["water"]
origin/release-candidate-ux:apps/api/app/services/care.py:470:    tips.append(CareTipPreview(type="water", title=t["title"], message=t["message"]))
origin/release-candidate-ux:apps/api/app/services/care.py:472:        t = CARE_TEMPLATES["family"]
origin/release-candidate-ux:apps/api/app/services/care.py:473:        tips.append(CareTipPreview(type="family", title=t["title"], message=t["message"]))
origin/release-candidate-ux:apps/api/app/services/care.py:475:        t = CARE_TEMPLATES["pro"]
origin/release-candidate-ux:apps/api/app/services/care.py:476:        tips.append(CareTipPreview(type="pro", title=t["title"], message=t["message"]))
origin/release-candidate-ux:apps/api/app/services/care.py:481:async def send_care_notification_by_type(
origin/release-candidate-ux:apps/api/app/services/care.py:489:) -> tuple[bool, str, CareNotification | None]:
origin/release-candidate-ux:apps/api/app/services/care.py:499:    template = CARE_TEMPLATES[notification_type]
origin/release-candidate-ux:apps/api/app/services/care.py:500:    notification = create_care_notification(
origin/release-candidate-ux:apps/api/app/services/care.py:510:    sent = await send_telegram_care_notification(db, notification, user)
origin/release-candidate-ux:apps/api/app/services/care.py:527:    ctx = build_care_context(db, user)
origin/release-candidate-ux:apps/api/app/services/care.py:530:    await send_care_notification_by_type(db, user, "menu")
origin/release-candidate-ux:apps/api/app/services/care.py:533:async def process_care_reminders_for_user(db: Session, user: User) -> None:
origin/release-candidate-ux:apps/api/app/services/care.py:534:    """Send at most one contextual care tip per scheduler tick."""
origin/release-candidate-ux:apps/api/app/services/care.py:535:    settings_row = get_or_create_care_settings(db, user)
origin/release-candidate-ux:apps/api/app/services/care.py:536:    if settings_row.care_level == "minimal" and not any(
origin/release-candidate-ux:apps/api/app/services/care.py:545:    ctx = build_care_context(db, user)
origin/release-candidate-ux:apps/api/app/services/care.py:546:    tips = generate_basic_care_tips(db, user, ctx)
origin/release-candidate-ux:apps/api/app/services/care.py:550:            await send_care_notification_by_type(db, user, tip.type)
origin/release-candidate-ux:apps/api/app/services/care.py:554:async def process_all_care_reminders(db: Session) -> None:
origin/release-candidate-ux:apps/api/app/services/care.py:560:            await process_care_reminders_for_user(db, user)
origin/release-candidate-ux:apps/api/app/services/care.py:562:            logger.exception("Care reminder failed for user %s", user.id)
origin/release-candidate-ux:apps/api/app/services/event_plan.py:19:from app.schemas.menu import MenuIngredient
origin/release-candidate-ux:apps/api/app/services/event_plan.py:27:from app.services import shopping_list as shopping_list_service
origin/release-candidate-ux:apps/api/app/services/event_plan.py:194:    from app.schemas.menu import MenuVariant
origin/release-candidate-ux:apps/api/app/services/event_plan.py:197:        MenuIngredient(
origin/release-candidate-ux:apps/api/app/services/event_plan.py:205:    menu = MenuVariant(
origin/release-candidate-ux:apps/api/app/services/event_plan.py:213:    shopping_list_service.sync_from_menu(db, scope, menu, None)
origin/release-candidate-ux:apps/api/app/services/family.py:21:from app.schemas.nutrition_profile import NutritionProfileData, NutritionProData
origin/release-candidate-ux:apps/api/app/services/family.py:23:from app.services.nutrition_profile import save_nutrition_profile
origin/release-candidate-ux:apps/api/app/services/family.py:99:        nutrition_profile_complete=complete,
origin/release-candidate-ux:apps/api/app/services/family.py:226:        invited_phone_masked=mask_phone(invite.invited_phone_normalized),
```

## Keyword scan in origin/recipe-engine-v1

Hits (max 300): **300**

```
origin/recipe-engine-v1:apps/api/app/database.py:36:        shopping_list,
origin/recipe-engine-v1:apps/api/app/database.py:42:    from app.models import care as care_models  # noqa: F401
origin/recipe-engine-v1:apps/api/app/database.py:47:    # Legacy tables: SQLAlchemy create_all. Recipe Engine tables: SQL migrations only.
origin/recipe-engine-v1:apps/api/app/database_migrations.py:65:        "ALTER TABLE family_shopping_lists ADD COLUMN IF NOT EXISTS user_id INTEGER",
origin/recipe-engine-v1:apps/api/app/database_migrations.py:71:                WHERE conname = 'family_shopping_lists_user_id_fkey'
origin/recipe-engine-v1:apps/api/app/database_migrations.py:73:                ALTER TABLE family_shopping_lists
origin/recipe-engine-v1:apps/api/app/database_migrations.py:74:                ADD CONSTRAINT family_shopping_lists_user_id_fkey
origin/recipe-engine-v1:apps/api/app/database_migrations.py:79:        "ALTER TABLE family_shopping_lists ALTER COLUMN family_id DROP NOT NULL",
origin/recipe-engine-v1:apps/api/app/database_migrations.py:80:        "CREATE UNIQUE INDEX IF NOT EXISTS ix_family_shopping_lists_user_id ON family_shopping_lists (user_id)",
origin/recipe-engine-v1:apps/api/app/database_migrations.py:115:            invited_phone_normalized VARCHAR(32) NOT NULL,
origin/recipe-engine-v1:apps/api/app/database_migrations.py:127:        ON family_invites (family_id, invited_phone_normalized)
origin/recipe-engine-v1:apps/api/app/database_migrations.py:133:        ON family_invites (family_id, invited_phone_normalized)
origin/recipe-engine-v1:apps/api/app/database_migrations.py:134:        WHERE status = 'pending' AND invited_phone_normalized != '__link__';
origin/recipe-engine-v1:apps/api/app/database_migrations.py:178:        "ALTER TABLE family_members ADD COLUMN IF NOT EXISTS nutrition_profile JSONB NOT NULL DEFAULT '{}'",
origin/recipe-engine-v1:apps/api/app/database_migrations.py:253:        # AI Care System (stage 8)
origin/recipe-engine-v1:apps/api/app/database_migrations.py:255:        CREATE TABLE IF NOT EXISTS care_settings (
origin/recipe-engine-v1:apps/api/app/database_migrations.py:266:            care_level VARCHAR(16) NOT NULL DEFAULT 'standard',
origin/recipe-engine-v1:apps/api/app/database_migrations.py:275:        CREATE TABLE IF NOT EXISTS care_notifications (
origin/recipe-engine-v1:apps/api/app/database_migrations.py:289:        "CREATE INDEX IF NOT EXISTS ix_care_notifications_user_id ON care_notifications (user_id);",
origin/recipe-engine-v1:apps/api/app/database_migrations.py:291:        CREATE TABLE IF NOT EXISTS care_events (
origin/recipe-engine-v1:apps/api/app/database_migrations.py:296:            source VARCHAR(64) NOT NULL DEFAULT 'care',
origin/recipe-engine-v1:apps/api/app/database_migrations.py:301:        "CREATE INDEX IF NOT EXISTS ix_care_events_user_id ON care_events (user_id);",
origin/recipe-engine-v1:apps/api/app/database_migrations.py:762:    legacy_tables = [
origin/recipe-engine-v1:apps/api/app/database_migrations.py:775:                tables=legacy_tables,
origin/recipe-engine-v1:apps/api/app/main.py:17:    care,
origin/recipe-engine-v1:apps/api/app/main.py:24:    notifications,
origin/recipe-engine-v1:apps/api/app/main.py:25:    nutrition_profile,
origin/recipe-engine-v1:apps/api/app/main.py:33:    shopping_lists,
origin/recipe-engine-v1:apps/api/app/main.py:105:app.include_router(care.router)
origin/recipe-engine-v1:apps/api/app/main.py:109:app.include_router(nutrition_profile.router)
origin/recipe-engine-v1:apps/api/app/main.py:115:app.include_router(shopping_lists.router)
origin/recipe-engine-v1:apps/api/app/main.py:118:app.include_router(notifications.router)
origin/recipe-engine-v1:apps/api/app/models/__init__.py:2:from app.models.care import CareEvent, CareNotification, CareSettings
origin/recipe-engine-v1:apps/api/app/models/__init__.py:7:from app.models.notification_settings import UserNotificationSettings
origin/recipe-engine-v1:apps/api/app/models/__init__.py:11:from app.models.shopping_list import FamilyShoppingList
origin/recipe-engine-v1:apps/api/app/models/__init__.py:36:    "UserNotificationSettings",
origin/recipe-engine-v1:apps/api/app/models/__init__.py:45:    "CareSettings",
origin/recipe-engine-v1:apps/api/app/models/__init__.py:46:    "CareNotification",
origin/recipe-engine-v1:apps/api/app/models/__init__.py:47:    "CareEvent",
origin/recipe-engine-v1:apps/api/app/models/care.py:11:class CareSettings(Base):
origin/recipe-engine-v1:apps/api/app/models/care.py:12:    __tablename__ = "care_settings"
origin/recipe-engine-v1:apps/api/app/models/care.py:26:    care_level: Mapped[str] = mapped_column(String(16), default="standard")
origin/recipe-engine-v1:apps/api/app/models/care.py:37:    user = relationship("User", backref="care_settings")
origin/recipe-engine-v1:apps/api/app/models/care.py:40:class CareNotification(Base):
origin/recipe-engine-v1:apps/api/app/models/care.py:41:    __tablename__ = "care_notifications"
origin/recipe-engine-v1:apps/api/app/models/care.py:66:class CareEvent(Base):
origin/recipe-engine-v1:apps/api/app/models/care.py:67:    __tablename__ = "care_events"
origin/recipe-engine-v1:apps/api/app/models/care.py:77:    source: Mapped[str] = mapped_column(String(64), default="care")
origin/recipe-engine-v1:apps/api/app/models/family.py:60:    nutrition_profile: Mapped[dict] = mapped_column(JSONB, default=dict)
origin/recipe-engine-v1:apps/api/app/models/family_invite.py:24:    invited_phone_normalized: Mapped[str] = mapped_column(String(32), index=True)
origin/recipe-engine-v1:apps/api/app/models/notification_settings.py:9:class UserNotificationSettings(Base):
origin/recipe-engine-v1:apps/api/app/models/shopping_list.py:11:    __tablename__ = "family_shopping_lists"
origin/recipe-engine-v1:apps/api/app/models/user.py:64:        "UserNotificationSettings",
origin/recipe-engine-v1:apps/api/app/routers/care.py:7:from app.schemas.care import (
origin/recipe-engine-v1:apps/api/app/routers/care.py:8:    CareNotificationResponse,
origin/recipe-engine-v1:apps/api/app/routers/care.py:9:    CareSettingsResponse,
origin/recipe-engine-v1:apps/api/app/routers/care.py:10:    CareSettingsUpdate,
origin/recipe-engine-v1:apps/api/app/routers/care.py:11:    CareTipsResponse,
origin/recipe-engine-v1:apps/api/app/routers/care.py:12:    TestCareNotificationRequest,
origin/recipe-engine-v1:apps/api/app/routers/care.py:13:    TestCareNotificationResponse,
origin/recipe-engine-v1:apps/api/app/routers/care.py:15:from app.services import care as care_service
origin/recipe-engine-v1:apps/api/app/routers/care.py:17:router = APIRouter(prefix="/care", tags=["care"])
origin/recipe-engine-v1:apps/api/app/routers/care.py:20:@router.get("/settings", response_model=CareSettingsResponse)
origin/recipe-engine-v1:apps/api/app/routers/care.py:21:def get_care_settings(
origin/recipe-engine-v1:apps/api/app/routers/care.py:24:) -> CareSettingsResponse:
origin/recipe-engine-v1:apps/api/app/routers/care.py:25:    return care_service.get_care_settings(db, user)
origin/recipe-engine-v1:apps/api/app/routers/care.py:28:@router.patch("/settings", response_model=CareSettingsResponse)
origin/recipe-engine-v1:apps/api/app/routers/care.py:29:def patch_care_settings(
origin/recipe-engine-v1:apps/api/app/routers/care.py:30:    payload: CareSettingsUpdate,
origin/recipe-engine-v1:apps/api/app/routers/care.py:33:) -> CareSettingsResponse:
origin/recipe-engine-v1:apps/api/app/routers/care.py:34:    return care_service.update_care_settings(db, user, payload)
origin/recipe-engine-v1:apps/api/app/routers/care.py:37:@router.get("/notifications", response_model=list[CareNotificationResponse])
origin/recipe-engine-v1:apps/api/app/routers/care.py:38:def list_care_notifications(
origin/recipe-engine-v1:apps/api/app/routers/care.py:41:) -> list[CareNotificationResponse]:
origin/recipe-engine-v1:apps/api/app/routers/care.py:42:    return care_service.list_care_notifications(db, user)
origin/recipe-engine-v1:apps/api/app/routers/care.py:45:@router.get("/tips", response_model=CareTipsResponse)
origin/recipe-engine-v1:apps/api/app/routers/care.py:46:def preview_care_tips(
origin/recipe-engine-v1:apps/api/app/routers/care.py:49:) -> CareTipsResponse:
origin/recipe-engine-v1:apps/api/app/routers/care.py:50:    ctx = care_service.build_care_context(db, user)
origin/recipe-engine-v1:apps/api/app/routers/care.py:51:    return CareTipsResponse(tips=care_service.generate_basic_care_tips(db, user, ctx))
origin/recipe-engine-v1:apps/api/app/routers/care.py:54:@router.post("/test-notification", response_model=TestCareNotificationResponse)
origin/recipe-engine-v1:apps/api/app/routers/care.py:56:    payload: TestCareNotificationRequest,
origin/recipe-engine-v1:apps/api/app/routers/care.py:59:) -> TestCareNotificationResponse:
origin/recipe-engine-v1:apps/api/app/routers/care.py:60:    ok, message, notification = await care_service.send_care_notification_by_type(
origin/recipe-engine-v1:apps/api/app/routers/care.py:67:    return TestCareNotificationResponse(
origin/recipe-engine-v1:apps/api/app/routers/event_plans.py:50:def create_event_shopping_list(
origin/recipe-engine-v1:apps/api/app/routers/families.py:53:        invited_phone_masked=mask_phone(invite.invited_phone_normalized),
origin/recipe-engine-v1:apps/api/app/routers/families.py:188:            invited_phone_masked=mask_phone(inv.invited_phone_normalized),
origin/recipe-engine-v1:apps/api/app/routers/menus.py:13:    MenuVariant,
origin/recipe-engine-v1:apps/api/app/routers/menus.py:25:from app.services import care as care_service
origin/recipe-engine-v1:apps/api/app/routers/menus.py:32:async def _send_menu_care_notification(user_id: int) -> None:
origin/recipe-engine-v1:apps/api/app/routers/menus.py:37:            await care_service.maybe_notify_menu_ready(db, user)
origin/recipe-engine-v1:apps/api/app/routers/menus.py:39:        logger.exception("Menu care notification failed for user %s", user_id)
origin/recipe-engine-v1:apps/api/app/routers/menus.py:56:@router.post("/replace-dish", response_model=MenuVariant)
origin/recipe-engine-v1:apps/api/app/routers/menus.py:62:) -> MenuVariant:
origin/recipe-engine-v1:apps/api/app/routers/menus.py:75:    background_tasks.add_task(_send_menu_care_notification, user.id)
origin/recipe-engine-v1:apps/api/app/routers/notifications.py:7:from app.schemas.notifications import (
origin/recipe-engine-v1:apps/api/app/routers/notifications.py:8:    NotificationSettingsResponse,
origin/recipe-engine-v1:apps/api/app/routers/notifications.py:9:    NotificationSettingsUpdate,
origin/recipe-engine-v1:apps/api/app/routers/notifications.py:11:from app.services import notifications as notifications_service
origin/recipe-engine-v1:apps/api/app/routers/notifications.py:13:router = APIRouter(prefix="/notifications", tags=["notifications"])
origin/recipe-engine-v1:apps/api/app/routers/notifications.py:16:@router.get("/settings", response_model=NotificationSettingsResponse)
origin/recipe-engine-v1:apps/api/app/routers/notifications.py:20:) -> NotificationSettingsResponse:
origin/recipe-engine-v1:apps/api/app/routers/notifications.py:21:    return notifications_service.get_settings(db, user)
origin/recipe-engine-v1:apps/api/app/routers/notifications.py:24:@router.put("/settings", response_model=NotificationSettingsResponse)
origin/recipe-engine-v1:apps/api/app/routers/notifications.py:26:    payload: NotificationSettingsUpdate,
origin/recipe-engine-v1:apps/api/app/routers/notifications.py:29:) -> NotificationSettingsResponse:
origin/recipe-engine-v1:apps/api/app/routers/notifications.py:30:    return notifications_service.update_settings(db, user, payload)
origin/recipe-engine-v1:apps/api/app/routers/nutrition_profile.py:7:from app.schemas.nutrition_profile import NutritionProfileData, NutritionProfileResponse
origin/recipe-engine-v1:apps/api/app/routers/nutrition_profile.py:8:from app.services.nutrition_profile import (
origin/recipe-engine-v1:apps/api/app/routers/nutrition_profile.py:9:    migrate_legacy_profile,
origin/recipe-engine-v1:apps/api/app/routers/nutrition_profile.py:12:    save_nutrition_profile,
origin/recipe-engine-v1:apps/api/app/routers/nutrition_profile.py:32:def get_nutrition_profile(
origin/recipe-engine-v1:apps/api/app/routers/nutrition_profile.py:37:    migrate_legacy_profile(db, profile)
origin/recipe-engine-v1:apps/api/app/routers/nutrition_profile.py:43:def save_nutrition_profile_endpoint(
origin/recipe-engine-v1:apps/api/app/routers/nutrition_profile.py:54:    profile = save_nutrition_profile(db, user, payload)
origin/recipe-engine-v1:apps/api/app/routers/recipes.py:18:from app.schemas.menu import MenuVariant
origin/recipe-engine-v1:apps/api/app/routers/recipes.py:112:def _normalized_ingredient_name(name: str) -> str:
origin/recipe-engine-v1:apps/api/app/routers/recipes.py:117:    normalized = _normalized_ingredient_name(name)
origin/recipe-engine-v1:apps/api/app/routers/recipes.py:118:    if not normalized:
origin/recipe-engine-v1:apps/api/app/routers/recipes.py:121:        item == normalized or item in normalized or normalized in item
origin/recipe-engine-v1:apps/api/app/routers/recipes.py:244:        _normalized_ingredient_name(item.name)
origin/recipe-engine-v1:apps/api/app/routers/recipes.py:540:@router.post("/{recipe_id}/add-to-menu", response_model=MenuVariant)
origin/recipe-engine-v1:apps/api/app/routers/recipes.py:547:) -> MenuVariant:
origin/recipe-engine-v1:apps/api/app/routers/shopping_lists.py:9:from app.schemas.shopping_list import (
origin/recipe-engine-v1:apps/api/app/routers/shopping_lists.py:16:from app.services import shopping_list as shopping_list_service
origin/recipe-engine-v1:apps/api/app/routers/shopping_lists.py:23:def get_my_shopping_list(
origin/recipe-engine-v1:apps/api/app/routers/shopping_lists.py:28:    result = shopping_list_service.get_shopping_list(db, user, scope)
origin/recipe-engine-v1:apps/api/app/routers/shopping_lists.py:38:def sync_shopping_list(
origin/recipe-engine-v1:apps/api/app/routers/shopping_lists.py:42:    return shopping_list_service.sync_shopping_list_for_scope(db, scope)
origin/recipe-engine-v1:apps/api/app/routers/shopping_lists.py:56:    return shopping_list_service.create_item(db, user, scope, payload)
origin/recipe-engine-v1:apps/api/app/routers/shopping_lists.py:68:        return shopping_list_service.toggle_item(
origin/recipe-engine-v1:apps/api/app/routers/shopping_lists.py:76:    return shopping_list_service.update_item(db, user, scope, item_id, payload)
origin/recipe-engine-v1:apps/api/app/routers/shopping_lists.py:86:    return shopping_list_service.delete_item(db, user, scope, item_id)
origin/recipe-engine-v1:apps/api/app/routers/shopping_lists.py:97:    return shopping_list_service.toggle_item(
origin/recipe-engine-v1:apps/api/app/schemas/care.py:6:CareLevel = Literal["minimal", "standard", "active"]
origin/recipe-engine-v1:apps/api/app/schemas/care.py:7:CareNotificationType = Literal[
origin/recipe-engine-v1:apps/api/app/schemas/care.py:19:class CareSettingsResponse(BaseModel):
origin/recipe-engine-v1:apps/api/app/schemas/care.py:28:    care_level: CareLevel
origin/recipe-engine-v1:apps/api/app/schemas/care.py:36:class CareSettingsUpdate(BaseModel):
origin/recipe-engine-v1:apps/api/app/schemas/care.py:45:    care_level: CareLevel | None = None
origin/recipe-engine-v1:apps/api/app/schemas/care.py:51:class CareNotificationResponse(BaseModel):
origin/recipe-engine-v1:apps/api/app/schemas/care.py:61:class TestCareNotificationRequest(BaseModel):
origin/recipe-engine-v1:apps/api/app/schemas/care.py:62:    notification_type: CareNotificationType = "water"
origin/recipe-engine-v1:apps/api/app/schemas/care.py:65:class TestCareNotificationResponse(BaseModel):
origin/recipe-engine-v1:apps/api/app/schemas/care.py:71:class CareTipPreview(BaseModel):
origin/recipe-engine-v1:apps/api/app/schemas/care.py:77:class CareTipsResponse(BaseModel):
origin/recipe-engine-v1:apps/api/app/schemas/care.py:78:    tips: list[CareTipPreview]
origin/recipe-engine-v1:apps/api/app/schemas/family.py:56:    nutrition_profile_complete: bool = False
origin/recipe-engine-v1:apps/api/app/schemas/family_member_nutrition.py:5:from app.services.member_age import MAX_AGE_MONTHS, normalize_age_months, validate_age_months
origin/recipe-engine-v1:apps/api/app/schemas/family_member_nutrition.py:9:    """Stored in family_members.nutrition_profile JSON."""
origin/recipe-engine-v1:apps/api/app/schemas/family_member_nutrition.py:22:    # Legacy fields (read/write compat)
origin/recipe-engine-v1:apps/api/app/schemas/family_member_nutrition.py:29:    def migrate_legacy_age(cls, data):
origin/recipe-engine-v1:apps/api/app/schemas/family_member_nutrition.py:33:            resolved = normalize_age_months(
origin/recipe-engine-v1:apps/api/app/schemas/menu.py:6:MenuVariantType = Literal["quick", "economy", "balanced"]
origin/recipe-engine-v1:apps/api/app/schemas/menu.py:26:class MenuIngredient(BaseModel):
origin/recipe-engine-v1:apps/api/app/schemas/menu.py:32:class MenuVariant(BaseModel):
origin/recipe-engine-v1:apps/api/app/schemas/menu.py:33:    variant: MenuVariantType
origin/recipe-engine-v1:apps/api/app/schemas/menu.py:40:    ingredients: list[MenuIngredient] = Field(min_length=1)
origin/recipe-engine-v1:apps/api/app/schemas/menu.py:46:    menus: list[MenuVariant] = Field(min_length=3, max_length=3)
origin/recipe-engine-v1:apps/api/app/schemas/menu.py:55:    menu: MenuVariant
origin/recipe-engine-v1:apps/api/app/schemas/menu.py:80:    menu: MenuVariant
origin/recipe-engine-v1:apps/api/app/schemas/menu.py:88:    variant: MenuVariantType
origin/recipe-engine-v1:apps/api/app/schemas/menu.py:89:    menu: MenuVariant
origin/recipe-engine-v1:apps/api/app/schemas/menu_overview.py:6:from app.schemas.menu import MenuVariant, SelectedMenuResponse
origin/recipe-engine-v1:apps/api/app/schemas/notifications.py:10:class NotificationSettingsResponse(BaseModel):
origin/recipe-engine-v1:apps/api/app/schemas/notifications.py:25:class NotificationSettingsUpdate(BaseModel):
origin/recipe-engine-v1:apps/api/app/schemas/subscription.py:10:    notifications: bool = True
origin/recipe-engine-v1:apps/api/app/schemas/subscription.py:11:    nutrition_profile: bool = True
origin/recipe-engine-v1:apps/api/app/schemas/subscription.py:18:    ai_care: bool = False
origin/recipe-engine-v1:apps/api/app/services/admin_errors.py:1:"""Admin error logging to database (and legacy file fallback)."""
origin/recipe-engine-v1:apps/api/app/services/ai.py:20:    MenuIngredient,
origin/recipe-engine-v1:apps/api/app/services/ai.py:22:    MenuVariant,
origin/recipe-engine-v1:apps/api/app/services/ai.py:23:    MenuVariantType,
origin/recipe-engine-v1:apps/api/app/services/ai.py:52:MenuVariantKey = Literal["quick", "economy", "balanced"]
origin/recipe-engine-v1:apps/api/app/services/ai.py:131:    menus: list[MenuVariant]
origin/recipe-engine-v1:apps/api/app/services/ai.py:204:def _menu_variants_from_ai(data: dict[str, Any]) -> list[MenuVariant]:
origin/recipe-engine-v1:apps/api/app/services/ai.py:224:    menus: list[MenuVariant] = []
origin/recipe-engine-v1:apps/api/app/services/ai.py:260:                MenuVariant(
origin/recipe-engine-v1:apps/api/app/services/ai.py:273:                        MenuIngredient(name="Вода", amount="1 л", category="drinks")
origin/recipe-engine-v1:apps/api/app/services/ai.py:343:def _ingredients_from_ai_rows(rows: list[dict]) -> list[MenuIngredient]:
origin/recipe-engine-v1:apps/api/app/services/ai.py:364:        MenuIngredient(
origin/recipe-engine-v1:apps/api/app/services/amount_parser.py:29:def normalize_unit(raw: str) -> str:
origin/recipe-engine-v1:apps/api/app/services/amount_parser.py:47:        return None, normalize_unit(text)
origin/recipe-engine-v1:apps/api/app/services/amount_parser.py:53:        return None, normalize_unit(text)
origin/recipe-engine-v1:apps/api/app/services/amount_parser.py:55:    unit = normalize_unit(unit_raw) if unit_raw else "шт"
origin/recipe-engine-v1:apps/api/app/services/bot_input.py:14:from app.schemas.shopping_list import ShoppingItemCreateRequest, ShoppingItemUpdateRequest
origin/recipe-engine-v1:apps/api/app/services/bot_input.py:16:from app.services import shopping_list as shopping_service
origin/recipe-engine-v1:apps/api/app/services/bot_input.py:62:def _normalize_match(name: str) -> str:
origin/recipe-engine-v1:apps/api/app/services/bot_input.py:169:    listing = shopping_service.get_shopping_list(db, user, scope)
origin/recipe-engine-v1:apps/api/app/services/bot_input.py:170:    key = _normalize_match(name)
origin/recipe-engine-v1:apps/api/app/services/bot_input.py:172:        if _normalize_match(item.name) == key and not item.checked:
origin/recipe-engine-v1:apps/api/app/services/bot_today.py:10:from app.services import shopping_list as shopping_service
origin/recipe-engine-v1:apps/api/app/services/bot_today.py:22:    shopping = shopping_service.get_shopping_list(db, user, scope)
origin/recipe-engine-v1:apps/api/app/services/care.py:13:from app.models.care import CareEvent, CareNotification, CareSettings
origin/recipe-engine-v1:apps/api/app/services/care.py:15:from app.schemas.care import (
origin/recipe-engine-v1:apps/api/app/services/care.py:16:    CareNotificationResponse,
origin/recipe-engine-v1:apps/api/app/services/care.py:17:    CareSettingsResponse,
origin/recipe-engine-v1:apps/api/app/services/care.py:18:    CareSettingsUpdate,
origin/recipe-engine-v1:apps/api/app/services/care.py:19:    CareTipPreview,
origin/recipe-engine-v1:apps/api/app/services/care.py:24:from app.services.notifications import get_or_create_settings as get_notif_settings_row
origin/recipe-engine-v1:apps/api/app/services/care.py:27:from app.services import shopping_list as shopping_list_service
origin/recipe-engine-v1:apps/api/app/services/care.py:32:CareLevel = str
origin/recipe-engine-v1:apps/api/app/services/care.py:40:COOLDOWN_HOURS: dict[str, dict[CareLevel, int]] = {
origin/recipe-engine-v1:apps/api/app/services/care.py:51:CARE_TEMPLATES: dict[str, dict[str, str]] = {
origin/recipe-engine-v1:apps/api/app/services/care.py:104:class CareContext:
origin/recipe-engine-v1:apps/api/app/services/care.py:116:def _user_timezone(settings_row: CareSettings, user: User, db: Session) -> str:
origin/recipe-engine-v1:apps/api/app/services/care.py:130:def _is_quiet_hours(settings_row: CareSettings, user: User, db: Session) -> bool:
origin/recipe-engine-v1:apps/api/app/services/care.py:148:        return bool(features.get("ai_care"))
origin/recipe-engine-v1:apps/api/app/services/care.py:153:def get_or_create_care_settings(db: Session, user: User) -> CareSettings:
origin/recipe-engine-v1:apps/api/app/services/care.py:155:        db.query(CareSettings).filter(CareSettings.user_id == user.id).one_or_none()
origin/recipe-engine-v1:apps/api/app/services/care.py:159:        row = CareSettings(
origin/recipe-engine-v1:apps/api/app/services/care.py:165:            care_level="standard",
origin/recipe-engine-v1:apps/api/app/services/care.py:174:    row: CareSettings, *, has_pro: bool
origin/recipe-engine-v1:apps/api/app/services/care.py:175:) -> CareSettingsResponse:
origin/recipe-engine-v1:apps/api/app/services/care.py:176:    return CareSettingsResponse(
origin/recipe-engine-v1:apps/api/app/services/care.py:185:        care_level=row.care_level,  # type: ignore[arg-type]
origin/recipe-engine-v1:apps/api/app/services/care.py:194:def get_care_settings(db: Session, user: User) -> CareSettingsResponse:
origin/recipe-engine-v1:apps/api/app/services/care.py:195:    row = get_or_create_care_settings(db, user)
origin/recipe-engine-v1:apps/api/app/services/care.py:199:def update_care_settings(
origin/recipe-engine-v1:apps/api/app/services/care.py:200:    db: Session, user: User, payload: CareSettingsUpdate
origin/recipe-engine-v1:apps/api/app/services/care.py:201:) -> CareSettingsResponse:
origin/recipe-engine-v1:apps/api/app/services/care.py:202:    row = get_or_create_care_settings(db, user)
origin/recipe-engine-v1:apps/api/app/services/care.py:204:    previous_level = row.care_level
origin/recipe-engine-v1:apps/api/app/services/care.py:208:    if data.get("care_level") == "minimal" and previous_level != "minimal":
origin/recipe-engine-v1:apps/api/app/services/care.py:224:def list_care_notifications(
origin/recipe-engine-v1:apps/api/app/services/care.py:226:) -> list[CareNotificationResponse]:
origin/recipe-engine-v1:apps/api/app/services/care.py:228:        db.query(CareNotification)
origin/recipe-engine-v1:apps/api/app/services/care.py:229:        .filter(CareNotification.user_id == user.id)
origin/recipe-engine-v1:apps/api/app/services/care.py:230:        .order_by(desc(CareNotification.created_at))
origin/recipe-engine-v1:apps/api/app/services/care.py:235:        CareNotificationResponse(
origin/recipe-engine-v1:apps/api/app/services/care.py:248:def _type_enabled(settings_row: CareSettings, notification_type: str) -> bool:
origin/recipe-engine-v1:apps/api/app/services/care.py:261:def _level_allows_type(care_level: str, notification_type: str) -> bool:
origin/recipe-engine-v1:apps/api/app/services/care.py:262:    if care_level == "minimal":
origin/recipe-engine-v1:apps/api/app/services/care.py:264:    if care_level == "standard":
origin/recipe-engine-v1:apps/api/app/services/care.py:269:def _cooldown_hours(care_level: str, notification_type: str) -> int:
origin/recipe-engine-v1:apps/api/app/services/care.py:271:    return by_type.get(care_level, 24)
origin/recipe-engine-v1:apps/api/app/services/care.py:278:        db.query(CareNotification)
origin/recipe-engine-v1:apps/api/app/services/care.py:280:            CareNotification.user_id == user_id,
origin/recipe-engine-v1:apps/api/app/services/care.py:281:            CareNotification.type == notification_type,
origin/recipe-engine-v1:apps/api/app/services/care.py:282:            CareNotification.status == "sent",
origin/recipe-engine-v1:apps/api/app/services/care.py:284:        .order_by(desc(CareNotification.sent_at))
origin/recipe-engine-v1:apps/api/app/services/care.py:298:    settings_row = get_or_create_care_settings(db, user)
origin/recipe-engine-v1:apps/api/app/services/care.py:302:    if not _level_allows_type(settings_row.care_level, notification_type):
origin/recipe-engine-v1:apps/api/app/services/care.py:312:            hours = _cooldown_hours(settings_row.care_level, notification_type)
origin/recipe-engine-v1:apps/api/app/services/care.py:319:def create_care_notification(
origin/recipe-engine-v1:apps/api/app/services/care.py:329:) -> CareNotification:
origin/recipe-engine-v1:apps/api/app/services/care.py:330:    template = CARE_TEMPLATES.get(notification_type, CARE_TEMPLATES["water"])
origin/recipe-engine-v1:apps/api/app/services/care.py:331:    row = CareNotification(
origin/recipe-engine-v1:apps/api/app/services/care.py:347:def log_care_event(
origin/recipe-engine-v1:apps/api/app/services/care.py:352:    source: str = "care",
origin/recipe-engine-v1:apps/api/app/services/care.py:355:) -> CareEvent:
origin/recipe-engine-v1:apps/api/app/services/care.py:356:    event = CareEvent(
origin/recipe-engine-v1:apps/api/app/services/care.py:369:async def send_telegram_care_notification(
origin/recipe-engine-v1:apps/api/app/services/care.py:371:    notification: CareNotification,
origin/recipe-engine-v1:apps/api/app/services/care.py:377:        logger.info("Care notification skipped: no telegram_id for user %s", user.id)
origin/recipe-engine-v1:apps/api/app/services/care.py:380:    template = CARE_TEMPLATES.get(notification.type, {})
origin/recipe-engine-v1:apps/api/app/services/care.py:400:    log_care_event(
origin/recipe-engine-v1:apps/api/app/services/care.py:403:        f"care_{notification.type}_{'sent' if sent else 'failed'}",
origin/recipe-engine-v1:apps/api/app/services/care.py:409:def build_care_context(db: Session, user: User) -> CareContext:
origin/recipe-engine-v1:apps/api/app/services/care.py:412:    shopping = shopping_list_service.get_shopping_list(db, user, scope)
origin/recipe-engine-v1:apps/api/app/services/care.py:428:    return CareContext(
origin/recipe-engine-v1:apps/api/app/services/care.py:441:def generate_basic_care_tips(
origin/recipe-engine-v1:apps/api/app/services/care.py:442:    db: Session, user: User, context: CareContext | None = None
origin/recipe-engine-v1:apps/api/app/services/care.py:443:) -> list[CareTipPreview]:
origin/recipe-engine-v1:apps/api/app/services/care.py:444:    ctx = context or build_care_context(db, user)
origin/recipe-engine-v1:apps/api/app/services/care.py:445:    tips: list[CareTipPreview] = []
origin/recipe-engine-v1:apps/api/app/services/care.py:448:        t = CARE_TEMPLATES["shopping"]
origin/recipe-engine-v1:apps/api/app/services/care.py:450:            CareTipPreview(type="shopping", title=t["title"], message=t["message"])
origin/recipe-engine-v1:apps/api/app/services/care.py:453:        t = CARE_TEMPLATES["pantry"]
origin/recipe-engine-v1:apps/api/app/services/care.py:460:        tips.append(CareTipPreview(type="pantry", title=t["title"], message=msg))
origin/recipe-engine-v1:apps/api/app/services/care.py:462:        t = CARE_TEMPLATES["menu"]
origin/recipe-engine-v1:apps/api/app/services/care.py:463:        tips.append(CareTipPreview(type="menu", title=t["title"], message=t["message"]))
origin/recipe-engine-v1:apps/api/app/services/care.py:465:        t = CARE_TEMPLATES["protein"]
origin/recipe-engine-v1:apps/api/app/services/care.py:467:            CareTipPreview(type="protein", title=t["title"], message=t["message"])
origin/recipe-engine-v1:apps/api/app/services/care.py:469:    t = CARE_TEMPLATES["water"]
origin/recipe-engine-v1:apps/api/app/services/care.py:470:    tips.append(CareTipPreview(type="water", title=t["title"], message=t["message"]))
origin/recipe-engine-v1:apps/api/app/services/care.py:472:        t = CARE_TEMPLATES["family"]
origin/recipe-engine-v1:apps/api/app/services/care.py:473:        tips.append(CareTipPreview(type="family", title=t["title"], message=t["message"]))
origin/recipe-engine-v1:apps/api/app/services/care.py:475:        t = CARE_TEMPLATES["pro"]
origin/recipe-engine-v1:apps/api/app/services/care.py:476:        tips.append(CareTipPreview(type="pro", title=t["title"], message=t["message"]))
origin/recipe-engine-v1:apps/api/app/services/care.py:481:async def send_care_notification_by_type(
origin/recipe-engine-v1:apps/api/app/services/care.py:489:) -> tuple[bool, str, CareNotification | None]:
origin/recipe-engine-v1:apps/api/app/services/care.py:499:    template = CARE_TEMPLATES[notification_type]
origin/recipe-engine-v1:apps/api/app/services/care.py:500:    notification = create_care_notification(
origin/recipe-engine-v1:apps/api/app/services/care.py:510:    sent = await send_telegram_care_notification(db, notification, user)
origin/recipe-engine-v1:apps/api/app/services/care.py:527:    ctx = build_care_context(db, user)
origin/recipe-engine-v1:apps/api/app/services/care.py:530:    await send_care_notification_by_type(db, user, "menu")
origin/recipe-engine-v1:apps/api/app/services/care.py:533:async def process_care_reminders_for_user(db: Session, user: User) -> None:
origin/recipe-engine-v1:apps/api/app/services/care.py:534:    """Send at most one contextual care tip per scheduler tick."""
origin/recipe-engine-v1:apps/api/app/services/care.py:535:    settings_row = get_or_create_care_settings(db, user)
origin/recipe-engine-v1:apps/api/app/services/care.py:536:    if settings_row.care_level == "minimal" and not any(
origin/recipe-engine-v1:apps/api/app/services/care.py:545:    ctx = build_care_context(db, user)
origin/recipe-engine-v1:apps/api/app/services/care.py:546:    tips = generate_basic_care_tips(db, user, ctx)
origin/recipe-engine-v1:apps/api/app/services/care.py:550:            await send_care_notification_by_type(db, user, tip.type)
origin/recipe-engine-v1:apps/api/app/services/care.py:554:async def process_all_care_reminders(db: Session) -> None:
origin/recipe-engine-v1:apps/api/app/services/care.py:560:            await process_care_reminders_for_user(db, user)
origin/recipe-engine-v1:apps/api/app/services/care.py:562:            logger.exception("Care reminder failed for user %s", user.id)
origin/recipe-engine-v1:apps/api/app/services/event_plan.py:19:from app.schemas.menu import MenuIngredient
origin/recipe-engine-v1:apps/api/app/services/event_plan.py:27:from app.services import shopping_list as shopping_list_service
```

## Keyword scan in origin/recipe-import-pipeline-v1

Hits (max 300): **300**

```
origin/recipe-import-pipeline-v1:apps/api/app/database.py:36:        shopping_list,
origin/recipe-import-pipeline-v1:apps/api/app/database.py:42:    from app.models import care as care_models  # noqa: F401
origin/recipe-import-pipeline-v1:apps/api/app/database.py:47:    # Legacy tables: SQLAlchemy create_all. Recipe Engine tables: SQL migrations only.
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:65:        "ALTER TABLE family_shopping_lists ADD COLUMN IF NOT EXISTS user_id INTEGER",
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:71:                WHERE conname = 'family_shopping_lists_user_id_fkey'
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:73:                ALTER TABLE family_shopping_lists
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:74:                ADD CONSTRAINT family_shopping_lists_user_id_fkey
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:79:        "ALTER TABLE family_shopping_lists ALTER COLUMN family_id DROP NOT NULL",
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:80:        "CREATE UNIQUE INDEX IF NOT EXISTS ix_family_shopping_lists_user_id ON family_shopping_lists (user_id)",
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:115:            invited_phone_normalized VARCHAR(32) NOT NULL,
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:127:        ON family_invites (family_id, invited_phone_normalized)
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:133:        ON family_invites (family_id, invited_phone_normalized)
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:134:        WHERE status = 'pending' AND invited_phone_normalized != '__link__';
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:178:        "ALTER TABLE family_members ADD COLUMN IF NOT EXISTS nutrition_profile JSONB NOT NULL DEFAULT '{}'",
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:253:        # AI Care System (stage 8)
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:255:        CREATE TABLE IF NOT EXISTS care_settings (
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:266:            care_level VARCHAR(16) NOT NULL DEFAULT 'standard',
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:275:        CREATE TABLE IF NOT EXISTS care_notifications (
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:289:        "CREATE INDEX IF NOT EXISTS ix_care_notifications_user_id ON care_notifications (user_id);",
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:291:        CREATE TABLE IF NOT EXISTS care_events (
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:296:            source VARCHAR(64) NOT NULL DEFAULT 'care',
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:301:        "CREATE INDEX IF NOT EXISTS ix_care_events_user_id ON care_events (user_id);",
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:853:    legacy_tables = [
origin/recipe-import-pipeline-v1:apps/api/app/database_migrations.py:866:                tables=legacy_tables,
origin/recipe-import-pipeline-v1:apps/api/app/main.py:17:    care,
origin/recipe-import-pipeline-v1:apps/api/app/main.py:24:    notifications,
origin/recipe-import-pipeline-v1:apps/api/app/main.py:25:    nutrition_profile,
origin/recipe-import-pipeline-v1:apps/api/app/main.py:33:    shopping_lists,
origin/recipe-import-pipeline-v1:apps/api/app/main.py:105:app.include_router(care.router)
origin/recipe-import-pipeline-v1:apps/api/app/main.py:109:app.include_router(nutrition_profile.router)
origin/recipe-import-pipeline-v1:apps/api/app/main.py:115:app.include_router(shopping_lists.router)
origin/recipe-import-pipeline-v1:apps/api/app/main.py:118:app.include_router(notifications.router)
origin/recipe-import-pipeline-v1:apps/api/app/models/__init__.py:2:from app.models.care import CareEvent, CareNotification, CareSettings
origin/recipe-import-pipeline-v1:apps/api/app/models/__init__.py:7:from app.models.notification_settings import UserNotificationSettings
origin/recipe-import-pipeline-v1:apps/api/app/models/__init__.py:11:from app.models.shopping_list import FamilyShoppingList
origin/recipe-import-pipeline-v1:apps/api/app/models/__init__.py:36:    "UserNotificationSettings",
origin/recipe-import-pipeline-v1:apps/api/app/models/__init__.py:45:    "CareSettings",
origin/recipe-import-pipeline-v1:apps/api/app/models/__init__.py:46:    "CareNotification",
origin/recipe-import-pipeline-v1:apps/api/app/models/__init__.py:47:    "CareEvent",
origin/recipe-import-pipeline-v1:apps/api/app/models/care.py:11:class CareSettings(Base):
origin/recipe-import-pipeline-v1:apps/api/app/models/care.py:12:    __tablename__ = "care_settings"
origin/recipe-import-pipeline-v1:apps/api/app/models/care.py:26:    care_level: Mapped[str] = mapped_column(String(16), default="standard")
origin/recipe-import-pipeline-v1:apps/api/app/models/care.py:37:    user = relationship("User", backref="care_settings")
origin/recipe-import-pipeline-v1:apps/api/app/models/care.py:40:class CareNotification(Base):
origin/recipe-import-pipeline-v1:apps/api/app/models/care.py:41:    __tablename__ = "care_notifications"
origin/recipe-import-pipeline-v1:apps/api/app/models/care.py:66:class CareEvent(Base):
origin/recipe-import-pipeline-v1:apps/api/app/models/care.py:67:    __tablename__ = "care_events"
origin/recipe-import-pipeline-v1:apps/api/app/models/care.py:77:    source: Mapped[str] = mapped_column(String(64), default="care")
origin/recipe-import-pipeline-v1:apps/api/app/models/family.py:60:    nutrition_profile: Mapped[dict] = mapped_column(JSONB, default=dict)
origin/recipe-import-pipeline-v1:apps/api/app/models/family_invite.py:24:    invited_phone_normalized: Mapped[str] = mapped_column(String(32), index=True)
origin/recipe-import-pipeline-v1:apps/api/app/models/notification_settings.py:9:class UserNotificationSettings(Base):
origin/recipe-import-pipeline-v1:apps/api/app/models/shopping_list.py:11:    __tablename__ = "family_shopping_lists"
origin/recipe-import-pipeline-v1:apps/api/app/models/user.py:64:        "UserNotificationSettings",
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:7:from app.schemas.care import (
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:8:    CareNotificationResponse,
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:9:    CareSettingsResponse,
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:10:    CareSettingsUpdate,
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:11:    CareTipsResponse,
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:12:    TestCareNotificationRequest,
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:13:    TestCareNotificationResponse,
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:15:from app.services import care as care_service
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:17:router = APIRouter(prefix="/care", tags=["care"])
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:20:@router.get("/settings", response_model=CareSettingsResponse)
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:21:def get_care_settings(
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:24:) -> CareSettingsResponse:
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:25:    return care_service.get_care_settings(db, user)
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:28:@router.patch("/settings", response_model=CareSettingsResponse)
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:29:def patch_care_settings(
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:30:    payload: CareSettingsUpdate,
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:33:) -> CareSettingsResponse:
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:34:    return care_service.update_care_settings(db, user, payload)
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:37:@router.get("/notifications", response_model=list[CareNotificationResponse])
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:38:def list_care_notifications(
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:41:) -> list[CareNotificationResponse]:
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:42:    return care_service.list_care_notifications(db, user)
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:45:@router.get("/tips", response_model=CareTipsResponse)
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:46:def preview_care_tips(
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:49:) -> CareTipsResponse:
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:50:    ctx = care_service.build_care_context(db, user)
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:51:    return CareTipsResponse(tips=care_service.generate_basic_care_tips(db, user, ctx))
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:54:@router.post("/test-notification", response_model=TestCareNotificationResponse)
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:56:    payload: TestCareNotificationRequest,
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:59:) -> TestCareNotificationResponse:
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:60:    ok, message, notification = await care_service.send_care_notification_by_type(
origin/recipe-import-pipeline-v1:apps/api/app/routers/care.py:67:    return TestCareNotificationResponse(
origin/recipe-import-pipeline-v1:apps/api/app/routers/event_plans.py:50:def create_event_shopping_list(
origin/recipe-import-pipeline-v1:apps/api/app/routers/families.py:53:        invited_phone_masked=mask_phone(invite.invited_phone_normalized),
origin/recipe-import-pipeline-v1:apps/api/app/routers/families.py:188:            invited_phone_masked=mask_phone(inv.invited_phone_normalized),
origin/recipe-import-pipeline-v1:apps/api/app/routers/menus.py:13:    MenuVariant,
origin/recipe-import-pipeline-v1:apps/api/app/routers/menus.py:25:from app.services import care as care_service
origin/recipe-import-pipeline-v1:apps/api/app/routers/menus.py:32:async def _send_menu_care_notification(user_id: int) -> None:
origin/recipe-import-pipeline-v1:apps/api/app/routers/menus.py:37:            await care_service.maybe_notify_menu_ready(db, user)
origin/recipe-import-pipeline-v1:apps/api/app/routers/menus.py:39:        logger.exception("Menu care notification failed for user %s", user_id)
origin/recipe-import-pipeline-v1:apps/api/app/routers/menus.py:56:@router.post("/replace-dish", response_model=MenuVariant)
origin/recipe-import-pipeline-v1:apps/api/app/routers/menus.py:62:) -> MenuVariant:
origin/recipe-import-pipeline-v1:apps/api/app/routers/menus.py:81:    background_tasks.add_task(_send_menu_care_notification, user.id)
origin/recipe-import-pipeline-v1:apps/api/app/routers/notifications.py:7:from app.schemas.notifications import (
origin/recipe-import-pipeline-v1:apps/api/app/routers/notifications.py:8:    NotificationSettingsResponse,
origin/recipe-import-pipeline-v1:apps/api/app/routers/notifications.py:9:    NotificationSettingsUpdate,
origin/recipe-import-pipeline-v1:apps/api/app/routers/notifications.py:11:from app.services import notifications as notifications_service
origin/recipe-import-pipeline-v1:apps/api/app/routers/notifications.py:13:router = APIRouter(prefix="/notifications", tags=["notifications"])
origin/recipe-import-pipeline-v1:apps/api/app/routers/notifications.py:16:@router.get("/settings", response_model=NotificationSettingsResponse)
origin/recipe-import-pipeline-v1:apps/api/app/routers/notifications.py:20:) -> NotificationSettingsResponse:
origin/recipe-import-pipeline-v1:apps/api/app/routers/notifications.py:21:    return notifications_service.get_settings(db, user)
origin/recipe-import-pipeline-v1:apps/api/app/routers/notifications.py:24:@router.put("/settings", response_model=NotificationSettingsResponse)
origin/recipe-import-pipeline-v1:apps/api/app/routers/notifications.py:26:    payload: NotificationSettingsUpdate,
origin/recipe-import-pipeline-v1:apps/api/app/routers/notifications.py:29:) -> NotificationSettingsResponse:
origin/recipe-import-pipeline-v1:apps/api/app/routers/notifications.py:30:    return notifications_service.update_settings(db, user, payload)
origin/recipe-import-pipeline-v1:apps/api/app/routers/nutrition_profile.py:7:from app.schemas.nutrition_profile import NutritionProfileData, NutritionProfileResponse
origin/recipe-import-pipeline-v1:apps/api/app/routers/nutrition_profile.py:8:from app.services.nutrition_profile import (
origin/recipe-import-pipeline-v1:apps/api/app/routers/nutrition_profile.py:9:    migrate_legacy_profile,
origin/recipe-import-pipeline-v1:apps/api/app/routers/nutrition_profile.py:12:    save_nutrition_profile,
origin/recipe-import-pipeline-v1:apps/api/app/routers/nutrition_profile.py:32:def get_nutrition_profile(
origin/recipe-import-pipeline-v1:apps/api/app/routers/nutrition_profile.py:37:    migrate_legacy_profile(db, profile)
origin/recipe-import-pipeline-v1:apps/api/app/routers/nutrition_profile.py:43:def save_nutrition_profile_endpoint(
origin/recipe-import-pipeline-v1:apps/api/app/routers/nutrition_profile.py:54:    profile = save_nutrition_profile(db, user, payload)
origin/recipe-import-pipeline-v1:apps/api/app/routers/recipes.py:20:from app.schemas.menu import MenuVariant
origin/recipe-import-pipeline-v1:apps/api/app/routers/recipes.py:115:def _normalized_ingredient_name(name: str) -> str:
origin/recipe-import-pipeline-v1:apps/api/app/routers/recipes.py:120:    normalized = _normalized_ingredient_name(name)
origin/recipe-import-pipeline-v1:apps/api/app/routers/recipes.py:121:    if not normalized:
origin/recipe-import-pipeline-v1:apps/api/app/routers/recipes.py:124:        item == normalized or item in normalized or normalized in item
origin/recipe-import-pipeline-v1:apps/api/app/routers/recipes.py:259:        _normalized_ingredient_name(item.name)
origin/recipe-import-pipeline-v1:apps/api/app/routers/recipes.py:555:@router.post("/{recipe_id}/add-to-menu", response_model=MenuVariant)
origin/recipe-import-pipeline-v1:apps/api/app/routers/recipes.py:562:) -> MenuVariant:
origin/recipe-import-pipeline-v1:apps/api/app/routers/shopping_lists.py:9:from app.schemas.shopping_list import (
origin/recipe-import-pipeline-v1:apps/api/app/routers/shopping_lists.py:16:from app.services import shopping_list as shopping_list_service
origin/recipe-import-pipeline-v1:apps/api/app/routers/shopping_lists.py:23:def get_my_shopping_list(
origin/recipe-import-pipeline-v1:apps/api/app/routers/shopping_lists.py:28:    result = shopping_list_service.get_shopping_list(db, user, scope)
origin/recipe-import-pipeline-v1:apps/api/app/routers/shopping_lists.py:38:def sync_shopping_list(
origin/recipe-import-pipeline-v1:apps/api/app/routers/shopping_lists.py:42:    return shopping_list_service.sync_shopping_list_for_scope(db, scope)
origin/recipe-import-pipeline-v1:apps/api/app/routers/shopping_lists.py:56:    return shopping_list_service.create_item(db, user, scope, payload)
origin/recipe-import-pipeline-v1:apps/api/app/routers/shopping_lists.py:68:        return shopping_list_service.toggle_item(
origin/recipe-import-pipeline-v1:apps/api/app/routers/shopping_lists.py:76:    return shopping_list_service.update_item(db, user, scope, item_id, payload)
origin/recipe-import-pipeline-v1:apps/api/app/routers/shopping_lists.py:86:    return shopping_list_service.delete_item(db, user, scope, item_id)
origin/recipe-import-pipeline-v1:apps/api/app/routers/shopping_lists.py:97:    return shopping_list_service.toggle_item(
origin/recipe-import-pipeline-v1:apps/api/app/schemas/care.py:6:CareLevel = Literal["minimal", "standard", "active"]
origin/recipe-import-pipeline-v1:apps/api/app/schemas/care.py:7:CareNotificationType = Literal[
origin/recipe-import-pipeline-v1:apps/api/app/schemas/care.py:19:class CareSettingsResponse(BaseModel):
origin/recipe-import-pipeline-v1:apps/api/app/schemas/care.py:28:    care_level: CareLevel
origin/recipe-import-pipeline-v1:apps/api/app/schemas/care.py:36:class CareSettingsUpdate(BaseModel):
origin/recipe-import-pipeline-v1:apps/api/app/schemas/care.py:45:    care_level: CareLevel | None = None
origin/recipe-import-pipeline-v1:apps/api/app/schemas/care.py:51:class CareNotificationResponse(BaseModel):
origin/recipe-import-pipeline-v1:apps/api/app/schemas/care.py:61:class TestCareNotificationRequest(BaseModel):
origin/recipe-import-pipeline-v1:apps/api/app/schemas/care.py:62:    notification_type: CareNotificationType = "water"
origin/recipe-import-pipeline-v1:apps/api/app/schemas/care.py:65:class TestCareNotificationResponse(BaseModel):
origin/recipe-import-pipeline-v1:apps/api/app/schemas/care.py:71:class CareTipPreview(BaseModel):
origin/recipe-import-pipeline-v1:apps/api/app/schemas/care.py:77:class CareTipsResponse(BaseModel):
origin/recipe-import-pipeline-v1:apps/api/app/schemas/care.py:78:    tips: list[CareTipPreview]
origin/recipe-import-pipeline-v1:apps/api/app/schemas/family.py:56:    nutrition_profile_complete: bool = False
origin/recipe-import-pipeline-v1:apps/api/app/schemas/family_member_nutrition.py:5:from app.services.member_age import MAX_AGE_MONTHS, normalize_age_months, validate_age_months
origin/recipe-import-pipeline-v1:apps/api/app/schemas/family_member_nutrition.py:9:    """Stored in family_members.nutrition_profile JSON."""
origin/recipe-import-pipeline-v1:apps/api/app/schemas/family_member_nutrition.py:22:    # Legacy fields (read/write compat)
origin/recipe-import-pipeline-v1:apps/api/app/schemas/family_member_nutrition.py:29:    def migrate_legacy_age(cls, data):
origin/recipe-import-pipeline-v1:apps/api/app/schemas/family_member_nutrition.py:33:            resolved = normalize_age_months(
origin/recipe-import-pipeline-v1:apps/api/app/schemas/menu.py:6:MenuVariantType = Literal["quick", "economy", "balanced"]
origin/recipe-import-pipeline-v1:apps/api/app/schemas/menu.py:26:class MenuIngredient(BaseModel):
origin/recipe-import-pipeline-v1:apps/api/app/schemas/menu.py:32:class MenuVariant(BaseModel):
origin/recipe-import-pipeline-v1:apps/api/app/schemas/menu.py:33:    variant: MenuVariantType
origin/recipe-import-pipeline-v1:apps/api/app/schemas/menu.py:40:    ingredients: list[MenuIngredient] = Field(min_length=1)
origin/recipe-import-pipeline-v1:apps/api/app/schemas/menu.py:46:    menus: list[MenuVariant] = Field(min_length=3, max_length=3)
origin/recipe-import-pipeline-v1:apps/api/app/schemas/menu.py:55:    menu: MenuVariant
origin/recipe-import-pipeline-v1:apps/api/app/schemas/menu.py:81:    menu: MenuVariant
origin/recipe-import-pipeline-v1:apps/api/app/schemas/menu.py:89:    variant: MenuVariantType
origin/recipe-import-pipeline-v1:apps/api/app/schemas/menu.py:90:    menu: MenuVariant
origin/recipe-import-pipeline-v1:apps/api/app/schemas/menu_overview.py:6:from app.schemas.menu import MenuVariant, SelectedMenuResponse
origin/recipe-import-pipeline-v1:apps/api/app/schemas/notifications.py:10:class NotificationSettingsResponse(BaseModel):
origin/recipe-import-pipeline-v1:apps/api/app/schemas/notifications.py:25:class NotificationSettingsUpdate(BaseModel):
origin/recipe-import-pipeline-v1:apps/api/app/schemas/subscription.py:10:    notifications: bool = True
origin/recipe-import-pipeline-v1:apps/api/app/schemas/subscription.py:11:    nutrition_profile: bool = True
origin/recipe-import-pipeline-v1:apps/api/app/schemas/subscription.py:18:    ai_care: bool = False
origin/recipe-import-pipeline-v1:apps/api/app/services/admin_errors.py:1:"""Admin error logging to database (and legacy file fallback)."""
origin/recipe-import-pipeline-v1:apps/api/app/services/ai.py:20:    MenuIngredient,
origin/recipe-import-pipeline-v1:apps/api/app/services/ai.py:22:    MenuVariant,
origin/recipe-import-pipeline-v1:apps/api/app/services/ai.py:23:    MenuVariantType,
origin/recipe-import-pipeline-v1:apps/api/app/services/ai.py:52:MenuVariantKey = Literal["quick", "economy", "balanced"]
origin/recipe-import-pipeline-v1:apps/api/app/services/ai.py:131:    menus: list[MenuVariant]
origin/recipe-import-pipeline-v1:apps/api/app/services/ai.py:204:def _menu_variants_from_ai(data: dict[str, Any]) -> list[MenuVariant]:
origin/recipe-import-pipeline-v1:apps/api/app/services/ai.py:224:    menus: list[MenuVariant] = []
origin/recipe-import-pipeline-v1:apps/api/app/services/ai.py:260:                MenuVariant(
origin/recipe-import-pipeline-v1:apps/api/app/services/ai.py:273:                        MenuIngredient(name="Вода", amount="1 л", category="drinks")
origin/recipe-import-pipeline-v1:apps/api/app/services/ai.py:343:def _ingredients_from_ai_rows(rows: list[dict]) -> list[MenuIngredient]:
origin/recipe-import-pipeline-v1:apps/api/app/services/ai.py:364:        MenuIngredient(
origin/recipe-import-pipeline-v1:apps/api/app/services/amount_parser.py:29:def normalize_unit(raw: str) -> str:
origin/recipe-import-pipeline-v1:apps/api/app/services/amount_parser.py:47:        return None, normalize_unit(text)
origin/recipe-import-pipeline-v1:apps/api/app/services/amount_parser.py:53:        return None, normalize_unit(text)
origin/recipe-import-pipeline-v1:apps/api/app/services/amount_parser.py:55:    unit = normalize_unit(unit_raw) if unit_raw else "шт"
origin/recipe-import-pipeline-v1:apps/api/app/services/bot_input.py:14:from app.schemas.shopping_list import ShoppingItemCreateRequest, ShoppingItemUpdateRequest
origin/recipe-import-pipeline-v1:apps/api/app/services/bot_input.py:16:from app.services import shopping_list as shopping_service
origin/recipe-import-pipeline-v1:apps/api/app/services/bot_input.py:62:def _normalize_match(name: str) -> str:
origin/recipe-import-pipeline-v1:apps/api/app/services/bot_input.py:169:    listing = shopping_service.get_shopping_list(db, user, scope)
origin/recipe-import-pipeline-v1:apps/api/app/services/bot_input.py:170:    key = _normalize_match(name)
origin/recipe-import-pipeline-v1:apps/api/app/services/bot_input.py:172:        if _normalize_match(item.name) == key and not item.checked:
origin/recipe-import-pipeline-v1:apps/api/app/services/bot_today.py:10:from app.services import shopping_list as shopping_service
origin/recipe-import-pipeline-v1:apps/api/app/services/bot_today.py:22:    shopping = shopping_service.get_shopping_list(db, user, scope)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:13:from app.models.care import CareEvent, CareNotification, CareSettings
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:15:from app.schemas.care import (
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:16:    CareNotificationResponse,
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:17:    CareSettingsResponse,
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:18:    CareSettingsUpdate,
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:19:    CareTipPreview,
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:24:from app.services.notifications import get_or_create_settings as get_notif_settings_row
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:27:from app.services import shopping_list as shopping_list_service
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:32:CareLevel = str
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:40:COOLDOWN_HOURS: dict[str, dict[CareLevel, int]] = {
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:51:CARE_TEMPLATES: dict[str, dict[str, str]] = {
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:104:class CareContext:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:116:def _user_timezone(settings_row: CareSettings, user: User, db: Session) -> str:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:130:def _is_quiet_hours(settings_row: CareSettings, user: User, db: Session) -> bool:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:148:        return bool(features.get("ai_care"))
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:153:def get_or_create_care_settings(db: Session, user: User) -> CareSettings:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:155:        db.query(CareSettings).filter(CareSettings.user_id == user.id).one_or_none()
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:159:        row = CareSettings(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:165:            care_level="standard",
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:174:    row: CareSettings, *, has_pro: bool
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:175:) -> CareSettingsResponse:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:176:    return CareSettingsResponse(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:185:        care_level=row.care_level,  # type: ignore[arg-type]
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:194:def get_care_settings(db: Session, user: User) -> CareSettingsResponse:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:195:    row = get_or_create_care_settings(db, user)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:199:def update_care_settings(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:200:    db: Session, user: User, payload: CareSettingsUpdate
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:201:) -> CareSettingsResponse:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:202:    row = get_or_create_care_settings(db, user)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:204:    previous_level = row.care_level
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:208:    if data.get("care_level") == "minimal" and previous_level != "minimal":
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:224:def list_care_notifications(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:226:) -> list[CareNotificationResponse]:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:228:        db.query(CareNotification)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:229:        .filter(CareNotification.user_id == user.id)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:230:        .order_by(desc(CareNotification.created_at))
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:235:        CareNotificationResponse(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:248:def _type_enabled(settings_row: CareSettings, notification_type: str) -> bool:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:261:def _level_allows_type(care_level: str, notification_type: str) -> bool:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:262:    if care_level == "minimal":
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:264:    if care_level == "standard":
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:269:def _cooldown_hours(care_level: str, notification_type: str) -> int:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:271:    return by_type.get(care_level, 24)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:278:        db.query(CareNotification)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:280:            CareNotification.user_id == user_id,
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:281:            CareNotification.type == notification_type,
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:282:            CareNotification.status == "sent",
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:284:        .order_by(desc(CareNotification.sent_at))
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:298:    settings_row = get_or_create_care_settings(db, user)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:302:    if not _level_allows_type(settings_row.care_level, notification_type):
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:312:            hours = _cooldown_hours(settings_row.care_level, notification_type)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:319:def create_care_notification(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:329:) -> CareNotification:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:330:    template = CARE_TEMPLATES.get(notification_type, CARE_TEMPLATES["water"])
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:331:    row = CareNotification(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:347:def log_care_event(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:352:    source: str = "care",
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:355:) -> CareEvent:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:356:    event = CareEvent(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:369:async def send_telegram_care_notification(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:371:    notification: CareNotification,
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:377:        logger.info("Care notification skipped: no telegram_id for user %s", user.id)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:380:    template = CARE_TEMPLATES.get(notification.type, {})
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:400:    log_care_event(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:403:        f"care_{notification.type}_{'sent' if sent else 'failed'}",
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:409:def build_care_context(db: Session, user: User) -> CareContext:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:412:    shopping = shopping_list_service.get_shopping_list(db, user, scope)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:428:    return CareContext(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:441:def generate_basic_care_tips(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:442:    db: Session, user: User, context: CareContext | None = None
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:443:) -> list[CareTipPreview]:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:444:    ctx = context or build_care_context(db, user)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:445:    tips: list[CareTipPreview] = []
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:448:        t = CARE_TEMPLATES["shopping"]
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:450:            CareTipPreview(type="shopping", title=t["title"], message=t["message"])
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:453:        t = CARE_TEMPLATES["pantry"]
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:460:        tips.append(CareTipPreview(type="pantry", title=t["title"], message=msg))
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:462:        t = CARE_TEMPLATES["menu"]
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:463:        tips.append(CareTipPreview(type="menu", title=t["title"], message=t["message"]))
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:465:        t = CARE_TEMPLATES["protein"]
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:467:            CareTipPreview(type="protein", title=t["title"], message=t["message"])
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:469:    t = CARE_TEMPLATES["water"]
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:470:    tips.append(CareTipPreview(type="water", title=t["title"], message=t["message"]))
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:472:        t = CARE_TEMPLATES["family"]
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:473:        tips.append(CareTipPreview(type="family", title=t["title"], message=t["message"]))
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:475:        t = CARE_TEMPLATES["pro"]
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:476:        tips.append(CareTipPreview(type="pro", title=t["title"], message=t["message"]))
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:481:async def send_care_notification_by_type(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:489:) -> tuple[bool, str, CareNotification | None]:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:499:    template = CARE_TEMPLATES[notification_type]
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:500:    notification = create_care_notification(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:510:    sent = await send_telegram_care_notification(db, notification, user)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:527:    ctx = build_care_context(db, user)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:530:    await send_care_notification_by_type(db, user, "menu")
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:533:async def process_care_reminders_for_user(db: Session, user: User) -> None:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:534:    """Send at most one contextual care tip per scheduler tick."""
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:535:    settings_row = get_or_create_care_settings(db, user)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:536:    if settings_row.care_level == "minimal" and not any(
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:545:    ctx = build_care_context(db, user)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:546:    tips = generate_basic_care_tips(db, user, ctx)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:550:            await send_care_notification_by_type(db, user, tip.type)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:554:async def process_all_care_reminders(db: Session) -> None:
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:560:            await process_care_reminders_for_user(db, user)
origin/recipe-import-pipeline-v1:apps/api/app/services/care.py:562:            logger.exception("Care reminder failed for user %s", user.id)
origin/recipe-import-pipeline-v1:apps/api/app/services/event_plan.py:19:from app.schemas.menu import MenuIngredient
origin/recipe-import-pipeline-v1:apps/api/app/services/event_plan.py:27:from app.services import shopping_list as shopping_list_service
```

## Keyword scan in origin/sprint-0/planam-2026-foundation

Hits (max 300): **300**

```
origin/sprint-0/planam-2026-foundation:apps/api/app/database.py:36:        shopping_list,
origin/sprint-0/planam-2026-foundation:apps/api/app/database.py:42:    from app.models import care as care_models  # noqa: F401
origin/sprint-0/planam-2026-foundation:apps/api/app/database.py:47:    # Legacy tables: SQLAlchemy create_all. Recipe Engine tables: SQL migrations only.
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:65:        "ALTER TABLE family_shopping_lists ADD COLUMN IF NOT EXISTS user_id INTEGER",
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:71:                WHERE conname = 'family_shopping_lists_user_id_fkey'
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:73:                ALTER TABLE family_shopping_lists
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:74:                ADD CONSTRAINT family_shopping_lists_user_id_fkey
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:79:        "ALTER TABLE family_shopping_lists ALTER COLUMN family_id DROP NOT NULL",
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:80:        "CREATE UNIQUE INDEX IF NOT EXISTS ix_family_shopping_lists_user_id ON family_shopping_lists (user_id)",
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:115:            invited_phone_normalized VARCHAR(32) NOT NULL,
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:127:        ON family_invites (family_id, invited_phone_normalized)
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:133:        ON family_invites (family_id, invited_phone_normalized)
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:134:        WHERE status = 'pending' AND invited_phone_normalized != '__link__';
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:179:        "ALTER TABLE family_members ADD COLUMN IF NOT EXISTS nutrition_profile JSONB NOT NULL DEFAULT '{}'",
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:254:        # AI Care System (stage 8)
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:256:        CREATE TABLE IF NOT EXISTS care_settings (
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:267:            care_level VARCHAR(16) NOT NULL DEFAULT 'standard',
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:276:        CREATE TABLE IF NOT EXISTS care_notifications (
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:290:        "CREATE INDEX IF NOT EXISTS ix_care_notifications_user_id ON care_notifications (user_id);",
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:292:        CREATE TABLE IF NOT EXISTS care_events (
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:297:            source VARCHAR(64) NOT NULL DEFAULT 'care',
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:302:        "CREATE INDEX IF NOT EXISTS ix_care_events_user_id ON care_events (user_id);",
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:440:        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS normalized_title VARCHAR(200)",
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:445:        SET normalized_title = lower(trim(regexp_replace(title, '\\s+', ' ', 'g')))
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:446:        WHERE normalized_title IS NULL AND title IS NOT NULL
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:448:        "CREATE INDEX IF NOT EXISTS ix_recipes_normalized_title ON recipes (normalized_title)",
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:894:    legacy_tables = [
origin/sprint-0/planam-2026-foundation:apps/api/app/database_migrations.py:907:                tables=legacy_tables,
origin/sprint-0/planam-2026-foundation:apps/api/app/main.py:17:    care,
origin/sprint-0/planam-2026-foundation:apps/api/app/main.py:24:    notifications,
origin/sprint-0/planam-2026-foundation:apps/api/app/main.py:25:    nutrition_profile,
origin/sprint-0/planam-2026-foundation:apps/api/app/main.py:33:    shopping_lists,
origin/sprint-0/planam-2026-foundation:apps/api/app/main.py:105:app.include_router(care.router)
origin/sprint-0/planam-2026-foundation:apps/api/app/main.py:109:app.include_router(nutrition_profile.router)
origin/sprint-0/planam-2026-foundation:apps/api/app/main.py:115:app.include_router(shopping_lists.router)
origin/sprint-0/planam-2026-foundation:apps/api/app/main.py:118:app.include_router(notifications.router)
origin/sprint-0/planam-2026-foundation:apps/api/app/models/__init__.py:2:from app.models.care import CareEvent, CareNotification, CareSettings
origin/sprint-0/planam-2026-foundation:apps/api/app/models/__init__.py:7:from app.models.notification_settings import UserNotificationSettings
origin/sprint-0/planam-2026-foundation:apps/api/app/models/__init__.py:11:from app.models.shopping_list import FamilyShoppingList
origin/sprint-0/planam-2026-foundation:apps/api/app/models/__init__.py:36:    "UserNotificationSettings",
origin/sprint-0/planam-2026-foundation:apps/api/app/models/__init__.py:45:    "CareSettings",
origin/sprint-0/planam-2026-foundation:apps/api/app/models/__init__.py:46:    "CareNotification",
origin/sprint-0/planam-2026-foundation:apps/api/app/models/__init__.py:47:    "CareEvent",
origin/sprint-0/planam-2026-foundation:apps/api/app/models/care.py:11:class CareSettings(Base):
origin/sprint-0/planam-2026-foundation:apps/api/app/models/care.py:12:    __tablename__ = "care_settings"
origin/sprint-0/planam-2026-foundation:apps/api/app/models/care.py:26:    care_level: Mapped[str] = mapped_column(String(16), default="standard")
origin/sprint-0/planam-2026-foundation:apps/api/app/models/care.py:37:    user = relationship("User", backref="care_settings")
origin/sprint-0/planam-2026-foundation:apps/api/app/models/care.py:40:class CareNotification(Base):
origin/sprint-0/planam-2026-foundation:apps/api/app/models/care.py:41:    __tablename__ = "care_notifications"
origin/sprint-0/planam-2026-foundation:apps/api/app/models/care.py:66:class CareEvent(Base):
origin/sprint-0/planam-2026-foundation:apps/api/app/models/care.py:67:    __tablename__ = "care_events"
origin/sprint-0/planam-2026-foundation:apps/api/app/models/care.py:77:    source: Mapped[str] = mapped_column(String(64), default="care")
origin/sprint-0/planam-2026-foundation:apps/api/app/models/family.py:60:    nutrition_profile: Mapped[dict] = mapped_column(JSONB, default=dict)
origin/sprint-0/planam-2026-foundation:apps/api/app/models/family_invite.py:24:    invited_phone_normalized: Mapped[str] = mapped_column(String(32), index=True)
origin/sprint-0/planam-2026-foundation:apps/api/app/models/notification_settings.py:9:class UserNotificationSettings(Base):
origin/sprint-0/planam-2026-foundation:apps/api/app/models/recipe.py:26:    normalized_title: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
origin/sprint-0/planam-2026-foundation:apps/api/app/models/recipe.py:61:    # legacy calories_per_serving / protein_g / fat_g / carbs_g fields.
origin/sprint-0/planam-2026-foundation:apps/api/app/models/shopping_list.py:11:    __tablename__ = "family_shopping_lists"
origin/sprint-0/planam-2026-foundation:apps/api/app/models/user.py:64:        "UserNotificationSettings",
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:7:from app.schemas.care import (
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:8:    CareNotificationResponse,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:9:    CareSettingsResponse,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:10:    CareSettingsUpdate,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:11:    CareTipsResponse,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:12:    TestCareNotificationRequest,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:13:    TestCareNotificationResponse,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:15:from app.services import care as care_service
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:17:router = APIRouter(prefix="/care", tags=["care"])
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:20:@router.get("/settings", response_model=CareSettingsResponse)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:21:def get_care_settings(
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:24:) -> CareSettingsResponse:
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:25:    return care_service.get_care_settings(db, user)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:28:@router.patch("/settings", response_model=CareSettingsResponse)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:29:def patch_care_settings(
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:30:    payload: CareSettingsUpdate,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:33:) -> CareSettingsResponse:
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:34:    return care_service.update_care_settings(db, user, payload)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:37:@router.get("/notifications", response_model=list[CareNotificationResponse])
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:38:def list_care_notifications(
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:41:) -> list[CareNotificationResponse]:
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:42:    return care_service.list_care_notifications(db, user)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:45:@router.get("/tips", response_model=CareTipsResponse)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:46:def preview_care_tips(
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:49:) -> CareTipsResponse:
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:50:    ctx = care_service.build_care_context(db, user)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:51:    return CareTipsResponse(tips=care_service.generate_basic_care_tips(db, user, ctx))
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:54:@router.post("/test-notification", response_model=TestCareNotificationResponse)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:56:    payload: TestCareNotificationRequest,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:59:) -> TestCareNotificationResponse:
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:60:    ok, message, notification = await care_service.send_care_notification_by_type(
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/care.py:67:    return TestCareNotificationResponse(
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/event_plans.py:50:def create_event_shopping_list(
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/families.py:53:        invited_phone_masked=mask_phone(invite.invited_phone_normalized),
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/families.py:188:            invited_phone_masked=mask_phone(inv.invited_phone_normalized),
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/menus.py:14:    MenuVariant,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/menus.py:31:from app.services import care as care_service
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/menus.py:38:async def _send_menu_care_notification(user_id: int) -> None:
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/menus.py:43:            await care_service.maybe_notify_menu_ready(db, user)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/menus.py:45:        logger.exception("Menu care notification failed for user %s", user_id)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/menus.py:62:@router.post("/replace-dish", response_model=MenuVariant)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/menus.py:68:) -> MenuVariant:
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/menus.py:87:    background_tasks.add_task(_send_menu_care_notification, user.id)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/notifications.py:7:from app.schemas.notifications import (
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/notifications.py:8:    NotificationSettingsResponse,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/notifications.py:9:    NotificationSettingsUpdate,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/notifications.py:11:from app.services import notifications as notifications_service
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/notifications.py:13:router = APIRouter(prefix="/notifications", tags=["notifications"])
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/notifications.py:16:@router.get("/settings", response_model=NotificationSettingsResponse)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/notifications.py:20:) -> NotificationSettingsResponse:
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/notifications.py:21:    return notifications_service.get_settings(db, user)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/notifications.py:24:@router.put("/settings", response_model=NotificationSettingsResponse)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/notifications.py:26:    payload: NotificationSettingsUpdate,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/notifications.py:29:) -> NotificationSettingsResponse:
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/notifications.py:30:    return notifications_service.update_settings(db, user, payload)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/nutrition_profile.py:7:from app.schemas.nutrition_profile import NutritionProfileData, NutritionProfileResponse
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/nutrition_profile.py:8:from app.services.nutrition_profile import (
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/nutrition_profile.py:9:    migrate_legacy_profile,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/nutrition_profile.py:12:    save_nutrition_profile,
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/nutrition_profile.py:32:def get_nutrition_profile(
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/nutrition_profile.py:37:    migrate_legacy_profile(db, profile)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/nutrition_profile.py:43:def save_nutrition_profile_endpoint(
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/nutrition_profile.py:54:    profile = save_nutrition_profile(db, user, payload)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/recipes.py:117:def _normalized_ingredient_name(name: str) -> str:
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/recipes.py:122:    normalized = _normalized_ingredient_name(name)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/recipes.py:123:    if not normalized:
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/recipes.py:126:        item == normalized or item in normalized or normalized in item
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/recipes.py:267:        _normalized_ingredient_name(item.name)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/shopping_lists.py:9:from app.schemas.shopping_list import (
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/shopping_lists.py:16:from app.services import shopping_list as shopping_list_service
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/shopping_lists.py:23:def get_my_shopping_list(
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/shopping_lists.py:28:    result = shopping_list_service.get_shopping_list(db, user, scope)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/shopping_lists.py:38:def sync_shopping_list(
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/shopping_lists.py:42:    return shopping_list_service.sync_shopping_list_for_scope(db, scope)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/shopping_lists.py:56:    return shopping_list_service.create_item(db, user, scope, payload)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/shopping_lists.py:68:        return shopping_list_service.toggle_item(
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/shopping_lists.py:76:    return shopping_list_service.update_item(db, user, scope, item_id, payload)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/shopping_lists.py:86:    return shopping_list_service.delete_item(db, user, scope, item_id)
origin/sprint-0/planam-2026-foundation:apps/api/app/routers/shopping_lists.py:97:    return shopping_list_service.toggle_item(
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/care.py:6:CareLevel = Literal["minimal", "standard", "active"]
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/care.py:7:CareNotificationType = Literal[
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/care.py:19:class CareSettingsResponse(BaseModel):
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/care.py:28:    care_level: CareLevel
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/care.py:36:class CareSettingsUpdate(BaseModel):
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/care.py:45:    care_level: CareLevel | None = None
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/care.py:51:class CareNotificationResponse(BaseModel):
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/care.py:61:class TestCareNotificationRequest(BaseModel):
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/care.py:62:    notification_type: CareNotificationType = "water"
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/care.py:65:class TestCareNotificationResponse(BaseModel):
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/care.py:71:class CareTipPreview(BaseModel):
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/care.py:77:class CareTipsResponse(BaseModel):
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/care.py:78:    tips: list[CareTipPreview]
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/family.py:56:    nutrition_profile_complete: bool = False
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/family_member_nutrition.py:5:from app.services.member_age import MAX_AGE_MONTHS, normalize_age_months, validate_age_months
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/family_member_nutrition.py:9:    """Stored in family_members.nutrition_profile JSON."""
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/family_member_nutrition.py:22:    # Legacy fields (read/write compat)
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/family_member_nutrition.py:29:    def migrate_legacy_age(cls, data):
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/family_member_nutrition.py:33:            resolved = normalize_age_months(
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu.py:6:MenuVariantType = Literal["quick", "economy", "balanced"]
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu.py:28:class MenuIngredient(BaseModel):
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu.py:34:class MenuVariant(BaseModel):
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu.py:35:    variant: MenuVariantType
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu.py:42:    ingredients: list[MenuIngredient] = Field(min_length=1)
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu.py:48:    menus: list[MenuVariant] = Field(min_length=3, max_length=3)
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu.py:57:    menu: MenuVariant
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu.py:83:    menu: MenuVariant
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu.py:91:    variant: MenuVariantType
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu.py:92:    menu: MenuVariant
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu_overview.py:6:from app.schemas.menu import MenuVariant, SelectedMenuResponse
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu_overview.py:152:    menu: MenuVariant
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu_overview.py:158:    menu: MenuVariant | None = None
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/menu_overview.py:168:    menu: MenuVariant
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/notifications.py:10:class NotificationSettingsResponse(BaseModel):
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/notifications.py:25:class NotificationSettingsUpdate(BaseModel):
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/subscription.py:10:    notifications: bool = True
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/subscription.py:11:    nutrition_profile: bool = True
origin/sprint-0/planam-2026-foundation:apps/api/app/schemas/subscription.py:18:    ai_care: bool = False
origin/sprint-0/planam-2026-foundation:apps/api/app/services/admin_errors.py:1:"""Admin error logging to database (and legacy file fallback)."""
origin/sprint-0/planam-2026-foundation:apps/api/app/services/ai.py:20:    MenuIngredient,
origin/sprint-0/planam-2026-foundation:apps/api/app/services/ai.py:22:    MenuVariant,
origin/sprint-0/planam-2026-foundation:apps/api/app/services/ai.py:23:    MenuVariantType,
origin/sprint-0/planam-2026-foundation:apps/api/app/services/ai.py:52:MenuVariantKey = Literal["quick", "economy", "balanced"]
origin/sprint-0/planam-2026-foundation:apps/api/app/services/ai.py:131:    menus: list[MenuVariant]
origin/sprint-0/planam-2026-foundation:apps/api/app/services/ai.py:204:def _menu_variants_from_ai(data: dict[str, Any]) -> list[MenuVariant]:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/ai.py:224:    menus: list[MenuVariant] = []
origin/sprint-0/planam-2026-foundation:apps/api/app/services/ai.py:260:                MenuVariant(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/ai.py:273:                        MenuIngredient(name="Вода", amount="1 л", category="drinks")
origin/sprint-0/planam-2026-foundation:apps/api/app/services/ai.py:343:def _ingredients_from_ai_rows(rows: list[dict]) -> list[MenuIngredient]:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/ai.py:364:        MenuIngredient(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/amount_parser.py:29:def normalize_unit(raw: str) -> str:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/amount_parser.py:47:        return None, normalize_unit(text)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/amount_parser.py:53:        return None, normalize_unit(text)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/amount_parser.py:55:    unit = normalize_unit(unit_raw) if unit_raw else "шт"
origin/sprint-0/planam-2026-foundation:apps/api/app/services/bot_input.py:14:from app.schemas.shopping_list import ShoppingItemCreateRequest, ShoppingItemUpdateRequest
origin/sprint-0/planam-2026-foundation:apps/api/app/services/bot_input.py:16:from app.services import shopping_list as shopping_service
origin/sprint-0/planam-2026-foundation:apps/api/app/services/bot_input.py:62:def _normalize_match(name: str) -> str:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/bot_input.py:169:    listing = shopping_service.get_shopping_list(db, user, scope)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/bot_input.py:170:    key = _normalize_match(name)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/bot_input.py:172:        if _normalize_match(item.name) == key and not item.checked:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/bot_today.py:10:from app.services import shopping_list as shopping_service
origin/sprint-0/planam-2026-foundation:apps/api/app/services/bot_today.py:22:    shopping = shopping_service.get_shopping_list(db, user, scope)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:13:from app.models.care import CareEvent, CareNotification, CareSettings
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:15:from app.schemas.care import (
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:16:    CareNotificationResponse,
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:17:    CareSettingsResponse,
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:18:    CareSettingsUpdate,
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:19:    CareTipPreview,
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:24:from app.services.notifications import get_or_create_settings as get_notif_settings_row
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:27:from app.services import shopping_list as shopping_list_service
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:32:CareLevel = str
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:40:COOLDOWN_HOURS: dict[str, dict[CareLevel, int]] = {
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:51:CARE_TEMPLATES: dict[str, dict[str, str]] = {
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:104:class CareContext:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:116:def _user_timezone(settings_row: CareSettings, user: User, db: Session) -> str:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:130:def _is_quiet_hours(settings_row: CareSettings, user: User, db: Session) -> bool:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:148:        return bool(features.get("ai_care"))
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:153:def get_or_create_care_settings(db: Session, user: User) -> CareSettings:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:155:        db.query(CareSettings).filter(CareSettings.user_id == user.id).one_or_none()
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:159:        row = CareSettings(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:165:            care_level="standard",
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:174:    row: CareSettings, *, has_pro: bool
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:175:) -> CareSettingsResponse:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:176:    return CareSettingsResponse(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:185:        care_level=row.care_level,  # type: ignore[arg-type]
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:194:def get_care_settings(db: Session, user: User) -> CareSettingsResponse:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:195:    row = get_or_create_care_settings(db, user)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:199:def update_care_settings(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:200:    db: Session, user: User, payload: CareSettingsUpdate
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:201:) -> CareSettingsResponse:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:202:    row = get_or_create_care_settings(db, user)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:204:    previous_level = row.care_level
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:208:    if data.get("care_level") == "minimal" and previous_level != "minimal":
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:224:def list_care_notifications(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:226:) -> list[CareNotificationResponse]:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:228:        db.query(CareNotification)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:229:        .filter(CareNotification.user_id == user.id)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:230:        .order_by(desc(CareNotification.created_at))
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:235:        CareNotificationResponse(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:248:def _type_enabled(settings_row: CareSettings, notification_type: str) -> bool:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:261:def _level_allows_type(care_level: str, notification_type: str) -> bool:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:262:    if care_level == "minimal":
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:264:    if care_level == "standard":
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:269:def _cooldown_hours(care_level: str, notification_type: str) -> int:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:271:    return by_type.get(care_level, 24)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:278:        db.query(CareNotification)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:280:            CareNotification.user_id == user_id,
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:281:            CareNotification.type == notification_type,
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:282:            CareNotification.status == "sent",
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:284:        .order_by(desc(CareNotification.sent_at))
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:298:    settings_row = get_or_create_care_settings(db, user)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:302:    if not _level_allows_type(settings_row.care_level, notification_type):
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:312:            hours = _cooldown_hours(settings_row.care_level, notification_type)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:319:def create_care_notification(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:329:) -> CareNotification:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:330:    template = CARE_TEMPLATES.get(notification_type, CARE_TEMPLATES["water"])
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:331:    row = CareNotification(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:347:def log_care_event(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:352:    source: str = "care",
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:355:) -> CareEvent:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:356:    event = CareEvent(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:369:async def send_telegram_care_notification(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:371:    notification: CareNotification,
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:377:        logger.info("Care notification skipped: no telegram_id for user %s", user.id)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:380:    template = CARE_TEMPLATES.get(notification.type, {})
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:400:    log_care_event(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:403:        f"care_{notification.type}_{'sent' if sent else 'failed'}",
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:409:def build_care_context(db: Session, user: User) -> CareContext:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:412:    shopping = shopping_list_service.get_shopping_list(db, user, scope)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:428:    return CareContext(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:441:def generate_basic_care_tips(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:442:    db: Session, user: User, context: CareContext | None = None
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:443:) -> list[CareTipPreview]:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:444:    ctx = context or build_care_context(db, user)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:445:    tips: list[CareTipPreview] = []
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:448:        t = CARE_TEMPLATES["shopping"]
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:450:            CareTipPreview(type="shopping", title=t["title"], message=t["message"])
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:453:        t = CARE_TEMPLATES["pantry"]
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:460:        tips.append(CareTipPreview(type="pantry", title=t["title"], message=msg))
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:462:        t = CARE_TEMPLATES["menu"]
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:463:        tips.append(CareTipPreview(type="menu", title=t["title"], message=t["message"]))
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:465:        t = CARE_TEMPLATES["protein"]
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:467:            CareTipPreview(type="protein", title=t["title"], message=t["message"])
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:469:    t = CARE_TEMPLATES["water"]
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:470:    tips.append(CareTipPreview(type="water", title=t["title"], message=t["message"]))
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:472:        t = CARE_TEMPLATES["family"]
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:473:        tips.append(CareTipPreview(type="family", title=t["title"], message=t["message"]))
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:475:        t = CARE_TEMPLATES["pro"]
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:476:        tips.append(CareTipPreview(type="pro", title=t["title"], message=t["message"]))
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:481:async def send_care_notification_by_type(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:489:) -> tuple[bool, str, CareNotification | None]:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:499:    template = CARE_TEMPLATES[notification_type]
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:500:    notification = create_care_notification(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:510:    sent = await send_telegram_care_notification(db, notification, user)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:527:    ctx = build_care_context(db, user)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:530:    await send_care_notification_by_type(db, user, "menu")
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:533:async def process_care_reminders_for_user(db: Session, user: User) -> None:
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:534:    """Send at most one contextual care tip per scheduler tick."""
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:535:    settings_row = get_or_create_care_settings(db, user)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:536:    if settings_row.care_level == "minimal" and not any(
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:545:    ctx = build_care_context(db, user)
origin/sprint-0/planam-2026-foundation:apps/api/app/services/care.py:546:    tips = generate_basic_care_tips(db, user, ctx)
```

## Conclusion / decisions

1. **Базовая ветка для актуального продукта:** `sprint-0/planam-2026-foundation`.
   Текущая ветка — строгое надмножество всех остальных remote-веток по
   коммитам (`HEAD..<branch>` = 0 unique commits для main, ux-foundation-v1,
   release-candidate-ux, recipe-engine-v1, recipe-import-pipeline-v1).
   Единственное отличие от `origin/sprint-0/planam-2026-foundation` —
   локальный коммит консолидации (`7523c0c`), ещё не запушенный.

2. **Ветки с полезной новой логикой (которой нет в current):** **нет**.
   Единственный когда-либо найденный уникальный коммит — `858df80`
   (`fix(admin): build absolute admin WebApp URL`) на `recipe-import-clean`;
   тот же фикс уже присутствует в `admin_auth.py` текущей ветки.

3. **Ветки со старой/legacy логикой (архивные):**
   `main`, `ux-foundation-v1`, `release-candidate-ux`, `recipe-engine-v1`,
   `recipe-import-pipeline-v1`, `recipe-import-clean`, `ux-ui-refinement-v1`,
   `planam-recipe-engine-v1`, `recipe-import-broken-backup`,
   `audit/planam-master-audit`.

4. **Файлы для cherry-pick / переноса:** **нет**.

5. **Файлы, которые нельзя переносить (superseded legacy):**
   - `apps/api/app/services/recipes.py` (монолит) → заменён пакетом `services/recipes/`;
   - `apps/web/components/layout/BottomNav.tsx` → `BottomNavigation2026`;
   - `apps/web/components/onboarding/OnboardingWizard.tsx` → `onboarding-2026`;
   - `apps/web/components/recipes/RecipeCatalog.tsx` → `recipes-2026/RecipeCatalog2026`;
   - прочие файлы из раздела «Files only in origin/main» — намеренно удалены в 2026.

6. **Merge старых веток целиком:** **запрещён** (вернёт legacy-файлы и старые баги).

**Gate result: PASSED.** Консолидация продолжается на
`sprint-0/planam-2026-foundation`.

