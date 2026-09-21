# 15 Testing And QA

## Risk-based gates

Validate the smallest relevant surface first, then broaden when a contract crosses domains. Evidence and safety changes require deterministic fixtures, explicit unknown cases, provenance assertions, and family aggregation tests.

## Required checks for evidence work

- Schema and migration acceptance checks
- Identity and source/provenance round trips
- Unit normalization and null/zero distinction
- Safety state precedence
- Personal path and virtual family-member path
- Low-confidence and unknown evidence behavior
- No unintended legacy data deletion

## UI and image QA

Check responsive layout, touch targets, contrast, loading/error/unknown states, and the one-master image crop contract. A bad crop requires manual review; it does not justify generating a second image master.

## Checkpoint policy

Tests are evidence, not permission to deploy. A passing local test cannot authorize migrations, backfill, reset, push, merge, or release.
