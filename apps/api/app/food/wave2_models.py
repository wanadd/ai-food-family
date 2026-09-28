from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import CoreJSON, CoreUUID
from app.database import Base


class FoodIdentity(Base):
    __tablename__ = "food_identities"
    __table_args__ = (
        CheckConstraint("canonical_key <> ''", name="ck_food_identities_key_not_blank"),
    )
    food_identity_id: Mapped[int] = mapped_column("id", Integer, primary_key=True)
    identity_key: Mapped[str] = mapped_column("canonical_key", String(160), nullable=False)
    display_name: Mapped[str] = mapped_column("canonical_name", String(240), nullable=False)
    food_kind: Mapped[str | None] = mapped_column("food_class", String(64), nullable=True)
    lifecycle_status: Mapped[str] = mapped_column("status", String(24), nullable=False, default="review")
    provenance_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PackagedProduct(Base):
    __tablename__ = "packaged_products"
    packaged_product_id: Mapped[int] = mapped_column("id", Integer, primary_key=True)
    product_key: Mapped[str | None] = mapped_column("gtin", String(32), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(160), nullable=True)
    product_name: Mapped[str] = mapped_column(String(240), nullable=False)
    lifecycle_status: Mapped[str] = mapped_column("status", String(24), nullable=False, default="review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductInstance(Base):
    __tablename__ = "product_instances"
    product_instance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    packaged_product_id: Mapped[int] = mapped_column(Integer, ForeignKey("packaged_products.id", ondelete="RESTRICT"))
    owner_person_id: Mapped[int | None] = mapped_column("user_id", Integer, nullable=True)
    lot_code: Mapped[str | None] = mapped_column(String(160), nullable=True)
    observed_at: Mapped[datetime] = mapped_column("acquired_at", DateTime(timezone=True), server_default=func.now())
    instance_status: Mapped[str] = mapped_column("status", String(24), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SourceRegistry(Base):
    __tablename__ = "source_registry"
    source_registry_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    source_code: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)
    authority_tier: Mapped[str] = mapped_column(String(32), nullable=False)
    jurisdiction: Mapped[str | None] = mapped_column(String(80), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(200), nullable=True)
    publication_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="ACTIVE")
    metadata_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FoodEvidenceLink(Base):
    __tablename__ = "food_evidence_links"
    __table_args__ = (UniqueConstraint("food_identity_id", "claim_id", "relation_type", name="uq_food_evidence_link"),)
    food_evidence_link_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    food_identity_id: Mapped[int] = mapped_column(Integer, ForeignKey("food_identities.id", ondelete="CASCADE"))
    claim_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("evidence_claims.claim_id", ondelete="CASCADE"))
    relation_type: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SafetyRule(Base):
    __tablename__ = "safety_rules"
    __table_args__ = (UniqueConstraint("rule_key", "version", name="uq_safety_rules_key_version"),)
    safety_rule_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    rule_key: Mapped[str] = mapped_column(String(160), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT")
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    target_concept: Mapped[str] = mapped_column(String(160), nullable=False)
    facts_consumed_json: Mapped[list] = mapped_column(CoreJSON, nullable=False, default=list)
    evidence_claim_ids_json: Mapped[list] = mapped_column(CoreJSON, nullable=False, default=list)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    explanation_code: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SafetyDecision(Base):
    __tablename__ = "safety_decisions"
    __table_args__ = (
        UniqueConstraint("person_id", "idempotency_key", name="uq_safety_decisions_person_idempotency"),
        Index("ix_safety_decisions_person_time", "person_id", "evaluated_at"),
    )
    safety_decision_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="CASCADE"))
    food_identity_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("food_identities.id", ondelete="SET NULL"))
    packaged_product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("packaged_products.id", ondelete="SET NULL"))
    process_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    reason_codes_json: Mapped[list] = mapped_column(CoreJSON, nullable=False, default=list)
    safety_rule_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("safety_rules.safety_rule_id", ondelete="SET NULL"))
    evidence_claim_ids_json: Mapped[list] = mapped_column(CoreJSON, nullable=False, default=list)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
