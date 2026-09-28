"""Operator-only CLI for the shared legacy outbound stop."""

import argparse
import json

import redis

from app.services.legacy_outbound_guard import FROZEN_KEY, redis_client


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status", "outbound-freeze"))
    parser.add_argument("value", nargs="?", choices=("on", "off"))
    args = parser.parse_args()
    if args.command == "outbound-freeze" and args.value is None:
        parser.error("outbound-freeze requires on or off")
    if args.command == "status" and args.value is not None:
        parser.error("status does not accept a value")

    try:
        client = redis_client()
        if args.command == "outbound-freeze":
            if args.value == "on":
                client.set(FROZEN_KEY, "1")
            else:
                client.delete(FROZEN_KEY)
        value = client.get(FROZEN_KEY)
    except redis.RedisError:
        print(json.dumps({"outbound_frozen": None, "redis_reachable": False, "guard_version": "OD-18"}))
        return 1
    if value not in (None, b"1"):
        print(json.dumps({"outbound_frozen": None, "redis_reachable": True, "guard_version": "OD-18", "error": "INVALID_STATE"}))
        return 1
    print(json.dumps({"outbound_frozen": value == b"1", "redis_reachable": True, "guard_version": "OD-18"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
