from __future__ import annotations

import argparse
import json

from app.cutover.backfill import BackfillEngine
from app.cutover.operations import collect_inventory_report
from app.cutover.safety import ExecutionRequest, assert_c1_safe


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PLANAM C1 local cutover readiness tooling")
    parser.add_argument("command", choices=("preflight", "backfill"))
    parser.add_argument("--environment", default="local")
    parser.add_argument("--database-url", default="postgresql://127.0.0.1/planam")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirmation-token")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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
