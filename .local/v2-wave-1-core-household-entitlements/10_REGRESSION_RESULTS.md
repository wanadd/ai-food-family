# Regression results

- Wave 1 backend focused tests: `6 passed`.
- Wave 0/core focused regression: `34 passed`.
- PostgreSQL migration acceptance: `2 passed`.
- Backend regression excluding unrelated dirty cutover readiness file: `1344 passed, 3 skipped, 3 warnings`.
- Full current worktree backend run: `1354 passed, 3 skipped, 3 warnings, 1 failure`.
- The one failure is the pre-existing `test_cutover_readiness_wave_11` inventory expectation. A clean Wave 0 checkout reproduced the baseline test as `1 passed`; current dirty cutover files change the inventory from 63 to 66. No Wave 1 file causes that failure.
