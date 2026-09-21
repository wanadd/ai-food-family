# 16 Do Not Do

- Do not redesign PLANAM during a documentation checkpoint.
- Do not change app behavior, frontend behavior, API behavior, or database schema unless a separate task explicitly authorizes it.
- Do not run destructive migrations, reset recipe data, delete recipes, or backfill evidence without explicit authorization.
- Do not use Alembic as authority for custom-SQL-owned evidence tables.
- Do not add a parallel evidence or safety engine beside existing P0-A through P0-E services.
- Do not treat missing, null, unknown, or uncomputable values as zero or safe.
- Do not infer phenylalanine from protein.
- Do not collapse allergy, celiac, pregnancy, PKU, age, and process-state facts into one unsupported flag.
- Do not lose person identity, participation, portion, provenance, or confidence during aggregation.
- Do not expose source URLs, source titles, or copied source structure as Gold V3 user-facing recipe content.
- Do not generate separate hero/card/thumb image masters for one recipe.
- Do not commit secrets, `.env` files, tokens, private content, or `.local/` artifacts.
- Do not claim evidence completeness while current blockers remain.
- Do not push, merge, deploy, or release from this checkpoint.
