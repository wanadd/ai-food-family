# PLANAM Cross-Branch Audit

Gate report for **PLANAM Project-Wide Architecture Consolidation V1**.
Generated before starting consolidation. Read-only (git inspection only).

## Current branch

`sprint-0/planam-2026-foundation` (HEAD = `fbc0177`).

## All branches

Local:
- `audit/planam-master-audit`
- `main`
- `planam-recipe-engine-v1`
- `recipe-engine-v1`
- `recipe-import-broken-backup`
- `recipe-import-clean`
- `recipe-import-pipeline-v1`
- `release-candidate-ux`
- `sprint-0/planam-2026-foundation` ← current
- `ux-foundation-v1`
- `ux-ui-refinement-v1`

Remote (`origin`): `main`, `recipe-engine-v1`, `recipe-import-clean`,
`recipe-import-pipeline-v1`, `release-candidate-ux`,
`sprint-0/planam-2026-foundation`, `ux-foundation-v1`, `ux-ui-refinement-v1`.

## Recent commits (current branch)

```
fbc0177 fix(shopping): clean up menu generated shopping list
1190639 fix(recipes): render ingredient amounts with correct units
781589c feat(nutrition): aggregate menu nutrition and expose daily summary
98c88ae feat(recipes): persist nutrition summary and expose in UI
cd7f497 feat(recipes): add nutrition (КБЖУ), shopping grouping and photo readiness pipeline
7d32f06 feat(recipes): add to-taste ingredient model and readiness reports
d8adc43 feat(recipes): add safe ingredient commit and jsonb resync
2813678 feat(v1): canonical products + unit normalization + dry-run normalizer
2edbbf6 feat(v1): read-only recipe ingredient quality audit
ae431eb hotfix(infra): persist recipe images on server
```

## Diff summary: current vs each branch

`HEAD..<branch>` = what `<branch>` has that current does NOT. The huge deletion
counts (going current → branch) mean those branches are **older/smaller**; the
current branch is a strict superset of their content.

| branch | `HEAD..branch` files | insertions | deletions | unique commits in branch not in HEAD |
|--------|----------------------|------------|-----------|--------------------------------------|
| origin/main | 596 | 5 235 | 97 910 | **0** |
| origin/ux-foundation-v1 | 584 | 5 180 | 96 492 | **0** |
| origin/release-candidate-ux | 584 | 5 180 | 96 492 | **0** |
| origin/recipe-engine-v1 | 551 | 5 083 | 89 984 | **0** |
| origin/recipe-import-pipeline-v1 | 451 | 2 730 | 81 312 | **0** |
| origin/ux-ui-refinement-v1 | 458 | 2 702 | 84 194 | **0** |
| origin/recipe-import-clean | 414 | 2 727 | 68 584 | **1** |

The only unique commit anywhere is `858df80 fix(admin): build absolute admin
WebApp URL` on `recipe-import-clean`. Verified: `git diff HEAD
origin/recipe-import-clean -- apps/api/app/services/admin_auth.py` is **empty** —
the same fix (`telegram_webapp_url or "https://planam.ru"`) is **already present**
in the current branch. Nothing to cherry-pick.

## Files that exist only in other branches (not in current)

Sampled vs `origin/main` (representative of all older branches). These are
**superseded legacy** that the 2026 branch intentionally replaced:

| file (only in old branches) | replaced in current by |
|-----------------------------|--------------------------|
| `apps/api/app/services/recipes.py` | `apps/api/app/services/recipes/` package (mapper, authoring, …) |
| `apps/web/components/layout/BottomNav.tsx` | `components/.../BottomNavigation2026` |
| `apps/web/components/layout/BottomBackButton.tsx`, `TopBackLink.tsx` | 2026 navigation/back helpers |
| `apps/web/components/onboarding/OnboardingWizard.tsx` + steps | current `/onboarding` 2026 flow |
| `apps/web/components/recipes/RecipeCatalog.tsx` | `components/recipes-2026/RecipeCatalog2026.tsx` |

None of these need to be brought forward.

## Conclusion / decisions

1. **Base of truth:** `sprint-0/planam-2026-foundation` is the canonical product
   branch. It contains the full history of every other branch (0 unique commits
   elsewhere) plus all 2026 work.
2. **Useful new logic in other branches:** none. The single divergent commit is
   already merged in content.
3. **Legacy/archival branches:** `main`, `ux-foundation-v1`,
   `release-candidate-ux`, `recipe-engine-v1`, `planam-recipe-engine-v1`,
   `recipe-import-pipeline-v1`, `recipe-import-clean`, `recipe-import-broken-backup`,
   `ux-ui-refinement-v1`, `audit/planam-master-audit` — treat as **archival**.
4. **Cherry-picks required:** none.
5. **Do NOT** merge any old branch wholesale (would re-introduce removed legacy
   files and old bugs).

**Gate result: PASSED.** Consolidation continues on
`sprint-0/planam-2026-foundation`.
