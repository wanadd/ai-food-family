# PLANAM V2 Selective Import

Wave 10 imports a non-production source snapshot into a clean V2 rehearsal target.

The pipeline in `apps/api/app/selective_import/pipeline.py` is deliberately split
into precheck, classification, transformation, import and report phases. Every
run carries a source hash, configuration hash, batch identity and target schema
head. Canonical UUID keys are deterministic for a `(target, legacy_id)` pair;
legacy IDs remain only in `legacy_id_mappings` and provenance.

The first pass is always `--mode dry-run`. It does not flush or commit. Apply
mode is permitted only against a disposable target and the exact Alembic head
`20260927_0019`; production-like URLs and overrides are rejected. Re-running a
source uses existing mappings and canonical keys, so it does not duplicate core
records.

Ambiguous profiles, age-only data, free-text allergies and event allergy notes
enter the reconfirmation queue. Missing facts are not emitted as `KNOWN_NONE`.
Legacy admin sessions, pending notification delivery and provider bearer data
are dropped; cooking does not create consumption and event guest counts do not
create participants. Unvalidated recipes are archive-only. Generated reports
are local rehearsal evidence and are not committed.

Example disposable rehearsal:

```text
python scripts/v2_selective_import.py --source tests/fixtures/v2_selective_import_fixture.json --target .local/v2-selective-import/rehearsal.sqlite --mode dry-run --report .local/v2-selective-import/dry-run.json
python scripts/v2_selective_import.py --source tests/fixtures/v2_selective_import_fixture.json --target .local/v2-selective-import/rehearsal.sqlite --mode apply --report .local/v2-selective-import/apply.json
```
