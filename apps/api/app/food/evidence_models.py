from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import CoreJSON, CoreUUID
from app.database import Base


class EvidenceSource(Base):
    __tablename__ = "evidence_sources"
    __table_args__ = (
        UniqueConstraint("source_code", name="uq_evidence_sources_code"),
        CheckConstraint(
            "authority_tier IN ('REGULATORY', 'AUTHORITATIVE_DATASET', 'PRODUCT_LABEL', 'CLINICAL_GUIDANCE', 'INTERNAL_LEGACY', 'AI_PROPOSAL')",
            name="ck_evidence_sources_authority_tier",
        ),
        CheckConstraint("status IN ('ACTIVE', 'RETIRED', 'REVIEW_REQUIRED')", name="ck_evidence_sources_status"),
    )

    source_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    source_code: Mapped[str] = mapped_column(String(96), nullable=False)
    authority_tier: Mapped[str] = mapped_column(String(32), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(200), nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="ACTIVE")
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SourceSnapshot(Base):
    __tablename__ = "source_snapshots"
    __table_args__ = (
        UniqueConstraint("source_id", "source_version", "content_hash", name="uq_source_snapshots_release_hash"),
        CheckConstraint("source_version <> ''", name="ck_source_snapshots_version_not_blank"),
    )

    snapshot_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    source_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("evidence_sources.source_id", ondelete="CASCADE"))
    source_version: Mapped[str] = mapped_column(String(128), nullable=False)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    release_metadata_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "source_record_locator", name="uq_evidence_records_snapshot_locator"),
        CheckConstraint("status IN ('ACTIVE', 'SUPERSEDED', 'REJECTED')", name="ck_evidence_records_status"),
    )

    record_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("source_snapshots.snapshot_id", ondelete="CASCADE"))
    source_record_locator: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str | None] = mapped_column(String(240), nullable=True)
    payload_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceClaim(Base):
    __tablename__ = "evidence_claims"
    __table_args__ = (
        UniqueConstraint("record_id", "claim_type", "subject_type", "subject_key", "predicate", name="uq_evidence_claim_scope"),
        CheckConstraint(
            "review_status IN ('NEEDS_REVIEW', 'REVIEWED_ACCEPTED', 'REVIEWED_REJECTED', 'SUPERSEDED')",
            name="ck_evidence_claims_review_status",
        ),
        CheckConstraint("confidence IN ('UNKNOWN', 'LOW', 'MEDIUM', 'HIGH', 'SOURCE_BACKED')", name="ck_evidence_claims_confidence"),
    )

    claim_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    record_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("evidence_records.record_id", ondelete="CASCADE"))
    claim_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_key: Mapped[str] = mapped_column(String(160), nullable=False)
    predicate: Mapped[str] = mapped_column(String(96), nullable=False)
    object_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    confidence: Mapped[str] = mapped_column(String(24), nullable=False, default="UNKNOWN")
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="NEEDS_REVIEW")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceApplicability(Base):
    __tablename__ = "evidence_applicability"
    __table_args__ = (
        CheckConstraint("applies_status IN ('APPLIES', 'DOES_NOT_APPLY', 'UNKNOWN', 'REVIEW_REQUIRED')", name="ck_evidence_applicability_status"),
    )

    applicability_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    claim_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("evidence_claims.claim_id", ondelete="CASCADE"))
    person_context_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    product_context_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    process_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    applies_status: Mapped[str] = mapped_column(String(24), nullable=False, default="UNKNOWN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FoodAlias(Base):
    __tablename__ = "food_aliases"
    __table_args__ = (
        UniqueConstraint("food_identity_key", "alias_text", "language", name="uq_food_alias_identity_text_language"),
        CheckConstraint("status IN ('ACTIVE', 'REVIEW_REQUIRED', 'REJECTED')", name="ck_food_aliases_status"),
    )

    food_alias_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    food_identity_key: Mapped[str] = mapped_column(String(160), nullable=False)
    alias_text: Mapped[str] = mapped_column(String(240), nullable=False)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="und")
    source_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("evidence_sources.source_id", ondelete="SET NULL"), nullable=True)
    confidence: Mapped[str] = mapped_column(String(24), nullable=False, default="UNKNOWN")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="REVIEW_REQUIRED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FoodCompositionFact(Base):
    __tablename__ = "food_composition_facts"
    __table_args__ = (
        UniqueConstraint(
            "food_identity_key",
            "nutrient_key",
            "food_state",
            "basis_amount",
            "basis_unit",
            "snapshot_id",
            "source_record_locator",
            name="uq_food_composition_fact_source_scope",
        ),
        CheckConstraint("value IS NULL OR value >= 0", name="ck_food_composition_facts_non_negative_or_unknown"),
        CheckConstraint("basis_amount > 0", name="ck_food_composition_facts_basis_positive"),
        CheckConstraint("value IS NULL OR source_id IS NOT NULL", name="ck_food_composition_facts_value_requires_source"),
        CheckConstraint("value IS NULL OR snapshot_id IS NOT NULL", name="ck_food_composition_facts_value_requires_snapshot"),
        CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_food_composition_facts_period"),
        CheckConstraint("review_status IN ('NEEDS_REVIEW', 'REVIEWED_ACCEPTED', 'REVIEWED_REJECTED', 'SUPERSEDED')", name="ck_food_composition_facts_review_status"),
        Index("ix_food_composition_identity_nutrient", "food_identity_key", "nutrient_key", "food_state"),
    )

    composition_fact_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    food_identity_key: Mapped[str] = mapped_column(String(160), nullable=False)
    nutrient_key: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(24), nullable=False)
    basis_amount: Mapped[float] = mapped_column(Float, nullable=False)
    basis_unit: Mapped[str] = mapped_column(String(24), nullable=False)
    food_state: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    source_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("evidence_sources.source_id", ondelete="RESTRICT"), nullable=True)
    snapshot_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("source_snapshots.snapshot_id", ondelete="RESTRICT"), nullable=True)
    source_record_locator: Mapped[str] = mapped_column(String(512), nullable=False)
    confidence: Mapped[str] = mapped_column(String(24), nullable=False, default="UNKNOWN")
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="NEEDS_REVIEW")
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FoodEvidenceFactLink(Base):
    __tablename__ = "food_evidence_fact_links"
    __table_args__ = (
        UniqueConstraint("claim_id", "fact_table", "fact_id_text", name="uq_food_evidence_fact_link"),
        CheckConstraint("link_type IN ('SUPPORTS', 'CONFLICTS_WITH', 'SUPERSEDES')", name="ck_food_evidence_fact_links_type"),
    )

    link_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    claim_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("evidence_claims.claim_id", ondelete="CASCADE"))
    fact_table: Mapped[str] = mapped_column(String(80), nullable=False)
    fact_id_text: Mapped[str] = mapped_column(String(120), nullable=False)
    link_type: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductLabelFact(Base):
    __tablename__ = "product_label_facts"
    __table_args__ = (
        UniqueConstraint("product_key", "fact_type", "fact_key", "snapshot_id", "source_record_locator", name="uq_product_label_fact_source_scope"),
        CheckConstraint("knowledge_state IN ('UNKNOWN', 'NOT_PROVIDED', 'KNOWN_NONE', 'KNOWN_PRESENT')", name="ck_product_label_facts_knowledge_state"),
        CheckConstraint("review_status IN ('NEEDS_REVIEW', 'REVIEWED_ACCEPTED', 'REVIEWED_REJECTED', 'SUPERSEDED')", name="ck_product_label_facts_review_status"),
        Index("ix_product_label_facts_product_type", "product_key", "fact_type", "fact_key"),
    )

    product_label_fact_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    product_key: Mapped[str] = mapped_column(String(160), nullable=False)
    fact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    fact_key: Mapped[str] = mapped_column(String(160), nullable=False)
    knowledge_state: Mapped[str] = mapped_column(String(24), nullable=False)
    value_json: Mapped[dict | None] = mapped_column(CoreJSON, nullable=True)
    source_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("evidence_sources.source_id", ondelete="RESTRICT"))
    snapshot_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("source_snapshots.snapshot_id", ondelete="RESTRICT"))
    source_record_locator: Mapped[str] = mapped_column(String(512), nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="NEEDS_REVIEW")
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
