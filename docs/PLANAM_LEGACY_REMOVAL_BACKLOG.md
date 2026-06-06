# PLANAM LEGACY REMOVAL BACKLOG

**Дата:** 2026-06-03  
**Связанный аудит:** [PLANAM_LEGACY_DECOMMISSION_AUDIT.md](./PLANAM_LEGACY_DECOMMISSION_AUDIT.md)  
**Правило:** удаление только после замены или подтверждения zero traffic

---

## P0 — блокирует чистоту V1 / высокий риск регрессии

| ID | Элемент | Действие | Причина | Риски | Зависимости |
|----|---------|----------|---------|-------|-------------|
| P0-1 | Backend category `продукты` | Убрать из `SYSTEM_CATEGORIES`, infer fallback → `другое` | Противоречит `PLANAM_V1_SHOPPING_MODEL_UPDATE.md` | Существующие DB rows с slug `продукты` | DB migration script; обновить API tests |
| P0-2 | `shopping_categories.py` legacy slugs | Свести к `categories-v1.ts` (15 slugs) | Client/server drift | Сломанные категории в старых списках | P0-1; sync с frontend |
| P0-3 | Pantry defaults `продукты` | Заменить на `другое` в model/schema/service | Тихое возвращение forbidden category | Legacy pantry UI | P0-1 |
| P0-4 | Legacy routes без redirect в prod | Включить `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=true` или hard-remove pages | Пользователь может открыть `/menu`, `/health` | Закладки, bot deep links | Analytics на traffic; bot URL audit |
| P0-5 | Dual shell flag as long-term state | План hard cutover: удалить legacy shell после Sprint 2 | Один env var = два продукта | Локальная разработка | Все V1 account screens готовы |
| P0-6 | `TelegramProvider` bg fallback `#fbf7ef` | Обновить на V1 `#FFFFFF` | Визуальный откат к cream в Telegram | Dark theme edge cases | `PLANAM_COLOR_SYSTEM_V1.md` |

---

## P1 — технический долг / дублирование, не блокирует Sprint 2 старт

| ID | Элемент | Действие | Причина | Риски | Зависимости |
|----|---------|----------|---------|-------|-------------|
| P1-1 | Orphan `components/home/*` (6 файлов) | Удалить | Не импортируются | Низкий | Убедиться grep=0 |
| P1-2 | Unused `home-2026/*` (5 компонентов) | Удалить | Superseded Sprint 1/1.5 | Низкий | Обновить `index.ts` exports |
| P1-3 | `components/onboarding/` (legacy wizard) | Удалить | Orphan; 2026 flow active | Низкий | — |
| P1-4 | Deprecated nav: `BottomNav`, `BottomBackButton`, `TopBackLink` | Удалить | @deprecated, no imports | Низкий | — |
| P1-5 | `RoutePlaceholder2026`, `HomeMonetizationBanner2026` | Удалить | Never mounted | Низкий | — |
| P1-6 | `lib/cache/use-cached-query.ts` | Удалить | Orphan hook | Низкий | — |
| P1-7 | Legacy pages `/menu/*` | Удалить после redirects stable | Дублируют `/plan/*` | Bot links, SEO | P0-4; Sprint 2 plan features |
| P1-8 | Legacy pages `/health/*`, `/nutritionist/*` | Удалить | Дублируют `/wellness` | Deep links | Wellness parity check |
| P1-9 | `ProgressDashboard` + `/progress` | Мигрировать в `/wellness/progress` или удалить | Нет V1 page | Users on progress route | P1-10 |
| P1-10 | Создать `/wellness/progress` | Implement or merge into wellness home | Middleware target missing | 404 при broad redirects | Sprint 2 scope |
| P1-11 | `ShoppingListView` + `components/shopping/*` legacy UI | Удалить после flag hard-on | Дублирует Shopping2026 | Shared subcomponents | Extract shared primitives first |
| P1-12 | `PantryDashboard` legacy | Удалить; оставить `Pantry2026` | `/shopping/pantry` legacy path | — | Redirect `/shopping/pantry` → `/home/pantry` |
| P1-13 | `RecipesView`, `RecipeDetailLegacy` | Удалить | Redirected to V1 catalog | External recipe links | RecipeDetail2026 parity |
| P1-14 | Account embedded legacy screens | Redesign: Family, Nutrition, Notifications, Settings | cream/stone внутри V1 hub | Large refactor | Sprint 2 design spec |
| P1-15 | `MenuHub`, `MenuPlanner`, `MenuCurrentView` | Удалить с `/menu` pages | Full menu stack duplicate | — | P1-7 |
| P1-16 | `NutritionistDashboard`, `HealthTodayView` | Удалить с `/health` | Wellness replacement | — | P1-8 |
| P1-17 | `nav-config.ts` + `BottomNavigation.tsx` | Удалить после shell cutover | Legacy nav SoT | flag=false dev | P0-5 |
| P1-18 | `ScreenLayout`, `SectionHub` | Удалить после account V1 screens | Legacy chrome | Embedded mode bridge | P1-14 |
| P1-19 | Backend extra categories (`заморозка`, `сладости`, …) | Deprecate + map to V1 | 17+ slugs vs 15 V1 | Historical items | P0-2 |
| P1-20 | API tests expecting `продукты` | Обновить на V1 slugs | Tests encode legacy | CI fail during P0 | P0-1 |
| P1-21 | `stone-*` / `emerald-*` in user-facing screens | Мигрировать на `pa-*` | Visual inconsistency | — | P1-14, settings V1 |
| P1-22 | Missing V1 routes: `/plan/favorites`, `/plan/collections` | Implement or remove from migration map | Dead redirect targets | 404 | Sprint 2/5 scope |

---

## P2 — cleanup / оптимизация после релиза

| ID | Элемент | Действие | Причина | Риски | Зависимости |
|----|---------|----------|---------|-------|-------------|
| P2-1 | `AppShell.tsx`, `AppShellBridge` dual logic | Single shell | Simplify architecture | Dev workflow | P0-5 complete |
| P2-2 | `isPlanamUi2026Enabled()` branches in 30+ pages | Remove branches | Dead code paths | — | P2-1 |
| P2-3 | `usePlanam2026Embedded()` bridge | Remove | No longer needed | — | P1-14 |
| P2-4 | `PlanAmHome.tsx` | Удалить | Legacy home | — | P2-1 |
| P2-5 | `route-migration-2026.ts` + middleware | Simplify to 410/redirect table | Migration complete | — | P0-4, P1-7/8 |
| P2-6 | `recipe_catalog_seed.py` placeholder recipes | Replace with real import | Image Strategy | Empty catalog if removed early | Import pipeline ready |
| P2-7 | `recipe_seed.py` (15 demo) | Archive or replace | Demo quality | Dev empty DB | P2-6 |
| P2-8 | Recipe Engine tables unused in V1 | Evaluate drop vs Sprint 3 | `recipe_scenarios`, `recipe_explanations` | Data loss | Product decision |
| P2-9 | `event_plans` + `/menu/event` | Remove or V2 feature | Legacy event wizard | — | Usage metrics |
| P2-10 | `care_*` tables + `CareSettingsPanel` | Merge into notifications | `/health/care` redirect hack | — | Notifications V1 |
| P2-11 | `components/care/` | Remove | Orphan path | — | P2-10 |
| P2-12 | `components/admin/` stone theme | Optional V1 admin skin | Visual only | Low | — |
| P2-13 | `dev/planam-2026` preview page | Keep internal / protect | DS reference | — | — |
| P2-14 | Legacy docs (`UI_SYSTEM_AUDIT`, pre-freeze specs) | Archive to `docs/archive/` | Confusion with V1 SoT | — | — |
| P2-15 | `pages.txt`, `nav-calls.txt`, `project-tree.txt` | Remove from repo root | Accidental commit artifacts | — | — |
| P2-16 | `RECIPE_ENGINE_V1=false` | Enable or remove flag | Dead feature gate | — | Recipe search scope |
| P2-17 | `RecipeDetailModal` modal pattern | Remove | Legacy menu UX | — | P1-13 |
| P2-18 | Subscription legacy `/subscription` | Force redirect only | Duplicate of account path | — | P0-4 |

---

## Recommended execution order

```text
Phase A (safe, no user impact)
  P1-1 → P1-6 (orphan file deletion)

Phase B (Sprint 2 parallel)
  P0-1 → P0-3 → P1-20 (shopping backend alignment)
  P1-14 (account V1 screens)
  P1-10 (wellness progress)

Phase C (cutover)
  P0-4 (enable broad redirects)
  P1-7, P1-8, P1-12, P1-13 (remove legacy pages)
  P0-5 (flag hard-on)

Phase D (post-release)
  P2-* (shell simplification, seeds, engine tables)
```

---

## Checklist before each deletion PR

- [ ] `grep` imports = 0 for target files
- [ ] No bot/deep-link references (check `telegram/bot.py`, care tips)
- [ ] Middleware redirect covers route (if page removed)
- [ ] `npm run lint` + `npm run build` pass
- [ ] API tests updated for shopping slugs
- [ ] No rollback of V1 Vision behavior (hero priority, categories)

---

## Финальный вердикт (backlog)

| Вопрос | Ответ |
|--------|-------|
| Начинать очистку? | **Да** — с Phase A (orphans) и Phase B (shopping backend) |
| Удалить первым | P1-1…P1-6 (zero-risk orphans) |
| Не трогать | API core, DB, TelegramProvider, account forms до замены, recipe seeds до import |
