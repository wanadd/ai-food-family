#!/usr/bin/env python3
"""Normalize subscription plans: enable start, disable free/demo/trial legacy."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.services.plan_codes import START_PLAN_CODE
from app.services.subscription_catalog import PLAN_SEEDS, seed_subscription_plans


def _migrate_trial_to_start(db) -> None:
  """Rename legacy trial plan row to start when start is missing."""
  trial = db.execute(
      text("SELECT id FROM subscription_plans WHERE code = 'trial' LIMIT 1")
  ).first()
  start = db.execute(
      text("SELECT id FROM subscription_plans WHERE code = 'start' LIMIT 1")
  ).first()
  if trial and not start:
      db.execute(
          text(
              "UPDATE subscription_plans SET code = :start, name = 'Старт' "
              "WHERE code = 'trial'"
          ),
          {"start": START_PLAN_CODE},
      )
      db.execute(
          text(
              "UPDATE user_subscriptions SET plan_code = :start "
              "WHERE plan_code = 'trial'"
          ),
          {"start": START_PLAN_CODE},
      )
  elif trial and start:
      db.execute(
          text("UPDATE subscription_plans SET is_active = false WHERE code = 'trial'")
      )
      db.execute(
          text(
              "UPDATE user_subscriptions SET plan_code = :start "
              "WHERE plan_code = 'trial'"
          ),
          {"start": START_PLAN_CODE},
      )


def _deactivate_legacy(db) -> None:
  for code in ("free", "demo"):
      db.execute(
          text(
              "UPDATE subscription_plans SET is_active = false WHERE code = :code"
          ),
          {"code": code},
      )
      db.execute(
          text(
              "UPDATE user_subscriptions SET plan_code = :start "
              "WHERE plan_code = :code"
          ),
          {"start": START_PLAN_CODE, "code": code},
      )


def main() -> int:
  url = os.environ.get("DATABASE_URL")
  if not url:
      print("DATABASE_URL is required", file=sys.stderr)
      return 1

  engine = create_engine(url)
  Session = sessionmaker(bind=engine)
  db = Session()
  try:
      seed_subscription_plans(db)
      _migrate_trial_to_start(db)
      _deactivate_legacy(db)
      db.commit()

      rows = db.execute(
          text(
              "SELECT code, name, is_active FROM subscription_plans "
              "ORDER BY sort_order, id"
          )
      ).mappings().all()
      print("subscription_plans:")
      for row in rows:
          print(f"  {row['code']}: {row['name']} active={row['is_active']}")
      return 0
  finally:
      db.close()


if __name__ == "__main__":
  raise SystemExit(main())
