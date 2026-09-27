# API results

Seven new `/api/v2` routes are registered:

- `GET /households`
- `POST /households`
- `GET /households/{household_id}/members`
- `POST /households/{household_id}/members`
- `PATCH /people/{person_id}`
- `DELETE /account/identities/{identity_id}`
- `GET /entitlements`

Mutation routes use idempotency headers. Context and permission checks are server-side. Unauthorized dependent/cross-household access is denied before mutation.
