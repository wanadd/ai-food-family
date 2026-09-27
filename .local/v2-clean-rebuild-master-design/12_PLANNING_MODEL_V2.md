# Planning Model V2

`Plan -> PlanRevision -> PlanSlot -> Assignment`. A slot has date/time/meal type, explicit state (`ASSIGNED`, `EMPTY`, `FREE`, `CANCELLED`), participants and portions. `EMPTY/FREE` are not NULL and cannot be silently repopulated.

OD-15 (`PERSON_OR_HOUSEHOLD_SCOPED_PLANNING`) makes Plan ownership explicit and mutually exclusive. A person-owned Plan has `person_id` set and `household_id` NULL; a household-owned Plan has `household_id` set and `person_id` NULL. The canonical database invariant is `XOR(person_id IS NOT NULL, household_id IS NOT NULL)`. There is no implicit, system, synthetic or hidden household for personal planning. Personal mode works without household setup.

Revision records generation provenance, actor, input snapshot, safety evaluation and replacement history and inherits its Plan owner scope. Manual override is first-class and retains reason. Person plans evaluate the owning Person; household plans evaluate participating Persons independently and aggregate safety conservatively. Planned food is not cooked or consumed.

Commands are idempotent and authorized against the server-resolved Plan owner: Person authorization uses self or canonical relationship/membership/permission grants, while Household authorization requires active membership and capability. Client-supplied IDs are resource selectors, never authority. Menu generation evaluates entitlement, candidate evidence, portions and safety before publication for either owner scope. Missing nutrition lowers confidence; it is not imputed as zero.
