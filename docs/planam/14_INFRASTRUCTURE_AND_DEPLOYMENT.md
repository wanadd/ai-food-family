# 14 Infrastructure And Deployment

## Development

The documented local baseline uses Next.js, FastAPI, PostgreSQL, Redis, and Docker-oriented commands. Environment variables are supplied through local configuration and are never committed.

## Production

Production deployment must use the existing repository deployment documentation, health checks, migration authority, and rollback procedure. A docs checkpoint does not deploy, migrate, backfill, or alter production data.

## Operational invariants

- Do not log tokens, API keys, raw private user content, or provider secrets.
- Keep evidence and safety decisions reproducible from stored provenance.
- Keep custom-SQL schema ownership explicit.
- Treat migration ordering as a release gate.
- Verify the running commit and configuration before claiming a release.

## References

- [`../PRODUCTION_DEPLOY.md`](../PRODUCTION_DEPLOY.md)
- [`../PLANAM_2026_IMPLEMENTATION_ROADMAP.md`](../PLANAM_2026_IMPLEMENTATION_ROADMAP.md)
- [`18_CURRENT_STATE.md`](18_CURRENT_STATE.md)
