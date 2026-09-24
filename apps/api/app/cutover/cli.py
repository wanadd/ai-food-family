from __future__ import annotations

import argparse
import json

from sqlalchemy import create_engine

from app.cutover.backfill import BackfillEngine
from app.cutover.environment import EnvironmentIdentity, RuntimeEnvironment
from app.cutover.operations import collect_inventory_report
from app.cutover.guard import ProductionGuard
from app.cutover.runtime_store import RuntimeStore
from app.cutover.safety import ExecutionRequest, assert_c1_safe


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PLANAM C1 local cutover readiness tooling")
    parser.add_argument("command", choices=("preflight", "backfill", "runtime-status", "runtime-preflight", "runtime-pause", "runtime-resume"))
    parser.add_argument("--environment", default="local")
    parser.add_argument("--database-url", default="postgresql://127.0.0.1/planam")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirmation-token")
    parser.add_argument("--run-id", default="operator-dry-run")
    parser.add_argument("--database-identity", default="")
    parser.add_argument("--expected-database-identity", default="")
    parser.add_argument("--target-revision", default="head")
    parser.add_argument("--reason", default="operator action")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command.startswith("runtime-"):
        engine = create_engine(args.database_url)
        identity = EnvironmentIdentity(
            RuntimeEnvironment(args.environment.upper()),
            args.database_identity or args.database_url,
            args.expected_database_identity or args.database_identity or args.database_url,
        )
        ProductionGuard.assert_dry_run(identity)
        if args.command == "runtime-status":
            store = RuntimeStore(engine, initialize=False)
            print(json.dumps(store.get_run(args.run_id), default=str, sort_keys=True))
        elif args.command == "runtime-preflight":
            print(json.dumps({"run_id": args.run_id, "environment": identity.environment, "target_revision": args.target_revision, "dry_run": True}, default=str, sort_keys=True))
        elif args.command == "runtime-pause":
            store = RuntimeStore(engine)
            store.set_control("WRITE_PAUSED", True, args.reason)
            print(json.dumps({"write_paused": True, "dry_run": False}, sort_keys=True))
        elif args.command == "runtime-resume":
            store = RuntimeStore(engine)
            store.set_control("WRITE_PAUSED", False, args.reason)
            print(json.dumps({"write_paused": False, "dry_run": False}, sort_keys=True))
        return 0
    request = ExecutionRequest(
        environment=args.environment,
        database_url=args.database_url,
        dry_run=not args.execute,
        execute=args.execute,
        confirmation_token=args.confirmation_token,
    )
    assert_c1_safe(request)
    if args.command == "preflight":
        print(json.dumps(collect_inventory_report().__dict__, sort_keys=True, default=str))
        return 0
    if args.execute:
        print("C1 execute mode is local/disposable only; source records must be supplied by an operator-owned fixture")
    else:
        print("C1 BACKFILL DRY RUN: no database mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
