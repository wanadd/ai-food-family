from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.models import EntitlementConsumption, EntitlementGrant, EntitlementPlan
from app.v2.errors import error
from app.v2.uuid7 import uuid7_str


@dataclass(frozen=True)
class EntitlementDecision:
    capability: str
    allowed: bool
    limit: int | None
    used: int
    remaining: int | None
    source: str | None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _active_grants(db: Session, account_id: str, household_id: str | None, person_id: str | None, capability: str, at: datetime):
    subjects = [EntitlementGrant.account_id == account_id]
    if household_id:
        subjects.append(EntitlementGrant.household_id == household_id)
    if person_id:
        subjects.append(EntitlementGrant.person_id == person_id)
    return list(
        db.scalars(
            select(EntitlementGrant)
            .where(
                EntitlementGrant.capability == capability,
                EntitlementGrant.grant_status == "active",
                EntitlementGrant.effective_from <= at,
                (EntitlementGrant.effective_to.is_(None) | (EntitlementGrant.effective_to > at)),
                or_(*subjects),
            )
            .order_by(EntitlementGrant.person_id.is_(None), EntitlementGrant.household_id.is_(None), EntitlementGrant.created_at.desc())
        )
    )


def effective_entitlement(
    db: Session,
    *,
    account_id: str,
    household_id: str | None,
    person_id: str | None,
    capability: str,
    at: datetime | None = None,
) -> EntitlementDecision:
    grants = _active_grants(db, account_id, household_id, person_id, capability, at or _now())
    if not grants:
        return EntitlementDecision(capability, False, None, 0, None, None)
    grant = grants[0]
    used = int(db.scalar(select(func.coalesce(func.sum(EntitlementConsumption.amount), 0)).where(EntitlementConsumption.grant_id == grant.grant_id)) or 0)
    remaining = max(grant.limit_value - used, 0) if grant.limit_value is not None else None
    return EntitlementDecision(capability, remaining is None or remaining > 0, grant.limit_value, used, remaining, grant.source)


def list_effective_entitlements(db: Session, *, account_id: str, household_id: str | None, person_id: str | None, at: datetime | None = None) -> list[EntitlementDecision]:
    now = at or _now()
    subjects = [EntitlementGrant.account_id == account_id]
    if household_id:
        subjects.append(EntitlementGrant.household_id == household_id)
    if person_id:
        subjects.append(EntitlementGrant.person_id == person_id)
    capabilities = sorted(db.scalars(select(EntitlementGrant.capability).where(
        EntitlementGrant.grant_status == "active",
        EntitlementGrant.effective_from <= now,
        (EntitlementGrant.effective_to.is_(None) | (EntitlementGrant.effective_to > now)),
        or_(*subjects),
    ).distinct()).all())
    return [effective_entitlement(db, account_id=account_id, household_id=household_id, person_id=person_id, capability=capability, at=now) for capability in capabilities]


def consume_entitlement(
    db: Session,
    *,
    account_id: str,
    household_id: str | None,
    person_id: str | None,
    capability: str,
    amount: int,
    idempotency_key: str,
) -> EntitlementConsumption:
    if amount < 0:
        raise error("validation_error", 422, details={"amount": "must_be_nonnegative"})
    grants = _active_grants(db, account_id, household_id, person_id, capability, _now())
    if not grants:
        raise error("entitlement_required", 403)
    grant = grants[0]
    existing = db.scalar(
        select(EntitlementConsumption).where(
            EntitlementConsumption.grant_id == grant.grant_id,
            EntitlementConsumption.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return existing
    decision = effective_entitlement(db, account_id=account_id, household_id=household_id, person_id=person_id, capability=capability)
    if decision.remaining is not None and amount > decision.remaining:
        raise error("entitlement_required", 403)
    consumption = EntitlementConsumption(
        consumption_id=uuid7_str(),
        grant_id=grant.grant_id,
        amount=amount,
        idempotency_key=idempotency_key,
        provenance_json={"account_id": account_id, "household_id": household_id, "person_id": person_id},
    )
    db.add(consumption)
    db.flush()
    return consumption
