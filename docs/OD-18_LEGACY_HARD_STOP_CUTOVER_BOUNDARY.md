# OD-18: HARD_STOP_LEGACY_CUTOVER_BOUNDARY

Owner decision for the one-time PLANAM legacy to V2 migration.

The legacy runtime is not retrofitted with exactly-once provider delivery or a
graceful scheduler drain. Non-financial reminders may be interrupted at cutover.
An uncertain provider result is not replayed into V2. This policy does not
cover payment capture, refund, or another financial provider operation.

The ordered boundary is: deploy the legacy bridge in normal mode; close only
PLANAM public ingress; set shared Redis `OUTBOUND_FROZEN`; stop all legacy
PLANAM API processes; verify no PLANAM process, application DB session, or
background writer remains; only then back up and snapshot the legacy database.
An in-flight remote provider outcome immediately before process termination
cannot be known. Hard stop bounds local activity; it does not prove delivery.

If V2 fails before writes open, restart legacy with `OUTBOUND_FROZEN` still ON.
The core app may be reopened after validation, but providers remain suppressed
until an operator reconciles uncertain notifications and explicitly unfreezes.

No legacy DB schema migration, notification claim table, or delivery-engine
redesign is authorized by this decision.
